# ==============================================================================
# build_staging_transport_routes.ps1
# Build data/staging/JP/transport_routes.csv from:
# - KSJ N02 Railway lines (Unique Operator + LineName)
# - KSJ N06 Expressways & Urban Expressways
# - National Highways (1 to 507, excluding 48 missing numbers = 459 routes)
# - Major Maritime Passenger Ferries
# - Major Domestic Airlines Routes
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$workspaceRoot = "c:\Users\user\Documents\PJT"
$rawDir = Join-Path $workspaceRoot "data\raw\JP"
$stagingDir = Join-Path $workspaceRoot "data\staging\JP"
$routesCsvPath = Join-Path $stagingDir "transport_routes.csv"

Write-Host "=================================================="
Write-Host " Building data/staging/JP/transport_routes.csv"
Write-Host "=================================================="

# Load operators mapping
$opsCsvPath = Join-Path $stagingDir "operators.csv"
$ops = Import-Csv $opsCsvPath -Encoding UTF8
$opMap = @{}
foreach ($o in $ops) {
    $opMap[$o.事業者名] = $o.operator_id
}
$mlitRoadOpId = $opMap["国土交通省道路局"]
if (-not $mlitRoadOpId) { $mlitRoadOpId = "JP-OP-000002" }

$routes = [System.Collections.Generic.List[PSCustomObject]]::new()
$rtSeq = 0
$seenRouteKeys = [System.Collections.Generic.HashSet[string]]::new()

function Add-Route($opId, $cat, $kind, $code, $name, $nameJa, $url, $wiki) {
    $key = "$opId|$kind|$name"
    if ($seenRouteKeys.Contains($key)) { return }
    $null = $seenRouteKeys.Add($key)
    $script:rtSeq++
    $rid = ("JP-RT-{0:D6}" -f $script:rtSeq)
    $script:routes.Add([PSCustomObject]@{
        route_id        = $rid
        country_code    = "JP"
        operator_id     = $opId
        大分類          = $cat
        種別            = $kind
        "路線記号・番号" = $code
        路線名          = $name
        路線名_公用語    = $nameJa
        公式サイトURL   = $url
        Wikipedia_url   = $wiki
        Wikidata_id     = ""
    })
}

# ------------------------------------------------------------------------------
# 1. National Highways (一般国道459路線)
# ------------------------------------------------------------------------------
Write-Host "[1/5] Adding 459 National Highways (一般国道)..."
$missingNationalHighways = [System.Collections.Generic.HashSet[int]]::new()
for ($i = 59; $i -le 100; $i++) { $null = $missingNationalHighways.Add($i) }
foreach ($m in @(109, 110, 111, 214, 215, 216)) { $null = $missingNationalHighways.Add($m) }

$nhCount = 0
for ($num = 1; $num -le 507; $num++) {
    if ($missingNationalHighways.Contains($num)) { continue }
    $rName = "国道$($num)号"
    $rCode = "$num"
    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($rName)
    Add-Route $mlitRoadOpId "陸上交通" "一般国道" $rCode $rName $rName "https://www.mlit.go.jp/road/" $wiki
    $nhCount++
}
Write-Host "-> Added $nhCount National Highways."

# ------------------------------------------------------------------------------
# 2. Expressways & Urban Expressways from KSJ N06
# ------------------------------------------------------------------------------
Write-Host "[2/5] Adding Expressways & Urban Expressways from KSJ N06..."
$n06Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N06_highway.zip"))
$entryN06 = $n06Zip.GetEntry("UTF-8/N06-23_HighwaySection.geojson")
$sr = New-Object System.IO.StreamReader($entryN06.Open(), [System.Text.Encoding]::UTF8)

function Get-HighwayOpId($hName) {
    if ($hName -match "^首都高速") { return $opMap["首都高速道路株式会社"] }
    if ($hName -match "^阪神高速") { return $opMap["阪神高速道路株式会社"] }
    if ($hName -match "^名古屋高速") { return $opMap["名古屋高速道路公社"] }
    if ($hName -match "^福岡高速|^北九州高速") { return $opMap["福岡北九州高速道路公社"] }
    if ($hName -match "^広島高速") { return $opMap["広島高速道路公社"] }
    if ($hName -match "本州四国|神戸淡路鳴門|瀬戸中央|西瀬戸") { return $opMap["本州四国連絡高速道路株式会社"] }
    if ($hName -match "東名|新東名|中央|伊勢湾岸|東海環状|新名神") { return $opMap["中日本高速道路株式会社"] }
    if ($hName -match "名神|中国自動車道|山陽自動車道|九州自動車道|長崎自動車道|大分自動車道|宮崎自動車道|沖縄自動車道|高知自動車道|徳島自動車道|松山自動車道|高松自動車道|西名阪|阪和|近畿自動車道|播磨|京都縦貫") {
        return $opMap["西日本高速道路株式会社"]
    }
    if ($hName -match "東北|八戸|秋田|山形|磐越|常磐|関越|上信越|長野|北陸|道央|札樽|道東|道南") {
        return $opMap["東日本高速道路株式会社"]
    }
    return $opMap["国土交通省道路局"]
}

$hwLines = [System.Collections.Generic.HashSet[string]]::new()
while (-not $sr.EndOfStream) {
    $line = $sr.ReadLine()
    if ($line -match '"N06_003":\s*9999' -and $line -match '"N06_007":\s*"([^"]+)"') {
        $null = $hwLines.Add($matches[1])
    }
}
$sr.Dispose()
$n06Zip.Dispose()

foreach ($h in $hwLines) {
    $opId = Get-HighwayOpId $h
    if (-not $opId) { $opId = $mlitRoadOpId }
    $kind = if ($h -match "高速.*[0-9]+号|都心環状|湾岸線|白川線|小牧線|一宮線") { "都市高速" } else { "高速道路" }
    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($h)
    Add-Route $opId "陸上交通" $kind "" $h $h "" $wiki
}
Write-Host "-> Added $($hwLines.Count) Expressways & Urban Expressways."

# ------------------------------------------------------------------------------
# 3. Railway Lines from KSJ N02
# ------------------------------------------------------------------------------
Write-Host "[3/5] Adding Railway Lines from KSJ N02..."
$n02Zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rawDir "ksj_N02_railway.zip"))
$entryN02 = $n02Zip.GetEntry("UTF-8/N02-23_Station.geojson")
$sr = New-Object System.IO.StreamReader($entryN02.Open(), [System.Text.Encoding]::UTF8)

$railPairs = [System.Collections.Generic.Dictionary[string, PSCustomObject]]::new()
while (-not $sr.EndOfStream) {
    $line = $sr.ReadLine()
    if ($line -match '"N02_003":\s*"([^"]+)"' -and $line -match '"N02_004":\s*"([^"]+)"') {
        $c3 = ""
        $c4 = ""
        $c1 = ""
        $c2 = ""
        if ($line -match '"N02_001":\s*"([^"]+)"') { $c1 = $matches[1] }
        if ($line -match '"N02_002":\s*"([^"]+)"') { $c2 = $matches[1] }
        if ($line -match '"N02_003":\s*"([^"]+)"') { $c3 = $matches[1] }
        if ($line -match '"N02_004":\s*"([^"]+)"') { $c4 = $matches[1] }
        
        if ($c3 -and $c4) {
            $pairKey = "$c4|$c3"
            if (-not $railPairs.ContainsKey($pairKey)) {
                $railPairs[$pairKey] = [PSCustomObject]@{ Op=$c4; Line=$c3; Code1=$c1; Code2=$c2 }
            }
        }
    }
}
$sr.Dispose()
$n02Zip.Dispose()

foreach ($rp in $railPairs.Values) {
    $opId = $opMap[$rp.Op]
    if (-not $opId) {
        foreach ($k in $opMap.Keys) {
            if ($k -match [regex]::Escape($rp.Op) -or $rp.Op -match [regex]::Escape($k)) {
                $opId = $opMap[$k]
                break
            }
        }
    }
    if (-not $opId) { $opId = "JP-OP-000000" }

    $kind = "鉄道"
    if ($rp.Code2 -eq "1" -or $rp.Line -match "新幹線") {
        $kind = "新幹線"
    } elseif ($rp.Code1 -eq "13" -or $rp.Line -match "鋼索|ケーブルカー|ロープウェイ") {
        $kind = "索道・鋼索"
    } elseif ($rp.Code1 -in @("14", "15", "23") -or $rp.Line -match "モノレール" -or $rp.Op -match "モノレール") {
        $kind = "モノレール"
    } elseif ($rp.Code1 -eq "21" -or $rp.Line -match "軌道|電軌|路面電車|トラム" -or $rp.Op -match "電気軌道|軌道|路面電車") {
        $kind = "路面電車・LRT"
    } elseif ($rp.Code1 -in @("22", "24", "25") -or $rp.Line -match "新交通|ライナー|ゆりかもめ|ニュートラム|リニモ") {
        $kind = "新交通システム"
    } elseif ($rp.Code1 -eq "16" -or $rp.Line -match "地下鉄|高速鉄道" -or $rp.Op -match "地下鉄|交通局|市営地下鉄") {
        $kind = "地下鉄"
    }

    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($rp.Line)
    Add-Route $opId "陸上交通" $kind "" $rp.Line $rp.Line "" $wiki
}
Write-Host "-> Added $($railPairs.Count) Railway Lines."

# ------------------------------------------------------------------------------
# 4. Major Maritime Passenger Ferries
# ------------------------------------------------------------------------------
Write-Host "[4/5] Adding Major Maritime Passenger Ferry Routes..."
$ferryRoutes = @(
    @{ Op="新日本海フェリー株式会社"; Name="舞鶴 - 小樽 航路"; Code="F-SNF-01" },
    @{ Op="新日本海フェリー株式会社"; Name="敦賀 - 苫小牧東 航路"; Code="F-SNF-02" },
    @{ Op="新日本海フェリー株式会社"; Name="新潟 - 小樽 航路"; Code="F-SNF-03" },
    @{ Op="太平洋フェリー株式会社"; Name="名古屋 - 仙台 - 苫小牧 航路"; Code="F-TAI-01" },
    @{ Op="株式会社商船三井さんふらわあ"; Name="大洗 - 苫小牧 航路"; Code="F-SUN-01" },
    @{ Op="株式会社商船三井さんふらわあ"; Name="大阪 - 志布志 航路"; Code="F-SUN-02" },
    @{ Op="株式会社商船三井さんふらわあ"; Name="大阪 - 別府 航路"; Code="F-SUN-03" },
    @{ Op="株式会社商船三井さんふらわあ"; Name="神戸 - 大分 航路"; Code="F-SUN-04" },
    @{ Op="株式会社名門大洋フェリー"; Name="大阪南港 - 新門司 航路"; Code="F-CTY-01" },
    @{ Op="阪九フェリー株式会社"; Name="泉大津・神戸六甲 - 新門司 航路"; Code="F-HAN-01" },
    @{ Op="東京九州フェリー株式会社"; Name="横須賀 - 新門司 航路"; Code="F-TQF-01" },
    @{ Op="オーシャン東九フェリー（オーシャントランス株式会社）"; Name="東京 - 徳島 - 新門司 航路"; Code="F-OTF-01" },
    @{ Op="宮崎カーフェリー株式会社"; Name="神戸 - 宮崎 航路"; Code="F-MIY-01" },
    @{ Op="川崎近海汽船株式会社"; Name="八戸 - 苫小牧 航路（シルバーフェリー）"; Code="F-KKK-01" },
    @{ Op="津軽海峡フェリー株式会社"; Name="青森 - 函館 航路"; Code="F-TSU-01" },
    @{ Op="津軽海峡フェリー株式会社"; Name="大間 - 函館 航路"; Code="F-TSU-02" },
    @{ Op="津軽海峡フェリー株式会社"; Name="室蘭 - 青森 航路"; Code="F-TSU-03" },
    @{ Op="青函フェリー株式会社"; Name="青森 - 函館 航路"; Code="F-SEI-01" },
    @{ Op="佐渡汽船株式会社"; Name="新潟 - 両津 航路"; Code="F-SAD-01" },
    @{ Op="佐渡汽船株式会社"; Name="直江津 - 小木 航路"; Code="F-SAD-02" },
    @{ Op="東海汽船株式会社"; Name="東京（竹芝） - 伊豆諸島 航路"; Code="F-TOK-01" },
    @{ Op="小笠原海運株式会社"; Name="東京（竹芝） - 父島（二見） 航路（おがさわら丸）"; Code="F-OGA-01" },
    @{ Op="東京湾フェリー株式会社"; Name="久里浜 - 金谷 航路"; Code="F-TWF-01" },
    @{ Op="伊勢湾フェリー株式会社"; Name="鳥羽 - 伊良湖 航路"; Code="F-ISE-01" },
    @{ Op="南海フェリー株式会社"; Name="和歌山港 - 徳島港 航路"; Code="F-NAN-01" },
    @{ Op="ジャンボフェリー株式会社"; Name="神戸（三宮） - 高松（東港） 航路"; Code="F-JUM-01" },
    @{ Op="四国開発フェリー株式会社"; Name="大阪・神戸 - 新居浜・東予 航路（オレンジフェリー）"; Code="F-ORA-01" },
    @{ Op="隠岐汽船株式会社"; Name="七類・境港 - 隠岐諸島 航路"; Code="F-OKI-01" },
    @{ Op="マルエーフェリー株式会社"; Name="鹿児島 - 奄美 - 那覇 航路"; Code="F-ALI-01" },
    @{ Op="JR西日本宮島フェリー株式会社"; Name="宮島口 - 宮島 航路"; Code="F-MIJ-01" }
)
foreach ($fr in $ferryRoutes) {
    $opId = $opMap[$fr.Op]
    if (-not $opId) { $opId = $opMap["国土交通省港湾局"] }
    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($fr.Name)
    Add-Route $opId "航路・空路" "旅客航路" $fr.Code $fr.Name $fr.Name "" $wiki
}
Write-Host "-> Added $($ferryRoutes.Count) Major Maritime Ferry Routes."

# ------------------------------------------------------------------------------
# 5. Major Domestic Airline Routes
# ------------------------------------------------------------------------------
Write-Host "[5/5] Adding Major Domestic Airline Routes..."
$anaOpId = $opMap["全日本空輸株式会社"]

$airRoutes = @(
    @{ Name="東京（羽田） - 札幌（新千歳）線"; Code="HND-CTS" },
    @{ Name="東京（羽田） - 福岡線"; Code="HND-FUK" },
    @{ Name="東京（羽田） - 那覇線"; Code="HND-OKA" },
    @{ Name="東京（羽田） - 大阪（伊丹）線"; Code="HND-ITM" },
    @{ Name="東京（羽田） - 大阪（関西）線"; Code="HND-KIX" },
    @{ Name="東京（羽田） - 鹿児島線"; Code="HND-KOJ" },
    @{ Name="東京（羽田） - 熊本線"; Code="HND-KMJ" },
    @{ Name="東京（羽田） - 広島線"; Code="HND-HIJ" },
    @{ Name="東京（羽田） - 松山線"; Code="HND-MYJ" },
    @{ Name="東京（羽田） - 高松線"; Code="HND-TAK" },
    @{ Name="東京（羽田） - 小松線"; Code="HND-KMQ" },
    @{ Name="東京（羽田） - 富山線"; Code="HND-TOY" },
    @{ Name="東京（羽田） - 秋田線"; Code="HND-AXT" },
    @{ Name="東京（羽田） - 宮崎線"; Code="HND-KMI" },
    @{ Name="東京（羽田） - 長崎線"; Code="HND-NGS" },
    @{ Name="大阪（伊丹） - 札幌（新千歳）線"; Code="ITM-CTS" },
    @{ Name="大阪（伊丹） - 那覇線"; Code="ITM-OKA" },
    @{ Name="大阪（伊丹） - 仙台線"; Code="ITM-SDJ" },
    @{ Name="大阪（伊丹） - 福岡線"; Code="ITM-FUK" },
    @{ Name="名古屋（中部） - 札幌（新千歳）線"; Code="NGO-CTS" },
    @{ Name="名古屋（中部） - 那覇線"; Code="NGO-OKA" },
    @{ Name="名古屋（中部） - 福岡線"; Code="NGO-FUK" },
    @{ Name="福岡 - 札幌（新千歳）線"; Code="FUK-CTS" },
    @{ Name="福岡 - 那覇線"; Code="FUK-OKA" },
    @{ Name="札幌（新千歳） - 仙台線"; Code="CTS-SDJ" },
    @{ Name="那覇 - 石垣線"; Code="OKA-ISG" },
    @{ Name="那覇 - 宮古線"; Code="OKA-MMY" }
)
foreach ($ar in $airRoutes) {
    $wiki = "https://ja.wikipedia.org/wiki/" + [uri]::EscapeDataString($ar.Name)
    Add-Route $anaOpId "航路・空路" "航空路" $ar.Code $ar.Name $ar.Name "" $wiki
}
Write-Host "-> Added $($airRoutes.Count) Major Airline Routes."

# ------------------------------------------------------------------------------
# Save transport_routes.csv
# ------------------------------------------------------------------------------
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("route_id,country_code,operator_id,大分類,種別,路線記号・番号,路線名,路線名_公用語,公式サイトURL,Wikipedia_url,Wikidata_id")

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
    $lines.Add(($vals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($routesCsvPath, $lines, $utf8NoBom)
Write-Host "=================================================="
Write-Host " Successfully generated data/staging/JP/transport_routes.csv!"
Write-Host " Total Routes: $($lines.Count - 1)"
Write-Host "=================================================="
