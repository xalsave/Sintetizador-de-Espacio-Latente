# Compila main.tex con la cadena completa: xelatex -> biber -> glosario -> xelatex x2.
# Uso: desde PowerShell, dentro de "memoria/plantilla latex/", ejecutar: .\build.ps1

$ErrorActionPreference = "Continue"

$xelatex = (Get-Command xelatex -ErrorAction SilentlyContinue).Source
if (-not $xelatex) {
    $xelatex = "C:\Users\alsav_9f696wk\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"
}
$bin = Split-Path $xelatex

Write-Host "== xelatex (1/3) ==" -ForegroundColor Cyan
& $xelatex -interaction=nonstopmode main.tex | Out-Null

Write-Host "== biber ==" -ForegroundColor Cyan
& "$bin\biber.exe" main | Out-Null

Write-Host "== glosario (siglas) ==" -ForegroundColor Cyan
& "$bin\makeglossaries-lite.exe" main | Out-Null

Write-Host "== xelatex (2/3) ==" -ForegroundColor Cyan
& $xelatex -interaction=nonstopmode main.tex | Out-Null

Write-Host "== xelatex (3/3) ==" -ForegroundColor Cyan
& $xelatex -interaction=nonstopmode main.tex | Out-Null

Write-Host ""
$errores = Select-String -Path main.log -Pattern "^!" -ErrorAction SilentlyContinue
if ($errores) {
    Write-Host "ERRORES DE LATEX:" -ForegroundColor Red
    $errores | ForEach-Object { Write-Host $_.Line -ForegroundColor Red }
} else {
    $undef = Select-String -Path main.log -Pattern "Citation .* undefined|Reference .* undefined" -ErrorAction SilentlyContinue
    if ($undef) {
        Write-Host "AVISO - referencias sin resolver:" -ForegroundColor Yellow
        $undef | ForEach-Object { Write-Host $_.Line -ForegroundColor Yellow }
    }
    $paginas = (Select-String -Path main.log -Pattern "Output written on main\.pdf \((\d+) pages" -ErrorAction SilentlyContinue).Matches.Groups[1].Value
    Write-Host "Listo: main.pdf ($paginas paginas)" -ForegroundColor Green
}
