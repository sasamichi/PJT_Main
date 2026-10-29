# ==============================================================================
# reset_all_masters.ps1
# 既存の汚染データを完全リセットし、新方針スキーマ（基盤の基盤）の空ヘッダーで初期化。
# countries.csv は新8列スキーマに移行し、area_types.csv / data_sources.csv は保持。
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$workspaceRoot = (Get-Location).Path

Write-Host "=== 1. Migrating countries.csv to New 8-Column Schema ==="
$oldCountriesPath = Join-Path $workspaceRoot "data\master\countries.csv"
$oldCountries = Import-Csv $oldCountriesPath -Encoding UTF8
$newCountriesLines = [System.Collections.Generic.List[string]]::new()
$newCountriesLines.Add("country_code,iso_alpha3,日本語名,公用語名,車両通行側,公式サイトURL,Wikipedia_ja,Wikidata_id")

foreach ($r in $oldCountries) {
    $cCode = $r.country_code
    $a3 = $r.iso_3166_1_a3
    $nameJa = $r.日本語略名
    $nameLocal = if ($r.Wikipedia_en -match '/wiki/(.+)$') { [uri]::UnescapeDataString($matches[1]) -replace '_', ' ' } else { $nameJa }
    if ($cCode -eq "JP") { $nameLocal = "日本国" }
    elseif ($cCode -eq "INT") { $nameLocal = "International" }
    $side = $r.車両通行側
    $officialUrl = if ($cCode -eq "JP") { "https://www.e-gov.go.jp/" } else { "" }
    $wikiJa = $r.Wikipedia_ja
    $wikidata = $r.Wikidata
    if ($wikidata -match '(Q\d+)$') { $wikidata = $matches[1] }

    $vals = @(
        $cCode,
        $a3,
        ('"' + ($nameJa -replace '"', '""') + '"'),
        ('"' + ($nameLocal -replace '"', '""') + '"'),
        $side,
        $officialUrl,
        $wikiJa,
        $wikidata
    )
    $newCountriesLines.Add(($vals -join ","))
}
[System.IO.File]::WriteAllLines($oldCountriesPath, $newCountriesLines, $utf8NoBom)
Write-Host "-> Migrated countries.csv: $($newCountriesLines.Count - 1) rows"

Write-Host "`n=== 2. Removing Obsolete Master CSVs and Old Backups ==="
$obsoleteFiles = @(
    "data\master\municipalities.csv",
    "data\master\weather_zones.csv",
    "data\master\historical_transitions.csv",
    "data\master\city_partnerships.csv",
    "data\master\theme_spots.csv"
)
foreach ($f in $obsoleteFiles) {
    $fullF = Join-Path $workspaceRoot $f
    if (Test-Path $fullF) {
        Remove-Item $fullF -Force
        Write-Host "-> Removed obsolete file: $f"
    }
}

$oldBackups = @("data\backup_20261022_schema_v2", "data\backup_pre_reset", "data\backup_pre_reset_20261015")
foreach ($b in $oldBackups) {
    $fullB = Join-Path $workspaceRoot $b
    if (Test-Path $fullB) {
        Remove-Item $fullB -Recurse -Force
        Write-Host "-> Removed old polluted backup: $b"
    }
}

Write-Host "`n=== 3. Resetting Core 6 Data Tables to Empty New Schema Headers ==="
$emptySchemas = [ordered]@{
    "data\master\areas.csv"            = "area_id,country_code,type_id,公的コード,親区域ID,気象予報区ID,名称,名称_公用語,代表緯度,代表経度,公式サイトURL,Wikipedia_url,Wikidata_id"
    "data\master\operators.csv"        = "operator_id,country_code,親事業体ID,公的コード,大分類,種別,事業者名,公式サイトURL,Wikipedia_url,Wikidata_id"
    "data\master\transport_routes.csv" = "route_id,country_code,operator_id,大分類,種別,路線記号・番号,路線名,路線名_公用語,公式サイトURL,Wikipedia_url,Wikidata_id"
    "data\master\nodes.csv"            = "node_id,country_code,area_id,operator_id,大分類,種別,公的コード,iata_code,icao_code,名称,名称_公用語,緯度,経度,公式サイトURL,Wikipedia_url,Wikidata_id"
    "data\master\edges.csv"            = "edge_id,route_id,from_node_id,to_node_id,順序,状態"
    "data\master\exploration_logs.csv" = "log_id,探索日,タイトル,記録種別,対象路線_ids,対象ノード_ids,対象自治体_ids,緯度,経度,ルート座標,タグ,本文,Webリンク,Geoguessr候補,公開ステータス"
}

foreach ($key in $emptySchemas.Keys) {
    $p = Join-Path $workspaceRoot $key
    [System.IO.File]::WriteAllLines($p, @($emptySchemas[$key]), $utf8NoBom)
    Write-Host "-> Reset to empty header: $key"
}

Write-Host "`n=== 4. Updating country_progress.csv (JP status reset to Pre-Research Done / Re-collecting) ==="
$progPath = Join-Path $workspaceRoot "data\master\country_progress.csv"
$progLines = [System.IO.File]::ReadAllLines($progPath, [System.Text.Encoding]::UTF8)
$updatedProg = [System.Collections.Generic.List[string]]::new()
foreach ($line in $progLines) {
    if ($line.StartsWith("JP,")) {
        $updatedProg.Add('JP,日本,フェーズ2（基準国）,総務省・e-Stat・国土数値情報,国土数値情報(N02/N06/C28/C02/P35/N09),事前調査完了・再収集準備中,2026-10-28,"作業順:001 | 優先度:0 | G7,G20,OECD | 東アジア"')
    } else {
        $updatedProg.Add($line)
    }
}
[System.IO.File]::WriteAllLines($progPath, $updatedProg, $utf8NoBom)
Write-Host "-> Updated JP status in country_progress.csv"

Write-Host "`n=== 5. Creating Staging Directories and Cleaning Fixers ==="
New-Item -ItemType Directory -Force -Path (Join-Path $workspaceRoot "data\staging\JP") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $workspaceRoot "data\raw\JP") | Out-Null
$fixersDir = Join-Path $workspaceRoot "scripts\fixers"
if (Test-Path $fixersDir) {
    Get-ChildItem "$fixersDir\*" | Remove-Item -Force
    Write-Host "-> Cleaned old patch scripts in scripts\fixers"
}

Write-Host "`n=================================================="
Write-Host " All Master Tables Reset & Initialized Cleanly!"
Write-Host "=================================================="
