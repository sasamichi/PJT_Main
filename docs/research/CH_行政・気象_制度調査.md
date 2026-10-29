# スイス 行政・統計・気象制度 事前調査シート

- 調査日: 2026-10-27
- 根拠法令・公式資料: スイス連邦憲法（Bundesverfassung der Schweizerischen Eidgenossenschaft: BV, SR 101）、連邦地理情報法（Bundesgesetz über Geoinformation: GeoIG, SR 510.62）、地理空間名政令（Verordnung über die geografischen Namen: GeoNV, SR 510.625）、連邦統計法（Bundesgesetz über die eidgenössische Statistik: BStatG, SR 431.01）、連邦気象気候法（Bundesgesetz über die Meteorologie und Klimatologie: MetG, SR 429.1）、eCH-0071 データ標準「スイス履歴付自治体台帳（Datenstandard Historisiertes Gemeindeverzeichnis der Schweiz V1.2.0）」、連邦測量局（swisstopo）、連邦統計局（BFS / OFS / UST）、連邦気象気候庁（MeteoSwiss / MeteoSchweiz）

## 1. 対象国基本情報・地理的範囲

スイス連邦の空間データ基盤（Federal Spatial Data Infrastructure: FSDI / BGDI）および統計・行政台帳の設計においては、4つの連邦公用語による多言語属性管理と、26カントン（州）が有する高度な自治権（公的測量・境界画定権限を含む）の把握が不可欠である。連邦レベルでは公用語としてドイツ語、フランス語、イタリア語、ロマンシュ語の4言語が規定されているが、空間データの公式名称属性（`swissBOUNDARIES3D` や連邦統計局の公式自治体台帳）は「当該自治体が属するカントンの公用語（現地語）」を正本（プライマリ名称）として格納する仕様を採用している。そのため、グローバルGISデータベースへ統合する際には、単一の国単一言語スキーマではなく、カントンおよび基礎自治体単位での言語コード判定ロジックを実装する必要がある。

| 項目 | 仕様・定義内容 | 備考・根拠規定 |
| --- | --- | --- |
| 国名（日本語） | スイス連邦 | 通称：スイス |
| 国名（ドイツ語: de） | Schweizerische Eidgenossenschaft | 連邦公用語（全人口の約62%が使用） |
| 国名（フランス語: fr） | Confédération suisse | 連邦公用語（西部ロマンディ地域） |
| 国名（イタリア語: it） | Confederazione Svizzera | 連邦公用語（南部ティチーノ州・グラウビュンデン州南部） |
| 国名（ロマンシュ語: rm） | Confederaziun svizra | 連邦公用語（グラウビュンデン州の一部、連邦憲法第4条・第70条） |
| 国名（ラテン語 / 英語） | Confoederatio Helvetica / Swiss Confederation (Switzerland) | ラテン語表記は国コード CH の由来 |
| ISO 3166-1 コード | Alpha-2: CH / Alpha-3: CHE / Numeric: 756 | ドメイン .ch、車両識別記号 CH |
| 国家体制 | 連邦制共和国（26カントンで構成） | 事実上の連邦首都（Bundesstadt）はベルン（Bern） |
| 準州由来カントン（6州） | OW, NW, BS, BL, AR, AI | 連邦参議院議席数（各1議席）および憲法改正州投票（0.5票）を除き、完全な自治権を有する独立カントンとして機能 |
| 領土BBox（本土実測境界） | 東経 5.9559° 〜 10.4921° / 北緯 45.8180° 〜 47.8084° | WGS84 (EPSG:4326)。最西端：Chancy (GE)、最東端：Val Müstair (GR)、最南端：Chiasso (TI)、最北端：Bargen (SH) |
| 領土BBox（WMTSタイル範囲） | 東経 5.5226° 〜 10.9427° / 北緯 45.0769° 〜 48.5308° | Swisstopo WMTS サービス定義領域（周辺緩衝域・リヒテンシュタイン公国を含む） |

各カントンの公用語区分は、カントン憲法に基づき単一言語州（ドイツ語17州、フランス語4州、イタリア語1州）と多言語州（独・仏2言語3州、独・ロマンシュ・伊3言語1州）に厳密に分類される。空間データベースにおける名称検索インデックスや地図ラベル描画ルールを設計する際は、以下のカントン別言語マッピングが基準となる。

| 公用語区分 | 該当カントン数 | 該当カントン（ISO 3166-2:CH 略称および名称） |
| --- | --- | --- |
| ドイツ語単一（de） | 17 | ZH (Zürich), LU (Luzern), UR (Uri), SZ (Schwyz), OW (Obwalden), NW (Nidwalden), GL (Glarus), ZG (Zug), SO (Solothurn), BS (Basel-Stadt), BL (Basel-Landschaft), SH (Schaffhausen), AR (Appenzell Ausserrhoden), AI (Appenzell Innerrhoden), SG (St. Gallen), AG (Aargau), TG (Thurgau) |
| フランス語単一（fr） | 4 | VD (Vaud), NE (Neuchâtel), GE (Genève), JU (Jura) |
| イタリア語単一（it） | 1 | TI (Ticino) |
| 独・仏2言語（de, fr） | 3 | BE (Bern / Berne), FR (Fribourg / Freiburg), VS (Valais / Wallis) |
| 独・ロマンシュ・伊3言語（de, rm, it） | 1 | GR (Graubünden / Grischun / Grigioni) |

地理的範囲および空間トポロジー処理において特筆すべき飛び地（Enklaven / Exklaven）および特殊行政区域は、外国領包領と国内の自治体非所属地域（Gemeindefreie Gebiete）に大別される。スイス領内にはドイツ領ビュージンゲンとイタリア領カンピョーネ・ディターリアという2つの外国領包領が存在し、国境ポリゴン（`Landesgebiet`）にドーナツ状の穴（Interior Ring）を形成しているほか、国内にも特定の基礎自治体に帰属しない国有林・共有地・大規模湖沼が存在し、これらも基礎自治体と同階層のポリゴンレイヤに独立オブジェクトとして格納されている。また、関税・通貨同盟を結ぶ隣接国リヒテンシュタイン公国（全11自治体）の空間境界・標高・気象観測網は、SwisstopoおよびMeteoSwissの国家データセットに標準で統合収録されている。

| 特殊区域種別 | 名称（現地語 / 日本語） | 空間データ・行政制度上の取り扱い仕様 |
| --- | --- | --- |
| 外国領の国内包領（ドイツ領） | Büsingen am Hochrhein（ビュージンゲン） | ドイツ・バーデン＝ヴュルテンベルク州コンスタンツ郡所属。シャフハウゼン州・チューリッヒ州・トゥールガウ州に囲まれる内包飛び地。スイス関税領域内にありスイス郵便番号 8238 が付与されるが、swissBOUNDARIES3D では国境（Landesgrenze）外の穴（Interior Ring）として処理される。 |
| 外国領の国内包領（イタリア領） | Campione d'Italia（カンピョーネ・ディターリア） | イタリア・ロンバルディア州コモ県所属。ティチーノ州およびルガーノ湖に囲まれる内包飛び地。2020年1月よりEU関税領域に復帰。スイス国境ポリゴン上はドーナツ状の除外領域となる。 |
| 国内飛び地（カントン・自治体） | 多数のカントン飛び地（FR, SO, SH, AI, BE, VD等） | フリブール州（Estavayer等の飛地）、ゾロトゥルン州（Kleinlützel、Steinhof等）、シャフハウゼン州（Stein am Rhein周辺、Buchberg/Rüdlingen）、ベルン州（Schelten）など、マルチポリゴン構造を持つカントン・自治体が多数存在する。なお、2026年1月1日付でMoutier（ムティエ）はベルン州からジュラ州へのカントン移管が完了している。 |
| 自治体非所属の州直轄林 | Staatswald Galm（ガルム国有林） | フリブール州ゼー郡（Bezirk See）内に位置する面積約 2.56 km² の州直轄地。いかなる基礎自治体（Gemeinde）にも属さず、独自のBFS番号 2391 を持つ独立ポリゴンとして swissBOUNDARIES3D の基礎単位レイヤに収録される。 |
| 自治体間共有地（Kommunanz） | Comunanza Cadenazzo/Monteceneri (5391)、Comunanza Capriasca/Lugano (5394) | ティチーノ州に存在する複数自治体の共同管轄区域（Kommunanzen / Gemeinschaftsareale）。単一の自治体に帰属しないため、5390番台の固有BFSコードが付与された独立ポリゴンとして管理される。 |
| 自治体未分割の大規模湖沼 | 面積 5 km² 超の湖沼（22湖沼）およびボーデン湖（Bodensee） | 面積 5 km² を超え自治体境界が湖面上に設定されていない湖沼は、9000番台のBFS擬似自治体コードを持つ独立ポリゴンとして収録される。またボーデン湖（Obersee）沖合はスイス・独・墺間で国際法上の国境線が未画定であり、空間データ利用時は湖岸線（Uferlinie）と領水境界の扱いに注意を要する。 |
| 隣接国の包含収録 | Fürstentum Liechtenstein（リヒテンシュタイン公国） | スイスと関税・通貨同盟を結ぶリヒテンシュタイン公国（全11基礎自治体、BFS番号 7001〜7011）は、Swisstopoの swissBOUNDARIES3D や swissALTI3D、MeteoSwissの気象警報・観測網に標準で統合収録されている。 |

## 2. 行政区画・国勢調査区の体系と詳細分類

### 2.1 行政・気象・統計階層と区域種別一覧（area_types.csv 登録データ表）

スイスの空間階層は、連邦・カントン・基礎自治体の3層を基本骨格としつつ、中間階層である郡（Bezirk）の設置有無や名称がカントン法に委ねられている点に最大の特徴がある。さらに、郵便・住所管理に用いられる公式集落（Ortschaft）や、連邦気象気候庁（MeteoSwiss）および連邦雪・雪崩研究所（SLF）が運用する自然災害警報区域（Warnregionen）が独自の空間分割体系を形成している。なお、2026年1月1日発効の自治体合併（アールガウ州Brugg、フリブール州Fétigny-MénièresおよびGurmels、ゾロトゥルン州Kriegstettenの4自治体新設・9旧自治体統合）およびMoutierのジュラ州移管により、スイス全国の基礎自治体数は確定値として2,110件となっている。

> [!NOTE]
> **【プロジェクト収集スコープ】**
> - 当データベースの行政区域収集対象は「連邦国家（Level 1）」、「カントン（Level 3: 26州）」、および「基礎自治体（Level 6: 2,110自治体＋ガルム国有林等の特殊区域）」とします。
> - 郡（Bezirk: Level 5）はカントンにより設置有無が異なり二次的に導出される境界のため、属性または任意参照として保持します。
> - 都市内統計街区（Level 7）や1haメッシュ（Level 8）は初期収集対象外とし、必要に応じた将来用ストック定義とします。

| type_id | 大分類 | 階層レベル | 種別名_日本語 | 種別名_公用語 | 規模目安(件数) | 検証状態 | 法的根拠・自治権の有無・説明 | Wikipedia_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ch_admin_bund | 行政区画 | 1 | 連邦国家 | Schweizerische Eidgenossenschaft / Confédération suisse / Confederazione Svizzera / Confederaziun svizra | 1 | 公的リスト確認済 | スイス連邦憲法第1条に基づく主権国家。swissBOUNDARIES3DのLandesgebietレイヤに対応。【初期収集対象】 | https://de.wikipedia.org/wiki/Schweiz |
| ch_stat_nuts2 | 統計区画 | 2 | 大地域（NUTS-2） | Grossregion / Grande région / Grande regione | 7 | 公的リスト確認済 | 連邦統計局（BFS）およびEurostat協定に基づく統計比較用の広域区分（CH01〜CH07）。行政機関や自治権は一切持たない。 | https://de.wikipedia.org/wiki/Grossregionen_der_Schweiz |
| ch_admin_kanton | 行政区画 | 3 | カントン（州） | Kanton / Canton / Cantone / Chantun | 26 | 公的リスト確認済 | 連邦憲法第1条・第3条に基づく連邦構成主体。独自の憲法・議会・政府・裁判所を有し、公的測量および自治体境界承認の管轄権を持つ。NUTS-3対応。【初期収集対象】 | https://de.wikipedia.org/wiki/Kanton_(Schweiz) |
| ch_admin_verwaltungsregion | 行政区画 | 4 | 行政地域（ベルン州） | Verwaltungsregion / Région administrative | 5 | 公的リスト確認済 | ベルン州法に基づき設置された州と行政管区（Verwaltungskreis）の中間広域単位。OSMでは admin_level=5 にマッピングされる。 | https://de.wikipedia.org/wiki/Verwaltungsregionen_des_Kantons_Bern |
| ch_admin_bezirk | 行政区画 | 5 | 郡・行政管区・選挙区・地域 | Bezirk / District / Distretto / Verwaltungskreis / Wahlkreis / Region / Amt | 143〜144 | 公的リスト確認済 | カントンと基礎自治体の中間単位（BFS 2022年時点で143件、2026年1月Moutier移管に伴い変動）。10カントンでは未設置。 | https://de.wikipedia.org/wiki/Bezirk_(Schweiz) |
| ch_admin_gemeinde | 行政区画 | 6 | 基礎自治体（政治自治体） | Politische Gemeinde / Einwohnergemeinde / Commune politique / Comune politico / Vischnanca politica | 2,110 | 公的リスト確認済 | 連邦憲法第50条により自治権が保障される最小の一般行政単位。BFS公式自治体台帳2026年1月1日基準の確定値。LAUに相当。【初期収集対象】 | https://de.wikipedia.org/wiki/Politische_Gemeinde |
| ch_admin_gemeindefrei | 行政区画 | 6 | 自治体非所属地域・共有地・湖沼 | Gemeindefreies Gebiet / Kommunanz / Staatswald / See | 約25 | 公的リスト確認済 | ガルム国有林（1件）、ティチーノ州コミュナンツァ（2件）、面積5km²超の自治体未分割湖沼（約22件）。swissBOUNDARIES3Dで基礎自治体と同階層に格納。 | https://de.wikipedia.org/wiki/Gemeindefreies_Gebiet |
| ch_admin_corp | 特別自治体 | 6 | 市民自治体・学校自治体・教会自治体 | Bürgergemeinde / Bourgeoisie / Patriziato / Schulgemeinde / Kirchgemeinde | 約3,500 | 統計参照 | 政治自治体とは別に公法人格を持つ伝統的・機能別自治体（森林・共有財産管理等）。【DB取得対象外】 | https://de.wikipedia.org/wiki/Gemeinde_(Schweiz) |
| ch_loc_post | 地理・郵便区画 | 7 | 公式集落（郵便番号区域） | Ortschaft / Localité / Località (AMTOVZ) | 約4,000 | API確認済 | 地理空間名政令（GeoNV）に基づきSwisstopoとスイスポストが管理する公式集落・6桁郵便番号（PLZ6）ポリゴン。【DB取得対象外】 | https://de.wikipedia.org/wiki/Ortschaft |
| ch_stat_quart | 統計区画 | 7 | 統計街区・都市行政区 | Statistisches Quartier / Stadtkreis / Secteur statistique | 約250 | 統計参照 | チューリッヒ（12行政区/34統計街区）等の大都市に設定される都市内統計区画。【DB取得対象外】 | https://de.wikipedia.org/wiki/Stadtteile_der_Stadt_Z%C3%BCrich |
| ch_stat_grid | 統計区画 | 8 | 1ヘクタール統計グリッド | Hektarraster (STATPOP / STATENT) | 約412万セル | API確認済 | BFS GEOSTATが提供する 100m×100m 国家標準統計グリッド（LV95 EPSG:2056 準拠）。【DB取得対象外】 | https://www.bfs.admin.ch/bfs/de/home/dienstleistungen/geostat.html |
| ch_meteo_warn | 気象予報区 | 気象警報区 (面) | 気象警報地域（MeteoSwiss） | Warnregion / Région d'alerte / Regione d'allerta | 159 | 公的リスト確認済 | MeteoSwissが風・雷雨・大雨・大雪・路面凍結・猛暑・霜の警報を発表する面的な最小警報単位。【収集対象】 | https://www.meteoschweiz.admin.ch/ |
| ch_meteo_obj | 気象予報区 | 気象警報対象 (点・湖) | 気象警報オブジェクト（湖沼・空港） | Warnobjekt (See / Flugplatz) | 51 | 公的リスト確認済 | MeteoSwissが強風（25〜33 kt）・暴風（> 33 kt）警報を発表する主要湖沼および飛行場。【収集対象】 | https://www.meteoschweiz.admin.ch/ |
| ch_slf_warn | 自然災害区 | 雪崩警報区 | 雪崩警報単位（SLF） | Lawinenwarnregion (Kleinste Einheit) | 149 | 公的リスト確認済 | 連邦雪・雪崩研究所（SLF）が雪崩ブレティンで使用する最小領域単位。MeteoSwiss警報区と調和化済。 | https://www.slf.ch/ |
| ch_bafu_drought | 自然災害区 | 渇水警報区 | 渇水予測・警報地域（BAFU） | Trockenheits-Warnregion | 38 | 公的リスト確認済 | 連邦環境庁（BAFU）とMeteoSwissが共同運用する渇水プラットフォームの広域水文警報区画。 | https://www.naturgefahren.ch/ |

スイスの行政階層データをRDBMSやGISスキーマに実装する際、最も注意すべき構造的特性は「郡（Bezirk）階層の非対称性と派生性」にある。連邦測量局（swisstopo）が明記している通り、カントン境界および基礎自治体境界は地籍測量（Amtliche Vermessung: AV）の筆界（Grundstücksgrenzen）に厳密に一致する法的境界であるが、郡境界（Bezirksgrenzen）は独自の測量境界階層を持たず、基礎自治体ポリゴンの集合（空間結合・ディゾルブ）から純粋に導出される二次的境界である。さらに、全26カントンのうち10カントン（UR, OW, NW, GL, ZG, BS, SH, AR, NE, GE）には行政区画としての郡が存在しないため、空間データベース設計においては基礎自治体（Gemeinde）の親外部キー（Parent ID）を必ずしも郡（Bezirk）経由とせず、カントン（Kanton）への直接参照と郡への任意参照（NullableまたはBFSのダミー郡コード経由）を併用する正規化モデルが求められる。

### 2.2 国勢調査・統計調査区の体系（将来用ストック）

スイスの公的統計および国勢調査（Eidgenössische Volkszählung）は、連邦内務省（EDI）傘下の連邦統計局（Bundesamt für Statistik: BFS / Office fédéral de la statistique: OFS / Ufficio federale di statistica: UST、公式ポータル：`https://www.bfs.admin.ch/`）が所管している。2010年以降、スイスの国勢調査は従来の10年ごとの全数調査票方式から、各自治体の住民登録台帳および連邦建物・住居登録台帳（GWR / RegBL）を毎年末基準（12月31日現在）で集計するレジスターベースの年次統計「人口・世帯統計（STATPOP: Statistik der Bevölkerung und der Haushalte）」および「構造調査（Strukturerhebung）」へと完全移行している。空間統計データおよび小地域境界は、BFSの空間データサービス部門である **GEOSTAT**（`https://www.bfs.admin.ch/bfs/de/home/dienstleistungen/geostat.html`）および空間区分ポータル（`https://www.bfs.admin.ch/bfs/de/home/grundlagen/raumgliederungen.html`）から一元的に提供されている。

基礎自治体（Politische Gemeinde）より細かい小地域・ミクロ統計区の階層構造は、大都市内部の「都市統計街区（Statistische Quartiere）」「調査区（Zählkreise）」と、全国土をシームレスに覆う「1ヘクタール統計グリッド（Hektarraster）」および「連邦建物・住居登録点（GWR）」の4階層で整備されている。

| 小地域・統計区種別 | 名称（独 / 仏） | 件数規模 | 空間構造・識別コード仕様 | 更新頻度・入手先および主な収録統計 |
| --- | --- | --- | --- | --- |
| 都市統計街区 | Statistische Quartiere / Secteurs statistiques (Quartiers) | 主要約20都市・計約250街区 | チューリッヒ（12行政区・34統計街区）、ジュネーヴ、バーゼル、ベルン、ローザンヌ等の大都市圏のみに定義されるポリゴン。BFS自治体番号（4桁）＋街区枝番（2〜3桁）で識別。 | 毎年1月1日基準でBFS ThemaKart境界データセット内に収録公開。都市内部の人口動態・社会経済指標・投票行動分析に使用。 |
| 調査区（サブ街区） | Zählkreise / Cercles de recensement | 主要都市・計約700区域 | 統計街区（Quartier）をさらに細分化した統計調査区。都市自治体の統計局（Statistik Stadt Zürich等）およびBFSが管理。 | 各都市のオープンデータポータル（例：geoportal.zh.ch 等）およびBFSで随時更新。学区需要予測や詳細人口分析に使用。 |
| 1ヘクタール統計グリッド | Hektarraster / Grille kilométrique et hectométrique (GEOSTAT) | 国土全域約412万セル（データ賦存セル約35万〜40万） | 国家標準座標系 LV95 (EPSG:2056) に準拠した 100 m × 100 m（1 ha）の正方形メッシュ。セル左下隅の東距（E）・北距（N）座標値から一意のグリッドID（RELI）を生成。 | 毎年8月下旬（前年12月31日基準データ）にBFS GEOSTATおよび opendata.swiss 上でCSV/Shapefile/GeoPackageとして更新公開。STATPOP（常住人口・年齢・国籍・世帯）およびSTATENT（事業所・従業者数）を収録。 |
| 連邦建物・住居登録点 | Eidgenössisches Gebäude- und Wohnungsregister (GWR / RegBL) | 約180万棟（点座標・3D建物連携） | すべての建物に一意の「連邦建物識別子（EGID: Eidgenössischer Gebäudeidentifikator）」および住居識別子（EWID）を付与。Swisstopoの swissBUILDINGS3D 3.0 ともEGIDで直接結合可能。 | FSDI（data.geo.admin.ch）上で日次〜月次更新。すべてのレジスター統計（STATPOP等）の最小集計原単位（マイクロデータ位置参照）として機能。 |

### 2.3 「政庁所在地（役所・庁舎の点座標）」の公式定義・データ有無

スイスの空間データ体系において、行政自治体の代表点座標（Point Geometry）や役場庁舎位置を取得・定義する方法は、利用目的に応じて3系統の公式データセットに明確に分かれている。第一に、地図上のラベル配置や都市・集落の代表点（政庁所在地の中心点）としては、Swisstopoが提供する公式地名データベース `swissNAMES3D` が国家標準となる。従来、`swissNAMES3D` では集落名（Siedlungsnamen）は有効範囲を示すポリゴン（Gültigkeitsperimeter）としてのみ収録されていたが、**2026年4月アップデート版より新たに集落名の中心点オブジェクト（Punktobjekte / Zentrumspunkte）がGeoPackage等の形式で正式に追加収録**されており、精密な代表点座標として直接利用できる。

第二に、物理的な市町村役場・行政庁舎（Gemeindehaus / Rathaus / Hôtel de ville / Maison communale / Municipio）の建物座標を取得する場合は、Swisstopoの3次元地形景観モデル `swissTLM3D`（2026年2月最新版）の建物・施設レイヤ、および連邦統計局（BFS）の「連邦建物・住居登録台帳（GWR / RegBL）」における建物分類コード（公共行政庁舎）と連邦建物識別子（EGID）を参照する。さらに第三の手段として、Swisstopoが連邦空間データ基盤（`data.geo.admin.ch`）上で公開している「公式建物住所台帳（Amtliches Verzeichnis der Gebäudeadressen）」および検索API（`api3.geo.admin.ch/rest/services/api/SearchServer`）を用いれば、全自治体役場の公的住所およびEGIDからミリメートル〜メートル精度の東距（E）・北距（N）座標を直接ジオコーディングすることが可能である。

### 2.4 OpenStreetMap（OSM）admin_level 対照表

スイスにおけるOpenStreetMap（OSM）の行政境界（`boundary=administrative`）は、Swisstopoの `swissBOUNDARIES3D` オープンデータを原典としてインポート・同期整備されており、幾何学的精度（±0.5 m 基準）および網羅性が極めて高い。OSMコミュニティ（`talk-ch`）における合意仕様と公式コードタグの対照は以下の通りである。

| admin_level | 本国の行政区画種別（公用語 / 日本語） | 該当件数 | 備考・OSM固有タグ仕様 |
| --- | --- | --- | --- |
| 2 | Schweizerische Eidgenossenschaft / Confédération suisse / Confederazione Svizzera / Confederaziun svizra（スイス連邦・国境） | 1 | 国境リレーション。ボーデン湖（Bodensee）上の境界線扱いに特有の議論あり。 |
| 3 | （未使用） | 0 | スイス国内では使用されない（NUTS-2の7大地域は統計区画であり行政境界ではないため boundary=administrative 対象外）。 |
| 4 | Kanton / Canton / Cantone / Chantun（カントン・州） | 26 | 全26カントンを完全網羅。公式識別タグとして ISO3166-2=CH-XX およびBFSカントン番号 ref:CH:kantonsnum=1〜26（旧タグ swisstopo:KANTONSNUM から移行）が付与される。 |
| 5 | Verwaltungsregion（ベルン州の行政地域） | 5 | ベルン州（Kanton Bern）の5つの行政地域（Berner Jura, Biel/Bienne, Emmental-Oberaargau, Bern-Mittelland, Oberland）にのみ限定使用される。 |
| 6 | Bezirk / District / Distretto / Verwaltungskreis / Wahlkreis / Region（郡・行政管区・選挙区・地域） | 約137〜143 | 郡を設置する16カントンのみ存在する。公式識別タグとして3〜4桁のBFS郡番号 ref:CH:bezirksnum（例：チューリッヒ州アフォルテルン郡は 101、ヴァレー州東西ラロン準郡は例外的に同一番号 2309 を共有）が付与される。アッペンツェル・インナーローデン州（AI）の6 Bezirkeは基礎自治体相当のため admin_level=8 に配置される。 |
| 7 | （原則未使用 / 歴史的巡回区 Kreis 等） | 0 | かつてグラウビュンデン州の Kreise やティチーノ州の Circoli で使用された例があるが、現行の行政制度では admin_level=6 および 8 に整理されている。 |
| 8 | Politische Gemeinde / Commune / Comune / Vischnanca（基礎自治体）および Gemeindefreies Gebiet（非所属地域・湖沼） | 約2,135（2,110自治体＋特殊区域・湖沼） | 全2,110基礎自治体（2026年1月基準）に加え、ガルム国有林、コミュナンツァ、未分割湖沼ポリゴンがマッピングされている。公式識別タグとして4桁のBFS自治体番号 ref=XXXX または swisstopo:BFS_NUMMER=XXXX が付与される。 |
| 9 | Stadtkreis / Stadtteil（大都市の行政区・地区） | 約30〜50 | チューリッヒ市の12行政区（Stadtkreise 1〜12）やヴィンタートゥール市の7都市区（Stadtkreise）など、大都市内部の上位区画に使用。 |
| 10 | Quartier / Ortsteil / Fraktion（街区・集落・旧自治体地区） | 数百件（整備途上） | チューリッヒ市の34統計街区（Quartiere）や、自治体合併前の旧村落領域（Fraktionen / Ortsteile）などに局所的に使用される。 |

## 3. 公式コード体系とWikidataプロパティ

### 3.1 国内公式コード（自治体コード・統計区コード）

スイス国内における行政区域コードの絶対的基準は、連邦統計局（BFS）が1960年に創設し維持管理している「**スイス公式自治体台帳（Amtliches Gemeindeverzeichnis der Schweiz: AGVCH）**」および電子政府標準規格「**eCH-0071（データ標準：スイス履歴付自治体台帳 V1.2.0）**」で規定される階層コード体系である。このコード体系は、カントン番号（1〜2桁）、郡番号（3〜4桁）、基礎自治体番号（1〜4桁）、および履歴変更番号（5桁）の4つの識別子によって構成されている。

最上位の「BFSカントン番号（Kantonsnummer: `1`〜`26`）」は、スイス連邦憲法第1条における歴史的・伝統的な州の記載順序（チューリッヒ州 `1`、ベルン州 `2`、ルツェルン州 `3` からジュラ州 `26` まで）に従って1から26までの整数が割り当てられている。中間階層の「BFS郡番号（Bezirksnummer: `101`〜`2604`）」は、上位1〜2桁のBFSカントン番号と下位2桁のカントン内連番（`01`〜`99`）を結合した3桁または4桁の数値コードであり、郡を持たない10カントン（ウーリ州 `4`、ジュネーヴ州 `25` 等）には統計処理の階層整合性を保つため下位2桁を `00` としたダミー郡番号（例：`400`、`2500`）がBFS台帳上で付与される。なお、ヴァレー州（カントン番号 `23`）の東ラロン準郡（Östlich Raron）と西ラロン準郡（Westlich Raron）は、例外的に同一のBFS郡番号 `2309` を共有している点に注意が必要である。

基礎自治体を識別する「BFS自治体番号（BFS-Gemeindenummer / Numéro OFS de la commune / Numero UST del comune: `1`〜`6812`）」は、カントンおよび郡ごとに固定の番号帯（Nummernkreise）が割り当てられた1〜4桁の整数コードである。自治体合併（新設合併・編入合併）やカントン移管が発生した際には、原則として当該番号帯内の未使用番号が新規採番されるか存続自治体の番号が継承される。さらに、eCH-0071規格に基づき、1960年以降のすべての自治体レコード状態（新設・名称変更・郡変更・廃止）には一意の5桁の履歴変更番号（Historisierungsnummer、例：`13256`）が付与されており、時系列での空間・属性変遷を完全に追跡できる設計となっている。最新版のコードリスト、2026年1月1日基準のスナップショット、およびXML/TXT/CSV一括ファイルとREST APIは、BFS公式自治体台帳ポータル（`https://www.bfs.admin.ch/bfs/de/home/grundlagen/agvch.html`）および専用Webアプリケーション（`https://www.agvchapp.bfs.admin.ch/de/state/results?SnapshotDate=01.01.2026`）から直接入手できる。

| カントン番号 | ISO略称 | カントン名（現地語） | BFS自治体番号の割当帯（Nummernkreise） | 特殊コード帯（国有林・共有地・湖沼・リヒテンシュタイン） |
| --- | --- | --- | --- | --- |
| 1 | ZH | Zürich | 0001 〜 0299 | — |
| 2 | BE | Bern / Berne | 0301 〜 0996 | — |
| 3 | LU | Luzern | 1001 〜 1151 | — |
| 4 〜 8 | UR, SZ, OW, NW, GL | Uri, Schwyz, Obwalden, Nidwalden, Glarus | 1201 〜 1632 | — |
| 9 〜 14 | ZG, FR, SO, BS, BL, SH | Zug, Fribourg, Solothurn, Basel-Stadt/Land, Schaffhausen | 1701 〜 2974 | 2391: Staatswald Galm (FR州ガルム国有林) |
| 15 〜 20 | AR, AI, SG, GR, AG, TG | Appenzell (AR/AI), St. Gallen, Graubünden, Aargau, Thurgau | 3001 〜 4951 | — |
| 21 | TI | Ticino | 5001 〜 5323 | 5391, 5394: Comunanza (TI州共有地2件) |
| 22 〜 25 | VD, VS, NE, GE | Vaud, Valais, Neuchâtel, Genève | 5401 〜 6645 | — |
| 26 | JU | Jura | 6701 〜 6812 | 2026年1月1日付で旧BE州 Moutier がJU州へ移管 |
| — | — | 特殊領域・国外連携 | 7001 〜 9799 | 7001〜7011: リヒテンシュタイン公国11自治体 / 9000番台: 未分割湖沼ポリゴン |

### 3.2 国際・地域標準コード

スイスは欧州連合（EU）非加盟国であるが、スイス＝EU間の二国間統計協力協定に基づき、Eurostat（欧州統計局）の地域統計分類体系である **NUTS（Nomenclature des unités territoriales statistiques）** および **LAU（Local Administrative Units）** に完全準拠したコードを運用している。また、ISO 3166-2:CH コードは国内の車両ナンバープレート、行政文書、および公式自治体名における同名自治体の識別用サフィックス（例：`Biel/Bienne BE`、`Wil SG`、`Rickenbach ZH` vs `Rickenbach TG`）として法的・日常的に使用されている。

| 標準規格名称 | 階層 | コード形式・桁数 | 該当件数 | スイス国内制度との対応・コード一覧 |
| --- | --- | --- | --- | --- |
| ISO 3166-2:CH | カントン | CH-XX（英字2文字） | 26 | 全26カントンの公式2文字略称に CH- を冠したもの：CH-AG, CH-AI, CH-AR, CH-BE, CH-BL, CH-BS, CH-FR, CH-GE, CH-GL, CH-GR, CH-JU, CH-LU, CH-NE, CH-NW, CH-OW, CH-SG, CH-SH, CH-SO, CH-SZ, CH-TG, CH-TI, CH-UR, CH-VD, CH-VS, CH-ZG, CH-ZH。 |
| NUTS-1 | 国全体 | CH0 | 1 | スイス連邦全域（Schweiz / Suisse / Svizzera）。 |
| NUTS-2 | 大地域 | CH01 〜 CH07 | 7 | BFSが定義する7つの大地域（Grossregionen）：CH01 Région lémanique / Genferseeregion（VD, VS, GE）、CH02 Espace Mittelland（BE, FR, SO, NE, JU）、CH03 Nordwestschweiz（BS, BL, AG）、CH04 Zürich（ZH）、CH05 Ostschweiz（GL, SH, AR, AI, SG, GR, TG）、CH06 Zentralschweiz（LU, UR, SZ, OW, NW, ZG）、CH07 Ticino（TI）。 |
| NUTS-3 | カントン | CH011 〜 CH070 | 26 | 全26カントンに1対1で対応（例：CH011 Vaud, CH012 Valais, CH013 Genève, CH040 Zürich, CH070 Ticino）。 |
| LAU | 基礎自治体 | 4桁数値（BFS番号） | 2,110 | 基礎自治体（Politische Gemeinden）に1対1で対応し、コード値には4桁のBFS自治体番号（BFS-Gemeindenummer）がそのまま使用される。 |

### 3.3 Wikidata抽出プロパティ（P番号）

Wikidataからスイスの行政区画および空間エンティティをSPARQL等で抽出・突合する際は、以下のプロパティ（P番号）およびクラス（Q番号）を条件指定することで、BFS公式台帳およびSwisstopo空間データとの完全な1対1マッピングが実現できる。

| 対象項目・用途 | Wikidata プロパティ / エンティティID | プロパティ名称（英語 / 日本語） | 抽出・クエリ実装時の指定条件・留意事項 |
| --- | --- | --- | --- |
| BFS自治体コード | P771 | Swiss municipality code（スイス自治体コード） | 1〜4桁のBFS自治体番号（例：チューリッヒ市は "261"、ベルン市は "351"）。現行の2,110基礎自治体を抽出する際は、分類（P31）が Q70208（municipality of Switzerland / スイスの基礎自治体）かつ廃止日（P576）を持たない（FILTER NOT EXISTS { ?item wdt:P576 ?dissolved }）エンティティを指定する。 |
| ISO 3166-2 コード | P300 | ISO 3166-2 code | カントン（P31 = Q23058: canton of Switzerland）の抽出キー（CH-ZH 等）。 |
| NUTS コード | P605 | NUTS code | 大地域（NUTS-2: CH01〜CH07）およびカントン（NUTS-3: CH011〜CH070）の突合に使用。 |
| HASC コード | P8119 | HASC (Hierarchical Administrative Subdivision Codes) | 州および郡（Bezirk）レベルの国際階層コード（例：CH.ZH.AF 等）の参照用。 |
| スイス歴史事典ID | P902 | Historical Dictionary of Switzerland ID (HLS / DHS / DSS) | スイスの全カントン・郡・基礎自治体・集落にほぼ100%付与されている学術・公的権威識別子。多言語名称（独・仏・伊）の権威あるクロスチェックに極めて有効。 |
| 上位行政区画 | P131 | located in the administrative territorial entity | 基礎自治体 → 郡（存在する場合） → カントン → スイス（Q39）の階層ツリー構築に使用。合併や州移管（Moutier等）に伴い修飾子として開始日（P580）・終了日（P582）が付与されているため、最新状態ステートメント（wikibase:BestRank）を取得すること。 |
| 公式サイトURL | P856 | official website | 自治体公式Webサイト（主に .ch ドメイン）の取得。多言語自治体の場合は言語修飾子（P407）が付与されている。 |
| 人口・面積・標高 | P1082 / P2046 / P2044 | population / area / elevation above sea level | BFSのSTATPOP年次データ等が反映されている。 |
| 政庁所在地・州都 | P36 | capital | カントンの州都（Hauptort）や郡の郡庁所在地（Bezirkshauptort）エンティティの特定に使用。 |
| OpenStreetMap リレーションID | P402 | OpenStreetMap relation ID | OSM上の boundary=administrative リレーションとの双方向リンク（OSM側には wikidata=Q... タグが付与されている）。 |

## 4. 気象機関・予報区・観測網

### 4.1 国家気象機関と予報区体系

スイスの国家気象・気候業務は、連邦気象気候法（MetG, SR 429.1）に基づき連邦内務省（EDI）傘下の連邦気象気候庁（Bundesamt für Meteorologie und Klimatologie: MeteoSchweiz / Office fédéral de la météorologie et de la climatologie: MétéoSuisse / Ufficio federale di meteorologia e climatologia: MeteoSvizzera / Federal Office of Meteorology and Climatology: MeteoSwiss、公式サイト：`https://www.meteoswiss.admin.ch/`）が管轄している。また、自然災害警報の発令においては、連邦機関の共同運営体制のもとで連邦環境庁（BAFU：洪水・土砂災害・森林火災・渇水）、連邦雪・雪崩研究所（SLF：雪崩）、スイス地震学サービス（SED：地震）と連携し、連邦自然災害ポータル（`https://www.naturgefahren.ch/`）上で共通の5段階危険度スケール（Gefahrenstufen 1〜5）を運用している。

陸上気象予報区および警報区の階層構造は、急峻なアルプス山脈・ジュラ山脈・中央高原（Mittelland）・アルプス南麓という複雑な地形特性を反映し、行政区画（カントン・自治体）ではなく地形・標高帯・流域に即した159の気象警報地域（Warnregionen）および51の警報オブジェクト（Warnobjekte：湖沼・空港）として設計されている。これらの159警報地域は、気象ワークステーションNinJoの導入およびSLF雪崩警報区域（149最小単位）との境界調和化（Harmonisierung）を経て確立されたものであり、警報発表時にはさらに標高閾値（例：平地低地帯 < 800 m、霜警報対象 < 600 m）や4大気候帯に応じた異なる気象パラメータ閾値が適用される。

| 区域・システム種別 | 名称（現地語 / 英語） | 区域・地点数 | 空間定義・標高閾値・運用仕様 |
| --- | --- | --- | --- |
| 気象警報地域（面） | Warnregionen / Warning regions | 159区域 | MeteoSwissが風・雷雨・大雨・大雪・路面凍結・猛暑・霜の面的な気象警報を発表する基本ポリゴン単位（かつての14地域から138地域を経て、SLF雪崩区域との調和化により現行の159区域に細分化）。リヒテンシュタイン公国も包含。 |
| 気象警報オブジェクト（湖沼・空港） | Warnobjekte (Seen und Flugplätze) | 51対象 | 面的な159警報地域とは独立して、突風・強風警報（Starkwindwarnung: 25〜33 kt、Sturmwarnung: > 33 kt）が発令される全国の主要湖沼および飛行場オブジェクト。 |
| 雪崩警報単位（SLF） | Lawinenwarnregionen (Kleinste Einheiten) | 149区域 | 連邦雪・雪崩研究所（SLF）が雪崩ブレティンで使用する最小ポリゴン単位。MeteoSwissの159警報地域と空間境界が整合されている。上位集約階層として気候大区分（アルプス北斜面、アルプス主稜線、内アルプス、アルプス南斜面、ジュラ）が存在する。 |
| 渇水警報地域（BAFU / MeteoSwiss） | Trockenheits-Warnregionen | 38区域 | BAFUとMeteoSwissの渇水予測プラットフォーム（2025年運用開始）で使用される広域水文・土壌水分警報区域（74箇所の河川流量観測点と連携）。 |
| 気候・大雨閾値地帯区分 | Klimaregionen / Warnschwellen-Zonen | 4大気候帯＋標高階層 | 同じ危険度レベル（Stufe 2〜4）でも地域・標高により警報閾値が異なる。具体的には（1）アルプス北斜面およびアルプス、（2）アルプス南斜面（マッジャ谷・マッジョーレ湖周辺を除く）、（3）マッジョーレ湖（Verbano）およびマッジャ谷（Valle Maggia：極端な多雨地域のため最高閾値）、（4）低地帯（Niederungen < 800 m、地面霜は < 600 m の面積比率で判定）に区分される。 |
| 地点別局地予報（郵便番号・地点） | Lokalprognose / Local Forecast Data | 全国全郵便番号・主要地点 | MeteoSwissアプリおよびWebサイトで提供される1時間更新・192時間先（8日間）までの時系列予報。郵便番号（PLZ）または観測・予報ポイントID単位で配信される。 |

予報・観測データのオープンデータ提供状況に関して、MeteoSwissは連邦政府のオープンガバメントデータ（OGD）戦略に基づき、地上観測データ、レーダー降水・降雹プロダクト（CombiPrecip等）、気候シナリオ（CH2025）、郵便番号別局地予報データ、および高解像度アンサンブル数値予報モデル（**ICON-CH1-EPS**［水平解像度約 1 km］および **ICON-CH2-EPS**［水平解像度約 2 km、最大5日先まで］）をすべて無償・APIキー不要のオープンデータ（出典表記 `Source: MeteoSwiss` のみ必須）として全面公開している。データ配信基盤にはSwisstopoが運用する連邦空間データ基盤（FSDI）の **STAC（SpatioTemporal Asset Catalog）REST API**（`https://data.geo.admin.ch/api/stac/v1/collections/...`）およびスイス国立スーパーコンピューティングセンター（CSCS）の配信基盤が採用されており、技術仕様は公式ドキュメントポータル（`https://opendatadocs.meteoswiss.ch/`）に体系化されている。

### 4.2 地上気象観測網と地点リスト入手先

MeteoSwissが運用する地上気象観測網は、リアルタイム自動気象観測網「**SwissMetNet（SMN）**」を中核とし、自動降水量観測網、手動降水量・積雪観測網（NIME）、スイス国家基本気候網（NBCN）、積算雨量計観測網（TOT）、目視観測網（OBS）、花粉観測網、フェノロジー（生物季節）観測網から構成されている。

| 観測網名称（略称） | 観測種別・時間粒度 | 地点規模 | STAC コレクションID / FSDI レイヤID |
| --- | --- | --- | --- |
| SwissMetNet (SMN) | 自動総合気象観測所（気温・降水量・風向風速・湿度・気圧・日射量等を10分間隔 t で自動計測、1時間値 h・日値 d・月値 m・年値 y も提供） | 約160地点（公的API確認済） | STAC: ch.meteoschweiz.ogd-smn<br>FSDI: ch.meteoschweiz.messnetz-automatisch |
| 自動降水量観測網 (SMN-Precip) | 自動雨量計による10分間隔等の降水量計測 | 約100地点（SMNと合わせて約260自動地点） | STAC: ch.meteoschweiz.ogd-smn-precip |
| 手動降水量・積雪観測網 (NIME) | 毎日06:00 UTC（前日06:10〜当日06:00 UTC）に日降水量・積雪深を計測する手動観測網 | 約240地点（公的API確認済） | STAC: ch.meteoschweiz.ogd-nime<br>FSDI: ch.meteoschweiz.messnetz-manuell |
| スイス国家基本気候網 (NBCN) | 1864年以降の長期均質化気候データ系列（Homogene Messreihen）を提供する気候基準観測所 | 約29〜75地点（主要気候地点29箇所＋降水量系列） | STAC: ch.meteoschweiz.ogd-nbcn<br>FSDI: ch.meteoschweiz.messnetz-klima |
| 積算雨量計観測網 (TOT) | 山岳高所等に設置されたトータライザー（積算雨量計）観測網 | 約80〜100地点 | STAC: ch.meteoschweiz.ogd-tot |
| 目視気象観測網 (OBS) | 視程・現在天気・過去天気・地面状態等の定時観測（06, 12, 18 UTC等） | 約30〜50地点 | STAC: ch.meteoschweiz.ogd-obs<br>FSDI: ch.meteoschweiz.messnetz-beobachtungen |
| 自動花粉観測網 (Pollen) | 大気中の花粉濃度を1時間単位等で自動計測 | 約14〜16地点 | STAC: ch.meteoschweiz.ogd-pollen<br>FSDI: ch.meteoschweiz.messnetz-pollen |

観測地点マスター（Station Metadata）は、GISパッケージ形式またはSTAC APIのコレクションレベルAssetsから直接取得できる。GISベクトル形式（GeoJSON / Shapefile / KML）の観測所位置マスターは `https://data.geo.admin.ch/ch.meteoschweiz.messnetz-automatisch/data.zip` から直接ZIPアーカイブとしてダウンロードできるほか、`api3.geo.admin.ch` のMapServerエンドポイントからもGeoJSONとして取得可能である。また、STAC APIエンドポイント（`https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn` 等）のコレクションレベルAssets内には、観測所一覧マスターCSV（例：`ogd-smn_meta_stations.csv`、`ogd-nbcn_meta_stations.csv`）、観測パラメータ定義CSV（`..._meta_parameters.csv`）、およびデータインベントリCSVが格納されている。なお、MeteoSwissのOpen Data CSVファイルはすべて列区切り文字にセミコロン（`;`）を使用し、参照タイムスタンプはすべて **UTC** で統一されており、かつメタデータCSVの文字エンコーディングには `ISO-8859-1 (Latin-1)` が使用されているため、データベース取り込み時にはUTF-8への文字コード変換処理を実装する必要がある。

## 5. 探索・GIS環境・出典メタデータ

### 5.1 公的オープンデータの出典メタデータ一覧（data_sources.csv 登録用表）

スイス連邦政府機関（Swisstopo、BFS、MeteoSwiss、BAFU等）が提供する公的空間データは、連邦オープンガバメントデータ（OGD）原則のもと、すべて無償かつ商用利用可能なオープンライセンス（`opendata.swiss` の `terms_by`：出典表示のみ義務付け、CC BY 4.0相当）で公開されている。

| source_id | category | source_name_ja | provider_ja | license | url | attribution_required | terms_summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CH_SWISSTOPO_BND3D | 行政境界 | swissBOUNDARIES3D（スイス・リヒテンシュタイン公式行政境界モデル 2026年版） | スイス連邦測量局 (swisstopo) | OGD (terms_by / CC BY 4.0相当) | https://www.swisstopo.admin.ch/de/landschaftsmodell-swissboundaries3d | Yes (© swisstopo) | 商用・非商用問わず無償利用・改変・再配布可能。複製または再配布時に出典（© swisstopo）の明記が必須。 |
| CH_SWISSTOPO_NAMES3D | 地名・代表点 | swissNAMES3D（スイス公式地理空間名称・集落中心点データベース 2026年版） | スイス連邦測量局 (swisstopo) | OGD (terms_by / CC BY 4.0相当) | https://www.swisstopo.admin.ch/de/landschaftsmodell-swissnames3d | Yes (© swisstopo) | 商用・非商用問わず無償利用可能。2026年4月版より集落中心点（Punktobjekte）およびGeoPackage形式を提供。 |
| CH_SWISSTOPO_TLM3D | 地形・施設 | swissTLM3D（スイス3次元地形景観モデル 2026年版） | スイス連邦測量局 (swisstopo) | OGD (terms_by / CC BY 4.0相当) | https://www.swisstopo.admin.ch/de/landschaftsmodell-swisstlm3d | Yes (© swisstopo) | 道路網・鉄道・水系・建物・土地被覆を含む国家基本ベクトルデータ。出典（© swisstopo）表記で自由利用可能。 |
| CH_BFS_AGVCH | 自治体台帳 | スイス公式自治体台帳・履歴付自治体台帳 (AGVCH / eCH-0071) | スイス連邦統計局 (BFS / OFS / UST) | OGD (terms_by) | https://www.bfs.admin.ch/bfs/de/home/grundlagen/agvch.html | Yes (Quelle: BFS – Amtliches Gemeindeverzeichnis der Schweiz) | 全カントン・郡・基礎自治体の公式コード、名称、合併履歴データ。出典明記により無償利用可能。 |
| CH_BFS_GEOSTAT | 統計区・メッシュ | GEOSTAT 空間統計データ（STATPOP/STATENT 1haグリッド・ThemaKart境界） | スイス連邦統計局 (BFS / OFS / UST) | OGD (terms_by) | https://www.bfs.admin.ch/bfs/de/home/dienstleistungen/geostat.html | Yes (Quelle: BFS – GEOSTAT / STATPOP) | 国勢調査（STATPOP）等の100mメッシュ統計および都市統計街区境界。出典明記により商用利用含め無償利用可能。 |
| CH_METEOSWISS_OGD | 気象・観測・予報 | MeteoSwiss オープンデータ（SwissMetNet観測値・ICON数値予報・局地予報） | スイス連邦気象気候庁 (MeteoSwiss) | OGD (terms_by / CC BY 4.0相当) | https://www.meteoswiss.admin.ch/services-and-publications/service/open-data.html | Yes (Source: MeteoSwiss) | STAC API経由でリアルタイム観測値・過去統計・数値予報モデルを無償取得可能。出典（Source: MeteoSwiss）表記が必須。 |
| CH_FSDI_WMTS | 背景地図・オルソ | 連邦空間データ基盤 WMTS/XYZ タイルサービス（国土地図・SWISSIMAGE） | スイス連邦測量局 (swisstopo) / geo.admin.ch | OGD (terms_by) | https://wmts.geo.admin.ch/ | Yes (© swisstopo) | Webメルカトル（EPSG:3857）およびスイス座標系（EPSG:2056）の背景タイル配信。高頻度スクレイピングを除き無償利用可。 |

### 5.2 標準測地系・投影法・EPSGコード

スイスの空間データを扱う上で最も重要な技術仕様は、独自の斜軸メルカトル図法（Oblique Mercator projection：ベルン旧天文台を原点とする球面投影）に基づく国家測量座標系である。現在、スイス全土の公的測量および連邦空間データ基盤（FSDI）は、第2世代の「**CH1903+ / LV95（EPSG:2056）**」へ完全移行している。

| 区分 | 測地系・投影座標系名称 | EPSGコード | 原点・オフセット値（False Easting / Northing） | 運用ステータス・GIS変換時の技術的注意点 |
| --- | --- | --- | --- | --- |
| 現行国家標準（平面直角） | CH1903+ / LV95 (Landesvermessung 1995) | EPSG:2056 | 原点：ベルン（Bern）<br>東距 E=2,600,000 m<br>北距 N=1,200,000 m | 現在のスイス国家標準座標系。Bessel 1841楕円体を使用し、斜軸メルカトル図法（Hotine Oblique Mercator Azimuth Center）を適用。国内全域で東距（E）は必ず 2百万m 台（2'485'000〜2'834'000）、北距（N）は必ず 1百万m 台（1'075'000〜1'296'000）となるため、X/Y（E/N）の取り違えが構造的に防止されている。 |
| 旧国家標準（平面直角・レガシー） | CH1903 / LV03 (Landesvermessung 1903) | EPSG:21781 | 原点：ベルン（Bern）<br>東距 y=600,000 m<br>北距 x=200,000 m | 旧標準座標系（レガシー互換用）。LV95とは先頭の「2」および「1」の有無だけでなく、1903年当時の三角測量網の局所的な歪み（最大約 1.6 m）が含まれる。したがって、地籍精度（±0.5 m 以内）を要する変換では単純なオフセット加算（+2,000,000 m / +1,000,000 m）を行ってはならず、Swisstopo公式の三角網補正グリッド FINELTRA（NTv2形式：CHENyx06a.gsb）をPROJ / GDAL等で適用する必要がある。また、旧LV03では慣習的に東距を y、北距を x と呼称していた点に注意。 |
| 現行国家標準（地理経緯度） | CH1903+ (Geographic 2D) | EPSG:4150 | — | CH1903+ の地理座標系（旧CH1903地理座標系は EPSG:4149）。 |
| グローバル標準 / Web地図 | ETRS89 / WGS84 / Web Mercator | EPSG:4258 / EPSG:4326 / EPSG:3857 | — | SwisstopoのSTAC APIやWMTSタイルサービスは、国際標準の EPSG:4326 およびWebメルカトル EPSG:3857 にも対応している。 |
| 国家標準標高系（鉛直座標系） | LN02 (Landesnivellement 1902) / LHN95 | EPSG:5728 (LN02 height) | 基準点：マルセイユ験潮儀（レマン湖ピエール・デュ・ニトン岩礁 Repère Pierre du Niton 標高 373.60 m） | swissBOUNDARIES3D 等の配布ファイル名（例：swissboundaries3d_2026-01_2056_5728.gpkg.zip）末尾の 5728 は、水平座標系 EPSG:2056 と鉛直標高系 EPSG:5728（LN02）の組み合わせを示している。 |

### 5.3 公式背景地図タイルとストリートビュー・パノラマカバレッジ状況

Swisstopoが運用する `wmts.geo.admin.ch` は、スイス国土地図（Landeskarten 1:10,000〜1:1,000,000）および高解像度オルソ航空写真（SWISSIMAGE）を、認証不要の標準XYZ / WMTSタイルとして配信している。利用にあたっては出典表記（`© swisstopo`）のみが義務付けられており、Webメルカトル（`EPSG:3857`）およびスイス国家標準座標系（`EPSG:2056`）、旧座標系（`EPSG:21781`）の各タイルマトリクスが提供されている。

| レイヤ種別 | レイヤID | XYZ / WMTS タイルURLテンプレート（Web Mercator EPSG:3857 形式等） |
| --- | --- | --- |
| 公式背景地図（カラー国土地図） | ch.swisstopo.pixelkarte-farbe | https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg |
| 公式背景地図（グレースケール版） | ch.swisstopo.pixelkarte-grau | https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-grau/default/current/3857/{z}/{x}/{y}.jpeg |
| 公式オルソ航空写真（SWISSIMAGE） | ch.swisstopo.swissimage | https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage/default/current/3857/{z}/{x}/{y}.jpeg |
| 国家標準座標系（EPSG:2056）WMTS | 各レイヤ共通 | https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/2056/{TileMatrix}/{TileCol}/{TileRow}.jpeg |
| WMTS Capabilities XML | メタデータ定義 | https://wmts.geo.admin.ch/EPSG/3857/1.0.0/WMTSCapabilities.xml?lang=de |

地上街路パノラマ画像（ストリートビュー等）の提供および利用に関しては、2012年3月31日のスイス連邦最高裁判所判決（BGE 138 II 346：Google Street View 事件）という極めて重要な法的規範が存在する。連邦データ保護・情報公開監察官（EDÖB）とGoogleの間で争われた同訴訟において、連邦最高裁は顔および車両ナンバープレートの自動匿名化（ボカシ処理）における許容エラー率上限を1%と定めたほか、学校、病院、老人ホーム、女性シェルター、刑務所、裁判所といった「センシティブ施設（sensible Einrichtungen）」周辺での完全匿名化、生垣や塀越しに私邸敷地内を撮影しないためのカメラ高引き下げ、および住民・施設からの無償オプトアウト（建物ボカシ申請）への対応を法的義務として確定させた。この判例は現在もスイス国内で街路3Dパノラマサービスを展開するすべての民間・公的事業者の法的基準として機能している。

| サービス・データ種別 | カバレッジ状況 | スイス固有の品質特性・ボカシ（Blurring）状況・技術的特徴 |
| --- | --- | --- |
| Google ストリートビュー | 高カバレッジ（全国主要道路網・都市・山岳峠道・一部鉄道線） | 2009年8月にサービス開始。上記最高裁判決（BGE 138 II 346）を受け一時更新が停滞したが、カメラ高を引き下げた撮影車両で全国を再撮影し、現在は高速道路・主要幹線・山岳峠・都市街路を高密度にカバーしている。ただし個人住宅や店舗・ホテルの一部、および学校・病院周辺で建物単位のボカシ（モザイク）が存在する。またレーティッシュ鉄道（ベルニナ線・アルブラ線）等の軌道上パノラマも収録。 |
| Apple Look Around | 高カバレッジ（全国全域の主要道路・都市網） | チューリッヒ、ジュネーヴ、バーゼル、ベルン、ローザンヌ等の大都市圏だけでなく、スイス全土の主要道路網で高解像度3Dパノラマが公開されている。Googleよりも後発で撮影されたため、画質・フレームレートが極めて高く、建物の全面ボカシも比較的少ない。 |
| Mapillary / KartaView | 中〜高カバレッジ（高速道路・主要都市・自転車道・登山道） | 欧州のOSMコミュニティ（特にチューリッヒ、バーゼル、ベルン、ジュネーヴ周辺）の活動が活発であり、主要国道・自転車レーン（Velolandルート）・山岳トレイルにおいて車載・自転車載カメラによるオープン画像が豊富に蓄積されている。 |
| Yandex Panoramas / 百度全景 | 該当なし（カバレッジほぼ皆無） | 商用道路網カバレッジは存在しない（観光地の一部にユーザー投稿の単発フォトスフィアが点在するのみ）。 |
| 公式オルソ画像（SWISSIMAGE 10 cm）および自治体3D画像 | 全国100%完全網羅（超高解像度） | Swisstopoが提供する公式デジタルオルソ画像 SWISSIMAGE 10 cm は、平地・主要谷底で地上画素寸法（GSD）10 cm、アルプス山岳域で 25 cm という世界最高水準の解像度でスイス全土を3年周期で更新している（無償OGD公開）。さらにバーゼル＝シュタット州（BS）やバーゼル＝ラントシャフト州（BL）、チューリッヒ市等のジオポータルでは、独自の3D都市画像サービスやモバイルマッピング街路画像が整備されている。 |

## 6. 一次情報源・公式オープンデータ入手先リンク集

| カテゴリ | リソース・システム名称 | 公式URL | 提供形式・用途 |
| --- | --- | --- | --- |
| 行政境界（GIS） | Swisstopo swissBOUNDARIES3D 製品・ダウンロードページ | https://www.swisstopo.admin.ch/de/landschaftsmodell-swissboundaries3d | GeoPackage (.gpkg), Shapefile (.shp), File Geodatabase (.gdb), INTERLIS 2 (.xtf)（毎年1月更新＋期中合併特別更新） |
| 地名・代表点（GIS） | Swisstopo swissNAMES3D 製品・ダウンロードページ | https://www.swisstopo.admin.ch/de/landschaftsmodell-swissnames3d | GeoPackage, Shapefile, CSV（全地名ポリゴン・集落中心点座標） |
| 自治体コード台帳 | BFS スイス公式自治体台帳（Amtliches Gemeindeverzeichnis: AGVCH） | https://www.bfs.admin.ch/bfs/de/home/grundlagen/agvch.html | 公式自治体リスト、カントン・郡・自治体コード体系解説 |
| 自治体台帳API / XML | BFS 自治体台帳Web検索アプリ・履歴データ配布（AGVCH App） | https://www.agvchapp.bfs.admin.ch/ | 2026年1月1日基準スナップショット検索、eCH-0071準拠 XML / CSV / REST Webサービス |
| 電子政府データ標準 | eCH-0071 データ標準「スイス履歴付自治体台帳 V1.2.0」 | https://www.ech.ch/de/standard-uebersicht | スイスの行政区画データベース設計における公式スキーマ仕様書（PDF / XSD） |
| 国勢調査・小地域統計 | BFS GEOSTAT（空間統計データ・1haグリッド・ThemaKart境界） | https://www.bfs.admin.ch/bfs/de/home/dienstleistungen/geostat.html | STATPOP / STATENT 100mメッシュ、都市統計街区（Quartiere）境界データ |
| 気象オープンデータ総合 | MeteoSwiss Open Data ポータル | https://www.meteoswiss.admin.ch/services-and-publications/service/open-data.html | 地上観測・レーダー・気候・数値予報（ICON-CH1/2-EPS）のオープンデータ案内 |
| 気象データ技術仕様書 | MeteoSwiss Open Data Technical Documentation | https://opendatadocs.meteoswiss.ch/ | STAC API利用手順、CSV構造、時間粒度（t, h, d, m, y）、GRIB2デコード仕様 |
| 気象観測網 STAC API | SwissMetNet 自動気象観測網 STAC Collection エンドポイント | https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn | 約160地点のステーションマスターCSVおよび10分値・時別・日別観測データの自動取得 |
| 局地気象予報 STAC API | Local Forecast Data STAC Collection エンドポイント | https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-local-forecasting | 郵便番号・地点別の時系列気象予報データ取得 |
| 雪崩警報区域定義 | SLF 雪崩ブレティン区域分割（Gebietseinteilung） | https://www.slf.ch/de/lawinenbulletin-und-schneesituation/wissen-zum-lawinenbulletin/gebietseinteilung/ | 149の雪崩警報最小単位および気候・地理領域階層の仕様 |
| 連邦空間データ基盤 | Swisstopo / BGDI 連邦ジオポータル・データカタログ | https://data.geo.admin.ch/ | 連邦全機関のGISレイヤ閲覧、STACブラウザ、直接データダウンロード |
| 連邦GIS開発者ドキュメント | GeoAdmin API / WMTS / XYZ タイル仕様書 | https://docs.geo.admin.ch/visualize-data/xyz.html | WMTS/XYZ背景地図タイル、検索API、座標変換APIの技術ドキュメント |
| 国家オープンデータ総合 | opendata.swiss（スイス連邦・州・自治体統合OGDポータル） | https://opendata.swiss/ | 連邦・カントン・基礎自治体の全オープンデータ横断検索・CKAN API |
