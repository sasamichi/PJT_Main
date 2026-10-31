# check_mapping.ps1
$content = [System.IO.File]::ReadAllText("web/explorer/audit_douo.html", [System.Text.Encoding]::UTF8)
if ($content -match '(?s)const DOUO_EDGES = (\[.*?\]);') {
    $edges = $matches[1] | ConvertFrom-Json
    foreach ($e in $edges[3..9]) {
        Write-Host ("Edge {0,2}: {1,-14} -> {2,-14} | 道路: {3,4} km | 直線: {4,4} km | 屈曲率: {5}" -f $e.seq, $e.from_short, $e.to_short, $e.dist_km, $e.haversine_km, $e.tortuosity)
    }
}
