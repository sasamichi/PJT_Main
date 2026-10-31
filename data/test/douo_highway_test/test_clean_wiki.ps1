# test_clean_wiki.ps1
$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
$wikiText = [System.IO.File]::ReadAllText((Join-Path $testDir "wikipedia_douo_wikitext.txt"), [System.Text.Encoding]::UTF8)

function Clean-Wikitext($text) {
    if (-not $text) { return "" }
    $t = $text -replace '(?s)<ref[^>]*>.*?</ref>', ''
    $t = $t -replace '<ref[^>]*/>', ''
    $t = $t -replace '<[^>]+>', ''
    $t = $t -replace '\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', '$1'
    $t = $t -replace '\{\{[^}]+\}\}', ''
    $t = $t -replace '\[http[^\s\]]+\s+([^\]]+)\]', '$1'
    $t = $t -replace '\[http[^\]]+\]', ''
    $t = $t -replace '^style=[^|]*\|', ''
    $t = $t -replace '^[!|]', ''
    $t = $t -replace '^style=[^|]*\|', ''
    $t = $t -replace "'''", ''
    $t = $t -replace "''", ''
    return $t.Trim()
}

if ($wikiText -match '(?s)==\s*インターチェンジなど\s*==\r?\n(.*?)\r?\n==[^=]') {
    $sec = $matches[1]
    $rows = $sec -split '\r?\n\|-'
    
    $results = @()
    $currSubPref = ""
    $currMuni = ""

    foreach ($r in $rows) {
        if ($r -match '\[\[([^\]|]+総合振興局|[^\]|]+振興局)\]\]') {
            $currSubPref = $matches[1]
        }
        if ($r -match '\[\[([^\]|]+(?:町|市|村))\]\]') {
            $currMuni = $matches[1]
        }

        $lines = ($r -split '\r?\n') | Where-Object { $_ -match '^[|!]' }
        if ($lines.Count -ge 2) {
            $ic = Clean-Wikitext $lines[0]
            $name = Clean-Wikitext $lines[1]
            $routes = if ($lines.Count -ge 3) { Clean-Wikitext $lines[2] } else { "" }
            $sDist = if ($lines.Count -ge 4) { Clean-Wikitext $lines[3] } else { "" }
            $nDist = if ($lines.Count -ge 5) { Clean-Wikitext $lines[4] } else { "" }
            $bs = if ($lines.Count -ge 6) { Clean-Wikitext $lines[5] } else { "" }
            $gs = if ($lines.Count -ge 7) { Clean-Wikitext $lines[6] } else { "" }
            $remarks = if ($lines.Count -ge 8) { Clean-Wikitext $lines[7] } else { "" }

            # 施設行判定
            if ($name -match 'IC|JCT|SA|PA|料金所|バス|ストップ|仮称|展望所') {
                $results += [PSCustomObject]@{
                    IC        = $ic
                    Name      = $name
                    Routes    = $routes
                    SapporoKm = $sDist
                    NanaeKm   = $nDist
                    BS        = $bs
                    GS        = $gs
                    Remarks   = $remarks
                    SubPref   = $currSubPref
                    Muni      = $currMuni
                }
            }
        }
    }

    Write-Host "抽出できた施設行数: $($results.Count)"
    $results | Select-Object -First 15 | Format-Table -AutoSize
}
