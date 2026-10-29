[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.IO.Compression.FileSystem

$zip = [System.IO.Compression.ZipFile]::OpenRead('c:\Users\user\Documents\PJT\data\raw\JP\ksj_N02_railway.zip')
$entry = $zip.GetEntry('UTF-8/N02-23_Station.geojson')
$sr = New-Object System.IO.StreamReader($entry.Open(), [System.Text.Encoding]::UTF8)

$shinkansenLines = [System.Collections.Generic.HashSet[string]]::new()
while (-not $sr.EndOfStream) {
    $line = $sr.ReadLine()
    if ($line -match '"N02_002":\s*"1".*?"N02_003":\s*"([^"]+)"' -or $line -match '"N02_003":\s*"([^"]+)".*?"N02_002":\s*"1"') {
        $null = $shinkansenLines.Add($matches[1])
    }
}
$sr.Dispose()
$zip.Dispose()

Write-Host "N02_002=1 Lines: $($shinkansenLines.Count)"
$shinkansenLines | ForEach-Object { Write-Host " - $_" }
