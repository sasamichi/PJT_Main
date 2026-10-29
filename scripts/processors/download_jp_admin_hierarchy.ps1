# ==============================================================================
# download_jp_admin_hierarchy.ps1
# Download official standard area codes (including Gun and Subprefectures) to data/raw/JP/
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$rawDir = "c:\Users\user\Documents\PJT\data\raw\JP"

# 1. Geolonia Japanese Addresses / Geoshape / e-Stat Standard Area Codes
$urls = @(
    @{ Url="https://geolonia.github.io/japanese-admins/data.json"; File="geolonia_japanese_admins.json"; Desc="Geolonia Japanese Admins Hierarchy JSON" },
    @{ Url="https://raw.githubusercontent.com/geolonia/japanese-addresses/master/data/latest.csv"; File="geolonia_latest_addresses.csv"; Desc="Geolonia Latest Addresses CSV" },
    @{ Url="https://www.soumu.go.jp/main_content/000925835.xlsx"; File="soumu_code_latest.xlsx"; Desc="Soumu Latest Code Excel" }
)

foreach ($u in $urls) {
    $dest = Join-Path $rawDir $u.File
    Write-Host "Trying $($u.Desc) from: $($u.Url)"
    try {
        Invoke-WebRequest -Uri $u.Url -OutFile $dest -UseBasicParsing -TimeoutSec 60 -UserAgent "Mozilla/5.0"
        if (Test-Path $dest) {
            Write-Host "-> [SUCCESS] $($u.File) : $((Get-Item $dest).Length) bytes"
        }
    } catch {
        Write-Host "   Failed: $($_.Exception.Message)"
    }
}

# 2. Also query Wikidata for all Japanese towns and villages with their P475 code and P131 (parent Gun / Subprefecture)
$sparql = @"
SELECT ?item ?itemLabel ?lgcode ?parent ?parentLabel ?parentCoord ?parentArticle WHERE {
  ?item wdt:P475 ?lgcode .
  FILTER NOT EXISTS { ?item wdt:P576 ?dissolved . }
  ?item wdt:P131 ?parent .
  ?parent wdt:P31/wdt:P279* ?pcls .
  VALUES ?pcls { wd:Q855697 wd:Q693138 wd:Q11395466 }
  FILTER NOT EXISTS { ?parent wdt:P576 ?pdis . }
  OPTIONAL { ?parent wdt:P625 ?parentCoord . }
  OPTIONAL {
    ?parentArticle schema:about ?parent ;
                   schema:isPartOf <https://ja.wikipedia.org/> .
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ja". }
}
"@

$wdUrl = "https://query.wikidata.org/sparql?format=json&query=" + [uri]::EscapeDataString($sparql)
$wdDest = Join-Path $rawDir "wikidata_jp_muni_gun_map.json"
Write-Host "Trying Wikidata Muni->Gun/Subpref mapping..."
try {
    Invoke-WebRequest -Uri $wdUrl -OutFile $wdDest -UseBasicParsing -TimeoutSec 90 -UserAgent "AntigravityCollector/1.0 (https://github.com/google/antigravity)"
    if (Test-Path $wdDest) {
        Write-Host "-> [SUCCESS] wikidata_jp_muni_gun_map.json : $((Get-Item $wdDest).Length) bytes"
    }
} catch {
    Write-Host "   Failed: $($_.Exception.Message)"
}
