#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Restablece la contrasena del usuario postgres en PostgreSQL (Windows).

.DESCRIPTION
  1) Aplica autenticacion trust solo en localhost (pg_hba.conf).
  2) Reinicia el servicio.
  3) Ejecuta ALTER USER postgres.
  4) Restaura pg_hba.conf desde el respaldo con scram-sha-256.
  5) Reinicia de nuevo.

  Debes ejecutar este script en PowerShell "Ejecutar como administrador".

.PARAMETER NewPassword
  Nueva contrasena. Si no la pasas, se pedira de forma oculta.

.PARAMETER ServiceName
  Nombre del servicio Windows de PostgreSQL (por defecto postgresql-x64-18).

.PARAMETER PgRoot
  Carpeta de instalacion (por defecto C:\Program Files\PostgreSQL\18).
#>
param(
    [Parameter(Mandatory = $false)]
    [string]$NewPassword,
    [string]$ServiceName = "postgresql-x64-18",
    [string]$PgRoot = "C:\Program Files\PostgreSQL\18"
)

$ErrorActionPreference = "Stop"

$dataDir = Join-Path $PgRoot "data"
$hbaPath = Join-Path $dataDir "pg_hba.conf"
$hbaBackup = Join-Path $dataDir "pg_hba.conf.bak_talentflow"
$psql = Join-Path $PgRoot "bin\psql.exe"

if (-not (Test-Path $psql)) {
    Write-Error "No se encontro psql en $psql. Ajusta -PgRoot (ej. ...\PostgreSQL\16)."
}

if (-not (Test-Path $hbaBackup)) {
    Copy-Item $hbaPath $hbaBackup -Force
    Write-Host "Creado respaldo: $hbaBackup"
}

if (-not $NewPassword) {
    $secure = Read-Host "Nueva contrasena para usuario postgres" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $NewPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

if ([string]::IsNullOrWhiteSpace($NewPassword)) {
    Write-Error "La contrasena no puede estar vacia."
}

$content = Get-Content $hbaPath -Raw
$trustContent = $content -replace '(?m)^(local\s+all\s+all\s+)scram-sha-256$', '${1}trust' `
    -replace '(?m)^(host\s+all\s+all\s+127\.0\.0\.1/32\s+)scram-sha-256$', '${1}trust' `
    -replace '(?m)^(host\s+all\s+all\s+::1/128\s+)scram-sha-256$', '${1}trust' `
    -replace '(?m)^(local\s+replication\s+all\s+)scram-sha-256$', '${1}trust' `
    -replace '(?m)^(host\s+replication\s+all\s+127\.0\.0\.1/32\s+)scram-sha-256$', '${1}trust' `
    -replace '(?m)^(host\s+replication\s+all\s+::1/128\s+)scram-sha-256$', '${1}trust'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($hbaPath, $trustContent, $utf8NoBom)

Write-Host "Reiniciando servicio $ServiceName..."
Restart-Service $ServiceName -Force
Start-Sleep -Seconds 4

$sqlPassword = $NewPassword -replace "'", "''"
$sql = "ALTER USER postgres WITH PASSWORD '$sqlPassword';"
& $psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c $sql

Write-Host "Restaurando pg_hba.conf seguro (scram-sha-256)..."
Copy-Item $hbaBackup $hbaPath -Force

Write-Host "Reiniciando servicio otra vez..."
Restart-Service $ServiceName -Force
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Listo. Anade en tu .env del proyecto:"
Write-Host "  DB_ADMIN_PASSWORD=<la misma contrasena que acabas de definir>"
Write-Host "Luego ejecuta: .\.venv\Scripts\python.exe setup_db.py"
