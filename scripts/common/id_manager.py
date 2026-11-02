# -*- coding: utf-8 -*-
"""
ID永続化共通マネージャー (id_manager.py)
----------------------------------------
- 一度発行したID（国コード-種別-6桁連番）を永続化し、再収集時にも変更・再利用しない。
- Wikidata ID、公的コード、または正規化名称キーにより既存レコードと突合。
- 新規レコードのみ最大連番+1で採番（municipalities と weather_zones は AR 連番空間を共有）。
- 現行スキーマv3（全14テーブル体系）完全準拠。
"""

import os
import re
import pandas as pd


class IdManager:
    # テーブル種別ごとのIDプレフィックス定義（docs/02 確定仕様 v3 準拠）
    PREFIX_MAP = {
        'municipalities': 'AR',
        'weather_zones': 'AR',
        'statistical_areas': 'ST',
        'operators': 'OP',
        'transport_routes': 'RT',
        'nodes': 'ND',
        'edges': 'ED',
        'relations': 'RL',
        'exploration_logs': 'LOG',
    }

    ID_COL_MAP = {
        'countries': 'country_code',
        'country_progress': 'country_code',
        'pilot_progress': 'target_id',
        'area_types': 'type_id',
        'data_sources': 'source_id',
        'municipalities': 'municipality_id',
        'weather_zones': 'zone_id',
        'statistical_areas': 'statistical_area_id',
        'operators': 'operator_id',
        'transport_routes': 'route_id',
        'nodes': 'node_id',
        'edges': 'edge_id',
        'relations': 'relation_id',
        'exploration_logs': 'log_id',
    }

    def __init__(self, master_dir):
        self.master_dir = master_dir
        self.existing_records = {}  # {table_name: DataFrame}
        self.max_seq = {}           # {(prefix, country_code): max_seq_int}
        self.key_to_id = {}         # {(table_name, country_code, match_key): id_str}

    def _extract_name_ja(self, row):
        for col in ('名称', '路線名', '事業者名', '日本語名'):
            v = str(row.get(col, '')).strip()
            if v:
                return v
        return ''

    def _extract_name_local(self, row):
        for col in ('名称_公用語', '路線名_公用語', '公用語名'):
            v = str(row.get(col, '')).strip()
            if v:
                return v
        return ''

    def _extract_code(self, row):
        for col in ('公的コード', '気象庁コード', '自治体コード', '拠点コード', '路線番号_記号'):
            v = str(row.get(col, '')).strip()
            if v:
                return v
        return ''

    def _extract_kind(self, row):
        for col in ('種別', 'type_id', '大分類'):
            v = str(row.get(col, '')).strip()
            if v:
                return v
        return ''

    def load_table(self, table_name):
        """マスタテーブルを読み込み、既存IDと照合キーのマッピングを構築"""
        # ARプレフィックス共有のため、municipalitiesとweather_zonesは両方読み込む
        targets = ['municipalities', 'weather_zones'] if table_name in ('municipalities', 'weather_zones') else [table_name]
        for tbl in targets:
            if tbl in self.existing_records:
                continue
            self._load_single_table(tbl)

    def _load_single_table(self, table_name):
        csv_file = os.path.join(self.master_dir, f"{table_name}.csv")
        id_col = self.ID_COL_MAP.get(table_name)

        if not os.path.exists(csv_file):
            self.existing_records[table_name] = pd.DataFrame()
            return

        df = pd.read_csv(csv_file, encoding='utf-8-sig', keep_default_na=False, dtype=str)
        self.existing_records[table_name] = df

        if not id_col or id_col not in df.columns:
            return

        for _, row in df.iterrows():
            current_id = str(row[id_col]).strip()
            if not current_id:
                continue

            m = re.match(r"^([A-Z]+)-([A-Z]+)-(\d+)$", current_id)
            if m:
                cc = m.group(1)
                pfx = m.group(2)
                seq = int(m.group(3))
                key_seq = (pfx, cc)
                if key_seq not in self.max_seq or seq > self.max_seq[key_seq]:
                    self.max_seq[key_seq] = seq

                kind = self._extract_kind(row)

                # 1. Wikidata QID
                wiki_val = str(row.get('Wikidata_id', row.get('Wikidata', ''))).strip()
                if wiki_val:
                    qid_m = re.search(r"Q\d+", wiki_val)
                    if qid_m:
                        self.key_to_id[(table_name, cc, f"wiki:{kind}:{qid_m.group(0)}")] = current_id

                # 2. 公的コード
                code = self._extract_code(row)
                if code:
                    self.key_to_id[(table_name, cc, f"code:{kind}:{code}")] = current_id

                # 3. 名称 / 公用語名
                name_ja = self._extract_name_ja(row)
                name_local = self._extract_name_local(row)
                if name_ja:
                    self.key_to_id[(table_name, cc, f"name_ja:{kind}:{name_ja}")] = current_id
                if name_local:
                    self.key_to_id[(table_name, cc, f"name_local:{kind}:{name_local}")] = current_id

                # 4. edges 用照合キー
                if table_name == 'edges':
                    r_id = str(row.get('route_id', '')).strip()
                    fn_id = str(row.get('from_node_id', '')).strip()
                    tn_id = str(row.get('to_node_id', '')).strip()
                    if r_id and fn_id and tn_id:
                        self.key_to_id[(table_name, cc, f"edge:{r_id}:{fn_id}:{tn_id}")] = current_id

    def get_or_assign_id(self, table_name, country_code, record_dict):
        """
        レコードに対して既存IDを照合・返却。存在しなければ新規6桁IDを発行。
        """
        self.load_table(table_name)

        prefix = self.PREFIX_MAP.get(table_name, 'REC')
        cc = country_code.strip()

        # 0. edges 特殊照合
        if table_name == 'edges':
            r_id = str(record_dict.get('route_id', '')).strip()
            fn_id = str(record_dict.get('from_node_id', '')).strip()
            tn_id = str(record_dict.get('to_node_id', '')).strip()
            edge_k = (table_name, cc, f"edge:{r_id}:{fn_id}:{tn_id}")
            if edge_k in self.key_to_id:
                return self.key_to_id[edge_k], False

        kind = self._extract_kind(record_dict)

        # 1. Wikidata QID優先
        wiki_val = str(record_dict.get('Wikidata_id', record_dict.get('Wikidata', ''))).strip()
        qid_m = re.search(r"Q\d+", wiki_val) if wiki_val else None
        if qid_m:
            k = (table_name, cc, f"wiki:{kind}:{qid_m.group(0)}")
            if k in self.key_to_id:
                return self.key_to_id[k], False

        # 2. 公的コードで照合
        code = self._extract_code(record_dict)
        if code:
            k = (table_name, cc, f"code:{kind}:{code}")
            if k in self.key_to_id:
                return self.key_to_id[k], False

        # 3. 種別＋名称で照合
        name_ja = self._extract_name_ja(record_dict)
        name_local = self._extract_name_local(record_dict)
        if name_ja:
            k = (table_name, cc, f"name_ja:{kind}:{name_ja}")
            if k in self.key_to_id:
                return self.key_to_id[k], False
        if name_local:
            k = (table_name, cc, f"name_local:{kind}:{name_local}")
            if k in self.key_to_id:
                return self.key_to_id[k], False

        # 新規採番
        key_seq = (prefix, cc)
        next_seq = self.max_seq.get(key_seq, 0) + 1
        self.max_seq[key_seq] = next_seq
        new_id = f"{cc}-{prefix}-{next_seq:06d}"

        # 辞書に登録
        if table_name == 'edges':
            r_id = str(record_dict.get('route_id', '')).strip()
            fn_id = str(record_dict.get('from_node_id', '')).strip()
            tn_id = str(record_dict.get('to_node_id', '')).strip()
            if r_id and fn_id and tn_id:
                self.key_to_id[(table_name, cc, f"edge:{r_id}:{fn_id}:{tn_id}")] = new_id
        if qid_m:
            self.key_to_id[(table_name, cc, f"wiki:{kind}:{qid_m.group(0)}")] = new_id
        if code:
            self.key_to_id[(table_name, cc, f"code:{kind}:{code}")] = new_id
        if name_ja:
            self.key_to_id[(table_name, cc, f"name_ja:{kind}:{name_ja}")] = new_id
        if name_local:
            self.key_to_id[(table_name, cc, f"name_local:{kind}:{name_local}")] = new_id

        return new_id, True

    def save_merged_master(self, table_name, df_new_records, country_code='JP', target_types=None, target_route_ids=None):
        """
        他分野・他国・他路線のレコードを保持したまま、対象レコードのみを安全に差し替えて保存する。
        """
        csv_file = os.path.join(self.master_dir, f"{table_name}.csv")
        id_col = self.ID_COL_MAP.get(table_name)

        if os.path.exists(csv_file):
            df_old = pd.read_csv(csv_file, encoding='utf-8-sig', keep_default_na=False, dtype=str)
            if table_name == 'edges' and target_route_ids:
                df_keep = df_old[~df_old['route_id'].isin(target_route_ids)].copy()
            elif 'country_code' in df_old.columns and '種別' in df_old.columns and target_types:
                mask_keep = (df_old['country_code'] != country_code) | (~df_old['種別'].isin(target_types))
                df_keep = df_old[mask_keep].copy()
            elif 'country_code' in df_old.columns:
                df_keep = df_old[df_old['country_code'] != country_code].copy()
            else:
                df_keep = pd.DataFrame()
        else:
            df_keep = pd.DataFrame()

        df_final = pd.concat([df_keep, df_new_records], ignore_index=True)
        if id_col and id_col in df_final.columns:
            dups = df_final[df_final.duplicated(id_col, keep=False)]
            if len(dups) > 0:
                print(f"[警告] {table_name}.csv 保存時に {len(dups)} 件のID重複を検知。重複を排除します。")
                df_final = df_final.drop_duplicates(subset=[id_col], keep='last')

        df_final.to_csv(csv_file, index=False, encoding='utf-8')
        self.existing_records[table_name] = df_final
        print(f"マスタ安全保存完了: {csv_file} (今回の対象: {len(df_new_records)} 件, 全体: {len(df_final)} 件)")
        return df_final
