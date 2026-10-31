# fetch_douo_sources.ps1
# 道央自動車道のSA・PAを Wikipedia / Wikidata / OpenStreetMap からテスト取得するスクリプト

$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
if (-not (Test-Path $testDir)) {
    New-Item -ItemType Directory -Force -Path $testDir | Out-Null
}

$headers = @{
    "User-Agent" = "AntigravityHokkaidoPilot/1.0 (test@example.com)"
}

Write-Host "=== 1. Wikipedia API から道央自動車道テーブルを取得中 ==="
$wikiUri = "https://ja.wikipedia.org/w/api.php?action=parse&page=%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93&prop=wikitext&format=json"
try {
    $wikiRes = Invoke-RestMethod -Uri $wikiUri -Headers $headers -Method Get
    $wikitext = $wikiRes.parse.wikitext.'*'
    $wikiPath = Join-Path $testDir "wikipedia_douo_wikitext.txt"
    [System.IO.File]::WriteAllText($wikiPath, $wikitext, [System.Text.Encoding]::UTF8)
    Write-Host "-> Wikipedia取得成功: $wikiPath ($($wikitext.Length) 文字)"
} catch {
    Write-Host "-> Wikipedia取得失敗: $_"
}

Write-Host "`n=== 2. Wikidata SPARQL API から道央道の施設を取得中 ==="
# 道央自動車道(Q1040854)の接続施設、または北海道のSA/PA
$sparqlQuery = @"
SELECT ?item ?itemLabel ?coord ?typeLabel ?routeLabel WHERE {
  ?item wdt:P31 ?type .
  FILTER(?type IN (wd:Q1151600, wd:Q1542475, wd:Q1802963, wd:Q623190)) . # service area, rest area, etc.
  ?item wdt:P131* wd:Q35671 . # located in Hokkaido
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P361 ?route . } # part of route
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ja,en". }
}
"@

$sparqlUri = "https://query.wikidata.org/sparql?query=" + [System.Uri]::EscapeDataString($sparqlQuery)
$sparqlHeaders = @{
    "User-Agent" = "AntigravityHokkaidoPilot/1.0"
    "Accept"     = "application/sparql-results+json"
}

try {
    $wdRes = Invoke-RestMethod -Uri $sparqlUri -Headers $sparqlHeaders -Method Get
    $wdPath = Join-Path $testDir "wikidata_hokkaido_sapa.json"
    $wdRes | ConvertTo-Json -Depth 10 | Set-Content $wdPath -Encoding UTF8
    Write-Host "-> Wikidata取得成功: $wdPath ($($wdRes.results.bindings.Count) 件)"
} catch {
    Write-Host "-> Wikidata取得失敗: $_"
}

Write-Host "`n=== 3. OpenStreetMap Overpass API から道央道のSA/PAを取得中 ==="
# 道央自動車道沿線（北海道中南部〜中央部 BBOX: 41.8 to 44.0, 140.0 to 143.0）の highway=services, highway=rest_area
$overpassQuery = @"
[out:json][timeout:30];
(
  node["highway"~"services|rest_area"](41.8,140.0,44.0,143.0);
  way["highway"~"services|rest_area"](41.8,140.0,44.0,143.0);
  relation["highway"~"services|rest_area"](41.8,140.0,44.0,143.0);
);
out center tags;
"@

$overpassUri = "https://overpass-api.de/api/interpreter"
try {
    $osmRes = Invoke-RestMethod -Uri $overpassUri -Method Post -Body $overpassQuery -Headers $headers -TimeoutSec 45
    $osmPath = Join-Path $testDir "osm_hokkaido_sapa.json"
    $osmRes | ConvertTo-Json -Depth 10 | Set-Content $osmPath -Encoding UTF8
    Write-Host "-> OpenStreetMap取得成功: $osmPath ($($osmRes.elements.Count) 件)"
} catch {
    Write-Host "-> OpenStreetMap取得失敗: $_"
}
