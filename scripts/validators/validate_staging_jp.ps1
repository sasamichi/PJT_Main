# ==============================================================================
# validate_staging_jp.ps1
# Step 3 Automated Quality Gate for data/staging/JP/
# 1. Precision Benchmark Master (精度基準マスタ.csv) Full Comparison
# 2. Foreign Key & Coordinate Bounding Box Verification
# 3. Edge Haversine Distance Inspection (Shinkansen / Air / Ferry)
# 4. Whitelist / Forbidden Keyword Contamination Check
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Get-HaversineKm([double]$lat1, [double]$lon1, [double]$lat2, [double]$lon2) {
    $r = 6371.0
    $dLat = ($lat2 - $lat1) * [Math]::PI / 180.0
    $dLon = ($lon2 - $lon1) * [Math]::PI / 180.0
    $a = [Math]::Sin($dLat / 2) * [Math]::Sin($dLat / 2) +
         [Math]::Cos($lat1 * [Math]::PI / 180.0) * [Math]::Cos($lat2 * [Math]::PI / 180.0) *
         [Math]::Sin($dLon / 2) * [Math]::Sin($dLon / 2)
    $c = 2 * [Math]::Atan2([Math]::Sqrt($a), [Math]::Sqrt(1 - $a))
    return [Math]::Round($r * $c, 2)
}

$workspaceRoot = "c:\Users\user\Documents\PJT"
$stagingDir    = Join-Path $workspaceRoot "data\staging\JP"

Write-Host "=================================================================="
Write-Host " [第3段階] 日本ステージングデータ 自動品質検査ゲート"
Write-Host "=================================================================="

$areas  = Import-Csv (Join-Path $stagingDir "areas.csv") -Encoding UTF8
$ops    = Import-Csv (Join-Path $stagingDir "operators.csv") -Encoding UTF8
$routes = Import-Csv (Join-Path $stagingDir "transport_routes.csv") -Encoding UTF8
$nodes  = Import-Csv (Join-Path $stagingDir "nodes.csv") -Encoding UTF8
$edges  = Import-Csv (Join-Path $stagingDir "edges.csv") -Encoding UTF8

# ------------------------------------------------------------------------------
# GATE 1: 精度基準マスタ突合検査
# ------------------------------------------------------------------------------
Write-Host "`n[Gate 1/4] 精度基準マスタ（公的基準件数）全件突合..."

$prefCount     = ($areas | Where-Object { $_.type_id -match "^JP_ADMIN_PREF_" }).Count
$hokkaidoSp    = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_SUBPREF" -and $_.公的コード -match "^01-" }).Count
$otherShicho   = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_SUBPREF" -and $_.公的コード -notmatch "^01-" }).Count
$gunCount      = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_GUN" }).Count
$desigCity     = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_CITY_DESIGNATED" }).Count
$adminWard     = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_WARD" }).Count
$coreCity      = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_CITY_CORE" }).Count
$specCity      = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_CITY_SPECIAL_EXC" }).Count
$ordCity       = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_CITY_ORDINARY" }).Count
$nonDesigCity  = $coreCity + $specCity + $ordCity
$specialWard   = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_SPECIAL_WARD" }).Count
$townCount     = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_TOWN" }).Count
$villageCount  = ($areas | Where-Object { $_.type_id -eq "JP_ADMIN_VILLAGE" }).Count

$wxCenter      = ($areas | Where-Object { $_.type_id -eq "JP_MET_CENTER" }).Count
$wxOffice      = ($areas | Where-Object { $_.type_id -eq "JP_MET_OFFICE" }).Count
$wxClass10     = ($areas | Where-Object { $_.type_id -eq "JP_MET_CLASS10" }).Count
$wxClass20     = ($areas | Where-Object { $_.type_id -eq "JP_MET_CLASS20" }).Count

$amedasCount   = ($nodes | Where-Object { $_.種別 -eq "気象観測点" }).Count
$natHighway    = ($routes | Where-Object { $_.種別 -eq "一般国道" }).Count
$expressway    = ($routes | Where-Object { $_.種別 -in @("高速道路", "都市高速") }).Count
$hwFacCount    = ($nodes | Where-Object { $_.種別 -in @("IC・JCT", "高速施設（SA・PA）") }).Count
$michiCount    = ($nodes | Where-Object { $_.種別 -eq "道の駅" }).Count
$airportCount  = ($nodes | Where-Object { $_.種別 -eq "空港" }).Count
$majorPort     = ($nodes | Where-Object { $_.種別 -eq "主要港湾" }).Count
$localPort     = ($nodes | Where-Object { $_.種別 -eq "地方港湾" }).Count
$opTotalCount  = $ops.Count
$railRoutes    = ($routes | Where-Object { $_.種別 -in @("新幹線", "鉄道", "地下鉄", "モノレール", "路面電車・LRT", "新交通システム", "索道・鋼索") }).Count
$railStations  = ($nodes | Where-Object { $_.種別 -eq "鉄道駅" }).Count

$checkResults = @(
    [PSCustomObject]@{ 項目="都道府県";               実測=$prefCount;    基準="47 (47-47)";          判定=if($prefCount -eq 47){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="総合振興局・振興局";     実測=$hokkaidoSp;   基準="14 (14-14)";          判定=if($hokkaidoSp -eq 14){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="支庁";                   実測=$otherShicho;  基準="10 (8-12)";           判定=if($otherShicho -ge 8 -and $otherShicho -le 12){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="郡（実効368＋北方5）";   実測=$gunCount;     基準="373 (368-379)";       判定=if($gunCount -ge 368 -and $gunCount -le 379){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="政令指定都市";           実測=$desigCity;    基準="20 (20-20)";          判定=if($desigCity -eq 20){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="政令指定都市_行政区";    実測=$adminWard;    基準="171 (171-171)";       判定=if($adminWard -eq 171){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="中核市";                 実測=$coreCity;     基準="62 (62-62)";          判定=if($coreCity -eq 62){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="施行時特例市";           実測=$specCity;     基準="23 (23-23)";          判定=if($specCity -eq 23){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="一般市";                 実測=$ordCity;      基準="687 (687-687)";       判定=if($ordCity -eq 687){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="市（政令市除く合計）";   実測=$nonDesigCity; 基準="772 (772-772)";       判定=if($nonDesigCity -eq 772){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="特別区";                 実測=$specialWard;  基準="23 (23-23)";          判定=if($specialWard -eq 23){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="町";                     実測=$townCount;    基準="743 (743-743)";       判定=if($townCount -eq 743){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="村（実効183＋北方6）";   実測=$villageCount; 基準="189 (183-189)";       判定=if($villageCount -ge 183 -and $villageCount -le 189){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="気象予報区_地方予報区";  実測=$wxCenter;     基準="11 (11-11)";          判定=if($wxCenter -eq 11){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="気象予報区_府県予報区";  実測=$wxOffice;     基準="58 (58-58)";          判定=if($wxOffice -eq 58){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="気象予報区_一次細分";    実測=$wxClass10;    基準="142 (142-142)";       判定=if($wxClass10 -eq 142){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="気象予報区_二次細分";    実測=$wxClass20;    基準="1805 (1800-1810)";    判定=if($wxClass20 -ge 1800 -and $wxClass20 -le 1810){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="気象庁アメダス観測所";   実測=$amedasCount;  基準="1286 (1280-1300)";    判定=if($amedasCount -eq 1286){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="一般国道";               実測=$natHighway;   基準="459 (459-459)";       判定=if($natHighway -eq 459){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="高速道路・高規格道路";   実測=$expressway;   基準="308 (KSJ N06実測)";   判定=if($expressway -ge 200 -and $expressway -le 320){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="高速道路IC・施設";       実測=$hwFacCount;   基準="2354 (KSJ N06実測)";  判定=if($hwFacCount -ge 2300 -and $hwFacCount -le 2550){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="道の駅";                 実測=$michiCount;   基準="1234 (1234-1234)";    判定=if($michiCount -eq 1234){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="旅客空港";               実測=$airportCount; 基準="97 (97-97)";          判定=if($airportCount -eq 97){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="重要港湾以上";           実測=$majorPort;    基準="125 (125-125)";       判定=if($majorPort -eq 125){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="地方港湾_フェリー発着";  実測=$localPort;    基準="201 (180-220)";       判定=if($localPort -ge 180 -and $localPort -le 220){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="事業者マスタ";           実測=$opTotalCount; 基準="225 (200-225)";       判定=if($opTotalCount -ge 200 -and $opTotalCount -le 225){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="鉄軌道路線（N02）";      実測=$railRoutes;   基準="597 (KSJ N02実測)";   判定=if($railRoutes -ge 550 -and $railRoutes -le 900){"PASS"}else{"FAIL"} },
    [PSCustomObject]@{ 項目="現行鉄道駅（N02）";      実測=$railStations; 基準="9476 (9100-9500)";    判定=if($railStations -ge 9100 -and $railStations -le 9500){"PASS"}else{"FAIL"} }
)

$checkResults | Format-Table -AutoSize
$gate1Fails = ($checkResults | Where-Object { $_.判定 -ne "PASS" }).Count
if ($gate1Fails -eq 0) {
    Write-Host "-> Gate 1 Result: ALL 28 BENCHMARKS PASSED (0 Failures)"
} else {
    Write-Host "-> Gate 1 Result: FAILED ($gate1Fails Failures)"
}

# ------------------------------------------------------------------------------
# GATE 2: 外部キー整合性 ＆ 日本領土BBOX空間検査
# ------------------------------------------------------------------------------
Write-Host "`n[Gate 2/4] 外部キー参照整合性 ＆ 日本領土バウンディングボックス検査..."
$areaIds  = [System.Collections.Generic.HashSet[string]]::new([string[]]($areas | ForEach-Object { $_.area_id }))
$opIds    = [System.Collections.Generic.HashSet[string]]::new([string[]]($ops | ForEach-Object { $_.operator_id }))
$routeIds = [System.Collections.Generic.HashSet[string]]::new([string[]]($routes | ForEach-Object { $_.route_id }))
$nodeIds  = [System.Collections.Generic.HashSet[string]]::new([string[]]($nodes | ForEach-Object { $_.node_id }))

$badParentAreas = ($areas | Where-Object { $_.親区域ID -and -not $areaIds.Contains($_.親区域ID) }).Count
$badWxAreas     = ($areas | Where-Object { $_.気象予報区ID -and -not $areaIds.Contains($_.気象予報区ID) }).Count
$badRouteOps    = ($routes | Where-Object { -not $opIds.Contains($_.operator_id) }).Count
$badNodeAreas   = ($nodes | Where-Object { -not $areaIds.Contains($_.area_id) }).Count
$badNodeOps     = ($nodes | Where-Object { -not $opIds.Contains($_.operator_id) }).Count
$badEdgeRoutes  = ($edges | Where-Object { -not $routeIds.Contains($_.route_id) }).Count
$badEdgeFrom    = ($edges | Where-Object { -not $nodeIds.Contains($_.from_node_id) }).Count
$badEdgeTo      = ($edges | Where-Object { -not $nodeIds.Contains($_.to_node_id) }).Count

$outBboxNodes = 0
foreach ($n in $nodes) {
    $lat = [double]$n.緯度
    $lon = [double]$n.経度
    if ($lat -lt 20.0 -or $lat -gt 46.0 -or $lon -lt 122.0 -or $lon -gt 154.5) {
        $outBboxNodes++
        Write-Warning "Out of BBOX Node: $($n.node_id) $($n.名称) ($lat, $lon)"
    }
}

Write-Host "  areas.csv invalid 親区域ID: $badParentAreas"
Write-Host "  areas.csv invalid 気象予報区ID: $badWxAreas"
Write-Host "  transport_routes.csv invalid operator_id: $badRouteOps"
Write-Host "  nodes.csv invalid area_id: $badNodeAreas"
Write-Host "  nodes.csv invalid operator_id: $badNodeOps"
Write-Host "  nodes.csv out-of-Japan BBOX: $outBboxNodes"
Write-Host "  edges.csv invalid route_id/from/to: $($badEdgeRoutes + $badEdgeFrom + $badEdgeTo)"

$gate2Fails = $badParentAreas + $badWxAreas + $badRouteOps + $badNodeAreas + $badNodeOps + $outBboxNodes + $badEdgeRoutes + $badEdgeFrom + $badEdgeTo
if ($gate2Fails -eq 0) {
    Write-Host "-> Gate 2 Result: PASSED (0 Integrity/BBOX Errors)"
} else {
    Write-Host "-> Gate 2 Result: FAILED ($gate2Fails Errors)"
}

# ------------------------------------------------------------------------------
# GATE 3: エッジ空間距離検査（異常ワープ・自己ループ検知）
# ------------------------------------------------------------------------------
Write-Host "`n[Gate 3/4] エッジ空間距離検査（新幹線駅間100km超ワープ・自己ループ検知）..."
$nodeLookup = @{}
foreach ($n in $nodes) {
    $nodeLookup[$n.node_id] = $n
}
$routeLookup = @{}
foreach ($r in $routes) {
    $routeLookup[$r.route_id] = $r
}

$selfLoops = 0
$shinkansenWarps = 0
$maxShinkansenDist = 0.0
$maxShinkansenPair = ""

foreach ($e in $edges) {
    $rObj = $routeLookup[$e.route_id]
    $n1   = $nodeLookup[$e.from_node_id]
    $n2   = $nodeLookup[$e.to_node_id]

    if ($e.from_node_id -eq $e.to_node_id) {
        $selfLoops++
        Write-Warning "Self-loop edge detected: $($e.edge_id) on $($rObj.路線名) ($($n1.名称))"
    }

    $dist = Get-HaversineKm ([double]$n1.緯度) ([double]$n1.経度) ([double]$n2.緯度) ([double]$n2.経度)
    if ($rObj.種別 -eq "新幹線") {
        if ($dist -gt $maxShinkansenDist) {
            $maxShinkansenDist = $dist
            $maxShinkansenPair = "$($rObj.路線名): $($n1.名称) -> $($n2.名称) (${dist} km)"
        }
        if ($dist -gt 100.0) {
            $shinkansenWarps++
            Write-Warning "Shinkansen Warp (>100km): $($e.edge_id) $($rObj.路線名) $($n1.名称) -> $($n2.名称) (${dist} km)"
        }
    }
}

Write-Host "  Self-loop edges: $selfLoops"
Write-Host "  Shinkansen abnormal warps (>100km): $shinkansenWarps"
Write-Host "  Max Shinkansen adjacent station distance: $maxShinkansenPair"
$gate3Fails = $selfLoops + $shinkansenWarps
if ($gate3Fails -eq 0) {
    Write-Host "-> Gate 3 Result: PASSED (0 Warps / 0 Self-loops)"
} else {
    Write-Host "-> Gate 3 Result: FAILED ($gate3Fails Anomalies)"
}

# ------------------------------------------------------------------------------
# GATE 4: ホワイトリスト・禁止キーワード（汚染データ）検査
# ------------------------------------------------------------------------------
Write-Host "`n[Gate 4/4] ホワイトリスト・禁止キーワード検査（廃線・未成線・商業施設・遊具混入チェック）..."
$forbiddenRouteRegex = "(廃線|未成線|休止線|森林鉄道|専用線|構内線|軌道跡|[\u0080-\u00FF])"
$forbiddenNodeRegex  = "(廃駅|駅跡|仮乗降場|信号場|操車場|(?<!大村)車両基地|検車区|変電所|エレベーター|エスカレーター|観覧車|ジェットコースター|[\u0080-\u00FF])"
$forbiddenAreaRegex  = "[\u0080-\u00FF]"

$badRoutes = @($routes | Where-Object { $_.路線名 -match $forbiddenRouteRegex })
$badNodes  = @($nodes  | Where-Object { $_.名称 -match $forbiddenNodeRegex })
$badAreas  = @($areas  | Where-Object { $_.名称 -match $forbiddenAreaRegex })

Write-Host "  Forbidden/Mojibake Area matches: $($badAreas.Count)"
Write-Host "  Forbidden/Mojibake Route matches: $($badRoutes.Count)"
Write-Host "  Forbidden/Mojibake Node matches: $($badNodes.Count)"
if ($badAreas.Count -gt 0)  { $badAreas  | Select-Object -First 5 | Format-Table area_id, type_id, 名称 }
if ($badRoutes.Count -gt 0) { $badRoutes | Select-Object -First 5 | Format-Table route_id, 種別, 路線名 }
if ($badNodes.Count -gt 0)  { $badNodes  | Select-Object -First 5 | Format-Table node_id, 種別, 名称 }

$gate4Fails = $badAreas.Count + $badRoutes.Count + $badNodes.Count
if ($gate4Fails -eq 0) {
    Write-Host "-> Gate 4 Result: PASSED (0 Contaminated Records)"
} else {
    Write-Host "-> Gate 4 Result: FAILED ($gate4Fails Contaminated Records)"
}

Write-Host "`n=================================================================="
$totalFails = $gate1Fails + $gate2Fails + $gate3Fails + $gate4Fails
if ($totalFails -eq 0) {
    Write-Host " OVERALL STEP 3 GATE STATUS: ALL 4 GATES PASSED PERFECTLY (0 ERRORS)!"
} else {
    Write-Host " OVERALL STEP 3 GATE STATUS: FAILED ($totalFails issues found)"
}
Write-Host "=================================================================="
