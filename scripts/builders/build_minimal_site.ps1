# -*- coding: utf-8 -*-
# build_minimal_site.ps1: 最低限Webサイト（仮）専用データ抽出・HTML生成ビルダー
# --------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$masterDir = Join-Path $projectRoot "data\master"
$outDir = Join-Path $projectRoot "web\minimal"
$jsDir = Join-Path $outDir "js"
$cssDir = Join-Path $outDir "css"

# 出力先ディレクトリの確保
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
if (-not (Test-Path $jsDir)) { New-Item -ItemType Directory -Path $jsDir -Force | Out-Null }
if (-not (Test-Path $cssDir)) { New-Item -ItemType Directory -Path $cssDir -Force | Out-Null }

Write-Host "=========================================================="
Write-Host " 最低限Webサイト（仮）多層ツリーデータ抽出・ビルドを開始します"
Write-Host "=========================================================="

# 1. 国マスタの読み込み (countries.csv)
Write-Host "[1/5] 国マスタ (countries.csv) を読み込み中..."
$countriesCsv = Join-Path $masterDir "countries.csv"
$rawCountries = Import-Csv -Path $countriesCsv
$countriesList = @()
foreach ($c in $rawCountries) {
    if ($c.country_code -and $c.country_code -ne "INT") {
        $countriesList += @{
            code = $c.country_code
            name = $c.日本語名
            en = $c.公用語名
            side = $c.車両通行側
        }
    }
}
Write-Host "  -> 全 $($countriesList.Count) カ国を抽出しました。"

# 2. 日本の行政区画マスタの読み込み (areas.csv) - 多層ツリー構築
Write-Host "[2/5] 日本の行政区画 (areas.csv) から多層ツリーを構築中..."
$areasCsv = Join-Path $masterDir "areas.csv"
$rawAreas = Import-Csv -Path $areasCsv | Where-Object { $_.country_code -eq "JP" }

# 地方区分マッピング
$regionDefs = @(
    @{ name = "北海道地方"; prefs = @("北海道") },
    @{ name = "東北地方"; prefs = @("青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県") },
    @{ name = "関東地方"; prefs = @("茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県") },
    @{ name = "中部地方"; prefs = @("新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県") },
    @{ name = "近畿地方"; prefs = @("三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県") },
    @{ name = "中国地方"; prefs = @("鳥取県", "島根県", "岡山県", "広島県", "山口県") },
    @{ name = "四国地方"; prefs = @("徳島県", "香川県", "愛媛県", "高知県") },
    @{ name = "九州・沖縄地方"; prefs = @("福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県") }
)

# 都道府県マスタの辞書化 (area_id -> Pref Object)
$prefMap = @{}
$prefNameMap = @{}
foreach ($a in $rawAreas) {
    if ($a.type_id -like "*_ADMIN_PREF_*") {
        $pObj = @{
            id = $a.area_id
            name = $a.名称
            code = $a.公的コード
            designatedCities = @() # 政令指定都市
            cities = @()           # 一般市・区・町・村
        }
        $prefMap[$a.area_id] = $pObj
        $prefNameMap[$a.名称] = $pObj
    }
}

# 政令指定都市マスタ (area_id -> Designated City Object)
$desigCityMap = @{}
foreach ($a in $rawAreas) {
    if ($a.type_id -eq "JP_ADMIN_CITY_DESIGNATED") {
        $cObj = @{
            id = $a.area_id
            name = $a.名称
            code = $a.公的コード
            prefId = $a.親区域ID
            wards = @() # 行政区
            nodes = @()
        }
        $desigCityMap[$a.area_id] = $cObj
        if ($prefMap.ContainsKey($a.親区域ID)) {
            $prefMap[$a.親区域ID].designatedCities += $cObj
        }
    }
}

# 全市区町村・区マスタ (area_id -> Unit Object)
$allUnitMap = @{} # ノード紐付け用の全自治体単位辞書
foreach ($a in $rawAreas) {
    # 行政区 (政令市の下)
    if ($a.type_id -eq "JP_ADMIN_WARD") {
        $wObj = @{
            id = $a.area_id
            name = $a.名称
            code = $a.公的コード
            type = "区"
            parentId = $a.親区域ID
            nodes = @()
        }
        $allUnitMap[$a.area_id] = $wObj
        if ($desigCityMap.ContainsKey($a.親区域ID)) {
            $desigCityMap[$a.親区域ID].wards += $wObj
        }
    }
    # 一般市区町村・特別区 (CITY, TOWN, VILLAGE, SPECIAL_WARD)
    elseif ($a.type_id -like "*_ADMIN_CITY_*" -or $a.type_id -like "*_ADMIN_TOWN*" -or $a.type_id -like "*_ADMIN_VILLAGE*" -or $a.type_id -eq "JP_ADMIN_SPECIAL_WARD") {
        if ($a.type_id -ne "JP_ADMIN_CITY_DESIGNATED") {
            # 親都道府県の特定
            $parentPrefId = $a.親区域ID
            if (-not $prefMap.ContainsKey($parentPrefId)) {
                $mid = $rawAreas | Where-Object { $_.area_id -eq $parentPrefId } | Select-Object -First 1
                if ($mid -and $prefMap.ContainsKey($mid.親区域ID)) {
                    $parentPrefId = $mid.親区域ID
                }
            }
            
            $kindName = "市町村"
            if ($a.type_id -eq "JP_ADMIN_SPECIAL_WARD") { $kindName = "特別区" }
            elseif ($a.type_id -like "*_TOWN*") { $kindName = "町" }
            elseif ($a.type_id -like "*_VILLAGE*") { $kindName = "村" }
            elseif ($a.type_id -like "*_CITY*") { $kindName = "市" }

            $cObj = @{
                id = $a.area_id
                name = $a.名称
                code = $a.公的コード
                type = $kindName
                prefId = $parentPrefId
                nodes = @()
            }
            $allUnitMap[$a.area_id] = $cObj
            if ($prefMap.ContainsKey($parentPrefId)) {
                $prefMap[$parentPrefId].cities += $cObj
            }
        }
    }
}
Write-Host "  -> 都道府県: $($prefMap.Count) 件, 政令市: $($desigCityMap.Count) 件, 基礎自治体・区: $($allUnitMap.Count) 件"

# 3. 交通拠点ノードの読み込みと多層ツリーへの紐付け (nodes.csv)
Write-Host "[3/5] 交通拠点ノード (nodes.csv) を読み込み中..."
$nodesCsv = Join-Path $masterDir "nodes.csv"
$rawNodes = Import-Csv -Path $nodesCsv | Where-Object { $_.country_code -eq "JP" }

$flatNodes = @()
foreach ($n in $rawNodes) {
    $lat = $null
    $lng = $null
    if ($n.緯度 -and [double]::TryParse($n.緯度, [ref]$lat)) {
        $lat = [math]::Round($lat, 5)
    }
    if ($n.経度 -and [double]::TryParse($n.経度, [ref]$lng)) {
        $lng = [math]::Round($lng, 5)
    }
    
    $unitName = ""
    $prefName = ""
    if ($n.area_id -and $allUnitMap.ContainsKey($n.area_id)) {
        $uObj = $allUnitMap[$n.area_id]
        $unitName = $uObj.name
        # 親が政令市の場合
        if ($uObj.parentId -and $desigCityMap.ContainsKey($uObj.parentId)) {
            $pCity = $desigCityMap[$uObj.parentId]
            $unitName = "$($pCity.name) $($uObj.name)"
            if ($pCity.prefId -and $prefMap.ContainsKey($pCity.prefId)) {
                $prefName = $prefMap[$pCity.prefId].name
            }
        } elseif ($uObj.prefId -and $prefMap.ContainsKey($uObj.prefId)) {
            $prefName = $prefMap[$uObj.prefId].name
        }
    } elseif ($n.area_id -and $desigCityMap.ContainsKey($n.area_id)) {
        $dCity = $desigCityMap[$n.area_id]
        $unitName = $dCity.name
        if ($dCity.prefId -and $prefMap.ContainsKey($dCity.prefId)) {
            $prefName = $prefMap[$dCity.prefId].name
        }
    } elseif ($n.area_id -and $prefMap.ContainsKey($n.area_id)) {
        $prefName = $prefMap[$n.area_id].name
    }

    $nodeObj = @{
        id = $n.node_id
        name = $n.名称
        kind = $n.種別
        cat = $n.大分類
        code = $n.公的コード
        lat = $lat
        lng = $lng
        pref = $prefName
        city = $unitName
    }
    $flatNodes += $nodeObj
    
    # ツリーへの紐付け
    $leafNode = @{
        id = $n.node_id
        name = $n.名称
        kind = $n.種別
        code = $n.公的コード
        lat = $lat
        lng = $lng
    }
    if ($n.area_id -and $allUnitMap.ContainsKey($n.area_id)) {
        $allUnitMap[$n.area_id].nodes += $leafNode
    } elseif ($n.area_id -and $desigCityMap.ContainsKey($n.area_id)) {
        $desigCityMap[$n.area_id].nodes += $leafNode
    }
}
Write-Host "  -> ノード: $($flatNodes.Count) 件"

# 地方区分ごとの多層ツリー構造の組み立て
$regionsData = @()
foreach ($rDef in $regionDefs) {
    $pList = @()
    foreach ($pName in $rDef.prefs) {
        if ($prefNameMap.ContainsKey($pName)) {
            $pList += $prefNameMap[$pName]
        }
    }
    $regionsData += @{
        name = $rDef.name
        prefectures = $pList
    }
}

# 4. JSONデータファイルの生成 (web/minimal/js/data.js)
Write-Host "[4/5] web/minimal/js/data.js を出力中..."

$summaryStats = @{
    totalCountries = $countriesList.Count
    totalRegions = $regionsData.Count
    totalPrefectures = $prefMap.Count
    totalCities = $allUnitMap.Count
    totalNodes = $flatNodes.Count
    updatedAt = (Get-Date).ToString("yyyy-MM-dd")
}

$minimalData = @{
    stats = $summaryStats
    countries = $countriesList
    regions = $regionsData
    nodes = $flatNodes
}

$jsonData = $minimalData | ConvertTo-Json -Depth 20 -Compress
$dataJsContent = "window.MINIMAL_DATA = $jsonData;"
$dataJsPath = Join-Path $jsDir "data.js"
[System.IO.File]::WriteAllText($dataJsPath, $dataJsContent, [System.Text.Encoding]::UTF8)

$sizeKb = [math]::Round((Get-Item $dataJsPath).Length / 1KB, 1)
Write-Host "  -> data.js 出力完了 (サイズ: $sizeKb KB)"

# 5. Googleサイト埋め込み用単一HTMLの自動生成 (embed_all_in_one.html)
Write-Host "[5/5] Googleサイト埋め込み用単体HTML (embed_all_in_one.html) を自動結合生成中..."

$cssPath = Join-Path $cssDir "minimal.css"
$treeJsPath = Join-Path $jsDir "tree.js"
$mapJsPath = Join-Path $jsDir "map.js"

$cssText = [System.IO.File]::ReadAllText($cssPath, [System.Text.Encoding]::UTF8)
$treeJsText = [System.IO.File]::ReadAllText($treeJsPath, [System.Text.Encoding]::UTF8)
$mapJsText = [System.IO.File]::ReadAllText($mapJsPath, [System.Text.Encoding]::UTF8)

$allInOneHtml = @"
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>世界交通網・地域データ基盤 (Googleサイト埋め込み版)</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <style>
$cssText
    body { background: #ffffff; padding: 4px; }
    .site-header { position: sticky; top: 0; background: #ffffff; border-bottom: 2px solid var(--border); padding: 8px 12px; margin-bottom: 8px; z-index: 1000; }
    .map-layout { height: 620px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); position: relative; }
  </style>
</head>
<body>

  <header class="site-header">
    <div class="brand-title">
      🌐 <span>世界交通網・地域データ基盤</span>
      <span class="brand-badge">EMBED</span>
    </div>
    <div class="header-nav">
      <button id="tab-btn-tree" class="nav-tab-btn active" onclick="switchEmbedTab('tree')">📖 階層・一覧検索</button>
      <button id="tab-btn-map" class="nav-tab-btn" onclick="switchEmbedTab('map')">🗺️ 地図ビュー</button>
    </div>
  </header>

  <!-- 階層検索タブエリア -->
  <div id="embed-tab-tree" class="main-container" style="padding: 0;">
    <!-- パンくずナビゲーション -->
    <div class="breadcrumb-bar" id="breadcrumb-bar">
      <span class="bc-item active" id="bc-world" onclick="window.showWorldView()">🌍 世界の国一覧</span>
      <span class="bc-sep" id="bc-sep" style="display:none;">›</span>
      <span class="bc-item" id="bc-country" style="display:none;">🇯🇵 日本</span>
    </div>

    <!-- Top画面：世界全カ国一覧ビュー (初期表示) -->
    <div id="view-world-area">
      <div class="search-box-card" style="margin-bottom: 12px;">
        <div class="search-input-wrapper">
          <span class="search-icon">🔍</span>
          <input type="text" id="world-search-input" class="search-input" placeholder="国名または国コードを入力して検索 (例: 日本、JP、アメリカ、フランス)...">
          <button id="world-search-clear-btn" class="search-clear-btn">✕</button>
        </div>
      </div>
      <div class="tree-results-card">
        <div class="card-title">
          <span>🌍 世界全251カ国・地域 (行をタップすると詳細を展開)</span>
          <span id="world-count-badge" style="font-size: 11px; font-weight: normal; color: var(--text-muted);">250カ国収録</span>
        </div>
        <div id="world-country-grid"></div>
      </div>
    </div>

    <!-- 日本詳細画面：多層ツリー構造 (初期非表示) -->
    <div id="view-japan-area" style="display: none;">
      <!-- 上部戻るボタン ＆ 検索バー -->
      <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
        <button class="nav-tab-btn" onclick="window.showWorldView()" style="padding: 6px 12px;">◀ 世界の国一覧に戻る</button>
        <div class="search-input-wrapper" style="flex: 1; min-width: 240px;">
          <span class="search-icon">🔍</span>
          <input type="text" id="search-input" class="search-input" placeholder="全国の駅名・空港・港湾・自治体名を検索...">
          <button id="search-clear-btn" class="search-clear-btn">✕</button>
        </div>
      </div>

      <!-- 多層ツリー展開コンテナ -->
      <div class="tree-results-card">
        <div class="card-title">
          <span id="japan-tree-title">🏛️ 日本の行政・交通 多層ツリー (地方 ➔ 都道府県 ➔ 市区町村 ➔ 拠点)</span>
          <span id="result-stats" style="font-size: 11px; font-weight: normal; color: var(--text-muted);"></span>
        </div>
        <div id="tree-container" class="tree-container"></div>
      </div>
    </div>
  </div>

  <!-- 地図ビュータブエリア (初期非表示) -->
  <div id="embed-tab-map" style="display: none; position: relative;">
    <div class="map-layout">
      <div id="map"></div>

      <!-- 地図上部フィルターバー ＆ 階層に戻るボタン -->
      <div class="map-filter-bar">
        <button class="nav-tab-btn" onclick="switchEmbedTab('tree')" style="font-size: 11px; padding: 3px 8px; background: #1e3a8a; color: #fff; border-color: #1e3a8a;">◀ 階層ビューに戻る</button>
        <label class="filter-chip"><input type="checkbox" data-filter="airSea" checked><span>✈️ 空港・港湾</span></label>
        <label class="filter-chip"><input type="checkbox" data-filter="shinkansen" checked><span>🚄 新幹線・主要駅</span></label>
        <label class="filter-chip"><input type="checkbox" data-filter="railways" checked><span>🚆 一般鉄道駅</span></label>
        <label class="filter-chip"><input type="checkbox" data-filter="roads" checked><span>🛣️ IC・道の駅</span></label>
        <label class="filter-chip"><input type="checkbox" data-filter="weather"><span>🌡️ 気象観測点</span></label>
      </div>

      <div class="map-info-bar">
        <span id="map-marker-count">読み込み中...</span>
      </div>
    </div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    window.IS_EMBED = true;
    $dataJsContent
  </script>
  <script>
    $treeJsText
  </script>
  <script>
    $mapJsText

    function switchEmbedTab(tab) {
      const treeTab = document.getElementById('embed-tab-tree');
      const mapTab = document.getElementById('embed-tab-map');
      const btnTree = document.getElementById('tab-btn-tree');
      const btnMap = document.getElementById('tab-btn-map');

      if (tab === 'tree') {
        treeTab.style.display = 'block';
        mapTab.style.display = 'none';
        btnTree.classList.add('active');
        btnMap.classList.remove('active');
      } else {
        treeTab.style.display = 'none';
        mapTab.style.display = 'block';
        btnTree.classList.remove('active');
        btnMap.classList.add('active');
        if (window.leafletMap) {
          setTimeout(() => { window.leafletMap.invalidateSize(); }, 150);
        }
      }
    }

    const origJumpToMap = window.jumpToMap;
    window.jumpToMap = function(lat, lng, name, nodeId) {
      switchEmbedTab('map');
      if (origJumpToMap) origJumpToMap(lat, lng, name, nodeId);
    };

    window.returnToTreeFromMap = function(nodeId) {
      switchEmbedTab('tree');
      if (nodeId && typeof window.highlightNodeInTree === 'function') {
        window.highlightNodeInTree(nodeId);
      }
    };
  </script>
</body>
</html>
"@

$embedAllInOnePath = Join-Path $outDir "embed_all_in_one.html"
[System.IO.File]::WriteAllText($embedAllInOnePath, $allInOneHtml, [System.Text.Encoding]::UTF8)
$sizeEmbedKb = [math]::Round((Get-Item $embedAllInOnePath).Length / 1KB, 1)
Write-Host "  -> embed_all_in_one.html 出力完了 (サイズ: $sizeEmbedKb KB)"

Write-Host "=========================================================="
Write-Host " 全ファイルのビルド・結合が正常に完了しました！"
Write-Host "=========================================================="
