# -*- coding: utf-8 -*-
"""
国・制度インフラガイド（📘 制度・インフラ解説）生成スクリプト
---------------------------------------------------------------
docs/research/*_制度調査.md から、一般公開用Webサイト向けの
制度・インフラ解説データを抽出し、構造化JSONとして出力・反映する。

【完全除外項目】:
- type_id, source_id 等の内部管理コード
- 初期自動収集フラグ（〇/×）
- OSMタグ対応表 (highway=motorway, admin_level 等)
- Wikidataプロパティ番号 (Pコード, Qコード, SPARQLクエリ)
- Overpass QLクエリ
- data_sources.csv 用の検証ステータスや内部フラグ
"""

import os
import sys
import re
import json
import glob

# UTF-8入出力設定
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(BASE_DIR, "docs", "research")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "web", "public", "data")
GUIDES_OUTPUT_DIR = os.path.join(PUBLIC_DATA_DIR, "guides")

COUNTRIES = ["JP", "AT", "TW", "KR", "CH", "IT"]

COUNTRY_NAMES = {
    "JP": "日本",
    "AT": "オーストリア",
    "TW": "台湾",
    "KR": "大韓民国",
    "CH": "スイス",
    "IT": "イタリア",
}

COUNTRY_FLAGS = {
    "JP": "🇯🇵",
    "AT": "🇦🇹",
    "TW": "🇹🇼",
    "KR": "🇰🇷",
    "CH": "🇨🇭",
    "IT": "🇮🇹",
}


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def sanitize_public_text(text):
    """一般公開向けに内部コード・OSMタグ・管理用語を除去"""
    if not text:
        return ""
    # OSMタグ言及の除去（例: OSMでは admin_level=5 にマッピング。等）
    text = re.sub(r"[\(（]?\s*OSM[^\)）\n]*?(?:admin_level|highway|railway)[^\)）\n]*?[\)）]?", "", text)
    text = re.sub(r"OSM[ではに][^\n。]*?[。]", "", text)
    text = re.sub(r"admin_level\s*=\s*\d+", "", text)
    text = re.sub(r"highway\s*=\s*[a-z_]+", "", text)
    text = re.sub(r"railway\s*=\s*[a-z_]+", "", text)
    text = re.sub(r"type_id", "", text)
    text = re.sub(r"source_id", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_section_text(content, start_pattern, end_patterns):
    start_match = re.search(start_pattern, content)
    if not start_match:
        return ""
    start_pos = start_match.end()

    end_pos = len(content)
    for ep in end_patterns:
        m = re.search(ep, content[start_pos:])
        if m:
            pos = start_pos + m.start()
            if pos < end_pos:
                end_pos = pos

    return content[start_pos:end_pos].strip()


def parse_bullets_flexible(text):
    items = {}
    current_key = None
    current_val = []

    for line in text.splitlines():
        line_s = line.strip()
        m = re.match(r"^-\s*(?:\*\*)?([^*\n:：]+?)(?:\*\*)?[:：]\s*(.*)", line_s)
        if m:
            if current_key:
                items[current_key] = clean_text(" ".join(current_val))
            current_key = clean_text(m.group(1))
            val = clean_text(m.group(2))
            current_val = [val] if val else []
        elif current_key and line_s:
            if line_s.startswith("- ") or line_s.startswith("* "):
                current_val.append("\n• " + line_s[2:].strip())
            else:
                current_val.append(line_s)

    if current_key:
        items[current_key] = clean_text(" ".join(current_val))
    return items


def parse_md_table(table_text):
    lines = [l.strip() for l in table_text.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return []
    headers = [clean_text(c) for c in lines[0].split("|")[1:-1]]
    rows = []
    for line in lines[2:]:
        cols = [clean_text(c) for c in line.split("|")[1:-1]]
        if len(cols) == len(headers):
            rows.append(dict(zip(headers, cols)))
    return rows


def parse_links_from_text(text, default_category="公式情報源"):
    links = []
    # 括弧URLパターン: 名称（https://...）または `https://...`
    # パターン1: - [名称](URL)
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^\)]+)\)", text):
        links.append({
            "category": default_category,
            "name": clean_text(m.group(1)),
            "url": clean_text(m.group(2))
        })
    # パターン2: 名称（`?https?://...`?）
    for m in re.finditer(r"([^\n（、*]+?)[（\(]\s*`?(https?://[^\s`\)]+?)`?\s*[）\)]", text):
        name = clean_text(m.group(1)).lstrip("- *").strip()
        url = clean_text(m.group(2))
        if name and not any(l["url"] == url for l in links):
            links.append({
                "category": default_category,
                "name": name,
                "url": url
            })
    # パターン3: - 名称: `https://...`
    for m in re.finditer(r"^[-*]\s*([^:`\n]+)[:：]\s*`?(https?://[^\s`\)]+)`?", text, re.MULTILINE):
        name = clean_text(m.group(1))
        url = clean_text(m.group(2))
        if name and not any(l["url"] == url for l in links):
            links.append({
                "category": default_category,
                "name": name,
                "url": url
            })
    return links


def build_jp_guide(admin_txt, transit_txt):
    """日本のガイド構築"""
    # 1. 基本情報
    s1 = extract_section_text(admin_txt, r"## 1\.\s*対象国基本情報[^\n]*\n", [r"## 2\."])
    b1 = parse_bullets_flexible(s1)

    basic_info = {
        "official_name": "日本国",
        "native_name": "日本国（にほんこく、にっぽんこく） / Japan",
        "government_type": b1.get("国家体制", "単一国家（立憲君主制・議院内閣制）。都道府県（47団体）と市町村（1,718団体）の二層制に加え、特別区（23区）および政令市の行政区（170区）が設置されている。"),
        "official_languages": b1.get("公用語（地域的公認言語を含む）", "事実上の公用語は日本語。アイヌ語（先住民族言語）や琉球諸語が存在する。"),
        "territory_bbox": "本土5島および全離島を含む法定全域。最北端：択捉島カモイワッカ岬、最南端：沖ノ鳥島、最西端：与那国島、最東端：南鳥島。",
        "special_regions": b1.get("飛び地・海外領土・特殊行政区域", "海外領土や自治領は存在せず、全領土が47都道府県に直接編入。北方領土、竹島、尖閣諸島などの地理的・領土的境界管理が存在する。")
    }

    # 2. 行政階層
    s2 = extract_section_text(admin_txt, r"### 2\.1\s*行政[^\n]*\n", [r"### 2\.2"])
    t2 = parse_md_table(s2)
    admin_levels = []
    for r in t2:
        if "行政" in r.get("大分類", ""):
            admin_levels.append({
                "level": r.get("階層レベル", ""),
                "name_ja": r.get("種別名_日本語", ""),
                "name_local": r.get("種別名_公用語", ""),
                "scale": r.get("規模目安(件数)", ""),
                "description": sanitize_public_text(r.get("法的根拠・自治権の有無・説明", ""))
            })

    admin_hierarchy = {
        "summary": "地方自治法に基づく広域普通地方公共団体（都道府県）と基礎自治体（市町村）の重層的二層制。大都市制度として政令指定都市（20市）、中核市（62市）、施行時特例市（23市）の権限移譲体系が整備されている。",
        "levels": admin_levels
    }

    # 3. 気象
    weather_system = {
        "agency_name": "気象庁 (Japan Meteorological Agency / JMA)",
        "agency_url": "https://www.jma.go.jp/",
        "agency_desc": "国土交通省の外局。全国の気象観測、地震・津波監視、防災気象情報の発表を一元管理する。",
        "forecast_zones": [
            {"level_name": "地方予報区 (centers)", "scale": "11ブロック", "description": "北海道、東北、関東甲信、東海、北陸、近畿、中国、四国、九州北部、九州南部・奄美、沖縄の広域ブロック。"},
            {"level_name": "府県予報区 (offices)", "scale": "58区域", "description": "各地方気象台等の管轄および天気予報・警報の配信単位。北海道（8区）、鹿児島（2区）、沖縄（4区）を細分。"},
            {"level_name": "一次細分区域 (class10s)", "scale": "142区域", "description": "府県予報区を気候・地形により2〜4分割した府県天気予報の基本発表単位。"},
            {"level_name": "二次細分区域 (class20s)", "scale": "1,805区域", "description": "気象特別警報・警報・注意報の最小発令単位。原則として市区町村単位で設定。"}
        ],
        "marine_zones": "全般海上予報区（11海域）、地方海上予報区（37海域）、津波予報区（全国沿岸66区域）",
        "observation_network": {
            "network_name": "地域気象観測システム（アメダス / AMeDAS）および地上気象観測網",
            "stations_scale": "約1,300か所（官署約150か所、アメダス四要素約840か所、積雪約330か所）",
            "description": "全国平均約17km間隔で配置。降水量、気温、風向風速、日照時間、積雪深（豪雪地帯）を10分間隔で自動観測。"
        }
    }

    # 4. 交通インフラ体系
    s_road = extract_section_text(transit_txt, r"## 1\.\s*道路網制度の詳細分類[^\n]*\n", [r"## 2\."])
    t_road = parse_md_table(s_road)
    clean_road = []
    for r in t_road:
        clean_road.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語相当", ""),
            "name_local": r.get("中分類・法的名称（公用語）", ""),
            "law": r.get("根拠法律", ""),
            "manager": r.get("管理主体", ""),
            "scale": r.get("全体規模目安", "")
        })

    s_rail = extract_section_text(transit_txt, r"## 2\.\s*鉄軌道[・都市交通]*・索道制度の詳細分類[^\n]*\n", [r"## 3\."])
    t_rail = parse_md_table(s_rail)
    clean_rail = []
    for r in t_rail:
        clean_rail.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語・技術分類", ""),
            "name_local": r.get("法的種別（公用語）", ""),
            "law": r.get("根拠法律・条文", ""),
            "lines_or_cities": r.get("主な運行都市・対象路線例", "")
        })

    t_op = parse_md_table(extract_section_text(transit_txt, r"### 2\.2\s*主要鉄道事業者[^\n]*\n", [r"### 2\.3", r"## 3\."]))
    clean_op = []
    for r in t_op[:12]:
        clean_op.append({
            "name": r.get("事業者名（公式名称）", "") or r.get("事業者名", ""),
            "role": r.get("種別・法的役割", ""),
            "lines": r.get("主な運行・保有路線", "")
        })

    transit_system = {
        "road": {
            "summary": "道路法に基づく高速自動車国道、一般国道、都道府県道、市町村道の4種別体系。高速道路はNEXCO3社・本四高速・都市高速道路公社等が管理。",
            "classifications": clean_road,
            "numbering_rules": "高速道路ナンバリング（E1東名・名神、E2山陽等、並行国道番号に準拠。環状線はC3、C4等）。一般国道は1〜58号および101〜507号（59〜100号等は欠番）。主要地方道は1〜2桁、一般県道は3桁付番。",
            "management_notes": "一般国道は国直轄の「指定区間（約24,000km）」と都道府県・政令市管理の「指定区間外（約32,000km）」に分かれる。"
        },
        "railway": {
            "summary": "全国新幹線鉄道整備法、鉄道事業法、軌道法に基づく法体系。JR旅客6社・貨物1社、大手民鉄16社、地下鉄公営・民営、地方鉄道、路面電車・LRT、モノレール、新交通（AGT）、索道（ロープウェイ・リフト）が網羅されている。",
            "classifications": clean_rail,
            "special_transit_notes": "道路敷地に敷設されたモノレール・新交通は軌道法、専用用地は鉄道事業法が適用される。立山トンネル無軌条電車（トロリーバス）は電気バス転換に伴い現役0路線となった。",
            "major_operators": clean_op
        },
        "bus": {
            "summary": "道路運送法に基づく一般乗合旅客自動車運送事業（路線バス・高速バス・コミュニティバス）。標準的なバス情報フォーマット（GTFS-JP）によるオープンデータ化が全国で急速に進展している。"
        },
        "maritime": {
            "summary": "海上運送法に基づく一般旅客定期航路事業。離島航路、長距離カーフェリー（本州〜北海道・九州・四国）、東京湾・伊勢湾・瀬戸内海等の短距離フェリー網が発達。"
        },
        "aviation": {
            "summary": "航空法および空港法に基づく拠点空港（国管理空港・会社管理空港・特定地方管理空港）と地方管理空港。羽田・成田・関西・伊丹・新千歳・福岡・那覇等の大拠点を軸に高密度の国内幹線・離島生活航空路網が形成されている。"
        }
    }


    # 6. 公式ポータルリンク
    portals = [
        {"category": "行政・自治体", "name": "総務省 全国地方公共団体コード", "url": "https://www.soumu.go.jp/denshijiti/code.html", "description": "公式自治体コード一覧台帳"},
        {"category": "行政・自治体", "name": "デジタル庁 アドレス・ベース・レジストリ", "url": "https://dataset.address-br.digital.go.jp/", "description": "町字・街区・住居表示公的マスター"},
        {"category": "地図・GIS", "name": "国土地理院 地理院地図", "url": "https://maps.gsi.go.jp/", "description": "日本公式Web GIS・基盤地図情報・航空写真"},
        {"category": "地図・GIS", "name": "国土交通省 国土数値情報", "url": "https://nlftp.mlit.go.jp/ksj/", "description": "行政区域・鉄道・道路・施設等の国家GISオープンデータ"},
        {"category": "地図・GIS", "name": "国土交通省 Project PLATEAU", "url": "https://www.plateauview.mlit.go.jp/", "description": "全国3D都市モデルポータル"},
        {"category": "統計", "name": "総務省統計局 e-Stat（政府統計ポータル）", "url": "https://www.e-stat.go.jp/gis", "description": "国勢調査小地域・メッシュ統計GISデータ"},
        {"category": "気象", "name": "気象庁 公式ホームページ", "url": "https://www.jma.go.jp/", "description": "天気予報・防災気象情報・アメダスリアルタイム観測"},
        {"category": "気象", "name": "気象庁 アメダス地点マスターJSON", "url": "https://www.jma.go.jp/bosai/amedas/const/amedastable.json", "description": "全国気象観測所定義データ"}
    ]

    return {
        "country_code": "JP",
        "name": "日本",
        "flag": "🇯🇵",
        "basic_info": basic_info,
        "admin_hierarchy": admin_hierarchy,
        "weather_system": weather_system,
        "transit_system": transit_system,
        "official_portals": portals
    }


def build_at_guide(admin_txt, transit_txt):
    """オーストリアのガイド構築"""
    s1 = extract_section_text(admin_txt, r"## 1\.\s*対象国基本情報[^\n]*\n", [r"## 2\."])
    b1 = parse_bullets_flexible(s1)

    basic_info = {
        "official_name": "オーストリア共和国",
        "native_name": "Republik Österreich / Republic of Austria",
        "government_type": b1.get("国家体制", "連邦共和制。9つの連邦州（Bundesländer）、79の政治地区（郡）および15の憲章都市（計94地区）、全2,092の基礎自治体（Gemeinde）から構成される。首都ウィーンは州・地区・市の3つの地位を兼ねる。"),
        "official_languages": b1.get("公用語（地域的公認言語を含む）", "連邦公用語はドイツ語。地域的公認言語としてブルゲンラント・クロアチア語、ハンガリー語、スロベニア語、チェコ語、スロバキア語、ロマ語が公認されている。"),
        "territory_bbox": "アルプス東部に位置する内陸国（面積83,894 km²）。緯度: 46.37°N〜49.04°N、経度: 9.48°E〜17.16°E。",
        "special_regions": b1.get("飛び地・海外領土・特殊行政区域", "海外領土なし。地理的準飛び地としてユングホルツ（ドイツ側にのみ開く）、ミッテルベルク（クラインヴァルサータール）、および国内州間飛地の東チロル（リエンツ郡）が存在する。")
    }

    s2 = extract_section_text(admin_txt, r"### 2\.1\s*行政[^\n]*\n", [r"### 2\.2"])
    t2 = parse_md_table(s2)
    admin_levels = []
    for r in t2:
        if "行政" in r.get("大分類", ""):
            admin_levels.append({
                "level": r.get("階層レベル", ""),
                "name_ja": r.get("種別名_日本語", ""),
                "name_local": r.get("種別名_公用語", ""),
                "scale": r.get("規模目安(件数)", ""),
                "description": sanitize_public_text(r.get("法的根拠・自治権の有無・説明", ""))
            })

    admin_hierarchy = {
        "summary": "連邦憲法（B-VG）に基づく連邦州（9州）、政治地区（79郡＋15憲章都市＝94地区）、基礎自治体（2,092市町村）の3層構造。憲章都市（Statutarstadt）は基礎自治体と郡行政の機能を併せ持つ。",
        "levels": admin_levels
    }

    weather_system = {
        "agency_name": "オーストリア国立地質・地球物理・気候・気象研究所 (GeoSphere Austria)",
        "agency_url": "https://www.geosphere.at/",
        "agency_desc": "連邦教育・科学・研究省所管の研究機関。旧中央気象地球物理研究所（ZAMG）と連邦地質研究所（GBA）が2023年に統合発足したオーストリアの国家気象機関。",
        "forecast_zones": [
            {"level_name": "連邦州予報区 (Bundesland)", "scale": "9州", "description": "広域天気予報の第1階層単位。"},
            {"level_name": "政治地区予報区 (Bezirke)", "scale": "94地区", "description": "気象警報・防災情報の中間発表単位。"},
            {"level_name": "基礎自治体局地予報 (Gemeinde)", "scale": "2,092自治体", "description": "市町村ピンポイント予報の配信単位。"}
        ],
        "marine_zones": "内陸国のため海洋予報区なし（主要湖沼ボーデン湖・ノイジードル湖等の突風警報網を運用）。",
        "observation_network": {
            "network_name": "半自動気象観測網（TAWES: Teilautomatisches Wetterstationsnetz）",
            "stations_scale": "約270〜280地点（全国自動観測所）",
            "description": "気温・気圧・湿度・風向風速・降水量・日照時間を10分間隔で自動計測・オープンデータ配信（GeoSphere Austria Data Hub）。"
        }
    }

    s_road = extract_section_text(transit_txt, r"## 1\.\s*道路網制度の詳細分類[^\n]*\n", [r"## 2\."])
    t_road = parse_md_table(s_road)
    clean_road = []
    for r in t_road:
        clean_road.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語相当", ""),
            "name_local": r.get("中分類・法的名称（公用語）", ""),
            "law": r.get("根拠法律", ""),
            "manager": r.get("管理主体", ""),
            "scale": r.get("全体規模目安", "")
        })

    s_rail = extract_section_text(transit_txt, r"## 2\.\s*鉄軌道[・都市交通]*・索道制度の詳細分類[^\n]*\n", [r"## 3\."])
    t_rail = parse_md_table(s_rail)
    clean_rail = []
    for r in t_rail:
        clean_rail.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語・技術分類", ""),
            "name_local": r.get("法的種別（公用語）", ""),
            "law": r.get("根拠法律・条文", ""),
            "lines_or_cities": r.get("主な運行都市・対象路線例", "")
        })

    t_op = parse_md_table(extract_section_text(transit_txt, r"### 2\.2\s*主要鉄道事業者[^\n]*\n", [r"### 2\.3", r"## 3\."]))
    clean_op = []
    for r in t_op:
        clean_op.append({
            "name": r.get("事業者名（公式名称）", "") or r.get("事業者名", ""),
            "role": r.get("種別・法的役割", ""),
            "lines": r.get("主な運行・保有路線", "")
        })

    transit_system = {
        "road": {
            "summary": "連邦道路法に基づくアウトバーン（A路線）、高速道路（S路線）、連邦州道路（B路線・L路線）、自治体道の体系。高速道路インフラは国有公社ASFINAGが一元管理・料金徴収（ヴィニエット・GO-Box）。",
            "classifications": clean_road,
            "numbering_rules": "アウトバーンはA1〜A26、高速道路はS1〜S37。主要地方道路はB路線（B1〜B320）、州道はL路線（L1〜）。欧州自動車道路（E-routes）のE45, E55, E60等が重複指定。",
            "management_notes": "高規格幹線道路（A/S路線 約2,250km）はASFINAGが管理。旧連邦道路B路線は連邦州に移管され州が管理。"
        },
        "railway": {
            "summary": "鉄道法（Eisenbahngesetz）に基づく幹線鉄道、支線鉄道、トラム・路面電車、地下鉄（ウィーンU-Bahn）、索道。連邦鉄道ÖBBが全国の主要幹線・高速列車Railjetを運行。",
            "classifications": clean_rail,
            "special_transit_notes": "山岳アルプス地域における交走式ロープウェイ・循環式ゴンドラリフト（索道：Seilbahn）が発達し、索道法に基づき厳格に法制化されている。",
            "major_operators": clean_op
        },
        "bus": {
            "summary": "連邦鉄道傘下のオーストリア郵便バス（Postbus）および各地域交通連合（VOR, OÖVV, SVV等）による統合運行。全国一括乗り放題の「Klimaticket（気候チケット）」が全土で導入されている。"
        },
        "maritime": {
            "summary": "ドナウ川の水上交通（ウィーン〜ブラチスラヴァを結ぶTwin City Liner等）および主要山岳湖沼（ヴォルフガング湖、アッター湖、ボーデン湖等）の観光定期船運航。"
        },
        "aviation": {
            "summary": "ウィーン国際空港（VIE）を最大ハブとし、グラーツ、リンツ、ザルツブルク、インスブルック、クラーゲンフルトの計6国際空港が機能。オーストリア航空（Lufthansaグループ）が基幹路線を運航。"
        }
    }


    portals = [
        {"category": "行政・統計", "name": "オーストリア統計局 (Statistik Austria)", "url": "https://www.statistik.at/", "description": "地域区分・自治体台帳・国勢調査区オープンデータ"},
        {"category": "行政・統計", "name": "オーストリア政府総合オープンデータ (data.gv.at)", "url": "https://www.data.gv.at/", "description": "連邦・州・自治体横断のオープンデータカタログ"},
        {"category": "地図・GIS", "name": "公式背景地図 basemap.at", "url": "https://basemap.at/", "description": "連邦・全9州共同のオープン背景地図タイルサービス"},
        {"category": "地図・GIS", "name": "連邦計量・測量局 (BEV)", "url": "https://kataster.bev.gv.at/", "description": "公式地籍図・行政境界（VGD）・標高データ"},
        {"category": "気象", "name": "GeoSphere Austria Data Hub", "url": "https://data.hub.geosphere.at/", "description": "TAWES観測データ・気候値・気象警報オープンデータ"},
        {"category": "交通", "name": "ASFINAG 高速道路インフラ公社", "url": "https://www.asfinag.at/", "description": "高速道路網・交通流・料金体系情報"},
        {"category": "交通", "name": "オーストリア連邦鉄道 (ÖBB)", "url": "https://www.oebb.at/", "description": "全国鉄軌道時刻表・路線網"}
    ]

    return {
        "country_code": "AT",
        "name": "オーストリア",
        "flag": "🇦🇹",
        "basic_info": basic_info,
        "admin_hierarchy": admin_hierarchy,
        "weather_system": weather_system,
        "transit_system": transit_system,
        "official_portals": portals
    }


def build_tw_guide(admin_txt, transit_txt):
    """台湾のガイド構築"""
    s1 = extract_section_text(admin_txt, r"## 1\.\s*対象国基本情報[^\n]*\n", [r"## 2\."])
    b1 = parse_bullets_flexible(s1)

    basic_info = {
        "official_name": "中華民国（台湾）",
        "native_name": "中華民國（臺灣） / Taiwan (Republic of China)",
        "government_type": b1.get("国家体制", "単一国家（民主共和国）。地方制度法に基づき、第1階層の直轄市（6市）、省轄市（3市）、県（13県）の計22団体の広域自治体と、第2階層の郷・鎮・県轄市・区（368郷鎮市区）から構成される。"),
        "official_languages": b1.get("公用語（地域的公認言語を含む）", "国語（標準華語・繁体字中国語）。国家言語発展法に基づき台湾語（台湾閩南語）、客家語、台湾原住民族諸語、馬祖語、台湾手話が国家言語として法的に平等に保障されている。"),
        "territory_bbox": "台湾本島および周辺管轄離島（澎湖諸島、金門島、馬祖列島、緑島、蘭嶼、小琉球、東沙群島、太平島）。標準GIS範囲: 緯度 21.89°N〜26.38°N、経度 118.20°E〜122.01°E。",
        "special_regions": b1.get("飛び地・海外領土・特殊行政区域", "海外領土なし。中国大陸沿岸に位置する金門県・連江県（馬祖）の実効支配地域、南シナ海の東沙諸島・南沙諸島太平島（高雄市旗津区管轄）、および55の原住民族地区が特殊区域として指定されている。")
    }

    s2 = extract_section_text(admin_txt, r"### 2\.1\s*行政[^\n]*\n", [r"### 2\.2"])
    t2 = parse_md_table(s2)
    admin_levels = []
    for r in t2:
        if "行政" in r.get("大分類", ""):
            admin_levels.append({
                "level": r.get("階層レベル", ""),
                "name_ja": r.get("種別名_日本語", ""),
                "name_local": r.get("種別名_公用語", ""),
                "scale": r.get("規模目安(件数)", "") or r.get("規模目安", ""),
                "description": sanitize_public_text(r.get("法的根拠・自治権の有無・説明", "")) or r.get("説明", "")
            })

    admin_hierarchy = {
        "summary": "地方制度法に基づく二層制自治体系。広域自治体として六都（台北・新北・桃園・台中・台南・高雄）の直轄市、3市（基隆・新竹・嘉義）、13県が存在。下位に368の郷鎮市区、さらに村里（約7,748）が置かれる。",
        "levels": admin_levels
    }

    weather_system = {
        "agency_name": "交通部中央気象署 (Central Weather Administration / CWA)",
        "agency_url": "https://www.cwa.gov.tw/",
        "agency_desc": "交通部直属の国家気象機関（2023年に中央気象局から中央気象署へ昇格改編）。気象予報・地震速報・台風警報・津波予報を統轄する。",
        "forecast_zones": [
            {"level_name": "第1階層（広域予報区）", "scale": "北部・中部・南部・東部・離島", "description": "広域の定時天気予報発表区分。"},
            {"level_name": "第2階層（県市予報区）", "scale": "22県市", "description": "大雨特報・豪雨特報・台風警報の基本発表区分。"},
            {"level_name": "第3階層（郷鎮市区局地予報）", "scale": "368郷鎮市区", "description": "市町村レベルのピンポイント予報および突風・雷雨即時情報の発表単位。"}
        ],
        "marine_zones": "近海漁業気象予報区（17海域）、遠洋漁業気象予報区・海上台風警報海面（23海域）",
        "observation_network": {
            "network_name": "署屬有人氣象站および自動氣象站網（郷鎮自動気象站）",
            "stations_scale": "約1,348站（有人27站、自動約600站、水利署等の雨量計合算）",
            "description": "全台368郷鎮市区すべてに自動気象観測所を配備し、気温・気圧・風速・雨量を10分値でオンライン公開。"
        }
    }

    s_road = extract_section_text(transit_txt, r"## 1\.\s*道路網制度の詳細分類[^\n]*\n", [r"## 2\."])
    t_road = parse_md_table(s_road)
    clean_road = []
    for r in t_road:
        clean_road.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語相当", ""),
            "name_local": r.get("中分類・法的名称（公用語）", ""),
            "law": r.get("根拠法律", ""),
            "manager": r.get("管理主体", ""),
            "scale": r.get("全体規模目安", "") or r.get("規模目安", "")
        })

    s_rail = extract_section_text(transit_txt, r"## 2\.\s*鉄軌道[・都市交通]*・索道制度の詳細分類[^\n]*\n", [r"## 3\."])
    t_rail = parse_md_table(s_rail)
    clean_rail = []
    for r in t_rail:
        clean_rail.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語・技術分類", ""),
            "name_local": r.get("法的種別（公用語）", ""),
            "law": r.get("根拠法律・条文", ""),
            "lines_or_cities": r.get("主な運行都市・対象路線例", "")
        })

    transit_system = {
        "road": {
            "summary": "公路法に基づく国道（高速公路）、省道（快速公路および一般省道）、市道・県道、区道・郷道の分類体系。交通部高速公路局が国道を、交通部公路局が省道を管理。",
            "classifications": clean_road,
            "numbering_rules": "国道は奇数が南北縦貫（国道1号・3号・5号等）、偶数が東西連絡（国道2号・4号等）。省道は快速公路に台61線・台64線等、一般省道に台1線・台9線等が付番される。市道・県道は3桁（101号線〜）。",
            "management_notes": "国道および省道は国直轄、市道・県道は直轄市または県が維持管理。"
        },
        "railway": {
            "summary": "鉄路法に基づく台湾高速鉄路（台湾高鉄：THSR）、国営台湾鉄路（台鉄：TR）、都市捷運（MRT：台北捷運、新北捷運、桃園捷運、台中捷運、高雄捷運）、ライトレール（高雄軽軌、淡海軽軌、安坑軽軌）、糖業鉄道、林業鉄道（阿里山林鉄）。",
            "classifications": clean_rail,
            "special_transit_notes": "猫空ロープウェイ（台北市）や日月潭ロープウェイ（南投県）等の観光旅客索道も運行されている。",
            "major_operators": [
                {"name": "国営台湾鉄路股份有限公司 (TRC)", "role": "国営鉄道", "lines": "西部幹線、東部幹線、南廻線、内湾線・平渓線・集集線等"},
                {"name": "台湾高速鉄路股份有限公司 (THSR)", "role": "高速鉄道", "lines": "南港〜左営（営業キロ350km）"},
                {"name": "台北大衆捷運股份有限公司 (TRTC)", "role": "都市地下鉄", "lines": "文湖線、淡水信義線、松山新店線、中和新蘆線、板南線"},
                {"name": "高雄捷運股份有限公司 (KRTC)", "role": "都市地下鉄・LRT", "lines": "紅線、橘線、高雄環状軽軌"}
            ]
        },
        "bus": {
            "summary": "公路客運（都市間高速・地方バス）および市区公車（都市路線バス）。交通部運輸資料流通サービス（TDX）により、全国のバスリアルタイム運行データ（GTFS準拠）がAPI公開されている。"
        },
        "maritime": {
            "summary": "台湾本島と離島（澎湖、金門、馬祖、緑島、蘭嶼、小琉球）を結ぶ離島定期フェリーおよび金門・馬祖と中国大陸沿岸を結ぶ「小三通」定期航路。"
        },
        "aviation": {
            "summary": "桃園国際空港（TPE）を最大の国際線ハブとし、台北松山（TSA）、高雄（KHH）、台中国際（RMQ）のほか、澎湖・金門・南竿・北竿・台東・花蓮等の離島・国内地方空港網が整備されている。"
        }
    }


    portals = [
        {"category": "地図・GIS", "name": "内政部国土測絵中心 (NLSC 地図サービス)", "url": "https://maps.nlsc.gov.tw/", "description": "台湾通用電子地図・正射航空写真・行政界WMTS"},
        {"category": "行政・政府", "name": "政府資料開放ポータル (data.gov.tw)", "url": "https://data.gov.tw/", "description": "台湾政府総合オープンデータプラットフォーム"},
        {"category": "交通", "name": "交通部運輸資料流通サービス (TDX)", "url": "https://tdx.transportdata.tw/", "description": "鉄軌道・バス・道路交通リアルタイムオープンAPI"},
        {"category": "気象", "name": "交通部中央気象署 (CWA)", "url": "https://www.cwa.gov.tw/", "description": "気象警報・地震速報・アメダスリアルタイム観測"},
        {"category": "気象", "name": "中央気象署オープンデータプラットフォーム", "url": "https://opendata.cwa.gov.tw/", "description": "気象観測所マスター・数値予報API"}
    ]

    return {
        "country_code": "TW",
        "name": "台湾",
        "flag": "🇹🇼",
        "basic_info": basic_info,
        "admin_hierarchy": admin_hierarchy,
        "weather_system": weather_system,
        "transit_system": transit_system,
        "official_portals": portals
    }


def build_kr_guide(admin_txt, transit_txt):
    """韓国のガイド構築"""
    s1 = extract_section_text(admin_txt, r"## 1\.\s*対象国基本情報[^\n]*\n", [r"## 2\."])
    b1 = parse_bullets_flexible(s1)

    basic_info = {
        "official_name": "大韓民国",
        "native_name": "대한민국（大韓民國） / Republic of Korea",
        "government_type": b1.get("国家体制", "単一国家（大統領制・共和制）。地方自治法に基づき、第1階層の広域自治団体（17団体：特別市1・広域市6・特別自治市1・道6・特別自治道3）と、第2階層の基礎自治団体（226団体：市75・郡82・自治区69）から構成される。"),
        "official_languages": b1.get("公用語（地域的公認言語を含む）", "公用語は韓国語（韓国文字・ハングル）。国家法令および行政文書はハングル専用法に基づき運用される。"),
        "territory_bbox": "軍事境界線（MDL）以南の実効支配管轄全域（鬱陵島・独島、済州島、離於島海洋科学基地等を含む）。実効管轄緯度: 33.11°N〜38.62°N、経度: 124.60°E〜131.87°E。",
        "special_regions": b1.get("飛び地・特殊行政区域", "海外領土なし。軍事境界線（MDL）に接する非武装地帯（DMZ）民間人統制区域、および高度な自治権を有する特別自治市（世宗市）や特別自治道（済州・江原・全北）が指定されている。")
    }

    s2 = extract_section_text(admin_txt, r"### 2\.1\s*行政[^\n]*\n", [r"### 2\.2"])
    t2 = parse_md_table(s2)
    admin_levels = []
    for r in t2:
        if "行政" in r.get("大分類", ""):
            admin_levels.append({
                "level": r.get("階層レベル", ""),
                "name_ja": r.get("種別名_日本語", ""),
                "name_local": r.get("種別名_公用語", ""),
                "scale": r.get("規模目安(件数)", "") or r.get("規模目安", ""),
                "description": sanitize_public_text(r.get("法的根拠・自治権の有無・説明", "")) or r.get("説明", "")
            })

    admin_hierarchy = {
        "summary": "地方自治法に基づく広域自治団体（17市・道）と基礎自治団体（226市・郡・区）の二層制。基礎自治団体の下位に邑・面・洞（約3,500）、統・里（約85,000）の末端行政区域が編成されている。",
        "levels": admin_levels
    }

    weather_system = {
        "agency_name": "気象庁 (Korea Meteorological Administration / KMA)",
        "agency_url": "https://www.kma.go.kr/",
        "agency_desc": "環境部傘下の国家気象機関。全国の気象観測、予報、地震監視を一括管理。",
        "forecast_zones": [
            {"level_name": "第1階層（広域予報区）", "scale": "13区域", "description": "ソウル・仁川・京畿、江原道、忠清道、全羅道、慶尚道、済州島等の大ブロック。"},
            {"level_name": "第2階層（市郡予報区）", "scale": "約170区域", "description": "市・郡単位の気象特報（警報・注意報）発表区域。"},
            {"level_name": "第3階層（邑面洞トンネ予報）", "scale": "約3,500区域", "description": "5kmメッシュ相当の邑面洞ピンポイント近隣予報（トンネ予報）。"}
        ],
        "marine_zones": "西海、南海、東海、済州道沿岸・近海予報区",
        "observation_network": {
            "network_name": "地上気象観測網（ASOS: 総観気象観測所 ＆ AWS: 自動気象観測装置）",
            "stations_scale": "約615〜630地点（ASOS約100地点、AWS約520地点）",
            "description": "全国約13km間隔で配備され、降水・気温・風向風速・気圧を1分〜10分値でリアルタイム提供。"
        }
    }

    s_road = extract_section_text(transit_txt, r"## 1\.\s*道路網制度の詳細分類[^\n]*\n", [r"## 2\."])
    t_road = parse_md_table(s_road)
    clean_road = []
    for r in t_road:
        clean_road.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語相当", ""),
            "name_local": r.get("中分類・法的名称（公用語）", ""),
            "law": r.get("根拠法律", ""),
            "manager": r.get("管理主体", ""),
            "scale": r.get("全体規模目安", "") or r.get("規模目安", "")
        })

    s_rail = extract_section_text(transit_txt, r"## 2\.\s*鉄軌道[・都市交通]*・索道制度の詳細分類[^\n]*\n", [r"## 3\."])
    t_rail = parse_md_table(s_rail)
    clean_rail = []
    for r in t_rail:
        clean_rail.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語・技術分類", ""),
            "name_local": r.get("法的種別（公用語）", ""),
            "law": r.get("根拠法律・条文", ""),
            "lines_or_cities": r.get("主な運行都市・対象路線例", "")
        })

    transit_system = {
        "road": {
            "summary": "道路法に基づく高速国道、一般国道、特別市道・広域市道、地方道、市道・郡道・区道。韓国道路公社（EX）が有料高速道路網を一元管理。",
            "classifications": clean_road,
            "numbering_rules": "高速道路は2桁付番（南北方向は奇数15〜65号、東西方向は偶数10〜50号、ソウル外郭循環線100号など環状線は末尾00番）。一般国道は1〜88号（南北奇数、東西偶数）。地方道は3桁・4桁付番。",
            "management_notes": "高速国道および一般国道は国土交通部直轄、特別市道・広域市道・地方道は各地方自治体が管理。"
        },
        "railway": {
            "summary": "鉄道事業法に基づく高速鉄道（KTX、SRT）、一般幹線鉄道（ITX-セマウル、ムグンファ号等）、首都圏広域急行鉄道（GTX）、都市鉄道（ソウル地下鉄1〜9号線、釜山・大邱・光州・大田地下鉄、新盆唐線、軽電鉄等）。",
            "classifications": clean_rail,
            "special_transit_notes": "議政府軽電鉄、龍仁軽電鉄、ソウル軽電鉄牛耳新設線などのゴムタイヤ式・鉄輪式AGT軽電鉄や南山ケーブルカーなどの索道が運行。",
            "major_operators": [
                {"name": "韓国鉄道公社 (KORAIL)", "role": "国営鉄道会社", "lines": "京釜線、湖南線、KTX各線、首都圏電鉄各線"},
                {"name": "株式会社SR (SR)", "role": "高速鉄道専業", "lines": "水西平沢高速線（SRT）"},
                {"name": "ソウル交通公社 (Seoul Metro)", "role": "都市地下鉄公営", "lines": "ソウル地下鉄1〜8号線、9号線第2・3段階区間"}
            ]
        },
        "bus": {
            "summary": "市外バス・高速バス（コバス・バスターミナル網）および市内バス・マウルバス。全国T-money交通カードによる乗り継ぎ割引制度が高度に統合。"
        },
        "maritime": {
            "summary": "仁川・木浦・莞島・浦項・釜山等を起点に、鬱陵島・済州島・白翎島・延坪島等の離島を結ぶ沿岸旅客フェリー網。"
        },
        "aviation": {
            "summary": "仁川国際空港（ICN）を主ハブ、金浦国際空港（GMP）を国内線・近距離国際線ハブとし、金海（PUS）、済州（CJU）、大邱、清州等の地方空港網。金浦〜済州線は世界最多の旅客輸送実績を持つ。"
        }
    }


    portals = [
        {"category": "地図・空間情報", "name": "国土交通部 国家空間情報ポータル (V-World)", "url": "https://www.vworld.kr/", "description": "韓国公式Web GIS・航空写真・行政境界オープンデータ"},
        {"category": "行政・政府", "name": "公共データポータル (data.go.kr)", "url": "https://www.data.go.kr/", "description": "韓国政府総合オープンデータポータル"},
        {"category": "気象", "name": "気象庁 (KMA) 公式ホームページ", "url": "https://www.kma.go.kr/", "description": "天気予報・気象特報・リアルタイム観測"},
        {"category": "気象", "name": "気象資料開放ポータル", "url": "https://data.kma.go.kr/", "description": "ASOS/AWS観測所マスター・過去気象データ"},
        {"category": "交通", "name": "韓国道路公社 (Roadplus)", "url": "https://www.roadplus.co.kr/", "description": "全国高速道路交通状況・路線情報"}
    ]

    return {
        "country_code": "KR",
        "name": "大韓民国",
        "flag": "🇰🇷",
        "basic_info": basic_info,
        "admin_hierarchy": admin_hierarchy,
        "weather_system": weather_system,
        "transit_system": transit_system,
        "official_portals": portals
    }


def build_ch_guide(admin_txt, transit_txt):
    """スイスのガイド構築"""
    basic_info = {
        "official_name": "スイス連邦",
        "native_name": "Schweizerische Eidgenossenschaft (de) / Confédération suisse (fr) / Confederazione Svizzera (it) / Confederaziun svizra (rm) / Confoederatio Helvetica",
        "government_type": "連邦制共和国。26の連邦構成州（カントン：うち6州が歴史的準州由来）および全2,110の基礎自治体（ゲマインデ / コミューン）から構成される。事実上の連邦首都はベルン（連邦都市：Bundesstadt）。",
        "official_languages": "連邦公用語はドイツ語（約62%）、フランス語（西部）、イタリア語（南部ティチーノ州等）、ロマンシュ語（グラウビュンデン州）。カントンごとに公用語（単一または多言語）が憲法で規定されている。",
        "territory_bbox": "アルプス山脈とジュラ山脈に挟まれた高原・山岳内陸国（面積41,285 km²）。本土外接矩形: 緯度 45.82°N〜47.81°N、経度 5.96°E〜10.49°E。",
        "special_regions": "スイス領内に2つの外国包領（ドイツ領ビュージンゲン、イタリア領カンピョーネ・ディターリア）が存在。また基礎自治体に属さない州直轄林や湖沼、共有地（Kommunanz）が存在する。隣接国リヒテンシュタイン公国とは関税・通貨同盟を結び空間データが統合されている。"
    }

    s2 = extract_section_text(admin_txt, r"### 2\.1\s*行政[^\n]*\n", [r"### 2\.2"])
    t2 = parse_md_table(s2)
    admin_levels = []
    for r in t2:
        if "行政" in r.get("大分類", ""):
            admin_levels.append({
                "level": r.get("階層レベル", ""),
                "name_ja": r.get("種別名_日本語", ""),
                "name_local": r.get("種別名_公用語", ""),
                "scale": r.get("規模目安(件数)", "") or r.get("規模目安", ""),
                "description": sanitize_public_text(r.get("法的根拠・自治権の有無・説明", "")) or r.get("説明", "")
            })

    admin_hierarchy = {
        "summary": "スイス連邦憲法（BV）に基づく連邦（Bund）、カントン（26州）、基礎自治体（Gemeinde：全2,110）の3層構造。カントンは独自の憲法・議会・司法・課税権を有する主権国家並みの高度な自治権を持ち、一部カントンでは中間行政区画として郡（Bezirk / District）が置かれる。",
        "levels": admin_levels
    }

    weather_system = {
        "agency_name": "連邦気象気候庁 (MeteoSchweiz / MétéoSuisse / MeteoSvizzera / MeteoSwiss)",
        "agency_url": "https://www.meteoswiss.admin.ch/",
        "agency_desc": "連邦内務省（EDI）傘下の国家気象機関。連邦自然災害ポータル（naturgefahren.ch）上で環境庁（BAFU）や雪崩研究所（SLF）と共通の5段階警報を運用。",
        "forecast_zones": [
            {"level_name": "気象警報地域 (Warnregionen)", "scale": "159区域", "description": "アルプス・ジュラ山脈等の地形・標高帯・流域に即した気象警報発表基本ポリゴン（リヒテンシュタインも包含）。"},
            {"level_name": "気象警報オブジェクト", "scale": "51対象", "description": "突風・強風警報が個別に発令される全国の主要湖沼および飛行場。"},
            {"level_name": "雪崩警報単位 (SLF)", "scale": "149区域", "description": "連邦雪・雪崩研究所（SLF）が運用する最小雪崩警報区域。"}
        ],
        "marine_zones": "内陸国のため海洋警報なし。全国の湖沼突風警報システムを運用。",
        "observation_network": {
            "network_name": "自動気象観測網「SwissMetNet (SMN)」および手動降雪観測網",
            "stations_scale": "総合自動観測約160地点、降水約100地点、手動積雪約240地点",
            "description": "気温・気圧・風速・日射・降水量を10分値で計測。Swisstopo連邦空間データ基盤（FSDI）のSTAC REST API経由で完全無償オープンデータ公開。"
        }
    }

    s_road = extract_section_text(transit_txt, r"## 1\.\s*道路網制度の詳細分類[^\n]*\n", [r"## 2\."])
    t_road = parse_md_table(s_road)
    clean_road = []
    for r in t_road:
        clean_road.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語相当", ""),
            "name_local": r.get("中分類・法的名称（公用語）", ""),
            "law": r.get("根拠法律", ""),
            "manager": r.get("管理主体", ""),
            "scale": r.get("全体規模目安", "") or r.get("規模目安", "")
        })

    s_rail = extract_section_text(transit_txt, r"## 2\.\s*鉄軌道[・都市交通]*・索道制度の詳細分類[^\n]*\n", [r"## 3\."])
    t_rail = parse_md_table(s_rail)
    clean_rail = []
    for r in t_rail:
        clean_rail.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語・技術分類", ""),
            "name_local": r.get("法的種別（公用語）", ""),
            "law": r.get("根拠法律・条文", ""),
            "lines_or_cities": r.get("主な運行都市・対象路線例", "")
        })

    transit_system = {
        "road": {
            "summary": "連邦道路法（NSG）に基づく国道（Nationalstrassen：高速道路A路線）、カントン道（Kantonsstrassen：主要道路・地方道路）、自治体道（Gemeindestrassen）。連邦道路庁（ASTRA）が一元管理。",
            "classifications": clean_road,
            "numbering_rules": "高速道路（Autobahn / Autoroute）はA1〜A16。主要幹線は欧州自動車道路E25, E35, E41, E43等と重複。",
            "management_notes": "高規格国道（A路線 約1,850km）は連邦ASTRA直轄管理（ヴィニエット料金制）。カントン道は州が管理。"
        },
        "railway": {
            "summary": "スイス連邦鉄道（SBB CFF FFS）をはじめ、民間・州立鉄道事業者（BLS、レーティッシュ鉄道RhB、Matterhorn Gotthard Bahn等）が網の目のように連携する世界屈指の高密度・高定時性鉄道王国。ラック式鉄道、ケーブルカー、登山電車、ロープウェイが極めて発達。",
            "classifications": clean_rail,
            "special_transit_notes": "アルプス山岳交通として交走式ロープウェイ、自動循環式ゴンドラ、フニテル、鋼索鉄道（ケーブルカー）が多数運行され、索道法（SebG）に基づき厳格に認可運用されている。",
            "major_operators": [
                {"name": "スイス連邦鉄道 (SBB CFF FFS)", "role": "国営幹線鉄道", "lines": "スイス全土の標準軌主要幹線、ゴッタルド基底トンネル、インターシティ各線"},
                {"name": "BLS AG (BLS)", "role": "準国営幹線鉄道", "lines": "レッチュベルク基底トンネル、ベルン近郊Sバーン網"},
                {"name": "レーティッシュ鉄道 (RhB)", "role": "狭軌山岳鉄道", "lines": "アルブラ線・ベルニナ線（世界遺産）、グラウビュンデン州全域"}
            ]
        },
        "bus": {
            "summary": "スイスポスト傘下の黄色いポストバス（PostAuto / CarPostal）が山岳集落や峠道をくまなく結び、鉄道との完全な定時乗り継ぎダイヤが構築されている。"
        },
        "maritime": {
            "summary": "レマン湖、ルツェルン湖（フィーアヴァルトシュテッター湖）、チューリッヒ湖、トゥーン湖、ブリエンツ湖、ボーデン湖等の観光・生活定期船。"
        },
        "aviation": {
            "summary": "チューリッヒ空港（ZRH）を主ハブとし、ジュネーヴ空港（GVA）、バーゼル・ミュールーズ・フライブルク空港（BSL：フランスとの二国共同管理空港）の3大空港が機能。"
        }
    }


    portals = [
        {"category": "地図・空間情報", "name": "連邦測量局 (swisstopo / geo.admin.ch)", "url": "https://map.geo.admin.ch/", "description": "スイス公式Web GIS・国土地図・オルソ写真タイル"},
        {"category": "行政・統計", "name": "連邦統計局 (BFS / OFS)", "url": "https://www.bfs.admin.ch/", "description": "自治体台帳・国勢調査統計データ"},
        {"category": "気象", "name": "連邦気象気候庁 (MeteoSwiss)", "url": "https://www.meteoswiss.admin.ch/", "description": "気象予報・観測データ・STAC APIオープンデータ"},
        {"category": "交通", "name": "連邦交通庁 (BAV / BFT)", "url": "https://www.bav.admin.ch/", "description": "スイス交通網政策・認可情報"},
        {"category": "政府", "name": "連邦オープンデータポータル (opendata.swiss)", "url": "https://opendata.swiss/", "description": "スイス連邦政府総合オープンデータカタログ"}
    ]

    return {
        "country_code": "CH",
        "name": "スイス",
        "flag": "🇨🇭",
        "basic_info": basic_info,
        "admin_hierarchy": admin_hierarchy,
        "weather_system": weather_system,
        "transit_system": transit_system,
        "official_portals": portals
    }


def build_it_guide(admin_txt, transit_txt):
    """イタリアのガイド構築"""
    s1 = extract_section_text(admin_txt, r"## 1\.\s*対象国基本情報[^\n]*\n", [r"## 2\."])
    b1 = parse_bullets_flexible(s1)

    basic_info = {
        "official_name": "イタリア共和国",
        "native_name": "Repubblica Italiana / Italian Republic",
        "government_type": b1.get("国家体制", "単一国家（地方分権型単一国家）。全20州（普通自治州15州・特別自治州5州）、第二級自治体としての県（80県）・広域市（14市）・自治県（2県）・自由基礎自治体組合（6組合）、および最基礎自治体のコムーネ（全7,896市町村）から構成される。"),
        "official_languages": b1.get("公用語", "全国公用語はイタリア語。地域レベルでトレンティーノ＝アルト・アディジェ州のドイツ語・ラディン語、ヴァッレ・ダオスタ州のフランス語、フリウリ州のスロベニア語、サルデーニャ語等が公認されている。"),
        "territory_bbox": "地中海に突き出す半島およびシチリア島・サルデーニャ島等の島嶼部（総面積約301,340 km²）。陸域検査範囲: 緯度 35.45°N〜47.10°N、経度 6.60°E〜18.55°E。",
        "special_regions": b1.get("飛び地・海外領土・特殊行政区域", "スイス国内に国外飛び地（カンピオーネ・ディターリア：コモ県所属）が存在。またイタリア領土内にバチカン市国およびサンマリノ共和国の2つの独立主権国家が完全に包囲されている。アルプス山中のリヴィーニョはEU非課税地域に指定。")
    }

    s2 = extract_section_text(admin_txt, r"### 2\.1\s*行政[^\n]*\n", [r"### 2\.2"])
    t2 = parse_md_table(s2)
    admin_levels = []
    for r in t2:
        if "行政" in r.get("大分類", ""):
            admin_levels.append({
                "level": r.get("階層レベル", ""),
                "name_ja": r.get("種別名_日本語", ""),
                "name_local": r.get("種別名_公用語", ""),
                "scale": r.get("規模目安(件数)", "") or r.get("規模目安", ""),
                "description": sanitize_public_text(r.get("法的根拠・自治権の有無・説明", "")) or r.get("説明", "")
            })

    admin_hierarchy = {
        "summary": "イタリア共和国憲法第5部および地方自治統一法（TUEL）に基づく州（Regione：20州）、超コムーネ広域単位（県・広域市・自治県・組合：計107単位）、コムーネ（Comune：全7,896自治体）の重層的体系。",
        "levels": admin_levels
    }

    weather_system = {
        "agency_name": "イタリア空軍気象局 (CNMCA) / 国立気象気候庁 (ItaliaMeteo) / 市民保護局 (DPC)",
        "agency_url": "https://www.meteoam.it/",
        "agency_desc": "軍事（空軍気象局：WMO代表機関・一般予報・Meteomar）、文民（国立ItaliaMeteo：技術基準・数値予報）、防災（内閣府市民保護局および各州環境保護庁ARPA：警報・水文観測）の3者連携分担体制。",
        "forecast_zones": [
            {"level_name": "州・自治県機能センター管区", "scale": "21管区", "description": "19州＋トレント・ボルツァーノ自治県の中央防災警報管区。"},
            {"level_name": "気象・水文警報区域 (Zone di allerta)", "scale": "158区域（細分約170）", "description": "河川流域・地形・気候の均一性に基づき画定された全国標準の警報ポリゴン。"},
            {"level_name": "コムーネ警報発令", "scale": "7,896自治体", "description": "警報区域に基づき自治体単位で災害対策本部が稼働。"}
        ],
        "marine_zones": "公式海上気象通報「Meteomar」イタリア周辺海域16セクター（リグーリア海、ティレニア海各部、アドリア海各部、イオニア海等）",
        "observation_network": {
            "network_name": "空軍総観気象観測網 ＆ 各州ARPA統合水文気象テレメトリ網",
            "stations_scale": "空軍SYNOP約110箇所、各州ARPA/APPA自動観測所約4,500箇所以上",
            "description": "空軍の総観観測網に加え、各州環境保護庁（ARPA）の高密度自動雨量計・気温計・水位計網がリアルタイム集約。"
        }
    }

    s_road = extract_section_text(transit_txt, r"## 1\.\s*道路網制度の詳細分類[^\n]*\n", [r"## 2\."])
    t_road = parse_md_table(s_road)
    clean_road = []
    for r in t_road:
        clean_road.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語相当", ""),
            "name_local": r.get("中分類・法的名称（公用語）", "") or r.get("中分類・法的名称", ""),
            "law": r.get("根拠法律", ""),
            "manager": r.get("管理主体", ""),
            "scale": r.get("全体規模目安", "") or r.get("規模目安", "")
        })

    s_rail = extract_section_text(transit_txt, r"## 2\.\s*鉄軌道[・都市交通]*・索道制度の詳細分類[^\n]*\n", [r"## 3\."])
    t_rail = parse_md_table(s_rail)
    clean_rail = []
    for r in t_rail:
        clean_rail.append({
            "category": r.get("大分類", ""),
            "name_ja": r.get("日本語・技術分類", ""),
            "name_local": r.get("法的種別（公用語）", "") or r.get("法的種別", ""),
            "law": r.get("根拠法律・条文", "") or r.get("根拠法律", ""),
            "lines_or_cities": r.get("主な運行都市・対象路線例", "") or r.get("対象路線例", "")
        })

    transit_system = {
        "road": {
            "summary": "新道路交通法典（Codice della Strada）に基づくアウトストラーダ（高速道路A路線）、主要郊外道路（SS国道）、二次郊外道路（SP県道・SR州道）、都市道路。ANAS（道路公社）およびAutostrade per l'Italia（ASPI）等の有料高速道路会社が管理。",
            "classifications": clean_road,
            "numbering_rules": "高速道路はA1（太陽の高速道路：ミラノ〜ローマ〜ナポリ）、A4（トリノ〜トリエステ）等。環状高速道路にはA50〜A52（ミラノ）、A90（ローマGRA）等が付番。国道はSS1〜SS700番台、県道はSP、州道はSR。",
            "management_notes": "高速道路網（約7,000km）は主にASPI等のコンセッション会社、無料国道・高速道路はANAS、県道は各県・広域市が管理。"
        },
        "railway": {
            "summary": "イタリア鉄道網RFI（国家鉄道インフラ保有）の基盤上で、トレニタリア（Trenitalia：Frecciarossa等）および民間高速鉄道イタロ（Italo - NTV）が高速旅客列車を競合運行。ローマ、ミラノ、ナポリ、トリノの地下鉄（Metropolitana）、各都市トラム・路面電車網。",
            "classifications": clean_rail,
            "special_transit_notes": "アルプス山岳地域やドロミテ、エトナ山周辺におけるロープウェイ・ゴンドラリフト（Funivia）、ナポリ等のケーブルカー（Funicolare）が多数運用。",
            "major_operators": [
                {"name": "イタリア鉄道網 (RFI - Rete Ferroviaria Italiana)", "role": "国有鉄道インフラ管理者", "lines": "全国の高速鉄道線（AV/AC）および在来線網"},
                {"name": "トレニタリア (Trenitalia)", "role": "国営旅客運行会社", "lines": "Frecciarossa, Frecciargento, Frecciabianca, インターシティ, 地域列車"},
                {"name": "Italo - Nuovo Trasporto Viaggiatori (NTV)", "role": "民間高速鉄道運行会社", "lines": "トリノ〜ミラノ〜ローマ〜ナポリ〜サレルノ、ヴェネツィア方面等"}
            ]
        },
        "bus": {
            "summary": "都市間長距離バス（FlixBus、Itabus等）および各都市・県の地域公共交通（TPL: Trasporto Pubblico Locale：ATACローマ、ATMミラノ、ANMナポリ等）。"
        },
        "maritime": {
            "summary": "半島部とシチリア島・サルデーニャ島を結ぶ長距離大型フェリー（Tirrenia、Grimaldi、Moby等）、メッシーナ海峡横断シャトルフェリー、ナポリ湾・カプリ島・イスキア島・エオリア諸島・トスカーナ群島等の沿岸高速船。"
        },
        "aviation": {
            "summary": "ローマ・フィウミチーノ空港（FCO：レオナルド・ダ・ヴィンチ空港）およびミラノ・マルペンサ空港（MXP）の二大国際ハブを中心に、ミラノ・リナーテ、ベルガモ、ヴェネツィア、ナポリ、カターニア、パレルモ等の国内・国際空港網。ITAエアウェイズが中核キャリア。"
        }
    }


    portals = [
        {"category": "行政・統計", "name": "イタリア国家統計局 (ISTAT)", "url": "https://www.istat.it/", "description": "自治体コード台帳（SITUAS）・国勢調査境界データ"},
        {"category": "行政・政府", "name": "国家オープンデータカタログ (dati.gov.it)", "url": "https://www.dati.gov.it/", "description": "イタリア政府総合オープンデータポータル"},
        {"category": "地図・GIS", "name": "環境・エネルギー安全保障省 国家地理ポータル", "url": "https://gn.mase.gov.it/", "description": "全国オルソフォト・標高モデル・行政界WMS"},
        {"category": "気象", "name": "イタリア空軍気象局 (MeteoAM)", "url": "https://www.meteoam.it/", "description": "公式気象予報・海上気象通報Meteomar"},
        {"category": "気象", "name": "内閣府市民保護局 (Protezione Civile)", "url": "https://www.protezionecivile.gov.it/", "description": "全国気象・水文警報ゾーンマップ"},
        {"category": "交通", "name": "イタリア鉄道網 (RFI)", "url": "https://www.rfi.it/", "description": "鉄道インフラ・路線網公式ポータル"}
    ]

    return {
        "country_code": "IT",
        "name": "イタリア",
        "flag": "🇮🇹",
        "basic_info": basic_info,
        "admin_hierarchy": admin_hierarchy,
        "weather_system": weather_system,
        "transit_system": transit_system,
        "official_portals": portals
    }


def main():
    print("==================================================================")
    print("国・制度インフラガイド（📘 制度・インフラ解説）生成スクリプト実行")
    print("==================================================================")

    os.makedirs(GUIDES_OUTPUT_DIR, exist_ok=True)

    builders = {
        "JP": build_jp_guide,
        "AT": build_at_guide,
        "TW": build_tw_guide,
        "KR": build_kr_guide,
        "CH": build_ch_guide,
        "IT": build_it_guide,
    }

    guides_data = {}

    for cc in COUNTRIES:
        admin_path = os.path.join(DOCS_DIR, f"{cc}_行政・気象_制度調査.md")
        transit_path = os.path.join(DOCS_DIR, f"{cc}_交通_制度調査.md")

        if not os.path.exists(admin_path) or not os.path.exists(transit_path):
            print(f"[警告] {cc} のマークダウンファイルが見つかりません。")
            continue

        with open(admin_path, "r", encoding="utf-8") as f:
            admin_txt = f.read()
        with open(transit_path, "r", encoding="utf-8") as f:
            transit_txt = f.read()

        builder_func = builders.get(cc)
        if builder_func:
            print(f"[{cc}] ガイドデータ抽出・生成中...")
            guide = builder_func(admin_txt, transit_txt)
            guides_data[cc] = guide

            # 1. 独立したガイドJSONとして保存
            guide_out_path = os.path.join(GUIDES_OUTPUT_DIR, f"{cc.lower()}.json")
            with open(guide_out_path, "w", encoding="utf-8") as gf:
                json.dump(guide, gf, ensure_ascii=False, indent=2)
            print(f"  -> {guide_out_path} を出力しました。")

            # 2. web/public/data/{cc.lower()}.json に guide フィールドを埋め込み
            country_json_path = os.path.join(PUBLIC_DATA_DIR, f"{cc.lower()}.json")
            if os.path.exists(country_json_path):
                with open(country_json_path, "r", encoding="utf-8") as cf:
                    cdata = json.load(cf)
                cdata["guide"] = guide
                with open(country_json_path, "w", encoding="utf-8") as cf:
                    json.dump(cdata, cf, ensure_ascii=False)
                print(f"  -> {country_json_path} に guide データを統合しました。")
            else:
                print(f"  [注] {country_json_path} が存在しません。")

    # 3. summary.json の各国オブジェクトに has_guide フラグを反映
    summary_path = os.path.join(PUBLIC_DATA_DIR, "summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as sf:
            sdata = json.load(sf)
        countries_list = sdata.get("countries", [])
        updated_count = 0
        for c in countries_list:
            code = c.get("code")
            has_guide = code in guides_data
            c["has_guide"] = has_guide
            if has_guide:
                updated_count += 1
        with open(summary_path, "w", encoding="utf-8") as sf:
            json.dump(sdata, sf, ensure_ascii=False, indent=2)
        print(f"[サマリー更新] summary.json に has_guide フラグを反映しました（対象: {updated_count}カ国）。")

    print("\n全処理が完了しました。")


if __name__ == "__main__":
    main()
