# test_osm_overpass.ps1
$overpassUri = "https://overpass-api.de/api/interpreter"
# Use standard browser User-Agent
$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Search specifically for highway=services OR highway=rest_area in Hokkaido area (around Douo expressway)
$ql = @"
[out:json][timeout:30];
area["ISO3166-2"="JP-01"]->.hokkaido;
(
  node["highway"~"services|rest_area"](area.hokkaido);
  way["highway"~"services|rest_area"](area.hokkaido);
  relation["highway"~"services|rest_area"](area.hokkaido);
);
out center tags;
"@

$body = "data=" + [System.Uri]::EscapeDataString($ql)
try {
    $res = Invoke-RestMethod -Uri $overpassUri -Method Post -Body $body -Headers $headers -ContentType "application/x-www-form-urlencoded"
    Write-Host "Success! Elements count:" $res.elements.Count
    $res | ConvertTo-Json -Depth 10 | Set-Content "data/test/douo_highway_test/osm_hokkaido_sapa.json" -Encoding UTF8
} catch {
    Write-Host "Failed:" $_.Exception.Message
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        Write-Host "Server response:" $reader.ReadToEnd()
    }
}
