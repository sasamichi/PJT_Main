# ==============================================================================
# build_staging_nodes.ps1
# Build data/staging/JP/nodes.csv from:
# - KSJ N02 Railway Stations (grouped by station code/name)
# - KSJ N06 Highway ICs / JCTs / SAs / PAs (active 9999)
# - KSJ C28 Passenger Airports (97 airports with IATA/ICAO)
# - MLIT C02 Major Ports (125 Ports: Strategic, Hub, Major)
# - KSJ P35 Michi-no-Eki (Roadside Stations)
# - JMA AMeDAS Stations (1,286 ground weather stations)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir = Join-Path $workspaceRoot "data\raw\JP"
$stagingDir = Join-Path $workspaceRoot "data\staging\JP"
$nodesCsvPath = Join-Path $stagingDir "nodes.csv"

Write-Host "=================================================="
Write-Host " Building data/staging/JP/nodes.csv"
Write-Host "=================================================="

# 1. Load areas.csv and build 2D Spatial Grid Index for Municipalities
Write-Host "[1/7] Loading areas.csv & building spatial grid index..."
$areasCsv = Import-Csv (Join-Path $stagingDir "areas.csv") -Encoding UTF8
$codeToAreaId = @{}
$grid = @{}

foreach ($a in $areasCsv) {
    if ($a.公的コード) {
        $codeToAreaId[$a.公的コード] = $a.area_id
        if ($a.公的コード.Length -eq 6) {
            $c5 = $a.公的コード.Substring(0, 5)
            if (-not $codeToAreaId.ContainsKey($c5)) { $codeToAreaId[$c5] = $a.area_id }
        }
    }
    if ($a.代表緯度 -and $a.代表経度 -and ($a.type_id -match "CITY|WARD|TOWN|VILLAGE")) {
        $lat = [double]$a.代表緯度
        $lon = [double]$a.代表経度
        $gLat = [Math]::Floor($lat * 2)
        $gLon = [Math]::Floor($lon * 2)
        $gKey = "${gLat}_${gLon}"
        if (-not $grid.ContainsKey($gKey)) {
            $grid[$gKey] = [System.Collections.Generic.List[PSCustomObject]]::new()
        }
        $grid[$gKey].Add([PSCustomObject]@{
            area_id = $a.area_id
            name    = $a.名称
            lat     = $lat
            lon     = $lon
        })
    }
}

function Find-NearestAreaId([double]$lat, [double]$lon) {
    $gLat = [Math]::Floor($lat * 2)
    $gLon = [Math]::Floor($lon * 2)
    $minDist = [double]::MaxValue
    $bestArea = ""

    for ($dLat = -2; $dLat -le 2; $dLat++) {
        for ($dLon = -2; $dLon -le 2; $dLon++) {
            $k = "$($gLat + $dLat)_$($gLon + $dLon)"
            if ($grid.ContainsKey($k)) {
                foreach ($m in $grid[$k]) {
                    $d = [Math]::Pow($lat - $m.lat, 2) + [Math]::Pow(($lon - $m.lon) * 0.8, 2)
                    if ($d -lt $minDist) {
                        $minDist = $d
                        $bestArea = $m.area_id
                    }
                }
            }
        }
    }
    if (-not $bestArea) {
        return "JP-AR-000570" # Fallback Tokyo Chiyoda
    }
    return $bestArea
}

# 2. Load operators.csv mapping
$opsCsv = Import-Csv (Join-Path $stagingDir "operators.csv") -Encoding UTF8
$opMap = @{}
foreach ($o in $opsCsv) {
    $opMap[$o.事業者名] = $o.operator_id
}
$jmaOpId   = $opMap["気象庁"]
$mlitRoad  = $opMap["国土交通省道路局"]
$mlitPort  = $opMap["国土交通省港湾局"]
$mlitAero  = $opMap["国土交通省航空局"]

$nodes = [System.Collections.Generic.List[PSCustomObject]]::new()
$nodeSeq = 0

function Add-Node($areaId, $opId, $cat, $kind, $code, $iata, $icao, $name, $nameJa, [double]$lat, [double]$lon, $url, $wiki) {
    $script:nodeSeq++
    $nid = ("JP-ND-{0:D6}" -f $script:nodeSeq)
    $script:nodes.Add([PSCustomObject]@{
        node_id       = $nid
        country_code  = "JP"
        area_id       = $areaId
        operator_id   = $opId
        大分類        = $cat
        種別          = $kind
        公的コード    = $code
        iata_code     = $iata
        icao_code     = $icao
        名称          = $name
        名称_公用語   = $nameJa
        緯度          = ([Math]::Round($lat, 6).ToString("F6"))
        経度          = ([Math]::Round($lon, 6).ToString("F6"))
        公式サイトURL = $url
        Wikipedia_url = $wiki
        Wikidata_id   = ""
    })
}

# ------------------------------------------------------------------------------
# 3. Passenger Airports (KSJ C28 + Wikidata IATA/ICAO: 97 airports)
# ------------------------------------------------------------------------------
Write-Host "[2/7] Extracting 97 Passenger Airports..."
$c28Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_C28_airport.zip"))
$srAir = New-Object System.IO.StreamReader($c28Zip.GetEntry("UTF-8/C28-21_Airport.geojson").Open(), [System.Text.Encoding]::UTF8)
$srRef = New-Object System.IO.StreamReader($c28Zip.GetEntry("UTF-8/C28-21_AirportReferencePoint.geojson").Open(), [System.Text.Encoding]::UTF8)

# Parse reference points
$refMap = @{}
while (-not $srRef.EndOfStream) {
    $line = $srRef.ReadLine()
    if ($line -match '"C28_000":\s*"([^"]+)".*?"coordinates":\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]') {
        $refMap[$matches[1]] = @{ Lon = [double]$matches[2]; Lat = [double]$matches[3] }
    }
}
$srRef.Dispose()

# Airport Wikidata mapping for IATA / ICAO
$wikiAirPath = Join-Path $rawDir "wikidata_jp_airports.json"
$wikiAirMap = @{}
if (Test-Path $wikiAirPath) {
    $wAir = Get-Content $wikiAirPath -Encoding UTF8 | ConvertFrom-Json
    if ($wAir.results.bindings) {
        foreach ($item in $wAir.results.bindings) {
            $label = if ($item.itemLabel) { $item.itemLabel.value } else { "" }
            if ($label) {
                $wikiAirMap[$label] = @{
                    IATA = if ($item.iata) { $item.iata.value } else { "" }
                    ICAO = if ($item.icao) { $item.icao.value } else { "" }
                }
            }
        }
    }
}

$seenAirports = [System.Collections.Generic.HashSet[string]]::new()
$airCount = 0
while (-not $srAir.EndOfStream) {
    $line = $srAir.ReadLine()
    if ($line -match '"C28_004":\s*"供用中"') {
        $aName = if ($line -match '"C28_005":\s*"([^"]+)"') { $matches[1] } else { "" }
        $refId = if ($line -match '"C28_101":\s*"#?([^"]+)"') { $matches[1] } else { "" }
        $muniCode = if ($line -match '"C28_001":\s*"([^"]+)"') { $matches[1] } else { "" }

        if (-not $aName -or $seenAirports.Contains($aName)) { continue }
        $null = $seenAirports.Add($aName)

        if ($refId -and $refMap.ContainsKey($refId)) {
            $coords = $refMap[$refId]
            $aId = if ($muniCode -and $codeToAreaId.ContainsKey($muniCode)) { $codeToAreaId[$muniCode] } else { Find-NearestAreaId $coords.Lat $coords.Lon }
            $iata = ""
            $icao = ""
            if ($wikiAirMap.ContainsKey($aName)) {
                $iata = $wikiAirMap[$aName].IATA
                $icao = $wikiAirMap[$aName].ICAO
            }
            if ($aName -match "新石垣|石垣") {
                $iata = "ISG"
                $icao = "ROIG"
            }
            $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($aName)
            Add-Node $aId $mlitAero "交通拠点" "空港" $muniCode $iata $icao $aName $aName $coords.Lat $coords.Lon "" $wiki
            $airCount++
        }
    }
}
$srAir.Dispose()
$c28Zip.Dispose()
Write-Host "-> Added $airCount Passenger Airports."

# ------------------------------------------------------------------------------
# 4. Major Ports (重要港湾以上 125港)
# ------------------------------------------------------------------------------
Write-Host "[3/7] Extracting Major Ports (重要港湾以上 125港)..."
$c02Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_C02_port.zip"))
$srC02 = New-Object System.IO.StreamReader($c02Zip.GetEntry("C02-14_GML/C02-14-g.xml").Open(), [System.Text.Encoding]::UTF8)
$txtC02 = $srC02.ReadToEnd()
$srC02.Dispose()
$c02Zip.Dispose()

# Index all Point positions
$pointPosMap = @{}
$ptMatches = [regex]::Matches($txtC02, '<gml:Point gml:id="([^"]+)">\s*<gml:pos>([0-9.]+)\s+([0-9.]+)</gml:pos>')
foreach ($pm in $ptMatches) {
    $pointPosMap[$pm.Groups[1].Value] = @{ Lat = [double]$pm.Groups[2].Value; Lon = [double]$pm.Groups[3].Value }
}
Write-Host "  Indexed $($pointPosMap.Count) Port Point coordinates."

$matchesC02 = [regex]::Matches($txtC02, '(?s)<ksj:PortAndHarbor\b.*?</ksj:PortAndHarbor>')
$seenPorts = [System.Collections.Generic.HashSet[string]]::new()
$portCount = 0

foreach ($m in $matchesC02) {
    $v = $m.Value
    $t1 = if ($v -match '<ksj:type1>(\d+)</ksj:type1>') { $matches[1] } else { "" }
    $t2 = if ($v -match '<ksj:type2>(\d+)</ksj:type2>') { $matches[1] } else { "" }
    $pName = if ($v -match '<ksj:portName>([^<]+)</ksj:portName>') { $matches[1] } else { "" }
    $pCode = if ($v -match '<ksj:portCode>([^<]+)</ksj:portCode>') { $matches[1] } else { "" }
    $posRef = if ($v -match '<ksj:position xlink:href="#([^"]+)"') { $matches[1] } else { "" }

    # type2: 11=国際戦略港湾(5), 12=国際拠点港湾(18), 13=重要港湾(102) => 計125港
    if ($t2 -in @("11", "12", "13") -and $pName) {
        if ($seenPorts.Contains($pName)) { continue }
        $null = $seenPorts.Add($pName)

        $lat = 35.0
        $lon = 135.0
        if ($posRef -and $pointPosMap.ContainsKey($posRef)) {
            $lat = $pointPosMap[$posRef].Lat
            $lon = $pointPosMap[$posRef].Lon
        }
        $aId = Find-NearestAreaId $lat $lon
        $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($pName + "港")
        Add-Node $aId $mlitPort "交通拠点" "主要港湾" $pCode "" "" ($pName + "港") ($pName + "港") $lat $lon "https://www.mlit.go.jp/kowan/" $wiki
        $portCount++
    }
}
Write-Host "-> Added $portCount Major Ports."

# ------------------------------------------------------------------------------
# 5. Michi-no-Eki (Roadside Stations from KSJ P35)
# ------------------------------------------------------------------------------
Write-Host "[4/7] Extracting Michi-no-Eki (道の駅)..."
$p35Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_P35_michinoeki.zip"))
$srP35 = New-Object System.IO.StreamReader($p35Zip.GetEntry("P35-18_GML/P35-18_Roadside_Station.geojson").Open(), [System.Text.Encoding]::UTF8)
$michiCount = 0

while (-not $srP35.EndOfStream) {
    $line = $srP35.ReadLine()
    if ($line -match '"P35_001":\s*([0-9.]+).*?"P35_002":\s*([0-9.]+).*?"P35_005":\s*"([^"]+)".*?"P35_006":\s*"([^"]+)"') {
        $lat = [double]$matches[1]
        $lon = [double]$matches[2]
        $muniCode = $matches[3]
        $mName = "道の駅 " + $matches[4]
        $url = if ($line -match '"P35_007":\s*"([^"]+)"') { $matches[1] -replace '\\/', '/' } else { "" }

        $aId = if ($muniCode -and $codeToAreaId.ContainsKey($muniCode)) { $codeToAreaId[$muniCode] } else { Find-NearestAreaId $lat $lon }
        $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($mName)
        Add-Node $aId $mlitRoad "交通拠点" "道の駅" $muniCode "" "" $mName $mName $lat $lon $url $wiki
        $michiCount++
    }
}
$srP35.Dispose()
$p35Zip.Dispose()
Write-Host "-> Added $michiCount Michi-no-Eki."

# ------------------------------------------------------------------------------
# 6. JMA AMeDAS Weather Stations (1,286 stations)
# ------------------------------------------------------------------------------
Write-Host "[5/7] Extracting 1,286 JMA AMeDAS Stations..."
$amedasText = [System.IO.File]::ReadAllText((Join-Path $rawDir "jma_amedas.json"), [System.Text.Encoding]::UTF8)
$amedasJson = $amedasText | ConvertFrom-Json
$amedasProps = $amedasJson.psobject.properties
$amedasCount = 0

foreach ($p in $amedasProps) {
    $code = $p.Name
    $val = $p.Value
    if ($val.kjName -and $val.lat -and $val.lon) {
        $lat = [double]$val.lat[0] + ([double]$val.lat[1] / 60.0)
        $lon = [double]$val.lon[0] + ([double]$val.lon[1] / 60.0)
        $stName = $val.kjName + "（アメダス）"
        $aId = Find-NearestAreaId $lat $lon
        $url = "https://www.jma.go.jp/bosai/amedas/#amdno=$code"
        $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($val.kjName)
        Add-Node $aId $jmaOpId "気象" "気象観測点" $code "" "" $stName $stName $lat $lon $url $wiki
        $amedasCount++
    }
}
Write-Host "-> Added $amedasCount JMA AMeDAS Stations."

# ------------------------------------------------------------------------------
# 7. Highway ICs / JCTs / SAs / PAs from KSJ N06 Joint (active 9999)
# ------------------------------------------------------------------------------
Write-Host "[6/7] Extracting Highway ICs & Facilities from KSJ N06..."
$n06Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N06_highway.zip"))
$srN06 = New-Object System.IO.StreamReader($n06Zip.GetEntry("UTF-8/N06-23_Joint.geojson").Open(), [System.Text.Encoding]::UTF8)
$hwFacCount = 0
$seenHwFac = [System.Collections.Generic.HashSet[string]]::new()

while (-not $srN06.EndOfStream) {
    $line = $srN06.ReadLine()
    if ($line -match '"N06_014":\s*9999' -and $line -match '"N06_018":\s*"([^"]+)"' -and $line -match '"coordinates":\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]') {
        $fName = $matches[1]
        $lon = [double]$matches[2]
        $lat = [double]$matches[3]
        $fCode = ""
        $fKindCode = ""
        if ($line -match '"N06_015":\s*"([^"]+)"') { $fCode = $matches[1] }
        if ($line -match '"N06_019":\s*"([^"]+)"') { $fKindCode = $matches[1] }

        $key = "$fName|$([Math]::Round($lat, 3))|$([Math]::Round($lon, 3))"
        if ($seenHwFac.Contains($key)) { continue }
        $null = $seenHwFac.Add($key)

        $kind = if ($fName -match "SA|PA|サービスエリア|パーキングエリア") { "高速施設（SA・PA）" } else { "IC・JCT" }
        $aId = Find-NearestAreaId $lat $lon
        $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($fName)
        Add-Node $aId $mlitRoad "交通拠点" $kind $fCode "" "" $fName $fName $lat $lon "" $wiki
        $hwFacCount++
    }
}
$srN06.Dispose()
$n06Zip.Dispose()
Write-Host "-> Added $hwFacCount Highway Facilities."

# ------------------------------------------------------------------------------
# 8. Railway Stations from KSJ N02
# ------------------------------------------------------------------------------
Write-Host "[7/7] Extracting Railway Stations from KSJ N02..."
$n02Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N02_railway.zip"))
$srN02 = New-Object System.IO.StreamReader($n02Zip.GetEntry("UTF-8/N02-23_Station.geojson").Open(), [System.Text.Encoding]::UTF8)

# Group stations by unique (Op + Name)
$stationGroups = [System.Collections.Generic.Dictionary[string, PSCustomObject]]::new()

while (-not $srN02.EndOfStream) {
    $line = $srN02.ReadLine()
    if ($line -match '"N02_005":\s*"([^"]+)".*?"N02_004":\s*"([^"]+)"' -or $line -match '"N02_004":\s*"([^"]+)".*?"N02_005":\s*"([^"]+)"') {
        $stName = ""
        $opName = ""
        $code = ""
        $gCode = ""
        if ($line -match '"N02_005":\s*"([^"]+)"') { $stName = $matches[1] }
        if ($line -match '"N02_004":\s*"([^"]+)"') { $opName = $matches[1] }
        if ($line -match '"N02_005c":\s*"([^"]+)"') { $code = $matches[1] }
        if ($line -match '"N02_005g":\s*"([^"]+)"') { $gCode = $matches[1] }

        if (-not $stName -or -not $opName) { continue }

        # Extract coordinates
        $coordsMatches = [regex]::Matches($line, '\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]')
        if ($coordsMatches.Count -gt 0) {
            $sumLon = 0.0
            $sumLat = 0.0
            foreach ($cm in $coordsMatches) {
                $sumLon += [double]$cm.Groups[1].Value
                $sumLat += [double]$cm.Groups[2].Value
            }
            $avgLon = $sumLon / $coordsMatches.Count
            $avgLat = $sumLat / $coordsMatches.Count

            $stKey = "$opName|$stName"
            if (-not $stationGroups.ContainsKey($stKey)) {
                $stationGroups[$stKey] = [PSCustomObject]@{
                    Op    = $opName
                    Name  = $stName
                    Code  = $code
                    GCode = $gCode
                    Lat   = $avgLat
                    Lon   = $avgLon
                }
            }
        }
    }
}
$srN02.Dispose()
$n02Zip.Dispose()

$railStCount = 0
foreach ($sg in $stationGroups.Values) {
    $opId = $opMap[$sg.Op]
    if (-not $opId) {
        foreach ($k in $opMap.Keys) {
            if ($k -match [regex]::Escape($sg.Op) -or $sg.Op -match [regex]::Escape($k)) {
                $opId = $opMap[$k]
                break
            }
        }
    }
    if (-not $opId) { $opId = "JP-OP-000000" }

    $aId = Find-NearestAreaId $sg.Lat $sg.Lon
    $fullName = if ($sg.Name -match "駅$|停留場$|停留所$") { $sg.Name } else { $sg.Name + "駅" }
    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($fullName)
    Add-Node $aId $opId "交通拠点" "鉄道駅" $sg.Code "" "" $fullName $fullName $sg.Lat $sg.Lon "" $wiki
    $railStCount++
}
Write-Host "-> Added $railStCount Railway Stations."

# ------------------------------------------------------------------------------
# Save nodes.csv
# ------------------------------------------------------------------------------
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("node_id,country_code,area_id,operator_id,大分類,種別,公的コード,iata_code,icao_code,名称,名称_公用語,緯度,経度,公式サイトURL,Wikipedia_url,Wikidata_id")

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
    $lines.Add(($vals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($nodesCsvPath, $lines, $utf8NoBom)
Write-Host "=================================================="
Write-Host " Successfully generated data/staging/JP/nodes.csv!"
Write-Host " Total Nodes: $($lines.Count - 1)"
Write-Host "=================================================="
