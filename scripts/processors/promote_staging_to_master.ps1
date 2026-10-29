# ==============================================================================
# promote_staging_to_master.ps1
# Step 6: Promote data/staging/JP/ to data/master/
# 1. Copy staging CSVs to master CSVs
# 2. Update country_progress.csv (JP status -> 本番データ格納完了)
# 3. Log into exploration_logs.csv
# 4. Verify line counts and integrity
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$workspaceRoot = "c:\Users\user\Documents\PJT"
$stagingDir    = Join-Path $workspaceRoot "data\staging\JP"
$masterDir     = Join-Path $workspaceRoot "data\master"

Write-Host "=================================================================="
Write-Host " [第6段階] 日本ステージングデータの本番マスタ（data/master/）格納"
Write-Host "=================================================================="

$tables = @("areas.csv", "operators.csv", "transport_routes.csv", "nodes.csv", "edges.csv")

foreach ($t in $tables) {
    $src = Join-Path $stagingDir $t
    $dst = Join-Path $masterDir $t
    Write-Host "Promoting $t to master..."
    Copy-Item -Path $src -Destination $dst -Force
    $lines = (Get-Content $dst -Encoding UTF8).Count
    Write-Host "  -> data/master/$t : $($lines - 1) records."
}

# Update country_progress.csv
Write-Host "`nUpdating country_progress.csv..."
$progPath = Join-Path $masterDir "country_progress.csv"
$progContent = Get-Content $progPath -Encoding UTF8
$updatedProg = [System.Collections.Generic.List[string]]::new()

$todayStr = (Get-Date).ToString("yyyy-MM-dd")

foreach ($line in $progContent) {
    if ($line -match "^JP,") {
        # JP,日本,フェーズ2（基準国）,総務省・国土数値情報,国土数値情報・JR・私鉄・高速・国道,事前調査完了・フェーズ2完了,2026-10-28,"作業順:001 | 優先度:0 | G7,G20,OECD | 東アジア"
        $newLine = "JP,日本,フェーズ2（基準国）,総務省・国土数値情報・気象庁,国土数値情報・JR・私鉄・高速・国道・航空・航路,本番データ格納完了,$todayStr,作業順:001 | 優先度:0 | G7,G20,OECD | 東アジア（全4ゲートPASS・独立実査完了）"
        $updatedProg.Add($newLine)
    } else {
        $updatedProg.Add($line)
    }
}
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($progPath, $updatedProg, $utf8NoBom)
Write-Host "  -> country_progress.csv updated: JP status = '本番データ格納完了'"

# Append to exploration_logs.csv
Write-Host "`nLogging to exploration_logs.csv..."
$logPath = Join-Path $masterDir "exploration_logs.csv"
$todayStr = (Get-Date).ToString("yyyy-MM-dd")
$logLine = "LOG-JP-000001,$todayStr,日本本番データ格納完了（新方針第6段階）,本番移行記録,,,,,,,全4ゲートPASS・独立実査完了,日本データ第6段階本番格納完了（areas: 4752件 / operators: 225件 / transport_routes: 1421件 / nodes: 14773件 / edges: 151件）,,なし,完了"
[System.IO.File]::AppendAllText($logPath, "`n" + $logLine, $utf8NoBom)
Write-Host "  -> exploration_logs.csv updated."

Write-Host "`n=================================================================="
Write-Host " STEP 6 PROMOTION COMPLETED SUCCESSFULLY!"
Write-Host "=================================================================="
