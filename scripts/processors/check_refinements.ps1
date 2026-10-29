[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.IO.Compression.FileSystem

$rawDir = "c:\Users\user\Documents\PJT\data\raw\JP"
$stagingDir = "c:\Users\user\Documents\PJT\data\staging\JP"

# 1. Check missing Guns in areas.csv vs Soumu Excel
$xlsxPath = Join-Path $rawDir "soumu_municipality_codes.xlsx"
$zip = [System.IO.Compression.ZipFile]::OpenRead($xlsxPath)
$ssEntry = $zip.GetEntry("xl/sharedStrings.xml")
$sr = New-Object System.IO.StreamReader($ssEntry.Open(), [System.Text.Encoding]::UTF8)
[xml]$ssXml = $sr.ReadToEnd()
$sr.Dispose()

$sharedStrings = [System.Collections.Generic.List[string]]::new()
foreach ($si in $ssXml.sst.si) {
    if ($null -ne $si.t) {
        if ($si.t -is [string]) { $sharedStrings.Add($si.t) } else { $sharedStrings.Add($si.t.InnerText) }
    } elseif ($null -ne $si.r) {
        $txt = ($si.r | ForEach-Object { if ($_.t -is [string]) { $_.t } else { $_.t.InnerText } }) -join ""
        $sharedStrings.Add($txt)
    } else { $sharedStrings.Add("") }
}

$e = $zip.GetEntry("xl/worksheets/sheet1.xml")
$sr = New-Object System.IO.StreamReader($e.Open(), [System.Text.Encoding]::UTF8)
[xml]$shXml = $sr.ReadToEnd()
$sr.Dispose()
$zip.Dispose()

$soumuGuns = @{}
foreach ($row in $shXml.worksheet.sheetData.row) {
    if ([int]$row.r -eq 1) { continue }
    $vals = @{"A"=""; "B"=""; "C"=""}
    foreach ($c in $row.c) {
        $col = ($c.r -replace '\d+', '')
        if ($vals.ContainsKey($col) -and $null -ne $c.v) {
            $vals[$col] = if ($c.t -eq "s") { $sharedStrings[[int]$c.v].Trim() } else { ([string]$c.v).Trim() }
        }
    }
    $code = $vals["A"].PadLeft(6, '0')
    $pCode = $code.Substring(0, 2)
    $muni = $vals["C"]
    if ($muni -notmatch "市$" -and $muni -match "^(.+?郡)(.+[町村])$") {
        $gName = $matches[1]
        $soumuGuns["$pCode|$gName"] = $gName
    }
}
Write-Host "Soumu Unique Guns: $($soumuGuns.Count)"

# 2. Check N06 active joints count without rounding
$n06Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N06_highway.zip"))
$srN06 = New-Object System.IO.StreamReader($n06Zip.GetEntry("UTF-8/N06-23_Joint.geojson").Open(), [System.Text.Encoding]::UTF8)
$rawJoints = 0
$uniqueCodeJoints = [System.Collections.Generic.HashSet[string]]::new()
while (-not $srN06.EndOfStream) {
    $line = $srN06.ReadLine()
    if ($line -match '"N06_014":\s*9999') {
        $rawJoints++
        if ($line -match '"N06_015":\s*"([^"]+)"') { $null = $uniqueCodeJoints.Add($matches[1]) }
    }
}
$srN06.Dispose()
$n06Zip.Dispose()
Write-Host "N06 Raw Active Joints: $rawJoints, Unique N06_015: $($uniqueCodeJoints.Count)"
