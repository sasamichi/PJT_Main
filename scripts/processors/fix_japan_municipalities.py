# -*- coding: utf-8 -*-
"""
日本自治体データ（都道府県・市町村・政令区・郡）座標・公式サイトURL補完スクリプト
1. 都道府県（47件）の代表座標（本庁舎）および公式サイトURLの補完
2. 政令指定都市（20市）の本庁舎座標および公式サイトURLの補完
3. 欠損市町村（22市町村＋浜松市新3区）の本庁舎座標および公式サイトURLの補完
4. 北方領土（6村）の地理的代表座標および備考付与
5. 郡（JP_ADMIN_GUN、373件）の代表緯度・代表経度の全件クリア（空欄化）
6. 全市区町村（1,741市区町村）の公式サイトURLの一括マッピング
"""

import os
import sys
import csv
import shutil
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MUNI_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "master", "municipalities.csv")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "data", "backup", "20261031_muni_coords_urls")
URLS_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "JP", "localgov_jp_urls.csv")

# 47都道府県の確定データ
PREF_DATA = {
    "010006": {"lat": "43.064312", "lon": "141.346853", "url": "https://www.pref.hokkaido.lg.jp/"},
    "020001": {"lat": "40.824440", "lon": "140.739998", "url": "https://www.pref.aomori.lg.jp/"},
    "030007": {"lat": "39.703619", "lon": "141.152684", "url": "https://www.pref.iwate.jp/"},
    "040002": {"lat": "38.268839", "lon": "140.872103", "url": "https://www.pref.miyagi.jp/"},
    "050008": {"lat": "39.718614", "lon": "140.102364", "url": "https://www.pref.akita.lg.jp/"},
    "060003": {"lat": "38.240437", "lon": "140.363632", "url": "https://www.pref.yamagata.jp/"},
    "070009": {"lat": "37.750299", "lon": "140.467551", "url": "https://www.pref.fukushima.lg.jp/"},
    "080004": {"lat": "36.341813", "lon": "140.446793", "url": "https://www.pref.ibaraki.jp/"},
    "090000": {"lat": "36.565863", "lon": "139.883569", "url": "https://www.pref.tochigi.lg.jp/"},
    "100005": {"lat": "36.391166", "lon": "139.060856", "url": "https://www.pref.gunma.jp/"},
    "110001": {"lat": "35.856999", "lon": "139.648933", "url": "https://www.pref.saitama.lg.jp/"},
    "120006": {"lat": "35.605058", "lon": "140.123308", "url": "https://www.pref.chiba.lg.jp/"},
    "130001": {"lat": "35.689506", "lon": "139.691700", "url": "https://www.metro.tokyo.lg.jp/"},
    "140007": {"lat": "35.447505", "lon": "139.642347", "url": "https://www.pref.kanagawa.jp/"},
    "150002": {"lat": "37.902552", "lon": "139.023095", "url": "https://www.pref.niigata.lg.jp/"},
    "160008": {"lat": "36.695291", "lon": "137.211338", "url": "https://www.pref.toyama.jp/"},
    "170003": {"lat": "36.594682", "lon": "136.625573", "url": "https://www.pref.ishikawa.lg.jp/"},
    "180009": {"lat": "36.065178", "lon": "136.221527", "url": "https://www.pref.fukui.lg.jp/"},
    "190004": {"lat": "35.664158", "lon": "138.568449", "url": "https://www.pref.yamanashi.jp/"},
    "200000": {"lat": "36.651299", "lon": "138.181224", "url": "https://www.pref.nagano.lg.jp/"},
    "210005": {"lat": "35.391227", "lon": "136.722291", "url": "https://www.pref.gifu.lg.jp/"},
    "220001": {"lat": "34.975562", "lon": "138.382760", "url": "https://www.pref.shizuoka.jp/"},
    "230006": {"lat": "35.180188", "lon": "136.906565", "url": "https://www.pref.aichi.jp/"},
    "240001": {"lat": "34.730283", "lon": "136.508591", "url": "https://www.pref.mie.lg.jp/"},
    "250007": {"lat": "35.004531", "lon": "135.868588", "url": "https://www.pref.shiga.lg.jp/"},
    "260002": {"lat": "35.021247", "lon": "135.755597", "url": "https://www.pref.kyoto.jp/"},
    "270008": {"lat": "34.686297", "lon": "135.519661", "url": "https://www.pref.osaka.lg.jp/"},
    "280003": {"lat": "34.691269", "lon": "135.183071", "url": "https://web.pref.hyogo.lg.jp/"},
    "290009": {"lat": "34.685333", "lon": "135.832742", "url": "https://www.pref.nara.jp/"},
    "300004": {"lat": "34.226034", "lon": "135.167506", "url": "https://www.pref.wakayama.lg.jp/"},
    "310000": {"lat": "35.503612", "lon": "134.238127", "url": "https://www.pref.tottori.lg.jp/"},
    "320005": {"lat": "35.472295", "lon": "133.050499", "url": "https://www.pref.shimane.lg.jp/"},
    "330001": {"lat": "34.661771", "lon": "133.935003", "url": "https://www.pref.okayama.jp/"},
    "340006": {"lat": "34.396560", "lon": "132.459622", "url": "https://www.pref.hiroshima.lg.jp/"},
    "350001": {"lat": "34.185884", "lon": "131.471387", "url": "https://www.pref.yamaguchi.lg.jp/"},
    "360007": {"lat": "34.065770", "lon": "134.559303", "url": "https://www.pref.tokushima.lg.jp/"},
    "370002": {"lat": "34.340156", "lon": "134.043444", "url": "https://www.pref.kagawa.lg.jp/"},
    "380008": {"lat": "33.841660", "lon": "132.766103", "url": "https://www.pref.ehime.jp/"},
    "390003": {"lat": "33.559705", "lon": "133.531080", "url": "https://www.pref.kochi.lg.jp/"},
    "400009": {"lat": "33.606785", "lon": "130.417957", "url": "https://www.pref.fukuoka.lg.jp/"},
    "410004": {"lat": "33.249442", "lon": "130.299793", "url": "https://www.pref.saga.lg.jp/"},
    "420000": {"lat": "32.744839", "lon": "129.873756", "url": "https://www.pref.nagasaki.jp/"},
    "430005": {"lat": "32.789828", "lon": "130.741667", "url": "https://www.pref.kumamoto.jp/"},
    "440001": {"lat": "33.238194", "lon": "131.612591", "url": "https://www.pref.oita.jp/"},
    "450006": {"lat": "31.911096", "lon": "131.423893", "url": "https://www.pref.miyazaki.lg.jp/"},
    "460001": {"lat": "31.560148", "lon": "130.557981", "url": "https://www.pref.kagoshima.jp/"},
    "470007": {"lat": "26.212401", "lon": "127.680932", "url": "https://www.pref.okinawa.lg.jp/"},
}

# 政令指定都市（20市）市役所本庁舎
DESIGNATED_CITIES = {
    "011002": {"lat": "43.061783", "lon": "141.354483", "url": "https://www.city.sapporo.jp/"},
    "041009": {"lat": "38.268222", "lon": "140.871028", "url": "https://www.city.sendai.jp/"},
    "111007": {"lat": "35.861722", "lon": "139.645472", "url": "https://www.city.saitama.lg.jp/"},
    "121002": {"lat": "35.607278", "lon": "140.106361", "url": "https://www.city.chiba.jp/"},
    "141003": {"lat": "35.444444", "lon": "139.638056", "url": "https://www.city.yokohama.lg.jp/"},
    "141305": {"lat": "35.530861", "lon": "139.702972", "url": "https://www.city.kawasaki.jp/"},
    "141500": {"lat": "35.571444", "lon": "139.373278", "url": "https://www.city.sagamihara.kanagawa.jp/"},
    "151009": {"lat": "37.916194", "lon": "139.036389", "url": "https://www.city.niigata.lg.jp/"},
    "221007": {"lat": "34.976944", "lon": "138.383056", "url": "https://www.city.shizuoka.lg.jp/"},
    "221309": {"lat": "34.710833", "lon": "137.726111", "url": "https://www.city.hamamatsu.shizuoka.jp/"},
    "231002": {"lat": "35.181444", "lon": "136.906417", "url": "https://www.city.nagoya.jp/"},
    "261009": {"lat": "35.011639", "lon": "135.768028", "url": "https://www.city.kyoto.lg.jp/"},
    "271004": {"lat": "34.693722", "lon": "135.502167", "url": "https://www.city.osaka.lg.jp/"},
    "271403": {"lat": "34.573333", "lon": "135.483056", "url": "https://www.city.sakai.lg.jp/"},
    "281000": {"lat": "34.690083", "lon": "135.195528", "url": "https://www.city.kobe.lg.jp/"},
    "331007": {"lat": "34.655139", "lon": "133.919556", "url": "https://www.city.okayama.jp/"},
    "341002": {"lat": "34.385278", "lon": "132.455278", "url": "https://www.city.hiroshima.lg.jp/"},
    "401005": {"lat": "33.883444", "lon": "130.875194", "url": "https://www.city.kitakyushu.lg.jp/"},
    "401307": {"lat": "33.590361", "lon": "130.401722", "url": "https://www.city.fukuoka.lg.jp/"},
    "431001": {"lat": "32.803194", "lon": "130.707889", "url": "https://www.city.kumamoto.jp/"},
}

# 欠損市町村・浜松市新3区・北方領土
SPECIFIC_MUNICIPALITIES = {
    "012041": {"lat": "43.770639", "lon": "142.364861", "url": "https://www.city.asahikawa.hokkaido.jp/"},
    "015598": {"lat": "44.180278", "lon": "143.593889", "url": "https://www.town.yubetsu.lg.jp/"},
    "016101": {"lat": "42.333333", "lon": "142.366667", "url": "https://www.town.shinhidaka.lg.jp/"},
    "052116": {"lat": "39.914167", "lon": "139.986667", "url": "https://www.city.katagami.lg.jp/"},
    "052159": {"lat": "39.601944", "lon": "140.564722", "url": "https://www.city.semboku.akita.jp/"},
    "075477": {"lat": "37.494722", "lon": "141.000833", "url": "https://www.town.namie.fukushima.jp/"},
    "075647": {"lat": "37.683056", "lon": "140.730556", "url": "https://www.vill.iitate.fukushima.jp/"},
    "092151": {"lat": "36.655278", "lon": "140.151111", "url": "https://www.city.nasukarasuyama.lg.jp/"},
    "204528": {"lat": "36.444722", "lon": "137.994722", "url": "https://www.vill.chikuhoku.lg.jp/"},
    "232343": {"lat": "35.248333", "lon": "136.871111", "url": "https://www.city.kitanagoya.lg.jp/"},
    "244724": {"lat": "34.331389", "lon": "136.666944", "url": "https://www.town.minamiise.mie.jp/"},
    "322067": {"lat": "35.432778", "lon": "133.253056", "url": "https://www.city.yasugi.shimane.jp/"},
    "325058": {"lat": "34.398056", "lon": "131.916111", "url": "https://www.town.yoshika.lg.jp/"},
    "463035": {"lat": "31.597500", "lon": "130.560833", "url": "https://mishimamura.com/", "note": "役場本庁舎は鹿児島市内に所在"},
    "463043": {"lat": "31.579167", "lon": "130.560000", "url": "https://www.tokara.jp/", "note": "役場本庁舎は鹿児島市内に所在"},
    "473812": {"lat": "24.338611", "lon": "124.156667", "url": "https://www.town.taketomi.lg.jp/", "note": "役場本庁舎は石垣市内に所在"},
    # 浜松市新3区（2024年再編）
    "221384": {"lat": "34.710833", "lon": "137.726111", "url": "https://www.city.hamamatsu.shizuoka.jp/c-shinko/index.html"},
    "221392": {"lat": "34.796389", "lon": "137.783611", "url": "https://www.city.hamamatsu.shizuoka.jp/hn-shinko/index.html"},
    "221406": {"lat": "34.876389", "lon": "137.820278", "url": "https://www.city.hamamatsu.shizuoka.jp/tn-shinko/index.html"},
    # 北方領土6村
    "016951": {"lat": "43.856944", "lon": "146.758333", "note": "現地庁舎なし（根室振興局等連絡窓口）"},
    "016969": {"lat": "43.693611", "lon": "145.503056", "note": "現地庁舎なし（根室振興局等連絡窓口）"},
    "016977": {"lat": "44.205278", "lon": "146.027222", "note": "現地庁舎なし（根室振興局等連絡窓口）"},
    "016985": {"lat": "44.881944", "lon": "147.545833", "note": "現地庁舎なし（根室振興局等連絡窓口）"},
    "016993": {"lat": "45.210000", "lon": "147.876389", "note": "現地庁舎なし（根室振興局等連絡窓口）"},
    "017001": {"lat": "45.526944", "lon": "148.868889", "note": "現地庁舎なし（根室振興局等連絡窓口）"},
}


def load_localgov_urls():
    url_dict = {}
    if not os.path.exists(URLS_CSV_PATH):
        return url_dict
    with open(URLS_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 5:
                pref = row[0].strip()
                muni = row[2].strip()
                url = row[4].strip()
                url_dict[f"{pref}_{muni}"] = url
                url_dict[muni] = url
    return url_dict


def main():
    print("=" * 60)
    print("日本自治体データ（座標・公式URL・郡座標削除）修復開始")
    print("=" * 60)

    # 1. バックアップ
    os.makedirs(BACKUP_DIR, exist_ok=True)
    bak_file = os.path.join(BACKUP_DIR, "municipalities.csv")
    shutil.copy2(MUNI_CSV_PATH, bak_file)
    print(f"✅ バックアップ保存完了: {bak_file}")

    # 2. URL辞書ロード
    url_dict = load_localgov_urls()
    print(f"✅ 全国市区町村URL辞書ロード完了: {len(url_dict)} 件")

    # 3. CSV読み込み
    with open(MUNI_CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # 親都道府県名の逆引きマップ作成
    pref_name_map = {}
    pref_url_map = {}
    city_url_map = {}
    for r in rows:
        if "PREF" in r.get("type_id", ""):
            pref_name_map[r["municipality_id"]] = r["名称"]
            pref_url_map[r["municipality_id"]] = r.get("公式サイトURL", "")
        if r.get("type_id") == "JP_ADMIN_CITY_DESIGNATED":
            city_url_map[r["municipality_id"]] = r.get("公式サイトURL", "")

    # 異体字辞書
    char_variants = {
        "檮原町": "梼原町", "梼原町": "檮原町",
        "須惠町": "須恵町", "須恵町": "須惠町",
        "かすみがうら市": "かすみがうら市",
    }

    updated_pref = 0
    updated_cities = 0
    cleared_gun = 0
    updated_urls = 0

    for r in rows:
        if r.get("country_code") != "JP":
            continue

        mid = r.get("municipality_id", "")
        tid = r.get("type_id", "")
        code = r.get("公的コード", "").strip()
        name = r.get("名称", "").strip()
        parent_id = r.get("親自治体ID", "")
        pref_name = pref_name_map.get(parent_id, "")

        # A. 郡（JP_ADMIN_GUN）の座標をすべてクリア（削除）
        if tid == "JP_ADMIN_GUN":
            if r.get("代表緯度") or r.get("代表経度"):
                r["代表緯度"] = ""
                r["代表経度"] = ""
                cleared_gun += 1

        # B. 都道府県（47件）の座標・URL投入
        if code in PREF_DATA:
            p = PREF_DATA[code]
            r["代表緯度"] = p["lat"]
            r["代表経度"] = p["lon"]
            r["公式サイトURL"] = p["url"]
            updated_pref += 1

        # C. 政令指定都市（20市）の本庁舎座標・URL投入
        elif code in DESIGNATED_CITIES:
            d = DESIGNATED_CITIES[code]
            r["代表緯度"] = d["lat"]
            r["代表経度"] = d["lon"]
            r["公式サイトURL"] = d["url"]
            updated_cities += 1

        # D. 欠損市町村・浜松市新3区・北方領土の反映
        elif code in SPECIFIC_MUNICIPALITIES:
            s = SPECIFIC_MUNICIPALITIES[code]
            if "lat" in s:
                r["代表緯度"] = s["lat"]
            if "lon" in s:
                r["代表経度"] = s["lon"]
                updated_cities += 1
            if "url" in s:
                r["公式サイトURL"] = s["url"]
            if "note" in s:
                ex_note = r.get("備考", "")
                r["備考"] = f"{ex_note}; {s['note']}".strip("; ") if ex_note else s["note"]

        # E. 一般市区町村の公式サイトURL自動補完
        if not r.get("公式サイトURL") and tid != "JP_ADMIN_GUN":
            lookup_key = f"{pref_name}_{name}"
            v_name = char_variants.get(name, "")
            v_lookup_key = f"{pref_name}_{v_name}" if v_name else ""

            if lookup_key in url_dict:
                r["公式サイトURL"] = url_dict[lookup_key]
                updated_urls += 1
            elif v_lookup_key and v_lookup_key in url_dict:
                r["公式サイトURL"] = url_dict[v_lookup_key]
                updated_urls += 1
            elif name in url_dict:
                r["公式サイトURL"] = url_dict[name]
                updated_urls += 1
            elif v_name and v_name in url_dict:
                r["公式サイトURL"] = url_dict[v_name]
                updated_urls += 1
            # 行政区（WARD）の場合、親政令市の公式URLをフォールバック設定
            elif tid == "JP_ADMIN_WARD" and parent_id in city_url_map:
                r["公式サイトURL"] = city_url_map[parent_id]
                updated_urls += 1

    # 4. CSV保存
    with open(MUNI_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("==========================================")
    print("🎉 自治体データ修復処理が完了しました！")
    print(f" - 都道府県（47件）座標・URL更新: {updated_pref} 件")
    print(f" - 市役所・役場本庁舎 座標更新: {updated_cities} 件")
    print(f" - 郡（GUN）の座標クリア（空欄化）: {cleared_gun} 件")
    print(f" - 市区町村 公式サイトURL追加: {updated_urls} 件")
    print("==========================================")


if __name__ == "__main__":
    main()
