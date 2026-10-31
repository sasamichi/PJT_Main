# parse_douo_wikipedia.ps1
# 道央自動車道のWikipedia記事（すでにローカル保存済）から、全IC/JCT/SA/PA/TBをパースする

$testDir = "c:\Users\user\Documents\PJT\data\test\douo_highway_test"
$wikitext = [System.IO.File]::ReadAllText((Join-Path $testDir "wikipedia_douo_wikitext.txt"), [System.Text.Encoding]::UTF8)

# ICテーブルの抽出
$lines = $wikitext -split '\r?\n'
$inTable = $false
$tableLines = @()

foreach ($line in $lines) {
    if ($line -match '==\s*インターチェンジなど\s*==') {
        $inTable = $true
        continue
    }
    if ($inTable -and $line -match '^==[^=]') {
        $inTable = $false
        break
    }
    if ($inTable) {
        $tableLines += $line
    }
}

Write-Host "Table lines count:" $tableLines.Count

# 各行のパース
# Wikipediaの表形式:
# |- (行区切り)
# | IC番号 || 施設名 || 接続路線名 || 起点からの距離(札幌JCT) || 起点からの距離(七飯IC) || BS || 備考 || 所在地(郡/市) || 所在地(町/区)

$facilities = @()
$currentSection = ""
$current振興局 = ""
$current郡 = ""
$current市町村 = ""

# テーブル内の各施設行を正規表現や構造から解析
# 簡易的に [[]] リンクを含む行から施設を特定
$sapaList = @()
$icList = @()

foreach ($l in $tableLines) {
    # 施設名を含むパターン: [[xxxサービスエリア|yyy]] または [[xxxパーキングエリア|yyy]]
    if ($l -match '\[\[([^\]|]+(?:サービスエリア|パーキングエリア|インターチェンジ|ジャンクション))(\|([^\]]+))?\]\]') {
        $pageTitle = $matches[1]
        $dispName = if ($matches[3]) { $matches[3] } else { $pageTitle }
        
        $kind = if ($pageTitle -match 'サービスエリア') { "SA" }
                elseif ($pageTitle -match 'パーキングエリア') { "PA" }
                elseif ($pageTitle -match 'ジャンクション') { "JCT" }
                elseif ($pageTitle -match 'インターチェンジ') { "IC" }
                else { "その他" }
        
        $sapaList += [PSCustomObject]@{
            page_title = $pageTitle
            disp_name  = $dispName
            kind       = $kind
            raw_line   = $l
        }
    }
}

Write-Host "Found facilities in Wikipedia:" $sapaList.Count
$sapaList | Where-Object { $_.kind -in @("SA", "PA") } | Format-Table -AutoSize
