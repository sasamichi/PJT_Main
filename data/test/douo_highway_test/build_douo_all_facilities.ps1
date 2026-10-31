# build_douo_all_facilities.ps1
# 道央自動車道の全拠点（IC, JCT, SA, PA, SIC, TB, BS, 展望所）を網羅した
# 隔離テストデータベースを構築するスクリプト

$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
$masterDir = "c:\Users\user\Documents\PJT\data\master"

# 大圏距離計算（Haversine）
function Get-HaversineKm($lat1, $lon1, $lat2, $lon2) {
    $R = 6371.0
    $dLat = [Math]::PI * ($lat2 - $lat1) / 180.0
    $dLon = [Math]::PI * ($lon2 - $lon1) / 180.0
    $rLat1 = [Math]::PI * $lat1 / 180.0
    $rLat2 = [Math]::PI * $lat2 / 180.0

    $a = [Math]::Sin($dLat / 2) * [Math]::Sin($dLat / 2) +
         [Math]::Cos($rLat1) * [Math]::Cos($rLat2) *
         [Math]::Sin($dLon / 2) * [Math]::Sin($dLon / 2)
    $c = 2 * [Math]::Atan2([Math]::Sqrt($a), [Math]::Sqrt(1 - $a))
    return $R * $c
}

# 1. 自治体マスタ（municipalities.csv）をロード
$muniPath = Join-Path $masterDir "municipalities.csv"
$munis = Import-Csv $muniPath -Encoding UTF8

$muniByName = @{}
foreach ($m in $munis) {
    if ($m.名称) {
        $muniByName[$m.名称] = $m.municipality_id
    }
}

# 2. 既存のPA/SAデータを test_sapa_nodes.csv として明示的に保存・保持
if (Test-Path (Join-Path $testDir "test_nodes.csv")) {
    $existingTestNodes = Import-Csv (Join-Path $testDir "test_nodes.csv") -Encoding UTF8
    $sapaOnly = $existingTestNodes | Where-Object { $_.種別 -eq '高速施設（SA・PA）' }
    $sapaOnly | Export-Csv (Join-Path $testDir "test_sapa_nodes.csv") -Encoding UTF8 -NoTypeInformation
    Write-Host "-> 既存PA/SAデータを test_sapa_nodes.csv ($($sapaOnly.Count) 件) として保持・保存しました。"
}

# 3. Wikidataから道央道関連全エンティティの最新諸元を取得
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
    "User-Agent" = "AntigravityHokkaidoPilot/1.0 (douo_all_facilities)"
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

# 4. Wikipedia「道央自動車道」記事から本線テーブルを全行精査
$wikiText = [System.IO.File]::ReadAllText((Join-Path $testDir "wikipedia_douo_wikitext.txt"), [System.Text.Encoding]::UTF8)

$sectionText = ""
if ($wikiText -match '(?s)==\s*インターチェンジなど\s*==\r?\n(.*?)\r?\n==[^=]') {
    $sectionText = $matches[1]
} else {
    $sectionText = $wikiText
}

$rows = $sectionText -split '\r?\n\|-'
$allFacilitiesList = [System.Collections.Generic.List[PSCustomObject]]::new()
$currMuni = ""
$currSubPref = ""

foreach ($r in $rows) {
    # 振興局
    if ($r -match '\[\[([^\]|]+総合振興局|[^\]|]+振興局)\]\]') {
        $currSubPref = $matches[1]
    }
    # 自治体
    if ($r -match '\[\[([^\]|]+(?:町|市|村))\]\]') {
        $currMuni = $matches[1]
    }

    # 各セルを行単位で抽出
    $rawLines = $r -split '\r?\n'
    $cells = @()
    foreach ($line in $rawLines) {
        if ($line -match '^[|!]') {
            $cells += $line
        }
    }

    if ($cells.Count -lt 2) { continue }

    # Cell 0: IC番号
    $icNo = ""
    if ($cells[0] -match '!style=[^|]*\|\s*([0-9]+|-)\s*') {
        $icNo = $matches[1].Trim()
    }

    # Cell 1: 施設名
    $c1 = $cells[1]
    $facilityRow = $null

    if ($c1 -match '\[\[([^\]|]+)(?:\|([^\]]+))?\]\]') {
        $pTitle = $matches[1].Trim()
        $dName  = if ($matches[2]) { $matches[2].Trim() } else { $pTitle }

        if ($pTitle -match 'インターチェンジ|サービスエリア|パーキングエリア|ジャンクション|本線料金所|バスストップ|展望所') {
            if ($pTitle -notin @("インターチェンジ", "スマートインターチェンジ", "ジャンクション", "サービスエリア", "パーキングエリア", "本線料金所", "バス停留所")) {
                $facilityRow = @{
                    title     = $pTitle
                    disp_name = $dName
                    is_linked = $true
                }
            }
        }
    } elseif ($c1 -match '(駒ケ岳PA|国縫PA)') {
        $rawName = $matches[1].Trim()
        $facilityRow = @{
            title     = if ($rawName -eq '駒ケ岳PA') { "駒ケ岳パーキングエリア" } else { "国縫パーキングエリア" }
            disp_name = $rawName
            is_linked = $false
        }
    }

    if (-not $facilityRow) { continue }

    $pTitle = $facilityRow.title
    # HTMLタグの完全除去
    $dName  = ($facilityRow.disp_name -replace '<[^>]+>', '').Trim()

    # 施設種別の判定
    $kind = if ($pTitle -match 'サービスエリア') { "高速施設（SA・PA）" }
            elseif ($pTitle -match 'パーキングエリア') { "高速施設（SA・PA）" }
            elseif ($pTitle -match '展望所') { "高速施設（SA・PA）" }
            elseif ($dName -match 'SIC|スマート') { "IC・JCT" }
            elseif ($pTitle -match 'ジャンクション') { "IC・JCT" }
            elseif ($pTitle -match 'インターチェンジ') { "IC・JCT" }
            elseif ($pTitle -match '本線料金所') { "本線料金所" }
            elseif ($pTitle -match 'バスストップ') { "バス停留所" }
            else { "その他" }

    # 位置基準のキロ程抽出
    # Cell 3: 札幌JCTから
    $kmSapporo = $null
    if ($cells.Count -ge 4) {
        $c3Clean = $cells[3] -replace '^.*\|', ''
        if ($c3Clean -match '^-?[0-9]+(?:\.[0-9]+)?$') {
            $kmSapporo = [double]$c3Clean
        }
    }

    # Cell 4: 七飯ICから
    $kmNanae = $null
    if ($cells.Count -ge 5) {
        $c4Clean = $cells[4] -replace '^.*\|', ''
        if ($c4Clean -match '^-?[0-9]+(?:\.[0-9]+)?$') {
            $kmNanae = [double]$c4Clean
        }
    }

    # 廃止日（バスストップ等）
    $endDate = ""
    if ($r -match '\[\[([0-9]{4})年\]\]\[\[([0-9]{1,2})月([0-9]{1,2})日\]\]をもって(?:廃止|休止)') {
        $endDate = ("{0:D4}-{1:D2}-{2:D2}" -f [int]$matches[1], [int]$matches[2], [int]$matches[3])
    }

    # 開設予定 / 供用状態の判定（#CCC背景またはキーワード）
    $isUnopened = ($c1 -match '#[cC]{3}' -or $r -match '開設予定|事業中|基本計画|仮称|計画中')
    $statusStr = if ($endDate) { "廃止・休止" }
                 elseif ($isUnopened) { "計画・事業中" }
                 else { "供用中" }

    # Wikidataとの突合
    $wd = $null
    if ($wdFacilities.ContainsKey($pTitle)) {
        $wd = $wdFacilities[$pTitle]
    } else {
        foreach ($k in $wdFacilities.Keys) {
            if ($pTitle -like "*$k*" -or $k -like "*$pTitle*") {
                $wd = $wdFacilities[$k]
                break
            }
        }
    }

    $allFacilitiesList.Add([PSCustomObject]@{
        ic_no       = $icNo
        page_title  = $pTitle
        disp_name   = $dName
        kind        = $kind
        sub_pref    = $currSubPref
        muni_name   = $currMuni
        km_sapporo  = $kmSapporo
        km_nanae    = $kmNanae
        wd_qid      = if ($wd) { $wd.qid } else { "" }
        lat         = if ($wd) { $wd.lat } else { "" }
        lon         = if ($wd) { $wd.lon } else { "" }
        inception   = if ($wd) { $wd.inception } else { "" }
        end_date    = $endDate
        status      = $statusStr
        wiki_url    = if ($facilityRow.is_linked) { "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($pTitle) } else { "" }
    })
}

Write-Host "抽出された全施設数: $($allFacilitiesList.Count) 件"

# 5. 全拠点網羅ノードCSV（test_all_highway_nodes.csv）の出力
$nodeLines = [System.Collections.Generic.List[string]]::new()
$nodeLines.Add("node_id,country_code,municipality_id,operator_id,大分類,種別,公的コード,iata_code,icao_code,名称,名称_公用語,よみ_かな,緯度,経度,公式サイトURL,Wikipedia_url,Wikidata_id,開始日,終了日,確定ステータス,備考")

$idx = 1
$nodeIdMap = @{}

foreach ($f in $allFacilitiesList) {
    $nId = ("TEST-ALL-ND-{0:D6}" -f $idx)
    $idx++
    $nodeIdMap[$f.page_title] = $nId

    # 自治体IDの解決
    $mId = ""
    if ($f.muni_name -and $muniByName.ContainsKey($f.muni_name)) {
        $mId = $muniByName[$f.muni_name]
    }

    $subKind = if ($f.page_title -match 'サービスエリア') { "SA" }
               elseif ($f.page_title -match 'パーキングエリア') { "PA" }
               elseif ($f.page_title -match '展望所') { "展望所" }
               elseif ($f.disp_name -match 'SIC|スマート') { "スマートIC" }
               elseif ($f.page_title -match 'ジャンクション') { "JCT" }
               elseif ($f.page_title -match '本線料金所') { "TB" }
               elseif ($f.page_title -match 'バスストップ') { "高速BS" }
               else { "IC" }

    $opId = "JP-OP-000002"

    $cleanDisp = $f.disp_name -replace '"', '""'
    $icNoStr = if ($f.ic_no -and $f.ic_no -ne '-') { "IC番号: [$($f.ic_no)] / " } else { "" }
    $kmStr = if ($f.km_nanae -ne $null) { "七飯起点: $($f.km_nanae)km / " } elseif ($f.km_sapporo -ne $null) { "札幌JCT基準: $($f.km_sapporo)km / " } else { "" }
    $cleanRemark = "道央自動車道 (${icNoStr}${kmStr}表示名: $cleanDisp / 細分: $subKind / 自治体: $($f.muni_name) / 状態: $($f.status))" -replace '"', '""'

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
        $f.end_date,
        "Wikipedia_Wikidata検証済",
        "`"$cleanRemark`""
    ) -join ","

    $nodeLines.Add($row)
}

$allNodesPath = Join-Path $testDir "test_all_highway_nodes.csv"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($allNodesPath, $nodeLines, $utf8NoBom)
Write-Host "-> 全拠点ノード保存完了: $allNodesPath ($($allFacilitiesList.Count) 件)"

# 6. 全拠点網羅エッジCSV（test_all_highway_edges.csv）の出力
$edgeLines = [System.Collections.Generic.List[string]]::new()
$edgeLines.Add("edge_id,route_id,from_node_id,to_node_id,順序,距離_km,複線電化,状態,備考")

$eIdx = 1
for ($i = 0; $i -lt ($allFacilitiesList.Count - 1); $i++) {
    $f1 = $allFacilitiesList[$i]
    $f2 = $allFacilitiesList[$i + 1]

    $fromId = $nodeIdMap[$f1.page_title]
    $toId   = $nodeIdMap[$f2.page_title]

    # 距離の精密計算（七飯IC起点キロ程の差分を最優先）
    $distKm = ""
    if ($f1.km_nanae -ne $null -and $f2.km_nanae -ne $null) {
        $d = [Math]::Abs([double]$f2.km_nanae - [double]$f1.km_nanae)
        if ($d -eq 0.0 -and $f1.lat -and $f1.lon -and $f2.lat -and $f2.lon) {
            # 同一キロポスト併設施設間の微小物理距離（例: 札幌JCT ➔ 札幌IC）
            $d = Get-HaversineKm ([double]$f1.lat) ([double]$f1.lon) ([double]$f2.lat) ([double]$f2.lon)
        }
        $distKm = ([Math]::Round($d, 1)).ToString("F1")
    } elseif ($f1.km_sapporo -ne $null -and $f2.km_sapporo -ne $null) {
        $d = [Math]::Abs([double]$f2.km_sapporo - [double]$f1.km_sapporo)
        if ($d -eq 0.0 -and $f1.lat -and $f1.lon -and $f2.lat -and $f2.lon) {
            $d = Get-HaversineKm ([double]$f1.lat) ([double]$f1.lon) ([double]$f2.lat) ([double]$f2.lon)
        }
        $distKm = ([Math]::Round($d, 1)).ToString("F1")
    }

    $eId = ("TEST-ALL-ED-{0:D6}" -f $eIdx)
    $eIdx++

    # エッジ状態: 両端ノードがともに供用中なら「供用中」、片方でも計画・事業中または休止なら「計画・事業中または休止」
    $stateStr = if ($f1.status -eq '供用中' -and $f2.status -eq '供用中') { "供用中" } else { "計画・事業中または休止" }
    $remarkStr = "$($f1.page_title) ➔ $($f2.page_title)" -replace '"', '""'

    $row = @(
        $eId,
        "TEST-RT-DOUO-EXP-ALL",
        $fromId,
        $toId,
        ($i + 1),
        $distKm,
        "高速道路（有料）",
        $stateStr,
        "`"$remarkStr`""
    ) -join ","
    $edgeLines.Add($row)
}

$allEdgesPath = Join-Path $testDir "test_all_highway_edges.csv"
[System.IO.File]::WriteAllLines($allEdgesPath, $edgeLines, $utf8NoBom)
Write-Host "-> 全拠点エッジ保存完了: $allEdgesPath ($($allFacilitiesList.Count - 1) 区間)"

# 7. 全拠点路線CSV（test_all_transport_routes.csv）の出力
$routeLines = @(
    "route_id,country_code,operator_id,路線名,路線名_公用語,よみ_かな,交通種別,路線記号,起点ノード_id,終点ノード_id,全長_km,状態,Wikipedia_url,Wikidata_id,備考",
    "TEST-RT-DOUO-EXP-ALL,JP,JP-OP-000002,道央自動車道,道央自動車道,どうおうじどうしゃどう,高速道路,E5,$($nodeIdMap[$allFacilitiesList[0].page_title]),$($nodeIdMap[$allFacilitiesList[-1].page_title]),423.1,供用中,https://ja.wikipedia.org/wiki/%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93,Q867982,道央自動車道（IC/JCT/SA/PA/SIC/TB/BS 全拠点網羅エッジ接続検証データ）"
)
$allRoutesPath = Join-Path $testDir "test_all_transport_routes.csv"
[System.IO.File]::WriteAllLines($allRoutesPath, $routeLines, $utf8NoBom)
Write-Host "-> 全拠点路線保存完了: $allRoutesPath"
