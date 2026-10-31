# test_status_classification.ps1
$nodes = Import-Csv "data/test/douo_highway_test/test_all_highway_nodes.csv" -Encoding UTF8

Write-Host "=== 供用中以外の施設（計画・事業中／廃止・休止） ==="
$closedCount = 0
$plannedCount = 0
$activeCount = 0

for ($i = 0; $i -lt $nodes.Count; $i++) {
    $n = $nodes[$i]
    $name = $n.名称
    
    # 廃止
    $isClosed = [bool]($n.終了日)
    
    # 計画・事業中判定：
    # 七飯藤城IC、七飯IC（仮称）、駒ケ岳PA、山崎PA、温根別PAなど
    $isPlanned = ($name -like "*仮称*" -or 
                  $name -eq "七飯藤城インターチェンジ" -or 
                  $name -eq "駒ケ岳パーキングエリア" -or 
                  $name -eq "山崎パーキングエリア" -or 
                  $name -eq "温根別パーキングエリア" -or
                  $n.備考 -like "*事業中*" -or
                  $n.備考 -like "*計画中*")

    # ただし岩見沢SAや砂川SAなど供用中施設でSICのみ準備段階のものはactive
    if ($name -match "岩見沢サービスエリア|砂川サービスエリア|輪厚パーキングエリア") {
        $isPlanned = $false
    }

    $status = if ($isClosed) { "closed" }
              elseif ($isPlanned) { "planned" }
              else { "active" }

    if ($status -eq "closed") { $closedCount++ }
    elseif ($status -eq "planned") { $plannedCount++ }
    else { $activeCount++ }

    if ($status -ne "active") {
        Write-Host ("[{0,2}] {1,-18} -> 判定: {2,-8} | 開始日: {3,-10} | 終了日: {4,-10}" -f ($i+1), $name, $status, $n.開始日, $n.終了日)
    }
}

Write-Host "`n集計結果:"
Write-Host "供用中 (active): $activeCount 件"
Write-Host "計画・事業中 (planned): $plannedCount 件"
Write-Host "廃止・休止 (closed): $closedCount 件"
Write-Host "合計: $($nodes.Count) 件"
