# PowerShell script to build Shinkansen (45 sections) and Domestic Flight (27 routes) edges
# and update origin/destination node IDs in transport_routes.csv (UTF-8 without BOM)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Get-HaversineKm($lat1, $lon1, $lat2, $lon2) {
    $r = 6371.0
    $dLat = ($lat2 - $lat1) * [Math]::PI / 180.0
    $dLon = ($lon2 - $lon1) * [Math]::PI / 180.0
    $a = [Math]::Sin($dLat / 2) * [Math]::Sin($dLat / 2) +
         [Math]::Cos($lat1 * [Math]::PI / 180.0) * [Math]::Cos($lat2 * [Math]::PI / 180.0) *
         [Math]::Sin($dLon / 2) * [Math]::Sin($dLon / 2)
    $c = 2 * [Math]::Atan2([Math]::Sqrt($a), [Math]::Sqrt(1 - $a))
    return [Math]::Round($r * $c, 1)
}

$workspaceRoot = (Get-Location).Path
$edgesCsvPath  = Join-Path $workspaceRoot "data\master\edges.csv"
$routesCsvPath = Join-Path $workspaceRoot "data\master\transport_routes.csv"
$nodesCsvPath  = Join-Path $workspaceRoot "data\master\nodes.csv"

Write-Host "=================================================="
Write-Host " 新幹線全線 (45区間) & 航空路 (27区間) エッジ構築"
Write-Host "=================================================="

# 1. ノードマスタ読み込み
Write-Host "`n[1/5] nodes.csv の読み込み..."
$nodes = Import-Csv -Path $nodesCsvPath -Encoding UTF8
$nodeMap = @{}
foreach ($nd in $nodes) {
    $nodeMap[$nd.node_id] = @{
        id = $nd.node_id
        name = $nd.日本語名
        lat = [double]$nd.緯度
        lon = [double]$nd.経度
    }
}
Write-Host "-> ノード辞書ロード完了: $($nodeMap.Count) 件"

# 2. 既存エッジ読み込み & 最大連番取得
Write-Host "`n[2/5] edges.csv の既存エッジ確認..."
$existingEdgeLines = [System.IO.File]::ReadAllLines($edgesCsvPath, [System.Text.Encoding]::UTF8)
$maxEdgeNum = 0
for ($i = 1; $i -lt $existingEdgeLines.Count; $i++) {
    $parts = $existingEdgeLines[$i].Split(',')
    if ($parts[0] -match "^JP-ED-(\d+)$") {
        $num = [int]$matches[1]
        if ($num -gt $maxEdgeNum) { $maxEdgeNum = $num }
    }
}
Write-Host "-> 既存エッジ行数: $($existingEdgeLines.Count - 1) 行 (最大ID番号: $maxEdgeNum)"
if ($maxEdgeNum -ne 226) {
    Write-Warning "直前の最大edge_idが JP-ED-000226 ではありません: $maxEdgeNum"
}

# 3. 新規エッジ定義
$routeEndpointUpdates = @{} # route_id -> @{ start = nid, end = nid }

# 3.1 新幹線5路線定義
$shinkansenRoutes = @(
    @{
        route_id = "JP-RT-005412"
        name = "上越新幹線"
        stations = @(
            "JP-ND-001535", # 大宮
            "JP-ND-001452", # 熊谷
            "JP-ND-002670", # 本庄早稲田
            "JP-ND-001363", # 高崎
            "JP-ND-002664", # 上毛高原
            "JP-ND-002715", # 越後湯沢
            "JP-ND-002699", # 浦佐
            "JP-ND-002661", # 長岡
            "JP-ND-002573", # 燕三条
            "JP-ND-001857"  # 新潟
        )
        electrification = "交流25kV 50Hz"
        start_date = "1982-11-15"
    },
    @{
        route_id = "JP-RT-005414"
        name = "北陸新幹線"
        stations = @(
            "JP-ND-001363", # 高崎
            "JP-ND-002714", # 安中榛名
            "JP-ND-002286", # 軽井沢
            "JP-ND-002737", # 佐久平
            "JP-ND-002410", # 上田
            "JP-ND-001682", # 長野
            "JP-ND-004477", # 飯山
            "JP-ND-009083", # 上越妙高
            "JP-ND-003059", # 糸魚川
            "JP-ND-005177", # 黒部宇奈月温泉
            "JP-ND-002142", # 富山
            "JP-ND-005273", # 新高岡
            "JP-ND-001913", # 金沢
            "JP-ND-005931", # 小松
            "JP-ND-005436", # 加賀温泉
            "JP-ND-002239", # 芦原温泉
            "JP-ND-003412", # 福井
            "JP-ND-005665", # 越前たけふ
            "JP-ND-005882"  # 敦賀
        )
        section_meta = @(
            @{ elec = "交流25kV 50Hz"; date = "1997-10-01" }, # 高崎 - 安中榛名
            @{ elec = "交流25kV 50Hz"; date = "1997-10-01" }, # 安中榛名 - 軽井沢
            @{ elec = "交流25kV 60Hz"; date = "1997-10-01" }, # 軽井沢 - 佐久平
            @{ elec = "交流25kV 60Hz"; date = "1997-10-01" }, # 佐久平 - 上田
            @{ elec = "交流25kV 60Hz"; date = "1997-10-01" }, # 上田 - 長野
            @{ elec = "交流25kV 50Hz"; date = "2015-03-14" }, # 長野 - 飯山
            @{ elec = "交流25kV 50Hz"; date = "2015-03-14" }, # 飯山 - 上越妙高
            @{ elec = "交流25kV 60Hz"; date = "2015-03-14" }, # 上越妙高 - 糸魚川
            @{ elec = "交流25kV 60Hz"; date = "2015-03-14" }, # 糸魚川 - 黒部宇奈月温泉
            @{ elec = "交流25kV 60Hz"; date = "2015-03-14" }, # 黒部宇奈月温泉 - 富山
            @{ elec = "交流25kV 60Hz"; date = "2015-03-14" }, # 富山 - 新高岡
            @{ elec = "交流25kV 60Hz"; date = "2015-03-14" }, # 新高岡 - 金沢
            @{ elec = "交流25kV 60Hz"; date = "2024-03-16" }, # 金沢 - 小松
            @{ elec = "交流25kV 60Hz"; date = "2024-03-16" }, # 小松 - 加賀温泉
            @{ elec = "交流25kV 60Hz"; date = "2024-03-16" }, # 加賀温泉 - 芦原温泉
            @{ elec = "交流25kV 60Hz"; date = "2024-03-16" }, # 芦原温泉 - 福井
            @{ elec = "交流25kV 60Hz"; date = "2024-03-16" }, # 福井 - 越前たけふ
            @{ elec = "交流25kV 60Hz"; date = "2024-03-16" }  # 越前たけふ - 敦賀
        )
    },
    @{
        route_id = "JP-RT-005458"
        name = "九州新幹線"
        stations = @(
            "JP-ND-001504", # 博多
            "JP-ND-010230", # 新鳥栖
            "JP-ND-002465", # 久留米
            "JP-ND-001906", # 筑後船小屋
            "JP-ND-002707", # 新大牟田
            "JP-ND-002731", # 新玉名
            "JP-ND-005957", # 熊本
            "JP-ND-002712", # 新八代
            "JP-ND-001905", # 新水俣
            "JP-ND-002684", # 出水
            "JP-ND-002673", # 川内
            "JP-ND-002963"  # 鹿児島中央
        )
        electrification = "交流25kV 60Hz"
        section_meta = @(
            @{ date = "2011-03-12" }, # 博多 - 新鳥栖
            @{ date = "2011-03-12" }, # 新鳥栖 - 久留米
            @{ date = "2011-03-12" }, # 久留米 - 筑後船小屋
            @{ date = "2011-03-12" }, # 筑後船小屋 - 新大牟田
            @{ date = "2011-03-12" }, # 新大牟田 - 新玉名
            @{ date = "2011-03-12" }, # 新玉名 - 熊本
            @{ date = "2011-03-12" }, # 熊本 - 新八代
            @{ date = "2004-03-13" }, # 新八代 - 新水俣
            @{ date = "2004-03-13" }, # 新水俣 - 出水
            @{ date = "2004-03-13" }, # 出水 - 川内
            @{ date = "2004-03-13" }  # 川内 - 鹿児島中央
        )
    },
    @{
        route_id = "JP-RT-005495"
        name = "西九州新幹線"
        stations = @(
            "JP-ND-003247", # 武雄温泉
            "JP-ND-008034", # 嬉野温泉
            "JP-ND-005304", # 新大村
            "JP-ND-005463", # 諫早
            "JP-ND-002348"  # 長崎
        )
        electrification = "交流25kV 60Hz"
        start_date = "2022-09-23"
    },
    @{
        route_id = "JP-RT-005386"
        name = "北海道新幹線"
        stations = @(
            "JP-ND-002685", # 新青森
            "JP-ND-002179", # 奥津軽いまべつ
            "JP-ND-009626", # 木古内
            "JP-ND-006368"  # 新函館北斗
        )
        electrification = "交流25kV 50Hz"
        start_date = "2016-03-26"
    }
)

# 3.2 航空路27路線定義
$flightRoutes = @(
    @{ route_id="JP-RT-005948"; name="羽田〜新千歳線"; from="JP-ND-014466"; to="JP-ND-014530" },
    @{ route_id="JP-RT-005949"; name="羽田〜福岡線";   from="JP-ND-014466"; to="JP-ND-014545" },
    @{ route_id="JP-RT-005950"; name="羽田〜那覇線";   from="JP-ND-014466"; to="JP-ND-014518" },
    @{ route_id="JP-RT-005951"; name="羽田〜伊丹線";   from="JP-ND-014466"; to="JP-ND-014502" },
    @{ route_id="JP-RT-005952"; name="羽田〜鹿児島線"; from="JP-ND-014466"; to="JP-ND-014525" },
    @{ route_id="JP-RT-005953"; name="羽田〜熊本線";   from="JP-ND-014466"; to="JP-ND-014517" },
    @{ route_id="JP-RT-005954"; name="羽田〜広島線";   from="JP-ND-014466"; to="JP-ND-014472" },
    @{ route_id="JP-RT-005955"; name="羽田〜松山線";   from="JP-ND-014466"; to="JP-ND-014468" },
    @{ route_id="JP-RT-005956"; name="羽田〜高松線";   from="JP-ND-014466"; to="JP-ND-014503" },
    @{ route_id="JP-RT-005957"; name="羽田〜小松線";   from="JP-ND-014466"; to="JP-ND-014532" },
    @{ route_id="JP-RT-005958"; name="羽田〜長崎線";   from="JP-ND-014466"; to="JP-ND-014463" },
    @{ route_id="JP-RT-005959"; name="成田〜新千歳線"; from="JP-ND-014473"; to="JP-ND-014530" },
    @{ route_id="JP-RT-005960"; name="成田〜福岡線";   from="JP-ND-014473"; to="JP-ND-014545" },
    @{ route_id="JP-RT-005961"; name="成田〜那覇線";   from="JP-ND-014473"; to="JP-ND-014518" },
    @{ route_id="JP-RT-005962"; name="関西〜新千歳線"; from="JP-ND-014467"; to="JP-ND-014530" },
    @{ route_id="JP-RT-005963"; name="関西〜那覇線";   from="JP-ND-014467"; to="JP-ND-014518" },
    @{ route_id="JP-RT-005964"; name="伊丹〜新千歳線"; from="JP-ND-014502"; to="JP-ND-014530" },
    @{ route_id="JP-RT-005965"; name="伊丹〜那覇線";   from="JP-ND-014502"; to="JP-ND-014518" },
    @{ route_id="JP-RT-005966"; name="伊丹〜仙台線";   from="JP-ND-014502"; to="JP-ND-014519" },
    @{ route_id="JP-RT-005967"; name="伊丹〜福岡線";   from="JP-ND-014502"; to="JP-ND-014545" },
    @{ route_id="JP-RT-005968"; name="中部〜新千歳線"; from="JP-ND-014476"; to="JP-ND-014530" },
    @{ route_id="JP-RT-005969"; name="中部〜那覇線";   from="JP-ND-014476"; to="JP-ND-014518" },
    @{ route_id="JP-RT-005970"; name="中部〜福岡線";   from="JP-ND-014476"; to="JP-ND-014545" },
    @{ route_id="JP-RT-005971"; name="福岡〜新千歳線"; from="JP-ND-014545"; to="JP-ND-014530" },
    @{ route_id="JP-RT-005972"; name="福岡〜那覇線";   from="JP-ND-014545"; to="JP-ND-014518" },
    @{ route_id="JP-RT-005973"; name="那覇〜石垣線";   from="JP-ND-014518"; to="JP-ND-014497" },
    @{ route_id="JP-RT-005974"; name="那覇〜宮古線";   from="JP-ND-014518"; to="JP-ND-014465" }
)

# 4. 新規エッジの生成
Write-Host "`n[3/5] 新規エッジの生成中..."
$newEdgeLines = [System.Collections.Generic.List[string]]::new()
$curEdgeNum = $maxEdgeNum

# (A) 新幹線
$shinkansenEdgeCount = 0
foreach ($route in $shinkansenRoutes) {
    $rid = $route.route_id
    $sts = $route.stations
    $routeEndpointUpdates[$rid] = @{ start = $sts[0]; end = $sts[-1] }

    for ($i = 0; $i -lt ($sts.Count - 1); $i++) {
        $curEdgeNum++
        $shinkansenEdgeCount++
        $eid = ("JP-ED-{0:D6}" -f $curEdgeNum)
        $seq = $i + 1
        $fn = $sts[$i]
        $tn = $sts[$i + 1]

        $u = $nodeMap[$fn]
        $v = $nodeMap[$tn]
        $dist = Get-HaversineKm $u.lat $u.lon $v.lat $v.lon

        $elec = if ($route.ContainsKey("electrification")) { $route.electrification } else { $route.section_meta[$i].elec }
        $sdate = if ($route.ContainsKey("start_date")) { $route.start_date } else { $route.section_meta[$i].date }

        $row = "$eid,$rid,$seq,$fn,$tn,,,,本線,{0:F1},複線,$elec,,$sdate,日,,,現用" -f $dist
        $newEdgeLines.Add($row)
    }
    Write-Host "-> $($route.name): $($sts.Count - 1) 区間生成 ($($sts[0]) ➔ $($sts[-1]))"
}

# (B) 航空路
$flightEdgeCount = 0
foreach ($f in $flightRoutes) {
    $curEdgeNum++
    $flightEdgeCount++
    $eid = ("JP-ED-{0:D6}" -f $curEdgeNum)
    $rid = $f.route_id
    $fn = $f.from
    $tn = $f.to
    $routeEndpointUpdates[$rid] = @{ start = $fn; end = $tn }

    $u = $nodeMap[$fn]
    $v = $nodeMap[$tn]
    $dist = Get-HaversineKm $u.lat $u.lon $v.lat $v.lon

    $row = "$eid,$rid,1,$fn,$tn,,,,本線,{0:F1},,,,,,,,,現用" -f $dist
    $newEdgeLines.Add($row)
}
Write-Host "-> 国内定期航空路: $flightEdgeCount 区間生成"
Write-Host "-> 総新規エッジ数: $($newEdgeLines.Count) 件 (新幹線: $shinkansenEdgeCount, 航空路: $flightEdgeCount)"

# 5. edges.csv への追記（BOMなしUTF-8）
Write-Host "`n[4/5] edges.csv の更新..."
$updatedEdgeLines = [System.Collections.Generic.List[string]]::new($existingEdgeLines)
foreach ($line in $newEdgeLines) {
    $updatedEdgeLines.Add($line)
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($edgesCsvPath, $updatedEdgeLines, $utf8NoBom)
Write-Host "-> $edgesCsvPath 保存完了 (総行数: $($updatedEdgeLines.Count - 1) 件、今回追加: $($newEdgeLines.Count) 件)"

# 6. transport_routes.csv の起終点ノード更新（BOMなしUTF-8）
Write-Host "`n[5/5] transport_routes.csv の起終点ノードID更新..."
$routeLines = [System.IO.File]::ReadAllLines($routesCsvPath, [System.Text.Encoding]::UTF8)
$updatedRouteLines = [System.Collections.Generic.List[string]]::new()
$updatedRouteLines.Add($routeLines[0])
$routesUpdatedCount = 0

for ($i = 1; $i -lt $routeLines.Count; $i++) {
    $line = $routeLines[$i]
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    # 引用符対応パース
    $cols = [System.Collections.Generic.List[string]]::new()
    $inQuote = $false
    $cur = ""
    for ($j = 0; $j -lt $line.Length; $j++) {
        $ch = $line[$j]
        if ($ch -eq '"') {
            $inQuote = -not $inQuote
            $cur += $ch
        } elseif ($ch -eq ',' -and -not $inQuote) {
            $cols.Add($cur)
            $cur = ""
        } else {
            $cur += $ch
        }
    }
    $cols.Add($cur)

    $rid = $cols[0]
    if ($routeEndpointUpdates.ContainsKey($rid)) {
        $ep = $routeEndpointUpdates[$rid]
        # 起点ノード_id: index 12, 終点ノード_id: index 13
        $cols[12] = $ep.start
        $cols[13] = $ep.end
        $routesUpdatedCount++
    }

    $updatedRouteLines.Add(($cols -join ","))
}

[System.IO.File]::WriteAllLines($routesCsvPath, $updatedRouteLines, $utf8NoBom)
Write-Host "-> $routesCsvPath 保存完了 (更新路線数: $routesUpdatedCount / 32 件)"

Write-Host "`n=================================================="
Write-Host " 全処理が正常に完了しました。"
Write-Host "=================================================="
