# export_douo_audit_json.ps1
$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
$webDir  = "c:\Users\user\Documents\PJT\web\explorer"

$nodes = Import-Csv (Join-Path $testDir "test_all_highway_nodes.csv") -Encoding UTF8
$edges = Import-Csv (Join-Path $testDir "test_all_highway_edges.csv") -Encoding UTF8
$wikiText = [System.IO.File]::ReadAllText((Join-Path $testDir "wikipedia_douo_wikitext.txt"), [System.Text.Encoding]::UTF8)

$items = [System.Collections.Generic.List[PSCustomObject]]::new()

for ($i = 0; $i -lt $nodes.Count; $i++) {
    $n = $nodes[$i]
    $nextEdge = if ($i -lt $edges.Count) { $edges[$i] } else { $null }

    $pName = $n.名称
    $wikiSnippet = ""
    $lines = $wikiText -split '\r?\n'
    for ($li = 0; $li -lt $lines.Count; $li++) {
        if ($lines[$li] -like "*$pName*" -or ($pName -like "*インターチェンジ*" -and $lines[$li] -like "*$($pName -replace 'インターチェンジ','IC')*")) {
            $start = [Math]::Max(0, $li - 2)
            $end = [Math]::Min($lines.Count - 1, $li + 5)
            $wikiSnippet = ($lines[$start..$end] -join "`n")
            break
        }
    }

    $toName = ""
    if ($nextEdge) {
        $toName = ($nextEdge.備考 -replace '^.*➔\s*', '')
    }

    $items.Add([PSCustomObject]@{
        index         = $i + 1
        node_id       = $n.node_id
        name          = $n.名称
        kind          = $n.種別
        municipality  = $n.municipality_id
        lat           = $n.緯度
        lon           = $n.経度
        start_date    = $n.開始日
        end_date      = $n.終了日
        wikidata_id   = $n.Wikidata_id
        wiki_url      = $n.Wikipedia_url
        remark        = $n.備考
        next_dist_km  = if ($nextEdge) { $nextEdge.距離_km } else { "" }
        next_to_name  = $toName
        next_state    = if ($nextEdge) { $nextEdge.状態 } else { "" }
        wiki_snippet  = $wikiSnippet
    })
}

$jsonPath = Join-Path $webDir "douo_audit_data.json"
$items | ConvertTo-Json -Depth 5 | Set-Content $jsonPath -Encoding UTF8
Write-Host "-> Exported: $jsonPath ($($items.Count) records)"
