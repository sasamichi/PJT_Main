# ==============================================================================
# download_jp_raw_data_part2.ps1
# Download P05 (Municipality Hall coordinates) and Wikidata SPARQL caches
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir = Join-Path $workspaceRoot "data\raw\JP"

function Try-Download($candidates, $outFile, $desc, $headers = @{}) {
    $dest = Join-Path $rawDir $outFile
    if (Test-Path $dest) {
        $len = (Get-Item $dest).Length
        if ($len -gt 1000) {
            Write-Host "[SKIP] $desc already exists ($outFile : $len bytes)"
            return $true
        }
    }
    foreach ($url in $candidates) {
        Write-Host "Trying $desc from: $url"
        try {
            $ua = "AntigravityDataCollector/1.0 (https://github.com/google/antigravity; contact: admin@example.org)"
            Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -TimeoutSec 90 -UserAgent $ua -Headers $headers
            if (Test-Path $dest) {
                $len = (Get-Item $dest).Length
                if ($len -gt 1000) {
                    Write-Host "-> [SUCCESS] $desc downloaded ($outFile : $len bytes)"
                    return $true
                } else {
                    Remove-Item $dest -Force -ErrorAction SilentlyContinue
                }
            }
        } catch {
            Write-Host "   Failed: $($_.Exception.Message)"
        }
    }
    Write-Warning "[FAILED] Could not download $desc from any candidate URL."
    return $false
}

# 1. MLIT KSJ P05 (Municipality halls & public facilities) or P34 (Municipality halls)
$p05Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/P05/P05-22/P05-22_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/P34/P34-14/P34-14_GML.zip"
)
Try-Download $p05Urls "ksj_P05_munihall.zip" "MLIT KSJ Municipality Hall Data (P05/P34)"

# 2. Wikidata SPARQL: Japanese Municipalities/Prefectures/Wards with P475 (6-digit code)
$sparqlMuni = "SELECT ?item ?itemLabel ?lgcode ?coord ?website ?article WHERE { ?item wdt:P475 ?lgcode . FILTER NOT EXISTS { ?item wdt:P576 ?dissolved . } OPTIONAL { ?item wdt:P625 ?coord . } OPTIONAL { ?item wdt:P856 ?website . } OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> . } SERVICE wikibase:label { bd:serviceParam wikibase:language 'ja'. } }"
$wdMuniUrl = "https://query.wikidata.org/sparql?query=" + [uri]::EscapeDataString($sparqlMuni)
Try-Download @($wdMuniUrl) "wikidata_jp_lgcode.json" "Wikidata JP LGCode (P475)" @{"Accept"="application/sparql-results+json"}

# 3. Wikidata SPARQL: Japanese Gun (Counties Q855697) and Subprefectures (Q693138)
$sparqlGun = "SELECT ?item ?itemLabel ?parent ?parentLabel ?coord ?article WHERE { VALUES ?cls { wd:Q855697 wd:Q693138 wd:Q11395466 } ?item wdt:P31/wdt:P279* ?cls . ?item wdt:P17 wd:Q17 . FILTER NOT EXISTS { ?item wdt:P576 ?dissolved . } OPTIONAL { ?item wdt:P131 ?parent . } OPTIONAL { ?item wdt:P625 ?coord . } OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> . } SERVICE wikibase:label { bd:serviceParam wikibase:language 'ja'. } }"
$wdGunUrl = "https://query.wikidata.org/sparql?query=" + [uri]::EscapeDataString($sparqlGun)
Try-Download @($wdGunUrl) "wikidata_jp_gun_subpref.json" "Wikidata JP Counties & Subprefectures" @{"Accept"="application/sparql-results+json"}

# 4. Wikidata SPARQL: Japanese Michi-no-Eki (Roadside stations Q1187691) - latest 1,234 stations
$sparqlMichi = "SELECT DISTINCT ?item ?itemLabel ?coord ?website ?article WHERE { ?item wdt:P31/wdt:P279* wd:Q1187691 . ?item wdt:P17 wd:Q17 . FILTER NOT EXISTS { ?item wdt:P576 ?dissolved . } OPTIONAL { ?item wdt:P625 ?coord . } OPTIONAL { ?item wdt:P856 ?website . } OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> . } SERVICE wikibase:label { bd:serviceParam wikibase:language 'ja'. } }"
$wdMichiUrl = "https://query.wikidata.org/sparql?query=" + [uri]::EscapeDataString($sparqlMichi)
Try-Download @($wdMichiUrl) "wikidata_jp_michinoeki.json" "Wikidata JP Michi-no-Eki" @{"Accept"="application/sparql-results+json"}

# 5. Wikidata SPARQL: Japanese Airports (IATA/ICAO codes)
$sparqlAir = "SELECT DISTINCT ?item ?itemLabel ?iata ?icao ?coord ?website ?article WHERE { ?item wdt:P31/wdt:P279* wd:Q1248784 . ?item wdt:P17 wd:Q17 . FILTER NOT EXISTS { ?item wdt:P576 ?dissolved . } OPTIONAL { ?item wdt:P238 ?iata . } OPTIONAL { ?item wdt:P239 ?icao . } OPTIONAL { ?item wdt:P625 ?coord . } OPTIONAL { ?item wdt:P856 ?website . } OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> . } SERVICE wikibase:label { bd:serviceParam wikibase:language 'ja'. } }"
$wdAirUrl = "https://query.wikidata.org/sparql?query=" + [uri]::EscapeDataString($sparqlAir)
Try-Download @($wdAirUrl) "wikidata_jp_airports.json" "Wikidata JP Airports" @{"Accept"="application/sparql-results+json"}

Write-Host "`n=================================================="
Write-Host " Updated Files in data/raw/JP:"
Get-ChildItem -Path $rawDir | Select-Object Name, Length | Format-Table -AutoSize
Write-Host "=================================================="
