# validate_douo_logic.ps1
# 道央自動車道テストデータ（data/test/douo_highway_test/）の
# 純粋なプログラム（決定論的）による論理検査スクリプト（AI不使用）

param (
    [string]$TestDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test",
    [string]$MasterDir = "c:\Users\user\Documents\PJT\data\master"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [論理検査] 道央自動車道テストデータベース自動整合性検証" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$nodesPath  = Join-Path $TestDir "test_all_highway_nodes.csv"
$edgesPath  = Join-Path $TestDir "test_all_highway_edges.csv"
$routesPath = Join-Path $TestDir "test_all_transport_routes.csv"
$munisPath  = Join-Path $MasterDir "municipalities.csv"

$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

# 大圏距離計算（Haversine）
function Get-HaversineKm($lat1, $lon1, $lat2, $lon2) {
    $R = 6371.0
    $dLat = [Math]::PI * ($lat2 - $lat1) / 180.0
    $dLon = [Math]::PI * ($lon2 - $lon1) / 180.0
    $rLat1 = [Math]::PI * $lat1 / 180.0
    $rLat2 = [Math]::PI * $lat2 / 180.0

    $a = [Math]::Sin($dLat / 2) * [Math]::Sin($dLat / 2) +
         [Math]::Cos($rLat1) * [Math]::Cos($rLat2) *
         [Math]::Sin($dLon / 2) * [Math]::Sin($dLon / 2)
    $c = 2 * [Math]::Atan2([Math]::Sqrt($a), [Math]::Sqrt(1 - $a))
    return $R * $c
}

# --- GATE 1: ファイル存在とスキーマ列数検査 ---
Write-Host "`n--- [Gate 1] スキーマ・フォーマット・タグ混入検査 ---" -ForegroundColor Yellow

$reqFiles = @($nodesPath, $edgesPath, $routesPath, $munisPath)
foreach ($f in $reqFiles) {
    if (-not (Test-Path $f)) {
        $errors.Add("Gate 1: ファイルが存在しません: $f")
    }
}

if ($errors.Count -gt 0) {
    Write-Host "致命的エラー: 必要ファイルが見つかりません。" -ForegroundColor Red
    exit 1
}

$nodesRaw = [System.IO.File]::ReadAllLines($nodesPath, [System.Text.Encoding]::UTF8)
$edgesRaw = [System.IO.File]::ReadAllLines($edgesPath, [System.Text.Encoding]::UTF8)
$routesRaw = [System.IO.File]::ReadAllLines($routesPath, [System.Text.Encoding]::UTF8)

# ヘッダー列数検査
$nodeHeaderCols = ($nodesRaw[0] -split ',').Count
$edgeHeaderCols = ($edgesRaw[0] -split ',').Count
$routeHeaderCols = ($routesRaw[0] -split ',').Count

if ($nodeHeaderCols -ne 21) {
    $errors.Add("Gate 1: nodes.csv のヘッダー列数が不正です (期待値: 21, 実際: $nodeHeaderCols)")
} else {
    Write-Host "  [PASS] nodes.csv 列数: 21列" -ForegroundColor Green
}

if ($edgeHeaderCols -ne 9) {
    $errors.Add("Gate 1: edges.csv のヘッダー列数が不正です (期待値: 9, 実際: $edgeHeaderCols)")
} else {
    Write-Host "  [PASS] edges.csv 列数: 9列" -ForegroundColor Green
}

if ($routeHeaderCols -ne 15) {
    $errors.Add("Gate 1: transport_routes.csv のヘッダー列数が不正です (期待値: 15, 実際: $routeHeaderCols)")
} else {
    Write-Host "  [PASS] transport_routes.csv 列数: 15列" -ForegroundColor Green
}

# HTMLタグ・制御文字・禁止ワード検査
$tagRegex = '<[^>]+>|&nbsp;|&amp;|&quot;'
for ($i = 1; $i -lt $nodesRaw.Count; $i++) {
    $line = $nodesRaw[$i]
    if ($line -match $tagRegex) {
        $errors.Add("Gate 1: nodes.csv 行 $($i+1) に未処理のHTMLタグ・実体参照が含まれています: $($matches[0])")
    }
}
for ($i = 1; $i -lt $edgesRaw.Count; $i++) {
    $line = $edgesRaw[$i]
    if ($line -match $tagRegex) {
        $errors.Add("Gate 1: edges.csv 行 $($i+1) に未処理のHTMLタグ・実体参照が含まれています: $($matches[0])")
    }
}

# CSVパース
$nodes = Import-Csv $nodesPath -Encoding UTF8
$edges = Import-Csv $edgesPath -Encoding UTF8
$routes = Import-Csv $routesPath -Encoding UTF8
$munis = Import-Csv $munisPath -Encoding UTF8

$muniIdSet = [System.Collections.Generic.HashSet[string]]::new()
foreach ($m in $munis) {
    if ($m.municipality_id) { $null = $muniIdSet.Add($m.municipality_id) }
}

# --- GATE 2: 外部キー・参照整合性検査 ---
Write-Host "`n--- [Gate 2] 外部キー・参照整合性検査 ---" -ForegroundColor Yellow

$nodeMap = @{}
$nodeIdSet = [System.Collections.Generic.HashSet[string]]::new()

foreach ($n in $nodes) {
    if (-not $n.node_id) {
        $errors.Add("Gate 2: node_id が空欄のノードが存在します")
        continue
    }
    if ($nodeIdSet.Contains($n.node_id)) {
        $errors.Add("Gate 2: node_id 重複: $($n.node_id)")
    }
    $null = $nodeIdSet.Add($n.node_id)
    $nodeMap[$n.node_id] = $n

    # 自治体IDの整合性
    if ($n.municipality_id -and -not $muniIdSet.Contains($n.municipality_id)) {
        $errors.Add("Gate 2: 存在しない municipality_id: $($n.municipality_id) (ノード: $($n.node_id) $($n.名称))")
    }

    # 北海道BBOX検査 (41.0 <= Lat <= 46.0, 139.0 <= Lon <= 146.0)
    if ($n.緯度 -and $n.経度) {
        $lat = [double]$n.緯度
        $lon = [double]$n.経度
        if ($lat -lt 41.0 -or $lat -gt 46.0 -or $lon -lt 139.0 -or $lon -gt 146.0) {
            $errors.Add("Gate 2: 座標が北海道の範囲外です: $lat, $lon (ノード: $($n.node_id) $($n.名称))")
        }
    }
}
Write-Host "  [PASS] 全 $($nodes.Count) ノードの主キー・外部キー検証完了" -ForegroundColor Green

$routeIdSet = [System.Collections.Generic.HashSet[string]]::new()
foreach ($r in $routes) {
    if ($r.route_id) { $null = $routeIdSet.Add($r.route_id) }
}

foreach ($e in $edges) {
    if (-not $nodeIdSet.Contains($e.from_node_id)) {
        $errors.Add("Gate 2: edges.csv の from_node_id が存在しません: $($e.from_node_id) (エッジ: $($e.edge_id))")
    }
    if (-not $nodeIdSet.Contains($e.to_node_id)) {
        $errors.Add("Gate 2: edges.csv の to_node_id が存在しません: $($e.to_node_id) (エッジ: $($e.edge_id))")
    }
    if (-not $routeIdSet.Contains($e.route_id)) {
        $errors.Add("Gate 2: edges.csv の route_id が存在しません: $($e.route_id) (エッジ: $($e.edge_id))")
    }
}
Write-Host "  [PASS] 全 $($edges.Count) エッジの参照整合性検証完了" -ForegroundColor Green

# --- GATE 3: トポロジーの一筆書き・順序連続性検査 ---
Write-Host "`n--- [Gate 3] トポロジー一筆書き・連続性検査 ---" -ForegroundColor Yellow

$prevToNode = $null
$expectedSeq = 1

for ($i = 0; $i -lt $edges.Count; $i++) {
    $e = $edges[$i]
    $seq = [int]$e.順序

    if ($seq -ne $expectedSeq) {
        $errors.Add("Gate 3: エッジ順序の欠番/飛び: 期待値 $expectedSeq, 実際 $seq (エッジ: $($e.edge_id))")
    }
    $expectedSeq++

    if ($prevToNode -ne $null) {
        if ($e.from_node_id -ne $prevToNode) {
            $prevName = $nodeMap[$prevToNode].名称
            $currName = $nodeMap[$e.from_node_id].名称
            $errors.Add("Gate 3: トポロジー断絶! 直前終点 [${prevName}] ($prevToNode) と 現在起点 [${currName}] ($($e.from_node_id)) が一致しません (エッジ: $($e.edge_id))")
        }
    }
    $prevToNode = $e.to_node_id
}
Write-Host "  [PASS] 全 $($edges.Count) エッジの完全一筆書き連続性を確認" -ForegroundColor Green

# 路線起終点との整合性
$route0 = $routes[0]
if ($edges[0].from_node_id -ne $route0.起点ノード_id) {
    $errors.Add("Gate 3: 路線起点ノード ($($route0.起点ノード_id)) と 第1エッジ起点 ($($edges[0].from_node_id)) が不一致")
}
if ($edges[-1].to_node_id -ne $route0.終点ノード_id) {
    $errors.Add("Gate 3: 路線終点ノード ($($route0.終点ノード_id)) と 最終エッジ終点 ($($edges[-1].to_node_id)) が不一致")
}

# --- GATE 4: 空間幾何・距離検算検査 ---
Write-Host "`n--- [Gate 4] 空間幾何・距離検算検査 ---" -ForegroundColor Yellow

$totalCalcDist = 0.0

foreach ($e in $edges) {
    $n1 = $nodeMap[$e.from_node_id]
    $n2 = $nodeMap[$e.to_node_id]

    $distKmStr = $e.距離_km
    if (-not [string]::IsNullOrWhiteSpace($distKmStr)) {
        $distKm = [double]$distKmStr
        $totalCalcDist += $distKm

        if ($distKm -le 0.0) {
            $errors.Add("Gate 4: 距離が0または負です: $distKm km (エッジ: $($e.edge_id) $($e.備考))")
        }

        # 大圏直線距離との照合（両方に座標がある場合）
        if ($n1.緯度 -and $n1.経度 -and $n2.緯度 -and $n2.経度) {
            $straightKm = Get-HaversineKm ([double]$n1.緯度) ([double]$n1.経度) ([double]$n2.緯度) ([double]$n2.経度)
            
            # 直線距離が台帳道路距離を大幅に超えている場合は座標ワープの疑い（余裕係数 1.05: 測量差考慮）
            if ($straightKm -gt ($distKm * 1.05 + 0.5)) {
                $errors.Add("Gate 4: 幾何学的破綻（直線距離が台帳距離を超過）: 直線=$([Math]::Round($straightKm, 1))km > 台帳=$distKm km (エッジ: $($e.edge_id) $($n1.名称)➔$($n2.名称))")
            }

            # 隣接区間で50km以上の異常ジャンプ
            if ($distKm -gt 50.0) {
                $warnings.Add("Gate 4 [注意]: 区間距離が50kmを超えています: $distKm km ($($n1.名称) ➔ $($n2.名称))")
            }
        }
    } else {
        # 計画区間・未供用区間などの場合
        if ($e.状態 -eq '供用中') {
            $warnings.Add("Gate 4 [注意]: 供用中区間なのに距離_kmが空欄です: (エッジ: $($e.edge_id) $($n1.名称)➔$($n2.名称))")
        }
    }
}

Write-Host "  [PASS] エッジ積算距離: $([Math]::Round($totalCalcDist, 1)) km" -ForegroundColor Green

# --- 判定サマリー ---
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [検査結果サマリー]" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($warnings.Count -gt 0) {
    Write-Host "警告 ($($warnings.Count) 件):" -ForegroundColor Yellow
    foreach ($w in $warnings) {
        Write-Host "  [WARN] $w" -ForegroundColor Yellow
    }
}

if ($errors.Count -eq 0) {
    Write-Host "`n【ALL PASS】すべての論理検査ゲートを完全クリアしました (エラー: 0件)" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n【FAILED】$($errors.Count) 件の論理エラーを検出しました:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "  [ERROR] $err" -ForegroundColor Red
    }
    exit 1
}
