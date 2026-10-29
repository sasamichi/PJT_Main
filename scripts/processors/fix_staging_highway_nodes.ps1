# ==============================================================================
# fix_staging_highway_nodes.ps1
# Fix the 2,354 Highway IC/JCT/SA/PA nodes in data/staging/JP/nodes.csv
# wherechained -match caused $matches[1] to overwrite facility name with longitude,
# and remove any self-loop edge in edges.csv.
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir        = Join-Path $workspaceRoot "data\raw\JP"
$stagingDir    = Join-Path $workspaceRoot "data\staging\JP"
$nodesCsvPath  = Join-Path $stagingDir "nodes.csv"
$edgesCsvPath  = Join-Path $stagingDir "edges.csv"

Write-Host "=================================================="
Write-Host " Fixing Highway Nodes & Self-Loop Edges in Staging"
Write-Host "=================================================="

# 1. Load areas.csv for Spatial Grid
$areas = Import-Csv (Join-Path $stagingDir "areas.csv") -Encoding UTF8
$grid = @{}
foreach ($a in $areas) {
    if ($a.代表緯度 -and $a.代表経度 -and ($a.type_id -match "CITY|WARD|TOWN|VILLAGE")) {
        $lat = [double]$a.代表緯度
        $lon = [double]$a.代表経度
        $gKey = "$([Math]::Floor($lat * 2))_$([Math]::Floor($lon * 2))"
        if (-not $grid.ContainsKey($gKey)) {
            $grid[$gKey] = [System.Collections.Generic.List[PSCustomObject]]::new()
        }
        $grid[$gKey].Add([PSCustomObject]@{ area_id=$a.area_id; lat=$lat; lon=$lon })
    }
}

function Find-NearestAreaId([double]$lat, [double]$lon) {
    $gLat = [Math]::Floor($lat * 2); $gLon = [Math]::Floor($lon * 2)
    $minDist = [double]::MaxValue; $bestArea = "JP-AR-000570"
    for ($dLat = -2; $dLat -le 2; $dLat++) {
        for ($dLon = -2; $dLon -le 2; $dLon++) {
            $k = "$($gLat + $dLat)_$($gLon + $dLon)"
            if ($grid.ContainsKey($k)) {
                foreach ($m in $grid[$k]) {
                    $d = [Math]::Pow($lat - $m.lat, 2) + [Math]::Pow(($lon - $m.lon) * 0.8, 2)
                    if ($d -lt $minDist) { $minDist = $d; $bestArea = $m.area_id }
                }
            }
        }
    }
    return $bestArea
}

# 2. Extract clean Highway Facilities from ksj_N06_highway.zip
Write-Host "[1/3] Extracting clean Highway ICs/JCTs/SAs/PAs from KSJ N06..."
$n06Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N06_highway.zip"))
$srN06 = New-Object System.IO.StreamReader($n06Zip.GetEntry("UTF-8/N06-23_Joint.geojson").Open(), [System.Text.Encoding]::UTF8)

$cleanHwList = [System.Collections.Generic.List[PSCustomObject]]::new()
$seenHwFac = [System.Collections.Generic.HashSet[string]]::new()

while (-not $srN06.EndOfStream) {
    $line = $srN06.ReadLine()
    if ($line -match '"N06_014":\s*9999') {
        $fName = if ($line -match '"N06_018":\s*"([^"]+)"') { $matches[1] } else { "" }
        $fCode = if ($line -match '"N06_015":\s*"([^"]+)"') { $matches[1] } else { "" }
        $fKind = if ($line -match '"N06_019":\s*"([^"]+)"') { $matches[1] } else { "" }
        $lon = 0.0; $lat = 0.0
        if ($line -match '"coordinates":\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]') {
            $lon = [double]$matches[1]
            $lat = [double]$matches[2]
        }
        if ($fName -and $lat -gt 20.0 -and $lon -gt 120.0) {
            $key = "$fName|$([Math]::Round($lat, 3))|$([Math]::Round($lon, 3))"
            if (-not $seenHwFac.Contains($key)) {
                $null = $seenHwFac.Add($key)
                $kindStr = if ($fName -match "SA|PA|サービスエリア|パーキングエリア") { "高速施設（SA・PA）" } else { "IC・JCT" }
                $aId = Find-NearestAreaId $lat $lon
                $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($fName)
                $cleanHwList.Add([PSCustomObject]@{
                    area_id = $aId
                    kind    = $kindStr
                    code    = $fCode
                    name    = $fName
                    lat     = ([Math]::Round($lat, 6).ToString("F6"))
                    lon     = ([Math]::Round($lon, 6).ToString("F6"))
                    wiki    = $wiki
                })
            }
        }
    }
}
$srN06.Dispose()
$n06Zip.Dispose()
Write-Host "-> Extracted $($cleanHwList.Count) clean Highway Facilities."

# 3. Replace the corrupted IC/JCT records in nodes.csv in-place
Write-Host "[2/3] Replacing Highway records in nodes.csv..."
$existingNodes = Import-Csv $nodesCsvPath -Encoding UTF8
$hwIdx = 0
$updatedCount = 0

foreach ($n in $existingNodes) {
    if ($n.種別 -in @("IC・JCT", "高速施設（SA・PA）")) {
        if ($hwIdx -lt $cleanHwList.Count) {
            $c = $cleanHwList[$hwIdx]
            $n.area_id       = $c.area_id
            $n.種別          = $c.kind
            $n.公的コード    = $c.code
            $n.名称          = $c.name
            $n.名称_公用語   = $c.name
            $n.緯度          = $c.lat
            $n.経度          = $c.lon
            $n.Wikipedia_url = $c.wiki
            $hwIdx++
            $updatedCount++
        }
    }
}
Write-Host "-> Replaced $updatedCount Highway nodes in-place."

# Save nodes.csv
$nodeLines = [System.Collections.Generic.List[string]]::new()
$nodeLines.Add("node_id,country_code,area_id,operator_id,大分類,種別,公的コード,iata_code,icao_code,名称,名称_公用語,緯度,経度,公式サイトURL,Wikipedia_url,Wikidata_id")
foreach ($r in $existingNodes) {
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
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($nodesCsvPath, $nodeLines, $utf8NoBom)

# 4. Remove any self-loop edges in edges.csv
Write-Host "[3/3] Checking & removing self-loop edges in edges.csv..."
$existingEdges = Import-Csv $edgesCsvPath -Encoding UTF8
$edgeLines = [System.Collections.Generic.List[string]]::new()
$edgeLines.Add("edge_id,route_id,from_node_id,to_node_id,順序,状態")
$eSeq = 0
foreach ($e in $existingEdges) {
    if ($e.from_node_id -eq $e.to_node_id) {
        Write-Host "  Removed self-loop edge: $($e.edge_id) ($($e.from_node_id))"
        continue
    }
    $eSeq++
    $eid = ("JP-ED-{0:D6}" -f $eSeq)
    $edgeLines.Add("$eid,$($e.route_id),$($e.from_node_id),$($e.to_node_id),$($e.順序),$($e.状態)")
}
[System.IO.File]::WriteAllLines($edgesCsvPath, $edgeLines, $utf8NoBom)
Write-Host "-> Saved clean edges.csv: $eSeq edges."
