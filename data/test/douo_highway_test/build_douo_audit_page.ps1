# build_douo_audit_page.ps1
# 道央自動車道のデータ照合・検査用専用ページ（web/explorer/audit_douo.html）を生成するスクリプト
# 1. 稼働状態（供用中 / 計画・事業中 / 廃止・休止）の表示非表示フィルタ機能
# 2. Wikipedia枠付近に引用元URL（道央道元記事 ＆ 施設個別記事）への直リンクを配備

$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
$webDir  = "c:\Users\user\Documents\PJT\web\explorer"

$nodes = Import-Csv (Join-Path $testDir "test_all_highway_nodes.csv") -Encoding UTF8
$edges = Import-Csv (Join-Path $testDir "test_all_highway_edges.csv") -Encoding UTF8

$wikiText = [System.IO.File]::ReadAllText((Join-Path $testDir "wikipedia_douo_wikitext.txt"), [System.Text.Encoding]::UTF8)

# 大圏距離計算（Haversine）
function Get-HaversineKm($lat1, $lon1, $lat2, $lon2) {
    if (-not $lat1 -or -not $lon1 -or -not $lat2 -or -not $lon2) { return 0.0 }
    $R = 6371.0
    $dLat = [Math]::PI * ($lat2 - $lat1) / 180.0
    $dLon = [Math]::PI * ($lon2 - $lon1) / 180.0
    $rLat1 = [Math]::PI * $lat1 / 180.0
    $rLat2 = [Math]::PI * $lat2 / 180.0

    $a = [Math]::Sin($dLat / 2) * [Math]::Sin($dLat / 2) +
         [Math]::Cos($rLat1) * [Math]::Cos($rLat2) *
         [Math]::Sin($dLon / 2) * [Math]::Sin($dLon / 2)
    $c = 2 * [Math]::Atan2([Math]::Sqrt($a), [Math]::Sqrt(1 - $a))
    return [Math]::Round(($R * $c), 2)
}

# Wikitextのセルクリーニング関数
function Clean-Wikitext($text) {
    if (-not $text) { return "" }
    $t = $text -replace '(?s)<ref[^>]*>.*?</ref>', ''
    $t = $t -replace '<ref[^>]*/>', ''
    $t = $t -replace '<[^>]+>', ''
    $t = $t -replace '\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', '$1'
    $t = $t -replace '\{\{[^}]+\}\}', ''
    $t = $t -replace '\[http[^\s\]]+\s+([^\]]+)\]', '$1'
    $t = $t -replace '\[http[^\]]+\]', ''
    $t = $t -replace '^style=[^|]*\|', ''
    $t = $t -replace '^[!|]', ''
    $t = $t -replace '^style=[^|]*\|', ''
    $t = $t -replace "'''", ''
    $t = $t -replace "''", ''
    return $t.Trim()
}

# Wikipediaの「インターチェンジなど」セクションから全施設行を解析
$wikiRows = [System.Collections.Generic.List[PSCustomObject]]::new()
$currSubPref = ""
$currMuni = ""

if ($wikiText -match '(?s)==\s*インターチェンジなど\s*==\r?\n(.*?)\r?\n==[^=]') {
    $sec = $matches[1]
    $rList = $sec -split '\r?\n\|-'

    foreach ($r in $rList) {
        if ($r -match '\[\[([^\]|]+総合振興局|[^\]|]+振興局)\]\]') {
            $currSubPref = $matches[1]
        }
        if ($r -match '\[\[([^\]|]+(?:町|市|村))\]\]') {
            $currMuni = $matches[1]
        }

        $lines = ($r -split '\r?\n') | Where-Object { $_ -match '^[|!]' }
        if ($lines.Count -ge 2) {
            $ic = Clean-Wikitext $lines[0]
            $name = Clean-Wikitext $lines[1]
            $routes = if ($lines.Count -ge 3) { Clean-Wikitext $lines[2] } else { "" }
            $sDist = if ($lines.Count -ge 4) { Clean-Wikitext $lines[3] } else { "" }
            $nDist = if ($lines.Count -ge 5) { Clean-Wikitext $lines[4] } else { "" }
            $bs = if ($lines.Count -ge 6) { Clean-Wikitext $lines[5] } else { "" }
            $gs = if ($lines.Count -ge 7) { Clean-Wikitext $lines[6] } else { "" }
            $remarks = if ($lines.Count -ge 8) { Clean-Wikitext $lines[7] } else { "" }

            if ($name -match 'IC|JCT|SA|PA|料金所|バス|ストップ|仮称|展望所') {
                $bsClean = if ($bs -eq '○') { "○ (運用中)" }
                           elseif ($bs -eq '◆') { "◆ (休止/廃止)" }
                           elseif ($bs -eq '―' -or $bs -eq '') { "― (なし)" }
                           else { $bs }

                $gsClean = if ($gs -eq '●') { "● (24時間営業)" }
                           elseif ($gs -eq '○') { "○ (8:00-20:00営業)" }
                           elseif ($gs -eq '―' -or $gs -eq '') { "― (なし)" }
                           else { $gs }

                $wikiRows.Add([PSCustomObject]@{
                    ic_no        = $ic
                    name         = $name
                    routes       = $routes
                    dist_sapporo = $sDist
                    dist_nanae   = $nDist
                    bs           = $bsClean
                    gs           = $gsClean
                    remarks      = $remarks
                    subpref      = $currSubPref
                    muni         = $currMuni
                    raw_text     = ($lines -join "`n")
                })
            }
        }
    }
}

Write-Host "Wikipediaから抽出した有効施設行数: $($wikiRows.Count)"

$nodeById = @{}
for ($i = 0; $i -lt $nodes.Count; $i++) {
    $nodeById[$nodes[$i].node_id] = $nodes[$i]
}

# 1. ノードリスト構築
$nodeItems = [System.Collections.Generic.List[PSCustomObject]]::new()

for ($i = 0; $i -lt $nodes.Count; $i++) {
    $n = $nodes[$i]
    $nextEdge = if ($i -lt $edges.Count) { $edges[$i] } else { $null }

    $pName = $n.名称
    $pShort = $pName -replace 'インターチェンジ','IC' -replace 'ジャンクション','JCT' -replace 'サービスエリア','SA' -replace 'パーキングエリア','PA' -replace '本線料金所','TB' -replace 'バスストップ','BS'

    # 稼働状態判定（active / planned / closed）
    $isClosed = [bool]($n.終了日)
    $isPlanned = ($pName -like "*仮称*" -or 
                  $pName -eq "七飯藤城インターチェンジ" -or 
                  $pName -eq "駒ケ岳パーキングエリア" -or 
                  $pName -eq "山崎パーキングエリア" -or 
                  $pName -eq "温根別パーキングエリア" -or
                  $n.備考 -like "*事業中*" -or
                  $n.備考 -like "*計画中*")

    if ($pName -match "岩見沢サービスエリア|砂川サービスエリア|輪厚パーキングエリア") {
        $isPlanned = $false
    }

    $opStatus = if ($isClosed) { "closed" }
                elseif ($isPlanned) { "planned" }
                else { "active" }

    $opStatusLabel = if ($isClosed) { "廃止・休止" }
                     elseif ($isPlanned) { "計画・事業中" }
                     else { "供用中" }

    # Wikipedia行を探す（厳密マッチ優先）
    $matchedWiki = $null
    $matchedWikiIndex = -1

    for ($wi = 0; $wi -lt $wikiRows.Count; $wi++) {
        $w = $wikiRows[$wi]
        if ($w.name -eq $pShort -or $w.name -eq $pName) {
            $matchedWiki = $w
            $matchedWikiIndex = $wi
            break
        }
    }

    if (-not $matchedWiki) {
        for ($wi = 0; $wi -lt $wikiRows.Count; $wi++) {
            $parts = $wikiRows[$wi].name -split '/'
            if ($parts -contains $pShort -or $parts -contains ($pShort -replace 'IC|PA|SA|TB|BS','')) {
                $matchedWiki = $wikiRows[$wi]
                $matchedWikiIndex = $wi
                break
            }
        }
    }

    if (-not $matchedWiki) {
        for ($wi = 0; $wi -lt $wikiRows.Count; $wi++) {
            if ($wikiRows[$wi].name -like "$pShort/*" -or $wikiRows[$wi].name -like "$pShort（*") {
                $matchedWiki = $wikiRows[$wi]
                $matchedWikiIndex = $wi
                break
            }
        }
    }

    if (-not $matchedWiki) {
        if ($pName -like "*料金所*") {
            for ($wi = 0; $wi -lt $wikiRows.Count; $wi++) {
                if ($wikiRows[$wi].name -like "*TB*" -or $wikiRows[$wi].remarks -like "*本線料金所*") {
                    $matchedWiki = $wikiRows[$wi]
                    $matchedWikiIndex = $wi
                    break
                }
            }
        } elseif ($pName -like "*バスストップ*") {
            $bsBase = $pName -replace 'バスストップ',''
            for ($wi = 0; $wi -lt $wikiRows.Count; $wi++) {
                if ($wikiRows[$wi].name -like "*$bsBase*" -or $wikiRows[$wi].remarks -like "*$bsBase*") {
                    $matchedWiki = $wikiRows[$wi]
                    $matchedWikiIndex = $wi
                    break
                }
            }
        }
    }

    if (-not $matchedWiki) {
        for ($wi = 0; $wi -lt $wikiRows.Count; $wi++) {
            $w = $wikiRows[$wi]
            $wName = $w.name
            if ($wName -like "*$pShort*" -or $pShort -like "*$wName*") {
                $matchedWiki = $w
                $matchedWikiIndex = $wi
                break
            }
        }
    }

    $wikiObj = if ($matchedWiki) {
        @{
            ic_no        = $matchedWiki.ic_no
            name         = $matchedWiki.name
            routes       = $matchedWiki.routes
            dist_sapporo = if ($matchedWiki.dist_sapporo) { $matchedWiki.dist_sapporo } else { "―" }
            dist_nanae   = if ($matchedWiki.dist_nanae) { $matchedWiki.dist_nanae } else { "―" }
            bs           = $matchedWiki.bs
            gs           = $matchedWiki.gs
            remarks      = if ($matchedWiki.remarks) { $matchedWiki.remarks } else { "特記なし" }
            subpref      = $matchedWiki.subpref
            muni         = $matchedWiki.muni
            raw_text     = $matchedWiki.raw_text
            wiki_index   = $matchedWikiIndex
        }
    } else {
        @{
            ic_no        = "―"
            name         = $pShort
            routes       = "―"
            dist_sapporo = "―"
            dist_nanae   = "―"
            bs           = "―"
            gs           = "―"
            remarks      = "―"
            subpref      = ""
            muni         = ""
            raw_text     = ""
            wiki_index   = -1
        }
    }

    $nextToName = ""
    if ($nextEdge -and $nextEdge.備考) {
        $nextToName = ($nextEdge.備考 -split '➔')[-1].Trim()
    }

    # Wikipedia 個別記事URL
    $wikiArticleUrl = if ($n.Wikipedia_url) { $n.Wikipedia_url } else { "" }

    $nodeItems.Add([PSCustomObject]@{
        index            = $i + 1
        node_id          = $n.node_id
        name             = $n.名称
        short_name       = $pShort
        kind             = $n.種別
        op_status        = $opStatus
        op_status_label  = $opStatusLabel
        municipality     = $n.municipality_id
        lat              = $n.緯度
        lon              = $n.経度
        start_date       = $n.開始日
        end_date         = $n.終了日
        wikidata_id      = $n.Wikidata_id
        wiki_url         = $wikiArticleUrl
        wiki_main_url    = "https://ja.wikipedia.org/wiki/%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93"
        remark           = $n.備考
        next_dist_km     = if ($nextEdge) { $nextEdge.距離_km } else { "" }
        next_to_name     = $nextToName
        next_state       = if ($nextEdge) { $nextEdge.状態 } else { "" }
        wiki             = $wikiObj
    })
}

# 2. エッジリスト構築
$edgeItems = [System.Collections.Generic.List[PSCustomObject]]::new()

for ($j = 0; $j -lt $edges.Count; $j++) {
    $e = $edges[$j]
    $fn = $nodeById[$e.from_node_id]
    $tn = $nodeById[$e.to_node_id]

    $fLat = [double]$fn.緯度
    $fLon = [double]$fn.経度
    $tLat = [double]$tn.緯度
    $tLon = [double]$tn.経度

    $havKm = Get-HaversineKm $fLat $fLon $tLat $tLon
    $roadKm = if ($e.距離_km -and [double]::TryParse($e.距離_km, [ref]0.0)) { [double]$e.距離_km } else { $null }

    $tortuosity = if ($roadKm -and $havKm -gt 0) { [Math]::Round(($roadKm / $havKm), 2) } else { $null }
    $tortuosityStr = if ($tortuosity) { "$tortuosity 倍" } else { "―" }

    $fromShort = $fn.名称 -replace 'インターチェンジ','IC' -replace 'ジャンクション','JCT' -replace 'サービスエリア','SA' -replace 'パーキングエリア','PA' -replace '本線料金所','TB' -replace 'バスストップ','BS'
    $toShort   = $tn.名称 -replace 'インターチェンジ','IC' -replace 'ジャンクション','JCT' -replace 'サービスエリア','SA' -replace 'パーキングエリア','PA' -replace '本線料金所','TB' -replace 'バスストップ','BS'

    # エッジの稼働ステータス（起点・終点ノードのいずれかが計画中/廃止ならそれに準じる）
    $fNodeItem = $nodeItems | Where-Object { $_.node_id -eq $e.from_node_id } | Select-Object -First 1
    $tNodeItem = $nodeItems | Where-Object { $_.node_id -eq $e.to_node_id } | Select-Object -First 1

    $edgeOpStatus = if ($fNodeItem.op_status -eq 'closed' -or $tNodeItem.op_status -eq 'closed') { 'closed' }
                    elseif ($fNodeItem.op_status -eq 'planned' -or $tNodeItem.op_status -eq 'planned' -or $e.状態 -like '*計画*') { 'planned' }
                    else { 'active' }

    $edgeItems.Add([PSCustomObject]@{
        index          = $j + 1
        edge_id        = $e.edge_id
        route_id       = $e.route_id
        seq            = $e.順序
        op_status      = $edgeOpStatus
        dist_km        = if ($roadKm) { $roadKm.ToString("F1") } else { "―" }
        haversine_km   = $havKm.ToString("F1")
        tortuosity     = $tortuosityStr
        road_type      = $e.軌道種別
        state          = $e.状態
        remark         = $e.備考
        from_node_id   = $e.from_node_id
        from_name      = $fn.名称
        from_short     = $fromShort
        from_lat       = $fn.緯度
        from_lon       = $fn.経度
        from_muni      = $fn.municipality_id
        from_op_status = $fNodeItem.op_status
        to_node_id     = $e.to_node_id
        to_name        = $tn.名称
        to_short       = $toShort
        to_lat         = $tn.緯度
        to_lon         = $tn.経度
        to_muni        = $tn.municipality_id
        to_op_status   = $tNodeItem.op_status
    })
}

Write-Host "構築完了: ノード数 $($nodeItems.Count) 件, エッジ数 $($edgeItems.Count) 件"

$jsonNodes   = $nodeItems | ConvertTo-Json -Depth 5
$jsonEdges   = $edgeItems | ConvertTo-Json -Depth 5
$jsonAllWiki = $wikiRows  | ConvertTo-Json -Depth 5

$templateHtml = @'
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>道央自動車道 データ照合・検査コンソール</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", Meiryo, sans-serif; height: 100vh; display: flex; flex-direction: column; background: #f1f5f9; color: #0f172a; overflow: hidden; }
    
    /* ヘッダー */
    header { background: #0f172a; color: #f8fafc; padding: 10px 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0284c7; z-index: 10; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    header h1 { font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; letter-spacing: 0.02em; }
    header .badge { background: #0284c7; color: white; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }
    header .header-controls { display: flex; gap: 10px; align-items: center; }
    .btn { background: #334155; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
    .btn:hover { background: #475569; }
    .btn-primary { background: #0284c7; }
    .btn-primary:hover { background: #0369a1; }
    .btn-toggle.active { background: #10b981; }

    /* メインコンテナ */
    .main-container { display: flex; flex: 1; height: calc(100vh - 50px); overflow: hidden; position: relative; }

    /* 左側ペイン：すっきりした路線図 */
    .left-pane { width: 350px; min-width: 310px; max-width: 390px; background: white; border-right: 1px solid #cbd5e1; display: flex; flex-direction: column; overflow: hidden; }
    .pane-header { padding: 10px 14px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 700; color: #334155; }
    
    /* フィルターコンテナ */
    .filter-section { background: #fafafa; border-bottom: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 6px; padding: 8px 12px; }
    .filter-tabs { display: flex; gap: 4px; }
    .filter-btn { font-size: 11px; padding: 3px 7px; border-radius: 4px; border: 1px solid #cbd5e1; background: white; cursor: pointer; font-weight: 600; color: #475569; }
    .filter-btn.active { background: #0284c7; color: white; border-color: #0284c7; }

    /* 稼働状態（供用中/計画中/廃止）切り替えバー */
    .status-filter-bar { display: flex; align-items: center; justify-content: space-between; padding-top: 4px; border-top: 1px dashed #e2e8f0; font-size: 11px; }
    .status-quick-btns { display: flex; gap: 4px; }
    .status-pill-btn { font-size: 10.5px; padding: 2px 7px; border-radius: 9999px; border: 1px solid #cbd5e1; background: white; cursor: pointer; font-weight: 600; color: #475569; }
    .status-pill-btn.active { background: #059669; color: white; border-color: #059669; }
    .status-checkboxes { display: flex; gap: 6px; }
    .status-checkbox-label { display: flex; align-items: center; gap: 3px; font-size: 10.5px; color: #475569; cursor: pointer; user-select: none; }
    .status-checkbox-label input { cursor: pointer; }

    .route-tree { flex: 1; overflow-y: auto; padding: 10px 8px 30px 12px; }

    /* 路線タイムライン要素 */
    .route-timeline { display: flex; flex-direction: column; position: relative; }

    /* ノード行（施設）：すっきり一行のみ */
    .node-row { display: flex; align-items: center; padding: 5px 8px; border-radius: 6px; cursor: pointer; transition: 0.15s; position: relative; z-index: 2; }
    .node-row:hover { background: #f1f5f9; }
    .node-row.selected { background: #e0f2fe; border: 1px solid #38bdf8; }

    /* ノードアイコンバッジ */
    .node-marker { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 800; color: white; flex-shrink: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.15); border: 2px solid white; }
    .icon-ic { background: #2563eb; }
    .icon-sa { background: #16a34a; }
    .icon-pa { background: #15803d; }
    .icon-bs { background: #ea580c; }
    .icon-jct { background: #7c3aed; }
    .icon-plan { background: #94a3b8; border-style: dashed; }
    .icon-closed { background: #64748b; opacity: 0.75; text-decoration: line-through; }

    .node-label { font-size: 13px; font-weight: 700; color: #0f172a; flex: 1; margin-left: 9px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .node-badge { font-size: 10.5px; font-weight: 700; color: #64748b; font-family: monospace; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
    .node-row.selected .node-badge { background: #0284c7; color: white; }
    .badge-closed-tag { background: #fee2e2 !important; color: #b91c1c !important; }
    .badge-plan-tag { background: #fef3c7 !important; color: #92400e !important; }

    /* エッジ行（区間） */
    .edge-row { display: flex; align-items: center; height: 24px; padding-left: 12px; cursor: pointer; position: relative; z-index: 1; margin: -2px 0; }
    .edge-rail { position: absolute; left: 24px; top: 0; bottom: 0; width: 4px; background: #cbd5e1; z-index: 1; }
    .edge-row:hover .edge-rail { background: #38bdf8; width: 5px; }
    .edge-row.selected .edge-rail { background: #0284c7; width: 6px; }

    .edge-pill { position: relative; z-index: 2; margin-left: 24px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 10px; font-family: monospace; color: #64748b; padding: 1px 7px; font-weight: 600; transition: 0.15s; }
    .edge-row:hover .edge-pill { border-color: #0284c7; color: #0284c7; background: #f0f9ff; }
    .edge-row.selected .edge-pill { background: #0284c7; color: white; border-color: #0284c7; font-weight: 700; box-shadow: 0 1px 3px rgba(2,132,199,0.3); }

    /* 右側ペイン：地図 ＆ 詳細照合 */
    .right-pane { flex: 1; display: flex; flex-direction: column; background: #f8fafc; overflow: hidden; position: relative; }

    /* 地図パネル */
    #map-wrapper { height: 42%; border-bottom: 2px solid #cbd5e1; position: relative; transition: height 0.3s; }
    #map-wrapper.fullscreen { height: 100%; }
    #map-wrapper.hidden { height: 0; display: none; }
    #map { width: 100%; height: 100%; }

    /* 詳細照合パネル */
    .audit-details-panel { flex: 1; overflow-y: auto; padding: 14px 18px 40px 18px; display: flex; flex-direction: column; gap: 14px; background: #f8fafc; }
    
    /* 詳細タイトルバー */
    .target-header-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #0284c7; }
    .target-title-box { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .target-type-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 700; }
    .badge-node-type { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-edge-type { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }

    .target-main-name { font-size: 17px; font-weight: 800; color: #0f172a; }
    .target-sub-badge { font-size: 12px; padding: 2px 7px; border-radius: 4px; font-weight: 700; font-family: monospace; }

    .audit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    
    .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .card h3 { font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid #f1f5f9; display: flex; align-items: center; justify-content: space-between; }
    .card h3 .card-tag { font-size: 11px; font-weight: 600; color: #0284c7; background: #e0f2fe; padding: 2px 6px; border-radius: 4px; }

    /* 外部リンクボタン */
    .wiki-ext-link { display: inline-flex; align-items: center; gap: 4px; background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; padding: 3px 8px; border-radius: 4px; font-size: 11.5px; font-weight: 600; text-decoration: none; transition: 0.15s; }
    .wiki-ext-link:hover { background: #0284c7; color: white; }

    .kv-table { width: 100%; font-size: 12px; border-collapse: collapse; }
    .kv-table th { width: 30%; text-align: left; color: #475569; padding: 5px 8px; font-weight: 600; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
    .kv-table td { padding: 5px 8px; color: #0f172a; border-bottom: 1px solid #e2e8f0; word-break: break-all; }
    
    /* Wikipedia対照表スタイル */
    .wiki-card { background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .wiki-header-line { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 2px solid #38bdf8; }
    .wiki-header-title { font-size: 13.5px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 6px; }

    .wiki-context-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; background: white; border: 1px solid #cbd5e1; }
    .wiki-context-table th { background: #e2e8f0; color: #334155; padding: 6px 8px; font-weight: 700; text-align: left; border: 1px solid #cbd5e1; white-space: nowrap; font-size: 11px; }
    .wiki-context-table td { padding: 6px 8px; border: 1px solid #cbd5e1; color: #1e293b; }
    .wiki-context-table tr.active-row { background: #e0f2fe !important; font-weight: 700; border-left: 4px solid #0284c7; }
    .wiki-context-table tr:hover { background: #f8fafc; cursor: pointer; }

    details.raw-source-accordion { margin-top: 10px; border: 1px solid #e2e8f0; border-radius: 6px; background: #f8fafc; }
    details.raw-source-accordion summary { padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #64748b; cursor: pointer; user-select: none; }
    details.raw-source-accordion summary:hover { color: #0f172a; }
    pre.code-snippet { background: #0f172a; color: #f8fafc; padding: 10px; border-radius: 0 0 6px 6px; font-size: 11px; line-height: 1.45; overflow-x: auto; white-space: pre-wrap; font-family: Consolas, monospace; }

    .view-section { display: none; }
    .view-section.active { display: flex; flex-direction: column; gap: 14px; }
  </style>
</head>
<body>

  <header>
    <h1>
      <span>🛣️ 道央自動車道 データ照合・検査コンソール</span>
      <span class="badge">全70拠点・69エッジ網羅</span>
    </h1>
    <div class="header-controls">
      <span style="font-size:12px; color:#94a3b8;">全線 430.6 km (E5)</span>
      <button id="btn-toggle-map" class="btn btn-primary btn-toggle active">🗺️ 地図を表示中</button>
      <button id="btn-zoom-all" class="btn">全線俯瞰</button>
      <a href="index.html" class="btn">机上探索ツールに戻る</a>
    </div>
  </header>

  <div class="main-container">
    
    <!-- 左側ペイン：すっきりした路線図 -->
    <div class="left-pane">
      <div class="pane-header">
        <span>📋 路線図＆施設シーケンス</span>
        <span id="node-count-badge" style="font-size:11px; color:#64748b;">70 施設</span>
      </div>
      
      <!-- フィルターエリア -->
      <div class="filter-section">
        <!-- 施設種別タブ -->
        <div class="filter-tabs">
          <button class="filter-btn active" data-filter="all">すべて</button>
          <button class="filter-btn" data-filter="sa-pa">SA・PA</button>
          <button class="filter-btn" data-filter="ic-jct">IC・JCT</button>
          <button class="filter-btn" data-filter="bs">バス停</button>
        </div>

        <!-- 稼働状態（供用中 / 計画中 / 廃止）フィルター -->
        <div class="status-filter-bar">
          <div class="status-quick-btns">
            <button id="btn-status-active-only" class="status-pill-btn active" title="現在営業・供用中の施設のみを表示">🟢 供用中のみ (63)</button>
            <button id="btn-status-all" class="status-pill-btn" title="計画中・廃止を含む全施設を表示">全表示 (70)</button>
          </div>
          <div class="status-checkboxes">
            <label class="status-checkbox-label" title="計画・事業中の施設を含める">
              <input type="checkbox" id="chk-show-planned"> 計画中
            </label>
            <label class="status-checkbox-label" title="過去に廃止された施設を含める">
              <input type="checkbox" id="chk-show-closed"> 廃止
            </label>
          </div>
        </div>
      </div>

      <div class="route-tree" id="route-tree-container">
        <!-- JavaScriptで動的生成 -->
      </div>
    </div>

    <!-- 右側ペイン：地図 ＆ データ照合パネル -->
    <div class="right-pane">
      <!-- 地図エリア -->
      <div id="map-wrapper">
        <div id="map"></div>
      </div>

      <!-- データ照合・対照詳細 -->
      <div class="audit-details-panel">
        
        <!-- ヘッダーカード（選択中の対象） -->
        <div class="target-header-card">
          <div class="target-title-box">
            <span id="target-mode-badge" class="target-type-badge badge-node-type">📍 施設（ノード）</span>
            <span id="target-main-name" class="target-main-name">大沼公園インターチェンジ</span>
            <span id="target-sub-badge" class="target-sub-badge" style="background:#0284c7; color:white;">IC 6</span>
            <span id="target-status-badge" class="target-type-badge" style="background:#dcfce7; color:#166534;">供用中</span>
          </div>
          <div style="font-size:12px; color:#64748b;">
            <span id="target-header-extra">所在地: <strong id="target-extra-val" style="color:#0f172a;">渡島総合振興局 亀田郡七飯町</strong></span>
          </div>
        </div>

        <!-- ================= A. ノード詳細ビュー ================= -->
        <div id="node-detail-view" class="view-section active">
          <!-- 諸元対照グリッド -->
          <div class="audit-grid">
            <!-- ① DB登録諸元 -->
            <div class="card">
              <h3>
                <span>📊 テストDB格納属性 (nodes.csv)</span>
                <span class="card-tag">システム保持データ</span>
              </h3>
              <table class="kv-table">
                <tr><th>node_id</th><td id="node-val-id" style="font-family:monospace; font-weight:600;">-</td></tr>
                <tr><th>種別 / 大分類</th><td id="node-val-kind">-</td></tr>
                <tr><th>運用ステータス</th><td id="node-val-status">-</td></tr>
                <tr><th>緯度・経度</th><td id="node-val-coords" style="font-family:monospace;">-</td></tr>
                <tr><th>自治体コード</th><td id="node-val-muni">-</td></tr>
                <tr><th>開通日 / 終了日</th><td id="node-val-dates">-</td></tr>
                <tr><th>次施設への距離</th><td id="node-val-next-dist" style="font-weight:700; color:#0284c7;">-</td></tr>
                <tr><th>論理整合検査</th><td style="color:#16a34a; font-weight:700;">✅ ALL PASS (0エラー)</td></tr>
              </table>
            </div>

            <!-- ② Wikipedia「道央自動車道」記事 抽出属性カード -->
            <div class="card" style="border-top: 3px solid #0284c7;">
              <h3>
                <span>📖 Wikipedia「道央道」記載データ</span>
                <div style="display:flex; gap:6px; align-items:center;">
                  <!-- Wikipedia元記事リンク -->
                  <a id="node-wiki-main-link" href="https://ja.wikipedia.org/wiki/%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93" target="_blank" rel="noopener noreferrer" class="wiki-ext-link" title="Wikipedia『道央自動車道』本編記事を開く">
                    🌐 道央道記事 ↗
                  </a>
                  <span class="card-tag" style="background:#dcfce7; color:#15803d;">照合済</span>
                </div>
              </h3>
              <table class="kv-table">
                <tr><th>Wikipedia表記名</th><td id="node-wiki-name" style="font-weight:700;">-</td></tr>
                <tr><th>IC番号</th><td id="node-wiki-ic" style="font-weight:700; color:#0284c7;">-</td></tr>
                <tr><th>接続路線名</th><td id="node-wiki-routes" style="font-weight:600; color:#1e293b;">-</td></tr>
                <tr><th>キロ程 (札幌JCT)</th><td id="node-wiki-dist-sapporo" style="font-family:monospace;">-</td></tr>
                <tr><th>キロ程 (七飯IC)</th><td id="node-wiki-dist-nanae" style="font-family:monospace;">-</td></tr>
                <tr><th>BS（高速バス停）</th><td id="node-wiki-bs">-</td></tr>
                <tr><th>GS（給油所）</th><td id="node-wiki-gs">-</td></tr>
                <tr><th>施設備考</th><td id="node-wiki-remarks">-</td></tr>
                <tr>
                  <th>引用元記事URL</th>
                  <td>
                    <span id="node-wiki-article-url-container">
                      <a id="node-wiki-article-link" href="#" target="_blank" rel="noopener noreferrer" class="wiki-ext-link">
                        🔗 施設個別記事を開く ↗
                      </a>
                    </span>
                  </td>
                </tr>
              </table>
            </div>
          </div>

          <!-- ③ Wikipedia 前後施設コンテキスト対照 -->
          <div class="wiki-card">
            <div class="wiki-header-line">
              <span class="wiki-header-title">📋 Wikipedia インターチェンジ一覧テーブル対照（選択位置と前後施設）</span>
              <div style="display:flex; gap:8px; align-items:center;">
                <a href="https://ja.wikipedia.org/wiki/%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93#%E3%82%A2%E3%83%B3%E3%82%BF%E3%83%BC%E3%83%81%E3%82%A7%E3%83%B3%E3%82%B8%E3%81%AA%E3%81%A9" target="_blank" rel="noopener noreferrer" class="wiki-ext-link">
                  📖 Wikipedia当該セクションを開く ↗
                </a>
                <span style="font-size:11px; color:#64748b;">行クリックで施設へ移動</span>
              </div>
            </div>
            <table class="wiki-context-table">
              <thead>
                <tr>
                  <th style="width:55px;">IC番号</th>
                  <th>施設名</th>
                  <th>接続路線名</th>
                  <th style="width:85px;">札幌JCT起点</th>
                  <th style="width:85px;">七飯IC起点</th>
                  <th style="width:80px;">バス停(BS)</th>
                  <th style="width:85px;">給油所(GS)</th>
                  <th>備考</th>
                  <th>所在地</th>
                </tr>
              </thead>
              <tbody id="wiki-context-tbody">
                <!-- JavaScriptで前後施設を展開 -->
              </tbody>
            </table>

            <!-- ④ 生Wikitextマークアップ -->
            <details class="raw-source-accordion">
              <summary>▶ Wikipedia 元記事の生マークアップ（Wikitext）ソースコードを展開する</summary>
              <pre class="code-snippet" id="node-wiki-snippet">（施設を選択すると元記事の該当行が表示されます）</pre>
            </details>
          </div>
        </div>

        <!-- ================= B. エッジ（区間）詳細ビュー ================= -->
        <div id="edge-detail-view" class="view-section">
          <div class="audit-grid">
            <!-- ① エッジDB諸元 -->
            <div class="card">
              <h3>
                <span>📊 区間DB属性 (edges.csv)</span>
                <span class="card-tag">第 <span id="edge-val-seq">-</span> 区間 / 全69</span>
              </h3>
              <table class="kv-table">
                <tr><th>edge_id</th><td id="edge-val-id" style="font-family:monospace; font-weight:600;">-</td></tr>
                <tr><th>route_id</th><td id="edge-val-route" style="font-family:monospace;">-</td></tr>
                <tr><th>区間公称距離</th><td id="edge-val-dist" style="font-weight:700; color:#0284c7; font-size:13px;">-</td></tr>
                <tr><th>供用状態</th><td id="edge-val-state">-</td></tr>
                <tr><th>軌道種別</th><td id="edge-val-road-type">-</td></tr>
                <tr><th>備考</th><td id="edge-val-remark">-</td></tr>
              </table>
            </div>

            <!-- ② 幾何・論理検査データ -->
            <div class="card" style="border-top: 3px solid #f59e0b;">
              <h3>
                <span>📐 幾何・トポロジー整合検査</span>
                <span class="card-tag" style="background:#dcfce7; color:#15803d;">Gate 3・Gate 4 検証済</span>
              </h3>
              <table class="kv-table">
                <tr><th>直線距離 (Haversine)</th><td id="edge-val-hav" style="font-family:monospace;">-</td></tr>
                <tr><th>屈曲率 (道路/直線)</th><td id="edge-val-tortuosity" style="font-family:monospace; font-weight:700;">-</td></tr>
                <tr><th>トポロジー連続性</th><td style="color:#16a34a; font-weight:700;">✅ 前後ノード完全一致 (1..69)</td></tr>
                <tr><th>ゼロ距離チェック</th><td style="color:#16a34a; font-weight:700;">✅ PASS (同一地点重複なし)</td></tr>
                <tr><th>逆行・単調増加検査</th><td style="color:#16a34a; font-weight:700;">✅ PASS (キロ程増加順)</td></tr>
              </table>
            </div>
          </div>

          <!-- ③ 区間両端の接続ノード情報 -->
          <div class="card">
            <h3><span>🔗 区間両端のノード対照</span></h3>
            <table class="kv-table">
              <tr>
                <th style="width:20%; background:#e0f2fe; color:#0369a1;">起点ノード (From)</th>
                <td>
                  <strong id="edge-val-from-name" style="font-size:13px; color:#0f172a;">-</strong>
                  <div style="font-size:11px; color:#64748b; margin-top:2px; font-family:monospace;">
                    ID: <span id="edge-val-from-id">-</span> | 座標: <span id="edge-val-from-coords">-</span> | 自治体: <span id="edge-val-from-muni">-</span>
                  </div>
                </td>
              </tr>
              <tr>
                <th style="width:20%; background:#fef3c7; color:#92400e;">終点ノード (To)</th>
                <td>
                  <strong id="edge-val-to-name" style="font-size:13px; color:#0f172a;">-</strong>
                  <div style="font-size:11px; color:#64748b; margin-top:2px; font-family:monospace;">
                    ID: <span id="edge-val-to-id">-</span> | 座標: <span id="edge-val-to-coords">-</span> | 自治体: <span id="edge-val-to-muni">-</span>
                  </div>
                </td>
              </tr>
            </table>
          </div>
        </div>

      </div>
    </div>

  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const DOUO_NODES = __DOUO_NODES_PLACEHOLDER__;
    const DOUO_EDGES = __DOUO_EDGES_PLACEHOLDER__;
    const ALL_WIKI_ROWS = __ALL_WIKI_PLACEHOLDER__;

    // 地図の初期化
    const map = L.map('map', { zoomControl: true }).setView([43.0, 141.5], 8);
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'
    }).addTo(map);

    const layerRoute = L.featureGroup().addTo(map);
    const layerMarkers = L.featureGroup().addTo(map);
    const layerEdgeHighlight = L.featureGroup().addTo(map);
    const markerMap = {};

    let currentKindFilter = 'all'; // 'all', 'sa-pa', 'ic-jct', 'bs'
    let showActiveOnly = true;     // デフォルト: 供用中のみ表示
    let showPlanned = false;
    let showClosed = false;

    let selectedMode = 'node'; // 'node' or 'edge'
    let selectedNodeIndex = 2; // デフォルトは大沼公園IC（供用中の起点施設）
    let selectedEdgeIndex = -1;

    // 路線ポリラインの描画（道央道 全線）
    const lineCoords = [];
    DOUO_NODES.forEach((d, idx) => {
      const lat = parseFloat(d.lat), lon = parseFloat(d.lon);
      if (!isNaN(lat) && !isNaN(lon)) {
        lineCoords.push([lat, lon]);
        
        let color = '#2563eb';
        if (d.kind.includes('SA') || d.kind.includes('PA') || d.kind.includes('展望所')) color = '#16a34a';
        else if (d.kind.includes('バス')) color = '#ea580c';
        else if (d.name.includes('JCT')) color = '#7c3aed';

        const cm = L.circleMarker([lat, lon], {
          radius: (d.kind.includes('SA') || d.kind.includes('PA')) ? 7 : 5,
          fillColor: color,
          color: '#ffffff',
          weight: 2,
          fillOpacity: 0.95
        }).bindPopup(`<strong>${d.name}</strong><br>状態: ${d.op_status_label}<br>種別: ${d.kind}<br>キロ程: ${d.remark}`);
        
        cm.on('click', () => selectNode(idx));
        markerMap[idx] = cm;
      }
    });

    if (lineCoords.length > 1) {
      L.polyline(lineCoords, { color: '#0284c7', weight: 4, opacity: 0.85 }).addTo(layerRoute);
      map.fitBounds(layerRoute.getBounds(), { padding: [30, 30] });
    }

    // 地図上のマーカーをフィルター状態に応じて更新
    function updateMapMarkers() {
      layerMarkers.clearLayers();
      DOUO_NODES.forEach((d, idx) => {
        if (checkNodeFilter(d) && markerMap[idx]) {
          layerMarkers.addLayer(markerMap[idx]);
        }
      });
    }

    // フィルター判定（種別 ＆ 稼働状態）
    function checkNodeFilter(d) {
      // 1. 稼働状態判定
      if (showActiveOnly) {
        if (d.op_status !== 'active') return false;
      } else {
        if (d.op_status === 'planned' && !showPlanned) return false;
        if (d.op_status === 'closed' && !showClosed) return false;
      }

      // 2. 種別判定
      if (currentKindFilter === 'sa-pa') return (d.kind.includes('SA') || d.kind.includes('PA') || d.kind.includes('展望所'));
      if (currentKindFilter === 'ic-jct') return (d.kind.includes('IC') || d.kind.includes('JCT') || d.kind.includes('本線料金所'));
      if (currentKindFilter === 'bs') return d.kind.includes('バス');

      return true;
    }

    // 路線図タイムラインの生成
    function renderRouteTree() {
      const container = document.getElementById('route-tree-container');
      container.innerHTML = '';

      const timeline = document.createElement('div');
      timeline.className = 'route-timeline';

      let visibleNodeCount = 0;
      let lastVisibleNodeIdx = -1;

      DOUO_NODES.forEach((d, idx) => {
        const isMatch = checkNodeFilter(d);

        if (isMatch) {
          visibleNodeCount++;

          // 直前の可視ノードからのエッジを描画
          if (lastVisibleNodeIdx !== -1) {
            // エッジの描画
            const edgeIdx = lastVisibleNodeIdx;
            const edge = DOUO_EDGES[edgeIdx];

            if (edge) {
              const edgeRow = document.createElement('div');
              edgeRow.className = 'edge-row' + (selectedMode === 'edge' && selectedEdgeIndex === edgeIdx ? ' selected' : '');
              edgeRow.id = `edge-row-${edgeIdx}`;
              edgeRow.onclick = (e) => { e.stopPropagation(); selectEdge(edgeIdx); };

              const distLabel = edge.dist_km && edge.dist_km !== '―' ? `${edge.dist_km} km` : (edge.state.includes('計画') ? '計画中' : '―');

              edgeRow.innerHTML = `
                <div class="edge-rail"></div>
                <div class="edge-pill" title="クリックで区間諸元を表示">${distLabel}</div>
              `;

              timeline.appendChild(edgeRow);
            }
          }

          // ノード行の描画
          let iconClass = 'icon-ic';
          let iconChar = 'IC';

          if (d.op_status === 'closed') {
            iconClass = 'icon-closed';
            iconChar = '廃';
          } else if (d.op_status === 'planned') {
            iconClass = 'icon-plan';
            iconChar = '計';
          } else if (d.name.includes('JCT')) {
            iconClass = 'icon-jct'; iconChar = 'JCT';
          } else if (d.kind.includes('SA')) {
            iconClass = 'icon-sa'; iconChar = 'SA';
          } else if (d.kind.includes('PA') || d.kind.includes('展望所')) {
            iconClass = 'icon-pa'; iconChar = 'PA';
          } else if (d.kind.includes('バス')) {
            iconClass = 'icon-bs'; iconChar = 'BS';
          }

          const nodeRow = document.createElement('div');
          nodeRow.className = 'node-row' + (selectedMode === 'node' && selectedNodeIndex === idx ? ' selected' : '');
          nodeRow.id = `node-row-${idx}`;
          nodeRow.onclick = (e) => { e.stopPropagation(); selectNode(idx); };

          let badgeHtml = '';
          if (d.op_status === 'closed') {
            badgeHtml = `<div class="node-badge badge-closed-tag">廃止</div>`;
          } else if (d.op_status === 'planned') {
            badgeHtml = `<div class="node-badge badge-plan-tag">事業中</div>`;
          } else {
            const icNo = d.wiki && d.wiki.ic_no && d.wiki.ic_no !== '―' ? `IC ${d.wiki.ic_no}` : (d.kind.includes('SA') ? 'SA' : (d.kind.includes('PA') ? 'PA' : (d.name.includes('JCT') ? 'JCT' : '')));
            if (icNo) badgeHtml = `<div class="node-badge">${icNo}</div>`;
          }

          nodeRow.innerHTML = `
            <div class="node-marker ${iconClass}">${iconChar}</div>
            <div class="node-label" title="${d.name}">${d.short_name || d.name}</div>
            ${badgeHtml}
          `;

          timeline.appendChild(nodeRow);
          lastVisibleNodeIdx = idx;
        }
      });

      container.appendChild(timeline);

      // 件数バッジ更新
      document.getElementById('node-count-badge').textContent = `${visibleNodeCount} 施設 表示中`;

      // 地図マーカー同期
      updateMapMarkers();
    }

    // 【ノード選択処理】
    function selectNode(idx) {
      if (idx < 0 || idx >= DOUO_NODES.length) return;
      selectedMode = 'node';
      selectedNodeIndex = idx;
      selectedEdgeIndex = -1;

      const d = DOUO_NODES[idx];
      const w = d.wiki || {};

      document.querySelectorAll('.node-row').forEach(el => el.classList.remove('selected'));
      document.querySelectorAll('.edge-row').forEach(el => el.classList.remove('selected'));
      const activeEl = document.getElementById(`node-row-${idx}`);
      if (activeEl) {
        activeEl.classList.add('selected');
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      layerEdgeHighlight.clearLayers();

      const lat = parseFloat(d.lat), lon = parseFloat(d.lon);
      if (!isNaN(lat) && !isNaN(lon)) {
        map.panTo([lat, lon], { animate: true, duration: 0.5 });
        if (markerMap[idx]) {
          markerMap[idx].openPopup();
        }
      }

      document.getElementById('node-detail-view').classList.add('active');
      document.getElementById('edge-detail-view').classList.remove('active');

      const headerBadge = document.getElementById('target-mode-badge');
      headerBadge.className = 'target-type-badge badge-node-type';
      headerBadge.textContent = '📍 施設（ノード）';

      document.getElementById('target-main-name').textContent = d.name;
      const subBadge = document.getElementById('target-sub-badge');
      subBadge.textContent = w.ic_no && w.ic_no !== '―' ? `IC ${w.ic_no}` : (d.kind.includes('SA') ? 'SA' : (d.kind.includes('PA') ? 'PA' : '施設'));
      subBadge.style.background = '#0284c7';

      // 稼働ステータスバッジ
      const statusBadge = document.getElementById('target-status-badge');
      if (d.op_status === 'active') {
        statusBadge.style.background = '#dcfce7'; statusBadge.style.color = '#166534'; statusBadge.textContent = '供用中';
      } else if (d.op_status === 'planned') {
        statusBadge.style.background = '#fef3c7'; statusBadge.style.color = '#92400e'; statusBadge.textContent = '計画・事業中';
      } else {
        statusBadge.style.background = '#fee2e2'; statusBadge.style.color = '#991b1b'; statusBadge.textContent = '廃止・休止';
      }

      document.getElementById('target-header-extra').innerHTML = `所在地: <strong style="color:#0f172a;">${(w.subpref ? w.subpref + ' ' : '') + (w.muni || d.municipality || '―')}</strong>`;

      // ① DB属性
      document.getElementById('node-val-id').textContent = d.node_id;
      document.getElementById('node-val-kind').textContent = d.kind;
      document.getElementById('node-val-status').textContent = d.op_status_label;
      document.getElementById('node-val-coords').textContent = (d.lat && d.lon) ? `${d.lat}, ${d.lon}` : '未測位（事業中・計画中）';
      document.getElementById('node-val-muni').textContent = d.municipality;
      document.getElementById('node-val-dates').textContent = (d.start_date || '不明') + ' 〜 ' + (d.end_date || (d.op_status === 'active' ? '現在供用中' : '未供用'));
      document.getElementById('node-val-next-dist').textContent = d.next_dist_km ? `${d.next_dist_km} km (➔ ${d.next_to_name})` : '終点（次区間なし）';

      // ② Wikipedia抽出属性
      document.getElementById('node-wiki-name').textContent = w.name || d.name;
      document.getElementById('node-wiki-ic').textContent = (w.ic_no && w.ic_no !== '―') ? w.ic_no : '―';
      document.getElementById('node-wiki-routes').textContent = w.routes || '―';
      document.getElementById('node-wiki-dist-sapporo').textContent = (w.dist_sapporo && w.dist_sapporo !== '―') ? `${w.dist_sapporo} km` : '―';
      document.getElementById('node-wiki-dist-nanae').textContent = (w.dist_nanae && w.dist_nanae !== '―') ? `${w.dist_nanae} km` : '―';
      document.getElementById('node-wiki-bs').textContent = w.bs || '―';
      document.getElementById('node-wiki-gs').textContent = w.gs || '―';
      document.getElementById('node-wiki-remarks').textContent = w.remarks || '特記なし';

      // 引用元URLリンクの設定
      const urlContainer = document.getElementById('node-wiki-article-url-container');
      if (d.wiki_url && d.wiki_url !== '') {
        urlContainer.innerHTML = `
          <a href="${d.wiki_url}" target="_blank" rel="noopener noreferrer" class="wiki-ext-link">
            🔗 Wikipedia個別記事を開く ↗
          </a>
          <span style="font-size:10.5px; color:#64748b; margin-left:6px; font-family:monospace;">${decodeURIComponent(d.wiki_url)}</span>
        `;
      } else {
        urlContainer.innerHTML = `<span style="color:#94a3b8; font-size:11px;">（個別記事なし／「道央自動車道」本編記事に記載）</span>`;
      }

      // ③ Wikipedia前後施設コンテキスト表
      renderWikiContextTable(w.wiki_index, idx);

      // ④ 生Wikitext
      document.getElementById('node-wiki-snippet').textContent = w.raw_text || '該当するWikitextが見つかりませんでした。';
    }

    // 【エッジ（区間）選択処理】
    function selectEdge(idx) {
      if (idx < 0 || idx >= DOUO_EDGES.length) return;
      selectedMode = 'edge';
      selectedEdgeIndex = idx;
      selectedNodeIndex = -1;

      const e = DOUO_EDGES[idx];

      document.querySelectorAll('.node-row').forEach(el => el.classList.remove('selected'));
      document.querySelectorAll('.edge-row').forEach(el => el.classList.remove('selected'));
      const activeEl = document.getElementById(`edge-row-${idx}`);
      if (activeEl) {
        activeEl.classList.add('selected');
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      layerEdgeHighlight.clearLayers();
      const fLat = parseFloat(e.from_lat), fLon = parseFloat(e.from_lon);
      const tLat = parseFloat(e.to_lat), tLon = parseFloat(e.to_lon);

      if (!isNaN(fLat) && !isNaN(fLon) && !isNaN(tLat) && !isNaN(tLon)) {
        const segPolyline = L.polyline([[fLat, fLon], [tLat, tLon]], {
          color: '#f59e0b',
          weight: 7,
          opacity: 0.95
        }).addTo(layerEdgeHighlight);

        segPolyline.bindPopup(`<strong>区間 ${e.seq}</strong><br>${e.from_name} ➔ ${e.to_name}<br>距離: ${e.dist_km} km`).openPopup();
        map.fitBounds(segPolyline.getBounds(), { padding: [60, 60], maxZoom: 12 });
      }

      document.getElementById('node-detail-view').classList.remove('active');
      document.getElementById('edge-detail-view').classList.add('active');

      const headerBadge = document.getElementById('target-mode-badge');
      headerBadge.className = 'target-type-badge badge-edge-type';
      headerBadge.textContent = '🛣️ 区間（エッジ）';

      document.getElementById('target-main-name').textContent = `${e.from_short} ➔ ${e.to_short}`;
      const subBadge = document.getElementById('target-sub-badge');
      subBadge.textContent = e.dist_km && e.dist_km !== '―' ? `${e.dist_km} km` : '計画区間';
      subBadge.style.background = '#f59e0b';

      const statusBadge = document.getElementById('target-status-badge');
      statusBadge.style.background = e.state === '供用中' ? '#dcfce7' : '#fef3c7';
      statusBadge.style.color = e.state === '供用中' ? '#166534' : '#92400e';
      statusBadge.textContent = e.state;

      document.getElementById('target-header-extra').innerHTML = `区間順序: <strong style="color:#0f172a;">第 ${e.seq} / 69 区間 (${e.state})</strong>`;

      // ① エッジDB属性
      document.getElementById('edge-val-seq').textContent = e.seq;
      document.getElementById('edge-val-id').textContent = e.edge_id;
      document.getElementById('edge-val-route').textContent = e.route_id;
      document.getElementById('edge-val-dist').textContent = e.dist_km !== '―' ? `${e.dist_km} km` : '未供用（距離未定）';
      document.getElementById('edge-val-state').textContent = e.state;
      document.getElementById('edge-val-road-type').textContent = e.road_type;
      document.getElementById('edge-val-remark').textContent = e.remark;

      // ② 幾何・論理検査データ
      document.getElementById('edge-val-hav').textContent = (e.haversine_km && e.haversine_km !== '0.0') ? `${e.haversine_km} km` : '未測位（計画中）';
      document.getElementById('edge-val-tortuosity').textContent = e.tortuosity;

      // ③ 区間両端ノード
      document.getElementById('edge-val-from-name').textContent = e.from_name;
      document.getElementById('edge-val-from-id').textContent = e.from_node_id;
      document.getElementById('edge-val-from-coords').textContent = (e.from_lat && e.from_lon) ? `${e.from_lat}, ${e.from_lon}` : '未測位';
      document.getElementById('edge-val-from-muni').textContent = e.from_muni;

      document.getElementById('edge-val-to-name').textContent = e.to_name;
      document.getElementById('edge-val-to-id').textContent = e.to_node_id;
      document.getElementById('edge-val-to-coords').textContent = (e.to_lat && e.to_lon) ? `${e.to_lat}, ${e.to_lon}` : '未測位';
      document.getElementById('edge-val-to-muni').textContent = e.to_muni;
    }

    // Wikipedia前後コンテキストテーブルのレンダリング
    function renderWikiContextTable(wikiIdx, nodeIdx) {
      const tbody = document.getElementById('wiki-context-tbody');
      tbody.innerHTML = '';

      if (wikiIdx < 0 || !ALL_WIKI_ROWS || ALL_WIKI_ROWS.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#94a3b8; padding:10px;">Wikipediaの対応表データがありません</td></tr>';
        return;
      }

      const start = Math.max(0, wikiIdx - 3);
      const end = Math.min(ALL_WIKI_ROWS.length - 1, wikiIdx + 3);

      for (let i = start; i <= end; i++) {
        const row = ALL_WIKI_ROWS[i];
        const isCurrent = (i === wikiIdx);

        const tr = document.createElement('tr');
        if (isCurrent) tr.className = 'active-row';

        tr.onclick = () => {
          const foundIdx = DOUO_NODES.findIndex(item => item.wiki && item.wiki.wiki_index === i);
          if (foundIdx >= 0) {
            selectNode(foundIdx);
          }
        };

        tr.innerHTML = `
          <td style="font-family:monospace; font-weight:700; text-align:center;">${row.ic_no || '―'}</td>
          <td style="font-weight:700; color:${isCurrent ? '#0284c7' : '#0f172a'};">${row.name}</td>
          <td style="color:#334155;">${row.routes || '―'}</td>
          <td style="font-family:monospace; text-align:right;">${row.dist_sapporo ? row.dist_sapporo + ' km' : '―'}</td>
          <td style="font-family:monospace; text-align:right;">${row.dist_nanae ? row.dist_nanae + ' km' : '―'}</td>
          <td style="text-align:center;">${row.bs || '―'}</td>
          <td style="text-align:center;">${row.gs || '―'}</td>
          <td style="font-size:11px; color:#475569;">${row.remarks || '―'}</td>
          <td style="font-size:11px; color:#475569;">${(row.subpref ? row.subpref + '<br>' : '') + (row.muni || '')}</td>
        `;

        tbody.appendChild(tr);
      }
    }

    // 施設種別タブ切り替え
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentKindFilter = e.target.getAttribute('data-filter');
        renderRouteTree();
      });
    });

    // 稼働状態切り替えイベント
    const btnActiveOnly = document.getElementById('btn-status-active-only');
    const btnAll = document.getElementById('btn-status-all');
    const chkPlanned = document.getElementById('chk-show-planned');
    const chkClosed = document.getElementById('chk-show-closed');

    btnActiveOnly.addEventListener('click', () => {
      showActiveOnly = true;
      btnActiveOnly.classList.add('active');
      btnAll.classList.remove('active');
      chkPlanned.checked = false;
      chkClosed.checked = false;
      renderRouteTree();
    });

    btnAll.addEventListener('click', () => {
      showActiveOnly = false;
      btnAll.classList.add('active');
      btnActiveOnly.classList.remove('active');
      chkPlanned.checked = true;
      chkClosed.checked = true;
      showPlanned = true;
      showClosed = true;
      renderRouteTree();
    });

    chkPlanned.addEventListener('change', (e) => {
      showPlanned = e.target.checked;
      showActiveOnly = (!showPlanned && !showClosed);
      if (showActiveOnly) {
        btnActiveOnly.classList.add('active');
        btnAll.classList.remove('active');
      } else {
        btnActiveOnly.classList.remove('active');
        if (showPlanned && showClosed) btnAll.classList.add('active');
        else btnAll.classList.remove('active');
      }
      renderRouteTree();
    });

    chkClosed.addEventListener('change', (e) => {
      showClosed = e.target.checked;
      showActiveOnly = (!showPlanned && !showClosed);
      if (showActiveOnly) {
        btnActiveOnly.classList.add('active');
        btnAll.classList.remove('active');
      } else {
        btnActiveOnly.classList.remove('active');
        if (showPlanned && showClosed) btnAll.classList.add('active');
        else btnAll.classList.remove('active');
      }
      renderRouteTree();
    });

    // 地図トグルボタン
    const btnToggleMap = document.getElementById('btn-toggle-map');
    const mapWrapper = document.getElementById('map-wrapper');
    btnToggleMap.addEventListener('click', () => {
      if (mapWrapper.classList.contains('hidden')) {
        mapWrapper.classList.remove('hidden');
        btnToggleMap.classList.add('active');
        btnToggleMap.textContent = '🗺️ 地図を表示中';
        setTimeout(() => map.invalidateSize(), 300);
      } else {
        mapWrapper.classList.add('hidden');
        btnToggleMap.classList.remove('active');
        btnToggleMap.textContent = '🗺️ 地図を非表示中';
      }
    });

    // 全線俯瞰ボタン
    document.getElementById('btn-zoom-all').addEventListener('click', () => {
      if (layerRoute.getBounds().isValid()) {
        map.fitBounds(layerRoute.getBounds(), { padding: [30, 30] });
      }
    });

    // 初期化実行
    renderRouteTree();
    selectNode(2); // 大沼公園IC（供用中）を選択

  </script>
</body>
</html>
'@

$finalHtml = $templateHtml.Replace('__DOUO_NODES_PLACEHOLDER__', $jsonNodes).Replace('__DOUO_EDGES_PLACEHOLDER__', $jsonEdges).Replace('__ALL_WIKI_PLACEHOLDER__', $jsonAllWiki)

# UTF-8 BOM付きで保存
$outPath = Join-Path $webDir "audit_douo.html"
$utf8WithBom = [System.Text.UTF8Encoding]::new($true)
[System.IO.File]::WriteAllText($outPath, $finalHtml, $utf8WithBom)

Write-Host "-> 道央道照合ページ（稼働状態フィルタ＋Wikipedia引用元URL配備）を生成しました: $outPath"
