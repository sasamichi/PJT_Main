# オーストリア 交通網・インフラ制度 事前調査シート

- 調査日: 2026-10-25
- 根拠法令・公式資料: 1971年連邦道路法（Bundesstraßengesetz 1971 – BStG 1971, BGBl. Nr. 286/1971）、1997年ASFINAG授権法（ASFINAG-Ermächtigungsgesetz 1997, BGBl. I Nr. 113/1997）、各連邦州道路法（Landesstraßengesetze）、1957年鉄道法（Eisenbahngesetz 1957 – EisbG, BGBl. Nr. 60/1957）、2003年索道法（Seilbahngesetz 2003 – SeilbG 2003）、1999年自動車路線法（Kraftfahrliniengesetz – KflG, BGBl. I Nr. 203/1999）、1999年公共近距離・地域旅客交通法（Öffentliches Personennah- und Regionalverkehrsgesetz 1999 – ÖPNRV-G 1999）、1996年不定期旅客運送法（Gelegenheitsverkehrs-Gesetz 1996 – GelverkG, BGBl. Nr. 112/1996）、1997年水運法（Schifffahrtsgesetz – SchFG, BGBl. I Nr. 62/1997）、2019年・2023年水路交通規則（Wasserstraßen-Verkehrsordnung – WVO, BGBl. II Nr. 31/2019・BGBl. II Nr. 204/2023）、1957年航空法（Luftfahrtgesetz – LFG）、気候保護・環境・エネルギー・モビリティ・イノベーション・技術連邦省（BMK / BMIMI）公的資料、ÖBB-Infrastruktur AG 鉄道網利用条件（Schienennetz-Nutzungsbedingungen – SNNB 2026/2027）、オーストリア標準交通参照システム（GIP.at）仕様書

---

## 1. 道路網制度の詳細分類

### 1.1 道路法体系と詳細種別一覧

| 大分類 | 中分類・法的名称（公用語） | 日本語相当 | 根拠法律 | 管理主体 | 全体規模目安 | 初期自動収集(〇/×) |
| --- | --- | --- | --- | --- | --- | --- |
| 連邦道路（Bundesstraßen） | Bundesautobahnen（Bundesstraßen A） | 連邦アウトバーン（高速自動車国道相当） | 1971年連邦道路法 別表1（BStG 1971 Verzeichnis 1） | ASFINAG（連邦所有・用益権契約に基づく管理運営） | 約1,756 km（A・S道路網合計2,278 km） | 〇 |
| 連邦道路（Bundesstraßen） | Bundesschnellstraßen（Bundesstraßen S） | 連邦自動車専用道路（高規格幹線道路相当） | 1971年連邦道路法 別表2（BStG 1971 Verzeichnis 2） | ASFINAG（連邦所有・用益権契約に基づく管理運営） | 約522 km（一部アウトバーン断面区間を含む） | 〇 |
| 州道（Landesstraßen） | Landesstraßen B（Vorrangstraßen） | 主要州道B（一般国道・主要幹線地方道相当） | 各連邦州道路法（Landesstraßengesetze） | 各連邦州政府（Amt der Landesregierung） | 約10,000 km | 〇 |
| 州道（Landesstraßen） | Landesstraßen L（Landesstraßen 1. und 2. Ordnung / Bezirksstraßen） | 一般州道L（都道府県道・二次地方道相当） | 各連邦州道路法（Landesstraßengesetze） | 各連邦州政府（Amt der Landesregierung） | 約24,000 km | 〇 |
| 市町村道（Gemeindestraßen） | Gemeindestraßen | 市町村道・都市内一般街路 | 各連邦州道路法・自治体条例 | 各基礎自治体（Gemeinden / Magistrat） | 約90,000 km | × |
| その他道路（Sonstige Straßen） | Güterwege, Forststraßen, Privatstraßen | 農道・林道・私道・特別有料山岳道路等 | 1975年森林法・各州農業道路法・私法 | 森林所有者・農業組合・特別道路会社等 | 約100,000 km以上 | × |

### 1.2 付番ルール・管理者・OSMタグ対照表

- **主要幹線道路（高速道路・国道・主要州道/地方道）の路線番号付番規則と例外ルール**: 連邦アウトバーン（Bundesautobahnen）はプレフィックス`A`に1〜2桁の数字を組み合わせた路線番号（データ上の表記は空白なしの`A1`または法規上の空白入り表記`A 1`）で識別され、ウィーンから放射状に延びる基幹路線やアルプス縦貫幹線には1桁〜10番台（`A1` West Autobahn、`A2` Süd Autobahn、`A9` Pyhrn Autobahn、`A10` Tauern Autobahn、`A12` Inntal Autobahn、`A13` Brenner Autobahn、`A14` Rheintal/Walgau Autobahn等）、大都市圏の環状線や都市内接続支線には20番台（ウィーン圏の`A21` Wiener Außenring Autobahn、`A22` Donauufer Autobahn、`A23` Autobahn Südosttangente Wien、リンツ・ヴェルス圏の`A25` Welser Autobahn、`A26` Linzer Autobahn）が付番されるほか、欧州自動車道路番号（`E45`、`E55`、`E60`等）が重複指定される。連邦自動車専用道路（Bundesschnellstraßen）はプレフィックス`S`に1〜2桁の数字（`S1` Wiener Außenring Schnellstraße、`S6` Semmering Schnellstraße等）を冠し、A道路網を補完する高規格幹線網を形成する。一方、各連邦州が管理する主要州道（Landesstraßen B）はプレフィックス`B`＋1〜3桁の数字で全国連番体系を維持しているが、最西端のフォアアールベルク州（Vorarlberg）のみが例外的な法制を採っており、`B`プレフィックスを一切使用せず主要幹線州道もすべてプレフィックス`L`（例：`L190` Vorarlberger Straße）に統一している。また、一般州道（`Landesstraßen L`）は9つの各連邦州ごとに独立して1番から付番されるため、異なる州に同一の`L`番号が重複して存在する構造となっており、GISデータベースのテーブル設計においては路線番号（`ref`）単独ではなく連邦州コード（ISO 3166-2:ATまたはGKZ）との複合主キー設計が不可欠となる。
- **OSMにおける道路タグ（highway=motorway, trunk, primary, secondary等）との対照関係**: OpenStreetMap（OSM）のオーストリア国内マッピング規約では、道路の法的分類（`A`・`S`・`B`・`L`）と物理的な道路断面規格（Ausbauzustand）の双方がタグ付けに反映される。`highway=motorway`は連邦アウトバーン全線（`ref=A1`〜`A26`）に加え、連邦自動車専用道路（`S`道路）のうち「アウトバーン断面（Autobahnquerschnitt：中央分離帯による往復分離および片側2車線以上）」で整備された区間（`S1`、`S2`、`S6`全線、`S5`や`S33`の大部分等、`motorroad=yes`併記）に適用される。これに対し、単断面2車線または2+1車線構造の立体交差方式で整備された`S`道路区間（`S3`、`S4`、`S7`等の非アウトバーン断面区間、`motorroad=yes`）および都市圏の一部立体交差化B道路には`highway=trunk`が割り当てられる。さらに、主要州道B（`Landesstraßen B`、フォアアールベルク州では主要幹線たる`L`道路）は`highway=primary`、地域間連絡を担う上位の一般州道L（`Landesstraßen 1. Ordnung`）は`highway=secondary`、基礎自治体間を結ぶ下位の一般州道L（`Landesstraßen 2. Ordnung` / `Bezirksstraßen`）および主要市町村道は`highway=tertiary`にそれぞれ対照される。
- **国直轄区間と地方自治体・公社管理区間の管理分担**: オーストリアの道路インフラ管理は、1971年連邦道路法第34b条（BStG 1971 § 34b）および1997年ASFINAG授権法第2条（ASFINAG-Ermächtigungsgesetz 1997 § 2）に基づく連邦政府との用益権契約（Fruchtgenussvertrag）により、連邦アウトバーン（`A`道路）および連邦自動車専用道路（`S`道路）の全線（総延長2,278 km、うち課金対象営業網2,249 km、橋梁5,917箇所、トンネル171箇所）について、連邦100%出資の特殊株式会社であるASFINAG（Autobahnen- und Schnellstraßen-Finanzierungs-Aktiengesellschaft）が計画・建設・維持管理・通行料金徴収を一元的に遂行し、連邦道路管理者（Bundesstraßenverwaltung）としてのすべての法的権利と義務を行使する体制となっている。一方、主要州道B（`Landesstraßen B`）および一般州道L（`Landesstraßen L`）は各連邦州の所有・直轄管理下に置かれ、9つの連邦州政府（Amt der jeweiligen Landesregierung）の道路建設・管理部局が維持管理を行い、市町村道（`Gemeindestraßen`）は各基礎自治体（Gemeinden）が固有の自治権の範囲内で管理する二層・三層の垂直分担構造が確立されている。

---

## 2. 鉄軌道・索道制度の詳細分類

### 2.1 鉄軌道・都市交通・索道の法体系一覧

| 大分類 | 根拠法律・条文 | 法的種別（公用語） | 日本語・技術分類 | 主な運行都市・対象路線例 | 初期収集(〇/×) |
| --- | --- | --- | --- | --- | --- |
| 公共鉄道（幹線） | 1957年鉄道法 第2条・第4条第1項（EisbG § 2, § 4 Abs. 1） | Öffentliche Eisenbahnen: Hauptbahnen | 主幹線鉄道（国際幹線・都市間長距離線・主要S-Bahn幹線） | ÖBB-Infrastruktur AG 基幹網（Westbahn, Südbahn, Koralmbahn, Tauernbahn, Brennerbahn, Arlbergbahn等） | 〇 |
| 公共鉄道（支線・地域鉄道） | 1957年鉄道法 第2条・第4条第2項（EisbG § 2, § 4 Abs. 2） | Öffentliche Eisenbahnen: Nebenbahnen（vernetzte / nicht vernetzte） | 地方鉄道・支線鉄道（全国網直通支線、独立狭軌鉄道、登山アプト式鉄道） | ÖBB支線網、Raaberbahn、GKB、StLB、NÖVOG（Mariazellerbahn, Schneebergbahn）、Salzburg AG（Pinzgauer Lokalbahn, Schafbergbahn）、Zillertalbahn等 | 〇 |
| 都市鉄道・軌道・無軌条電車 | 1957年鉄道法 第5条（EisbG § 5） | Straßenbahnen（U-Bahnen, Straßenbahnen, Oberleitungsomnibusse） | 地下鉄（U-Bahn）・路面電車（Straßenbahn / Tram）・トロリーバス（Obus） | ウィーン（U-Bahn U1〜U6, Tram）、グラーツ（Tram）、リンツ（Tram, Pöstlingbergbahn, Obus）、インスブルック（Tram, Stubaitalbahn）、ザルツブルク（Obus）、グムンデン（Traunseetram） | 〇 |
| 公共索道（普通索道・鋼索鉄道） | 2003年索道法 第1条〜第3条（SeilbG 2003 §§ 1–3） | Öffentliche Seilbahnen（Standseilbahnen, Pendelbahnen, Kabinen-Umlaufbahnen / EUB / ZUB / 3S） | ケーブルカー（鋼索鉄道）・交走式ロープウェイ・普通ゴンドラリフト（都市交通・通年旅客用） | インスブルック（Hungerburgbahn, Nordkettenbahnen）、ザルツブルク（FestungsBahn）、グラーツ（Schlossbergbahn）、主要通年ゴンドラ（8-EUB Acherkogelbahn等） | 〇 |
| 非公共鉄道・特殊索道 | 1957年鉄道法 第3条・第7条・第8条（EisbG §§ 3, 7, 8）／2003年索道法 第2条（SeilbG 2003 § 2） | Nicht-öffentliche Eisenbahnen（Anschlussbahnen, Materialbahnen）, Sesselbahnen, Schlepplifte, Materialseilbahnen | 専用引込線・工事鉱山用軌道・冬季スキー場内チェアリフト・Tバーリフト・貨物索道 | 工場専用線（Anschlussbahnverzeichnis登録線）、スキー場内リフト設備等 | × |

### 2.2 主要鉄道事業者・索道リスト（operators.csv 登録用）

- **国鉄・インフラ保有公社・主要民間鉄道事業者・都市交通局の一覧**: 1957年鉄道法（EisbG 第1a条〜第1d条）に基づき、オーストリアの鉄道事業者はインフラ保有・管理を担う鉄道インフラ企業（Eisenbahninfrastrukturunternehmen – EIU）、列車運行を担う鉄道運送企業（Eisenbahnverkehrsunternehmen – EVU）、および双方を兼営する統合鉄道企業（Integrierte Eisenbahnunternehmen）に厳密に法区分されている。特にトロリーバス（Oberleitungsomnibusbetriebe）は道路交通法ではなく1957年鉄道法第5条（EisbG § 5）の「路面電車（Straßenbahnen）」に含まれる公共鉄道として法制化されている点がデータベース設計上の重要な特徴である。

| 事業者名（公用語） | 略称 | 事業種別・役割（EIU:インフラ保有 / EVU:列車運行） | 主な管轄地域・運行路線 | 公式サイトURL |
| --- | --- | --- | --- | --- |
| ÖBB-Infrastruktur AG | ÖBB-INFRA | 国鉄インフラ保有・管理公社（EIU） | 全国主幹線（Hauptbahnen）および主要支線網 | https://infrastruktur.oebb.at/ |
| ÖBB-Personenverkehr AG | ÖBB-PV | 国鉄旅客鉄道運行会社（EVU） | 全国長距離（Railjet, Nightjet, EuroCity）・地域鉄道（S-Bahn, REX） | https://www.oebb.at/ |
| WESTbahn Management GmbH | WESTbahn | 民間長距離鉄道運行会社（EVU） | ウィーン〜ザルツブルク〜インスブルック〜ブレゲンツ／フィラッハ等 | https://westbahn.at/ |
| City Air Terminal Betriebsgesellschaft m.b.H. | CAT | 空港アクセス鉄道運行会社（EVU） | Wien Mitte – Flughafen Wien（空港特急） | https://www.cityairporttrain.com/ |
| Wiener Linien GmbH & Co KG | WL | 都市交通局（EIU/EVU） | ウィーン市（地下鉄U1〜U6、路面電車、都市バス） | https://www.wienerlinien.at/ |
| Wiener Lokalbahnen GmbH | WLB | 地域鉄道・都市間軌道事業者（EIU/EVU） | Badner Bahn（Wien Oper – Baden Josefsplatz） | https://www.wlb.at/ |
| Niederösterreichische Verkehrsorganisationsges.m.b.H. | NÖVOG | 州営地域鉄道・索道公社（EIU/EVU） | Mariazellerbahn, Citybahn Waidhofen, Schneebergbahn, Rax-Seilbahn等 | https://www.noevog.at/ |
| Raab-Oedenburg-Ebenfurter Eisenbahn AG | Raaberbahn | 国際地域鉄道インフラ・運行会社（EIU/EVU） | ブルゲンラント州・ハンガリー国境路線（Neufeld a.d. Leitha – Baumgarten等） | https://www.raaberbahn.at/ |
| Neusiedler Seebahn GmbH | NSB | 地域鉄道インフラ保有会社（EIU） | Neusiedl am See – Pamhagen（ハンガリー国境） | https://www.neusiedlerseebahn.at/ |
| Graz-Köflacher Bahn und Busbetrieb GmbH | GKB | 連邦所有地域鉄道・バス事業者（EIU/EVU） | シュタイアーマルク州西部（S-Bahn S6, S61, S7） | https://www.gkb.at/ |
| Steiermarkbahn und Bus GmbH (Steiermärkische Landesbahnen) | StLB | 州営地域鉄道・バス事業者（EIU/EVU） | Murtalbahn, Gleichenberger Bahn, Weizer Bahn, Übelbacher Bahn | https://www.steiermarkbahn.at/ |
| Holding Graz – Kommunale Dienstleistungen GmbH | Graz Linien | 都市交通局（EIU/EVU） | グラーツ市（路面電車、Schlossbergbahn、都市バス） | https://www.holding-graz.at/ |
| Linz Linien GmbH (LINZ AG LINIEN) | LINZ AG | 都市交通局（EIU/EVU） | リンツ市（路面電車、Pöstlingbergbahn、トロリーバス、都市バス） | https://www.linzag.at/ |
| Stern & Hafferl Verkehrsgesellschaft m.b.H. | StH | 民間地域鉄道・トラム事業者（EIU/EVU） | Linzer Lokalbahn (LILO), Traunseetram, Vorchdorferbahn, Atterseebahn | https://www.stern-verkehr.at/ |
| Salzburg AG für Energie, Verkehr und Telekommunikation | Salzburg AG | 地域鉄道・軌道・索道事業者（EIU/EVU） | Salzburger Lokalbahn, Pinzgauer Lokalbahn, Schafbergbahn, FestungsBahn, Obus | https://www.salzburg-ag.at/ |
| Innsbrucker Verkehrsbetriebe und Stubaitalbahn GmbH | IVB | 都市交通・地域軌道事業者（EIU/EVU） | インスブルック市（路面電車、Stubaitalbahn、Hungerburgbahn、都市バス） | https://www.ivb.at/ |
| Zillertaler Verkehrsbetriebe AG | ZVB | 民間地域鉄道・バス事業者（EIU/EVU） | Zillertalbahn（Jenbach – Mayrhofen） | https://www.zillertalbahn.at/ |
| Achenseebahn Infrastruktur- und Betriebs-GmbH | ASB | 登山アプト式鉄道事業者（EIU/EVU） | Achenseebahn（Jenbach – Seespitz） | https://www.achenseebahn.at/ |
| Montafonerbahn AG | mbs | 地域鉄道・バス事業者（EIU/EVU） | フォアアールベルク州（Bludenz – Schruns） | https://www.montafonerbahn.at/ |

- **索道（旅客用普通索道：ケーブルカー、交走式ロープウェイ、ゴンドラリフト）の公的事業者リスト入手先URL**: 2003年索道法（Seilbahngesetz 2003）に基づき、鋼索鉄道（Standseilbahnen）、交走式普通索道（Pendelbahnen）、および自動循環式ゴンドラリフト（Einseil-Umlaufbahnen mit kuppelbaren Seilklemmen / 8-EUB等）は連邦省（BMK / BMIMI）内の最高索道当局（Oberste Seilbahnbehörde / Abteilung IV/E6）が管轄しており、公式統計・技術台帳は同省ポータル（ https://www.bmk.gv.at/themen/verkehr/seilbahn.html および https://www.bmimi.gv.at/themen/verkehr/seilbahn.html ）ならびにオーストリア連邦経済会議所・索道専門部会（WKO Fachverband der Seilbahnen： https://www.wko.at/oe/transport-verkehr/seilbahnen/start ）から入手できる。

### 2.3 鉄軌道のWikidata抽出条件

- **鉄軌道路線（P31=Q34486等）、駅（P31=Q55488等）の抽出クエリ条件**: Wikidataからオーストリア（国プロパティ `wdt:P17 wd:Q40`）の現役鉄軌道路線を抽出する際は、分類プロパティ `wdt:P31/wdt:P279*` に対して鉄道路線（`wd:Q728937`）、鉄道施設・路線（`wd:Q34486`）、地下鉄路線（`wd:Q15079663`）、路面電車路線（`wd:Q1144661`）、鋼索鉄道（`wd:Q142031`）、および普通索道（`wd:Q13406463`）を指定し、廃止日（`wdt:P576`）や公式閉鎖日（`wdt:P3999`）が存在するレコードおよび利用状態（`wdt:P5817`）が廃止（`wd:Q11639308`）となっているレコードを `FILTER NOT EXISTS` で除外する。同様に、現役の鉄道駅・地下鉄駅・電停を抽出する際は、`wdt:P17 wd:Q40` かつ `wdt:P31/wdt:P279*` が鉄道駅（`wd:Q55488`）、鉄道停留場（`wd:Q55678`）、地下鉄駅（`wd:Q928830`）、路面電車停留場（`wd:Q2175765`）、または索道駅（`wd:Q55485`）であるものを対象とし、廃駅クラス（`wd:Q65464941`）および `wdt:P576`・`wdt:P3999` を持つエンティティを除外したうえで、地理座標（`wdt:P625`）、UIC駅コード（`wdt:P722`：オーストリアは`81`から始まる7桁コード）、駅略称・IBNR（`wdt:P954`）、所属路線（`wdt:P81`）、隣接駅（`wdt:P197`）を取得する設計とする。

---

## 3. バス事業制度の詳細分類

### 3.1 自動車運送事業法に基づく法的区分一覧

| 法的分類 | 運行態様・種別（公用語/日本語） | 概要・対象範囲 | プロジェクトでの位置づけ(初期収集/探索時/対象外) |
| --- | --- | --- | --- |
| 定期路線バス（公益・運輸連合委託） | Kraftfahrlinienverkehr（Gemeinwirtschaftlicher Betrieb / Bestellverkehr） / 定期路線バス（都市・地域路線バス） | 1999年自動車路線法（KflG §§ 1, 7）および1999年公共近距離・地域旅客交通法（ÖPNRV-G 1999）に基づき、7大運輸連合や自治体が公共サービス義務（PSO）契約として発注・統合管理する都市バス（Stadtbus）・地域幹線バス（Regionalbus / Postbus等） | 初期収集 |
| 定期路線バス（独立採算・長距離・国際） | Kraftfahrlinienverkehr（Eigenwirtschaftlicher Betrieb / Fernbusverkehr） / 都市間高速バス・空港連絡バス・国際定期バス | 1999年自動車路線法（KflG §§ 1, 7）およびEU規則1073/2009号に基づき、事業者が独立採算認可（Konzession / Genehmigung）で運行する都市間高速バス（FlixBus等）および空港シャトル（Vienna Airport Lines等） | 初期収集 |
| デマンド型公共交通 | Bedarfsorientierter Verkehr / Mikro-ÖV（Anrufsammeltaxi - AST, Rufbus） / デマンドバス・乗合タクシー | KflGまたはGelverkGに基づき、運輸連合の補完地域交通（VOR Flex, Postbus Shuttle, VVT Regiobusオンデマンド等）として運行される予約制・定時定路線外交通 | 探索時 |
| 不定期旅客運送事業 | Gelegenheitsverkehr（Ausflugswagen-Gewerbe, Mietwagen-Gewerbe mit Omnibussen, Gästewagen-Gewerbe） / 貸切観光バス・チャーターバス・特定送迎バス | 1996年不定期旅客運送法（GelverkG § 3 Abs. 1）に基づく非路線型の観光遊覧バス・貸切バス・宿泊施設送迎車等 | 対象外 |

### 3.2 運輸連合・主要バス事業者（operators.csv 登録用）

- **地域・州ごとの運輸連合（Verkehrsverbund等）や全国バス運営網の構造**: オーストリアでは1999年公共近距離・地域旅客交通法（ÖPNRV-G 1999）に基づき、全9連邦州のすべての基礎自治体を漏れなくカバーする7つの地域運輸連合（Verkehrsverbünde）が各州の純粋な公的組織会社（Landesgesellschaften）として法的に設置されている。東部3州（ウィーン・ニーダーエスターライヒ・ブルゲンラント）を単一で統合する国内最大の「Verkehrsverbund Ost-Region（VOR）」は最適経路距離に応じて運賃を算出する経路距離制（Streckenmodell）を採用し、シュタイアーマルク州（VST / Verbund Linie）は平均約10 km四方のゾーン制（Zonenmodell）、他の5つの運輸連合（OÖVV、SVV、VVT、VVV、VVK/VKG）は平均約6 kmのハニカムゾーン制（Wabenmodell）を採用しており、いずれのモデルでも並行路線間で鉄道・バス・トラムの自由な選択乗車が保証されている。さらにこれら7つの運輸連合は全国統括組織「Mobilitätsverbünde Österreich」（旧称IGV）を結成し、路線網計画の広域調整、全国共通定期券（KlimaTicket）の運用、および全国統合交通データの標準化を一元的に推進している。

| 運輸連合名（公用語・法人名） | 略称・ブランド名 | 管轄連邦州 | 運賃モデル | 公式サイトURL |
| --- | --- | --- | --- | --- |
| Verkehrsverbund Ost-Region (VOR) GmbH | VOR | ウィーン州、ニーダーエスターライヒ州、ブルゲンラント州 | Streckenmodell（経路距離制） | https://www.vor.at/ |
| Oberösterreichische Verkehrsverbund-Organisation GmbH Nfg. & Co. KG | OÖVV | オーバーエスターライヒ州 | Wabenmodell（ハニカムゾーン制） | https://www.ooevv.at/ |
| Salzburger Verkehrsverbund GmbH | SVV (Salzburg Verkehr) | ザルツブルク州 | Wabenmodell（ハニカムゾーン制） | https://www.salzburg-verkehr.at/ |
| Steirische Verkehrsverbund GmbH | VST / STVV (Verbund Linie) | シュタイアーマルク州 | Zonenmodell（ゾーン制） | https://www.verbundlinie.at/ |
| Verkehrsverbund Kärnten GmbH | VKG / VVK (Kärntner Linien) | ケルンテン州 | Wabenmodell（ハニカムゾーン制） | https://www.kaerntner-linien.at/ |
| Verkehrsverbund Tirol GmbH | VVT | チロル州 | Wabenmodell（ハニカムゾーン制） | https://www.vvt.at/ |
| Verkehrsverbund Vorarlberg GmbH | VVV (VMOBIL) | フォアアールベルク州 | Wabenmodell（ハニカムゾーン制） | https://www.vmobil.at/ |

- **主要高速バス・都市間バス事業者名・公式サイトURL**: 運輸連合から路線運行を受託する地域バス事業者および独立採算で都市間・空港連絡路線を運行する主要事業者は以下のとおりである。

| 事業者名（公用語） | 事業種別・役割 | 主な運行範囲・路線網 | 公式サイトURL |
| --- | --- | --- | --- |
| Österreichische Postbus AG | 国鉄（ÖBB）傘下・国内最大路線バス事業者 | 全9連邦州の地域幹線バス網（Regionalbus）およびウィーン国際空港直行バス（Vienna Airport Lines） | https://www.postbus.at/ |
| Dr. Richard Verkehrsbetrieb GmbH & Co KG | 国内最大の民間路線バスグループ | ウィーン市内路線受託、VOR地域路線、シュタイアーマルク・ザルツブルク・チロル等の地域バス | https://www.richard.at/ |
| Blaguss Reisen GmbH | 民間地域路線・国際都市間バス事業者 | 東部地域（VOR圏・ブルゲンラント州）路線バスおよび中東欧方面の都市間バス | https://www.blaguss.com/ |
| Sabtours Touristik GmbH | 民間地域路線バス事業者 | オーバーエスターライヒ州（OÖVV）・ニーダーエスターライヒ州の地域路線バス | https://www.sabtours.at/ |
| Flix SE (FlixBus Österreich) | 民間都市間高速バス（Fernbus）事業者 | ウィーン・グラーツ・リンツ・ザルツブルク・インスブルック・ブレゲンツ等を結ぶ都市間・国際高速バス | https://www.flixbus.at/ |

- **GTFSオープンデータの整備状況および公式リポジトリURL**: オーストリアは欧州でも最も公共交通オープンデータの統合が進んだ国の一つであり、7大運輸連合の統括組織である「Mobilitätsverbünde Österreich」が公式データポータル（ https://data.mobilitaetsverbuende.at/ ）において、国内すべての運輸連合の地域路線バス・都市バス・路面電車・地下鉄・地域鉄道を網羅した全国統合GTFSデータおよび各運輸連合別GTFSデータをCC BY 4.0ライセンスで無償公開している。また、ÖBBグループが直営・連携する鉄道およびバス路線のGTFSデータと欧州標準NeTEx形式データ（`NETEX_2026.zip`）は、ÖBB公式オープンデータポータル（ https://data.oebb.at/de/datensaetze ）から定期更新で提供されている。

---

## 4. 航路（旅客船・フェリー）制度の詳細分類

### 4.1 水運法・航路事業法に基づく航路種別一覧

| 大分類 | 法的種別（公用語/日本語） | 根拠法律 | 概要・対象航路例 | プロジェクトでの位置づけ(初期収集/探索時/対象外) |
| --- | --- | --- | --- | --- |
| 定期旅客航路（河川・湖沼） | Linienverkehr（§ 78 Abs. 1 Z 1 SchFG） / 定期旅客船航路 | 1997年水運法（Schifffahrtsgesetz – SchFG § 78）およびボーデン湖水運規則（BSO） | 公表されたダイヤに基づき定点間を定期運航する航路（ドナウ川ウィーン〜ブラチスラヴァ高速船Twin City Liner、ヴァッハウ渓谷定期船、ハルシュタット湖鉄道連絡船、ヴォルフガング湖・アッター湖・ヴェルター湖・ボーデン湖等の定期航路） | 初期収集 |
| 渡船・フェリー航路 | Fährverkehr（§ 78 Abs. 1 Z 3 SchFG） / 渡船・フェリー航路（車両・自転車・歩行者） | 1997年水運法（SchFG § 78） | ドナウ川の両岸や湖沼を横断する車両・自転車・旅客渡船（Rollfähre Korneuburg–Klosterneuburg、Drahtseilbrücke Ottensheim、ノイジードラー湖自転車フェリー等） | 初期収集 |
| 不定期遊覧・河川クルーズ | Gelegenheitsverkehr（§ 78 Abs. 1 Z 2 SchFG） / Flusskreuzfahrten / 周遊観光船・国際河川クルーズ | 1997年水運法（SchFG § 78） | 同一港発着の観光周遊船およびドナウ川国際宿泊クルーズ船 | 探索時（固定ダイヤを持つ主要周遊便のみ） |
| 貨物・専用・レジャー水運 | Güterbeförderung（§ 78 Abs. 1 Z 4 SchFG）, Werkverkehr（§ 78 Abs. 2 SchFG）, Sportschifffahrt / 貨物専用船・特定者専用船・プレジャーボート | 1997年水運法（SchFG § 78） | ドナウ川貨物輸送船、工事・自社専用船、レジャーボート | 対象外 |

### 4.2 主要旅客航路・フェリー事業者（operators.csv 登録用）

- **主要事業者名・種別・公式サイトURL（沿岸フェリー、湖上・河川旅客船、渡船等）**: 1997年水運法（SchFG）に基づき、国際水路であるドナウ川本流およびウィーン・ドナウ運河の航行管理・インフラ維持は連邦省（BMK / BMIMI）の最高水運当局（Oberste Schifffahrtsbehörde / Abteilung IV/W1・W2）および連邦水路公社via donau（Österreichische Wasserstraßen-Gesellschaft mbH）が管轄し、各連邦州内の湖沼（ザルツカンマーグート諸湖、ヴェルター湖、アッヘン湖、ノイジードラー湖、ボーデン湖等）における旅客航路認可は各州政府の水運担当部局が管轄している。

| 事業者名（公用語） | 事業種別・水系 | 主な運航区間・路線網 | 公式サイトURL |
| --- | --- | --- | --- |
| Central Danube Region Marketing & Development GmbH (Twin City Liner) | 河川国際定期高速船（ドナウ運河・ドナウ川） | Wien City (Schwedenplatz) – Bratislava（高速カタマラン定期便） | https://www.twincityliner.com/ |
| DDSG Blue Danube Schiffahrt GmbH | 河川定期旅客船（ドナウ川） | ウィーン市内定期便、ヴァッハウ渓谷定期航路（Krems – Dürnstein – Spitz – Melk） | https://www.ddsg-bluedanube.at/ |
| BRANDNER Schiffahrt GmbH | 河川定期旅客船（ドナウ川） | ヴァッハウ渓谷定期航路（Krems – Melk） | https://www.brandner.at/ |
| Donauschifffahrt Wurm & Noé GmbH & Co. KG | 河川定期・観光旅客船（ドナウ川上部） | Passau – Engelhartszell – Aschach – Linz | https://www.donauschifffahrt.eu/ |
| Hallstättersee Schifffahrt Hemetsberger GmbH | 湖上通年定期連絡船（ハルシュタット湖） | Hallstatt Bahnhof（ÖBB鉄道駅直結）– Hallstatt Markt | https://www.hallstattschifffahrt.at/ |
| Salzburg AG Tourismus GmbH (WolfgangseeSchifffahrt) | 湖上定期旅客船（ヴォルフガング湖） | Strobl – St. Wolfgang (Schafbergbahn接続) – St. Gilgen | https://www.5schaetze.at/de/wolfgangseeschifffahrt.html |
| Stern & Hafferl Verkehrsgesellschaft m.b.H. (Attersee-Schifffahrt) | 湖上定期旅客船（アッター湖） | Attersee（Atterseebahn接続）– Weyregg – Unterach | https://www.atterseeschifffahrt.at/ |
| Traunsee Schifffahrt (Eder GmbH) | 湖上定期旅客船（トラウン湖） | Gmunden – Altmünster – Traunkirchen – Ebensee | https://www.traunseeschifffahrt.at/ |
| WSG Wörthersee Schifffahrt GmbH | 湖上定期旅客船（ヴェルター湖） | Klagenfurt – Krumpendorf – Pörtschach – Maria Wörth – Velden | https://www.woertherseeschifffahrt.at/ |
| Achenseeschifffahrt-GmbH | 湖上定期旅客船（アッヘン湖） | Seespitz（Achenseebahn接続）– Pertisau – Achenkirch | https://www.achenseeschifffahrt.at/ |
| Vorarlberg Lines-Bodenseeschifffahrt GmbH & Co KG | 湖上国際定期旅客船（ボーデン湖） | Bregenz – Lindau – Konstanz（ボーデン湖統合船隊BSB連携） | https://www.vorarlberg-lines.at/ |
| Donau-Rollfähre Korneuburg-Klosterneuburg GmbH | 河川渡船・車両フェリー（ドナウ川） | Korneuburg – Klosterneuburg（水流利用ワイヤー式渡船） | https://www.rollfaehre.at/ |

- **公的航路リスト・航路網台帳の入手先URL**: ドナウ川水系の公式水路・閘門（全9箇所）・船着場台帳は、連邦水路公社via donauの電子水路図（Inland ENC Standard 2.4）および水路アトラス提供ページ（ https://www.viadonau.org/wirtschaft/services-transportplanung/karten ）ならびにドナウ河川情報サービスDoRISの船着場アトラス（Atlas of berths： https://www.doris.bmimi.gv.at/ ）から入手可能であり、法規・全国の管轄水運庁一覧は連邦省（BMK / BMIMI）の水運ポータル（ https://www.bmk.gv.at/themen/verkehr/wasser/schifffahrt.html ）に整備されている。

---

## 5. 航空路（国内定期航空路）制度の詳細分類

### 5.1 航空法に基づく運航種別一覧

| 大分類 | 法的種別（公用語/日本語） | 根拠法律 | 概要・対象範囲 | プロジェクトでの位置づけ(初期収集/探索時/対象外) |
| --- | --- | --- | --- | --- |
| 定期航空運送事業 | Fluglinienverkehr（Linienflugverkehr gemäß § 102 LFG / VO (EG) Nr. 1008/2008） / 定期航空路線（国内線・国際線） | 1957年航空法（Luftfahrtgesetz – LFG §§ 101–102）およびEU規則1008/2008号 | 公表された時刻表に従い一般旅客向けに反復運航される定期便（国内線はウィーン国際空港（VIE）と地方空港を結ぶ路線） | 初期収集 |
| 地域・季節定期航空便 | Regionaler Saison-Linienflugverkehr / 季節定期便 | LFG § 102 / EU規則1008/2008号 | 冬季・夏季の特定スケジュール期間に定期ダイヤで運航される地域路線 | 探索時 |
| 不定期・汎用航空 | Bedarfsflugverkehr（Gelegenheitsluftverkehr / Charter）, Rundflüge, Arbeitsflüge, Allgemeine Luftfahrt / チャーター便・遊覧飛行・航空測量・救難ヘリ | 1957年航空法（LFG §§ 102, 130） | 観光チャーター便、ビジネスジェット、遊覧飛行、航空測量、山岳救難ヘリ等 | 対象外 |

### 5.2 主要航空運送事業者（operators.csv 登録用）

- **主要国内航空事業者名・種別・公式サイトURL**: オーストリア国内の定期航空路線は、ナショナルフラッグキャリアであるAustrian Airlines AG (AUA)が唯一運航している。高速鉄道網（ÖBB Railjet）の拡充およびモーダルシフトの進展に伴い、短距離国内線は鉄道にIATA便名（`OS`）を付与してウィーン国際空港駅（Flughafen Wien Bahnhof）へ直通させるコードシェア鉄道連絡便「AIRail」（リンツ・ザルツブルク・グラーツ発着）への転換が進んでおり、ウィーン（`VIE`）〜グラーツ（`GRZ`）間の航空便が2026年10月23日をもって運航を終了したため、2026年冬季スケジュール時点における純粋な国内定期航空路線はウィーン（`VIE`）〜インスブルック（`INN`）線および**ウィーン（`VIE`）〜クラーゲンフルト（`KLU`）線**の2路線となっている。なお、最西端のフォアアールベルク州には商業空港が存在しないため、オーストリア法人のリージョナル航空会社であるPeople's (Altenrhein Luftfahrt GmbH)がスイス国境直近のサンクト・ガレン・アルテンライン空港（`ACH`）とウィーン（`VIE`）の間で準国内線として機能する定期便を運航している。

| 事業者名（公用語） | IATA | ICAO | 事業種別・国内線運航状況 | 公式サイトURL |
| --- | --- | --- | --- | --- |
| Austrian Airlines AG (AUA) | OS | AUA | 定期航空運送事業者（国内定期線：VIE–INN、VIE–KLUの2路線を運航） | https://www.austrian.com/ |
| People's (Altenrhein Luftfahrt GmbH) | PE | PEV | リージョナル定期航空事業者（フォアアールベルク州隣接のACH–VIE線を運航） | https://www.peoples.at/ |

- **国内定期航空路線一覧の入手先URL**: 国内空港・空域・計器飛行経路の公式台帳はオーストリア民間航空管制公社（Austro Control：Österreichische Gesellschaft für Zivilluftfahrt mbH）が発行する電子航空情報刊行物（eAIP Austria： https://eaip.austrocontrol.at/ ）で公開されており、路線別の定期航空輸送実績および発着統計はオーストリア統計局（Statistik Austria： https://www.statistik.at/statistiken/tourismus-und-verkehr/verkehr/luftfahrt ）から入手できる。

---

## 6. 交通拠点（ノード）の詳細種別と公式コード

- **鉄道駅・地下鉄駅・電停（駅コード規格、駅ナンバリング規格、UIC駅コード、Wikidata P番号等）**: オーストリアの鉄道網における国際標準コードはUIC国別コード`81`を冠した7桁の**UIC駅コード**（ÖBBのオープンデータ上では`Eva-Nr.`と表記、例：Wien Hbf = `8103000`、Salzburg Hbf = `8100002`、Innsbruck Hbf = `8100108`）であり、Wikidataのプロパティ`P722`（UIC station code）および`P954`（IBNR）に直接対応している。これと並行して、ÖBB-Infrastruktur AGの内部管理および鉄道網利用条件（SNNB Anhang 2.3.3 `Verzeichnis der Verkehrsstationen`および`Streckendaten Notfallmanagement`）では、すべての駅・信号場（Betriebsstelle）に対して1〜4文字のアルファベットからなる公式略称コード**`DB640-Code`**（および正式名称`DB640-Name`、例：Wien Hbf = `Wbf`、Linz Hbf = `Lz`、Graz Hbf = `G`）とキロ程管理コード**`KMSYS-Code`**が付与されている。さらに、鉄道駅・地下鉄駅・路面電車電停・バス停を横断するマルチモーダルな全国統一識別子として、7大運輸連合（Mobilitätsverbünde Österreich）およびGIP.atでは欧州標準CEN規格（IFOPT）に準拠した階層型グローバル停留所ID **`at:{System/Bundesland}:{Gemeinde/Ort}:{StopID}:{Mast/Platform}`**（例：`at:49:1349:0:1`）が全拠点に付与されており、全国GTFSの`stop_id`およびNeTExの主キーとして機能する（なお、日本のような駅固有の連番駅ナンバリング制度は採用されておらず、路線系統番号とIFOPTコード・駅名で管理される）。
- **高速道路施設（IC/JCT/SA/PA等の公式名称・番号体系）**: 1971年連邦道路法第2条・第26条（BStG 1971 §§ 2, 26）およびASFINAGの管理基準に基づき、アウトバーン・自動車専用道路同士が接続するジャンクションは**`Knoten`**（例：`Knoten Voralpenkreuz`、`Knoten Prater`、`Knoten Inzersdorf`）、一般道路網と接続するインターチェンジは**`Anschlussstelle (ASt)`**（全国386箇所、特定方向のみ接続するハーフICは`Halbanschlussstelle (HASt)`）と定義される。オーストリアのIC/JCT出口番号は連番方式ではなく、**当該路線の起点からのキロ程（km整数値）をそのまま出口番号（Exit Number）として使用する距離基準方式**（OSMでは`highway=motorway_junction`の`ref`タグにキロ程整数値を格納）が採られている。また、高速道路上の休憩施設はASFINAGにより、給油所・レストラン・売店を備えた大型サービスエリアに相当する**`Raststation`**（全国85箇所）、ASFINAG直営でトイレ・シャワー・自販機・休憩室を備えた高機能パーキングエリアである**`Rastplatz`**（全国59箇所）、および簡易駐車施設である**`Parkplatz`**（全国96箇所）の3階層で厳密に区分管理されている。
- **道の駅・公式休憩施設等（制度の有無とリスト入手先）**: 一般州道（B・L道路）には日本の「道の駅」に相当する国認定の休憩施設制度は存在しないが、1971年連邦道路法第2条（BStG 1971 § 2）において、高速道路のIC直近に整備される相乗り用駐車場**`Park & Drive (P&D) Anlage`**（全国73箇所）および鉄道駅接続の**`Park & Ride (P&R) Anlage`**が道路・鉄道の公式附属施設として法定化されている。公式施設リストおよび位置データは、ASFINAGの休憩・駐車施設ポータル（ https://www.asfinag.at/parken-rasten/ ）およびÖBB Open DataのP&R・Bike&Ride・Shared-Mobility拠点データセット（ https://data.oebb.at/de/datensaetze ）から取得できる。
- **旅客空港（定期便就航空港、IATA 3レターコード、ICAOコード、Wikidata P238/P239）**: オーストリア国内で定期旅客便が就航する主要6空港のコード体系（ICAOコードはすべてプレフィックス`LOW`で始まる）は以下のとおりである。

| 空港名（公用語） | 所在地（連邦州） | IATA (P238) | ICAO (P239) | Wikidata QID | 定期便運航区分・鉄道接続状況 |
| --- | --- | --- | --- | --- | --- |
| Flughafen Wien-Schwechat | Schwechat（Niederösterreich / Wien） | VIE | LOWW | Q27075 | 国際ハブ空港・国内定期便基点（ÖBB長距離Railjet・S7・CAT直結） |
| Flughafen Innsbruck | Innsbruck（Tirol） | INN | LOWI | Q694545 | 国際定期便・国内定期便（VIE線就航） |
| Flughafen Klagenfurt | Klagenfurt（Kärnten） | KLU | LOWK | Q694426 | 国際定期便・国内定期便（VIE線就航、S-Bahn駅近接） |
| Flughafen Graz | Feldkirchen bei Graz（Steiermark） | GRZ | LOWG | Q170336 | 国際定期便（VIEへはÖBB AIRail連絡、S-Bahn S5駅近接） |
| Flughafen Salzburg | Salzburg（Salzburg） | SZG | LOWS | Q169135 | 国際定期便・季節定期便（VIEへはÖBB AIRail連絡、トロリーバス直結） |
| Flughafen Linz | Hörsching（Oberösterreich） | LNZ | LOWL | Q694404 | 国際定期便・貨物拠点（VIEへはÖBB AIRail連絡） |

- **主要港湾（国際港、主要旅客港、UN/LOCODEコード）**: 内陸国であるオーストリアでは、国際水路ドナウ川（TEN-Tライン＝ドナウ回廊）沿いに4大商業港（ウィーン、エンス、リンツ、クレムス）および主要旅客船ターミナルが整備されており、各港の位置は黒海河口からの距離を示す`Strom-km`およびUN/LOCODEで管理されている。

| 港湾・船着場名（公用語） | 所在地（水系） | ドナウ河口からのキロ程 | UN/LOCODE | 港湾区分・主な役割 |
| --- | --- | --- | --- | --- |
| Hafen Wien（Freudenau / Albern / Lobau） | Wien（ドナウ川） | Strom-km 1920.1 | AT VIE | 国内最大の国際内陸商業港・TEN-T複合一貫物流拠点 |
| Schiffstation Wien City / Reichsbrücke | Wien（ドナウ運河 / ドナウ川） | Strom-km 1928.9 | AT VIE | 国際定期高速船（Twin City Liner）・ドナウ河川クルーズ旅客港 |
| Ennshafen | Enns / Ennsdorf（ドナウ川） | Strom-km 2111.8 | AT ENS | 国際内陸商業港・コンテナターミナル（OÖ州・NÖ州境） |
| Hafen Linz | Linz（ドナウ川） | Strom-km 2131.8 | AT LNZ | 国際内陸商業港・ドナウ旅客船ターミナル |
| Hafen Krems | Krems an der Donau（ドナウ川） | Strom-km 2001.5 | AT KRE | 内陸商業港・ヴァッハウ渓谷定期旅客船拠点 |
| Hafen Bregenz | Bregenz（ボーデン湖） | ―（湖上港） | AT BRZ | ボーデン湖国際定期旅客船ターミナル |

---

## 7. 路線の繋がり（順序）の公式基準 ＆ 駅順データ調達

- **起点〜終点までの順序を決定する公式基準（キロ程、駅ナンバリング順、法令指定起終点等）**: 鉄軌道網における物理的な駅・分岐点の順序は、ÖBB-Infrastruktur AGが管理する公式路線番号**`VzG-Strecke`**（Verzeichnis örtlich zulässiger Geschwindigkeiten：区間許容最高速度台帳の路線番号）およびキロ程管理軸**`KMSYS-Strecke`**上の**起点からの累積キロ程（`KM`およびヘクトメートル`HM`）の昇順**によって一意に決定される。トンネル新線切替等により歴史的なキロ程に不連続（距離更正：Fehlerprofil）が生じている区間については、`KMSYS-Code`によって路線がサブセグメントに分割管理されており、セグメント順とキロ程昇順を組み合わせることで正確なトポロジー順序が復元できる構造となっている。道路網については、1971年連邦道路法（BStG 1971）の別表1・別表2（Verzeichnis 1 und 2）に規定された路線記述順（原則としてウィーンまたは主要分岐ジャンクションを起点とし、地方・国境方向を終点とするキロ程昇順）が法的基準となり、GISデータ上では全国標準交通参照グラフ`GIP.at`のリンク方向と線形参照値（Linear Referencing）が標準基準となる。また、ドナウ川水路網（Wasserstraße Donau）の公式キロ程（`Strom-km`）は、黒海河口（ルーマニア・スリナ：0.0 km）を起点として上流に向かって数値が増加する国際ドナウ委員会基準を採用しているため、オーストリア国内では東端のスロバキア国境（約1872.7 km）から西端のドイツ・パッサウ国境（約2223.2 km）へ向かってキロ程が昇順となる点に留意が必要である。
- **公式路線網台帳（鉄道要覧、Streckenverzeichnis等）の入手先URL**: 鉄軌道網の最も権威ある一次台帳は、ÖBB-Infrastruktur AGが毎年公表する鉄道網利用条件（Schienennetz-Nutzungsbedingungen – SNNB 2026 / 2027： https://infrastruktur.oebb.at/de/geschaeftspartner/schienennetz/snnb ）およびその別冊である旅客駅一覧台帳（Anhang 2.3.3 `Verzeichnis der Verkehrsstationen`： https://data.oebb.at/de/datensaetze~verzeichnis-der-verkehrsstationen~ ）である。さらに、GISに直接インポート可能な空間路線網台帳として、ÖBB Open Dataポータルにて「Geo Netz」（ https://data.oebb.at/de/datensaetze~geo-netz~ ）および毎月更新の「Streckendaten Notfallmanagement」（ https://data.oebb.at/de/datensaetze~streckendaten_notfallmanagement~ ）が公開されており、路線ポリライン（`Strecke`）、全駅・信号場ポイント（`Betriebsstellen`）、100m単位のキロポスト（`KM` / `HM`）を`VZG-Strecke`・`KMSYS-Code`・`DB640-Code`・`Eva-Nr.`属性付きでShapefile / GeoJSON / XLSX形式で一括調達できる。また、Raaberbahn AG等の私鉄インフラも独自のSNNB（ https://www.raaberbahn.at/ ）を公表している。
- **Wikidata（次の駅 P197）またはOSM路線リレーション（type=route, route=railway）からの駅順エッジ取得可能性**: オーストリアの交通データベース構築においては、物理的なインフラ上の駅順エッジはÖBB Open Data（`Streckendaten Notfallmanagement`および`Geo Netz`）の`VZG-Strecke`別キロ程ソートから、また運行系統（S-Bahn、REX、U-Bahn、トラム、バス）上の停車駅順エッジは**Mobilitätsverbünde Österreichの全国統合GTFS（`stop_times.txt`の`stop_sequence`）**および**ÖBBのNeTExデータ（`NETEX_2026.zip`）**から欠損なく直接生成できるため、これら公的オープンデータを主軸とすることが最も確実である。これを補完するOpenStreetMap（OSM）の路線リレーションについても、物理路線（`type=route`, `route=railway`, `ref={VzG番号}`）および運行系統（`type=route`, `route=train`/`subway`/`tram`, `public_transport:version=2`）ともにオーストリア国内の整備精度は極めて高く、リレーションメンバーの順序から正確にエッジを抽出できる。一方、Wikidataの隣接駅プロパティ（`P197`）は主要幹線やウィーン地下鉄では網羅されているものの、快速（REX）と各駅停車（S-Bahn）が重複する区間や地方私鉄線において通過駅のスキップやリンク欠損が見られるため、公的GIS・GTFSデータに対するクロスチェックおよびQID紐付け用途として利用するのが最適である。

---

## 8. 交通オープンデータの出典メタデータ一覧（data_sources.csv 登録用表）

| source_id | category | source_name_ja | provider_ja | license | url | attribution_required | terms_summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| aut_gip_ogd | 道路・複合交通網 | オーストリア標準交通参照グラフ（GIP.at OGD） | ITS Vienna Region / 各連邦州・BMK・ASFINAG・ÖBB | CC BY 4.0 | https://www.gip.gv.at/ | TRUE | 商用・非商用利用可。出典表記（「Datenquelle: GIP.at」）が必須。 |
| aut_basemap | 背景地図・道路GIS | オーストリア公式行政背景地図（basemap.at） | ウィーン市およびオーストリア全連邦州（geoland.at） | CC BY 4.0 | https://basemap.at/ | TRUE | 2ヶ月更新の公式WMTS/ベクター地図（2026年Q3より新ベクター版提供）。リンク付きで「Datenquelle: basemap.at」の表記が必須。 |
| aut_oebb_geonetz | 鉄軌道インフラ・駅 | ÖBB Geo Netz（路線網・旅客駅GISデータ） | ÖBB-Infrastruktur AG | CC BY 3.0 AT | https://data.oebb.at/de/datensaetze~geo-netz~ | TRUE | GIP.atに基づく鉄道線（Streckenliste）および旅客乗降駅（Betriebsstellen）のGeoJSON/SHP/XLSX。「Datenquelle: ÖBB-Infrastruktur AG」の表記が必要。 |
| aut_oebb_notfall | 鉄軌道詳細・キロ程 | ÖBB Streckendaten Notfallmanagement | ÖBB-Infrastruktur AG | CC BY 3.0 AT | https://data.oebb.at/de/datensaetze~streckendaten_notfallmanagement~ | TRUE | 毎月更新。DB640コード、VzG路線番号、KMSYSキロ程、UIC駅コード（Eva-Nr.）、踏切、トンネルを含むGISデータ。 |
| aut_oebb_stations | 交通拠点（鉄道駅） | ÖBB 駅・停留場一覧台帳（Verzeichnis der Verkehrsstationen） | ÖBB-Infrastruktur AG | CC BY 3.0 AT | https://data.oebb.at/de/datensaetze~verzeichnis-der-verkehrsstationen~ | TRUE | SNNB Anhang 2.3.3として公開される全駅の公式台帳（XLSX）。リンク付き出典表記が必須。 |
| aut_oebb_gtfs_netex | 鉄道時刻表・系統 | ÖBB GTFS / NeTEx 全国鉄道運行データ | ÖBB-Personenverkehr AG / ÖBB-Holding AG | CC BY 3.0 AT | https://data.oebb.at/de/datensaetze | TRUE | ÖBB旅客列車、CAT、Montafonerbahnを含む全国GTFSおよびNeTEx（NETEX_2026.zip）データ。 |
| aut_mobverb_gtfs | バス・都市交通・全公共交通 | オーストリア7大運輸連合 統合GTFSデータ | Mobilitätsverbünde Österreich | CC BY 4.0 | https://data.mobilitaetsverbuende.at/ | TRUE | 全9州・7運輸連合（VOR, OÖVV, SVV, VVT, VVV, VST, VKG）の鉄道・地下鉄・トラム・バスを網羅する公式GTFSデータ。 |
| aut_viadonau_enc | 航路・水路GIS | ドナウ川電子水路図（Inland ENC）および水路OGD | via donau – Österreichische Wasserstraßen-Gesellschaft mbH | CC BY 4.0 / IWG | https://www.viadonau.org/infrastruktur/geoinformation/informationsweiterverwendung-open-data | TRUE | INSPIRE指令および情報再利用法（IWG）に基づくドナウ川水路・閘門・船着場のOGC/Inland ECDIS 2.4データ。 |
| aut_austrocontrol_aip | 航空路・空港 | オーストリア航空情報刊行物（eAIP Austria） | Austro Control GmbH | 閲覧無料（商用再配布は要許諾） | https://eaip.austrocontrol.at/ | TRUE | 国内全空港・飛行場・空域・航空路の公式台帳。二次配布にはAustro Controlの許諾が必要。 |
| aut_datagvat | 総合交通オープンデータ | オーストリア政府オープンデータポータル（data.gv.at） | オーストリア連邦政府・各連邦州・自治体 | CC BY 4.0（一部CC BY 3.0 AT） | https://www.data.gv.at/ | TRUE | オーストリア全行政機関・公社のオープンデータ統合カタログ。 |

---

## 9. 一次情報源・公式オープンデータ入手先リンク集

- **道路・交通網GISデータダウンロード元URL**: オーストリア全土の行政道路網グラフ（GIP.at： https://www.gip.gv.at/ ）、2ヶ月ごとに更新される公式行政ベクター・ラスタ背景地図（basemap.at： https://basemap.at/ ）、ASFINAGの高速道路インフラ統計・休憩施設データ（ https://www.asfinag.at/ueber-uns/zahlen-fakten/ ）、および政府総合オープンデータカタログ（data.gv.at： https://www.data.gv.at/ ）から道路・マルチモーダルGISデータを直接ダウンロードできる。
- **鉄軌道・索道公的台帳・事業者一覧URL**: 鉄軌道インフラのGISデータ（Geo Netz、Streckendaten Notfallmanagement）、駅台帳（Verzeichnis der Verkehrsstationen）、および全国鉄道GTFS/NeTExはÖBB Open Dataポータル（ https://data.oebb.at/de/datensaetze ）で一元配布されており、路線網利用条件（SNNB 2026 / 2027）はÖBB-Infrastruktur AG公式サイト（ https://infrastruktur.oebb.at/de/geschaeftspartner/schienennetz/snnb ）、全7運輸連合のバス・都市交通を含む統合GTFSはMobilitätsverbünde Österreichのデータポータル（ https://data.mobilitaetsverbuende.at/ ）、索道に関する公的情報・統計は連邦省（BMK / BMIMI）の索道当局ページ（ https://www.bmk.gv.at/themen/verkehr/seilbahn.html および https://www.bmimi.gv.at/themen/verkehr/seilbahn.html ）からそれぞれ入手できる。
- **航路・水上交通公的台帳URL**: ドナウ川およびドナウ運河の電子水路図（Inland ENC Standard 2.4）と水路アトラス（Streckenatlas）は連邦水路公社via donauの地図サービスページ（ https://www.viadonau.org/wirtschaft/services-transportplanung/karten ）およびOpen Data窓口（ https://www.viadonau.org/infrastruktur/geoinformation/informationsweiterverwendung-open-data ）で提供されており、リアルタイム水路情報・閘門稼働状況・船着場台帳はDoRISポータル（ https://www.doris.bmimi.gv.at/ および https://www.doris.bmk.gv.at/ ）、水運法規・行政窓口一覧は連邦省（BMK / BMIMI）水運ページ（ https://www.bmk.gv.at/themen/verkehr/wasser/schifffahrt.html ）から取得できる。
- **航空局・国内航空網台帳URL**: 国内空港・飛行場の座標、滑走路諸元、空域および航空路の公式台帳はAustro Controlの電子航空情報刊行物（eAIP Austria： https://eaip.austrocontrol.at/ ）およびAustro Control公式サイト（ https://www.austrocontrol.at/ ）、ならびに連邦省（BMK / BMIMI）民間航空ポータル（ https://www.bmk.gv.at/themen/verkehr/luftfahrt.html ）において公開されている。
- **港湾局・公式港湾一覧URL**: ドナウ川沿いの全商業港湾（Häfen）および公共・専用船着場（Länden）の公式位置・キロ程台帳はDoRISの船着場アトラス（Atlas of berths： https://www.doris.bmimi.gv.at/ ）およびvia donauの年次報告書・刊行物ページ（ https://www.viadonau.org/newsroom/publikationen ）に収録されており、国際港湾・拠点コードはUNECEのUN/LOCODE公式リスト（ https://unece.org/trade/cefact/unlocode-code-list-country-and-territory ）から参照できる。
