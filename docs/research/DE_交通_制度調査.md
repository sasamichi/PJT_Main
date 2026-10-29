# ドイツ 交通網・インフラ制度 事前調査シート

- 調査日: 2026-10-28
- 根拠法令・公式資料: 連邦遠距離道路法（Bundesfernstraßengesetz: FStrG）、道路交通令（Straßenverkehrs-Ordnung: StVO）、各連邦州道路法（Straßengesetze der Länder）、一般鉄道法（Allgemeines Eisenbahngesetz: AEG）、鉄道建設・運行規則（Eisenbahn-Bau- und Betriebsordnung: EBO）、狭軌鉄道建設・運行規則（ESBO）、旅客運送法（Personenbeförderungsgesetz: PBefG）、路面電車建設・運行規則（Straßenbahn-Bau- und Betriebsordnung: BOStrab）、連邦水路法（Bundeswasserstraßengesetz: WaStrG）、内陸水運任務法（BinSchAufgG）、海洋航運任務法（SeeAufgG）、航空法（Luftverkehrsgesetz: LuftVG）、連邦デジタル・交通省（BMDV / BMV）、連邦鉄道庁（Eisenbahn-Bundesamt: EBA）、Die Autobahn GmbH des Bundes、DB InfraGO AG、連邦水路・航運局（WSV）、連邦航空局（LBA）、国家モビリティデータポータル（Mobilithek / DELFI e.V.）

## 1. 道路網制度の詳細分類

### 1.1 道路法体系と詳細種別一覧

| 大分類 | 中分類・法的名称（公用語） | 日本語相当 | 根拠法律 | 管理主体 | 全体規模目安 | 初期自動収集(〇/×) |
| --- | --- | --- | --- | --- | --- | --- |
| 連邦遠距離道路（Bundesfernstraßen） | Bundesautobahn (BAB / A) | 連邦高速道路（アウトバーン） | 連邦遠距離道路法（FStrG § 1 Abs. 2 Nr. 1）、道路交通令（StVO Zeichen 330.1） | 連邦（連邦直轄公社 Die Autobahn GmbH des Bundes が計画・建設・維持管理・交通管制を一元実施） | 約13,200 km | 〇 |
| 連邦遠距離道路（Bundesfernstraßen） | Bundesstraße (B) | 連邦道路（一般国道相当） | 連邦遠距離道路法（FStrG § 1 Abs. 2 Nr. 2） | 連邦（基本法第90条の連邦委託管理［Auftragsverwaltung］により原則として各連邦州の道路建設局が管理。一部都市圏はAutobahn GmbH、人口8万人超の自治体の市街地通過区間［Ortsdurchfahrten, FStrG § 5］は当該市町村が管理） | 約38,000 km | 〇 |
| 州道（Landesstraßen） | Landesstraße (L) / Staatsstraße (St / S) | 州道（都道府県道相当。バイエルン州は「Staatsstraße (St)」、ザクセン州は「Staatsstraße (S)」、他12州は「Landesstraße (L)」と呼称） | 各連邦州の道路法（Straßengesetze der Länder） | 各連邦州の道路建設局（Straßenbauverwaltungen der Länder。都市州であるベルリン・ハンブルクには当該区分なし） | 約87,000 km | 〇 |
| 郡道（Kreisstraßen） | Kreisstraße (K) | 郡道（地域幹線・郡内連絡道） | 各連邦州の道路法（Straßengesetze der Länder） | 各郡（Landkreise）および郡独立市（Kreisfreie Städte） | 約92,000 km | 〇 |
| 市町村道（Gemeindestraßen） | Gemeindestraße (Innerortsstraße / Ortsverbindungsstraße) | 市町村道（都市内幹線道路・地区集散道路・生活道路） | 各連邦州の道路法（Straßengesetze der Länder） | 各市町村（Gemeinden / Städte） | 約600,000 km | ×（都市内主要幹線のみ探索時補完） |
| その他道路（対象外） | Sonstige öffentliche Straßen / Eigentümerwege (Wirtschaftswege, Forstwege, Privatstraßen) | 農道・林道・経済道・私道・歩道・自転車専用道 | 各連邦州道路法・連邦森林法・民法 | 森林管理署・土地改良組合・私人・基礎自治体 | 計測対象外 | × |

### 1.2 付番ルール・管理者・OSMタグ対照表

| 道路種別（公用語） | 路線プレフィックス・付番範囲 | 標識様式（StVO） | 主な管理主体 | OSM主タグ（highway=*） | OSM付番タグ（ref=*） |
| --- | --- | --- | --- | --- | --- |
| Bundesautobahn | A 1 〜 A 999 | 青地白文字・六角形（Zeichen 405） | Die Autobahn GmbH des Bundes | highway=motorway | ref=A 1（空白あり標準） |
| Bundesstraße（自専道規格：Kraftfahrstraße） | B 1 〜 B 588（および枝番 n/a） | 黄地黒文字・角丸長方形（Zeichen 401）＋Zeichen 331.1 | 各州道路建設局（一部Autobahn GmbH） | highway=trunk（分離帯付多車線）または highway=primary + motorroad=yes | ref=B 1 |
| Bundesstraße（一般規格） | B 1 〜 B 588 | 黄地黒文字・角丸長方形（Zeichen 401） | 各州道路建設局／大都市自治体 | highway=primary | ref=B 30 |
| Landesstraße / Staatsstraße | L 1〜 / St 2001〜 / S 1〜 | 現地案内標識には原則非表示（キロポスト・台帳表示のみ） | 各州道路建設局／大都市自治体 | highway=secondary | ref=L 100 / ref=St 2070 / ref=S 100 |
| Kreisstraße | K 1〜 または <ナンバープレート地域符号> 1〜 | 現地案内標識には原則非表示（キロポスト・台帳表示のみ） | 各郡（Landkreis）／郡独立市 | highway=tertiary | ref=K 6012 / ref=M 12 |
| Gemeindestraße | 原則付番なし（道路名 name=* 管理） | 道路名標識（Straßennamensschild） | 各市町村（Gemeinde / Stadt） | highway=unclassified / residential / living_street | なし |

- **連邦高速道路（A1〜A999）および連邦道路（B1〜B588）の付番規則と地域コード構造**: 連邦高速道路（Bundesautobahn）の付番は、偶奇による方向識別と桁数によるネットワーク階層の2軸で体系化されている。方向別原則として、奇数番号は南北方向（Nord-Süd：例 `A 1`, `A 3`, `A 5`, `A 7`, `A 9`、国内最長路線は南北縦断の `A 7`）、偶数番号は東西方向（West-Ost：例 `A 2`, `A 4`, `A 6`, `A 8`）の路線に割り当てられる。桁数別では、1桁（`A 1`〜`A 9`）が国土を縦横断する国家基幹路線および国際連絡幹線を構成し、2桁（`A 10`〜`A 99`）が広域リージョン幹線および都市圏外環道を構成する。2桁路線の十の位は地域ゾーンを表し、`A 10〜A 19` がベルリン首都圏・ブランデンブルク・メクレンブルク＝フォアポンメルン・ザクセン東部（`A 10` はベルリン外環状線 Berliner Ring）、`A 20〜A 29` が北ドイツ（シュレースヴィヒ＝ホルシュタイン、ハンブルク、ニーダーザクセン北部）、`A 30〜A 39` がニーダーザクセン中南部・ヴェストファーレン北部・ザクセン＝アンハルト南部〜テューリンゲン北部、`A 40〜A 49` がライン・ルール大都市圏（NRW州）およびヘッセン州北部、`A 52〜A 59` がニーダーライン・ケルン／ボン都市圏、`A 60〜A 67` がラインラント＝プファルツ・ザールラント・ライン＝マイン都市圏、`A 70〜A 73` がフランケン地方（バイエルン北部）〜テューリンゲン南部、`A 81` がバーデン＝ヴュルテンベルク州、`A 90〜A 99` がバイエルン州中南部・アルプス連絡線（`A 99` はミュンヘン環状線）に対応する。3桁（`A 100`〜`A 999`）は都市内高速道路（ベルリン都市高速 `A 100` 等）、都市導入支線（Zubringer）、空港アクセス線、ジャンクション間短絡線に割り当てられ、百の位の数字は2桁路線の十の位と同一の地域ゾーンに準拠する。一方、連邦道路（Bundesstraße）は1桁（`B 1`〜`B 9`）が全国基幹道、2桁（`B 10`〜`B 99`）が地域ブロック別主要幹線（南ドイツ `B 10〜B 29`、南西部 `B 30〜B 39`、中西部 `B 40〜B 59`、北西部 `B 60〜B 79`、北部・東部 `B 80〜B 99`）、3桁（`B 100`〜`B 588`）が地域補完連邦道路網（`B 100〜B 399` は地域別細分、`B 400〜B 588` は追加指定路線）であり、バイパス新設区間や支線には `B 1n`（neu）や `B 26a` 等のサフィックスが付与される。
- **OSMにおける道路タグとの対照関係および州・郡道コードの正規化要件**: OpenStreetMap（OSM）におけるドイツ道路網のタグ付けは、法的道路種別と物理的道路構造の双方を反映している。連邦高速道路（Autobahn）は道路交通令（StVO）の標識 Zeichen 330.1 で指定され、一意に `highway=motorway` および `ref=A <番号>`（英字と数字の間に半角スペースを入れるのがドイツOSM標準）が対応する。連邦道路（Bundesstraße）は、一般規格区間が `highway=primary` にマッピングされる一方、中央分離帯を備えた多車線の自動車専用道路規格区間（Gelbe Autobahn / Kraftfahrstraße, Zeichen 331.1）は `highway=trunk`（または `highway=primary` + `motorroad=yes`）として表現されるため、GISデータベースへの初期自動収集時には `ref ~ "^B [0-9]+"` の正規表現フィルタを `highway=trunk` と `highway=primary` の双方に適用する必要がある。州道（`highway=secondary`）は12州で `L`（Landesstraße）、バイエルン州で `St`（Staatsstraße）、ザクセン州で `S`（Staatsstraße）のプレフィックスを持ち、郡道（`highway=tertiary`）は多くの州で `K <番号>`（例：`K 6012`）と表記されるが、バイエルン州およびザクセン州等の一部の連邦州では「当該郡または郡独立市の自動車登録番号標コード（Kfz-Kennzeichen。郡独立市は小文字 `s` を付加）＋路線番号」（例：ミュンヘン郡 `M 12`、アウグスブルク市 `As 5`）の形式が公式台帳およびOSMの `ref` タグで用いられるため、パーサー設計時には州別のプレフィックス辞書を定義する必要がある。また、道路機能等級を規定する交通工学指針（RIN: Richtlinien für integrierte Netzgestaltung）では、自動車交通網を `AS`（Autobahnen）、`LS`（Landstraßen）、`VS`（都市内非沿道型幹線）、`HS`（都市内沿道型幹線）、`ES`（地区集散・生活道路）の5階層に分類し、自転車・歩行者交通網を市街地外の `AR`/`AF` と市街地内の `IR`/`IF` に区分しており、これが都市計画GISの属性スキーマと連動している。
- **連邦直轄公社（Die Autobahn GmbH des Bundes）と各州道路建設局の管理分担およびGIS標準**: 連邦遠距離道路（Bundesfernstraßen）のうち、連邦高速道路網は連邦政府100%出資のインフラ公社である **Die Autobahn GmbH des Bundes**（本社：ベルリン、全国10支社［Niederlassungen：Nord, Nordwest, Westfalen, Rheinland, West, Südwest, Nordbayern, Südbayern, Ost, Nordost］および9つの交通管制センター体制）が計画・建設・維持管理・交通管制システム（AutobahnOS）を一元的に管轄している。一方、連邦道路（Bundesstraße）は原則として各連邦州の道路建設局（ノルトライン＝ヴェストファーレン州の `Straßen.NRW`、ニーダーザクセン州の `NLStBV`、ヘッセン州の `Hessen Mobil`、バーデン＝ヴュルテンベルク州の `Regierungspräsidien`、バイエルン州の `Staatliche Bauämter` 等）が連邦委託管理（Auftragsverwaltung）として州道（L/St/S）と一体的に管理し、人口8万人を超える自治体の市街地通過区間（Ortsdurchfahrten, FStrG § 5）のみ当該市町村が道路管理権を担う。データモデリング上の重要仕様として、連邦および全16州の道路台帳GISは「道路情報バンク指針（ASB: Anweisung Straßeninformationsbank）」に基づく「道路網ノード（Netzknoten: NK）間のセクション（Abschnitt）と距離標（Stationierung）」による線形参照モデルで統一されており、CAD・GISデータの公式交換フォーマットには国家標準 **OKSTRA（Objektkatalog für das Straßen- und Verkehrswesen）**（XML形式、Version 1.015 / 2.017〜2.019等）が採用されている。

## 2. 鉄軌道・索道制度の詳細分類

### 2.1 鉄軌道・都市交通・索道の法体系一覧

| 大分類 | 根拠法律・条文 | 法的種別（公用語） | 日本語・技術分類 | 主な運行都市・対象路線例 | 初期収集(〇/×) |
| --- | --- | --- | --- | --- | --- |
| 一般鉄道（標準軌公共鉄道） | 一般鉄道法（AEG § 1, § 2, § 26）、鉄道建設・運行規則（EBO § 1 Abs. 2） | Hauptbahnen (Regelspurige öffentliche Eisenbahnen) | 標準軌幹線鉄道（本線：軌間1,435mm、車軸重基準18〜25t、最高速度160km/h超の高速新線［SFS］・都市間幹線・S-Bahn本線を含む） | 全国ICE/IC/EC幹線、主要RE/RB路線、S-Bahn全路線（ベルリン、ハンブルク、ミュンヘン、フランクフルト、シュトゥットガルト、ケルン／ルール等） | 〇 |
| 一般鉄道（標準軌公共鉄道） | 一般鉄道法（AEG § 1, § 2, § 26）、鉄道建設・運行規則（EBO § 1 Abs. 2） | Nebenbahnen (Regelspurige öffentliche Eisenbahnen) | 標準軌支線鉄道（地方交通線・支線：軌間1,435mm、最高速度原則80〜100km/h、踏切・信号・軌道基準が緩和された地域路線） | 全国の地域RB支線、非連邦鉄道（NE-Bahnen）が運営する地方支線網 | 〇 |
| 一般鉄道（狭軌公共鉄道） | 一般鉄道法（AEG § 26）、狭軌鉄道建設・運行規則（ESBO § 1） | Schmalspurbahnen des öffentlichen Verkehrs | 公共狭軌鉄道（軌間750mm, 900mm, 1,000mm等の公共営業鉄道路線） | ハルツ狭軌鉄道（HSB: 1,000mm）、モリー鉄道（Bäderbahn Molli: 900mm）、ザクセン狭軌鉄道群（SDG: 750mm）、ヴァンゲローゲ島鉄道（DB: 1,000mm） | 〇 |
| 山岳・歯軌条鉄道 | 一般鉄道法（AEG § 1 Abs. 2 適用除外規定）、各州山岳鉄道法（Landesbergbahngesetze / BOZ） | Bergbahnen / Zahnradbahnen | 登山鉄道・アプト式／リッゲンバッハ式歯軌条鉄道（※シュトゥットガルト歯軌条鉄道ZackeのみBOStrab適用） | バイエルン・ツークシュピッツ鉄道（BZB）、ヴェンデルシュタイン鉄道、ドラッヘンフェルス鉄道 | 〇 |
| 都市軌道（完全独立軌道） | 旅客運送法（PBefG § 4 Abs. 2）、路面電車建設・運行規則（BOStrab § 1 Abs. 2 Nr. 2） | Unabhängige Bahnen: Hoch- und Untergrundbahnen (U-Bahn) | 地下鉄・高架都市高速鉄道（道路交通・他交通と完全立体交差する独立専用軌道。路面電車の車体幅・編成制限非適用） | ベルリン（BVG）、ハンブルク（HHA）、ミュンヘン（MVG）、ニュルンベルク（VAG）の4都市圏 | 〇 |
| 都市軌道（特殊構造独立軌道） | 旅客運送法（PBefG § 4 Abs. 2）、路面電車建設・運行規則（BOStrab § 1 Abs. 2 Nr. 2） | Unabhängige Bahnen: Schwebebahnen und ähnliche Bahnen besonderer Bauart | 懸垂式モノレール・特殊案内軌条式鉄道（完全独立軌道） | ヴッパータール空中鉄道（Schwebebahn）、ドルトムントH-Bahn、デュッセルドルフ空港SkyTrain | 〇 |
| 都市軌道（併用・専用複合軌道） | 旅客運送法（PBefG § 4 Abs. 1, 2）、BOStrab § 1 Abs. 2 Nr. 1（鉄道線直通区間はEBO併用） | Straßenabhängige Bahnen: Stadtbahn | ライトレール・シュタットバーン（都心地下区間と地上併用／専用軌道を直通する都市鉄道、およびEBO本線直通型トラムトレイン） | シュトゥットガルト、ケルン／ボン、ハノーファー、フランクフルト、デュッセルドルフ、ドルトムント、エッセン／ボーフム、ビーレフェルト、カールスルーエ（EBO直通）等 | 〇 |
| 都市軌道（路面電車） | 旅客運送法（PBefG § 4 Abs. 1）、路面電車建設・運行規則（BOStrab § 1 Abs. 2 Nr. 1） | Straßenabhängige Bahnen: Straßenbahn | 路面電車（併用軌道・新設軌道。車体幅上限2.65m、編成最大長75m） | ベルリン、ミュンヘン、ドレスデン、ライプツィヒ、ブレーメン、ニュルンベルク、ハレ、マクデブルク、マインツ、ヴュルツブルク等約50都市 | 〇 |
| 索道（公共索道・鋼索鉄道） | EU索道規則（Verordnung (EU) 2016/424）、各連邦州索道法（Landesseilbahngesetze） | Seilbahnen des öffentlichen Personenverkehrs (Kabinenbahnen, Pendelbahnen, Standseilbahnen) | 都市型ロープウェイ・交走式／循環式普通索道・鋼索鉄道（ケーブルカー / Standseilbahn） | ケルン・ロープウェイ、コブレンツ・ロープウェイ、ツークシュピッツェ索道、ドレスデン鋼索鉄道、ハイデルベルク鋼索鉄道、バーデン＝バーデン等 | 〇（通年公共交通・主要山岳連絡線） |
| 専用鉄道・特殊索道（対象外） | 各連邦州専用鉄道規則（BOA / EBOA）、各連邦州索道法（Schlepplifte） | Nichtöffentliche Eisenbahnen (Anschlussbahnen / Werkbahnen) / Schlepplifte und Sesselbahnen des Wintersports | 非公共産業専用線・工場側線・港湾構内線、および冬季スキー場用Tバーリフト・チェアリフト・季節遊覧リフト | 各地の工場・鉱山・港湾専用線、アルプス・中低山帯の冬季スキーリフト群 | × |

### 2.2 主要鉄道事業者・索道リスト（operators.csv 登録用）

| 事業者種別 | 事業者名（公用語 / 略称） | 法的地位・役割 | 主な管轄エリア・運行系統 | 公式サイトURL |
| --- | --- | --- | --- | --- |
| 国家インフラ管理会社（EIU） | DB InfraGO AG | 連邦鉄道インフラ管理会社（公益指向インフラ事業体：軌道網および約5,400の旅客駅を一元管理） | ドイツ全国の連邦鉄道網（約33,400 km）および連邦鉄道旅客駅 | https://www.dbinfrago.com/ |
| 連邦長距離旅客運行会社（EVU） | DB Fernverkehr AG | 連邦鉄道長距離旅客運行会社 | 全国のICE（Intercity-Express）、IC（Intercity）、EC（EuroCity）およびヴァンゲローゲ島連絡鉄道・船 | https://www.bahn.de/ |
| 連邦地域旅客運行会社（EVU） | DB Regio AG（S-Bahn Berlin GmbH, S-Bahn Hamburg GmbH, Regionalverkehre Start Deutschland GmbH等を含む） | 連邦鉄道地域・近郊旅客運行会社（SPNV最大手） | 全国各州のRE（Regional-Express）、RB（Regionalbahn）、主要大都市圏S-Bahn | https://www.dbregio.de/ |
| 非連邦鉄道（NE-Bahnen: EVU） | Transdev GmbH（Bayerische Regiobahn [BRB], NordWestBahn [NWB], Transdev Regio Ost, S-Bahn Hannover等） | 民間大手鉄道・バス運行グループ | バイエルン、ニーダーザクセン、ブレーメン、NRW、ザクセン等のRE/RBおよびハノーファーS-Bahn | https://www.transdev.de/ |
| 非連邦鉄道（NE-Bahnen: EVU） | Netinera Deutschland GmbH（metronom, erixx, enno, vlexx, Die Länderbahn [DLB]等） | 民間大手地域鉄道グループ（Trenitalia傘下） | ニーダーザクセン、ハンブルク、シュレースヴィヒ＝ホルシュタイン、ラインラント＝プファルツ、ザールラント、バイエルン、ザクセン等 | https://www.netinera.de/ |
| 非連邦鉄道（NE-Bahnen: EVU） | ODEG - Ostdeutsche Eisenbahn GmbH | 民間地域鉄道事業者（BeNEX・Netinera合弁） | ベルリン、ブランデンブルク、メクレンブルク＝フォアポンメルン、ザクセン＝アンハルト、ザクセンのRE/RB | https://www.odeg.de/ |
| 非連邦鉄道（NE-Bahnen: EVU） | cantus Verkehrsgesellschaft mbH | 地域鉄道事業者（HLB・BeNEX合弁） | ヘッセン州北東部、ニーダーザクセン州南部、テューリンゲン州西部のRB網 | https://www.cantus-bahn.de/ |
| 非連邦鉄道（NE-Bahnen: EVU） | National Express Rail GmbH / Arverio Deutschland GmbH | 民間地域鉄道事業者 | NRW州の主要幹線（RRX: Rhein-Ruhr-Express）、バーデン＝ヴュルテンベルク州・バイエルン州のRE/RB路線網 | https://www.nationalexpress.de/ / https://www.arverio.de/ |
| 非連邦鉄道（NE-Bahnen: EVU/EIU） | Hessische Landesbahn GmbH (HLB) / SWEG Südwestdeutsche Landesverkehrs-GmbH / Albtal-Verkehrs-Gesellschaft mbH (AVG) | 州・自治体出資の公営非連邦鉄道（インフラ保有EIU兼運行EVU） | ヘッセン州（HLB）、バーデン＝ヴュルテンベルク州（SWEG、およびカールスルーエ圏トラムトレイン網AVG） | https://www.hlb-online.de/ / https://www.sweg.de/ / https://www.avg.info/ |
| 都市交通局（BOStrab） | Berliner Verkehrsbetriebe (BVG) AöR / Münchner Verkehrsgesellschaft mbH (MVG) / Hamburger Hochbahn AG (HHA) | ベルリン・ミュンヘン・ハンブルクの公営都市交通公社 | ベルリン（U-Bahn・Straßenbahn・バス・渡船）、ミュンヘン（U-Bahn・Straßenbahn・バス）、ハンブルク（U-Bahn・バス） | https://www.bvg.de/ / https://www.mvg.de/ / https://www.hochbahn.de/ |
| 都市交通局（BOStrab） | Kölner Verkehrs-Betriebe AG (KVB) / Rheinbahn AG / Stuttgarter Straßenbahnen AG (SSB) / ÜSTRA / VGF | ケルン・デュッセルドルフ・シュトゥットガルト・ハノーファー・フランクフルトの都市交通会社 | 各大都市圏のStadtbahn（ライトレール）、Straßenbahn（路面電車）、および基幹バス網 | https://www.kvb.koeln/ / https://www.rheinbahn.de/ / https://www.ssb-ag.de/ |
| 索道・山岳鉄道事業者 | Bayerische Zugspitzbahn Bergbahn AG (BZB) / Kölner Seilbahn-Gesellschaft mbH / Seilbahn Koblenz GmbH / Dresdner Verkehrsbetriebe AG | 山岳鉄道・都市型索道・鋼索鉄道運営事業者 | ツークシュピッツ鉄道・索道群（Seilbahn Zugspitze等）、ケルン・ロープウェイ、コブレンツ・ロープウェイ、ドレスデン鋼索鉄道・懸垂鉄道 | https://zugspitze.de/ / https://www.koelner-seilbahn.de/ / https://www.seilbahn-koblenz.de/ |

- **国家インフラ管理会社（DB InfraGO AG）および主要旅客運行会社（DB Fernverkehr, DB Regio）の構造**: 一般鉄道法（AEG）に基づくドイツの鉄道制度は、インフラ管理企業（Eisenbahninfrastrukturunternehmen: EIU）と列車運行企業（Eisenbahnverkehrsunternehmen: EVU）の上下分離およびオープンアクセス競争を原則としている。連邦所有の軌道インフラ（HauptbahnenおよびNebenbahnenの決定権を持つ連邦鉄道網）と旅客駅施設は、公益指向の単一インフラ会社 **DB InfraGO AG** によって一元管理されており、その線路網上で長距離独立採算列車を運行する **DB Fernverkehr AG** と、各州の鉄道発注機関（Aufgabenträger）との公共サービス契約に基づき近距離鉄道（SPNV：S-Bahn, RE, RB）を運行する **DB Regio AG** が営業を行っている。S-Bahn（都市近郊高速鉄道）はベルリン・ハンブルク（直流第三軌条方式）を含めすべて法的にはAEG/EBO準拠の一般鉄道（Hauptbahnen、都市高速鉄道専用線では最小軸重20t基準が適用可能）であり、PBefG/BOStrab準拠のU-Bahnとは法体系・監督官庁（連邦鉄道庁EBA vs 各州技術監督庁TAB）が完全に異なる。
- **主要非連邦鉄道（NE-Bahnen / 私鉄事業者）の事業形態と監督区分**: 連邦鉄道網に属さない鉄道事業者（Nichtbundeseigene Eisenbahnen: NE-Bahnen）は、Transdev、Netinera、ODEG、cantus、National Express、ArverioのようにDB InfraGOの線路を使用して地域のRE/RBを運行するEVU専業事業者と、HLB、SWEG、AVGのように自社の鉄道インフラ（EIU）を保有しつつ列車運行（EVU）も行う事業者に大別される。AEG第5条に基づき、NE-Bahnenの鉄道監督権は各連邦州に属するが、大半の州は実務上の技術監督（Landeseisenbahnaufsicht）を連邦鉄道庁（EBA）へ委託している。
- **主要都市交通局（BVG, MVG, Hamburger Hochbahn, KVB, Rheinbahn等）と直通運転モデル**: 都市内のU-Bahn、Stadtbahn、Straßenbahnは旅客運送法（PBefG第4条）および路面電車建設・運行規則（BOStrab）に基づき各都市の公営交通局がインフラ管理と運行を一体的に担う。データモデリング上の重要点として、「U-Bahn」の呼称は完全独立軌道の4都市（ベルリン、ハンブルク、ミュンヘン、ニュルンベルク）だけでなく、フランクフルト、ケルン／ボン、シュトゥットガルト、デュッセルドルフ、ドルトムント、エッセン、ハノーファー等の地下区間を有するStadtbahn（法的にはBOStrab第1条第2項第1号の併用・道路依存型軌道と第2号の独立軌道のハイブリッド）でも駅標識（白抜き「U」マーク）および系統番号（`U1`〜`U99`）として使用される。さらにカールスルーエ・モデル（AVG）やハイルブロン、カッセル（RegioTram）、ケムニッツ・モデルでは、BOStrab軌道とEBO一般鉄道本線を直通運転（Zweisystem-Stadtbahn）するため、GISデータベース上では同一運行系統がEBO線区エッジとBOStrab軌道エッジの双方を跨ぐトポロジー設計が必要となる。
- **索道（公共交通索道・山岳索道）の公式リスト入手先**: 全国の普通索道（Seilbahn / Kabinenbahn）、鋼索鉄道（Standseilbahn）、歯軌条鉄道（Zahnradbahn）の公式事業者ディレクトリは、**ドイツ索道・リフト協会（Verband Deutscher Seilbahnen und Schlepplifte e.V. - VDS）** の索道検索データベース（`https://www.seilbahnen.de/seilbahnsuche/`：全133事業者・設備種別フィルタ付）および都市型索道特設ページ（`https://www.seilbahnen.de/urbane-seilbahnen/`）、ならびに連邦鉄道庁（EBA）の認可鉄道事業者リスト（`https://www.eba.bund.de/DE/Themen/Eisenbahnunternehmen/Unternehmenslisten/unternehmenslisten_node.html`）から調達可能である。

### 2.3 鉄軌道のWikidata抽出条件

| 抽出対象エンティティ | Wikidataクラス指定（wdt:P31/wdt:P279*） | 必須国フィルタ | 主要取得プロパティ（ドイツ固有ID・空間属性） |
| --- | --- | --- | --- |
| 一般鉄道路線（物理線区） | wd:Q728937 (railway line / Bahnstrecke) | ?item wdt:P17 wd:Q183 | P1671 (VzG線区番号4桁), P137 (管理者: DB InfraGO wd:Q124046168 等), P559 (起終点) |
| 鉄道・S-Bahn運行系統 | wd:Q15141321 (railway service), wd:Q96351215 (S-Bahn line) | ?item wdt:P17 wd:Q183 | P137 (運行事業者EVU), P559 (起終点駅), P527 (構成駅) |
| 地下鉄・都市軌道・路面電車路線 | wd:Q13406463 (rapid transit line), wd:Q2175765 (tram line), wd:Q1262022 (Stadtbahn) | ?item wdt:P17 wd:Q183 | P137 (都市交通局), P361 (所属ネットワーク), P625 (座標) |
| 鋼索鉄道・普通索道 | wd:Q1424289 (funicular), wd:Q335318 (aerial tramway / gondola lift) | ?item wdt:P17 wd:Q183 | P137 (運営会社), P625 (座標) |
| 鉄道駅・鉄道停留所（EBO/ESBO） | wd:Q55488 (railway station / Bahnhof), wd:Q55678 (railway stop / Haltepunkt) | ?item wdt:P17 wd:Q183 | P8671 (DB駅番号), P296 (DS 100略号), P954 (IBNR 7桁), P722 (UIC駅コード 7桁), P625 (座標), P197 (隣接駅) |
| 地下鉄駅・電停・索道駅 | wd:Q928830 (metro station), wd:Q2175765 (tram stop), wd:Q1339195 (cable car station) | ?item wdt:P17 wd:Q183 | P954 (IBNR), P296 (駅略号), P197 (隣接駅), P625 (座標) |

- **鉄軌道路線および駅・停留場の抽出クエリ条件**: ドイツ国内（`wdt:P17 wd:Q183`）の鉄軌道データをWikidata SPARQLから抽出する際は、物理インフラとしての鉄道路線（`wd:Q728937`）と旅客案内上の運行系統（S-Bahn系統 `wd:Q96351215`、地下鉄路線 `wd:Q13406463`、路面電車系統 `wd:Q2175765`）を明確に分離してクエリを発行する。同様に拠点ノードについても、EBO第4条第2項に基づき分岐器（Weiche）を有する停車場である `Bahnhof`（`wd:Q55488`）と、分岐器を持たない本線上の乗降場である `Haltepunkt`（`wd:Q55678`）の双方を抽出対象に含めることが不可欠である。
- **現役施設限定フィルタ（廃止P576除外等）および主要プロパティの活用仕様**: 廃止済み路線や廃駅・休止施設を完全に排除するため、SPARQLのWHERE句に `FILTER NOT EXISTS { ?item wdt:P576 ?dissolved . }`（廃止・解体日）、`FILTER NOT EXISTS { ?item wdt:P582 ?endTime . }`（終了日）、`FILTER NOT EXISTS { ?item wdt:P3999 ?closureDate . }`（公式閉鎖日）を必須条件として付与し、さらにクラスおよび供用状態（`P5816`）に対して `FILTER NOT EXISTS { ?item wdt:P31/wdt:P279* wd:Q65464941 . }`（廃止駅除外）、`FILTER NOT EXISTS { ?item wdt:P31/wdt:P279* wd:Q15630906 . }`（廃止鉄道路線除外）、`FILTER NOT EXISTS { ?item wdt:P5816 wd:Q11639308 . }`（廃止状態除外）、`FILTER NOT EXISTS { ?item wdt:P5816 wd:Q109551035 . }`（営業休止状態除外）を適用する。取得すべき主要外部IDプロパティとして、路線には4桁のドイツ線区番号 `P1671`（VzG-Streckennummer）、駅にはDB旅客駅番号 `P8671`（Bahnhofsnummer）、運転管理用のDS 100 / Ril 100電報略号 `P296`、HAFAS時刻表系と直結する7桁のIBNR `P954`、およびUIC国コード `80` で始まる7桁のUIC駅ロケーションコード `P722`（チェックディジットを除いた7桁整数値）を同時取得することで、DB InfraGOおよびDELFIオープンデータとの決定論的な突合が可能となる。

## 3. バス事業制度の詳細分類

### 3.1 自動車運送事業法に基づく法的区分一覧

| 法的分類 | 運行態様・種別（公用語/日本語） | 概要・対象範囲 | プロジェクトでの位置づけ(初期収集/探索時/対象外) |
| --- | --- | --- | --- |
| 旅客運送法（PBefG § 42 i.V.m. § 8 PBefG） | Linienverkehr im ÖPNV (Stadtbus, Regionalbus, Schnellbus / Expressbus / PlusBus, MetroBus, Nachtbus) / 一般近距離定期路線バス（市内バス・地域都市間バス・急行バス） | 定められた起点・終点・停留所間を定期のダイヤおよび共通運賃で結ぶ乗合バス運送のうち、原則として乗車距離50km以下または所要時間1時間以内の近距離公共交通（ÖPNV）。各地域の運輸連合（Verkehrsverbund）の運賃・系統番号体系に統合されている。 | 初期収集（都市間急行バス［Schnellbus/PlusBus/X-Bus］・主要都市基幹バス）／探索時（一般生活支線バス） |
| 旅客運送法（PBefG § 42a） | Linienfernverkehr mit Kraftfahrzeugen (Fernbuslinienverkehr) / 都市間長距離定期高速バス | 乗車距離が原則50kmを超える、または並行する近距離鉄道（SPNV）で所要時間1時間以上の都市間を結ぶ商業ベースの定期長距離バス（FlixBusおよび国際長距離路線等）。独立採算（Eigenwirtschaftlicher Verkehr）で運行される。 | 初期収集 |
| 旅客運送法（PBefG § 44） | Linienbedarfsverkehr (On-Demand-Verkehr im ÖPNV, Rufbus, Anruf-Sammel-Taxi [AST]) / 公的区域オンデマンド乗合交通 | 定期路線バスを補完する公的近距離公共交通（ÖPNV）として、事前予約・アプリ配車により固定停留所または仮想停留所（Virtuelle Haltestellen）間を運行する公的デマンド交通。運輸連合の共通運賃（または加算運賃）が適用される。 | 探索時 |
| 旅客運送法（PBefG § 43） | Sonderformen des Linienverkehrs (Berufsverkehr, Schülerfahrten, Marktfahrten, Theaterfahrten) / 特定定期路線バス（通勤・通学専用バス） | 特定の利用者層（工場従業員、児童・生徒等）のみを対象とし、一般公衆の乗車を排除して運行される閉鎖型特定バス（※一般旅客が乗車可能な通学時間帯の増発便は§ 42の一般定期路線バスに分類される）。 | 対象外（一般混乗路線を除く） |
| 旅客運送法（PBefG §§ 46–51） | Gelegenheitsverkehr (Ausflugsfahrten § 48, Ferienziel-Reisen § 48, Verkehr mit Taxen § 47, Mietomnibusse / Mietwagen § 49, Gebündelter Bedarfsverkehr § 50) / 不定期運送事業（貸切観光バス・タクシー・ハイヤー・民間相乗り配車） | 定期の路線・時刻表を持たない貸切バス、観光周遊バス、タクシー、ハイヤー、および公的ÖPNV枠外の商業ライドプーリング事業。 | 対象外 |

### 3.2 運輸連合・主要バス事業者（operators.csv 登録用）

| 区分 | 組織・事業者名（公用語 / 略称） | 管轄地域・事業概要 | 公式サイトURL |
| --- | --- | --- | --- |
| 主要運輸連合 | Verkehrsverbund Rhein-Ruhr AöR (VRR) | ノルトライン＝ヴェストファーレン州ライン・ルール大都市圏（デュッセルドルフ、ドルトムント、エッセン、デュースブルク、ヴッパータール等） | https://www.vrr.de/ |
| 主要運輸連合 | Rhein-Main-Verkehrsverbund GmbH (RMV) | ヘッセン州中南部およびライン＝マイン大都市圏（フランクフルト、ヴィースバーデン、マインツ、ダルムシュタット等） | https://www.rmv.de/ |
| 主要運輸連合 | Hamburger Verkehrsverbund GmbH (HVV) | ハンブルク都市州および隣接するシュレースヴィヒ＝ホルシュタイン州・ニーダーザクセン州の3州広域都市圏 | https://www.hvv.de/ |
| 主要運輸連合 | Verkehrsverbund Berlin-Brandenburg GmbH (VBB) | ベルリン州およびブランデンブルク州全域（首都圏広域統合ネットワーク） | https://www.vbb.de/ |
| 主要運輸連合 | Münchner Verkehrs- und Tarifverbund GmbH (MVV) | ミュンヘン市およびオーバーバイエルン周辺郡の広域都市圏 | https://www.mvv-muenchen.de/ |
| 主要運輸連合 | Verkehrs- und Tarifverbund Stuttgart GmbH (VVS) | シュトゥットガルト市および周辺4郡の都市圏 | https://www.vvs.de/ |
| 主要運輸連合 | Verkehrsverbund Rhein-Neckar (VRN) / Verkehrsverbund Rhein-Sieg (VRS) / Verkehrsverbund Großraum Nürnberg (VGN) / Mitteldeutscher Verkehrsverbund (MDV) | ライン＝ネッカー圏（マンハイム・ハイデルベルク）、ケルン／ボン圏（VRS）、ニュルンベルク広域圏（VGN）、ライプツィヒ／ハレ圏（MDV） | https://www.vrn.de/ / https://www.vrs.de/ / https://www.vgn.de/ / https://www.mdv.de/ |
| 長距離高速バス | Flix SE (FlixBus DACH GmbH) / BlaBlaCar Bus / Sindbad / Bayern Express & P. Kühn Berlin GmbH (BEX) | ドイツ国内の都市間長距離バス（Fernbus § 42a PBefG）市場の95%以上を占める最大手FlixBusおよび都市間・国際長距離バス事業者群 | https://www.flixbus.de/ / https://www.blablacar.de/bus / https://www.bex.de/ |
| 地域バス公社群 | DB Regio Bus（傘下地域会社：Autokraft GmbH, Regionalverkehr Oberbayern [RVO], DB Regio Bus NRW, DB Regio Bus Mitte, DB Regio Bus Ost, Südbadenbus [SBG], Weser-Ems-Bus等） | ドイツ最大の地域路線バスグループ（DB Regio AG傘下の全国約30社の地域バス事業会社群） | https://www.dbregiobus.de/ |
| 民間・自治体広域バス | Transdev Verkehr GmbH / Netinera (OHE等) / 各都市シュタットヴェルケ（Stadtwerke）バス部門 | 各州・郡の公的入札（Verkehrsvertrag）を受託してRegionalbus / Schnellbus / PlusBusを運行する民間事業者および自治体公社 | https://www.transdev.de/ / https://www.netinera.de/ |

- **地域ごとの運輸連合（Verkehrsverbund：VRR, RMV, HVV, VBB, MVV, VVS等）の公的枠組みと役割**: ドイツの近距離公共交通（ÖPNV）は、各州の近距離交通法（ÖPNV-Gesetze der Länder）に基づき、州・郡・郡独立市が構成する公的計画・発注主体（Aufgabenträger）と運行事業者（Verkehrsunternehmen）が統合された地域運輸連合（Verkehrsverbund）によって一元管理されている。データベース設計上、個々の路線バスは民間の中小受託事業者（Subunternehmer）が実運行する場合であっても、利用者向けの系統番号（Liniennummer：都市内幹線のMetroBus `M1`〜、広域急行のExpressbus `X1`〜 / `PlusBus`、一般系統の3桁番号等）、停留所ID（DHID）、および時刻表データ（DELFI GTFS/NeTEx）はすべて各運輸連合または州データプール単位で集約・正規化されてMobilithekへ供給される。そのため、`operators.csv` のスキーマ設計では「統括運輸連合（Network / Tariff Authority）」と「実運行事業者（Operating Carrier）」の2階層リレーションを保持することが不可欠である。
- **主要都市間長距離バス事業者（FlixBus等）および主要地域バス公社（DB Regio Bus等）の構造**: 旅客運送法第42a条に基づく都市間長距離高速バス（Fernbus）は運輸連合の枠外の独立採算事業として運行され、**Flix SE（FlixBus）** が路線企画・予約プラットフォーム・GTFS配信を一元管理し、全国の提携バス会社が車両運行を担う構造となっている。一方、地域路線バス（Regionalbus / Schnellbus）においては、ドイツ鉄道傘下の **DB Regio Bus** が全国約30社の地域別バス子会社（シュレースヴィヒ＝ホルシュタイン州のAutokraft、バイエルン州南部のRVO、バーデン＝ヴュルテンベルク州のSüdbadenbus、NRW州のDB Regio Bus NRW等）を通じて最大のネットワークを形成しており、都市内バスは各自治体の公営公益企業（Stadtwerke）または都市交通局（BVG, HHA, MVG, SSB等）が直営している。

## 4. 航路（旅客船・フェリー）制度の詳細分類

### 4.1 海上運送法・内陸水運法に基づく航路種別一覧

| 大分類 | 法的種別（公用語/日本語） | 根拠法律 | 概要・対象航路例 | プロジェクトでの位置づけ(初期収集/探索時/対象外) |
| --- | --- | --- | --- | --- |
| 海上・沿岸離島連絡航路（Seeschifffahrt） | See- und Küstenlinienverkehr / Inselfährverkehr (北海・バルト海離島連絡定期航路・カーフェリー) | 海洋航運任務法（SeeAufgG）、海上航路交通規則（SeeSchStrO）、連邦水路法（WaStrG § 1 Seewasserstraßen） | 北海（東フリジア諸島7島、北フリジア諸島［ズュルト島・フェール島・アムルム島・ペルヴォルム島・ハリゲン諸島］、外洋離島ヘルゴラント島）およびバルト海（ヒッデンゼー島、リューゲン島、フェーマルン島〜デンマーク等）と本土港湾を結ぶ定期旅客船・RO-ROフェリー・高速双胴船。 | 初期収集 |
| 都市内公共交通渡船（ÖPNV-Fährverkehr） | Öffentlicher Fährverkehr im ÖPNV / Hafen- und Flussfähren (都市内定期渡船・運輸連合統合フェリー) | 内陸水運任務法（BinSchAufgG）、連邦水路法（WaStrG）、旅客運送法（PBefG § 8 ÖPNV統合枠）、各州水路・渡船法 | 大都市の運輸連合（Verkehrsverbund）の共通運賃・系統番号に完全統合された日常通勤渡船。ハンブルク港・エルベ川のHADAG渡船（HVV 61〜75号線）、ベルリン市内のBVG渡船（VBB F10〜F24号線）、ロストック（Warnowfähre）、キール（SFK）、ドレスデン（エルベ渡船）等。 | 初期収集 |
| 内陸大河川・湖沼定期航路（Binnenschifffahrt） | Linien- und Fährverkehr auf Binnengewässern / Wagenfähren (内陸河川・湖沼定期航路・道路連絡カーフェリー) | 内陸水運任務法（BinSchAufgG）、ライン川航行規則（RheinSchPV）、ボーデン湖航行規則（BSO）、各水路航行規則 | ①ボーデン湖の通年定期船・高速船・カーフェリー（コンスタンツ〜メーアスブルク間、フリードリヒスハーフェン〜コンスタンツ間等）、②ライン川・エルベ川・ヴェーザー川・モーゼル川等の連邦道路・州道接続カーフェリー（Wagenfähren：ビンゲン〜リューデスハイム、グリュックシュタット〜ヴィシュハーフェン等）、③ライン川・バイエルン湖沼群の定期旅客航路。 | 初期収集（通年定期航路・道路連絡カーフェリー）／探索時（季節定期航路） |
| 観光遊覧・クルーズ航路（対象外） | Rundfahrten, Ausflugsschifffahrt und Flusskreuzfahrten (港湾周遊船・河川クルーズ船・チャーター船) | 内陸水運任務法（BinSchAufgG）、海洋航運任務法（SeeAufgG）、営業法（GewO） | 同一発着点に戻る港湾遊覧船（Hafenrundfahrten）、宿泊を伴う河川・海洋クルーズ船、不定期貸切船。 | 対象外 |

### 4.2 主要旅客航路・フェリー事業者（operators.csv 登録用）

| 事業者名（公用語 / 略称） | 運航海域・水系 | 主な運航航路・接続拠点 | 公式サイトURL |
| --- | --- | --- | --- |
| Aktien-Gesellschaft „EMS“ (AG Ems) | 北海（東フリジア諸島） | エムデン／エムスハーフェン 〜 ボルクム島（Borkum）定期フェリー・高速カタマラン | https://www.ag-ems.de/ |
| Reederei Norden-Frisia AG | 北海（東フリジア諸島） | ノルドダイヒ（Norddeich Mole）〜 ノルデナイ島（Norderney）・ユイスト島（Juist）定期フェリー・高速船 | https://www.reederei-frisia.de/ |
| Baltrum-Linie GmbH / Schiffahrt der Inselgemeinde Langeoog / Reederei Warrings / DB Fernverkehr AG (Wangerooge) | 北海（東フリジア諸島） | ネスマールジール〜バルトルム島、ベンスジール〜ランゲオーク島、ノイハーリンガージール〜シュピーカーオーク島、ハルデジール〜ヴァンゲローゲ島（DB直営航路＋島内鉄道一貫運行） | https://www.baltrum-linie.de/ / https://www.langeoog.de/ / https://www.spiekeroog.de/ / https://www.siw-wangerooge.de/ |
| Wyker Dampfschiffs-Reederei Föhr-Amrum GmbH (W.D.R.) | 北海（北フリジア諸島） | ダゲビュル（Dagebüll Mole）〜 ヴィーク（フェール島 Föhr）〜 ヴィットデュン（アムルム島 Amrum）、およびシュリュッツジール〜ハリゲン諸島 | https://www.faehre.de/ |
| FRS GmbH & Co. KG (FRS Helgoline / FRS Syltfähre / FRS Elbfähre / Weiße Flotte GmbH) | 北海・エルベ川・バルト海 | ハンブルク／クックスハーフェン〜ヘルゴラント島（高速双胴船Halunder Jet）、リスト（ズュルト島）〜ハヴネビ、グリュックシュタット〜ヴィシュハーフェン（エルベ川横断）、シュトラールズント〜ヒッデンゼー島・リューゲン島 | https://www.frs.world/ / https://www.helgoline.de/ / https://www.weisse-flotte.de/ |
| Reederei Cassen Eils GmbH | 北海（ヘルゴラント島・ノイヴェルク島） | クックスハーフェン／ブレーマーハーフェン／ビュスム 〜 ヘルゴラント島（通年定期船MS Helgoland等）、クックスハーフェン〜ノイヴェルク島 | https://www.cassen-eils.de/ |
| HADAG Seetouristik und Fährdienst AG | エルベ川（ハンブルク港内） | ハンブルク都市交通（HVV）統合の定期渡船網（61, 62, 64, 68, 72, 73, 75号線等：ザンクト・パウリ桟橋 Landungsbrücken 〜 フィンケンヴェルダー等） | https://hadag.de/ |
| Stern und Kreisschiffahrt GmbH（BVG受託運航） | シュプレー川・ハーフェル川・ベルリン湖沼群 | ベルリン都市交通（BVG / VBB）統合の定期渡船6路線（F10: Wannsee〜Alt-Kladow、F11, F12, F21, F23, F24） | https://www.bvg.de/ / https://www.sternundkreis.de/ |
| Bodensee-Schiffsbetriebe GmbH (BSB) / Stadtwerke Konstanz GmbH / Katamaran-Reederei Bodensee GmbH | ボーデン湖（Bodensee） | コンスタンツ〜メーアスブルク間24時間通年カーフェリー、フリードリヒスハーフェン〜コンスタンツ間通年高速カタマラン、リンダウ・ユーバーリンゲン等のボーデン湖定期航路網 | https://www.bsb.de/ / https://www.stadtwerke-konstanz.de/faehre/ / https://www.der-katamaran.de/ |
| Köln-Düsseldorfer Deutsche Rheinschiffahrt GmbH (KD) / Bingen-Rüdesheimer Fähr- und Schiffahrtsgesellschaft | ライン川・モーゼル川 | ケルン〜コブレンツ〜マインツ間のライン川中流定期航路、およびビンゲン〜リューデスハイム間等のライン川横断通年カーフェリー・旅客渡船 | https://www.k-d.com/ / https://www.bingen-ruedesheimer.de/ |
| Bayerische Seenschifffahrt GmbH / Chiemsee-Schifffahrt Ludwig Feßler KG | バイエルン州湖沼群 | シュタルンベルク湖、アンマー湖、ケーニヒス湖、テーゲルン湖（州公社）、およびキーム湖（プリーン〜ヘレンインゼル島〜フラウエンインゼル島通年連絡船） | https://www.seenschifffahrt.de/ / https://www.chiemsee-schifffahrt.de/ |

- **主要フェリー事業者の運航特性と公共交通データ統合**: 北海の東フリジア諸島・北フリジア諸島・ヘルゴラント島およびバルト海のヒッデンゼー島等を結ぶ離島航路（Reederei Norden-Frisia, AG Ems, W.D.R., FRS Helgoline, Cassen Eils等）、ボーデン湖定期航路（BSB, Stadtwerke Konstanz等）、ならびにハンブルク（HADAG）・ベルリン（BVG）・キール（SFK）・ロストック（RSAG/Weiße Flotte）の都市内渡船は、すべてDELFIの全国標準時刻表データセット（GTFS `route_type=4` / NeTEx `water`）に収録されており、鉄道駅（Norddeich Mole駅、Dagebüll Mole駅等）とフェリー桟橋が同一複合ノードまたは隣接DHIDノードとしてシームレスに結節されている。
- **連邦水路・航運局（WSV）等の公的航路・水路台帳入手先URL**: 連邦水路法（WaStrG）に基づく全国の海上水路（Seewasserstraßen）および内陸水路（Binnenwasserstraßen：クラスI〜VIおよび非分類水路）の公式空間データは、**連邦水路・航運局（WSV）および水路・航運総局（GDWS）** の地理データサービスポータル（`https://www.gdws.wsv.bund.de/DE/service/karten/02_Geodatendienste_Geoanwendungen/01_Geodatendienste/Geodatendienste_node.html`）から無償取得できる。特に基幹データセットである「連邦水路交通網（Verkehrsnetz der Bundeswasserstraßen: VerkNet-BWaStr）」および「連邦水路ロケータREST API（Bundeswasserstraßen-Locator REST-Schnittstelle）」は、全水路の路線ジオメトリ・流向・水路キロ程（BWaStr-km）をJSON/GeoJSONおよびINSPIRE準拠WMS/WFS形式で提供しており、水路インフラデータ「WInD（Wasserstraßen Infrastruktur Daten）」（WMS）、デジタル連邦水路図・路線番号台帳「DBWK1000 / Bundeswasserstraßen mit Nummern und Abkürzungen (w161t)」（`https://www.gdws.wsv.bund.de/DE/service/karten/01_karten/karten-node.html`）、および電子水路情報システム「ELWIS（Inland ENC）」（`https://www.elwis.de/`）と組み合わせることで、全河川・運河・沿岸航路および渡船場の正確な線形参照台帳を構築できる。

## 5. 航空路（国内定期航空路）制度の詳細分類

### 5.1 航空法に基づく運航種別一覧

| 大分類 | 法的種別（公用語/日本語） | 根拠法律 | 概要・対象範囲 | プロジェクトでの位置づけ(初期収集/探索時/対象外) |
| --- | --- | --- | --- | --- |
| 国内幹線定期航空運送 | Genehmigter Fluglinienverkehr zwischen Verkehrsflughäfen (§ 20, § 21 LuftVG i.V.m. VO (EG) Nr. 1008/2008) / 主要民間空港間商業国内定期便 | 連邦航空法（LuftVG §§ 20–21a）、航空許可規則（LuftVZO）、EU規則1008/2008 | 連邦航空局（LBA）認可の航空運送事業者が、公表された時刻表に基づき主要民間交通空港（Verkehrsflughäfen：FRA, MUC, BER, HAM, DUS, STR等）間で定期運航する国内旅客便。 | 初期収集 |
| 離島・地域定期航空運送 | Insel- und Regionalfluglinienverkehr (§ 21 LuftVG) / 北海離島連絡定期便・リージョナル定期便 | 連邦航空法（LuftVG § 21）、各州航空監督庁認可規定 | 本土の交通飛行場（Verkehrslandeplätze：ノルデン＝ノルドダイヒ、エムデン、ハルレ、ハイデ／ビュスム等）と東フリジア諸島・ヘルゴラント島等の離島飛行場を結ぶ小型固定翼機による通年定期旅客便。 | 初期収集 |
| 不定期航空運送・一般航空（対象外） | Gelegenheitsverkehr (Charterverkehr, Taxiflug, Rundflüge nach § 20, § 22 LuftVG) / Allgemeine Luftfahrt | 連邦航空法（LuftVG §§ 20, 22） | 季節観光チャーター便、ビジネスジェット、エアタクシー、遊覧飛行、救急ヘリコプター、自家用航空機・グライダー等。 | 対象外 |

### 5.2 主要航空運送事業者（operators.csv 登録用）

| 事業者名（公用語） | IATA / ICAOコード | 運航形態・主な国内就航路線 | 公式サイトURL |
| --- | --- | --- | --- |
| Deutsche Lufthansa AG | LH / DLH | フランクフルト（FRA）およびミュンヘン（MUC）の2大ハブ空港とベルリン（BER）、ハンブルク（HAM）、デュッセルドルフ（DUS）、シュトゥットガルト（STR）、ハノーファー（HAJ）、ブレーメン（BRE）、ニュルンベルク（NUE）、ドレスデン（DRS）、ライプツィヒ（LEJ）、ミュンスター（FMO）等を結ぶ国内幹線 | https://www.lufthansa.com/ |
| Lufthansa City Airlines GmbH / Lufthansa CityLine GmbH | VL (LHX) / CL (CLH) | ルフトハンザ・グループの国内・欧州リージョナル定期便運航会社（FRA・MUC発着の国内各都市路線をLH便名・自社便名で運航） | https://www.lufthansa-city.com/ / https://www.lufthansacityline.com/ |
| Eurowings GmbH | EW / EWG | デュッセルドルフ（DUS）、ハンブルク（HAM）、シュトゥットガルト（STR）、ベルリン（BER）、ケルン／ボン（CGN）等を結ぶ非ハブ間（Point-to-Point）国内定期便（DUS〜BER, STR〜HAM, STR〜BER, CGN〜BER, HAM〜MUC等） | https://www.eurowings.com/ |
| FLN FRISIA-Luftverkehr GmbH Norddeich | - / FLN | 東フリジア諸島・離島連絡定期便（ノルドダイヒ〜ユイスト島・ノルデナイ島、ハルレ〜ヴァンゲローゲ島間の通年定期便） | https://www.inselflieger.de/ |
| OFD Ostfriesischer-Flug-Dienst GmbH | - / OFD | 北海離島連絡定期便（エムデン〜ボルクム島、クックスハーフェン／ノルトホルツ・ハイデ／ビュスム〜ヘルゴラント島間の通年定期便） | https://www.fliegofd.de/ |
| AIS Airlines B.V. / Rhein-Neckar Air GmbH (MHS Aviation) | IS (PNX) / M2 (MHV) | 地方都市間コミューター定期便（ミュンスター／オスナブリュック FMO 〜 シュトゥットガルト STR、マンハイム MHG 〜 ズュルト島 GWT・ウーゼドム島 HDF 等） | https://www.aisairlines.com/ / https://www.flyrna.com/ |

| 空港名（公用語 / 日本語） | 所在地（連邦州） | IATA | ICAO | 法的区分（LuftVG / LuftVZO） | 国内定期便の有無 |
| --- | --- | --- | --- | --- | --- |
| Flughafen Frankfurt Main（フランクフルト空港） | ヘッセン州 (HE) | FRA | EDDF | 国際交通空港（Verkehrsflughafen） | 〇（最大ハブ） |
| Flughafen München „Franz Josef Strauß“（ミュンヘン空港） | バイエルン州 (BY) | MUC | EDDM | 国際交通空港（Verkehrsflughafen） | 〇（第2ハブ） |
| Flughafen Berlin Brandenburg „Willy Brandt“（ベルリン・ブランデンブルク空港） | ブランデンブルク州 (BB) | BER | EDDB | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Düsseldorf（デュッセルドルフ空港） | ノルトライン＝ヴェストファーレン州 (NW) | DUS | EDDL | 国際交通空港（Verkehrsflughafen） | 〇 |
| Hamburg Airport „Helmut Schmidt“（ハンブルク空港） | ハンブルク都市州 (HH) | HAM | EDDH | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Stuttgart（シュトゥットガルト空港） | バーデン＝ヴュルテンベルク州 (BW) | STR | EDDS | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Köln/Bonn „Konrad Adenauer“（ケルン・ボン空港） | ノルトライン＝ヴェストファーレン州 (NW) | CGN | EDDK | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Hannover-Langenhagen（ハノーファー空港） | ニーダーザクセン州 (NI) | HAJ | EDDV | 国際交通空港（Verkehrsflughafen） | 〇 |
| Airport Nürnberg „Albrecht Dürer“（ニュルンベルク空港） | バイエルン州 (BY) | NUE | EDDN | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Bremen „Hans Koschnick“（ブレーメン空港） | ブレーメン都市州 (HB) | BRE | EDDW | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Leipzig/Halle（ライプツィヒ・ハレ空港） | ザクセン州 / ザクセン＝アンハルト州 (SN/ST) | LEJ | EDDP | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Dresden（ドレスデン空港） | ザクセン州 (SN) | DRS | EDDC | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Münster/Osnabrück（ミュンスター・オスナブリュック空港） | ノルトライン＝ヴェストファーレン州 (NW) | FMO | EDDG | 国際交通空港（Verkehrsflughafen） | 〇 |
| Flughafen Sylt / Flugplatz Mannheim City / Flughafen Heringsdorf | SH / BW / MV | GWT / MHG / HDF | EDXW / EDFM / EDAH | 地域空港・交通飛行場（Verkehrslandeplatz） | 〇（季節・地域定期便） |
| 北海離島連絡飛行場群（Norddeich, Emden, Harle, Juist, Norderney, Borkum, Wangerooge, Baltrum, Langeoog, Helgoland-Düne） | ニーダーザクセン州 (NI) / シュレースヴィヒ＝ホルシュタイン州 (SH) | NOD, EME, JUI, NRD, BMK, AGE, BMR, LGO, HGL | EDWS, EDWE, EDXP, EDWY, EDWR, EDWG, EDWZ, EDWL, EDXH | 交通飛行場（Verkehrslandeplätze） | 〇（通年離島定期便） |

- **主要航空運送事業者の運航構造と鉄道連携（Intermodalität）**: ドイツ国内の定期航空網は、フランクフルト（FRA）およびミュンヘン（MUC）へのハブ・アンド・スポーク接続を担う **Deutsche Lufthansa AG**（および傘下のLufthansa City Airlines / Lufthansa CityLine）と、デュッセルドルフ・ハンブルク・シュトゥットガルト・ベルリン等の主要都市間直行便を担う **Eurowings GmbH**、ならびに北海の離島生活路線を運航する **FLN** および **OFD** によって構成されている。なお、短距離国内区間ではルフトハンザ便名（LH）が付与されたDBのICE列車（Lufthansa Express Rail / AIRail：フランクフルト空港長距離駅 `FRA` / DS 100 `FFLF` 発着）が航空予約システム（GDS）上に混在するため、航空路データベース構築時には純粋な航空機運航便と鉄道コードシェア便を機材コードで選別する必要がある。
- **連邦航空局（LBA）公認民間空港一覧および国内定期路線の入手先URL**: 航空法（LuftVG）および航空許可規則（LuftVZO）では民間飛行場を「空港（Flughäfen：広域安全区域を有するVerkehrsflughäfenおよびSonderflughäfen）」と「飛行場（Landeplätze：VerkehrslandeplätzeおよびSonderlandeplätze）」に法的に区分しており、許認可および監督は連邦航空局（LBA）と各連邦州の航空監督庁（Landesluftfahrtbehörden）が分担している。公式の認可航空運送事業者および空港一覧は **連邦航空局（LBA）** ポータル（`https://www.lba.de/DE/Luftfahrtunternehmen/Genehmigungen/Genehmigungen_node.html`）、全飛行場の公式座標・滑走路・ICAOコード原典は **ドイツ航空保安公社（DFS）** の航空路誌「AIP Germany - BasicAIP」（`https://aip.dfs.de/basicAIP/`）、国内定期路線のペア別運航統計は **ドイツ空港協会（ADV）** の統計ライブラリ（`https://www.adv.aero/service/downloadbibliothek/`）から取得できる。

## 6. 交通拠点（ノード）の詳細種別と公式コード

| モード | コード・分類名称 | 管轄・標準規格 | フォーマット・桁数 | 用途・構造的特徴・具体例 |
| --- | --- | --- | --- | --- |
| 鉄軌道 | DS 100 / Ril 100（電報略号 / Betriebsstellenverzeichnis） | DB InfraGO AG（Richtlinie 100） | 英大文字2〜5文字（一部空白・数字含む） | 全鉄道施設（駅・信号場・分岐点・車庫）の運転管理用識別子。先頭1文字が旧鉄道管理局に由来する15の地域ゾーン（A ハンブルク、B ベルリン、D ドレスデン、E エッセン、F フランクフルト、H ハノーファー、K ケルン、L ライプツィヒ、M ミュンヘン、N ニュルンベルク、R カールスルーエ、S ザールブリュッケン、T シュトゥットガルト、U エアフルト、W シュヴェリーン）を表す（例：ベルリン中央駅地上 BLS・地下 BL、ミュンヘン中央駅 MH、フランクフルト中央駅 FF）。 |
| 鉄軌道 | DB駅番号（Bahnhofsnummer / StaDa-ID） | DB InfraGO AG（旅客駅部門） | 1〜4桁の整数（1〜9999） | DB InfraGOが管理する約5,400の旅客駅（Personenbahnhöfe）の施設台帳（StaDa API）主キー。Wikidataプロパティ P8671（例：ベルリン中央駅 1071、ミュンヘン中央駅 4234、フランクフルト中央駅 1866）。 |
| 鉄軌道・バス | EVA番号 / IBNR（Internationale Bahnhofsnummer） | DB / UIC / HAFAS時刻表系 | 7桁整数（ドイツの鉄道駅は 80 始まり） | 旅客案内・時刻表検索エンジン（HAFAS）における全鉄道駅・都市軌道駅・主要バス停の一意識別子。Wikidataプロパティ P954（例：ベルリン中央駅 8011160、ミュンヘン中央駅 8000261、フランクフルト中央駅 8000105）。 |
| 鉄軌道 | UIC駅コード（UIC Station Code） | 国際鉄道連合（UIC） | 7桁整数（またはLuhnチェックディジット1桁付8桁） | 欧州国際鉄道ネットワークにおける駅ロケーション識別子。ドイツ国内の鉄道駅では通常7桁IBNRと同一値となる。Wikidataプロパティ P722。 |
| 全公共交通（統合標準） | DHID（Deutschlandweite Haltestellen-ID / IFOPT） | DELFI e.V. / VDV 432 / CEN IFOPT | de:<AGS>:<LocalID>:<Area>:<Quay> | ドイツ全国の鉄道駅・地下鉄駅・電停・バス停・フェリー桟橋を網羅する国家標準グローバルID（Mobilithek GTFSの stop_id 採用規格）。第2階層の数値は連邦統計局の自治体コード（AGS: Amtlicher Gemeindeschlüssel 5桁または郡コード）に対応し、親ステーション・乗換エリア（Bereich）・個別番線／バス標柱（Steig/Gleis）の3階層でマルチモーダル結節点を表現する（例：ベルリン中央駅 de:11000:900100003、ミュンヘン中央駅 de:09162:6）。 |
| 鉄軌道 | 駅等級区分（Preisklasse 1〜7） | DB InfraGO AG（Stationspreissystem） | 整数 1 〜 7 | 乗降客数・発着列車本数・ホーム数・バリアフリー設備に基づく全旅客駅の7段階公式階層。Preisklasse 1（全国最重要ハブ21駅）、Preisklasse 2（ICE/IC主要停車駅約87駅）、Preisklasse 3（地域中核駅約250駅）、Preisklasse 4（高頻度RE/S-Bahn拠点駅約630駅）、Preisklasse 5（中小都市駅約1,000駅）、Preisklasse 6（地方基本設備駅約2,500駅）、Preisklasse 7（地方簡易停留所Haltepunkte約900駅）。 |
| 高速道路 | Knotenpunktnummer（IC/JCT番号：AK, AD, AS） | Die Autobahn GmbH / StVO Zeichen 406 | 路線別連番整数（1〜）＋追加枝番（a, b） | 四肢以上のジャンクション Autobahnkreuz (AK)、三肢ジャンクション Autobahndreieck (AD)、一般道接続インターチェンジ Anschlussstelle (AS) に同一連番体系で付与される公式番号（StVO標識 Zeichen 406）。 |
| 空港 | IATA / ICAO空港コード | IATA / ICAO / DFS | IATA: 英字3文字 / ICAO: ED**（民間）または ET**（軍民共用） | 民間空港・交通飛行場は ED プレフィックス4文字（主要国際空港は EDD*：例 EDDF / FRA）、軍用・軍民共用飛行場は ET プレフィックス4文字（例：ロストック＝ラーゲ ETNL / RLG）。 |
| 港湾 | UN/LOCODE | UNECE（国連欧州経済委員会） | DE ＋ 英字3文字（5文字） | 海港（Function 1）および内陸河川港（Function 8）の国際位置コード（例：ハンブルク港 DE HAM、ブレーメン港 DE BRE、ブレーマーハーフェン港 DE BRV、デュースブルク内陸港 DE DUI、ロストック港 DE RSK、キール港 DE KEL）。 |

- **鉄道駅・地下鉄駅・電停の法的種別とマルチモーダル階層コード統合**: 鉄道建設・運行規則（EBO第4条）上、鉄道の営業拠点は少なくとも1基以上の分岐器（Weiche）を有し列車の始発・終着・待避が可能な停車場 **`Bahnhof (Bf)`** と、分岐器を持たない本線上の乗降場 **`Haltepunkt (Hp)`**（および分岐点と一体化した `Haltestelle (Hst)`）に厳格に区分される。大規模ターミナル駅（ベルリン中央駅やフランクフルト中央駅等）では、地上ホーム・地下ホーム・S-Bahnホーム・U-Bahn駅・駅前路面電車停留場・バスターミナルにそれぞれ別個のDS 100略号（例：`BLS`, `BL`）やEVA番号が付与されているが、DELFIの全国標準停留所ID（**DHID / IFOPT**）では同一の親ステーションID（`parent_station`）の下に各モードの番線・標柱（Quay）がツリー構造で紐付けられているため、乗換グラフ（Transfer Graph）はDHIDの階層構造を主軸として構築するのが最も正確である。
- **高速道路施設（AK, AD, AS, Raststätte）の公式番号体系と方向規則**: アウトバーン上のすべてのジャンクション（AK / AD）およびインターチェンジ（AS）には、道路交通令（StVO）の標識 **Zeichen 406** により路線ごとの通し番号（Knotenpunktnummer）が付与されている。この付番順序は各路線のキロ程起点（km 0,0）から終点へ向かって割り当てられ、**南北方向の路線（奇数A）は北から南へ**、**東西方向の路線（偶数A）は西から東へ**昇順（`1`, `2`, `3`...）に付番される（ベルリン外環状線A10から放射状に伸びる路線はベルリン側から外側へ昇順）。供用後に既設IC間に新設されたICには `25a`, `25b` のようなアルファベット枝番が付与され、複数路線の重複区間では若番路線の番号体系が優先される。なお、本線直結のサービスエリア（Bewirtschaftete Rastanlage / Raststätte）およびパーキングエリア（P / PWC）にはZeichen 406の番号は付与されず、路線番号・進行方向（Richtungsfahrbahn）・キロ程（Betriebskilometer）によって台帳管理される。
- **旅客空港（IATA / ICAOコード）および主要港湾（UN/LOCODE）の識別仕様**: 空港ノードはIATA 3文字コードとICAO 4文字コード（民間 `ED**`）の双方を保持する。港湾ノードについては、北海・バルト海の主要外貿・フェリー港湾（ハンブルク `DE HAM`、ブレーマーハーフェン `DE BRV`、ヴィルヘルムスハーフェン `DE WVN`、エムデン `DE EME`、クックスハーフェン `DE CUX`、ロストック `DE RSK`、キール `DE KEL`、リューベック `DE LBC`、プットガルデン `DE PUT`、ザスニッツ `DE SAS`）および世界最大の内陸河川港であるデュースブルク港（Port of Duisburg：`DE DUI`）やケルン港（`DE CGN`）、マンハイム港（`DE MHG`）に対してUN/LOCODEを付与し、離島連絡フェリーの発着桟橋（Norddeich Mole、Dagebüll Mole等）にはUN/LOCODEに加えてDELFIのDHIDおよびWSVの連邦水路キロ程（BWaStr-km）を併記して道路・鉄道網と接続する。

## 7. 路線の繋がり（順序）の公式基準 ＆ 駅順データ調達

| 対象レイヤー | 公式順序基準・主キー | 原典データセット・提供機関 | 順序決定ロジック・抽出フィールド |
| --- | --- | --- | --- |
| 鉄道物理インフラ網（EBO/ESBO線路・全停車場・分岐点） | VzG線区番号（Streckennummer 4桁） ＋ 公式キロ程（Streckenkilometer） | DB InfraGO AG「Geo-Streckennetz」/「Infrastrukturregister (ISR)」/ EBA「Strecken-Locator」 | streckennummer（4桁：1000〜9999）でグループ化し、線区起点からの線形参照累積距離 km_lfd（Kilometersprung補正済キロ程）の昇順で停車場（DS 100）をソート。 |
| 鉄道・都市軌道・バス・渡船の旅客運行系統（Service Lines） | DELFI GTFS stop_sequence / NeTEx PointInJourneyPattern | Mobilithek / DELFI e.V.「Deutschlandweite Soll-Fahrplandaten (GTFS / NeTEx)」 | GTFSの routes.txt → trips.txt → stop_times.txt の stop_sequence 昇順で stops.txt の stop_id（DHID）を抽出し、系統ごとの正確な停車駅・停留所順序を確定。 |
| 連邦遠距離道路網（Autobahn / Bundesstraße） | 路線番号 ＋ 道路網ノード（Netzknoten）間の距離標（Stationierung / Betriebskilometer） | Die Autobahn GmbH / BKG / 各州道路建設局（ASB / OKSTRA台帳） | 北→南（奇数A）または西→東（偶数A）のキロ程昇順およびKnotenpunktnummer（Zeichen 406）昇順でAK/AD/ASノードを順序付け。 |
| 連邦水路網（河川・運河・沿岸航路） | 連邦水路番号（BWaStr-ID） ＋ 水路キロ程（BWaStr-km） | 連邦水路・航運局（WSV / GDWS）「VerkNet-BWaStr」/「BWaStr-Locator REST API」 | 水路番号（4桁）ごとに定義された起点（水源または河口・分岐点）からの BWaStr-km 昇順で渡船場・閘門・港湾ノードを順序付け。 |

- **起点〜終点までの順序を決定する公式基準（DB InfraGO公式線区番号［Streckennummer 4桁］、公式キロ程［Streckenkilometer］、駅順）**: ドイツ国内のすべての公共鉄道路線は、「現地許容速度台帳（VzG: Verzeichnis örtlich zulässiger Geschwindigkeiten）」に基づく**4桁の公式線区番号（Streckennummer：`1000`〜`9999`）**によって物理インフラ単位で一意に管理されている。線区番号の先頭数字は地域ブロックに対応し、`1000〜1999` が北部・北西部（ハンブルク・ブレーメン・ニーダーザクセン・シュレースヴィヒ＝ホルシュタイン：例 `1700` ハノーファー〜ハンブルク線）、`2000〜2999` がノルトライン＝ヴェストファーレン州（例 `2650` ケルン〜ハム線）、`3000〜3999` がヘッセン・ラインラント＝プファルツ・ザールラント州、`4000〜4999` がバーデン＝ヴュルテンベルク州、`5000〜5999` がバイエルン州、`6000〜6999` が東部6州（ベルリン・ブランデンブルク・ザクセン等）、`7000〜9999` が非連邦鉄道（NE-Bahnen）および特殊接続線に割り当てられている。各4桁線区には固有の起点（Nullpunkt：`km 0,000`）から終点へ向かって公式キロ程（Streckenkilometer）が昇順に振られているが、過去の線路付け替えや曲線改良により実距離が変化した箇所では、後続区間のキロポスト打ち直しを回避するために「長尺キロ程（Überlänge）」または「欠番・飛越キロ程（Fehl-Länge / Kilometersprung：例 `km 45,200 = km 45,800`）」が存在する。そのため、プログラムで物理的な駅順および分岐点（Abzweigstelle）の並び順を自動生成する際は、単なる表示キロ程文字列ではなく、DB InfraGOのGIS路線網データに収録されている**線区起点からの線形参照実累積距離（`km_lfd`）の昇順**でソートすることが必須の実装基準となる。
- **公式路線網台帳（Streckenverzeichnis、Infrastrukturregister等）の入手先URL**: 全国の鉄道インフラ台帳の一次原典は、DB InfraGO AGが一般鉄道法（AEG）に基づき公開している **インフラストラクチャ登録簿（Infrastrukturregister - ISR）**（`https://www.dbinfrago.com/web/schienennetz/netzzugang-und-regulierung/infrastrukturregister`）であり、インタラクティブ地図（ISR-Viewer）およびWFS/API経由で全線区の4桁番号・キロ程・DS 100停車場・電化方式・軸重・最高速度を取得できる。また、機械判読可能なGISファイル（GeoJSON / Shapefile / CSV）およびREST APIは **DB API Marketplace**（`https://developers.deutschebahn.com/` 内の `ISR Data Service`、`Geo-Streckennetz`、`Betriebsstellen`、`StaDa - Station Data`）および **連邦鉄道庁（EBA）のGeoPortal.EBA**（`https://geoportal.eisenbahn-bundesamt.de/` 内の `Strecken Locator` および `Betriebsstellen` レイヤ）から直接ダウンロード可能である。
- **全国オープン交通データポータル（Mobilithek: mobilithek.info / DELFI）のGTFS・NeTExデータからの駅順調達可能性**: EU委任規則（(EU) 2017/1926）、旅客運送法（PBefG）、およびモビリティデータ令（Mobilitätsdatenverordnung）の法的義務に基づき、ドイツ国内の全公共交通事業者の時刻表・路線・停留所データは、**DELFI e.V.** の統合プラットフォーム（DIP）および全国運輸連合オープンデータプラットフォーム（DODP）を経由して、国家アクセスポイントである **Mobilithek（`https://mobilithek.info`）** に集約・無償公開されている。この「ドイツ全国標準時刻表データ（Deutschlandweite Soll-Fahrplandaten）」は **GTFS形式** および欧州標準 **NeTEx形式** の双方で提供されており、DB長距離列車（ICE/IC/EC）、全国の地域鉄道（RE/RB/S-Bahn：DBおよびNE-Bahnen全社）、全国の都市軌道（U-Bahn、Stadtbahn、Straßenbahn）、路線バス・長距離バス、定期渡船・フェリーを100%網羅している。したがって、物理的な鉄道線路と全駅のトポロジー順序はDB InfraGOの「ISR / Geo-Streckennetz（VzG 4桁線区番号＋キロ程）」から構築し、その上を走る旅客運行系統（快速列車REが通過駅をスキップする停車パターン等）やBOStrab都市軌道・バス・フェリーの停留所順序はDELFI GTFSの `stop_times.txt`（`stop_sequence`）またはNeTExの `ServiceJourneyPattern` から自動抽出して、DHID / EVA番号で両レイヤーを結合するハイブリッド調達が完全に可能である。

## 8. 交通オープンデータの出典メタデータ一覧（data_sources.csv 登録用表）

| source_id | category | source_name_ja | provider_ja | license | url | attribution_required | terms_summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DE_MOBILITHEK_DELFI | 総合公共交通（鉄道・軌道・バス・船） | ドイツ全国公共交通統合時刻表・停留所データ（DELFI Soll-Fahrplandaten GTFS / NeTEx） | DELFI e.V. / 連邦デジタル・交通省（BMDV - Mobilithek） | CC BY 4.0 / DL-DE->BY-2.0 | https://mobilithek.info/ | true | 商用・非商用問わず無償利用・加工・再配布可能。利用時は「Quelle: DELFI e.V. / Mobilithek」等の出典表示が必須。 |
| DE_DB_ISR | 鉄軌道インフラ台帳 | DB InfraGO インフラストラクチャ登録簿（Infrastrukturregister: ISR） | DB InfraGO AG | DB公的公開規約（無償閲覧・API利用可） | https://www.dbinfrago.com/web/schienennetz/netzzugang-und-regulierung/infrastrukturregister | true | AEGおよびEU指令に基づく公的インフラ台帳。WFS/API経由での路線番号・キロ程・設備データの取得時にDB InfraGO AGの出典明記が必要。 |
| DE_DB_API_MARKETPLACE | 鉄軌道拠点・路線GIS | DB API Marketplace（StaDa駅データ・Betriebsstellen・Geo-Streckennetz） | Deutsche Bahn AG / DB InfraGO AG | CC BY 4.0 | https://developers.deutschebahn.com/ | true | 開発者ポータルにてCC BY 4.0で公開。DB駅番号、DS 100略号、Preisklasse、VzG路線網GISデータの商用・非商用利用が可能（クレジット表記必須）。 |
| DE_EBA_GEOPORTAL | 鉄軌道GIS・規制情報 | 連邦鉄道庁 地理情報ポータル（GeoPortal.EBA） | 連邦鉄道庁（Eisenbahn-Bundesamt: EBA） | DL-DE->BY-2.0（データライセンス・ドイツ - 表示 - Version 2.0） | https://geoportal.eisenbahn-bundesamt.de/ | true | 著作権保護あり、DL-DE->BY-2.0の下で無償利用可能。出典表記「© Eisenbahn-Bundesamt (www.eba.bund.de/)」が必須。 |
| DE_AUTOBAHN_OPENDATA | 高速道路網・拠点 | 連邦高速道路オープンデータ・Autobahn App API | Die Autobahn GmbH des Bundes | DL-DE->BY-2.0 / CC BY 4.0 | https://www.autobahn.de/ | true | 全国のアウトバーン路線、IC/JCT、SA/PA、交通規制情報をREST APIおよびMobilithek経由で無償提供。出典表記が必要。 |
| DE_BKG_GEOBASIS | 道路網・行政界・基底GIS | 連邦測地庁 デジタル景観モデル・交通網データ（DLM250 / INSPIRE TN） | 連邦測地庁（Bundesamt für Kartographie und Geodäsie: BKG） | DL-DE->BY-2.0（GeoNutzV準拠） | https://gdz.bkg.bund.de/ | true | 連邦地理データ利用規定（GeoNutzV）およびDL-DE->BY-2.0に基づき無償利用可能。「© GeoBasis-DE / BKG」の出典表示が必須。 |
| DE_WSV_GEODATEN | 水路・航路・渡船インフラ | 連邦水路・航運局 地理データサービス（VerkNet-BWaStr / WInD / ELWIS） | 連邦水路・航運局（WSV / GDWS） | GeoNutzV / DL-DE->BY-2.0 | https://www.gdws.wsv.bund.de/DE/service/karten/02_Geodatendienste_Geoanwendungen/01_Geodatendienste/Geodatendienste_node.html | true | 連邦地理データ利用規定（GeoNutzV）に準拠しアクセス制限なしで無償利用可能。出典表記「© www.wsv.de」が必須。 |
| DE_LBA_DFS_AIP | 空港・航空路 | 連邦航空局 公認空港・事業者一覧およびDFS航空路誌（BasicAIP） | 連邦航空局（LBA） / ドイツ航空保安公社（DFS） | 公的資料公開（AIPは航法・参照規約準拠） | https://www.lba.de/ | true | LBAの認可空港・航空会社一覧は公的統計・台帳として参照可能。DFS BasicAIPはWeb上で無償閲覧可能。 |
| DE_OSM_GEOFABRIK | 総合道路・鉄軌道・交通網 | OpenStreetMap ドイツ全国抽出データ（Geofabrik Germany） | OpenStreetMap Contributors | ODbL 1.0 | https://download.geofabrik.de/europe/germany.html | true | ODbL 1.0ライセンスに準拠。「© OpenStreetMap contributors」の帰属表示および派生データベース公開条件を適用。 |
| DE_WIKIDATA_SPARQL | 鉄軌道・交通拠点属性 | Wikidata SPARQL Query Service（ドイツ交通エンティティ） | Wikimedia Foundation | CC0 1.0（パブリックドメイン） | https://query.wikidata.org/ | false | CC0 1.0により帰属表示の法的義務なしで商用・データベース統合に自由利用可能。 |

## 9. 一次情報源・公式オープンデータ入手先リンク集

- **連邦デジタル・交通省（BMDV）および国家モビリティデータポータル（Mobilithek）URL**: 連邦デジタル・交通省（BMDV）公式サイト（`https://bmdv.bund.de/` および `https://www.bmv.de/`）、国家モビリティデータポータル **Mobilithek**（`https://mobilithek.info/`：DELFI全国GTFS/NeTEx、リアルタイムSIRI/GTFS-RT、道路・シェアリングデータの国家アクセスポイント）、および **DELFI e.V.** 公式サイト（`https://www.delfi.de/`）。
- **連邦道路公社（Die Autobahn GmbH des Bundes）道路網データURL**: Die Autobahn GmbH des Bundes 公式サイト（`https://www.autobahn.de/`）、Autobahn交通情報・オープンデータポータル（`https://verkehr.autobahn.de/` および `https://mobilithek.info/offers/110000000003477001`）、ならびにドイツ道路・交通オブジェクトカタログ標準 **OKSTRA**（`https://www.okstra.de/`）。
- **DB InfraGO AG オープンデータ・路線台帳URL**: DB InfraGO AG インフラストラクチャ登録簿 **Infrastrukturregister (ISR)**（`https://www.dbinfrago.com/web/schienennetz/netzzugang-und-regulierung/infrastrukturregister`）、**DB API Marketplace**（`https://developers.deutschebahn.com/db-api-marketplace/apis/product/isr-data-service` および `https://developers.deutschebahn.com/`：ISR、StaDa駅データベース、DS 100 Betriebsstellen、Geo-Streckennetz提供）、ならびにDB旅客駅情報ポータル（`https://www.bahnhof.de/`）。
- **連邦鉄道庁（Eisenbahn-Bundesamt - EBA）GISポータルURL**: **GeoPortal.EBA** マップビューア・OGCサービス配信ポータル（`https://geoportal.eisenbahn-bundesamt.de/` および `https://www.eba.bund.de/kartendienst`：Strecken-Locator、Betriebsstellen、WFS/WMTS提供）、および連邦鉄道庁（EBA）公式サイト（`https://www.eba.bund.de/`）。
- **連邦水路・航運局（WSV）水路・航路データURL**: 連邦水路・航運局（WSV）公式サイト（`https://www.wsv.de/`）、水路・航運総局（GDWS）地理データサービス一覧（`https://www.gdws.wsv.bund.de/DE/service/karten/02_Geodatendienste_Geoanwendungen/01_Geodatendienste/Geodatendienste_node.html`：VerkNet-BWaStr、BWaStr-Locator REST API、WInD、Inland ENC提供）、GDWSデジタル連邦水路図・路線番号台帳（`https://www.gdws.wsv.bund.de/DE/service/karten/01_karten/karten-node.html`）、電子水路情報システム **ELWIS**（`https://www.elwis.de/`）、および水位・観測所WFS/RESTサービス **PEGELONLINE**（`https://www.pegelonline.wsv.de/webservices/gis/aktuell/wfs`）。
- **連邦航空局（LBA）空港一覧URL**: 連邦航空局（Luftfahrt-Bundesamt - LBA）公式サイト・認可事業者一覧（`https://www.lba.de/`）、ドイツ航空保安公社（DFS）航空路誌 **BasicAIP**（`https://aip.dfs.de/basicAIP/`）、およびドイツ空港協会（ADV）公式サイト（`https://www.adv.aero/`）。
