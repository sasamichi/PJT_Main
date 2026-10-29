# オーストリア 行政・統計・気象制度 事前調査シート

- 調査日: 2026-10-25
- 根拠法令・公式資料: オーストリア連邦憲法（Bundes-Verfassungsgesetz: B-VG 第115条〜第120条）、登録ベース国勢調査法（Registerzählungsgesetz）、建物・住宅登録法（GWR-Gesetz）、測量法（Vermessungsgesetz: VermG）、オーストリア統計局（Statistik Austria）『Gemeindeverzeichnis』『Regionale Gliederungen』『AGWR-Merkmalskatalog』、連邦計量・測量局（BEV）『Verwaltungsgrenzen (VGD)』『Digitale Katastralmappe (DKM)』『Regionalinformation』、オーストリア国立地質・地球物理・気候・気象研究所（GeoSphere Austria）『GeoSphere Austria Data Hub』『Dataset API Documentation』

---

## 1. 対象国基本情報・地理的範囲

- 国名（日本語 / 公用語 / 英語）: オーストリア共和国 / Republik Österreich（通称: Österreich） / Republic of Austria（通称: Austria）
- ISO 3166-1コード: Alpha-2: `AT`, Alpha-3: `AUT`, 数値: `040`
- 公用語（地域的公認言語を含む）: ドイツ語（Deutsch：連邦全体の公用語）。地域的公認言語として、ブルゲンラント・クロアチア語およびハンガリー語（ブルゲンラント州）、スロベニア語（ケルンテン州・シュタイアーマルク州の一部）、チェコ語、スロバキア語、ロマ語、オーストリア手話が公認されている。
- 国家体制: 連邦共和制（9つの連邦州［Bundesländer］から構成される連邦国家）。地方行政の基本構造は、第1階層の連邦州（9州）、第2階層の連邦・州の一般行政管区である政治地区（Politischer Bezirk：79郡）および郡の行政機能を兼ねる憲章都市（Statutarstadt：15市）の計94地区、第3階層の基礎自治体（Gemeinde：2,092市町村）による階層構造をとる。連邦首都ウィーン（Wien）は、連邦州・憲章都市（政治地区）・基礎自治体の3階層の法的地位を単一領域で兼ね備える特別構造を有する。
- 領土バウンディングボックス（経緯度範囲）: 本土全域（内陸国のため海洋島嶼なし、総面積83,894 km²）の外接矩形（WGS84 / `EPSG:4326`）は、緯度: `46.372°N 〜 49.039°N`（Gist標準境界基準 `46.431817°N 〜 49.039074°N`、気象観測網基準 `46.443890°N 〜 48.966670°N`）、経度: `9.479°E 〜 17.161°E`（Gist標準境界基準 `9.479970°E 〜 16.979667°E`、気象観測網基準 `9.600000°E 〜 17.133333°E`）。
- 飛び地・海外領土・特殊行政区域: 海外領土・自治領は一切存在しない。国境上の地理的機能飛び地（準飛び地）として、チロル州ロイテ郡（Bezirk Reutte）の基礎自治体ユングホルツ（Jungholz, GKZ: `70818`：ツォークシュピッツェ山頂の1点のみで本土と接続し四方をドイツ領に囲まれる）およびフォアアールベルク州ブレゲンツ郡（Bezirk Bregenz）の基礎自治体ミッテルベルク（Mittelberg / Kleinwalsertal, GKZ: `80228`：アルプス山脈により道路網がドイツ側とのみ接続）が存在するほか、国内の州間飛地としてチロル州のリアンツ郡（Bezirk Lienz / 東チロル, GKZ: `707`）がザルツブルク州とイタリア国境により北チロル本領から分断されている。これらはいずれも行政法・統計・地籍上は特別な除外区域ではなく、通常の連邦州・政治地区・基礎自治体コード体系の内部に完全に統合されて扱われる。

---

## 2. 行政区画・国勢調査区の体系と詳細分類

### 2.1 行政・気象・統計階層と区域種別一覧（area_types.csv 登録データ表）

| type_id | 大分類 | 階層レベル | 種別名_日本語 | 種別名_公用語 | 規模目安(件数) | 検証状態 | 法的根拠・自治権の有無・説明 | Wikipedia_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AT_ADMIN_BUNDESLAND | 行政 | 1 | 連邦州 | Bundesland | 9 | 公的リスト確認済 | 連邦憲法（B-VG）に基づく連邦構成州。独自の州政府・州法体系を持ち高度な自治権を有する。EU統計のNUTS 2と完全一致する。 | https://de.wikipedia.org/wiki/Land_(%C3%96sterreich) |
| AT_ADMIN_STATUTARSTADT | 行政 | 2 | 憲章都市（特別市） | Stadt mit eigenem Statut (Statutarstadt) | 15 | 公的リスト確認済 | 連邦憲法第116条第3項に基づき独自の都市憲章を持つ都市。基礎自治体（Gemeinde）の自治権と政治地区（郡行政庁）の管轄権を併せ持つ（94政治地区の内数かつ2,092基礎自治体の内数）。 | https://de.wikipedia.org/wiki/Statutarstadt_(%C3%96sterreich) |
| AT_ADMIN_POLITISCHER_BEZIRK | 行政 | 2 | 政治地区（郡） | Politischer Bezirk (Verwaltungsbezirk) | 79 | 公的リスト確認済 | 連邦および州の間接行政を担う郡行政庁（Bezirkshauptmannschaft）の管轄区域。自治権を持たない純粋な行政管区であり、憲章都市15市と合わせて計94の政治地区を構成する。 | https://de.wikipedia.org/wiki/Politischer_Bezirk |
| AT_ADMIN_GERICHTSBEZIRK | 行政 | 2 | 司法管区（区裁判所管区） | Gerichtsbezirk | 113 | 統計参照 | 区裁判所（Bezirksgericht）の管轄区域。自治権を持たない司法行政単位であり、原則として複数の基礎自治体を束ねて政治地区の下位または同等に配置される（4桁コード）。 | https://de.wikipedia.org/wiki/Gerichtsbezirk |
| AT_ADMIN_STADTGEMEINDE | 行政 | 3 | 市（一般市） | Stadtgemeinde | 186 | 公的リスト確認済 | 連邦憲法第116条に基づく基礎自治体のうち、州法により「市（Stadt）」の称号を付与された自治体（憲章都市15市を除く）。法的権限や自治権の範囲は市場町・一般町村と同一。 | https://de.wikipedia.org/wiki/Gemeinde_(%C3%96sterreich) |
| AT_ADMIN_MARKTGEMEINDE | 行政 | 3 | 市場町（町） | Marktgemeinde | 771 | 公的リスト確認済 | 基礎自治体のうち、州法により「市場町（Markt）」の称号を付与された自治体。法的権限や自治権の範囲は一般市や一般町村と同一。 | https://de.wikipedia.org/wiki/Marktgemeinde |
| AT_ADMIN_GEMEINDE | 行政 | 3 | 町村（一般ゲマインデ） | Gemeinde (einfache Gemeinde / Landgemeinde) | 1,120 | 公的リスト確認済 | 憲章都市（15）・一般市（186）・市場町（771）の称号を持たない基礎自治体。連邦憲法第116条に基づく完全な地方自治権を有し、4種別合計で全2,092基礎自治体（LAU）を構成する。 | https://de.wikipedia.org/wiki/Gemeinde_(%C3%96sterreich) |
| AT_ADMIN_GEMEINDEBEZIRK | 行政 | 4 | 市区（都市内行政区） | Gemeindebezirk (Stadtbezirk) | 40 | 統計参照 | ウィーン市（23区）およびグラーツ市（17区）に置かれる都市内の下部行政区。独立した法人格はなく、市の内部行政単位として機能する。 | https://de.wikipedia.org/wiki/Wiener_Gemeindebezirke |
| AT_ADMIN_KATASTRALGEMEINDE | 行政 | 4 | 地籍区（カダスター区） | Katastralgemeinde (KG) | 7,850 | 公的リスト確認済 | 測量法（VermG）および連邦計量・測量局（BEV）のデジタル地籍図（DKM）・土地登記簿の最小管理区域。自治権はないが、全行政境界の幾何学的構成単位となる。 | https://de.wikipedia.org/wiki/Katastralgemeinde |
| AT_STAT_NUTS1 | 統計 | 1 | NUTS 1 大地域 | NUTS-1 Großregion | 3 | 公的リスト確認済 | 欧州連合（Eurostat）地域統計分類の第1階層（東・南・西オーストリアの3地域）。行政機関や自治権を持たない統計集計単位。 | https://de.wikipedia.org/wiki/NUTS:AT |
| AT_STAT_NUTS2 | 統計 | 2 | NUTS 2 地域 | NUTS-2 Region | 9 | 公的リスト確認済 | 欧州連合（Eurostat）地域統計分類の第2階層。9つの連邦州（Bundesländer）と領域が1対1で完全一致する。 | https://de.wikipedia.org/wiki/NUTS:AT |
| AT_STAT_NUTS3 | 統計 | 3 | NUTS 3 地域 | NUTS-3 Region | 35 | 公的リスト確認済 | 欧州連合（Eurostat）地域統計分類の第3階層。複数の政治地区・憲章都市・司法管区の組み合わせで構成される広域統計単位。 | https://de.wikipedia.org/wiki/NUTS:AT |
| AT_STAT_ORTSCHAFT | 統計 | 4 | 集落・居住区（オルトシャフト） | Ortschaft | 約17,200 | 統計参照 | 基礎自治体の下位に置かれる伝統的な集落・字単位。統計局が5桁の固有識別子を付与し、住所体系（建物・番地）や年次人口統計の集計単位として運用される。 | https://de.wikipedia.org/wiki/Ortschaft |
| AT_STAT_ZAEHLBEZIRK | 統計 | 4 | 統計調査区（中分類：統計区） | Zählbezirk (Statistischer Bezirk) | 約2,600 | 推計 | 統計局（Statistik Austria）が設定する最小統計区の上位集計区域（7桁コード）。主要都市では都市機能・地区別に分割され、小規模町村では自治体領域と一致する。 | https://de.wikipedia.org/wiki/Z%C3%A4hlbezirk |
| AT_STAT_ZAEHLSPRENGEL | 統計 | 4 | 国勢統計調査区（最小統計区） | Statistischer Zählsprengel (ウィーンはZählgebiet) | 約8,900 | 統計参照 | 統計局が設定する行政境界準拠の最小統計単位（8桁コード）。登録ベース国勢調査や年次人口統計における最小の面的公表単位として機能する。 | https://de.wikipedia.org/wiki/Z%C3%A4hlsprengel |
| AT_METEO_WARNREGION_LAND | 気象 | 1 | 広域気象予報領域（連邦州） | Bundesland (Prognoseregion) | 9 | 公的リスト確認済 | 国立気象機関GeoSphere Austriaの広域天気予報・解説における第1階層単位であり、9連邦州の領域に一致する。 | https://de.wikipedia.org/wiki/GeoSphere_Austria |
| AT_METEO_WARNBEZIRK | 気象 | 2 | 気象警報発令区域（政治地区単位） | Warnbezirk (Politischer Bezirk / Meteoalarm) | 94 | 統計参照 | GeoSphere Austriaの気象警報システムおよび欧州Meteoalarmにおける警報発令の基準単位。原則として94の政治地区（郡・憲章都市）の境界に準拠する。 | https://de.wikipedia.org/wiki/Meteoalarm |

### 2.2 国勢調査・統計調査区の体系（将来用ストック）

- **所管統計機関名・公式ポータルURL**: オーストリア統計局（公用語名: Bundesanstalt Statistik Österreich / 通称: Statistik Austria）が国家統計および国勢調査を一元的に所管している。公式ポータル（`https://www.statistik.at/`）、地域区分・統計区解説ページ（`https://www.statistik.at/services/tools/regionale-internationale-daten/regionale-daten-und-gliederungen/regionale-gliederungen`）、およびオープンデータカタログ（`https://data.statistik.gv.at/web/catalog.jsp`）を通じて統計表・空間境界データが公開されている。
- **基礎自治体より細かい統計調査単位の階層構造・単位名称・件数規模**: オーストリアは行政記録（中央住民登録［ZMR］、建物・住宅登録［AGWR］等）を連結する登録ベース国勢調査（Registerzählung）を採用しており、全2,092の基礎自治体（Gemeinde）の下位に複数の空間集計単位が重層的に配置されている。行政・統計直系の階層としては、まず基礎自治体と最小統計区の中間に7桁コード（GKZ 5桁＋2桁連番）を持つ中分類の「統計区（Zählbezirk / Statistischer Bezirk：全国約2,600件規模）」が置かれ、下位調査区が10個以下の町村では自治体領域と一致（下2桁 `00`）する一方、ウィーン市（23行政区の下に約250区を設定）やヴェルス市（9区に分割）等の都市部では都市構造・機能別の実質的な地区単位（Echte Zählbezirke）として機能する。その直下に位置する最小の行政境界準拠単位が8桁コード（GKZ 5桁＋Zählbezirk 2桁＋1桁連番、ウィーンのみ下3桁 `010`〜）を持つ「国勢統計調査区（Statistischer Zählsprengel / ウィーン市内は Zählgebiet：全国約8,900件規模）」であり、原則として人口2,000人以上の自治体を対象に1区あたり平均人口約1,000人（300〜2,000人規模）で画定され、人口・世帯・住宅・建物構造データの最小面的公表単位となる。これらと並行して、伝統的な集落単位であり住所・番地体系の基礎となる5桁コードの「集落・居住区（Ortschaft：約17,200件規模）」、連邦計量・測量局（BEV）が管轄するデジタル地籍図（DKM）の単位である5桁コードの「地籍区（Katastralgemeinde: KG：全国7,850件、うち土壌評価対象7,778件）」でも毎年1月1日現在の人口統計および土地利用統計（Regionalinformation）が集計される。さらに、行政境界に依存しない幾何学的集計単位として、建物・住宅登録（AGWR II）の建物入口座標を空間結合した「地域統計メッシュ（Regionalstatistische Rastereinheiten：100m×100m、250m×250m、500m×500m、1km×1km等）」が標準提供されている。
- **統計調査区境界データ（Shapefile/GeoJSON等）の入手先URL・更新頻度**: 国勢統計調査区（Zählsprengel）のポリゴンデータは、Statistik Austriaオープンデータカタログ（`https://data.statistik.gv.at/web/catalog.jsp`）および政府オープンデータポータル data.gv.at（`https://www.data.gv.at/datasets/11571547-64e8-3565-a6e3-f94461611fd2`）にてShapefile形式（座標系: `EPSG:31287`）で無償配布されており、更新頻度は年1回（毎年1月1日の領域基準［Gebietsstand 01.01.YYYY］・前年12月31日データ基準として公開）である。一方、地籍区（Katastralgemeinde）から基礎自治体・政治地区・司法管区・連邦州までの公式境界を収録する行政境界データベース（Verwaltungsgrenzen: VGD）は、BEV製品ポータル（`https://www.bev.gv.at/Services/Produkte/Kataster-und-Verzeichnisse/Verwaltungsgrenzen.html`）および data.gv.at（全国1:250,000版 `https://www.data.gv.at/datasets/d960f393-0a19-43f7-b2f1-2a79d9fc6fdd`、ウィーン地籍精度版 `https://www.data.gv.at/datasets/1a22d558-544a-46c1-95b9-baa77d2bb485`）にてShapefile形式（`EPSG:31287`、地籍精度・1:50,000・1:250,000の3段階）で無償提供されており、更新頻度は年2回（毎年4月・10月のDKM基準データが各1四半期後に公開）となっている。

### 2.3 「政庁所在地（役所・庁舎の点座標）」の公式定義とデータ有無

- 各自治体の代表点座標として、BEVの行政境界データ（VGD）やStatistik Austriaの自治体境界ポリゴン単体には庁舎の点座標レイヤーは含まれておらず、ポリゴン単体から算出する場合は「行政領域の幾何学的重心（Centroid）」となるが、オーストリアでは公的台帳データを組み合わせることで「市役所・町村役場（Rathaus / Gemeindeamt）の正確な建物位置座標（Point）」を公的データから確定的に取得する仕組みが確立されている。具体的には、Statistik Austriaの自治体台帳『Gemeindeverzeichnis』に全2,092基礎自治体の自治体コード（GKZ）と「役場（Gemeindeamt）の郵便番号・公式所在地住所」が収録されており、これを測量法第9a条およびGWR法に基づきBEVとStatistik Austriaが運用する公式住所・建物登録（Adressregister / AGWR II）と照合することで、当該役場建物の7桁アドレスコード（Adresscode）・建物オブジェクト番号（Objektnummer）および国家測量座標系における建物代表点座標（原則として建物入口［Gebäudezugang］の正確なPoint座標）を抽出できる。このアドレス座標検索はBEVの公式オンライン地籍サービス（`https://kataster.bev.gv.at/`）やAPI、オープンデータ住所台帳から無償で利用可能である。さらに補助的な公的入手手段として、Statistik Austriaの自治体別統計カルテ（`http://www.statistik.at/blickgem/gemDetail.do?gemnr={5桁GKZ}`）に各自治体中心基準点の標高（Seehöhe）と経緯度（度分秒形式）が記載されているほか、BEVのデジタル景観モデル（DLM）やdata.gv.at上の州・自治体POIデータセット（例: 自治体別の「POI Gemeindeamt」CSV/Shapefile、`EPSG:31255` / `EPSG:31258` および `EPSG:4326` 収録）から役場庁舎のPoint座標を直接取得することもできる。

### 2.4 OpenStreetMap（OSM）admin_level 対照表

| admin_level | 本国の行政区画種別（公用語/日本語） | 該当件数目安 | 備考 |
| --- | --- | --- | --- |
| 2 | Republik Österreich / オーストリア共和国（国境） | 1 | 国家境界（boundary=administrative + admin_level=2）。 |
| 3 | （未使用 / 該当なし） | 0 | オーストリア国内のOSMマッピング規約では使用されない。 |
| 4 | Bundesland / 連邦州 | 9 | NUTS 2地域と完全一致。ISO3166-2=AT-1〜AT-9 タグが付与される。 |
| 5 | （未使用 / 該当なし） | 0 | オーストリア国内では未使用。 |
| 6 | Politischer Bezirk, Statutarstadt / 政治地区（郡）・憲章都市 | 94 | 79の政治地区（郡）および15の憲章都市。3桁の政治地区コード（ref:at:gkz=xxx）が付与される。 |
| 7 | （未使用 / 該当なし） | 0 | オーストリア国内では未使用。 |
| 8 | Gemeinde / 基礎自治体（市・市場町・町村） | 2,092 | LAU相当。5桁の自治体コード（ref:at:gkz=xxxyy）が付与される（ウィーンは4・6・8を兼ねる）。 |
| 9 | Stadtbezirk, Gemeindebezirk / 市区（都市内行政区） | 40 | ウィーン市の23区（Wiener Gemeindebezirke）およびグラーツ市の17区（Grazer Stadtbezirke）等で使用。 |
| 10 | Katastralgemeinde, Stadtteile / 地籍区・都市内地区（任意） | 約7,850 | 主に7,850の地籍区（Katastralgemeinde：5桁のKG番号）や一部都市の地区境界に任意（optional）で適用される。 |
| 11 | （未使用 / 該当なし） | 0 | オーストリア国内では未使用。 |

---

## 3. 公式コード体系とWikidataプロパティ

### 3.1 国内公式コード（自治体コード・統計区コード）

- **コード規格名、桁数ルール、体系の仕組み**: 行政・統計の中核となる識別子は、Statistik Austriaが管理する5桁の「自治体コード（Gemeindekennziffer: GKZ / 旧称: ÖSTAT-Nr.、フォーマット: `B PP GG`）」である。第1桁（`B`）は連邦州をアルファベット順に識別する番号（`1`=ブルゲンラント、`2`=ケルンテン、`3`=ニーダーエスターライヒ、`4`=オーバーエスターライヒ、`5`=ザルツブルク、`6`=シュタイアーマルク、`7`=チロル、`8`=フォアアールベルク、`9`=ウィーン）でISO 3166-2:ATの末尾番号と一致し、第2〜3桁（`PP`、上3桁 `BPP` で政治地区コード `Bezirkskennziffer`）は州内の憲章都市および政治地区（`01`から開始）、第4〜5桁（`GG`）は政治地区内の基礎自治体を識別する（例: `10304` ＝ ブルゲンラント州 `1` ＋ アイゼンシュタット＝ウムゲーブング郡 `03` ＋ ブライテンブルン `04`、ウィーン市は自治体全体が `90001`、23区が `90101`〜`92301`）。統計調査区コードはこの5桁のGKZを直接拡張した階層構造をとり、第6〜7桁に統計区（Zählbezirk：`00`から開始）を加えた7桁コード（`B PP GG ZZ`）、さらに第8桁に最小調査区（Zählsprengel：`0`から開始、ウィーン市内のZählgebietのみ下3桁 `010`〜）を加えた8桁コード（`B PP GG ZZ S`）として構成される。また、司法管区コード（Gerichtsbezirkskennziffer）は3桁の政治地区コードに1桁連番を付加した4桁コードとなる。一方、BEVが管理する地籍区番号（Katastralgemeindenummer: KG-Nr.）はGKZと同じ5桁の数字（例: アフィースル地籍区は `47301`）であるが、司法・測量管区に基づく独立した付番体系であるため、データベース設計においてはGKZ（Wikidata `P964`）とKG番号（`P8322`）を厳格に別カラムとして分離する必要がある。その他、集落（Ortschaft）には5桁の集落コード（OKZ）、AGWR IIの個別住所には `5000000` 以上の地域非依存の7桁アドレスコード（Adresscode）および7桁の建物オブジェクト番号（Objektnummer）が付与される。
- **最新版コードリストの入手先（国家統計局等の公式ダウンロードURL、ファイル形式）**: 最新の自治体コード（GKZ）、政治地区、司法管区、集落（Ortschaft）、統計調査区（Zählsprengel）の対応リストおよび人口表は、Statistik Austriaの地域区分ポータルページ（`https://www.statistik.at/services/tools/regionale-internationale-daten/regionale-daten-und-gliederungen/regionale-gliederungen`）およびオープンデータカタログ（`https://data.statistik.gv.at/web/catalog.jsp`）からCSV、XLSX、ODS、PDF形式で無償ダウンロードできる。また、BEVが管轄する全7,850地籍区（Katastralgemeinden）の公式コードリストは data.gv.at（`https://www.data.gv.at/datasets/10ebbd81-c823-4bf3-9455-36fb09803e82`）からCSVおよびXLSX形式で入手可能である。

### 3.2 国際・地域標準コード

- **ISO 3166-2コード（州・県・地域区分コード）**: 9つの連邦州（Bundesländer）に対して `ISO 3166-2:AT` コードが割り当てられており、ハイフン以降の数字は国内自治体コード（GKZ）の第1桁と完全に一致する。内訳は `AT-1`（Burgenland）、`AT-2`（Kärnten）、`AT-3`（Niederösterreich）、`AT-4`（Oberösterreich）、`AT-5`（Salzburg）、`AT-6`（Steiermark）、`AT-7`（Tirol）、`AT-8`（Vorarlberg）、`AT-9`（Wien）の9コードである。
- **地域標準コード（EU加盟国ならNUTS 1〜3およびLAUコード等）**: 欧州連合（Eurostat）の地域統計分類であるNUTS体系において、第1階層のNUTS 1は3大地域（`AT1`: Ostösterreich、`AT2`: Südösterreich、`AT3`: Westösterreich）、第2階層のNUTS 2は9連邦州と1対1で完全一致する9地域（`AT11`: Burgenland、`AT12`: Niederösterreich、`AT13`: Wien、`AT21`: Kärnten、`AT22`: Steiermark、`AT31`: Oberösterreich、`AT32`: Salzburg、`AT33`: Tirol、`AT34`: Vorarlberg）、第3階層のNUTS 3は複数の政治地区・憲章都市・司法管区の組み合わせから成る35地域（`AT111`〜`AT342`）として定義されている。下位のLAU（Local Administrative Units）階層は全2,092の基礎自治体（Gemeinde）に一致し、5桁の自治体コード（GKZ）がそのままLAUコードとして用いられる。

### 3.3 Wikidata抽出プロパティ（P番号）

- **自治体コードプロパティ番号**: オーストリアの自治体コード（Gemeindekennziffer: GKZ）にはプロパティ `P964`（Austrian municipality key）が割り当てられており、基礎自治体は5桁、政治地区（郡）は3桁の文字列として格納されている。これとは別に、5桁の地籍区番号（Katastralgemeinde-Nummer）には `P8322` が割り当てられており、国際・地域標準コードとしては `P300`（ISO 3166-2コード）、`P605`（NUTSコード）、`P402`（OpenStreetMapリレーションID）が利用される。
- **公式ウェブサイト（P856）、人口（P1082）、上位行政区画（P131）等の指定条件**: SPARQLクエリによる抽出時は、`P31`（instance of）に対して連邦州 `Q261543`、政治地区 `Q871419`、憲章都市 `Q262882`、基礎自治体全般 `Q667509`（サブクラスの一般市 `Q13539802` および市場町 `Q7930989` を含む）、地籍区 `Q1736127` を指定し、現行の2,092自治体のみを厳密に取得するため廃止日プロパティ（`wdt:P576`）を持たないこと（`FILTER NOT EXISTS { ?item wdt:P576 ?end }`）および `P964` ステートメントに終了日修飾子（`pq:P582`）が存在しないことを必須フィルタ条件とする。併せて、公式ウェブサイト（`P856`）、時点修飾子 `pq:P585` 付きの最新人口（`P1082`）、基礎自治体から政治地区・連邦州への階層ツリーを構築する上位行政区画（`P131`）、代表点地理座標（`P625`）、海抜標高（`P2044`）、面積（`P2046`）、郵便番号（`P281`）を取得対象として指定する。

---

## 4. 気象機関・予報区・観測網

### 4.1 国家気象機関と予報区体系（陸上および海上）

- **国家気象機関名（公用語 / 英語 / 日本語）および公式サイトURL**: 公用語名称は「GeoSphere Austria — Bundesanstalt für Geologie, Geophysik, Klimatologie und Meteorologie」、英語名称は「GeoSphere Austria — Federal Institute for Geology, Geophysics, Climatology and Meteorology」、日本語名称は「オーストリア国立地質・地球物理・気候・気象研究所（通称: GeoSphere Austria）」である。公式サイトは `https://www.geosphere.at/`、気象警報ポータルは `https://warnungen.zamg.at/`、オープンデータポータル（Data Hub）は `https://data.hub.geosphere.at/` で運用されている。
- **陸上気象予報区の階層構造および公式API/JSON等の有無**: 陸上予報区は、第1階層の広域予報領域として9つの連邦州（Bundesländer）、第2階層の気象警報発令単位（Warnbezirke：欧州気象警報網 Meteoalarm と連動）として94の政治地区・憲章都市（Politischer Bezirk / Statutarstadt）に準拠した区域が設定されており、強風・大雨・大雪・凍結・雷雨・猛暑・寒波の7要素について4段階の警戒レベルで警報が発令される。さらに第3階層として、全2,092基礎自治体別のピンポイント予報および全国を1km×1kmメッシュ（1時間または15分分解能）で解析・予測する統合ナウキャストシステム「INCA（Integrated Nowcasting through Comprehensive Analysis）」（APIエンドポイント: `inca-v1-1h-1km` 等）が運用されている。公式APIとしてREST形式の「GeoSphere Austria Dataset API」（`https://dataset.api.hub.geosphere.at/v1/`）が無償公開（認証不要、CC BY 4.0）されており、JSON、GeoJSON、CSV、NetCDF形式で観測値・予測値・グリッドデータを取得できる。なお、旧ドメイン `*.hub.zamg.ac.at` からのHTTPリダイレクトは2026年1月15日をもって完全に終了しているため、システム実装時は必ず現行ドメイン `https://dataset.api.hub.geosphere.at/` を指定する必要がある。
- **海上予報区・沿岸警報区の有無と体系**: オーストリアは内陸国であるため海上予報区や沿岸警報区は存在しない。ただし、内水面の気象安全管理として、ボーデン湖、ノイジードラー湖、アッター湖、トラウン湖、ヴェルター湖などの主要湖沼において、湖岸の光学点滅標識と連動した湖沼強風・暴風警報（Sturmwarnung：毎分40回点滅のオレンジ光による強風注意［Starkwindwarnung］および毎分90回点滅による暴風警報［Sturmwarnung］）が運用されている。

### 4.2 地上気象観測網と観測所地点リスト入手先

- **観測網の名称**: 地上気象観測の基幹ネットワークは「TAWES（Teilautomatisches Wettererfassungssystem：半自動気象観測システム）」と呼称され、これと一体的にWMO国際通報用の「SYNOP観測網」および長期気候監視用の「Klimastationen（気候観測網）」が運用されている。
- **観測所ネットワークの規模（総地点数、観測要素ごとの地点数内訳）**: TAWESリアルタイム観測網は全国に約271地点が展開されており、10分間隔で気温、湿度、気圧、風向・風速、降水量、日射量、日照時間、積雪深の8要素群を自動計測し、ウィーン本庁（Hohe Warte）へリアルタイム伝送している。このTAWES約271地点のうち約150地点がWMO基準のSYNOP観測所に分類されており、さらにそのうちの約65地点では自動計測に加えて現地観測員による目視・補足観測（雲量、視程、現在天気現象、地面状態等）が実施されている。また、品質検証済みの気候データセット（`klima-v2-10min`、`klima-v2-1h`、`klima-v2-1d`、`klima-v2-1m`）には、現行TAWES地点に加えて過去の廃止地点や提携観測所を含む拡大地点群が収録される一方、新設直後の観測所や臨時観測所はリアルタイム生データ（`tawes-v1-10min`）のみに含まれる場合がある。
- **地点マスターデータ（観測所番号、観測所名、所在地、緯度・経度、標高）の公式ダウンロードURL・API仕様・ファイル形式**: 観測所地点マスターデータは、Dataset APIのメタデータエンドポイントであるTAWES現行10分値地点マスター（`https://dataset.api.hub.geosphere.at/v1/station/current/tawes-v1-10min/metadata`）、TAWES過去10分値地点マスター（`https://dataset.api.hub.geosphere.at/v1/station/historical/tawes-v1-10min/metadata`）、検証済み気候1時間値地点マスター（`https://dataset.api.hub.geosphere.at/v1/station/historical/klima-v2-1h/metadata`）、およびSYNOP 1時間値地点マスター（`https://dataset.api.hub.geosphere.at/v1/station/historical/synop-v1-1h/metadata`）からJSON形式で直接取得できる。返却されるJSONの `stations` 配列には、各観測所の `id`（観測所番号）、`name`（観測所名）、`state`（所属連邦州）、`lat`（緯度：`EPSG:4326`）、`lon`（経度：`EPSG:4326`）、`altitude`（海抜標高［m］）、`valid_from`（観測開始日）、`valid_to`（観測終了日）が構造化されて格納されており、観測データ本体もクエリ指定によりGeoJSONまたはCSV形式（時刻系はすべてUTC）で取得可能である。

---

## 5. 探索・GIS環境・出典メタデータ

### 5.1 公的オープンデータの出典メタデータ一覧（data_sources.csv 登録用表）

| source_id | category | source_name_ja | provider_ja | license | url | attribution_required | terms_summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT_STAT_REGIONAL | 統計・行政コード | オーストリア地域区分・自治体台帳・統計調査区データ | オーストリア統計局（Statistik Austria） | CC BY 4.0 | https://data.statistik.gv.at/web/catalog.jsp | Yes | 商用・非商用とも無償利用可。利用時は「Quelle: STATISTIK AUSTRIA」の出典明記が必須。 |
| AT_BEV_VGD | 行政境界・地籍区 | 行政境界データベース（Verwaltungsgrenzen: VGD）および地籍区一覧 | 連邦計量・測量局（BEV） | CC BY 4.0 | https://www.bev.gv.at/Services/Produkte/Kataster-und-Verzeichnisse/Verwaltungsgrenzen.html | Yes | DKMに基づく地籍区・自治体・郡・司法管区・州境界のShapefile。年2回無償公開。「© BEV」の帰属表示が必須。 |
| AT_BEV_KATASTER | 地籍・住所・建物座標 | 公式地籍・住所台帳ウェブサービス（kataster.bev.gv.at / Adressregister） | 連邦計量・測量局（BEV） | CC BY 4.0 (BEV OGD) | https://kataster.bev.gv.at/ | Yes | 全国約1,020万筆の地籍・住所・建物座標への無料アクセスおよびAPI連携を提供。BEV利用規約に基づく出典表示が必須。 |
| AT_GEOSPHERE_HUB | 気象・観測網 | GeoSphere Austria Data Hub（TAWES・SYNOP・気候・INCA） | オーストリア国立地質・地球物理・気候・気象研究所（GeoSphere Austria） | CC BY 4.0 | https://data.hub.geosphere.at/ | Yes | EU高価値データセット（HVD）準拠。リアルタイム観測・気候値・メッシュ解析をAPIで無償提供。「Quelle: GeoSphere Austria」の明記が必須。 |
| AT_BASEMAP | 背景地図・オルソ画像 | オーストリア公式行政背景地図（basemap.at） | オーストリア9連邦州（geoland.at）・BEV・都市連盟 | CC BY 4.0 | https://basemap.at/ | Yes | 行政公式データ100%のWMTS/ベクトル背景地図およびオルソ航空写真。「Quelle: basemap.at」の帰属表示で無償利用可。 |
| AT_DATA_GV | 総合オープンデータ | オーストリア政府オープンデータポータル（data.gv.at） | 連邦政府・各連邦州・自治体 | CC BY 4.0 | https://www.data.gv.at/ | Yes | 約74,000件以上の公的データセットを収録する国家カタログ。原則CC BY 4.0が適用され各提供機関名の明記が必須。 |

### 5.2 標準測地系・投影法・EPSGコード

- **公式GISデータで採用されている標準測地系・EPSGコード（WGS84への変換要否）**: オーストリアの全国規模の公的空間データ（Statistik Austriaの統計調査区ポリゴンやBEVの行政境界データVGD等）では、ベッセル1841楕円体に基づく国内測地系MGI（Militär-Geographisches Institut）のランベルト正角円錐図法である **`EPSG:31287`（MGI / Austria Lambert）** が標準採用されており、グローバル標準のWGS84（`EPSG:4326`）データベースへ統合する際には**座標変換（Reprojection）が必須**である。また、地籍図や各連邦州・基礎自治体の大縮尺GISデータでは、ガウス・クリューゲル3度帯投影（中央子午線別に西からM28・M31・M34の3ゾーン）である **`EPSG:31254`（MGI / Austria GK West）**、**`EPSG:31255`（MGI / Austria GK Central）**、**`EPSG:31256`（MGI / Austria GK East：ウィーン市オープンデータ等の標準）** が標準推奨されており（一部では北方オフセット-5,000,000mを適用しない `EPSG:31257`〜`31259` やフェロ子午線基準の `EPSG:31251`〜`31253` も使用）、これらもすべて **`EPSG:4326` への変換が必須**となる。MGI系座標からWGS84（`EPSG:4326`）やWebメルカトル（`EPSG:3857`）へ変換する際は、楕円体間の差異を補正する7パラメータ変換またはBEV公式のNTv2グリッド変換（AT_GIS_GRID）を適用しないと数十メートルの位置ズレが生じるため、GDAL/PROJやPostGISでの変換パラメータ指定に注意を要する。一方、EU INSPIRE指令準拠データで用いられる **`EPSG:3416`（ETRS89 / Austria Lambert）** および **`EPSG:4258`（ETRS89）** はGRS80楕円体ベースであり、またGeoSphere Austriaの気象観測所メタデータ・API出力は最初から **`EPSG:4326`（WGS 84）** で提供されているため、気象データは測地系変換なしでそのまま利用可能である。

### 5.3 公式背景地図タイルとストリートビュー状況

- **公式背景地図タイル（WMTS/XYZタイルURL）**:
  - オーストリア9連邦州（geoland.at）、BEV、オーストリア都市連盟の共同事業による公式背景地図 **`basemap.at`** がオープンデータ（CC BY 4.0）として無償提供されており、標準地図は隔月更新、オルソ航空写真（全国標準解像度29cm、詳細域15cm、ズームレベル17〜18に撮影年透かし入り）は年次更新、さらに2026年第3四半期にはベクトルタイル版も展開されている。
  - Webメルカトル（`EPSG:3857`）に対応したWMTS GetCapabilities URLは `https://www.basemap.at/wmts/1.0.0/WMTSCapabilities.xml`（または `https://maps.wien.gv.at/basemap/1.0.0/WMTSCapabilities.xml`）
  - XYZ / WMTS RESTタイルURLテンプレート:
    - 標準地図（Standard）: `https://maps.wien.gv.at/basemap/geolandbasemap/normal/google3857/{z}/{y}/{x}.png`
    - グレースケール地図（Grau）: `https://maps.wien.gv.at/basemap/bmapgrau/normal/google3857/{z}/{y}/{x}.png`
    - 高解像度地図（HighDPI）: `https://maps.wien.gv.at/basemap/bmaphidpi/normal/google3857/{z}/{y}/{x}.jpeg`
    - オルソ航空写真（Orthofoto）: `https://maps.wien.gv.at/basemap/bmaporthofoto30cm/normal/google3857/{z}/{y}/{x}.jpeg`
    - 地名・道路透過オーバーレイ（Overlay）: `https://maps.wien.gv.at/basemap/bmapoverlay/normal/google3857/{z}/{y}/{x}.png`

- **ストリートビューおよび類似パノラマサービス各社のカバレッジ状況**:
  - **Google ストリートビュー**: ウィーン、グラーツ、リンツ、ザルツブルク、インスブルック等の主要都市圏や幹線道路網（アウトバーン・連邦道路）、および各基礎自治体の中心街路を広くカバー。自治体庁舎（Rathaus / Gemeindeamt）や気象観測所の外観・設置環境確認に有効（農山村の生活道路等には一部未撮影区間あり）。
  - **Apple Look Around（Apple Maps）**: 2021年7月からの車両・歩行撮影を経て、**2023年4月にオーストリア全土で公式ローンチ**。ウィーンをはじめとする全国の主要幹線道路・都市部・基礎自治体を高解像度360度パノラマでフルカバーしており、Googleストリートビューと同等以上の高精細画質で閲覧可能。
  - **Yandex パノラマ（Yandex Panoramas）**: ロシア、ベラルーシ、カザフスタン、ウズベキスタン、トルコ等を中心としたサービスであり、**オーストリア国内のストリートビューカバレッジは提供されていない（ゼロ）**。
  - **百度全景（Baidu Total View）**: 中国国内特化のパノラマ機能であり、**オーストリア国内のストリートビューカバレッジは一切なし（ゼロ）**（※2Dベクター地図のみHERE等からの提供データで閲覧可能）。
  - **Mapillary（Meta傘下） / KartaView（オープン系ストリートビュー）**: オーストリア国内のOSMコミュニティや一般ユーザーによる走行撮影が極めて活発。Google/Appleが未撮影の地方道、農道、生活道路、山岳ハイキング道まで多数の走行パノラマ画像がCC BY-SA 4.0で公開されており、探索補完手段として極めて有用。
  - **現地独自サービス**: ウィーン市公式GISが提供する街路画像サービス「Kappazunder」や、各連邦州公式Web GIS（TIRIS、DORIS、NÖ Atlas、SAGIS、GIS-Steiermark等）が公開している15cm〜29cm級の超高解像度オルソ航空写真・斜め航空写真が利用可能。

---

## 6. 一次情報源・公式オープンデータ入手先リンク集

- **自治体・統計調査区オープンデータURL**: Statistik Austria 地域区分・自治体台帳・統計区総合ポータル（`https://www.statistik.at/services/tools/regionale-internationale-daten/regionale-daten-und-gliederungen/regionale-gliederungen`）、Statistik Austria オープンデータカタログ（`https://data.statistik.gv.at/web/catalog.jsp`）、国勢統計調査区（Statistische Zählsprengel）Shapefileダウンロードページ（`https://www.data.gv.at/datasets/11571547-64e8-3565-a6e3-f94461611fd2`）、Zählsprengel・Ortschaften・Katastralgemeinden別人口統計ODSダウンロードページ（`https://www.statistik.at/statistiken/bevoelkerung-und-soziales/bevoelkerung/bevoelkerungsstand/bevoelkerung-zu-jahres-/-quartalsanfang`）、BEV 行政境界データベース（Verwaltungsgrenzen: VGD）公式ページ（`https://www.bev.gv.at/Services/Produkte/Kataster-und-Verzeichnisse/Verwaltungsgrenzen.html`）、BEV 地籍区（Katastralgemeinden）公式リスト（`https://www.data.gv.at/datasets/10ebbd81-c823-4bf3-9455-36fb09803e82`）、およびBEV 地域情報（Regionalinformation：地籍区別面積・土地利用統計）（`https://www.bev.gv.at/Services/Produkte/Kataster-und-Verzeichnisse/Regionalinformation.html`）。
- **政府GIS・公式背景地図ポータルURL**: オーストリア公式背景地図ポータル basemap.at（`https://basemap.at/` / 英語版 `https://basemap.at/en/`）、basemap.at WMTS Capabilities XML（`https://www.basemap.at/wmts/1.0.0/WMTSCapabilities.xml`）、BEV 公式オンライン地籍・住所検索サービス（`https://kataster.bev.gv.at/`）、Statistik Austria Web GIS「STATatlas - Regionale Gliederungen」（`https://www.statistik.at/atlas/?mapid=topo_regionale_gliederung_oesterreich&layerid=layer5`）、およびオーストリア政府総合オープンデータポータル（`https://www.data.gv.at/`）。
- **国家気象機関・観測データ・APIダウンロードURL**: GeoSphere Austria Data Hub トップページ（`https://data.hub.geosphere.at/`）、地上気象観測所データセット一覧（`https://data.hub.geosphere.at/group/stationsdaten`）、TAWES 10分値リアルタイム観測データセット（`https://data.hub.geosphere.at/dataset/tawes-v1-10min`）、検証済み気候観測データセット1時間値（`https://data.hub.geosphere.at/dataset/klima-v2-1h`）および月次値（`https://data.hub.geosphere.at/en/dataset/klima-v2-1m`）、SYNOP観測データセット1時間値（`https://data.hub.geosphere.at/en/dataset/synop-v1-1h`）、Dataset API 現行TAWES観測所地点マスターJSONエンドポイント（`https://dataset.api.hub.geosphere.at/v1/station/current/tawes-v1-10min/metadata`）、およびDataset API 公式ドキュメント・変更履歴（`https://dataset.api.hub.geosphere.at/v1/docs/changelog.html`）。
