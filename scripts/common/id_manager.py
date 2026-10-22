# -*- coding: utf-8 -*-
"""
ID永続化共通マネージャー (id_manager.py)
----------------------------------------
- 一度発行したID（国コード-種別-6桁連番）を永続化し、再収集時にも変更・再利用しない。
- Wikidata ID、公的コード、または正規化名称キーにより既存レコードと突合。
- 新規レコードのみ最大連番+1で採番。
- ソースから消えたレコードは削除せず論理フラグ（廃止/要確認）を残す。
"""

import os
import re
import pandas as pd


class IdManager:
    # テーブル種別ごとのIDプレフィックス定義
    PREFIX_MAP = {
        'municipalities': 'M',
        'operators': 'OP',
        'transport_routes': 'RT',
        'transport_nodes': 'ND',
        'route_nodes': 'RN',
        'exploration_logs': 'LOG'
    }

    ID_COL_MAP = {
        'municipalities': 'municipality_id',
        'operators': 'operator_id',
        'transport_routes': 'route_id',
        'transport_nodes': 'node_id',
        'route_nodes': 'link_id',
        'exploration_logs': 'log_id'
    }

    def __init__(self, master_dir):
        self.master_dir = master_dir
        self.existing_records = {}  # {table_name: DataFrame}
        self.max_seq = {}           # {(table_name, country_code): max_seq_int}
        self.key_to_id = {}         # {(table_name, country_code, match_key): id_str}

    def load_table(self, table_name):
        """マスタテーブルを読み込み、既存IDと照合キーのマッピングを構築"""
        csv_file = os.path.join(self.master_dir, f"{table_name}.csv")
        prefix = self.PREFIX_MAP.get(table_name)
        id_col = self.ID_COL_MAP.get(table_name)

        if not os.path.exists(csv_file):
            self.existing_records[table_name] = pd.DataFrame()
            return

        df = pd.read_csv(csv_file, encoding='utf-8', keep_default_na=False, dtype=str)
        self.existing_records[table_name] = df

        if id_col not in df.columns:
            return

        for _, row in df.iterrows():
            current_id = str(row[id_col]).strip()
            if not current_id:
                continue

            # ID形式: [CC]-[PREFIX]-[SEQ] (例: JP-ND-000001)
            # 旧形式 5桁 (例: JP-ND-00001) にも対応
            m = re.match(r"^([A-Z]+)-([A-Z]+)-(\d+)$", current_id)
            if m:
                cc = m.group(1)
                seq = int(m.group(3))
                key_cc = (table_name, cc)
                if key_cc not in self.max_seq or seq > self.max_seq[key_cc]:
                    self.max_seq[key_cc] = seq

                # 照合キーを複数登録して頑健に照合（必ず種別を含める）
                kind = str(row.get('種別', '')).strip()

                # 1. Wikidata URL (QID)
                wiki_url = str(row.get('Wikidata', '')).strip()
                if wiki_url:
                    qid_m = re.search(r"Q\d+", wiki_url)
                    if qid_m:
                        self.key_to_id[(table_name, cc, f"wiki:{kind}:{qid_m.group(0)}")] = current_id

                # 2. 公的コード (自治体コード、拠点コード、路線番号)
                code = str(row.get('自治体コード', row.get('拠点コード', row.get('路線番号_記号', '')))).strip()
                if code:
                    self.key_to_id[(table_name, cc, f"code:{kind}:{code}")] = current_id

                # 3. 日本語名 / 公用語名
                name_ja = str(row.get('日本語名', '')).strip()
                name_local = str(row.get('公用語名', '')).strip()
                # 4. route_nodes 用照合キー (route_id + node_id + 区間別称)
                if table_name == 'route_nodes':
                    r_id = str(row.get('route_id', '')).strip()
                    n_id = str(row.get('node_id', '')).strip()
                    sub_sec = str(row.get('区間別称', '')).strip()
                    if r_id and n_id:
                        self.key_to_id[(table_name, cc, f"link:{r_id}:{n_id}:{sub_sec}")] = current_id

    def get_or_assign_id(self, table_name, country_code, record_dict):
        """
        レコードに対して既存IDを照合・返却。存在しなければ新規6桁IDを発行。
        """
        if table_name not in self.existing_records:
            self.load_table(table_name)

        prefix = self.PREFIX_MAP.get(table_name, 'REC')
        cc = country_code.strip()

        # 0. route_nodes 特殊照合 (route_id + node_id + 区間別称)
        if table_name == 'route_nodes':
            r_id = str(record_dict.get('route_id', '')).strip()
            n_id = str(record_dict.get('node_id', '')).strip()
            sub_sec = str(record_dict.get('区間別称', '')).strip()
            link_k = (table_name, cc, f"link:{r_id}:{n_id}:{sub_sec}")
            if link_k in self.key_to_id:
                return self.key_to_id[link_k], False

        kind = str(record_dict.get('種別', '')).strip()

        # 1. 既存照合 (Wikidata QID優先、種別一致)
        wiki_url = str(record_dict.get('Wikidata', '')).strip()
        qid_m = None
        if wiki_url:
            qid_m = re.search(r"Q\d+", wiki_url)
            if qid_m:
                k = (table_name, cc, f"wiki:{kind}:{qid_m.group(0)}")
                if k in self.key_to_id:
                    return self.key_to_id[k], False

        # 2. 公的コードで照合（種別一致）
        code = str(record_dict.get('自治体コード', record_dict.get('拠点コード', record_dict.get('路線番号_記号', '')))).strip()
        if code:
            k = (table_name, cc, f"code:{kind}:{code}")
            if k in self.key_to_id:
                return self.key_to_id[k], False

        # 3. 種別＋名称で照合
        name_ja = str(record_dict.get('日本語名', '')).strip()
        name_local = str(record_dict.get('公用語名', '')).strip()
        if name_ja:
            k = (table_name, cc, f"name_ja:{kind}:{name_ja}")
            if k in self.key_to_id:
                return self.key_to_id[k], False
        if name_local:
            k = (table_name, cc, f"name_local:{kind}:{name_local}")
            if k in self.key_to_id:
                return self.key_to_id[k], False

        # 新規採番
        key_cc = (table_name, cc)
        next_seq = self.max_seq.get(key_cc, 0) + 1
        self.max_seq[key_cc] = next_seq
        new_id = f"{cc}-{prefix}-{next_seq:06d}"

        # 辞書に登録
        if table_name == 'route_nodes':
            r_id = str(record_dict.get('route_id', '')).strip()
            n_id = str(record_dict.get('node_id', '')).strip()
            sub_sec = str(record_dict.get('区間別称', '')).strip()
            self.key_to_id[(table_name, cc, f"link:{r_id}:{n_id}:{sub_sec}")] = new_id
        if wiki_url and qid_m:
            self.key_to_id[(table_name, cc, f"wiki:{kind}:{qid_m.group(0)}")] = new_id
        if code:
            self.key_to_id[(table_name, cc, f"code:{kind}:{code}")] = new_id
        if name_ja:
            self.key_to_id[(table_name, cc, f"name_ja:{kind}:{name_ja}")] = new_id
        if name_local:
            self.key_to_id[(table_name, cc, f"name_local:{kind}:{name_local}")] = new_id

        return new_id, True

    def fix_exploration_logs_ids(self):
        """
        過去の探索ログ (exploration_logs.csv) に残る5桁ID等を6桁IDに修復
        """
        log_file = os.path.join(self.master_dir, "exploration_logs.csv")
        if not os.path.exists(log_file):
            return

        df = pd.read_csv(log_file, encoding='utf-8', keep_default_na=False, dtype=str)
        if len(df) == 0:
            return

        def expand_id(val):
            # 例: JP-RT-00001 -> JP-RT-000001, JP-ND-00001 -> JP-ND-000001
            def repl(m):
                cc = m.group(1)
                kind = m.group(2)
                num = int(m.group(3))
                return f"{cc}-{kind}-{num:06d}"
            return re.sub(r"([A-Z]+)-([A-Z]+)-(\d{1,5})\b", repl, str(val))

        for col in ['log_id', '対象路線_ids', '対象拠点_ids', '対象自治体_ids']:
            if col in df.columns:
                df[col] = df[col].apply(expand_id)

        df.to_csv(log_file, index=False, encoding='utf-8')
        print(f"探索ログのIDを6桁に修復しました: {log_file}")

    def save_merged_master(self, table_name, df_new_records, country_code='JP', target_types=None, target_route_ids=None):
        """
        他分野・他国・他路線のレコードを完全に保持したまま、今回の収集対象レコードのみを安全に差し替えて保存する。
        """
        csv_file = os.path.join(self.master_dir, f"{table_name}.csv")
        id_col = self.ID_COL_MAP.get(table_name)

        if os.path.exists(csv_file):
            df_old = pd.read_csv(csv_file, encoding='utf-8', keep_default_na=False, dtype=str)
            if table_name == 'route_nodes' and target_route_ids:
                # 対象路線以外のリンクデータを保持
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
        # ID重複がないか安全確認（万が一重複があれば重複排除）
        if id_col in df_final.columns:
            dups = df_final[df_final.duplicated(id_col, keep=False)]
            if len(dups) > 0:
                print(f"[警告] {table_name}.csv 保存時に {len(dups)} 件のID重複を検知。重複を排除します。")
                df_final = df_final.drop_duplicates(subset=[id_col], keep='last')

        df_final.to_csv(csv_file, index=False, encoding='utf-8')
        self.existing_records[table_name] = df_final
        print(f"マスタ安全保存完了: {csv_file} (今回の対象: {len(df_new_records)} 件, 全体: {len(df_final)} 件)")
        return df_final
