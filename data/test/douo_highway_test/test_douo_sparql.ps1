# test_douo_sparql.ps1
$sparqlQuery = @"
SELECT ?item ?itemLabel ?type ?typeLabel ?coord ?inception ?operatorLabel WHERE {
  ?item wdt:P361 wd:Q867982 .
  OPTIONAL { ?item wdt:P31 ?type . }
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P571 ?inception . }
  OPTIONAL { ?item wdt:P137 ?operator . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ja,en". }
}
ORDER BY ?itemLabel
"@

$sparqlUri = "https://query.wikidata.org/sparql?query=" + [System.Uri]::EscapeDataString($sparqlQuery)
$sparqlHeaders = @{
    "User-Agent" = "AntigravityHokkaidoPilot/1.0"
    "Accept"     = "application/sparql-results+json"
}

try {
    $wdRes = Invoke-RestMethod -Uri $sparqlUri -Headers $sparqlHeaders -Method Get
    Write-Host "Success! Count:" $wdRes.results.bindings.Count
    $wdRes.results.bindings | ForEach-Object {
        [PSCustomObject]@{
            itemLabel    = $_.itemLabel.value
            typeLabel    = $_.typeLabel.value
            coord        = $_.coord.value
            inception    = $_.inception.value
            operator     = $_.operatorLabel.value
            qid          = ($_.item.value -replace '^.*/', '')
        }
    } | Format-Table -AutoSize
} catch {
    Write-Host "Failed: $_"
}
