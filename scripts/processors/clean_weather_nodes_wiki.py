# -*- coding: utf-8 -*-
"""
気象観測地点（アメダス等）のWikipedia_urlクリアスクリプト
仕様: 気象観測地点についてはWikipediaURLは追加しない
対象: data/master/nodes.csv および data/staging/JP/nodes.csv
"""

import os
import sys
import csv
import shutil

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER_NODES_PATH = os.path.join(PROJECT_ROOT, "data", "master", "nodes.csv")
STAGING_NODES_PATH = os.path.join(PROJECT_ROOT, "data", "staging", "JP", "nodes.csv")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "data", "backup", "20261031_weather_wiki_clean")


def clean_file(path, label):
    if not os.path.exists(path):
        print(f"スキップ（ファイルなし）: {path}")
        return 0, 0

    # バックアップ
    os.makedirs(BACKUP_DIR, exist_ok=True)
    fname = os.path.basename(path)
    bak_path = os.path.join(BACKUP_DIR, f"{label}_{fname}")
    shutil.copy2(path, bak_path)
    print(f"[{label}] バックアップ作成: {bak_path}")

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    cleaned_count = 0
    total_weather = 0

    for r in rows:
        cat = r.get("大分類", "")
        kind = r.get("種別", "")
        name = r.get("名称", "")

        is_weather = (
            cat == "気象"
            or "アメダス" in kind
            or "気象" in kind
            or "観測" in kind
            or "アメダス" in name
        )

        if is_weather:
            total_weather += 1
            # Wikipedia_url のクリア
            if r.get("Wikipedia_url"):
                r["Wikipedia_url"] = ""
                cleaned_count += 1
            # 旧カラム名互換があればそれもクリア
            if "Wikipedia_ja" in r and r.get("Wikipedia_ja"):
                r["Wikipedia_ja"] = ""
            if "Wikidata_id" in r and r.get("Wikidata_id") == "Q296238":
                r["Wikidata_id"] = ""

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{label}] 気象ノード: {total_weather} 件中 {cleaned_count} 件のWikipedia_urlをクリアしました。")
    return total_weather, cleaned_count


def main():
    print("=" * 60)
    print("気象観測地点（アメダス）Wikipedia_url 削除処理開始")
    print("=" * 60)

    clean_file(MASTER_NODES_PATH, "master")
    clean_file(STAGING_NODES_PATH, "staging")

    print("=" * 60)
    print("気象観測地点のWikipedia_url削除が正常に完了しました。")
    print("=" * 60)


if __name__ == "__main__":
    main()
