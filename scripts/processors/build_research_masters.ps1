# ==============================================================================
# build_research_masters.ps1
# 先行5カ国（JP, AT, TW, KR, CH）の事前調査シートから
# area_types.csv および data_sources.csv を生成し、
# country_progress.csv の進捗ステータスを更新するスクリプト。
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$workspaceRoot = (Get-Location).Path

$researchDir = Join-Path $workspaceRoot "docs\research"
$masterDir = Join-Path $workspaceRoot "data\master"

$countries = @("JP", "AT", "TW", "KR", "CH", "IT", "DE")

Write-Host "=================================================="
Write-Host " Building Masters from Research Sheets (5 Countries)"
Write-Host "=================================================="

# ------------------------------------------------------------------------------
# 1. area_types.csv の抽出・構築
# ------------------------------------------------------------------------------
Write-Host "`n[1/3] Extracting area_types.csv..."

$areaTypesList = [System.Collections.Generic.List[PSCustomObject]]::new()
$areaTypeIds = [System.Collections.Generic.HashSet[string]]::new()

foreach ($c in $countries) {
    $fAdmin = Join-Path $researchDir "${c}_行政・気象_制度調査.md"
    if (-not (Test-Path $fAdmin)) {
        Write-Warning "File not found: $fAdmin"
        continue
    }

    $lines = [System.IO.File]::ReadAllLines($fAdmin, [System.Text.Encoding]::UTF8)
    $inTable = $false
    $headers = @()

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ($trimmed -match "^### 2\.1") {
            $inTable = $true
            continue
        }
        if ($inTable -and ($trimmed -match "^### 2\.2" -or ($trimmed.StartsWith("## ") -and -not $trimmed.StartsWith("## 2.")))) {
            $inTable = $false
            break
        }
        if ($inTable -and $trimmed.StartsWith("|")) {
            $cols = $trimmed.Trim('|').Split('|') | ForEach-Object { $_.Trim() }
            if ($cols[0] -match "^---") { continue }
            if ($headers.Count -eq 0) {
                $headers = $cols
            } else {
                if ($cols.Count -eq $headers.Count) {
                    $typeId = $cols[0]
                    if ($areaTypeIds.Contains($typeId)) {
                        Write-Warning "Duplicate type_id: $typeId in $c"
                    } else {
                        $null = $areaTypeIds.Add($typeId)
                    }

                    $obj = [ordered]@{
                        "type_id"       = $typeId
                        "country_code"  = $c
                        "category"      = $cols[1]
                        "level"         = $cols[2]
                        "name_ja"       = $cols[3]
                        "name_local"    = $cols[4]
                        "scale"         = $cols[5]
                        "status"        = $cols[6]
                        "description"   = $cols[7]
                        "wikipedia_url" = $cols[8]
                    }
                    $areaTypesList.Add([PSCustomObject]$obj)
                }
            }
        }
    }
}

Write-Host "-> Extracted area_types: $($areaTypesList.Count) rows"

# CSV出力 (BOMなしUTF-8)
$areaTypesPath = Join-Path $masterDir "area_types.csv"
$csvHeader = "type_id,country_code,大分類,階層レベル,種別名_日本語,種別名_公用語,規模目安,検証状態,説明,Wikipedia_url"
$csvLines = [System.Collections.Generic.List[string]]::new()
$csvLines.Add($csvHeader)

foreach ($row in $areaTypesList) {
    $lineVals = @(
        $row.type_id,
        $row.country_code,
        $row.category,
        $row.level,
        ('"' + ($row.name_ja -replace '"', '""') + '"'),
        ('"' + ($row.name_local -replace '"', '""') + '"'),
        ('"' + ($row.scale -replace '"', '""') + '"'),
        $row.status,
        ('"' + ($row.description -replace '"', '""') + '"'),
        $row.wikipedia_url
    )
    $csvLines.Add(($lineVals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($areaTypesPath, $csvLines, $utf8NoBom)
Write-Host "-> Saved: $areaTypesPath ($($csvLines.Count - 1) records)"

# ------------------------------------------------------------------------------
# 2. data_sources.csv の抽出・構築
# ------------------------------------------------------------------------------
Write-Host "`n[2/3] Extracting data_sources.csv..."

$dataSourcesMap = [ordered]@{}

foreach ($c in $countries) {
    # 1. 行政・気象編
    $fAdmin = Join-Path $researchDir "${c}_行政・気象_制度調査.md"
    if (Test-Path $fAdmin) {
        $lines = [System.IO.File]::ReadAllLines($fAdmin, [System.Text.Encoding]::UTF8)
        $inTable = $false
        $headers = @()
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ($trimmed -match "^### 5\.1") { $inTable = $true; continue }
            if ($inTable -and ($trimmed -match "^### 5\.2" -or $trimmed -match "^---" -or ($trimmed.StartsWith("## ") -and -not $trimmed.StartsWith("## 5.")))) {
                $inTable = $false
                break
            }
            if ($inTable -and $trimmed.StartsWith("|")) {
                $cols = $trimmed.Trim('|').Split('|') | ForEach-Object { $_.Trim() }
                if ($cols[0] -match "^---") { continue }
                if ($headers.Count -eq 0) {
                    $headers = $cols
                } else {
                    if ($cols.Count -eq $headers.Count) {
                        $sId = $cols[0].ToLowerInvariant()
                        if (-not $dataSourcesMap.Contains($sId)) {
                            $dataSourcesMap[$sId] = [ordered]@{
                                "source_id"            = $cols[0]
                                "country_code"         = $c
                                "category"             = $cols[1]
                                "source_name_ja"       = $cols[2]
                                "provider_ja"          = $cols[3]
                                "license"              = $cols[4]
                                "url"                  = $cols[5]
                                "attribution_required" = $cols[6]
                                "terms_summary"        = $cols[7]
                            }
                        } else {
                            $existing = $dataSourcesMap[$sId]
                            if ($existing.category -notlike "*$($cols[1])*") {
                                $existing.category = "$($existing.category) / $($cols[1])"
                            }
                        }
                    }
                }
            }
        }
    }

    # 2. 交通網・インフラ編
    $fTrans = Join-Path $researchDir "${c}_交通_制度調査.md"
    if (Test-Path $fTrans) {
        $lines = [System.IO.File]::ReadAllLines($fTrans, [System.Text.Encoding]::UTF8)
        $inTable = $false
        $headers = @()
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ($trimmed -match "^## 8\.") { $inTable = $true; continue }
            if ($inTable -and ($trimmed -match "^## 9\." -or $trimmed -match "^---")) {
                $inTable = $false
                break
            }
            if ($inTable -and $trimmed.StartsWith("|")) {
                $cols = $trimmed.Trim('|').Split('|') | ForEach-Object { $_.Trim() }
                if ($cols[0] -match "^---") { continue }
                if ($headers.Count -eq 0) {
                    $headers = $cols
                } else {
                    if ($cols.Count -eq $headers.Count) {
                        $sId = $cols[0].ToLowerInvariant()
                        if (-not $dataSourcesMap.Contains($sId)) {
                            $dataSourcesMap[$sId] = [ordered]@{
                                "source_id"            = $cols[0]
                                "country_code"         = $c
                                "category"             = $cols[1]
                                "source_name_ja"       = $cols[2]
                                "provider_ja"          = $cols[3]
                                "license"              = $cols[4]
                                "url"                  = $cols[5]
                                "attribution_required" = $cols[6]
                                "terms_summary"        = $cols[7]
                            }
                        } else {
                            $existing = $dataSourcesMap[$sId]
                            if ($existing.category -notlike "*$($cols[1])*") {
                                $existing.category = "$($existing.category) / $($cols[1])"
                            }
                        }
                    }
                }
            }
        }
    }
}

Write-Host "-> Extracted data_sources: $($dataSourcesMap.Count) rows"

# CSV出力 (BOMなしUTF-8)
$dataSourcesPath = Join-Path $masterDir "data_sources.csv"
$dsCsvHeader = "source_id,country_code,category,source_name_ja,provider_ja,license,url,attribution_required,terms_summary"
$dsCsvLines = [System.Collections.Generic.List[string]]::new()
$dsCsvLines.Add($dsCsvHeader)

foreach ($key in $dataSourcesMap.Keys) {
    $row = $dataSourcesMap[$key]
    $lineVals = @(
        $row.source_id,
        $row.country_code,
        ('"' + ($row.category -replace '"', '""') + '"'),
        ('"' + ($row.source_name_ja -replace '"', '""') + '"'),
        ('"' + ($row.provider_ja -replace '"', '""') + '"'),
        ('"' + ($row.license -replace '"', '""') + '"'),
        $row.url,
        $row.attribution_required,
        ('"' + ($row.terms_summary -replace '"', '""') + '"')
    )
    $dsCsvLines.Add(($lineVals -join ","))
}

[System.IO.File]::WriteAllLines($dataSourcesPath, $dsCsvLines, $utf8NoBom)
Write-Host "-> Saved: $dataSourcesPath ($($dsCsvLines.Count - 1) records)"

# ------------------------------------------------------------------------------
# 3. country_progress.csv の更新
# ------------------------------------------------------------------------------
Write-Host "`n[3/3] Updating country_progress.csv..."
$progPath = Join-Path $masterDir "country_progress.csv"
$progLines = [System.IO.File]::ReadAllLines($progPath, [System.Text.Encoding]::UTF8)
$progHeader = $progLines[0]

$updatedProgLines = [System.Collections.Generic.List[string]]::new()
$updatedProgLines.Add($progHeader)

# 更新対象マッピング
$statusMap = @{
    "JP" = @{ "status" = "事前調査完了・フェーズ2完了"; "date" = "2026-10-28"; "admin" = "総務省・国土数値情報"; "trans" = "国土数値情報・JR・私鉄・高速・国道" }
    "AT" = @{ "status" = "事前調査完了・フェーズ2準備中"; "date" = "2026-10-28"; "admin" = "オーストリア統計局(Statistik Austria)"; "trans" = "ÖBB・ASFINAG・全国GTFS" }
    "TW" = @{ "status" = "事前調査完了・フェーズ2準備中"; "date" = "2026-10-28"; "admin" = "内政部(MOI)・NLSC"; "trans" = "交通部TDX API・台鉄・高鉄" }
    "KR" = @{ "status" = "事前調査完了・フェーズ2準備中"; "date" = "2026-10-28"; "admin" = "行政安全部(MOIS)・統計庁(KOSTAT)"; "trans" = "KRIC・TAGO・Korail" }
    "CH" = @{ "status" = "事前調査完了・フェーズ2準備中"; "date" = "2026-10-28"; "admin" = "連邦測量局(swisstopo)・連邦統計局(BFS)"; "trans" = "SBB・BAV・opentransportdata.swiss" }
    "IT" = @{ "status" = "事前調査完了・フェーズ2準備中"; "date" = "2026-10-28"; "admin" = "国家統計局(ISTAT)・市民保護局(DPC)"; "trans" = "MIT・ANAS・RFI・ANSFISA" }
    "DE" = @{ "status" = "事前調査完了・フェーズ2準備中"; "date" = "2026-10-28"; "admin" = "連邦地図測地庁(BKG)・連邦統計局(Destatis)"; "trans" = "Mobilithek・DB InfraGO・Die Autobahn" }
}

for ($i = 1; $i -lt $progLines.Count; $i++) {
    $line = $progLines[$i]
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    
    $cols = [System.Collections.Generic.List[string]]::new()
    $inQuote = $false
    $cur = ""
    for ($j = 0; $j -lt $line.Length; $j++) {
        $ch = $line[$j]
        if ($ch -eq '"') {
            $inQuote = -not $inQuote
            $cur += $ch
        } elseif ($ch -eq ',' -and -not $inQuote) {
            $cols.Add($cur)
            $cur = ""
        } else {
            $cur += $ch
        }
    }
    $cols.Add($cur)

    $cCode = $cols[0]
    if ($statusMap.ContainsKey($cCode)) {
        $meta = $statusMap[$cCode]
        $cols[3] = $meta["admin"]
        $cols[4] = $meta["trans"]
        $cols[5] = $meta["status"]
        $cols[6] = $meta["date"]
        
        Write-Host "-> $cCode : status updated to '$($meta["status"])'"
    }

    $updatedProgLines.Add(($cols -join ","))
}

[System.IO.File]::WriteAllLines($progPath, $updatedProgLines, $utf8NoBom)
Write-Host "-> Saved: $progPath"

Write-Host "`n=================================================="
Write-Host " Master build successfully finished."
Write-Host "=================================================="
