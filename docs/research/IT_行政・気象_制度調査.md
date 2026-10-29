--- 
title: イタリア行政・気象データ基礎調査要綱 - Google Gemini
date: 2026/10/28 10:20:11
source: https://gemini.google.com/app/7f2963d74f86dd84?canvas-id=im_cf8194780d6e8782
model: Gemini
---

## イタリアの行政・統計・気象GIS調査

# イタリア 行政・統計・気象制度 事前調査シート

- 調査日: 2026-10-28
- 根拠法令・公式資料: イタリア共和国憲法第5部（Costituzione della Repubblica Italiana, Parte II, Titolo V, Art. 114-133）、地方自治統一法（D.Lgs. 18 agosto 2000, n. 267 - TUEL）、広域市・県・コムーネ連合に関する2014年法律第56号（Legge 7 aprile 2014, n. 56）、国家統計局（ISTAT）『Codici statistici delle unità amministrative territoriali』『Basi territoriali e variabili censuarie』、全国都市道路地番アーカイブ技術仕様書（Specifiche tecniche ANNCSU - DPCM 12 maggio 2016）、国家測地系規定（DM 10 novembre 2011 - Adozione del Sistema di riferimento geodetico nazionale RDN2008）、国立気象気候庁設立規則（DPR 15 ottobre 2020, n. 186 - Regolamento ItaliaMeteo、および2026年予算法 Legge 30 dicembre 2025, n. 199）、市民保護局コード（D.Lgs. 2 gennaio 2018, n. 1 - Codice della protezione civile）。

## 1. 対象国基本情報・地理的範囲

- 国名（日本語 / 公用語 / 英語）: イタリア共和国 / Repubblica Italiana / Italian Republic
- ISO 3166-1コード: Alpha-2: `IT`, Alpha-3: `ITA`, 数値: `380`
- 公用語: イタリア語（全国公用語。憲法第6条および1999年法律第482号に基づき、地域レベルでトレンティーノ＝アルト・アディジェ特別自治州ボルツァーノ自治県のドイツ語およびラディン語、ヴァッレ・ダオスタ特別自治州のフランス語、フリウリ＝ヴェネツィア・ジュリア特別自治州のスロベニア語およびフリウリ語、サルデーニャ特別自治州のサルデーニャ語等を公認。ISTATの自治体名称台帳および全国都市道路地番アーカイブ［ANNCSU］では、二言語公用地域の自治体名・道路名［DUF］においてイタリア語名と地域公用語名をスラッシュ区切りまたは別カラムで併記管理するデータベース仕様となっている）。
- 国家体制: 単一国家（地方分権型単一国家、全20州［普通自治州15州・特別自治州5州］）。
- 領土バウンディングボックス（経緯度範囲）: 南端（最小緯度）は北緯35°29'24"（`35.4900° N`：シチリア州アグリジェント自由基礎自治体組合ランペドゥーザ・エ・リノーザ基礎自治体に属するペラージェ諸島ランピョーネ島［Isolotto di Lampione］、ランペドゥーザ島本島南端Punta Pesce Spadaは `35.4929° N`）、北端（最大緯度）は北緯47°05'29"（`47.0914° N`：トレンティーノ＝アルト・アディジェ州ボルツァーノ自治県プレドーイ［Predoi / Prettau］のヴェッタ・ディターリア［Vetta d'Italia］）、西端（最小経度）は東経06°37'32"（`6.6256° E`：ピエモンテ州トリノ広域市バルドネッキア［Bardonecchia］のロッカ・ベルナウダ［Rocca Bernauda］）、東端（最大経度）は東経18°31'13"（`18.5203° E`：プッリャ州レッチェ県オトラント［Otranto］のパラシア岬［Capo d'Otranto / Punta Palascìa］）である。データベースへの異常座標混入を防止する空間バリデーション用バウンディングボックス（WGS84 / EPSG:4326）としては、陸域検査範囲 `Lon: [6.60, 18.55], Lat: [35.45, 47.10]`、領海（12海里）を含む空間インデックス範囲 `Lon: [6.30, 18.85], Lat: [35.25, 47.15]` を適用する。
- 飛び地・海外領土・特殊行政区域: ロンバルディア州コモ県に属するカンピオーネ・ディターリア（Campione d'Italia、ISTATコード: `013040`、面積 2.68 km²）はスイス連邦ティチーノ州（ルガーノ湖畔）の領域内に完全に囲まれた国外飛び地（エクスプラーブ）であり、EU関税領域および物品税領域に属する一方、付加価値税（IVA）は適用外（現地の地方消費税を適用）で、法定通貨ユーロと並びスイス・フランが流通する。GISポリゴン処理上、カンピオーネ・ディターリアはスイス国境ポリゴンの内部リング（inner ring）かつイタリア・ロンバルディア州・コモ県の外部飛び地ポリゴン（multipolygon outer）として構成される。ロンバルディア州ソンドリオ県のリヴィーニョ（Livigno、ISTATコード: `014037`）はアルプス主分水嶺北側のドナウ川水系スポール川流域に位置し、EU関税領域外および付加価値税（IVA）非課税地域に指定されているが、行政階層および統計区画上は通常のコムーネとして扱われる。また、イタリア領土内にはバチカン市国（Stato della Città del Vaticano、ISO 3166-1: `VA` / `VAT` / `336`、ラツィオ州ローマ広域市ローマ市内に完全包囲）およびサンマリノ共和国（Repubblica di San Marino、ISO 3166-1: `SM` / `SMR` / `674`、エミリア＝ロマーニャ州リミニ県とマルケ州ペーザロ・エ・ウルビーノ県の境界に完全包囲）の2つの独立主権国家（エンクラーブ）が存在するため、イタリア全体の国境ポリゴンおよび該当する州・県・コムーネの行政境界ポリゴンにおいて中抜き穴（inner ring）としてトポロジー除外処理を行う必要がある。なお、憲法上およびISO規格上の海外領土・属領は存在しない。

## 2. 行政区画・国勢調査区の体系と詳細分類

### 2.1 行政・気象・統計階層と区域種別一覧（area_types.csv 登録データ表）

| type_id | 大分類 | 階層レベル | 種別名_日本語 | 種別名_公用語 | 規模目安(件数) | 検証状態 | 法的根拠・自治権の有無・説明 | Wikipedia_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IT-T-RIP | 統計 | 1 | 地理的大区分（NUTS 1） | Ripartizione geografica | 5件 | 公的リスト取得済 | ISTATおよびEurostat（NUTS 1）が規定する統計上の最上位大区分（北西部、北東部、中部、南部、島嶼部）。法人格や行政機関・自治権は持たない。 | https://it.wikipedia.org/wiki/Gruppi_di_regioni_d%27Italia |
| IT-T-RSO | 行政 | 2 | 州（普通自治州） | Regione a statuto ordinario | 15件 | 公的リスト取得済 | 憲法第114条・第117条・第123条に基づく第一級地方自治体。州政府（Giunta regionale）および州議会（Consiglio regionale）を有し、憲法が国に専属留保した事項以外の立法権・行政権を持つ。 | https://it.wikipedia.org/wiki/Regione_a_statuto_ordinario |
| IT-T-RSS | 行政 | 2 | 特別自治州 | Regione a statuto speciale | 5件 | 公的リスト取得済 | 憲法第116条第1項および憲法的法律（特別自治憲章）により特別な自治の形態・条件が付与された第一級地方自治体（ヴァッレ・ダオスタ、トレンティーノ＝アルト・アディジェ、フリウリ＝ヴェネツィア・ジュリア、シチリア、サルデーニャ）。広範な一次的立法権および域内地方自治体制度の編成権を持つ。 | https://it.wikipedia.org/wiki/Regione_a_statuto_speciale |
| IT-T-CMT | 行政 | 3 | 広域市（大都市圏） | Città metropolitana | 14件 | 公的リスト取得済 | 憲法第114条および2014年法律第56号・各特別自治州法に基づく第二級広域自治体（普通自治州10件、シチリア州3件、サルデーニャ州1件）。広域市長（Sindaco metropolitano）および広域市議会を置き、広域インフラ・都市計画・交通網を管轄する。ISTATの超コムーネ領域単位（UTS）およびNUTS 3を構成。 | https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_(Italia) |
| IT-T-PRV | 行政 | 3 | 県 | Provincia | 80件 | 公的リスト取得済 | 憲法第114条および2014年法律第56号に基づく第二級広域自治体（普通自治州76県＋サルデーニャ特別自治州4県）。県知事（Presidente della Provincia）、県議会および県首長会議を有し、広域調整・道路管理・学校施設管理等を担う。ISTATのUTS（全107件）およびNUTS 3を構成。 | https://it.wikipedia.org/wiki/Provincia_(Italia) |
| IT-T-PAU | 行政 | 3 | 自治県 | Provincia autonoma | 2件 | 公的リスト取得済 | 憲法第116条第2項およびトレンティーノ＝アルト・アディジェ特別自治州憲章に基づく特別自治体（トレント自治県、ボルツァーノ自治県）。一般の県とは異なり州と同等の一次的立法権・行政権を有し、EUのNUTS分類でもNUTS 2（ITH1, ITH2）およびNUTS 3の双方に位置付けられる。 | https://it.wikipedia.org/wiki/Province_autonome_di_Trento_e_Bolzano |
| IT-T-LCC | 行政 | 3 | 自由基礎自治体組合（シチリア） | Libero consorzio comunale | 6件 | 公的リスト取得済 | シチリア特別自治州法2015年第15号に基づき設置されている第二級広域自治体（アグリジェント、カルタニッセッタ、エンナ、ラグーザ、シラクーザ、トラーパニの6区域）。法人格と自治権を有し、ISTATのUTS（全107件）およびNUTS 3を構成。 | https://it.wikipedia.org/wiki/Libero_consorzio_comunale |
| IT-T-EDR | 行政 | 3 | 地域分権機関（フリウリ） | Ente di decentramento regionale | 4件 | 公的リスト取得済 | フリウリ＝ヴェネツィア・ジュリア特別自治州法2019年第21号により設置されている州の機能分権機関（ウーディネ、ポルデノーネ、ゴリツィア、トリエステ）。地方自治体としての政治的自治権や議決機関は持たないが、ISTAT統計上は県と同列の超コムーネ領域単位（UTS全107件の一部）およびNUTS 3として3桁コードが割り当てられている。 | https://it.wikipedia.org/wiki/Ente_di_decentramento_regionale |
| IT-T-UDC | 行政 | 4 | コムーネ連合・山岳共同体 | Unione di comuni / Comunità montana | 約550件 | 統計参照 | 地方自治統一法（D.Lgs. 267/2000）第27条〜第32条および各州法に基づき、複数のコムーネが行政事務の共同処理のために形成する地方公共団体（トレント自治県の渓谷共同体［Comunità di valle］15件等を含む）。全国土を網羅する階層ではなく、該当地域のみに存在する。 | https://it.wikipedia.org/wiki/Unione_di_comuni |
| IT-T-COM | 行政 | 5 | コムーネ（基礎自治体） | Comune | 7,896件 | 公的リスト取得済 | 憲法第114条およびD.Lgs. 267/2000に基づく最基礎の地方自治体（2025年1月1日時点ISTAT公式確定数7,896件；データセットの基準時期により7,896〜7,899件）。首長（Sindaco）、行政委員会（Giunta comunale）および議会（Consiglio comunale）を持ち、戸籍・住民登録（Anagrafe）、都市計画、道路・地番管理（ANNCSU）等の一次的自治権を有する。EUのLAUに完全対応。 | https://it.wikipedia.org/wiki/Comune_(Italia) |
| IT-T-CIR | 行政 | 6 | 都市内行政分権区（ムニチピオ・区） | Circoscrizione di decentramento / Municipio | 約250件 | 公的リスト取得済 | D.Lgs. 267/2000第17条に基づき、大都市コムーネ内部に設置される行政分権区域（人口25万人超のコムーネで設置義務、10万〜25万人で任意設置）。都市により「Municipio（ローマ15区、ミラノ9区、ジェノヴァ9区、バーリ5区）」「Circoscrizione（トリノ8区）」「Quartiere（ボローニャ6区、フィレンツェ5区）」「Municipalità（ナポリ10区、ヴェネツィア6区）」等と呼称される。独立法人格は持たないが、区長および区評議会を置く。ISTATのAree subcomunali（ASC）としてポリゴン提供済。 | https://it.wikipedia.org/wiki/Circoscrizione_di_decentramento_comunale |
| IT-T-FRA | 行政 | 7 | 分離集落・字（フラツィオーネ） | Frazione geografica | 約35,000件 | 統計参照 | D.Lgs. 267/2000第17条およびコムーネ定款（Statuto comunale）に基づく基礎自治体内の集落区分。原則として法人格・自治権は持たないが、一部でコムーネ首長の代理人（Prosindaco）の配置や、共有地管理のための分離財産管理区（Amministrazione separata dei beni di uso civico - ASBUC）が管理権を持つ場合がある。 | https://it.wikipedia.org/wiki/Frazione_(geografia) |
| IT-T-LOC | 統計 | 7 | 居住・生産ロカリティ | Località abitata e produttiva | 61,101件 | 公的リスト取得済 | ISTATの領域基盤（Basi territoriali 2021）において定義される集落・土地利用ポリゴン。中心集落（Centro abitato）、小集落（Nucleo abitato）、生産地区（Località produttiva）、および残余の散居地域（Case sparse）に分類される統計単位であり、自治権はない。 | https://it.wikipedia.org/wiki/Localit%C3%A0_abitata |
| IT-T-SEZ | 統計 | 8 | 国勢調査区 | Sezione di censimento | 約402,000件 | 公的リスト取得済 | ISTATが国勢調査および場所の基本統計レジストリ（RSBL）の最小空間単位としてコムーネ内を隙間なく分割したポリゴン区画。道路地番アーカイブ（ANNCSU）の各アクセス（建物入口）にも必ず所属国勢調査区コードが紐付けられる。自治権なし。 | https://it.wikipedia.org/wiki/Sezione_di_censimento |
| IT-T-ZAL | 気象 | 4 | 気象・水文警報区域 | Zona di allerta | 158件（細分約170件） | 公的リスト取得済 | 市民保護局コード（D.Lgs. 1/2018）および2004年首相府指令に基づき、全国21の州・自治県機能センター（CFD）が水害・土砂災害・雷雨等の気象警報を発令するために河川流域・地形別に画定した区域（全国標準158区域、ヴェネト州25区域等の州細分を含めると約170区域）。 | https://it.wikipedia.org/wiki/Protezione_civile |
| IT-T-MAR | 気象 | 4 | 海上気象予報区（メテオマール） | Settore Meteomar | 16件（広域29件） | 公的リスト取得済 | イタリア空軍気象局（CNMCA）がWMO GMDSS基準に基づき発表する海上気象通報「Meteomar」の予報海域。イタリア周辺海域（Mari italiani）として16セクター、地中海全域の暴風・雷雨監視対象を含めると29セクターで構成される。 | https://it.wikipedia.org/wiki/Meteomar |

### 2.2 国勢調査・統計調査区の体系（将来用ストック）

- 所管統計機関名・公式ポータルURL: イタリア国家統計局（ISTAT: Istituto Nazionale di Statistica、公式ポータル `https://www.istat.it/` 、地理・空間統計データ専用ポータル `https://www.istat.it/statistiche-per-temi/focus/informazioni-territoriali-e-cartografiche/` ）が全国の行政単位コードおよび統計調査区を一元的に所管している。
- 基礎自治体（Comune）より細かい統計調査単位の階層構造・単位名称・件数規模: ISTATは「統合レジストリシステム（SIR: Sistema Integrato dei Registri）」および「常設国勢調査（Censimento permanente della popolazione e delle abitazioni）」の空間インフラである「場所の基本統計レジストリ（RSBL: Registro statistico di base dei luoghi）」の下に、「領域基盤（Basi territoriali - BT）」として4層のサブコムーネ統計区画を整備している。第1の層は「サブコムーネ区域（Aree subcomunali - ASC）」であり、大都市・中核都市に設定される行政分権区（Municipi, Circoscrizioni, Quartieri）および都市統計区を指し、2021年確定版データ（`ASC_21.ZIP`、2026年5月14日改訂版）として社会経済的困窮指数（IDISE）等の都市内集計単位に使用される。第2の層は「国勢調査集計区（Aree di censimento - ACE）」および「都市形態集積地（Agglomerati morfologici urbani - AMU）」であり、ACEは人口2万人以上のコムーネまたは県都において複数の調査区を束ねた中間集計区（全国約3,000件、BT2011定義）、AMUは土地被覆と市街地の連続性に基づく都市集積ポリゴン（BT2021確定値で全国2,623件）である。第3の層は「居住・生産ロカリティ（Località abitate e produttive）」であり、コムーネ内を集落形態と機能で分割した単位として全国61,101件（面積約21,000 km²、国土の6.9%）が画定されており、「1: 中心集落（Centro abitato：公共施設やサービスが集積し建物が連続する集落）」「2: 小集落（Nucleo abitato：中心施設を持たない小規模な建物群）」「3: 生産地区（Località produttiva：市街地外にある工業・商業団地）」「4: 散居地域（Case sparse：上記1〜3以外の農山村・散居領域）」の4種別に完全分類される。第4の最下層は最小の空間統計単位である「国勢調査区（Sezioni di censimento、全国約402,000件）」であり、1つの国勢調査区は必ず単一のコムーネおよび単一のロカリティ（上記1〜4のいずれか）に完全に内包される厳密な階層トポロジーを持つ。区画境界の生成・更新にはAGEAの都市部20cm・郊外50cm解像度オルソフォト、地籍図（Catasto）、およびOpenStreetMapの建物ポリゴン（50mバッファによる凝集判定）が併用されている。
- 統計調査区境界データ（Shapefile/GeoJSON等）の入手先URL・更新頻度: 国勢調査区・ロカリティ・サブコムーネ境界データはISTATのBasi territoriali配布ページ（`https://www.istat.it/notizia/basi-territoriali-e-variabili-censuarie/`）にて、州別または全国一括のShapefile（文字コードUTF-8、座標系WGS84）および統計変数テーブルとして提供されている。一方、統計目的の行政境界（州・県・コムーネ）は行政境界配布ページ（`https://www.istat.it/notizia/confini-delle-unita-amministrative-a-fini-statistici-al-1-gennaio-2018-2/`）にて、高精度な「詳細版（Versione non generalizzata）」とWeb描画向けの「簡略版（Versione generalizzata）」の2種類が提供されている。更新頻度について、行政境界（州・県・コムーネ）は毎年1月1日基準で年1回更新（最新版は2026年1月1日基準）され、国勢調査区（Basi territoriali）は10年ごとの基準年（直近は2021年12月31日基準のBT2021確定版）に加え、地籍・衛星データを用いた継続的更新および常設国勢調査に基づく年次サブコムーネ統計（ $t+2$ 年公表サイクル）として運用されている。

### 2.3 「政庁所在地（役所・庁舎の点座標）」の公式定義とデータ有無

- 各自治体の代表点座標における「役場・庁舎（Municipio / Casa Comunale）」と「幾何学的重心（Centroid）」の区別および入手方法: ISTATが提供するGIS境界データ（Basi territoriali / Confini amministrativi）や内部の統計ジオコーディング基盤で用いられているコムーネおよび国勢調査区の単一代表点座標は、原則として「領域ポリゴンの幾何学的重心（Coordinate del centroide del comune / Centroide della sezione di censimento）」であり、住所正規化や番地特定が不可能な統計レコードのフォールバック位置座標としてもこのコムーネ重心が割り当てられる仕様となっている。一方で、ISTATが公表する「コムーネの主要地理的特性（Principali caratteristiche geografiche dei comuni）」において、各コムーネの公式代表標高（Altitudine del centro）は「市役所・役場庁舎（Casa Comunale / Municipio）が位置する地点の海抜標高（m s.l.m.）」として厳密に定義されているものの、ISTATの自治体コード一覧CSV単体には庁舎建物の経緯度座標カラムは含まれていない。そのため、データベース構築において「役場・庁舎（Casa Comunale）の正確な建物位置座標」を公的オープンデータのみで確定するには、デジタルイタリア庁（AgID）が管理する「公的機関デジタル住所録（IPA: Indice dei domicili digitali della Pubblica Amministrazione、`https://indicepa.gov.it/`）」から全コムーネの法定本庁舎（Sede legale del Comune）の公式住所（道路名・番地）を取得し、これをISTATと歳入庁（Agenzia delle Entrate）が共同運用する「全国都市道路地番アーカイブ（ANNCSU: Archivio Nazionale dei Numeri Civici delle Strade Urbane、`https://www.anncsu.gov.it/`）」のオープンデータ（月次一括ダウンロードまたは日次更新API）と結合する手法が最も確実である。ANNCSUの各アクセス（建物入口番号）には国家測地系（RDN2008 / WGS84）の経度・緯度座標および測位精度フラグ（`METODO`: `1`=現地GNSS測量［誤差5m未満］、`2`=現地測量［誤差5m以上］、`3`=地図データベースからの間接取得［誤差5m未満］等）が記録されているため、全コムーネの庁舎玄関の正確な点座標を100%公的ソースから取得できる。さらに補完ソースとして、OpenStreetMapのコムーネ境界リレーション（`boundary=administrative` + `admin_level=8`）におけるメンバーロール `admin_centre`（または `amenity=townhall`）およびWikidataの `P159`（本部所在地）修飾子座標をクロスチェックに利用できる。

### 2.4 OpenStreetMap（OSM）admin_level 対照表

| admin_level | 本国の行政区画種別（公用語/日本語） | 該当件数 | 備考 |
| --- | --- | --- | --- |
| 2 | Stato (Repubblica Italiana) / 国（イタリア共和国） | 1件 | 領海（原則12海里）を含む国家境界リレーション。バチカン市国およびサンマリノ共和国を inner ロールで中抜き除外し、スイス国内のカンピオーネ・ディターリアを outer ロールで包含する。 |
| 3 | Ripartizione geografica (NUTS 1) / 地理的大区分 | 5件 | ISTAT / Eurostatの5大統計区分（Nord-ovest, Nord-est, Centro, Sud, Isole）。行政機関ではないため、通常の boundary=administrative としては原則使用されないか統計境界として区別される。 |
| 4 | Regione (a statuto ordinario / speciale) / 州（普通自治州・特別自治州） | 20件 | 第一級行政区画。ref:ISTAT タグに2桁のISTAT州コード（01〜20）、ISO3166-2 タグに IT-21〜IT-88 を付与。 |
| 5 | （該当なし / 未使用） | 0件 | イタリア国内のOSMマッピング基準において admin_level=5 に割り当てられる現行行政区画は存在しない。 |
| 6 | Provincia / Città metropolitana / Provincia autonoma / Libero consorzio comunale / EDR / 県・広域市・自治県・自由基礎自治体組合・地域分権機関 | 106〜107件 | 第二級広域行政・統計区画（NUTS 3相当）。ヴァッレ・ダオスタ州（州が県機能を兼務）を除く106件、またはヴァッレ・ダオスタを含めた107件。ref:ISTAT タグに3桁コード（001〜111等）、short_name または ISO3166-2 に2文字県略号（IT-RM, IT-MI等）を付与。 |
| 7 | Comunità montana / Comunità isolana / Comunità di valle / Unione di comuni / 山岳共同体・渓谷共同体・コムーネ連合 | 約550件 | 複数コムーネによる広域連合や山岳共同体（トレント自治県の15のComunità di valle等）。設置されている地域のみに存在し、全国を網羅するポリゴン層ではない。 |
| 8 | Comune / コムーネ（基礎自治体） | 7,896件 | 基礎自治体（LAU相当）。全国土を隙間・重複なく完全分割する最重要ポリゴン層。ref:ISTAT タグに6桁のISTATコード（例: 058091）、ref:catasto タグに4桁の地籍コード（例: H501）が標準付与される。 |
| 9 | Circoscrizione / Municipio (uso residuale) / 都市内行政区（一部都市の例外階層） | 数十件 | イタリアのOSM基準ではコムーネ内の行政分権区は原則 admin_level=10 に統一されているが、ミラノ等の大都市で admin_level=9 が一部併用されているケースがある。 |
| 10 | Municipio / Circoscrizione di decentramento / Quartiere / Frazione / 都市内行政分権区・分離集落 | 約300件（行政区）＋数千件（集落） | ローマ市（Roma Capitale）の15のMunicipiなど、D.Lgs. 267/2000第17条に基づく都市内行政分権区の標準レベル。また一部地域でFrazione（分離集落）の境界にも使用される（なおローマのZone urbanistiche等の都市計画統計区には admin_level=11 が使用される）。 |

## 3. 公式コード体系とWikidataプロパティ

### 3.1 国内公式コード（自治体コード・統計区コード）

- コード規格名・桁数ルール・体系の仕組み: 国家統計局（ISTAT）が管理する「ISTAT統計コード（Codice ISTAT / Codici statistici delle unità amministrative territoriali）」がすべての公的統計・GIS境界データの主キーとなる（先頭ゼロが意味を持つため、データベース上では必ず固定長文字列型 `CHAR` / `VARCHAR` として格納すること）。上位から順に、地理的大区分コード（`COD_RIP`: 1桁 `1`〜`5`）、州コード（`COD_REG`: 2桁 `01`［ピエモンテ州］〜`20`［サルデーニャ州］）が定義される（なお保健医療省や州の医療システムでは州コードを3桁 `010`〜`200` で表し、トレンティーノ＝アルト・アディジェ州 `04` を `041`［ボルツァーノ自治県］と `042`［トレント自治県］に分割する派生規格が存在するため外部データ結合時に注意を要する）。県・超コムーネ領域単位コード（`COD_PROV` / `COD_UTS`）は3桁数字（`001`［トリノ］〜`111`［スッド・サルデーニャ］）であり、「州コード2桁＋1桁」ではなく全国を通じた独立の3桁通し番号となっている（例：ラツィオ州は `12`、ローマは `058`）。14の広域市（Città metropolitana）には、3桁のUTS基本コード（例：ローマ `058`、ミラノ `015`）に加えて `200` 番台の広域市識別コード（`COD_CM`: ローマ `258`、ミラノ `215` 等、UTS基本コードに200を加算した番号）が併記されるが、コムーネコードの先頭3桁およびUTS標準主キーとしては `001`〜`111` の基本コードが使用される。基礎自治体のコムーネコード（`PRO_COM_T`）は6桁数字（`PPPCCC` 形式）であり、先頭3桁（`PPP`）が「所属する県（UTS）の3桁コード」、末尾3桁（`CCC`）が「県内のコムーネ通し番号（`001` から付番）」で構成される（例：カゼルタ県 `061` ＋ サン・マルチェッリーノ `077` ＝ `061077`）。サブコムーネ統計区画では、国勢調査区コード（`SEZ2021`）が「コムーネコード6桁＋調査区番号7桁ゼロ埋め（`NSEZ`）」の13桁数字、ロカリティコード（`LOC2021`）が「コムーネコード6桁＋種別1桁（`1`〜`4`）＋通し番号4桁」の11桁数字で構成される。さらに、歳入庁（Agenzia delle Entrate）が管理する4桁英数字の「地籍コード / ベルフィオーレ・コード（Codice Catastale / Codice Belfiore：先頭英大文字1桁＋数字3桁、例：ローマ `H501`、ミラノ `F205`）」が個人納税者番号（Codice Fiscale）や不動産登記・自治体間連携における第二主キーとして機能しているほか、全国都市道路地番アーカイブ（ANNCSU）では全国道路コード（`PROG_NAZ_STR`）および全国アクセスコード（`PROG_NAZ_ACC`）により全道路と建物入口に全国一意の連番IDが付与されている。
- 最新版コードリストの入手先（公式ダウンロードURL・ファイル形式）: ISTAT公式コード配布ページ（`https://www.istat.it/classificazione/codici-dei-comuni-delle-province-e-delle-regioni/`）および最新コムーネ一覧の固定パーマリンク（`https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv` および `.xls`）から、ISTATコード、イタリア語・地域公用語自治体名、NUTSコード、地籍コード等を網羅した公式マスターファイルを直接取得できる。また、ISTATの「行政・統計単位空間情報システム（SITUAS: `https://situas.istat.it/`）」のWeb画面およびREST APIから最新の州・県・コムーネ一覧をCSV / JSON / Excel形式で抽出可能である。

### 3.2 国際・地域標準コード

- ISO 3166-2:ITコード（州コード、県コード）: 全20州には `IT-` ＋ 2桁数字のコードが割り当てられている（`IT-21` ピエモンテ、`IT-23` ヴァッレ・ダオスタ、`IT-25` ロンバルディア、`IT-32` トレンティーノ＝アルト・アディジェ、`IT-34` ヴェネト、`IT-36` フリウリ＝ヴェネツィア・ジュリア、`IT-42` リグーリア、`IT-45` エミリア＝ロマーニャ、`IT-52` トスカーナ、`IT-55` ウンブリア、`IT-57` マルケ、`IT-62` ラツィオ、`IT-65` アブルッツォ、`IT-67` モリーゼ、`IT-72` カンパニア、`IT-75` プッリャ、`IT-77` バジリカータ、`IT-78` カラブリア、`IT-82` シチリア、`IT-88` サルデーニャ）。また、県・広域市・自治県・自由基礎自治体組合には、伝統的な2文字県略号（Sigla automobilistica）と同一の `IT-` ＋ 英大文字2文字コード（例：`IT-RM` ローマ広域市、`IT-MI` ミラノ広域市、`IT-NA` ナポリ広域市、`IT-BZ` ボルツァーノ自治県、`IT-TN` トレント自治県、`IT-AG` アグリジェント自由基礎自治体組合、`IT-SU` スッド・サルデーニャ県等）が割り当てられている。
- EU地域標準コード（NUTS 1〜3およびLAUコード）: NUTS 1（全5件、3文字）は地理的大区分に対応し、`ITC`（Nord-Ovest：北西部）、`ITH`（Nord-Est：北東部）、`ITI`（Centro：中部）、`ITF`（Sud：南部）、`ITG`（Isole：島嶼部）で構成される。NUTS 2（全21件、4文字）は19の州と2つの自治県に対応しており、トレンティーノ＝アルト・アディジェ州のみ州単位のNUTS 2コードを持たず `ITH1`（ボルツァーノ自治県）と `ITH2`（トレント自治県）の2つに分かれる（他は `ITC1` ピエモンテ、`ITC2` ヴァッレ・ダオスタ、`ITC3` リグーリア、`ITC4` ロンバルディア、`ITH3` ヴェネト、`ITH4` フリウリ＝ヴェネツィア・ジュリア、`ITH5` エミリア＝ロマーニャ、`ITI1` トスカーナ、`ITI2` ウンブリア、`ITI3` マルケ、`ITI4` ラツィオ、`ITF1` アブルッツォ、`ITF2` モリーゼ、`ITF3` カンパニア、`ITF4` プッリャ、`ITF5` バジリカータ、`ITF6` カラブリア、`ITG1` シチリア、`ITG2` サルデーニャ）。NUTS 3（全107件、5文字）はISTATの107の超コムーネ領域単位（UTS）と1対1で完全一致し（例：`ITC4C` ミラノ、`ITI43` ローマ、`ITF33` ナポリ）、LAU（Local Administrative Units、全7,896件）はコムーネと1対1で完全一致して6桁のISTATコムーネコードがそのままLAUコードとして使用される。

### 3.3 Wikidata抽出プロパティ（P番号）

- 自治体コードプロパティ番号: `P635`（ISTAT ID：州2桁、県・UTS 3桁、コムーネ6桁のISTAT公式コードであり、WikidataとISTAT台帳を結合する絶対的主キー）、`P806`（Italian cadastre code：4桁の地籍コード／ベルフィオーレ・コード、例 `H501`）、`P605`（NUTS code：EU NUTS 1〜3コード）、`P300`（ISO 3166-2 code）、`P402`（OpenStreetMap relation ID）。
- 公式ウェブサイト（P856）、人口（P1082）、上位行政区画（P131）等の指定条件: SPARQLクエリで現行の7,896コムーネのみを正確に抽出する際は、分類プロパティ `P31`（instance of）に `wd:Q747074`（comune of Italy）を指定した上で、`FILTER NOT EXISTS { ?item wdt:P31 wd:Q1134686 }`（廃止コムーネの除外）および `P31` ステートメントに終了日修飾子 `pq:P582`（end time）または廃止日 `wdt:P576`（dissolved, abolished or demolished date）が存在しないことを必須条件とする（上位区画の `P31` は普通自治州 `wd:Q16110`、特別自治州 `wd:Q585956`、広域市 `wd:Q15110`、県 `wd:Q15089`、自治県 `wd:Q1710033`、自由基礎自治体組合 `wd:Q21190155`、地域分権機関 `wd:Q97336222`）。上位行政区画 `P131`（located in the administrative territorial entity）は `wikibase:BestRank` かつ終了日修飾子 `pq:P582` なしの条件で現行の所属UTS・州を取得する。政庁所在地 `P36`（capital）は州都・県都コムーネの特定に加え、分散型コムーネ（Comune sparso：自治体名と役場所在集落名が異なるコムーネ）における役場所在フラツィオーネ（Frazione capoluogo）の特定に使用する。座標 `P625`（coordinate location）に加え、役場庁舎建物のピンポイント座標には `P159`（headquarters location：市役所庁舎）の修飾子 `pq:P625`、標高には `P2044`（Casa Comunale基準の海抜標高）、面積には正規化ノード `p:P2046/psn:P2046`、人口には `P1082`（時点修飾子 `pq:P585` 付き最新値）、公式ウェブサイトには `P856`、郵便番号（CAP 5桁）には `P281` を指定する。

## 4. 気象機関・予報区・観測網

### 4.1 国家気象機関と予報区体系（陸上および海上）

- 国家気象機関名および公式サイトURL: イタリアの気象・水文業務は、軍事（空軍）・文民（国立気象気候庁）・防災（市民保護局および各州機関）の3主体が法令に基づき連携する分担体制となっている。第1に「イタリア空軍気象局（Servizio Meteorologico dell'Aeronautica Militare - CNMCA: Centro Nazionale di Meteorologia e Climatologia Aerospaziale / COMET、公式サイト `https://www.meteoam.it/`）」は世界気象機関（WMO）におけるイタリアの常任代表機関であり、航空気象、防衛気象、一般天気予報、および海上気象通報（Meteomar）の作成・発表を所管する。第2に「国立気象気候庁イタリアメテオ（Agenzia nazionale per la meteorologia e climatologia "ItaliaMeteo"、公式サイト `https://www.agenziaitaliameteo.it/`）」は2017年法律第205号および大統領令（DPR 15 ottobre 2020, n. 186）に基づきボローニャに設置された国家文民気象機関であり、国・州の気象観測網の技術標準策定（空間解像度・取得頻度・品質基準の統一）、数値気象予測プロダクトの作成および各州機関との調整を担い、2026年予算法（Legge 30 dicembre 2025, n. 199）に基づき内閣府市民保護局が同庁の指導・監督（indirizzo e vigilanza）を担う。第3に「内閣府市民保護局（Dipartimento della Protezione Civile - DPC、公式サイト `https://www.protezionecivile.gov.it/` 、リアルタイム警報マップ `https://mappe.protezionecivile.gov.it/`）」は、市民保護局コード（D.Lgs. 1/2018）に基づき、DPCの中央機能センター（CFC）と19州・2自治県の分散機能センター（CFD: Centri Funzionali Decentrati、州立環境保護庁ARPAや州防災局内に設置）からなる機能センター網（Rete dei Centri Funzionali）を通じて全国気象・水文警報システムを運用する。
- 陸上気象予報区・警報区域の階層構造（市民保護局の警報ゾーン［Zone di allerta］等）: 陸上警報の空間階層は「全国（DPC中央機能センター）」→「21の州・自治県警報管区（19州＋トレント自治県＋ボルツァーノ自治県）」→「警報区域（Zone di allerta）」→「コムーネ（Comune）」で構成される。警報区域（Zone di allerta）は2004年2月27日首相府指令（Direttiva PCM 27 febbraio 2004）に基づき、行政境界（県境）ではなく「河川流域（Bacini idrografici）」「地形・標高特性（山岳・丘陵・平野・沿岸）」「降水気候区分」の均一性を基準として全国を分割したポリゴン区画であり、全国標準の集計単位として158区域（例：アブルッツォ州 `Abru-A`〜`D`、エミリア＝ロマーニャ州 `A1`〜`H2` の18区域等）が設定されている。さらに各州CFDレベルでは細分ゾーンの運用が行われており（例：ヴェネト州では8つのマクロゾーン `A`〜`H` の下に25の細分ゾーン `A1`〜`H6` を設定）、データベース上は「DPC全国コード（例: `Vene-A`）」と「州細分コード（例: `A1`, `A2`）」の親子関係および各区域に属するコムーネ（ISTAT 6桁コード）のマッピングテーブルを保持する設計とする。全国共通の警報リスク種別は「水害リスク（Rischio idraulico：大河川本川の洪水）」「水文地質リスク（Rischio idrogeologico：斜面崩壊・中小河川の氾濫）」「雷雨に伴う水文地質リスク（Rischio idrogeologico per temporali：短時間強雨による鉄砲水・都市型浸水）」の3区分（州レベルでは強風［Vento forte］、大雪［Neve］、路面凍結［Ghiaccio al suolo / Pioggia che gela］、雪崩［Valanghe］、熱波［Ondate di calore］を追加監視）であり、「緑（Verde：重大性なし）」「黄（Giallo：通常重大性）」「オレンジ（Arancione：中度重大性）」「赤（Rosso：高度重大性）」の4段階カラーコードで毎日発表される。
- 地中海・沿岸海上予報区（Meteomar等）の体系: 空軍気象局（CNMCA）がWMO GMDSSの「METAREA III（地中海・黒海）」基準に基づき、1日4回（00, 06, 12, 18 UTC）発表する公式海上気象通報「Meteomar」（`https://www.meteoam.it/it/messaggio-meteomar`、沿岸無線VHF Ch 16 / Ch 68 156.425 MHz、NAVTEXおよび沿岸警備隊航行警報で配信）によって運用されている。その第4部等で12時間ごとの風向・風力（ビューフォート階級）・波浪（ダグラス海況階級）が個別発表される「イタリア周辺海域（Mari italiani）」は以下の16セクターに区分されている：(1) `Mar Ligure`（リグーリア海）、(2) `Mar di Corsica`（コルシカ海）、(3) `Mar di Sardegna`（サルデーニャ海）、(4) `Canale di Sardegna`（サルデーニャ海峡）、(5) `Tirreno settentrionale`（ティレニア海北部）、(6) `Tirreno centrale - settore ovest`（ティレニア海中部・西セクター）、(7) `Tirreno centrale - settore est`（ティレニア海中部・東セクター）、(8) `Tirreno meridionale - settore ovest`（ティレニア海南部・西セクター）、(9) `Tirreno meridionale - settore est`（ティレニア海南部・東セクター）、(10) `Stretto di Sicilia`（シチリア海峡）、(11) `Ionio meridionale`（イオニア海南部）、(12) `Ionio settentrionale`（イオニア海北部）、(13) `Adriatico meridionale`（アドリア海南部）、(14) `Adriatico centrale`（アドリア海中部）、(15) `Adriatico settentrionale`（アドリア海北部）、(16) `Mare e Canale di Malta`（マルタ海・マルタ海峡）。また、第1部（Avvisi：雷雨・暴風警報）および第3部（Previsione）では、これら16海域に加えて地中海全域の広域13〜14セクター（`Mar di Alboran`, `Mare Nord Baleari`, `Mare Sud Baleari`, `Golfo del Leone`, `Mar Libico`, `Mar di Creta`, `Mar Egeo`, `Mar di Levante`, `Mar Nero` 等）が監視対象となる。

### 4.2 地上気象観測網と観測所地点リスト入手先

- 国家観測網・州立環境保護庁（ARPA）観測網の構造: イタリアの地上気象・水文観測網は3系統のネットワークが相互補完・データ統合される構造を持つ。第1は「空軍気象局・航空気象観測網（Rete sinottica AM / ENAV）」であり、空軍気象局（Aeronautica Militare）および航空管制公社（ENAV）が全国の空港・主要拠点で運用する約110箇所の総観気象観測所（SYNOP / METAR、WMO国際地点番号ブロック `16`：`16001`〜`16597`、WIGOS ID `0-20000-0-16xxx`）で構成される。第2は「市民保護局・各州機能センター統合水文気象観測網（Rete fiduciaria nazionale / Reti ARPA-APPA）」であり、19州の環境保護庁（ARPA: Agenzia Regionale per la Protezione dell'Ambiente、エミリア＝ロマーニャ州はARPAE等）およびトレント・ボルツァーノ両自治県の環境保護庁（APPA）、または州市民保護局が直接維持管理している約4,500箇所以上の自動気象・雨量・水位・積雪テレメトリ観測所群で構成され、リアルタイムで市民保護局（DPC）の中央システム（Dewetraプラットフォーム）およびItaliaMeteoに集約されている。第3は「専門機関観測網」であり、農業食料主権森林省（MASAF / CREA）の全国農業気象観測網（RAN: Rete Agrometeorologica Nazionale）、および環境保護高等研究所（ISPRA）の全国潮位観測網（RMN: Rete Mareografica Nazionale、沿岸36地点）と全国波浪観測網（RON）が運用されている。
- 観測所地点マスター（地点番号、名称、緯度・経度、標高）の公式ダウンロードURL・API仕様・形式: 全国横断の統合観測所マスターは、ISPRAが運用する国家気候データシステム「SCIA」（`http://www.scia.isprambiente.it/`）から取得可能であり、空軍（AM）、全州ARPA/APPA、農業気象網（RAN）、ENAV、ISPRAの全国数千箇所の観測所メタデータ（観測所ID、名称、管理機関、所属州・県・コムーネ、WGS84経緯度、標高、観測要素）をCSV / JSON形式でエクスポートできる。また、内閣府市民保護局（DPC）のリアルタイムレーダー・観測所マップ（`https://mappe.protezionecivile.gov.it/`）および公式GitHubリポジトリ（`https://github.com/pcm-dpc`）では、全国警報区域ポリゴン（Shapefile / GeoJSON）および全国の水文気象観測所（雨量計・温度計・水位計）の地点座標・標高・観測値がREST API（GeoJSON）で配信されている。さらに、空軍気象局観測所一覧（`https://www.meteoam.it/it/osservazioni-e-profili-verticali` およびWMO公式メタデータポータル `https://oscar.wmo.int/surface/` ）、ISPRA全国潮位観測網ポータル（`https://www.mareografico.it/` 、CSV / XML / API）、ならびに国家オープンデータカタログ（`https://www.dati.gov.it/`）および各州ARPAのオープンデータポータル（例：エミリア＝ロマーニャ州ARPAE `https://dati.arpae.it/`、ロンバルディア州 `https://www.dati.lombardia.it/` 等）から高密度観測網の地点マスター（CSV / Shapefile / GeoJSON）を直接取得できる。

## 5. 探索・GIS環境・出典メタデータ

### 5.1 公的オープンデータの出典メタデータ一覧（data_sources.csv 登録用表）

| source_id | category | source_name_ja | provider_ja | license | url | attribution_required | terms_summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IT-SRC-ISTAT-COD | 行政コード・統計台帳 | ISTAT 行政・統計単位コードおよび自治体一覧（SITUAS） | イタリア国家統計局（ISTAT） | CC BY 4.0 | https://situas.istat.it/ | true | 出典（Fonte: Istat）の明記を条件に、商用・非商用を問わず複製・改変・二次配布が可能。 |
| IT-SRC-ISTAT-BT | 行政境界・統計調査区 | ISTAT 行政境界および国勢調査領域基盤（Basi territoriali） | イタリア国家統計局（ISTAT） | CC BY 4.0 | https://www.istat.it/notizia/basi-territoriali-e-variabili-censuarie/ | true | 統計目的の行政境界（1991〜2026年）および国勢調査区・ロカリティ・サブコムーネ境界（Shapefile, UTF-8）。出典明記で自由利用可。 |
| IT-SRC-ANNCSU | 住所・道路・庁舎座標 | 全国都市道路地番アーカイブ（ANNCSU Open Data） | イタリア国家統計局（ISTAT）・歳入庁（Agenzia delle Entrate） | CC BY 4.0 | https://www.anncsu.gov.it/ | true | 全国の道路名（Odonimi）および番地・建物入口座標（Accessi）。APIは日次更新、地域・全国一括ダンプは月次更新で無料提供。 |
| IT-SRC-IPA | 行政機関台帳 | 公的機関デジタル住所録（Indice PA - IPA） | デジタルイタリア庁（AgID） | CC BY 4.0 (IODL 2.0) | https://indicepa.gov.it/ | true | 全コムーネ・県・州を含む公的機関の法定本庁舎所在地住所、組織コード、公式URLをオープンデータ（CSV/API）で提供。 |
| IT-SRC-DPC-ZAL | 気象警報区域 | 市民保護局 全国警報区域（Zone di allerta）および気象重大度データ | 内閣府市民保護局（Dipartimento della Protezione Civile） | CC BY 4.0 | https://github.com/pcm-dpc | true | 全国158（細分約170）の気象・水文警報区域ポリゴン（Shapefile/GeoJSON）および日次警報データ。出典（Dipartimento della Protezione Civile）明記で利用可。 |
| IT-SRC-METEOAM | 気象・海上予報 | 空軍気象局（MeteoAM）気象通報・Meteomar・観測データ | イタリア空軍気象局（CNMCA / Aeronautica Militare） | 公的機関利用規約 | https://www.meteoam.it/ | true | 海上気象通報Meteomar（16セクター）および総観気象観測所情報。データの引用・二次利用時は空軍気象局のクレジット表示が必須。 |
| IT-SRC-ITMETEO | 気象・気候標準 | 国立気象気候庁（ItaliaMeteo）技術標準・気象データ | 国立気象気候庁（Agenzia ItaliaMeteo） | CC BY 4.0 | https://www.agenziaitaliameteo.it/ | true | DPR 186/2020に基づく国家気象観測網の統合基準および気象・気候プロダクト。 |
| IT-SRC-ISPRA-SCIA | 気象・水文観測網 | 国家気候データシステム（SCIA）および全国潮位観測網（RMN） | 環境保護高等研究所（ISPRA） | CC BY 4.0 (IODL 2.0) | http://www.scia.isprambiente.it/ | true | 空軍・各州ARPA・農業気象網を統合した全国気象観測所マスター（経緯度・標高）および気候統計値。出典（ISPRA - SCIA）明記で利用可。 |
| IT-SRC-MASE-GN | 背景地図・空間基盤 | 国家地理ポータル（Geoportale Nazionale）WMS/WFS | 環境・エネルギー安全保障省（MASE） | CC BY 4.0 | https://gn.mase.gov.it/ | true | 全国オルソフォト、標高モデル、河川網、行政境界等のOGC WMS/WFSサービスを提供。 |
| IT-SRC-ADE-CAT | 地籍図・建物境界 | 歳入庁 地籍地図WMS・INSPIRE地籍区画（Cartografia Catastale） | 歳入庁（Agenzia delle Entrate） | CC BY 4.0 | https://www.agenziaentrate.gov.it/portale/it/web/guest/schede/fabbricatieterreni/consultazione-cartografia-catastale | true | トレント・ボルツァーノ両自治県を除く全国の地籍境界・筆界・建物形状のWMSおよびINSPIREダウンロードデータ（商用転売制限あり、出典明記必須）。 |

### 5.2 標準測地系・投影法・EPSGコード

- 公式GISデータで採用されている標準測地系・EPSGコードとWGS84への変換要否: 2011年11月10日首相府令（DM 10 novembre 2011）により、イタリア共和国の全公的機関およびGISデータの法定標準測地系は、欧州基準座標系ETRS89の国内実現値である「RDN2008（Rete Dinamica Nazionale 2008：ETRF2000 Epoch 2008.0）」と定められており、地理2D座標系（経緯度）には `EPSG:6706`（RDN2008、GRS80楕円体、歳入庁地籍WMSやANNCSU等の公式基準）および `EPSG:4326`（WGS 84、Web GISや簡略版境界データ等で使用）が用いられる。投影座標系については、イタリア領土が東経6.6°〜18.5°にわたるため、UTMゾーン32N（東経6°〜12°：北西部・中部西側・サルデーニャ州）、ゾーン33N（東経12°〜18°：北東部・中部東側・南部・シチリア州）、およびゾーン34N（東経18°以東：プッリャ州サレント半島東端の一部）の3ゾーンに跨り、軸順序（Axis Order）の違いにより「N-E（北距・東距順：公式・INSPIRE準拠）」と「E-N（東距・北距順：一般的なGISソフトのX-Y順）」の2系統のEPSGコードが定義されている。具体的には、RDN2008 / UTM zone 32Nが `EPSG:6707`（N-E順）および `EPSG:7791`（E-N順）、UTM zone 33Nが `EPSG:6708`（N-E順）および `EPSG:7792`（E-N順）、UTM zone 34Nが `EPSG:6709`（N-E順）および `EPSG:7793`（E-N順）であり、さらに東経12°を中央子午線（縮尺係数0.9985・偽東距7,000,000m）としてイタリア全土を単一平面に投影する国家公式投影法「RDN2008 / Italy zone（Fuso Italia）」として `EPSG:6875`（N-E順）および `EPSG:7794`（E-N順）が規定されている。なお、ISTATが配布する行政境界および国勢調査領域基盤（Basi territoriali）のShapefileは、全国一括での空間解析の利便性から東経12度以東の地域も含めて全国一律で `EPSG:32632`（WGS 84 / UTM zone 32N）に統一投影されており、RDN2008（`EPSG:6706`/`7791`）とWGS 84（`EPSG:4326`/`32632`）の間の座標変換（変換コード `EPSG:6711`）は公的精度1.0m（実測差は数十cm以内）と定義されているため、行政・統計区画レベルのGIS構築ではパラメータ変換なしで事実上同一視して問題ない。一方、地方自治体の技術基本図（CTR）等で用いられることがある旧国家測地系「Roma 1940（Monte Mario）」に基づくガウス・ボアガ（Gauss-Boaga）投影の `EPSG:3003`（西ゾーン）および `EPSG:3004`（東ゾーン）は、WGS 84 / RDN2008に対して水平方向に約100〜200mのオフセットが生じるため、必ず国土地理院（IGM）のNTv2グリッドまたは7パラメータ変換（ヘルマート変換）を適用してWGS 84へ再投影する必要がある。

### 5.3 公式背景地図タイルとストリートビュー・パノラマカバレッジ状況

- 机上探索（Web GIS）で利用可能な現地政府・公的機関の公式背景地図・航空写真タイル: 第1に、環境・エネルギー安全保障省（MASE）の「国家地理ポータル（Geoportale Nazionale - GN / 旧Portale Cartografico Nazionale - PCN、`https://gn.mase.gov.it/`）」がOGC WMSサービス（ベースURL: `http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/...`）を提供しており、全国カラーオルソフォト（`.../raster/ortofoto_colore_12.map` および `ortofoto_colore_06.map`、レイヤ名 `OI.ORTOIMMAGINI.2006.32` / `33`）、県都高解像度オルソフォト（`.../raster/ortofoto_colore_capoluoghi.map`）、IGM 1:25,000地形図（`.../raster/IGM_25000.map`）、河川網（`.../Vettoriali/Aste_fluviali.map`）等を背景利用できる（ただしPCNサーバーは短時間の大量タイル要求に対してIP自動遮断レート制限を行うため、QGISやJOSMではローカルキャッシュ設定が必須）。第2に、歳入庁（Agenzia delle Entrate）が提供する「全国リアルタイム地籍地図WMS（エンドポイント: `https://wms.cartografia.agenziaentrate.gov.it/inspire/wms/ows01.php`）」では、`province`（県・コムーネ境界）、`CP.CadastralParcel`（地番筆界）、`fabbricati`（建物形状）、`strade`（道路）、`vestizioni`（地番ラベル）の各レイヤを配信しており、役場庁舎（Casa Comunale）の建物形状や飛び地境界の机上検証に極めて有効である（トレント・ボルツァーノ両自治県は独自の土地台帳［Catasto tavolare］WMSを運用）。第3に、農業支払庁（AGEA）が撮影する都市部20cm・郊外50cm解像度の最新航空写真および州技術基本図（CTR 1:5,000 / 1:10,000）が、全20州の公式Geoportale（ロンバルディア州 `https://www.geoportale.regione.lombardia.it/`、ヴェネト州 `https://idt2.regione.veneto.it/`、エミリア＝ロマーニャ州 `https://geoportale.regione.emilia-romagna.it/` 等）からWMS/WMTSとして無料公開されている。
- ストリートビュー・パノラマカバレッジ（Googleストリートビュー、Apple Look Around、Mapillary等のイタリア国内整備・更新状況）: Googleストリートビューはイタリア全20州・全7,896コムーネのほぼ100%を網羅しており、建物への大規模なモザイク（ブラー）処理もほとんど存在しないため、コムーネ庁舎（Municipio）の外観、入口に掲示された地番プレート（Numero civico）、道路名標識（Targa stradale）、および集落境界標識（Inizio/Fine centro abitato）を机上で直接目視確認できる。旧市街（Centro storico）の車両進入制限区域（ZTL）やヴェネツィアの歩行者路・運河、山岳集落についてもトレッカー撮影が実施されており、主要道路・都市部では2023〜2026年撮影の最新パノラマに更新されている。また、Apple Look Aroundもイタリア全土（本土およびシチリア・サルデーニャ等の離島全域）で高解像度パノラマを公開しており、Googleストリートビューの死角補完やクロスチェックに有効であるほか、MapillaryおよびKartaViewも高速道路（Autostrade）・国道（SS）・県道（SP）および北イタリア・都市部を中心にCC BY-SAライセンスの豊富な地上画像を有している。

## 6. 一次情報源・公式オープンデータ入手先リンク集

- 自治体・統計調査区オープンデータURL（ISTAT / dati.gov.it）:

  - ISTAT 空間・統計・行政単位総合ポータル: `https://www.istat.it/statistiche-per-temi/focus/informazioni-territoriali-e-cartografiche/`
  - ISTAT 自治体・県・州コード公式ページ: `https://www.istat.it/classificazione/codici-dei-comuni-delle-province-e-delle-regioni/`
  - ISTAT SITUAS（行政・統計単位空間情報システム・コード出力）: `https://situas.istat.it/`
  - ISTAT 国勢調査領域基盤（Basi territoriali e variabili censuarie）: `https://www.istat.it/notizia/basi-territoriali-e-variabili-censuarie/`
  - ISTAT 統計用行政境界データ（Confini delle unità amministrative）: `https://www.istat.it/notizia/confini-delle-unita-amministrative-a-fini-statistici-al-1-gennaio-2018-2/`
  - 全国都市道路地番アーカイブ（ANNCSU 公式ポータル・Open Data・API）: `https://www.anncsu.gov.it/`
  - 公的機関デジタル住所録（Indice PA - IPA オープンデータ）: `https://indicepa.gov.it/`
  - イタリア政府公式オープンデータカタログ（dati.gov.it）: `https://www.dati.gov.it/`
- 国家地理ポータル（Geoportale Nazionale）URL:

  - 環境・エネルギー安全保障省（MASE）国家地理ポータル（Geoportale Nazionale）: `https://gn.mase.gov.it/`
  - デジタルイタリア庁（AgID）国家空間データレパートリ（RNDT: Repertorio Nazionale dei Dati Territoriali）: `https://geodati.gov.it/`
  - 歳入庁（Agenzia delle Entrate）地籍地図WMS・INSPIREサービス: `https://www.agenziaentrate.gov.it/portale/it/web/guest/schede/fabbricatieterreni/consultazione-cartografia-catastale`
  - イタリア国土地理院（IGM: Istituto Geografico Militare）: `https://www.igmi.org/`
- 法令集・官報ポータル（Normattiva）URL:

  - 国家現行法令データベース（Normattiva: Il portale della legge vigente）: `https://www.normattiva.it/`
  - イタリア共和国官報（Gazzetta Ufficiale della Repubblica Italiana）: `https://www.gazzettaufficiale.it/`
  - 内務省地方自治・領域局（DAIT: Dipartimento per gli Affari Interni e Territoriali）: `https://dait.interno.gov.it/`
- 気象機関・観測データポータルURL:

  - イタリア空軍気象局（MeteoAM / CNMCA）公式ポータル: `https://www.meteoam.it/`
  - 空軍気象局 海上気象通報（Messaggio Meteomar）: `https://www.meteoam.it/it/messaggio-meteomar`
  - 国立気象気候庁（Agenzia Nazionale ItaliaMeteo）公式ポータル: `https://www.agenziaitaliameteo.it/`
  - 内閣府市民保護局（Dipartimento della Protezione Civile）公式ポータル: `https://www.protezionecivile.gov.it/`
  - 市民保護局 全国気象レーダー・警報区域リアルタイムマップ: `https://mappe.protezionecivile.gov.it/`
  - 市民保護局 公式GitHubリポジトリ（警報区域Shapefile/GeoJSON等）: `https://github.com/pcm-dpc`
  - 環境保護高等研究所（ISPRA）国家気候データシステム（SCIA）: `http://www.scia.isprambiente.it/`
  - ISPRA 全国潮位観測網（Rete Mareografica Nazionale）: `https://www.mareografico.it/`
