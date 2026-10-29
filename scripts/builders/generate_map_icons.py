# -*- coding: utf-8 -*-
"""
高精細 地図円形バッジSVGアイコン生成スクリプト (generate_map_icons.py)
---------------------------------------------------------------
確定仕様に基づき、国際交通標識風（ウィーン条約・ISO 7001・国際標準）に準拠した
4大分野（交通網・行政・気象・史跡）の全16種アイコンをベクターSVGとして出力する。
出力先:
  - web/public/assets/icons/
  - web/explorer/assets/icons/
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_DIRS = [
    os.path.join(BASE_DIR, "web", "public", "assets", "icons"),
    os.path.join(BASE_DIR, "web", "explorer", "assets", "icons"),
]

# 全16種類のSVG定義（国際標準・ウィーン道路標識条約・ISO 7001準拠）
ICONS = {
    # -------------------------------------------------------------
    # ① 交通網 (Transport) - クッキリ白太枠(2px) ＋ 国際標識ピクトグラム
    # -------------------------------------------------------------
    # 高速道路IC/JCT: ウィーン条約 E, 5a Motorway標識（立体交差橋・オーバーパス構造）
    "highway-ic.svg": {
        "bg": "#15803d", # 国際高速道路グリーン
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- ウィーン道路標識条約 Motorway（高速道路 立体交差橋） -->
          <!-- 橋の手前の2本道 -->
          <polygon points="10,27 12.5,27 14,16 12,16" fill="#ffffff" />
          <polygon points="26,27 23.5,27 22,16 24,16" fill="#ffffff" />
          <!-- 橋の奥の2本道 -->
          <polygon points="12,12 13.8,12 14.5,8 13,8" fill="#ffffff" />
          <polygon points="24,12 22.2,12 21.5,8 23,8" fill="#ffffff" />
          <!-- 中央分離帯・破線 -->
          <line x1="18" y1="18" x2="18" y2="21" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
          <line x1="18" y1="24" x2="18" y2="27" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
          <!-- 立体交差オーバーパス橋梁 -->
          <rect x="8" y="12" width="20" height="3.5" rx="0.8" fill="#ffffff" />
        """
    },
    # サービスエリア/PA: 国際標識（白角丸内の「P」および国際給油/サービスシンボル）
    "highway-sa.svg": {
        "bg": "#15803d", # 高速道路グリーン
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- 国際パーキング P プレート -->
          <rect x="7.5" y="10" width="10" height="16" rx="2" fill="#ffffff" />
          <path d="M10.5 13 L14 13 Q16 13 16 15.5 Q16 18 14 18 L10.5 18 Z" fill="#15803d" />
          <path d="M12 14.5 L13.5 14.5 Q14.5 14.5 14.5 15.5 Q14.5 16.5 13.5 16.5 L12 16.5 Z" fill="#ffffff" />
          <line x1="12" y1="18" x2="12" y2="23" stroke="#15803d" stroke-width="1.5" stroke-linecap="square" />
          <!-- 国際給油機シンボル (Fuel Pump) -->
          <rect x="19.5" y="12" width="6.5" height="12" rx="1" fill="#ffffff" />
          <rect x="21" y="14" width="3.5" height="3" rx="0.5" fill="#15803d" />
          <path d="M26 14.5 L27.5 14.5 Q28.5 14.5 28.5 16.5 L28.5 22 L27 21" fill="none" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
          <line x1="18.5" y1="24" x2="27" y2="24" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
        """
    },
    # 一般鉄道駅: ISO 7001準拠 国際鉄道標識（白抜き列車正面シルエット）
    "train-station.svg": {
        "bg": "#2563eb", # 国際鉄道ブルー
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- 国際鉄道標識（ISO 7001 白抜きの列車正面シルエット） -->
          <path d="M11 10 C11 8.5 13 8 18 8 C23 8 25 8.5 25 10 L25 21 C25 23 23.5 23.5 18 23.5 C12.5 23.5 11 23 11 21 Z" fill="#ffffff" />
          <!-- 運転席フロントガラス -->
          <path d="M13 11 L23 11 C23.5 11 23.5 11.5 23.5 12 L23.5 15.5 C23.5 16 23 16 23 16 L13 16 C12.5 16 12.5 15.5 12.5 15.5 L12.5 12 C12.5 11.5 13 11 13 11 Z" fill="#2563eb" />
          <!-- ヘッドライト2基 -->
          <circle cx="14" cy="19.5" r="1.3" fill="#fbbf24" />
          <circle cx="22" cy="19.5" r="1.3" fill="#fbbf24" />
          <!-- レール/軌道 -->
          <line x1="9" y1="26" x2="27" y2="26" stroke="#ffffff" stroke-width="2" stroke-linecap="round" />
          <line x1="13" y1="24" x2="11.5" y2="27" stroke="#ffffff" stroke-width="1.5" />
          <line x1="23" y1="24" x2="24.5" y2="27" stroke="#ffffff" stroke-width="1.5" />
        """
    },
    # 新幹線・高速鉄道: 国際高速列車（エアロダイナミック流線型ノーズ＋スピードライン）
    "train-shinkansen.svg": {
        "bg": "#7c3aed", # 高速鉄道バイオレット
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- 国際高速列車（流線型ノーズ＋スピードライン） -->
          <path d="M8.5 22 L11 17 C13 11.5 18 9 27.5 9 L27.5 22 Z" fill="#ffffff" />
          <path d="M15 15.5 C17 13 20 11.5 24.5 11.5 L24.5 14.5 C20 14.5 17.5 15.5 15 16.5 Z" fill="#7c3aed" />
          <line x1="7" y1="24" x2="28" y2="24" stroke="#ffffff" stroke-width="2" stroke-linecap="round" />
          <line x1="12" y1="26" x2="26" y2="26" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round" />
          <path d="M12 19.5 L16 19.5" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" />
        """
    },
    # 地下鉄: 国際メトロ標識（白抜きボールド「M」シンボル）
    "subway.svg": {
        "bg": "#1d4ed8", # メトロ濃紺
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- 国際メトロ標識（白抜きの太字「M」シンボル） -->
          <path d="M9 26 L9 10 L13.5 10 L18 18 L22.5 10 L27 10 L27 26 L23 26 L23 15.5 L19.5 22 L16.5 22 L13 15.5 L13 26 Z" fill="#ffffff" />
        """
    },
    # 路面電車/LRT: 国際トラム標識（架線・パンタグラフ付きトラム）
    "tram.svg": {
        "bg": "#0284c7", # トラム水色
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- 国際トラム標識（架線・パンタグラフ付き路面電車） -->
          <line x1="11" y1="6.5" x2="25" y2="6.5" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round" />
          <path d="M15 10 L18 7 L21 10 L18 12 Z" fill="none" stroke="#ffffff" stroke-width="1.2" />
          <line x1="18" y1="12" x2="18" y2="13.5" stroke="#ffffff" stroke-width="1.5" />
          <rect x="11" y="13.5" width="14" height="11.5" rx="2" fill="#ffffff" />
          <rect x="12.5" y="15.5" width="11" height="4.5" rx="0.8" fill="#0284c7" />
          <circle cx="14" cy="22" r="1.1" fill="#fbbf24" />
          <circle cx="22" cy="22" r="1.1" fill="#fbbf24" />
          <line x1="9" y1="26.5" x2="27" y2="26.5" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
        """
    },
    # 空港: ICAO / ISO 7001 国際航空標識（明快な飛行機シルエット）
    "airport.svg": {
        "bg": "#0ea5e9", # 航空スカイブルー
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- ICAO / ISO 7001 国際航空機シンボル -->
          <path d="M18 7 C17.2 7 16.5 7.8 16.5 8.8 L16.5 15 L7.5 19.5 L7.5 22 L16.5 19 L16.5 24.5 L14 26.5 L14 28.5 L18 27.5 L22 28.5 L22 26.5 L19.5 24.5 L19.5 19 L28.5 22 L28.5 19.5 L19.5 15 L19.5 8.8 C19.5 7.8 18.8 7 18 7 Z" fill="#ffffff" />
        """
    },
    # 港湾: ISO 7001 国際旅客港・フェリー標識（水面を進む客船シルエット）
    "port.svg": {
        "bg": "#0d9488", # 港湾ティール
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- ISO 7001 港湾・旅客客船フェリー標識 -->
          <rect x="15.5" y="9.5" width="2.5" height="3.5" fill="#ffffff" />
          <path d="M12 13.5 L24 13.5 L23 17.5 L12 17.5 Z" fill="#ffffff" />
          <rect x="13.5" y="14.8" width="2" height="1.5" fill="#0d9488" />
          <rect x="17" y="14.8" width="2" height="1.5" fill="#0d9488" />
          <rect x="20.5" y="14.8" width="2" height="1.5" fill="#0d9488" />
          <path d="M8 18.5 L28 18.5 L25 24 L10 24 Z" fill="#ffffff" />
          <path d="M7 26.5 Q9.5 25 12 26.5 T17 26.5 T22 26.5 T27 26.5 T30 26.5" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" />
        """
    },
    # 道の駅/案内所: 国際インフォメーション「i」シンボル
    "roadside-station.svg": {
        "bg": "#ea580c", # 案内オレンジ
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- 国際インフォメーション「i」シンボル -->
          <circle cx="18" cy="11.5" r="2.2" fill="#ffffff" />
          <rect x="15.8" y="15.5" width="4.4" height="10.5" rx="1.5" fill="#ffffff" />
        """
    },
    # 構造物: ウィーン道路標識条約 トンネル坑門シンボル (E, 11a)
    "structure.svg": {
        "bg": "#78350f", # 構造物ブラウン
        "border": "#ffffff",
        "border_width": "2",
        "inner_decor": "",
        "glyph": """
          <!-- ウィーン道路標識条約 トンネル坑門シンボル (E, 11a) -->
          <path d="M9 11 L27 11 L27 25 L23 25 L23 18 C23 15 21 14 18 14 C15 14 13 15 13 18 L13 25 L9 25 Z" fill="#ffffff" />
          <polygon points="14.5,25 21.5,25 19.5,19 16.5,19" fill="#ffffff" />
          <line x1="18" y1="20" x2="18" y2="24" stroke="#78350f" stroke-width="1" stroke-linecap="round" />
        """
    },

    # -------------------------------------------------------------
    # ② 地域・行政 (Region / Admin) - 威厳ある二重リング装飾
    # -------------------------------------------------------------
    "gov-pref.svg": {
        "bg": "#be123c", # 深紅
        "border": "#ffffff",
        "border_width": "1.5",
        "inner_decor": """
          <!-- ゴールド内側リング -->
          <circle cx="18" cy="18" r="13.8" fill="none" stroke="#fbbf24" stroke-width="1.2" />
        """,
        "glyph": """
          <!-- 都道府県庁・州都 議事堂・ドーム列柱 -->
          <path d="M18 9 Q21 12 21 14 L15 14 Q15 12 18 9 Z" fill="#fbbf24" />
          <rect x="11" y="14" width="14" height="2" rx="0.5" fill="#ffffff" />
          <!-- 4本列柱 -->
          <rect x="12" y="16" width="2" height="7" fill="#ffffff" />
          <rect x="15.3" y="16" width="2" height="7" fill="#ffffff" />
          <rect x="18.7" y="16" width="2" height="7" fill="#ffffff" />
          <rect x="22" y="16" width="2" height="7" fill="#ffffff" />
          <!-- 基壇 -->
          <rect x="10" y="23" width="16" height="2.5" rx="0.5" fill="#ffffff" />
        """
    },
    "gov-muni.svg": {
        "bg": "#334155", # スレート濃灰
        "border": "#ffffff",
        "border_width": "1.5",
        "inner_decor": """
          <!-- シルバー内側リング -->
          <circle cx="18" cy="18" r="13.8" fill="none" stroke="#cbd5e1" stroke-width="1.2" />
        """,
        "glyph": """
          <!-- 市区町村役場 庁舎ビルディング ＆ 旗 -->
          <path d="M11 25 L11 13 L21 13 L21 25 Z" fill="#ffffff" />
          <path d="M21 25 L21 17 L25 17 L25 25 Z" fill="#e2e8f0" />
          <rect x="13" y="15" width="2" height="2" fill="#334155" />
          <rect x="17" y="15" width="2" height="2" fill="#334155" />
          <rect x="13" y="18" width="2" height="2" fill="#334155" />
          <rect x="17" y="18" width="2" height="2" fill="#334155" />
          <rect x="14.5" y="22" width="3" height="3" fill="#334155" />
          <line x1="16" y1="13" x2="16" y2="9.5" stroke="#cbd5e1" stroke-width="1" />
          <polygon points="16,9.5 19,10.5 16,11.5" fill="#38bdf8" />
        """
    },

    # -------------------------------------------------------------
    # ③ 気象 (Weather) - 目盛り・コンパス風ダッシュリング
    # -------------------------------------------------------------
    "weather.svg": {
        "bg": "#dc2626", # 赤
        "border": "#ffffff",
        "border_width": "1.5",
        "inner_decor": """
          <!-- コンパス・目盛りダッシュリング -->
          <circle cx="18" cy="18" r="13.8" fill="none" stroke="#ffffff" stroke-width="1.2" stroke-dasharray="2 1.5" />
        """,
        "glyph": """
          <!-- 温度計 ＆ 気象観測波 -->
          <rect x="13.5" y="11" width="3" height="10" rx="1.5" fill="#ffffff" />
          <circle cx="15" cy="22" r="3" fill="#ffffff" />
          <rect x="14.2" y="14" width="1.6" height="7" fill="#dc2626" />
          <circle cx="15" cy="22" r="1.8" fill="#dc2626" />
          <path d="M21 13 Q24 15 21 17" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
          <path d="M23 11 Q27 15 23 19" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
          <circle cx="21" cy="22" r="1.5" fill="#fef08a" />
        """
    },

    # -------------------------------------------------------------
    # ④ 史跡・探索ポイント (Historical Sites / Explorer) - 金縁装飾
    # -------------------------------------------------------------
    "spot-castle.svg": {
        "bg": "#1c1917", # 漆黒
        "border": "#d97706", # 琥珀金枠
        "border_width": "2",
        "inner_decor": """
          <!-- 内側金縁 -->
          <circle cx="18" cy="18" r="14" fill="none" stroke="#fcd34d" stroke-width="1" />
        """,
        "glyph": """
          <!-- 和風城郭 天守閣シルエット -->
          <path d="M12 24 L10 26 L26 26 L24 24 Z" fill="#a8a29e" />
          <path d="M12 24 L24 24 L23 19 L13 19 Z" fill="#ffffff" />
          <path d="M10 19 Q18 16 26 19 L25 18 Q18 15 11 18 Z" fill="#fcd34d" />
          <path d="M14 18 L22 18 L21 14 L15 14 Z" fill="#ffffff" />
          <path d="M12 14 Q18 11.5 24 14 L23.5 13 Q18 10.5 12.5 13 Z" fill="#fcd34d" />
          <path d="M16 13 L20 13 L18 10 Z" fill="#fcd34d" />
          <rect x="17" y="21" width="2" height="3" fill="#1c1917" />
        """
    },
    "pin-saved.svg": {
        "bg": "#991b1b", # 臙脂（えんじ）
        "border": "#f59e0b", # ゴールド枠
        "border_width": "2",
        "inner_decor": """
          <!-- 金縁インナーリング -->
          <circle cx="18" cy="18" r="14" fill="none" stroke="#fef08a" stroke-width="0.8" />
        """,
        "glyph": """
          <!-- 地図ピン・スターマーク -->
          <path d="M18 10 C14.5 10 12 12.5 12 16 C12 20.5 18 26 18 26 C18 26 24 20.5 24 16 C24 12.5 21.5 10 18 10 Z" fill="#ffffff" />
          <circle cx="18" cy="15.5" r="2.5" fill="#f59e0b" />
        """
    },
    "pin-draft.svg": {
        "bg": "#d97706", # アンバー橙
        "border": "#fde68a", # 薄金枠
        "border_width": "2",
        "inner_decor": """
          <!-- ダッシュ金縁 -->
          <circle cx="18" cy="18" r="14" fill="none" stroke="#fde68a" stroke-width="1" stroke-dasharray="3 1.5" />
        """,
        "glyph": """
          <!-- 編集・下書き十字ピン -->
          <circle cx="18" cy="18" r="5" fill="#ffffff" />
          <line x1="18" y1="9" x2="18" y2="27" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" />
          <line x1="9" y1="18" x2="27" y2="18" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" />
          <circle cx="18" cy="18" r="2.2" fill="#d97706" />
        """
    },
}

def build_svg_xml(filename, config):
    """36x36 viewBox のベクターSVGを構築"""
    bg = config["bg"]
    border = config["border"]
    border_width = config["border_width"]
    inner_decor = config["inner_decor"]
    glyph = config["glyph"]

    # 外枠半径（border_width を考慮してクリップされないよう調整）
    r = 18 - float(border_width) / 2.0

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
  <defs>
    <filter id="badge-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-opacity="0.35" />
    </filter>
  </defs>
  <!-- 円形バッジ本体（外枠＋背景色） -->
  <circle cx="18" cy="18" r="{r:.1f}" fill="{bg}" stroke="{border}" stroke-width="{border_width}" filter="url(#badge-shadow)" />
  {inner_decor}
  <!-- 独自デザインピクトグラム -->
  <g>
    {glyph}
  </g>
</svg>
"""
    return svg_content

def main():
    print(f"=== 地図用SVGアイコン生成開始 (全{len(ICONS)}種) ===")
    total_created = 0

    for target_dir in TARGET_DIRS:
        os.makedirs(target_dir, exist_ok=True)
        for icon_name, config in ICONS.items():
            svg_xml = build_svg_xml(icon_name, config)
            file_path = os.path.join(target_dir, icon_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(svg_xml)
            total_created += 1

    print(f"完了: 計 {total_created} ファイルを正常に出力しました。")
    for d in TARGET_DIRS:
        print(f" - {d}")

if __name__ == "__main__":
    main()
