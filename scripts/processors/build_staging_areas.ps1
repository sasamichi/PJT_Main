# ==============================================================================
# build_staging_areas.ps1
# Build data/staging/JP/areas.csv from official raw datasets:
# - Soumu Excel: Prefectures (47), Municipalities (1,747), Designated Wards (171)
# - Geolonia Addresses: Gun (379), Subprefectures (18), Coordinates
# - MLIT KSJ P05: Municipality Hall Coordinates
# - JMA area.json: Centers (11), Offices (58), Class10s (142), Class20s (1,805)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir = Join-Path $workspaceRoot "data\raw\JP"
$stagingDir = Join-Path $workspaceRoot "data\staging\JP"
New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null
$areasCsvPath = Join-Path $stagingDir "areas.csv"

Write-Host "=================================================="
Write-Host " Building data/staging/JP/areas.csv from Raw Data"
Write-Host "=================================================="

# ------------------------------------------------------------------------------
# 1. Load P05 Municipality Hall Coordinates (Official Main Halls)
# ------------------------------------------------------------------------------
Write-Host "[1/6] Loading P05 Municipality Hall Coordinates..."
$outerZip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_P05_munihall.zip"))
$hallCoords = @{} # 5-digit code -> @{ Lat, Lon, Name, Addr, Score }

foreach ($entry in $outerZip.Entries) {
    if ($entry.FullName -notlike "*.zip") { continue }
    $ms = New-Object System.IO.MemoryStream
    $s = $entry.Open()
    $s.CopyTo($ms)
    $s.Dispose()
    $ms.Position = 0
    $innerZip = New-Object System.IO.Compression.ZipArchive($ms, [System.IO.Compression.ZipArchiveMode]::Read)
    foreach ($ie in $innerZip.Entries) {
        if ($ie.FullName -like "*.geojson") {
            $sr = New-Object System.IO.StreamReader($ie.Open(), [System.Text.Encoding]::UTF8)
            $json = $sr.ReadToEnd() | ConvertFrom-Json
            $sr.Dispose()
            foreach ($f in $json.features) {
                $p = $f.properties
                $code5 = [string]$p.P05_001
                $kind  = [string]$p.P05_002
                $fname = [string]$p.P05_003
                $addr  = [string]$p.P05_004
                $lon   = [double]$f.geometry.coordinates[0]
                $lat   = [double]$f.geometry.coordinates[1]

                if ($kind -eq "1") {
                    $score = 1
                    if ($fname -match "(市役所|区役所|町役場|村役場|本庁舎)$" -and $fname -notmatch "(支所|出張所|分室|分庁舎|連絡所)") {
                        $score = 10
                    } elseif ($fname -notmatch "(支所|出張所|分室|連絡所)") {
                        $score = 5
                    }
                    if (-not $hallCoords.ContainsKey($code5) -or $score -gt $hallCoords[$code5].Score) {
                        $hallCoords[$code5] = @{ Lat=$lat; Lon=$lon; Name=$fname; Addr=$addr; Score=$score }
                    }
                }
            }
        }
    }
    $innerZip.Dispose()
    $ms.Dispose()
}
$outerZip.Dispose()
Write-Host "-> P05 Hall coordinates loaded: $($hallCoords.Count) municipalities"

# ------------------------------------------------------------------------------
# 2. Load Soumu Municipality Code Excel (Sheet 1: Prefs & Munis, Sheet 2: Wards)
# ------------------------------------------------------------------------------
Write-Host "[2/6] Loading Soumu Municipality Codes..."
$xlsxPath = Join-Path $rawDir "soumu_municipality_codes.xlsx"
$zip = [System.IO.Compression.ZipFile]::OpenRead($xlsxPath)
$ssEntry = $zip.GetEntry("xl/sharedStrings.xml")
$sr = New-Object System.IO.StreamReader($ssEntry.Open(), [System.Text.Encoding]::UTF8)
[xml]$ssXml = $sr.ReadToEnd()
$sr.Dispose()

$sharedStrings = [System.Collections.Generic.List[string]]::new()
foreach ($si in $ssXml.sst.si) {
    if ($null -ne $si.t) {
        if ($si.t -is [string]) { $sharedStrings.Add($si.t) }
        else { $sharedStrings.Add($si.t.InnerText) }
    } elseif ($null -ne $si.r) {
        $txt = ($si.r | ForEach-Object { if ($_.t -is [string]) { $_.t } else { $_.t.InnerText } }) -join ""
        $sharedStrings.Add($txt)
    } else {
        $sharedStrings.Add("")
    }
}

function Read-Sheet($entryName) {
    $e = $zip.GetEntry($entryName)
    $sr = New-Object System.IO.StreamReader($e.Open(), [System.Text.Encoding]::UTF8)
    [xml]$shXml = $sr.ReadToEnd()
    $sr.Dispose()
    $rows = [System.Collections.Generic.List[PSCustomObject]]::new()
    foreach ($row in $shXml.worksheet.sheetData.row) {
        if ([int]$row.r -eq 1) { continue }
        $vals = @{"A"=""; "B"=""; "C"=""; "D"=""; "E"=""}
        foreach ($c in $row.c) {
            $col = ($c.r -replace '\d+', '')
            $v = ""
            if ($null -ne $c.v) {
                if ($c.t -eq "s") { $v = $sharedStrings[[int]$c.v] }
                else { $v = [string]$c.v }
            }
            $vals[$col] = $v.Trim()
        }
        if ($vals["A"]) {
            $rows.Add([PSCustomObject]@{
                Code = $vals["A"].PadLeft(6, '0')
                Pref = $vals["B"]
                Muni = $vals["C"]
                PrefKana = $vals["D"]
                MuniKana = $vals["E"]
            })
        }
    }
    return $rows
}

$sheet1 = Read-Sheet "xl/worksheets/sheet1.xml"
$sheet2 = Read-Sheet "xl/worksheets/sheet2.xml"
$zip.Dispose()

$prefRows = $sheet1 | Where-Object { [string]::IsNullOrEmpty($_.Muni) }
$muniRows = $sheet1 | Where-Object { -not [string]::IsNullOrEmpty($_.Muni) }
$wardRows = $sheet2 | Where-Object { $_.Muni -match "区$" -and $_.Muni -notmatch "^.+市$" }
Write-Host "-> Soumu: Prefs=$($prefRows.Count), Munis=$($muniRows.Count), Wards=$($wardRows.Count)"

$desigCities = [System.Collections.Generic.HashSet[string]]::new([string[]]@(
    '札幌市', '仙台市', 'さいたま市', '千葉市', '横浜市', '川崎市', '相模原市',
    '新潟市', '静岡市', '浜松市', '名古屋市', '京都市', '大阪市', '堺市',
    '神戸市', '岡山市', '広島市', '北九州市', '福岡市', '熊本市'
))
$coreCities = [System.Collections.Generic.HashSet[string]]::new([string[]]@(
    '函館市', '旭川市', '青森市', '八戸市', '盛岡市', '秋田市', '山形市', '福島市',
    '郡山市', 'いわき市', '水戸市', '宇都宮市', '前橋市', '高崎市', '川越市',
    '越谷市', '川口市', '船橋市', '柏市', '八王子市', '横須賀市', '富山市',
    '金沢市', '福井市', '甲府市', '長野市', '松本市', '岐阜市', '豊橋市',
    '岡崎市', '一宮市', '豊田市', '大津市', '豊中市', '吹田市', '高槻市',
    '枚方市', '八尾市', '寝屋川市', '東大阪市', '姫路市', '尼崎市', '明石市',
    '西宮市', '奈良市', '和歌山市', '鳥取市', '松江市', '倉敷市', '呉市',
    '福山市', '下関市', '高松市', '松山市', '高知市', '久留米市', '長崎市',
    '佐世保市', '大分市', '宮崎市', '鹿児島市', '那覇市'
))
$specialCities = [System.Collections.Generic.HashSet[string]]::new([string[]]@(
    'つくば市', '伊勢崎市', '太田市', '所沢市', '草加市', '春日部市', '熊谷市',
    '小田原市', '大和市', '厚木市', '平塚市', '茅ヶ崎市', '長岡市', '上越市',
    '富士市', '沼津市', '春日井市', '四日市市', '茨木市', '岸和田市', '加古川市',
    '宝塚市', '佐賀市'
))

# ------------------------------------------------------------------------------
# 3. Load JMA Weather Zones (jma_area.json) & Class20 mapping
# ------------------------------------------------------------------------------
Write-Host "[3/6] Loading JMA Weather Zones (jma_area.json)..."
$jmaPath = Join-Path $rawDir "jma_area.json"
$jmaJson = [System.IO.File]::ReadAllText($jmaPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$centers = $jmaJson.centers
$offices = $jmaJson.offices
$class10s = $jmaJson.class10s
$class15s = $jmaJson.class15s
$class20s = $jmaJson.class20s

$code5ToClass20 = @{}
foreach ($prop in $class20s.PSObject.Properties) {
    $c20Code = $prop.Name # 7-digit code like "1310100"
    $c5 = $c20Code.Substring(0, 5)
    if (-not $code5ToClass20.ContainsKey($c5)) {
        $code5ToClass20[$c5] = $c20Code
    }
}
Write-Host "-> JMA: class20s loaded"

# ------------------------------------------------------------------------------
# 4. Extract Gun (Counties) and Subprefectures from Geolonia Addresses
# ------------------------------------------------------------------------------
Write-Host "[4/6] Extracting Gun and Subprefectures..."
$subprefList = @(
    @{ Code="01-SP-01"; Name="空知総合振興局"; PrefCode="01"; Lat=43.198; Lon=141.768 },
    @{ Code="01-SP-02"; Name="石狩振興局";     PrefCode="01"; Lat=43.064; Lon=141.347 },
    @{ Code="01-SP-03"; Name="後志総合振興局"; PrefCode="01"; Lat=42.902; Lon=140.757 },
    @{ Code="01-SP-04"; Name="胆振総合振興局"; PrefCode="01"; Lat=42.347; Lon=140.970 },
    @{ Code="01-SP-05"; Name="日高振興局";     PrefCode="01"; Lat=42.172; Lon=142.766 },
    @{ Code="01-SP-06"; Name="渡島総合振興局"; PrefCode="01"; Lat=41.819; Lon=140.754 },
    @{ Code="01-SP-07"; Name="檜山振興局";     PrefCode="01"; Lat=41.869; Lon=140.128 },
    @{ Code="01-SP-08"; Name="上川総合振興局"; PrefCode="01"; Lat=43.771; Lon=142.365 },
    @{ Code="01-SP-09"; Name="留萌振興局";     PrefCode="01"; Lat=43.934; Lon=141.654 },
    @{ Code="01-SP-10"; Name="宗谷総合振興局"; PrefCode="01"; Lat=45.398; Lon=141.701 },
    @{ Code="01-SP-11"; Name="オホーツク総合振興局"; PrefCode="01"; Lat=44.026; Lon=144.263 },
    @{ Code="01-SP-12"; Name="十勝総合振興局"; PrefCode="01"; Lat=42.924; Lon=143.196 },
    @{ Code="01-SP-13"; Name="釧路総合振興局"; PrefCode="01"; Lat=42.985; Lon=144.385 },
    @{ Code="01-SP-14"; Name="根室振興局";     PrefCode="01"; Lat=43.330; Lon=145.583 },
    @{ Code="13-SP-01"; Name="大島支庁";       PrefCode="13"; Lat=34.752; Lon=139.358 },
    @{ Code="13-SP-02"; Name="三宅支庁";       PrefCode="13"; Lat=34.116; Lon=139.527 },
    @{ Code="13-SP-03"; Name="八丈支庁";       PrefCode="13"; Lat=33.112; Lon=139.791 },
    @{ Code="13-SP-04"; Name="小笠原支庁";     PrefCode="13"; Lat=27.095; Lon=142.193 }
)

$csvPath = Join-Path $rawDir "geolonia_latest_addresses.csv"
$srAddr = New-Object System.IO.StreamReader($csvPath, [System.Text.Encoding]::UTF8)
$null = $srAddr.ReadLine() # header
$gunDict = @{} # "PrefCode|GunName" -> @{ PrefCode, GunName, SampleCode5, Lat, Lon }

while (-not $srAddr.EndOfStream) {
    $line = $srAddr.ReadLine()
    if ([string]::IsNullOrEmpty($line)) { continue }
    $parts = $line.Split(',')
    $pCode = $parts[0].Trim('"')
    $mName = $parts[5].Trim('"')
    if ($mName -notmatch "市$" -and $mName -match "^(.+?郡)(.+[町村])$") {
        $gName = $matches[1]
        $gKey = "$pCode|$gName"
        if (-not $gunDict.ContainsKey($gKey)) {
            $gunDict[$gKey] = @{
                PrefCode = $pCode
                GunName  = $gName
                SampleCode5 = $parts[4].Trim('"')
                Lat = $parts[-2]
                Lon = $parts[-1]
            }
        }
    }
}
$srAddr.Dispose()

# Northern Territories 5 counties in Hokkaido (01)
$ntGuns = @("色丹郡", "国後郡", "択捉郡", "紗那郡", "蘂取郡")
foreach ($nt in $ntGuns) {
    $gKey = "01|$nt"
    if (-not $gunDict.ContainsKey($gKey)) {
        $gunDict[$gKey] = @{ PrefCode="01"; GunName=$nt; SampleCode5=""; Lat=""; Lon="" }
    }
}
Write-Host "-> Loaded Gun (Counties): $($gunDict.Count) (Benchmark: 379)"

# ------------------------------------------------------------------------------
# 5. Build areas.csv records with Parent / Child / Weather IDs
# ------------------------------------------------------------------------------
Write-Host "[5/6] Building areas.csv Records..."

$areaRecords = [System.Collections.Generic.List[PSCustomObject]]::new()
$areaSeq = 0
$prefIdMap = @{}   # PrefCode ("01") -> area_id ("JP-AR-000001")
$subprefIdMap = @{}# Subpref Name -> area_id
$gunIdMap = @{}    # "PrefCode|GunName" -> area_id
$cityIdMap = @{}   # City Name ("大阪市") -> area_id
$c20IdMap = @{}    # Class20 code ("1310100") -> area_id

# (A) Prefectures (47)
foreach ($pr in $prefRows) {
    $areaSeq++
    $aid = ("JP-AR-{0:D6}" -f $areaSeq)
    $pCode = $pr.Code.Substring(0, 2)
    $prefIdMap[$pCode] = $aid

    $typeId = switch ($pr.Pref) {
        "東京都" { "JP_ADMIN_PREF_TO" }
        "北海道" { "JP_ADMIN_PREF_DO" }
        "京都府" { "JP_ADMIN_PREF_FU" }
        "大阪府" { "JP_ADMIN_PREF_FU" }
        default  { "JP_ADMIN_PREF_KEN" }
    }

    $c5 = $pr.Code.Substring(0, 5)
    $lat = ""; $lon = ""
    if ($hallCoords.ContainsKey($c5)) {
        $lat = "{0:F6}" -f $hallCoords[$c5].Lat
        $lon = "{0:F6}" -f $hallCoords[$c5].Lon
    }

    $areaRecords.Add([PSCustomObject]@{
        area_id       = $aid
        country_code  = "JP"
        type_id       = $typeId
        公的コード    = $pr.Code
        親区域ID      = ""
        気象予報区ID  = ""
        名称          = $pr.Pref
        名称_公用語   = $pr.Pref
        代表緯度      = $lat
        代表経度      = $lon
        公式サイトURL = ""
        Wikipedia_url = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($pr.Pref)
        Wikidata_id   = ""
    })
}

# (B) Subprefectures (18: Hokkaido 14 + Tokyo 4)
foreach ($sp in $subprefList) {
    $areaSeq++
    $aid = ("JP-AR-{0:D6}" -f $areaSeq)
    $subprefIdMap[$sp.Name] = $aid
    $parentPrefId = $prefIdMap[$sp.PrefCode]

    $areaRecords.Add([PSCustomObject]@{
        area_id       = $aid
        country_code  = "JP"
        type_id       = "JP_ADMIN_SUBPREF"
        公的コード    = $sp.Code
        親区域ID      = $parentPrefId
        気象予報区ID  = ""
        名称          = $sp.Name
        名称_公用語   = $sp.Name
        代表緯度      = "{0:F6}" -f $sp.Lat
        代表経度      = "{0:F6}" -f $sp.Lon
        公式サイトURL = ""
        Wikipedia_url = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($sp.Name)
        Wikidata_id   = ""
    })
}

# (C) Gun / Counties (379)
foreach ($k in $gunDict.Keys) {
    $areaSeq++
    $aid = ("JP-AR-{0:D6}" -f $areaSeq)
    $gunIdMap[$k] = $aid
    $g = $gunDict[$k]
    $parentPrefId = $prefIdMap[$g.PrefCode]

    $lat = $g.Lat; $lon = $g.Lon
    if (-not $lat -and $g.SampleCode5 -and $hallCoords.ContainsKey($g.SampleCode5)) {
        $lat = "{0:F6}" -f $hallCoords[$g.SampleCode5].Lat
        $lon = "{0:F6}" -f $hallCoords[$g.SampleCode5].Lon
    }

    $areaRecords.Add([PSCustomObject]@{
        area_id       = $aid
        country_code  = "JP"
        type_id       = "JP_ADMIN_GUN"
        公的コード    = ""
        親区域ID      = $parentPrefId
        気象予報区ID  = ""
        名称          = $g.GunName
        名称_公用語   = $g.GunName
        代表緯度      = $lat
        代表経度      = $lon
        公式サイトURL = ""
        Wikipedia_url = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($g.GunName)
        Wikidata_id   = ""
    })
}

# (D) Weather Zones: JMA Class20 (Secondary Weather Warning Zones: 1,805)
foreach ($prop in $class20s.PSObject.Properties) {
    $areaSeq++
    $aid = ("JP-AR-{0:D6}" -f $areaSeq)
    $c20Code = $prop.Name
    $c20Obj  = $prop.Value
    $c20IdMap[$c20Code] = $aid

    $areaRecords.Add([PSCustomObject]@{
        area_id       = $aid
        country_code  = "JP"
        type_id       = "JP_MET_CLASS20"
        公的コード    = $c20Code
        親区域ID      = ""
        気象予報区ID  = ""
        名称          = $c20Obj.name
        名称_公用語   = $c20Obj.name
        代表緯度      = ""
        代表経度      = ""
        公式サイトURL = "https://www.jma.go.jp/bosai/forecast/"
        Wikipedia_url = "https://ja.wikipedia.org/wiki/%E6%B0%97%E8%B1%A1%E4%BA%88%E5%A0%B1%E5%8C%BA"
        Wikidata_id   = ""
    })
}

# (E) Municipalities (1,747: Cities, Special Wards, Towns, Villages)
foreach ($m in $muniRows) {
    $areaSeq++
    $aid = ("JP-AR-{0:D6}" -f $areaSeq)
    $pCode = $m.Code.Substring(0, 2)
    $c5    = $m.Code.Substring(0, 5)
    $parentPrefId = $prefIdMap[$pCode]

    # Parent determination: If town/village has Gun, link to Gun!
    $parentId = $parentPrefId
    $dispName = $m.Muni
    if ($m.Muni -notmatch "市$" -and $m.Muni -match "^(.+?郡)(.+[町村])$") {
        $gName = $matches[1]
        $dispName = $matches[2]
        $gKey = "$pCode|$gName"
        if ($gunIdMap.ContainsKey($gKey)) {
            $parentId = $gunIdMap[$gKey]
        }
    }

    # Type determination
    $typeId = "JP_ADMIN_VILLAGE"
    if ($desigCities.Contains($m.Muni)) {
        $typeId = "JP_ADMIN_CITY_DESIGNATED"
        $cityIdMap[$m.Muni] = $aid
    } elseif ($coreCities.Contains($m.Muni)) {
        $typeId = "JP_ADMIN_CITY_CORE"
    } elseif ($specialCities.Contains($m.Muni)) {
        $typeId = "JP_ADMIN_CITY_SPECIAL_EXC"
    } elseif ($m.Muni.EndsWith("市")) {
        $typeId = "JP_ADMIN_CITY_ORDINARY"
    } elseif ($pCode -eq "13" -and $m.Muni.EndsWith("区")) {
        $typeId = "JP_ADMIN_SPECIAL_WARD"
    } elseif ($m.Muni.EndsWith("町")) {
        $typeId = "JP_ADMIN_TOWN"
    } elseif ($m.Muni.EndsWith("村")) {
        $typeId = "JP_ADMIN_VILLAGE"
    }

    # P05 Hall coordinates
    $lat = ""; $lon = ""
    if ($hallCoords.ContainsKey($c5)) {
        $lat = "{0:F6}" -f $hallCoords[$c5].Lat
        $lon = "{0:F6}" -f $hallCoords[$c5].Lon
    }

    # Weather Zone (Class20) linkage
    $wxId = ""
    if ($code5ToClass20.ContainsKey($c5)) {
        $c20Code = $code5ToClass20[$c5]
        if ($c20IdMap.ContainsKey($c20Code)) {
            $wxId = $c20IdMap[$c20Code]
        }
    }

    $areaRecords.Add([PSCustomObject]@{
        area_id       = $aid
        country_code  = "JP"
        type_id       = $typeId
        公的コード    = $m.Code
        親区域ID      = $parentId
        気象予報区ID  = $wxId
        名称          = $dispName
        名称_公用語   = $dispName
        代表緯度      = $lat
        代表経度      = $lon
        公式サイトURL = ""
        Wikipedia_url = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($m.Muni)
        Wikidata_id   = ""
    })
}

# (F) Designated City Wards (171)
foreach ($w in $wardRows) {
    $areaSeq++
    $aid = ("JP-AR-{0:D6}" -f $areaSeq)
    $c5 = $w.Code.Substring(0, 5)

    $parentCityId = ""
    if ($w.Muni -match "^(.+?市)(.+区)$") {
        $cityName = $matches[1]
        $wardName = $matches[2]
        if ($cityIdMap.ContainsKey($cityName)) {
            $parentCityId = $cityIdMap[$cityName]
        }
    } else {
        $wardName = $w.Muni
    }

    $lat = ""; $lon = ""
    if ($hallCoords.ContainsKey($c5)) {
        $lat = "{0:F6}" -f $hallCoords[$c5].Lat
        $lon = "{0:F6}" -f $hallCoords[$c5].Lon
    }

    $wxId = ""
    if ($code5ToClass20.ContainsKey($c5)) {
        $c20Code = $code5ToClass20[$c5]
        if ($c20IdMap.ContainsKey($c20Code)) {
            $wxId = $c20IdMap[$c20Code]
        }
    }

    $areaRecords.Add([PSCustomObject]@{
        area_id       = $aid
        country_code  = "JP"
        type_id       = "JP_ADMIN_WARD"
        公的コード    = $w.Code
        親区域ID      = $parentCityId
        気象予報区ID  = $wxId
        名称          = $wardName
        名称_公用語   = $wardName
        代表緯度      = $lat
        代表経度      = $lon
        公式サイトURL = ""
        Wikipedia_url = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($w.Muni)
        Wikidata_id   = ""
    })
}

# ------------------------------------------------------------------------------
# 6. Save areas.csv to data/staging/JP/ (UTF-8 without BOM)
# ------------------------------------------------------------------------------
Write-Host "[6/6] Saving to $areasCsvPath..."
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("area_id,country_code,type_id,公的コード,親区域ID,気象予報区ID,名称,名称_公用語,代表緯度,代表経度,公式サイトURL,Wikipedia_url,Wikidata_id")

foreach ($r in $areaRecords) {
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
    $lines.Add(($vals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($areasCsvPath, $lines, $utf8NoBom)
Write-Host "-> Successfully generated data/staging/JP/areas.csv: $($lines.Count - 1) records!"

Write-Host "`nBreakdown by type_id in staging areas.csv:"
$areaRecords | Group-Object type_id | Select-Object Name, Count | Format-Table -AutoSize
