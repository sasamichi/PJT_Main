# test_osm_kumi.ps1
$servers = @(
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
)

$ql = "[out:json][timeout:25];(node[""highway""~""services|rest_area""](41.5,139.5,44.5,143.5);way[""highway""~""services|rest_area""](41.5,139.5,44.5,143.5););out center tags;"
$encoded = [System.Uri]::EscapeDataString($ql)

foreach ($srv in $servers) {
    Write-Host "Trying $srv ..."
    try {
        $fullUri = [System.Uri]"$srv?data=$encoded"
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        $jsonStr = $wc.DownloadString($fullUri)
        $res = $jsonStr | ConvertFrom-Json
        Write-Host "Success from $srv ! Elements:" $res.elements.Count
        [System.IO.File]::WriteAllText("data/test/douo_highway_test/osm_hokkaido_sapa.json", $jsonStr, [System.Text.Encoding]::UTF8)
        break
    } catch {
        Write-Host "Failed: $($_.Exception.Message)"
    }
}
