# check_status.ps1
$nodes = Import-Csv "data/test/douo_highway_test/test_all_highway_nodes.csv" -Encoding UTF8
Write-Host "=== 稼働中以外の施設一覧 ==="
foreach ($n in $nodes) {
    $isClosed = ($n.終了日 -ne "")
    $isUnopened = ($n.備考 -like "*計画・事業中*" -or ($n.開始日 -eq "" -and $n.備考 -notlike "*供用中*"))
    
    $status = if ($isClosed) { "廃止・休止" }
              elseif ($isUnopened) { "計画・事業中" }
              else { "供用中" }

    if ($status -ne "供用中") {
        Write-Host ("[{0}] {1,-18} | 状態: {2,-8} | 開始日: {3,-10} | 終了日: {4,-10} | 備考: {5}" -f $n.node_id, $n.名称, $status, $n.開始日, $n.終了日, $n.備考)
    }
}
