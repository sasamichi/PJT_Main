# ==============================================================================
# fix_staging_audit_issues.ps1
# Fix the 3 issues discovered by quality-auditor in Step 4:
# 1. Decode ISO-8859-1 -> UTF-8 Mojibake in raw/JP/jma_area.json & jma_amedas.json
#    and update all 2,391 weather zones in areas.csv + 1,286 AMeDAS nodes in nodes.csv.
# 2. Fix duplicate route code F-MIY-01 on 宮島口 - 宮島 航路 -> F-MIJ-01 in transport_routes.csv.
# 3. Rebuild edges.csv with proper F-MIY-01 (神戸-宮崎) and F-MIJ-01 (宮島航路).
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir        = Join-Path $workspaceRoot "data\raw\JP"
$stagingDir    = Join-Path $workspaceRoot "data\staging\JP"

$iso88591 = [System.Text.Encoding]::GetEncoding("ISO-8859-1")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Repair-Mojibake([string]$str) {
    if ([string]::IsNullOrEmpty($str)) { return $str }
    # Convert string (whose chars 0x00..0xFF represent raw UTF-8 bytes) back to UTF-8 string
    $bytes = $iso88591.GetBytes($str)
    return [System.Text.Encoding]::UTF8.GetString($bytes)
}

Write-Host "=================================================================="
Write-Host " [是正処置] 気象データ文字化け復元 ＆ 航路コード重複修正"
Write-Host "=================================================================="

# ------------------------------------------------------------------------------
# 1. Repair raw jma_area.json and jma_amedas.json in-place
# ------------------------------------------------------------------------------
Write-Host "[1/4] Repairing raw jma_area.json & jma_amedas.json..."

$jmaAreaPath = Join-Path $rawDir "jma_area.json"
$rawAreaObj = [System.IO.File]::ReadAllText($jmaAreaPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

# Build lookup of weather code -> clean Japanese name
$wxCleanNameMap = @{}
foreach ($groupName in @("centers", "offices", "class10s", "class15s", "class20s")) {
    $grp = $rawAreaObj.$groupName
    foreach ($p in $grp.PSObject.Properties) {
        $code = $p.Name
        $val  = $p.Value
        # Check if already clean or needs repair
        $name = $val.name
        if ($name -match "[\u0080-\u00FF]") {
            $name = Repair-Mojibake $name
            $val.name = $name
        }
        if ($val.officeName -and $val.officeName -match "[\u0080-\u00FF]") {
            $val.officeName = Repair-Mojibake $val.officeName
        }
        $wxCleanNameMap[$code] = $name
    }
}
$cleanAreaJson = $rawAreaObj | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($jmaAreaPath, $cleanAreaJson, $utf8NoBom)
Write-Host "  Repaired jma_area.json ($($wxCleanNameMap.Count) weather zones). Sample 010100: $($wxCleanNameMap['010100'])"

$jmaAmedasPath = Join-Path $rawDir "jma_amedas.json"
$rawAmedasObj = [System.IO.File]::ReadAllText($jmaAmedasPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$amedasCleanMap = @{}
foreach ($p in $rawAmedasObj.PSObject.Properties) {
    $code = $p.Name
    $val  = $p.Value
    $kj = $val.kjName
    if ($kj -match "[\u0080-\u00FF]") {
        $kj = Repair-Mojibake $kj
        $val.kjName = $kj
    }
    if ($val.knName -and $val.knName -match "[\u0080-\u00FF]") {
        $val.knName = Repair-Mojibake $val.knName
    }
    $amedasCleanMap[$code] = $kj
}
$cleanAmedasJson = $rawAmedasObj | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($jmaAmedasPath, $cleanAmedasJson, $utf8NoBom)
Write-Host "  Repaired jma_amedas.json ($($amedasCleanMap.Count) stations). Sample 11001: $($amedasCleanMap['11001'])"

# ------------------------------------------------------------------------------
# 2. Update data/staging/JP/areas.csv (2,391 weather zones)
# ------------------------------------------------------------------------------
Write-Host "[2/4] Updating data/staging/JP/areas.csv..."
$areasCsvPath = Join-Path $stagingDir "areas.csv"
$areas = Import-Csv $areasCsvPath -Encoding UTF8
$fixedAreas = 0

foreach ($a in $areas) {
    if ($a.type_id -match "^JP_MET_") {
        $code = $a.公的コード
        if ($wxCleanNameMap.ContainsKey($code)) {
            $cleanName = $wxCleanNameMap[$code]
            $a.名称        = $cleanName
            $a.名称_公用語 = $cleanName
            $fixedAreas++
        } elseif ($a.名称 -match "[\u0080-\u00FF]") {
            $cleanName = Repair-Mojibake $a.名称
            $a.名称        = $cleanName
            $a.名称_公用語 = $cleanName
            $fixedAreas++
        }
    }
}

$areaLines = [System.Collections.Generic.List[string]]::new()
$areaLines.Add("area_id,country_code,type_id,公的コード,親区域ID,気象予報区ID,名称,名称_公用語,代表緯度,代表経度,公式サイトURL,Wikipedia_url,Wikidata_id")
foreach ($r in $areas) {
    $vals = @(
        $r.area_id,
        $r.country_code,
        $r.type_id,
        ('"' + ($r.公的コード -replace '"', '""') + '"'),
        $r.親区域ID,
        $r.気象予報区ID,
        ('"' + ($r.名称 -replace '"', '""') + '"'),
        ('"' + ($r.名称_公用語 -replace '"', '""') + '"'),
        $r.代表緯度,
        $r.代表経度,
        $r.公式サイトURL,
        $r.Wikipedia_url,
        $r.Wikidata_id
    )
    $areaLines.Add(($vals -join ","))
}
[System.IO.File]::WriteAllLines($areasCsvPath, $areaLines, $utf8NoBom)
Write-Host "  Updated $fixedAreas weather zone names in areas.csv."

# ------------------------------------------------------------------------------
# 3. Update data/staging/JP/nodes.csv (1,286 AMeDAS nodes)
# ------------------------------------------------------------------------------
Write-Host "[3/4] Updating data/staging/JP/nodes.csv..."
$nodesCsvPath = Join-Path $stagingDir "nodes.csv"
$nodes = Import-Csv $nodesCsvPath -Encoding UTF8
$fixedNodes = 0

foreach ($n in $nodes) {
    if ($n.種別 -eq "気象観測点") {
        $code = $n.公的コード
        if ($amedasCleanMap.ContainsKey($code)) {
            $kj = $amedasCleanMap[$code]
            $fullName = "${kj}（アメダス）"
            $n.名称          = $fullName
            $n.名称_公用語   = $fullName
            $n.Wikipedia_url = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($kj)
            $fixedNodes++
        }
    }
}

$nodeLines = [System.Collections.Generic.List[string]]::new()
$nodeLines.Add("node_id,country_code,area_id,operator_id,大分類,種別,公的コード,iata_code,icao_code,名称,名称_公用語,緯度,経度,公式サイトURL,Wikipedia_url,Wikidata_id")
foreach ($r in $nodes) {
    $vals = @(
        $r.node_id,
        $r.country_code,
        $r.area_id,
        $r.operator_id,
        $r.大分類,
        $r.種別,
        ('"' + ($r.公的コード -replace '"', '""') + '"'),
        $r.iata_code,
        $r.icao_code,
        ('"' + ($r.名称 -replace '"', '""') + '"'),
        ('"' + ($r.名称_公用語 -replace '"', '""') + '"'),
        $r.緯度,
        $r.経度,
        $r.公式サイトURL,
        $r.Wikipedia_url,
        $r.Wikidata_id
    )
    $nodeLines.Add(($vals -join ","))
}
[System.IO.File]::WriteAllLines($nodesCsvPath, $nodeLines, $utf8NoBom)
Write-Host "  Updated $fixedNodes AMeDAS station names in nodes.csv."

# ------------------------------------------------------------------------------
# 4. Fix F-MIY-01 duplicate in transport_routes.csv -> F-MIJ-01 for 宮島航路
# ------------------------------------------------------------------------------
Write-Host "[4/4] Fixing duplicate route code F-MIY-01 in transport_routes.csv..."
$routesCsvPath = Join-Path $stagingDir "transport_routes.csv"
$routes = Import-Csv $routesCsvPath -Encoding UTF8
foreach ($rt in $routes) {
    if ($rt.路線名 -match "宮島口\s*-\s*宮島") {
        $rt."路線記号・番号" = "F-MIJ-01"
        Write-Host "  Updated $($rt.route_id) ($($rt.路線名)) code -> F-MIJ-01"
    }
}

$routeLines = [System.Collections.Generic.List[string]]::new()
$routeLines.Add("route_id,country_code,operator_id,大分類,種別,路線記号・番号,路線名,路線名_公用語,公式サイトURL,Wikipedia_url,Wikidata_id")
foreach ($r in $routes) {
    $vals = @(
        $r.route_id,
        $r.country_code,
        $r.operator_id,
        $r.大分類,
        $r.種別,
        ('"' + ($r."路線記号・番号" -replace '"', '""') + '"'),
        ('"' + ($r.路線名 -replace '"', '""') + '"'),
        ('"' + ($r.路線名_公用語 -replace '"', '""') + '"'),
        $r.公式サイトURL,
        $r.Wikipedia_url,
        $r.Wikidata_id
    )
    $routeLines.Add(($vals -join ","))
}
[System.IO.File]::WriteAllLines($routesCsvPath, $routeLines, $utf8NoBom)
Write-Host "=================================================================="
Write-Host " Audit Issues Repaired Successfully!"
Write-Host "=================================================================="
