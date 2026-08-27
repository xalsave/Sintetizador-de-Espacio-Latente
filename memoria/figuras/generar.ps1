# Regenera las figuras de la memoria.
#
#   .\generar.ps1            -> regenera todas
#   .\generar.ps1 adsr       -> regenera solo fig_adsr.py
#   .\generar.ps1 adsr filtros
#
# Necesita matplotlib y numpy, ya instalados en el Python del PATH.

param([string[]]$Figuras)

Set-Location $PSScriptRoot

if ($Figuras) {
    $scripts = $Figuras | ForEach-Object { "fig_$_.py" }
} else {
    $scripts = Get-ChildItem -Filter "fig_*.py" | Select-Object -ExpandProperty Name
}

foreach ($s in $scripts) {
    if (-not (Test-Path $s)) {
        Write-Host "no existe: $s" -ForegroundColor Yellow
        continue
    }
    & python $s
}
