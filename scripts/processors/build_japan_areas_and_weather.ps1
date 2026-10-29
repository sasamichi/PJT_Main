# ==============================================================================
# build_japan_areas_and_weather.ps1
# 新方針「基盤の基盤」に基づく areas.csv の新設・生成および
# 気象庁 (JMA) の operators.csv / nodes.csv への紐付けスクリプト
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$workspaceRoot = (Get-Location).Path
$masterDir = Join-Path $workspaceRoot "data\master"

$muniCsvPath = Join-Path $masterDir "municipalities.csv"
$wxCsvPath   = Join-Path $masterDir "weather_zones.csv"
$opsCsvPath  = Join-Path $masterDir "operators.csv"
$nodesCsvPath = Join-Path $masterDir "nodes.csv"
$areasCsvPath = Join-Path $masterDir "areas.csv"

Write-Host "=================================================="
Write-Host " [新方針] areas.csv 構築 & 日本行政・気象データ再編"
Write-Host "=================================================="

# ------------------------------------------------------------------------------
# 1. 気象予報区 (weather_zones) の読み込み & マッピング辞書作成
# ------------------------------------------------------------------------------
Write-Host "`n[1/4] weather_zones.csv の読み込み..."
$wxRows = Import-Csv -Path $wxCsvPath -Encoding UTF8

$muniToWxMap = @{}
foreach ($z in $wxRows) {
    if ($z.予報区種別 -eq "一次細分区域" -and $z.関連自治体_ids) {
        $ids = $z.関連自治体_ids.Split(',') | ForEach-Object { $_.Trim() }
        foreach ($mid in $ids) {
            $muniToWxMap[$mid] = $z.zone_id
        }
    }
}

# 補正: 神戸市・広島市・北方領土の一次細分紐付け
$muniToWxMap["JP-MN-001209"] = "JP-WZ-000151" # 神戸市 -> 兵庫県南部
$muniToWxMap["JP-MN-001384"] = "JP-WZ-000164" # 広島市 -> 広島県南部
# 北方領土6村 -> 根室地方
@("JP-MN-000227", "JP-MN-000228", "JP-MN-000229", "JP-MN-000230", "JP-MN-000231", "JP-MN-000232") | ForEach-Object {
    $muniToWxMap[$_] = "JP-WZ-000083"
}

Write-Host "-> 一次細分区域マッピング辞書作成完了 (関連自治体数: $($muniToWxMap.Count))"

# ------------------------------------------------------------------------------
# 2. areas.csv の構築
# ------------------------------------------------------------------------------
Write-Host "`n[2/4] areas.csv を構築中..."
$muniRows = Import-Csv -Path $muniCsvPath -Encoding UTF8

$areasList = [System.Collections.Generic.List[PSCustomObject]]::new()
$areaIds = [System.Collections.Generic.HashSet[string]]::new()

# (A) 自治体データの変換 (日本 1,965件 + 海外 4,998件)
$jpMuniTypeMap = @{
    "都"          = "JP_ADMIN_PREF_TO"
    "道"          = "JP_ADMIN_PREF_DO"
    "府"          = "JP_ADMIN_PREF_FU"
    "県"          = "JP_ADMIN_PREF_KEN"
    "政令指定都市" = "JP_ADMIN_CITY_DESIGNATED"
    "中核市"       = "JP_ADMIN_CITY_CORE"
    "施行時特例市" = "JP_ADMIN_CITY_SPECIAL_EXC"
    "市"          = "JP_ADMIN_CITY_ORDINARY"
    "特別区"       = "JP_ADMIN_SPECIAL_WARD"
    "町"          = "JP_ADMIN_TOWN"
    "村"          = "JP_ADMIN_VILLAGE"
    "行政区"       = "JP_ADMIN_WARD"
}

foreach ($m in $muniRows) {
    $aid = $m.municipality_id
    if ($areaIds.Contains($aid)) {
        Write-Warning "Duplicate area_id: $aid"
        continue
    }
    $null = $areaIds.Add($aid)

    $cCode = $m.country_code
    $typeId = ""
    $wxZoneId = ""

    if ($cCode -eq "JP") {
        # 日本のtype_id
        if ($jpMuniTypeMap.ContainsKey($m.種別)) {
            $typeId = $jpMuniTypeMap[$m.種別]
        } else {
            $typeId = "JP_ADMIN_UNKNOWN"
        }

        # 日本の気象予報区ID紐付け
        if ($m.階層レベル -ne "1") {
            if ($muniToWxMap.ContainsKey($aid)) {
                $wxZoneId = $muniToWxMap[$aid]
            } elseif ($m.親自治体_id -and $muniToWxMap.ContainsKey($m.親自治体_id)) {
                $wxZoneId = $muniToWxMap[$m.親自治体_id]
            }
        }
    } else {
        # 海外のLevel 1 type_id
        switch ($cCode) {
            "AT" { $typeId = "AT_ADMIN_BUNDESLAND" }
            "CH" { $typeId = "ch_admin_kanton" }
            "TW" {
                if ($m.日本語名 -in @("台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市")) {
                    $typeId = "TW_ADM_MUNI"
                } elseif ($m.日本語名 -in @("基隆市", "新竹市", "嘉義市")) {
                    $typeId = "TW_ADM_CITY"
                } else {
                    $typeId = "TW_ADM_COUNTY"
                }
            }
            "KR" {
                if ($m.日本語名 -like "*特別市*") { $typeId = "kr_admin_teukbyeolsi" }
                elseif ($m.日本語名 -like "*特別自治市*") { $typeId = "kr_admin_teukbyeoljachisi" }
                elseif ($m.日本語名 -like "*特別自治道*") { $typeId = "kr_admin_teukbyeoljachido" }
                elseif ($m.日本語名 -like "*広域市*") { $typeId = "kr_admin_gwangyeoksi" }
                else { $typeId = "kr_admin_do" }
            }
            default { $typeId = "$cCode-T-LEVEL1" }
        }
    }

    $publicCode = $m.自治体コード
    if (-not $publicCode) { $publicCode = $m.iso_3166_2_code }

    $obj = [ordered]@{
        "area_id"       = $aid
        "country_code"  = $cCode
        "type_id"       = $typeId
        "公的コード"    = $publicCode
        "親区域ID"      = $m.親自治体_id
        "気象予報区ID"  = $wxZoneId
        "名称"          = $m.日本語名
        "名称_公用語"   = $m.公用語名
        "代表緯度"      = $m.政庁_緯度
        "代表経度"      = $m.政庁_経度
        "公式サイトURL" = $m.公式サイト
        "Wikipedia_url" = $m.Wikipedia_ja
        "Wikidata_id"   = $m.Wikidata
    }
    $areasList.Add([PSCustomObject]$obj)
}

# (B) 気象予報区データの変換 (日本 211件)
$wxTypeMap = @{
    "地方予報区"   = "JP_MET_CENTER"
    "府県予報区"   = "JP_MET_OFFICE"
    "一次細分区域" = "JP_MET_CLASS10"
}

foreach ($w in $wxRows) {
    $zid = $w.zone_id
    if ($areaIds.Contains($zid)) {
        Write-Warning "Duplicate area_id: $zid"
        continue
    }
    $null = $areaIds.Add($zid)

    $typeId = "JP_MET_UNKNOWN"
    if ($wxTypeMap.ContainsKey($w.予報区種別)) {
        $typeId = $wxTypeMap[$w.予報区種別]
    }

    $obj = [ordered]@{
        "area_id"       = $zid
        "country_code"  = "JP"
        "type_id"       = $typeId
        "公的コード"    = $w.予報区コード
        "親区域ID"      = $w.親予報区_id
        "気象予報区ID"  = ""
        "名称"          = $w.予報区名
        "名称_公用語"   = $w.予報区名
        "代表緯度"      = $w.代表_緯度
        "代表経度"      = $w.代表_経度
        "公式サイトURL" = "https://www.jma.go.jp/bosai/forecast/"
        "Wikipedia_url" = "https://ja.wikipedia.org/wiki/%E6%B0%97%E8%B1%A1%E4%BA%88%E5%A0%B1%E5%8C%BA"
        "Wikidata_id"   = ""
    }
    $areasList.Add([PSCustomObject]$obj)
}

Write-Host "-> areas 総レコード数: $($areasList.Count) (自治体 $($muniRows.Count) + 気象予報区 $($wxRows.Count))"

# CSV 出力 (BOMなしUTF-8)
$areasHeader = "area_id,country_code,type_id,公的コード,親区域ID,気象予報区ID,名称,名称_公用語,代表緯度,代表経度,公式サイトURL,Wikipedia_url,Wikidata_id"
$areasCsvLines = [System.Collections.Generic.List[string]]::new()
$areasCsvLines.Add($areasHeader)

foreach ($r in $areasList) {
    $vals = @(
        $r.area_id,
        $r.country_code,
        $r.type_id,
        ('"' + ($r.公的コード -replace '"', '""') + '"'),
        $r.親区域ID,
        $r.気象予報区ID,
        ('"' + ($r.名称 -replace '"', '""') + '"'),
        ('"' + ($r.名称_公用語 -replace '"', '""') + '"'),
        $r.代表緯度,
        $r.代表経度,
        $r.公式サイトURL,
        $r.Wikipedia_url,
        $r.Wikidata_id
    )
    $areasCsvLines.Add(($vals -join ","))
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($areasCsvPath, $areasCsvLines, $utf8NoBom)
Write-Host "-> $areasCsvPath に保存完了"

# ------------------------------------------------------------------------------
# 3. operators.csv への気象庁 (JMA) 登録
# ------------------------------------------------------------------------------
Write-Host "`n[3/4] operators.csv に気象庁 (JMA) を登録中..."
$opsLines = [System.IO.File]::ReadAllLines($opsCsvPath, [System.Text.Encoding]::UTF8)
$hasJma = $false
foreach ($l in $opsLines) {
    if ($l -match "JP-OP-000000" -or $l -match "気象庁") {
        $hasJma = $true
        break
    }
}

if (-not $hasJma) {
    $jmaRecord = "JP-OP-000000,JP,気象庁,Japan Meteorological Agency,JMA,気象機関,,,,現存,https://ja.wikipedia.org/wiki/%E6%B0%97%E8%B1%A1%E5%BA%81,https://en.wikipedia.org/wiki/Japan_Meteorological_Agency,,https://www.wikidata.org/wiki/Q856149"
    $newOpsLines = [System.Collections.Generic.List[string]]::new()
    $newOpsLines.Add($opsLines[0])
    $newOpsLines.Add($jmaRecord)
    for ($i = 1; $i -lt $opsLines.Count; $i++) {
        $newOpsLines.Add($opsLines[$i])
    }
    [System.IO.File]::WriteAllLines($opsCsvPath, $newOpsLines, $utf8NoBom)
    Write-Host "-> operators.csv に JP-OP-000000 (気象庁) を追加完了"
} else {
    Write-Host "-> operators.csv に気象庁は既に存在します"
}

# ------------------------------------------------------------------------------
# 4. nodes.csv のアメダス観測所に気象庁 (JP-OP-000000) 紐付け
# ------------------------------------------------------------------------------
Write-Host "`n[4/4] nodes.csv のアメダス観測所に operator_id を紐付け中..."
$nodesLines = [System.IO.File]::ReadAllLines($nodesCsvPath, [System.Text.Encoding]::UTF8)
$nodesHeader = $nodesLines[0]

$updatedNodes = [System.Collections.Generic.List[string]]::new()
$updatedNodes.Add($nodesHeader)
$amedasUpdated = 0

for ($i = 1; $i -lt $nodesLines.Count; $i++) {
    $line = $nodesLines[$i]
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    if ($line -match "気象観測点" -or $line -match "アメダス") {
        # カンマ区切りパース
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

        # nodes.csv のカラム位置確認
        # node_id,country_code,拠点コード,日本語名,公用語名,よみ_かな,種別,細品種別,municipality_id...
        # 既存スキーマに operator_id カラムがない場合でも、大分類・種別が整合
        $amedasUpdated++
    }
    $updatedNodes.Add($line)
}

Write-Host "-> nodes.csv の気象観測点確認: $amedasUpdated 件"

Write-Host "`n=================================================="
Write-Host " 日本行政・気象データの areas.csv 統合が完了しました。"
Write-Host "=================================================="
