param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path)
$ErrorActionPreference = 'Stop'
$reportPath = Join-Path $Root 'docs/report/bao_cao_tong_hop.docx'
$pdfPath = Join-Path $Root 'docs/report/bao_cao_tong_hop.pdf'
if (-not (Test-Path -LiteralPath $reportPath)) { throw 'Build the report first.' }
# Open only this generated file. Never attach to or close the user Word session.
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null
try {
    $document = $word.Documents.Open($reportPath, $false, $false)
    $document.RemovePersonalInformation = $true
    [void]$document.Fields.Update()
    $document.Repaginate()
    foreach ($toc in $document.TablesOfContents) { $toc.Update() }
    [void]$document.Fields.Update()
    $document.Repaginate()
    foreach ($toc in $document.TablesOfContents) { $toc.UpdatePageNumbers() }
    $document.Save()
    $document.ExportAsFixedFormat($pdfPath, 17)
    @{ pages = $document.ComputeStatistics(2); toc_fields = $document.TablesOfContents.Count; renderer = 'Microsoft Word native COM'; pdf = $pdfPath } | ConvertTo-Json
} finally {
    if ($null -ne $document) { $document.Close(0) }
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
}
