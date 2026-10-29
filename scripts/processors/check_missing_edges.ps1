[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$nodesCsv = Import-Csv 'c:\Users\user\Documents\PJT\data\staging\JP\nodes.csv' -Encoding UTF8
$airMap = @{}
$portMap = @{}
foreach ($n in $nodesCsv) {
    if ($n.種別 -eq "空港") {
        if ($n.iata_code) { $airMap[$n.iata_code] = $n.node_id }
        $airMap[$n.名称] = $n.node_id
    } elseif ($n.種別 -eq "主要港湾") {
        $cleanP = $n.名称 -replace "港$", ""
        $portMap[$cleanP] = $n.node_id
        $portMap[$n.名称] = $n.node_id
    }
}

# Check missing air
$airCodes = @("HND","CTS","FUK","OKA","ITM","KIX","KOJ","KMJ","HIJ","MYJ","TAK","KMQ","TOY","AXT","KMI","NGS","SDJ","NGO","ISG","MMY")
foreach ($c in $airCodes) {
    if (-not $airMap.ContainsKey($c)) {
        Write-Host "Missing Air code in airMap: $c"
    }
}

# Check missing ferry ports
$ferryPorts = @("舞鶴","小樽","敦賀","苫小牧","新潟","名古屋","仙台","大洗","志布志","大阪","別府","神戸","大分","北九州","泉大津","横須賀","東京","徳島","宮崎","八戸","青森","函館","大間","室蘭","両津","直江津","小木","伊豆大島","二見","木更津","鳥羽","三河","和歌山","高松","新居浜","境港","西郷","鹿児島","那覇","広島","厳島")
foreach ($p in $ferryPorts) {
    if (-not $portMap.ContainsKey($p)) {
        Write-Host "Missing Ferry Port: $p"
    }
}
