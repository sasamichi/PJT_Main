# ==============================================================================
# build_staging_edges.ps1
# Build data/staging/JP/edges.csv for:
# - Shinkansen 8 Lines (adjacent station edges)
# - Major Airline Routes (27 routes, origin to destination)
# - Major Passenger Ferry Routes (25 routes, origin port to destination port)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$workspaceRoot = "c:\Users\user\Documents\PJT"
$stagingDir = Join-Path $workspaceRoot "data\staging\JP"
$edgesCsvPath = Join-Path $stagingDir "edges.csv"

Write-Host "=================================================="
Write-Host " Building data/staging/JP/edges.csv"
Write-Host "=================================================="

# 1. Load nodes dictionary
Write-Host "[1/4] Loading nodes.csv..."
$nodesCsv = Import-Csv (Join-Path $stagingDir "nodes.csv") -Encoding UTF8
$stMap = @{}
$airMap = @{}
$portMap = @{}

foreach ($n in $nodesCsv) {
    if ($n.種別 -eq "鉄道駅") {
        $clean = $n.名称 -replace "駅$", ""
        if (-not $stMap.ContainsKey($clean)) {
            $stMap[$clean] = $n.node_id
        } else {
            # Prefer JR stations for同名異駅 used in Shinkansen (小倉/大宮/郡山/福島/高崎 etc.)
            $lat = [double]$n.緯度
            $lon = [double]$n.経度
            if ($clean -eq "小倉" -and $lat -lt 34.0 -and $lon -lt 131.5) {
                $stMap[$clean] = $n.node_id
            } elseif ($clean -eq "大宮" -and $lat -gt 35.8 -and $lon -gt 139.5) {
                $stMap[$clean] = $n.node_id
            } elseif ($clean -eq "郡山" -and $lat -gt 37.0 -and $lon -gt 140.0) {
                $stMap[$clean] = $n.node_id
            }
        }
    } elseif ($n.種別 -eq "空港") {
        $airMap[$n.名称] = $n.node_id
        if ($n.iata_code) { $airMap[$n.iata_code] = $n.node_id }
    } elseif ($n.種別 -in @("主要港湾", "地方港湾")) {
        $cleanP = $n.名称 -replace "港$", ""
        if (-not $portMap.ContainsKey($cleanP) -or $n.種別 -eq "主要港湾") {
            $portMap[$cleanP] = $n.node_id
            $portMap[$n.名称] = $n.node_id
        }
    }
}

# Add port alias mappings to official 125 major ports
$portMap["仙台"]   = $portMap["仙台塩釜"]
$portMap["大洗"]   = $portMap["茨城"]
$portMap["泉大津"] = $portMap["堺泉北"]
$portMap["徳島"]   = $portMap["徳島小松島"]
$portMap["和歌山"] = $portMap["和歌山下津"]
$portMap["三河"]   = $portMap["三河"]
$portMap["志布志"] = $portMap["志布志"]
$portMap["新居浜"] = $portMap["新居浜"]
$portMap["別府"]   = $portMap["大分"]
$portMap["宮島"]   = $portMap["広島"]

# 2. Load routes dictionary
Write-Host "[2/4] Loading transport_routes.csv..."
$routesCsv = Import-Csv (Join-Path $stagingDir "transport_routes.csv") -Encoding UTF8
$routeMap = @{}
foreach ($r in $routesCsv) {
    $key = "$($r.種別)|$($r.路線名)"
    if (-not $routeMap.ContainsKey($key)) { $routeMap[$key] = $r.route_id }
    if ($r."路線記号・番号") { $routeMap[$r."路線記号・番号"] = $r.route_id }
}

$edges = [System.Collections.Generic.List[PSCustomObject]]::new()
$edgeSeq = 0

function Add-Edge($routeId, $fromId, $toId, $order) {
    if (-not $routeId -or -not $fromId -or -not $toId) { return }
    $script:edgeSeq++
    $eid = ("JP-ED-{0:D6}" -f $script:edgeSeq)
    $script:edges.Add([PSCustomObject]@{
        edge_id      = $eid
        route_id     = $routeId
        from_node_id = $fromId
        to_node_id   = $toId
        順序         = $order
        状態         = "現行"
    })
}

# ------------------------------------------------------------------------------
# 3. Shinkansen 8 Lines
# ------------------------------------------------------------------------------
Write-Host "[3/4] Building Shinkansen Station Edges..."
$shinkansenData = @(
    @{
        Name = "東海道新幹線"
        Stations = @("東京", "品川", "新横浜", "小田原", "熱海", "三島", "新富士", "静岡", "掛川", "浜松", "豊橋", "三河安城", "名古屋", "岐阜羽島", "米原", "京都", "新大阪")
    },
    @{
        Name = "山陽新幹線"
        Stations = @("新大阪", "新神戸", "西明石", "姫路", "相生", "岡山", "新倉敷", "福山", "新尾道", "三原", "東広島", "広島", "新岩国", "徳山", "新山口", "厚狭", "新下関", "小倉", "博多")
    },
    @{
        Name = "東北新幹線"
        Stations = @("東京", "上野", "大宮", "小山", "宇都宮", "那須塩原", "新白河", "郡山", "福島", "白石蔵王", "仙台", "古川", "くりこま高原", "一ノ関", "水沢江刺", "北上", "新花巻", "盛岡", "いわて沼宮内", "二戸", "八戸", "七戸十和田", "新青森")
    },
    @{
        Name = "上越新幹線"
        Stations = @("大宮", "熊谷", "本庄早稲田", "高崎", "上毛高原", "越後湯沢", "浦佐", "長岡", "燕三条", "新潟")
    },
    @{
        Name = "北陸新幹線"
        Stations = @("高崎", "安中榛名", "軽井沢", "佐久平", "上田", "長野", "飯山", "上越妙高", "糸魚川", "黒部宇奈月温泉", "富山", "新高岡", "金沢", "小松", "加賀温泉", "芦原温泉", "福井", "敦賀")
    },
    @{
        Name = "九州新幹線"
        Stations = @("博多", "新鳥栖", "久留米", "筑後船小屋", "新大牟田", "新玉名", "熊本", "新八代", "新水俣", "出水", "川内", "鹿児島中央")
    },
    @{
        Name = "西九州新幹線"
        Stations = @("武雄温泉", "嬉野温泉", "新大村", "諫早", "長崎")
    },
    @{
        Name = "北海道新幹線"
        Stations = @("新青森", "奥津軽いまべつ", "木古内", "新函館北斗")
    }
)

$shinkansenEdgeCount = 0
foreach ($sh in $shinkansenData) {
    $rKey = "新幹線|$($sh.Name)"
    $rId = $routeMap[$rKey]
    if (-not $rId) {
        foreach ($k in $routeMap.Keys) {
            if ($k -match [regex]::Escape($sh.Name)) { $rId = $routeMap[$k]; break }
        }
    }
    for ($i = 0; $i -lt ($sh.Stations.Count - 1); $i++) {
        $fromName = $sh.Stations[$i]
        $toName = $sh.Stations[$i + 1]
        $fromId = $stMap[$fromName]
        $toId = $stMap[$toName]
        if ($fromId -and $toId -and $rId) {
            Add-Edge $rId $fromId $toId ($i + 1)
            $shinkansenEdgeCount++
        } else {
            Write-Warning "Shinkansen edge missing node: $($sh.Name) $fromName ($fromId) -> $toName ($toId)"
        }
    }
}
Write-Host "-> Added $shinkansenEdgeCount Shinkansen edges."

# ------------------------------------------------------------------------------
# 4. Major Domestic Airline Edges (27 routes)
# ------------------------------------------------------------------------------
Write-Host "[4/4] Building Airline & Ferry Edges..."
$airRoutes = @(
    @{ Code="HND-CTS"; From="HND"; To="CTS" },
    @{ Code="HND-FUK"; From="HND"; To="FUK" },
    @{ Code="HND-OKA"; From="HND"; To="OKA" },
    @{ Code="HND-ITM"; From="HND"; To="ITM" },
    @{ Code="HND-KIX"; From="HND"; To="KIX" },
    @{ Code="HND-KOJ"; From="HND"; To="KOJ" },
    @{ Code="HND-KMJ"; From="HND"; To="KMJ" },
    @{ Code="HND-HIJ"; From="HND"; To="HIJ" },
    @{ Code="HND-MYJ"; From="HND"; To="MYJ" },
    @{ Code="HND-TAK"; From="HND"; To="TAK" },
    @{ Code="HND-KMQ"; From="HND"; To="KMQ" },
    @{ Code="HND-TOY"; From="HND"; To="TOY" },
    @{ Code="HND-AXT"; From="HND"; To="AXT" },
    @{ Code="HND-KMI"; From="HND"; To="KMI" },
    @{ Code="HND-NGS"; From="HND"; To="NGS" },
    @{ Code="ITM-CTS"; From="ITM"; To="CTS" },
    @{ Code="ITM-OKA"; From="ITM"; To="OKA" },
    @{ Code="ITM-SDJ"; From="ITM"; To="SDJ" },
    @{ Code="ITM-FUK"; From="ITM"; To="FUK" },
    @{ Code="NGO-CTS"; From="NGO"; To="CTS" },
    @{ Code="NGO-OKA"; From="NGO"; To="OKA" },
    @{ Code="NGO-FUK"; From="NGO"; To="FUK" },
    @{ Code="FUK-CTS"; From="FUK"; To="CTS" },
    @{ Code="FUK-OKA"; From="FUK"; To="OKA" },
    @{ Code="CTS-SDJ"; From="CTS"; To="SDJ" },
    @{ Code="OKA-ISG"; From="OKA"; To="ISG" },
    @{ Code="OKA-MMY"; From="OKA"; To="MMY" }
)

$airEdgeCount = 0
foreach ($ar in $airRoutes) {
    $rId = $routeMap[$ar.Code]
    $fromId = $airMap[$ar.From]
    $toId = $airMap[$ar.To]
    if ($rId -and $fromId -and $toId) {
        Add-Edge $rId $fromId $toId 1
        $airEdgeCount++
    } else {
        Write-Warning "Air edge missing: $($ar.Code) From=$fromId To=$toId"
    }
}
Write-Host "-> Added $airEdgeCount Airline edges."

# ------------------------------------------------------------------------------
# 5. Major Maritime Passenger Ferry Edges (25 routes)
# ------------------------------------------------------------------------------
$ferryRoutes = @(
    @{ Code="F-SNF-01"; From="京都舞鶴"; To="小樽" },
    @{ Code="F-SNF-02"; From="敦賀"; To="苫小牧" },
    @{ Code="F-SNF-03"; From="新潟"; To="小樽" },
    @{ Code="F-TAI-01"; From="名古屋"; To="仙台" },
    @{ Code="F-SUN-01"; From="大洗"; To="苫小牧" },
    @{ Code="F-SUN-02"; From="大阪"; To="志布志" },
    @{ Code="F-SUN-03"; From="大阪"; To="別府" },
    @{ Code="F-SUN-04"; From="神戸"; To="大分" },
    @{ Code="F-CTY-01"; From="大阪"; To="北九州" },
    @{ Code="F-HAN-01"; From="泉大津"; To="北九州" },
    @{ Code="F-TQF-01"; From="横須賀"; To="北九州" },
    @{ Code="F-OTF-01"; From="東京"; To="徳島" },
    @{ Code="F-MIY-01"; From="神戸"; To="宮崎" },
    @{ Code="F-KKK-01"; From="八戸"; To="苫小牧" },
    @{ Code="F-TSU-01"; From="青森"; To="函館" },
    @{ Code="F-TSU-03"; From="室蘭"; To="青森" },
    @{ Code="F-SEI-01"; From="青森"; To="函館" },
    @{ Code="F-SAD-01"; From="新潟"; To="両津" },
    @{ Code="F-SAD-02"; From="直江津"; To="小木" },
    @{ Code="F-TWF-01"; From="横須賀"; To="木更津" },
    @{ Code="F-ISE-01"; From="鳥羽"; To="三河" },
    @{ Code="F-NAN-01"; From="和歌山"; To="徳島" },
    @{ Code="F-JUM-01"; From="神戸"; To="高松" },
    @{ Code="F-ORA-01"; From="大阪"; To="新居浜" },
    @{ Code="F-OKI-01"; From="境港"; To="西郷" },
    @{ Code="F-ALI-01"; From="鹿児島"; To="那覇" },
    @{ Code="F-MIJ-01"; From="広島"; To="厳島" }
)

$ferryEdgeCount = 0
foreach ($fr in $ferryRoutes) {
    $rId = $routeMap[$fr.Code]
    $fromId = $portMap[$fr.From]
    $toId = $portMap[$fr.To]
    if (-not $fromId) {
        foreach ($k in $portMap.Keys) {
            if ($k -match [regex]::Escape($fr.From)) { $fromId = $portMap[$k]; break }
        }
    }
    if (-not $toId) {
        foreach ($k in $portMap.Keys) {
            if ($k -match [regex]::Escape($fr.To)) { $toId = $portMap[$k]; break }
        }
    }
    if ($rId -and $fromId -and $toId) {
        Add-Edge $rId $fromId $toId 1
        $ferryEdgeCount++
    }
}
Write-Host "-> Added $ferryEdgeCount Maritime Ferry edges."

# ------------------------------------------------------------------------------
# Save edges.csv
# ------------------------------------------------------------------------------
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("edge_id,route_id,from_node_id,to_node_id,順序,状態")

foreach ($e in $edges) {
    $vals = @(
        $e.edge_id,
        $e.route_id,
        $e.from_node_id,
        $e.to_node_id,
        $e.順序,
        $e.状態
    )
    $lines.Add(($vals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($edgesCsvPath, $lines, $utf8NoBom)
Write-Host "=================================================="
Write-Host " Successfully generated data/staging/JP/edges.csv!"
Write-Host " Total Edges: $($lines.Count - 1)"
Write-Host "=================================================="
