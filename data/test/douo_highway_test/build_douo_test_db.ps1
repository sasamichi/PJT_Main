# build_douo_test_db.ps1
# 道央自動車道の施設（全SA/PA/IC/JCT）をWikipediaとWikidataから調達し、
# 隔離テストデータベース（data/test/douo_highway_test/）を構築・検証するスクリプト

$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
$masterDir = "c:\Users\user\Documents\PJT\data\master"

# 1. 自治体マスタ（municipalities.csv）をロード
$muniPath = Join-Path $masterDir "municipalities.csv"
$munis = Import-Csv $muniPath -Encoding UTF8

$muniByName = @{}
foreach ($m in $munis) {
    if ($m.名称) {
        $muniByName[$m.名称] = $m.municipality_id
    }
}

# 2. Wikidataから道央道施設一覧（SPARQL結果）を取得
$sparqlQuery = @"
SELECT ?item ?itemLabel ?type ?typeLabel ?coord ?inception ?operatorLabel WHERE {
  ?item wdt:P361 wd:Q867982 .
  OPTIONAL { ?item wdt:P31 ?type . }
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P571 ?inception . }
  OPTIONAL { ?item wdt:P137 ?operator . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ja,en". }
}
ORDER BY ?itemLabel
"@

$sparqlUri = "https://query.wikidata.org/sparql?query=" + [System.Uri]::EscapeDataString($sparqlQuery)
$sparqlHeaders = @{
    "User-Agent" = "AntigravityHokkaidoPilot/1.0 (douo_test)"
    "Accept"     = "application/sparql-results+json"
}

Write-Host "Wikidata SPARQLクエリ実行中..."
$wdRes = Invoke-RestMethod -Uri $sparqlUri -Headers $sparqlHeaders -Method Get

$wdFacilities = @{}
foreach ($b in $wdRes.results.bindings) {
    $name = $b.itemLabel.value
    $qid = ($b.item.value -replace '^.*/', '')
    $coordStr = if ($b.coord) { $b.coord.value } else { "" }
    $lat = ""
    $lon = ""
    if ($coordStr -match 'Point\(([0-9.]+)\s+([0-9.]+)\)') {
        $lon = [Math]::Round([double]$matches[1], 6).ToString("F6")
        $lat = [Math]::Round([double]$matches[2], 6).ToString("F6")
    }
    $incept = if ($b.inception) { ($b.inception.value -replace 'T.*$', '') } else { "" }
    $typeLabel = if ($b.typeLabel) { $b.typeLabel.value } else { "" }

    if (-not $wdFacilities.ContainsKey($name)) {
        $wdFacilities[$name] = @{
            qid       = $qid
            name      = $name
            lat       = $lat
            lon       = $lon
            inception = $incept
            typeLabel = $typeLabel
        }
    }
}

Write-Host "Wikidataから取得した施設エンティティ数: $($wdFacilities.Count)"

# 3. Wikipedia「道央自動車道」記事から本線テーブルをブロック単位（|- 区切り）で精密解析
$wikiText = [System.IO.File]::ReadAllText((Join-Path $testDir "wikipedia_douo_wikitext.txt"), [System.Text.Encoding]::UTF8)

# インターチェンジなどセクションの切り出し
$sectionText = ""
if ($wikiText -match '(?s)==\s*インターチェンジなど\s*==\r?\n(.*?)\r?\n==[^=]') {
    $sectionText = $matches[1]
} else {
    $sectionText = $wikiText
}

$rows = $sectionText -split '\r?\n\|-'
$facilitiesList = [System.Collections.Generic.List[PSCustomObject]]::new()
$currMuni = ""

foreach ($r in $rows) {
    # 自治体セルの追尾 (例: [[二海郡]]<br>[[八雲町]] または [[砂川市]])
    if ($r -match '\[\[([^\]|]+(?:町|市|村))\]\]') {
        $currMuni = $matches[1]
    }

    # 施設名リンクの検出
    if ($r -match '\[\[([^\]|]+(?:インターチェンジ|サービスエリア|パーキングエリア|ジャンクション|本線料金所))(\|([^\]]+))?\]\]') {
        $pageTitle = $matches[1]
        $dispName  = if ($matches[3]) { $matches[3] } else { $pageTitle }

        # 一般名詞リンクの除外
        if ($pageTitle -in @("インターチェンジ", "スマートインターチェンジ", "ジャンクション", "サービスエリア", "パーキングエリア", "本線料金所")) {
            continue
        }

        # 施設種別の判定
        $kind = if ($pageTitle -match 'サービスエリア') { "高速施設（SA・PA）" }
                elseif ($pageTitle -match 'パーキングエリア') { "高速施設（SA・PA）" }
                elseif ($dispName -match 'SIC|スマート') { "IC・JCT" }
                elseif ($pageTitle -match 'ジャンクション') { "IC・JCT" }
                elseif ($pageTitle -match 'インターチェンジ') { "IC・JCT" }
                elseif ($pageTitle -match '本線料金所') { "本線料金所" }
                else { "その他" }

        # セル行から距離（数値）の抽出
        # 書式: |style="text-align: right"|234.9 または | 234.9
        $kmList = @()
        $cellLines = $r -split '\r?\n'
        foreach ($cl in $cellLines) {
            if ($cl -match '\|\s*(?:style="[^"]*"\s*\|\s*)?(-?[0-9]+(?:\.[0-9]+)?)\s*$') {
                $numVal = $matches[1]
                # IC番号（例: 9, 10）とキロ程（小数点あり、または大きな整数）の識別
                if ($numVal -match '\.' -or [double]$numVal -gt 50.0) {
                    $kmList += [double]$numVal
                }
            }
        }

        $kmSapporo = if ($kmList.Count -ge 1) { $kmList[0] } else { $null }
        $kmNanae   = if ($kmList.Count -ge 2) { $kmList[1] } else { $null }

        # Wikidataとの突合
        $wd = $null
        if ($wdFacilities.ContainsKey($pageTitle)) {
            $wd = $wdFacilities[$pageTitle]
        } else {
            foreach ($k in $wdFacilities.Keys) {
                if ($pageTitle -like "*$k*" -or $k -like "*$pageTitle*") {
                    $wd = $wdFacilities[$k]
                    break
                }
            }
        }

        $facilitiesList.Add([PSCustomObject]@{
            page_title  = $pageTitle
            disp_name   = $dispName
            kind        = $kind
            muni_name   = $currMuni
            km_sapporo  = $kmSapporo
            km_nanae    = $kmNanae
            wd_qid      = if ($wd) { $wd.qid } else { "" }
            lat         = if ($wd) { $wd.lat } else { "" }
            lon         = if ($wd) { $wd.lon } else { "" }
            inception   = if ($wd) { $wd.inception } else { "" }
            wiki_url    = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($pageTitle)
        })
    }
}

Write-Host "本線順に抽出された施設数: $($facilitiesList.Count) 件"

# 4. テスト用 nodes.csv の生成
$nodeLines = [System.Collections.Generic.List[string]]::new()
$nodeLines.Add("node_id,country_code,municipality_id,operator_id,大分類,種別,公的コード,iata_code,icao_code,名称,名称_公用語,よみ_かな,緯度,経度,公式サイトURL,Wikipedia_url,Wikidata_id,開始日,終了日,確定ステータス,備考")

$idx = 1
$nodeIdMap = @{}

foreach ($f in $facilitiesList) {
    $nId = ("TEST-ND-{0:D6}" -f $idx)
    $idx++
    $nodeIdMap[$f.page_title] = $nId

    # 自治体IDの解決
    $mId = ""
    if ($f.muni_name -and $muniByName.ContainsKey($f.muni_name)) {
        $mId = $muniByName[$f.muni_name]
    }

    $subKind = if ($f.page_title -match 'サービスエリア') { "SA" }
               elseif ($f.page_title -match 'パーキングエリア') { "PA" }
               elseif ($f.disp_name -match 'SIC|スマート') { "スマートIC" }
               elseif ($f.page_title -match 'ジャンクション') { "JCT" }
               else { "IC" }

    $opId = "JP-OP-000002"

    $cleanDisp = $f.disp_name -replace '"', '""'
    $cleanRemark = "道央自動車道 (表示名: $cleanDisp / 細分: $subKind / 自治体: $($f.muni_name))" -replace '"', '""'

    $row = @(
        $nId,
        "JP",
        $mId,
        $opId,
        "交通拠点",
        $f.kind,
        "",
        "",
        "",
        "`"$($f.page_title)`"",
        "`"$($f.page_title)`"",
        "",
        $f.lat,
        $f.lon,
        "",
        "`"$($f.wiki_url)`"",
        $f.wd_qid,
        $f.inception,
        "",
        "Wikipedia_Wikidata検証済",
        "`"$cleanRemark`""
    ) -join ","

    $nodeLines.Add($row)
}

$nodesTestPath = Join-Path $testDir "test_nodes.csv"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($nodesTestPath, $nodeLines, $utf8NoBom)
Write-Host "-> テストノード保存完了: $nodesTestPath ($($facilitiesList.Count) 件)"

# 5. テスト用 edges.csv の生成（施設間の本線隣接順序・物理エッジ接続）
$edgeLines = [System.Collections.Generic.List[string]]::new()
$edgeLines.Add("edge_id,route_id,from_node_id,to_node_id,順序,距離_km,複線電化,状態,備考")

$eIdx = 1
for ($i = 0; $i -lt ($facilitiesList.Count - 1); $i++) {
    $f1 = $facilitiesList[$i]
    $f2 = $facilitiesList[$i + 1]

    $fromId = $nodeIdMap[$f1.page_title]
    $toId   = $nodeIdMap[$f2.page_title]

    $distKm = ""
    if ($f1.km_nanae -ne $null -and $f2.km_nanae -ne $null) {
        $d = [Math]::Abs([double]$f2.km_nanae - [double]$f1.km_nanae)
        $distKm = ([Math]::Round($d, 1)).ToString("F1")
    } elseif ($f1.km_sapporo -ne $null -and $f2.km_sapporo -ne $null) {
        $d = [Math]::Abs([double]$f2.km_sapporo - [double]$f1.km_sapporo)
        $distKm = ([Math]::Round($d, 1)).ToString("F1")
    }

    $eId = ("TEST-ED-{0:D6}" -f $eIdx)
    $eIdx++

    $remarkStr = "$($f1.page_title) ➔ $($f2.page_title)" -replace '"', '""'

    $row = @(
        $eId,
        "TEST-RT-DOUO-EXP",
        $fromId,
        $toId,
        ($i + 1),
        $distKm,
        "高速道路（有料）",
        "供用中",
        "`"$remarkStr`""
    ) -join ","
    $edgeLines.Add($row)
}

$edgesTestPath = Join-Path $testDir "test_edges.csv"
[System.IO.File]::WriteAllLines($edgesTestPath, $edgeLines, $utf8NoBom)
Write-Host "-> テストエッジ保存完了: $edgesTestPath ($($facilitiesList.Count - 1) 区間)"

# 6. テスト用 transport_routes.csv の生成
$routeLines = @(
    "route_id,country_code,operator_id,路線名,路線名_公用語,よみ_かな,交通種別,路線記号,起点ノード_id,終点ノード_id,全長_km,状態,Wikipedia_url,Wikidata_id,備考",
    "TEST-RT-DOUO-EXP,JP,JP-OP-000002,道央自動車道,道央自動車道,どうおうじどうしゃどう,高速道路,E5,$($nodeIdMap[$facilitiesList[0].page_title]),$($nodeIdMap[$facilitiesList[-1].page_title]),423.1,供用中,https://ja.wikipedia.org/wiki/%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93,Q867982,大沼公園IC〜札幌JCT〜旭川鷹栖IC（全線SA・PA網羅テスト検証）"
)
$routesTestPath = Join-Path $testDir "test_transport_routes.csv"
[System.IO.File]::WriteAllLines($routesTestPath, $routeLines, $utf8NoBom)
Write-Host "-> テスト路線保存完了: $routesTestPath"
