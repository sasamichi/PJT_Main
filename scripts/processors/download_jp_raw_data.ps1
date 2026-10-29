# ==============================================================================
# download_jp_raw_data.ps1
# Download official Japanese open data (MLIT KSJ, Geoshape, Wikidata) to data/raw/JP/
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir = Join-Path $workspaceRoot "data\raw\JP"
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

Write-Host "=================================================="
Write-Host " Starting download of JP official raw datasets"
Write-Host "=================================================="

function Try-Download($candidates, $outFile, $desc) {
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
            Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -TimeoutSec 60 -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

# 1. MLIT KSJ: Railway data (N02) - All active railways, trams, monorails, cableways, stations, operators
$n02Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/N02/N02-23/N02-23_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N02/N02-22/N02-22_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N02/N02-24/N02-24_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N02/N02-21/N02-21_GML.zip"
)
Try-Download $n02Urls "ksj_N02_railway.zip" "MLIT KSJ Railway Data (N02)"

# 2. MLIT KSJ: Airport data (C28)
$c28Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/C28/C28-21/C28-21_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/C28/C28-20/C28-20_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/C28/C28-13/C28-13_GML.zip"
)
Try-Download $c28Urls "ksj_C28_airport.zip" "MLIT KSJ Airport Data (C28)"

# 3. MLIT KSJ: Port data (C02)
$c02Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/C02/C02-20/C02-20_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/C02/C02-14/C02-14_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/C02/C02-22/C02-22_GML.zip"
)
Try-Download $c02Urls "ksj_C02_port.zip" "MLIT KSJ Port Data (C02)"

# 4. MLIT KSJ: Ferry route data (N09)
$n09Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/N09/N09-12/N09-12_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N09/N09-20/N09-20_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N09/N09-07/N09-07_GML.zip"
)
Try-Download $n09Urls "ksj_N09_ferry.zip" "MLIT KSJ Ferry Data (N09)"

# 5. MLIT KSJ: Michi-no-Eki data (P35)
$p35Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/P35/P35-18/P35-18_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/P35/P35-23/P35-23_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/P35/P35-22/P35-22_GML.zip"
)
Try-Download $p35Urls "ksj_P35_michinoeki.zip" "MLIT KSJ Michi-no-Eki Data (P35)"

# 6. MLIT KSJ: Highway time-series data (N06) - Expressways & IC/JCT/SA/PA
$n06Urls = @(
    "https://nlftp.mlit.go.jp/ksj/gml/data/N06/N06-23/N06-23_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N06/N06-22/N06-22_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N06/N06-21/N06-21_GML.zip",
    "https://nlftp.mlit.go.jp/ksj/gml/data/N06/N06-20/N06-20_GML.zip"
)
Try-Download $n06Urls "ksj_N06_highway.zip" "MLIT KSJ Highway Data (N06)"

# 7. Wikidata SPARQL query for all Japanese municipalities/prefectures/wards with P475 (6-digit LG code), coordinates, official URL, Wikipedia URL
$sparqlMuni = @"
SELECT ?item ?lgcode ?coord ?website ?article WHERE {
  ?item wdt:P475 ?lgcode .
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P856 ?website . }
  OPTIONAL {
    ?article schema:about ?item ;
             schema:isPartOf <https://ja.wikipedia.org/> .
  }
}
"@
$wdMuniUrl = "https://query.wikidata.org/sparql?format=json&query=" + [uri]::EscapeDataString($sparqlMuni)
Try-Download @($wdMuniUrl) "wikidata_jp_lgcode_coords.json" "Wikidata JP LGCode Coordinates & Links"

Write-Host "`n=================================================="
Write-Host " Files in data/raw/JP:"
Get-ChildItem -Path $rawDir | Select-Object Name, Length | Format-Table -AutoSize
Write-Host "=================================================="
