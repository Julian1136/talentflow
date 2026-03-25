# Sube la rama main al remoto origin (crea origin si no existe).
# Uso (PowerShell):
#   .\scripts\git_push_origin.ps1 -OriginUrl "https://github.com/USUARIO/talentflow.git"
param(
    [Parameter(Mandatory = $true)]
    [string]$OriginUrl
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
if (-not (Test-Path ".git")) {
    Write-Error "No hay repositorio Git en $(Get-Location)"
}

$remotes = git remote
if ($remotes -contains "origin") {
    git remote set-url origin $OriginUrl
    Write-Host "Remoto 'origin' actualizado."
} else {
    git remote add origin $OriginUrl
    Write-Host "Remoto 'origin' anadido."
}

git branch -M main
git push -u origin main
Write-Host "Push completado."
