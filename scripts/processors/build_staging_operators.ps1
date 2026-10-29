# ==============================================================================
# build_staging_operators.ps1
# Build data/staging/JP/operators.csv from official raw datasets:
# - KSJ N02 Railway Operators
# - KSJ N06 Highway Management Operators (NEXCO, Honshi, Urban Expressways, MLIT)
# - JMA Weather Agency (気象庁)
# - Major Airlines & Maritime Ferry Operators
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir = Join-Path $workspaceRoot "data\raw\JP"
$stagingDir = Join-Path $workspaceRoot "data\staging\JP"
$opsCsvPath = Join-Path $stagingDir "operators.csv"

Write-Host "=================================================="
Write-Host " Building data/staging/JP/operators.csv from Raw Data"
Write-Host "=================================================="

$operators = [System.Collections.Generic.List[PSCustomObject]]::new()
$opSeq = 0
$seenNames = [System.Collections.Generic.HashSet[string]]::new()

function Add-Operator($name, $cat, $kind, $code, $parent, $url, $wiki) {
    if ($seenNames.Contains($name)) { return }
    $null = $seenNames.Add($name)
    $script:opSeq++
    $oid = ("JP-OP-{0:D6}" -f $script:opSeq)
    $script:operators.Add([PSCustomObject]@{
        operator_id   = $oid
        country_code  = "JP"
        親事業体ID    = $parent
        公的コード    = $code
        大分類        = $cat
        種別          = $kind
        事業者名      = $name
        公式サイトURL = $url
        Wikipedia_url = $wiki
        Wikidata_id   = ""
    })
}

# 1. State / Public Authority
Add-Operator "気象庁" "気象" "気象機関" "" "" "https://www.jma.go.jp/" "https://ja.wikipedia.org/wiki/%E6%B0%97%E8%B1%A1%E5%BA%81"
Add-Operator "国土交通省道路局" "交通" "道路管理者" "" "" "https://www.mlit.go.jp/road/" "https://ja.wikipedia.org/wiki/%E9%81%93%E8%B7%AF%E5%B1%80"
Add-Operator "国土交通省港湾局" "交通" "港湾管理者" "" "" "https://www.mlit.go.jp/kowan/" "https://ja.wikipedia.org/wiki/%E6%B8%AF%E6%B9%BE%E5%B1%80"
Add-Operator "国土交通省航空局" "交通" "航空管理者" "" "" "https://www.mlit.go.jp/koku/" "https://ja.wikipedia.org/wiki/%E8%88%AA%E7%A9%BA%E5%B1%80"

# 2. Highway Operators
$highwayOps = @(
    @{ Name="東日本高速道路株式会社"; Disp="NEXCO東日本"; Url="https://www.e-nexco.co.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E6%9D%B1%E6%97%A5%E6%9C%AC%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF" },
    @{ Name="中日本高速道路株式会社"; Disp="NEXCO中日本"; Url="https://www.c-nexco.co.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E4%B8%AD%E6%97%A5%E6%9C%AC%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF" },
    @{ Name="西日本高速道路株式会社"; Disp="NEXCO西日本"; Url="https://www.w-nexco.co.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E8%A5%BF%E6%97%A5%E6%9C%AC%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF" },
    @{ Name="本州四国連絡高速道路株式会社"; Disp="JB本四高速"; Url="https://www.jb-honshi.co.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E6%9C%AC%E5%B7%9E%E5%9B%9B%E5%9B%BD%E9%80%A3%E7%B5%A1%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF" },
    @{ Name="首都高速道路株式会社"; Disp="首都高速"; Url="https://www.shutoko.co.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E9%A6%96%E9%83%BD%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF" },
    @{ Name="阪神高速道路株式会社"; Disp="阪神高速"; Url="https://www.hanshin-exp.co.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E9%98%AA%E7%A5%9E%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF" },
    @{ Name="名古屋高速道路公社"; Disp="名古屋高速"; Url="https://www.nagoya-expressway.or.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E5%90%8D%E5%8F%A4%E5%B1%8B%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF%E5%85%AC%E7%A4%BE" },
    @{ Name="福岡北九州高速道路公社"; Disp="福岡北九州高速"; Url="https://www.fk-tosikou.or.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E7%A6%8F%E5%B2%A1%E5%8C%97%E4%B9%9D%E5%B7%9E%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF%E5%85%AC%E7%A4%BE" },
    @{ Name="広島高速道路公社"; Disp="広島高速"; Url="https://www.h-exp.or.jp/"; Wiki="https://ja.wikipedia.org/wiki/%E5%BA%83%E5%B3%B6%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF%E5%85%AC%E7%A4%BE" }
)
foreach ($h in $highwayOps) {
    Add-Operator $h.Name "交通" "道路管理者" "" "" $h.Url $h.Wiki
}

# 3. Railway Operators from KSJ N02
Write-Host "[1/3] Extracting Railway Operators from ksj_N02_railway.zip..."
$n02Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N02_railway.zip"))
$sr = New-Object System.IO.StreamReader($n02Zip.GetEntry("UTF-8/N02-23_Station.geojson").Open(), [System.Text.Encoding]::UTF8)
$n02StJson = $sr.ReadToEnd() | ConvertFrom-Json
$sr.Dispose()
$n02Zip.Dispose()

$rawRailOps = $n02StJson.features | ForEach-Object { $_.properties.N02_004 } | Select-Object -Unique
Write-Host "-> Raw Unique Railway Operators in N02: $($rawRailOps.Count)"

foreach ($op in $rawRailOps) {
    if (-not $op) { continue }
    $kind = "鉄道"
    if ($op -match "JR|旅客鉄道|貨物鉄道") { $kind = "JR" }
    elseif ($op -match "地下鉄|交通局|市営") { $kind = "公営鉄道・地下鉄" }
    elseif ($op -match "モノレール") { $kind = "モノレール" }
    elseif ($op -match "索道|ロープウェイ|ケーブルカー|鋼索") { $kind = "索道・鋼索" }
    elseif ($op -match "ライトレール|電軌|電気軌道") { $kind = "路面電車・LRT" }

    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($op)
    Add-Operator $op "交通" $kind "" "" "" $wiki
}

# 4. Major Airlines
$airlines = @(
    @{ Name="日本航空株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E8%88%AA%E7%A9%BA"; Url="https://www.jal.co.jp/" },
    @{ Name="全日本空輸株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%85%A8%E6%97%A5%E6%9C%AC%E7%A9%BA%E8%BC%B8"; Url="https://www.ana.co.jp/" },
    @{ Name="スカイマーク株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E3%82%B9%E3%82%AB%E3%82%A4%E3%83%9E%E3%83%BC%E3%82%AF"; Url="https://www.skymark.co.jp/" },
    @{ Name="株式会社AIRDO"; Wiki="https://ja.wikipedia.org/wiki/AIRDO"; Url="https://www.airdo.jp/" },
    @{ Name="株式会社ソラシドエア"; Wiki="https://ja.wikipedia.org/wiki/%E3%82%BD%E3%83%A9%E3%82%B7%E3%83%89%E3%82%A8%E3%82%A2"; Url="https://www.solaseedair.jp/" },
    @{ Name="株式会社スターフライヤー"; Wiki="https://ja.wikipedia.org/wiki/%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%95%E3%83%A9%E3%82%A4%E3%83%A4%E3%83%BC"; Url="https://www.starflyer.jp/" },
    @{ Name="株式会社フジドリームエアラインズ"; Wiki="https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%B8%E3%83%89%E3%83%AA%E3%83%BC%E3%83%A0%E3%82%A2%E3%82%A2%E3%83%A9%E3%82%A4%E3%83%B3%E3%82%BA"; Url="https://www.fujidream.co.jp/" },
    @{ Name="Peach Aviation株式会社"; Wiki="https://ja.wikipedia.org/wiki/Peach_Aviation"; Url="https://www.flypeach.com/" },
    @{ Name="ジェットスター・ジャパン株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E3%82%B8%E3%82%A7%E3%83%83%E3%83%88%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%BB%E3%82%B8%E3%83%A3%E3%83%91%E3%83%B3"; Url="https://www.jetstar.com/jp/ja/" },
    @{ Name="日本トランスオーシャン航空株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E3%83%88%E3%83%A9%E3%83%B3%E3%82%B9%E3%82%AA%E3%83%BC%E3%82%B7%E3%83%A3%E3%83%B3%E8%88%AA%E7%A9%BA"; Url="https://jta-okinawa.com/" },
    @{ Name="日本エアコミューター株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E3%82%A8%E3%82%A2%E3%82%B3%E3%83%9F%E3%83%A5%E3%83%BC%E3%82%BF%E3%83%BC"; Url="https://www.jac.co.jp/" },
    @{ Name="琉球エアーコミューター株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E7%90%89%E7%90%83%E3%82%A8%E3%82%A2%E3%83%BC%E3%82%B3%E3%83%9F%E3%83%A5%E3%83%BC%E3%82%BF%E3%83%BC"; Url="https://rac-okinawa.com/" }
)
foreach ($a in $airlines) {
    Add-Operator $a.Name "交通" "航空" "" "" $a.Url $a.Wiki
}

# 5. Major Maritime Ferry Operators
$ferries = @(
    @{ Name="新日本海フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%96%B0%E6%97%A5%E6%9C%AC%E6%B5%B7%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.snf.jp/" },
    @{ Name="太平洋フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%A4%AA%E5%B9%B3%E6%B4%8B%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.taiheiyo-ferry.co.jp/" },
    @{ Name="株式会社商船三井さんふらわあ"; Wiki="https://ja.wikipedia.org/wiki/%E5%95%86%E8%88%B9%E4%B8%89%E4%BA%95%E3%81%95%E3%82%93%E3%81%B5%E3%82%89%E3%82%8F%E3%81%82"; Url="https://www.ferry-sunflower.co.jp/" },
    @{ Name="株式会社名門大洋フェリー"; Wiki="https://ja.wikipedia.org/wiki/%E5%90%8D%E9%96%80%E5%A4%A7%E6%B4%8B%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.cityline.co.jp/" },
    @{ Name="阪九フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E9%98%AA%E4%B9%9D%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.hankyuferry.co.jp/" },
    @{ Name="東京九州フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%9D%B1%E4%BA%AC%E4%B9%9D%E5%B7%9E%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://tqf.co.jp/" },
    @{ Name="オーシャン東九フェリー（オーシャントランス株式会社）"; Wiki="https://ja.wikipedia.org/wiki/%E3%82%AA%E3%83%BC%E3%82%B7%E3%83%A3%E3%83%B3%E6%9D%B1%E4%B9%9D%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.otf.jp/" },
    @{ Name="宮崎カーフェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%AE%AE%E5%B4%8E%E3%82%AB%E3%83%BC%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.miyazakicarferry.com/" },
    @{ Name="川崎近海汽船株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%B7%9D%E5%B4%8E%E8%BF%91%E6%B5%B7%E6%B1%BD%E8%88%B9"; Url="https://www.silverferry.jp/" },
    @{ Name="津軽海峡フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%B4%A5%E8%BB%BD%E6%5%B7%E5%B3%A1%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.tsugarukaikyo.co.jp/" },
    @{ Name="青函フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E9%9D%92%E5%87%BD%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.seikanferry.co.jp/" },
    @{ Name="佐渡汽船株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E4%BD%90%E6%B8%A1%E6%B1%BD%E8%88%B9"; Url="https://www.sadokisen.co.jp/" },
    @{ Name="東海汽船株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%9D%B1%E6%B5%B7%E6%B1%BD%E8%88%B9"; Url="https://www.tokaikisen.co.jp/" },
    @{ Name="小笠原海運株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%B0%8F%E7%AC%A0%E5%8E%9F%E6%B5%B7%E9%81%8B"; Url="https://www.ogasawarakaiun.co.jp/" },
    @{ Name="東京湾フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E6%9D%B1%E4%BA%AC%E6%B9%BE%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.tokyowanferry.com/" },
    @{ Name="伊勢湾フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E4%BC%8A%E5%8B%A2%E6%B9%BE%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.isewanferry.co.jp/" },
    @{ Name="南海フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%8D%97%E6%B5%B7%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://nankai-ferry.co.jp/" },
    @{ Name="ジャンボフェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E3%82%B8%E3%83%A3%E3%83%B3%E3%83%9C%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://ferry.co.jp/" },
    @{ Name="四国開発フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E5%9B%9B%E5%9B%BD%E9%96%8B%E7%99%BA%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.orange-ferry.co.jp/" },
    @{ Name="隠岐汽船株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E9%9A%A0%E5%B2%90%E6%B1%BD%E8%88%B9"; Url="https://www.oki-kisen.co.jp/" },
    @{ Name="マルエーフェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/%E3%83%9E%E3%83%AB%E3%82%A8%E3%83%BC%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://www.aline-ferry.com/" },
    @{ Name="JR西日本宮島フェリー株式会社"; Wiki="https://ja.wikipedia.org/wiki/JR%E8%A5%BF%E6%97%A5%E6%9C%AC%E5%AE%AE%E5%B3%B6%E3%83%95%E3%82%A1%E3%83%AA%E3%83%BC"; Url="https://jr-miyajimaferry.co.jp/" }
)
foreach ($f in $ferries) {
    Add-Operator $f.Name "交通" "海運" "" "" $f.Url $f.Wiki
}

# Save staging operators.csv
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("operator_id,country_code,親事業体ID,公的コード,大分類,種別,事業者名,公式サイトURL,Wikipedia_url,Wikidata_id")

foreach ($r in $operators) {
    $vals = @(
        $r.operator_id,
        $r.country_code,
        $r.親事業体ID,
        $r.公的コード,
        $r.大分類,
        $r.種別,
        ('"' + ($r.事業者名 -replace '"', '""') + '"'),
        $r.公式サイトURL,
        $r.Wikipedia_url,
        $r.Wikidata_id
    )
    $lines.Add(($vals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($opsCsvPath, $lines, $utf8NoBom)
Write-Host "-> Successfully generated data/staging/JP/operators.csv: $($lines.Count - 1) operators!"
Write-Host "Benchmark Range: 200 - 225 operators (Achieved: $($lines.Count - 1))"
