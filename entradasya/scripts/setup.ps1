<#
  EntradasYa v1 - Preparacion en Windows
    1) Crea el .env de cada servicio (contrasenas y secretos aleatorios)
    2) Crea las bases de datos y usuarios en PostgreSQL (con psql)
    3) Crea el entorno virtual de cada servicio e instala sus dependencias

  Uso (desde la carpeta entradasya):
    powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

  Opciones:
    -Psql   "C:\Program Files\PostgreSQL\18\bin\psql.exe"
    -Python python   (o py)
    -PgUser postgres
#>
param(
    [string]$Psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe",
    [string]$Python = "",
    [string]$PgUser = "postgres",
    [string]$PgHost = "localhost",
    [int]$PgPort = 5432
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Servicios = @("web", "auth", "events", "orders", "payments", "tickets", "notifications", "checkin")
$ConBD = @("auth", "events", "orders", "payments", "tickets", "checkin")
$Utf8SinBom = New-Object System.Text.UTF8Encoding($false)

function Nueva-Clave([int]$n) {
    $chars = [char[]]"abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    $bytes = New-Object byte[] $n
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return -join ($bytes | ForEach-Object { $chars[$_ % $chars.Length] })
}

function Leer-Env([string]$archivo, [string]$clave) {
    if (-not (Test-Path $archivo)) { return "" }
    foreach ($linea in Get-Content $archivo) {
        if ($linea -match "^$clave=(.*)$") { return $Matches[1].Trim() }
    }
    return ""
}

function Probar-Python([string]$cmd) {
    try {
        $ok = & $cmd -c "import sys; print(sys.version_info >= (3, 11))" 2>$null
        return ($LASTEXITCODE -eq 0 -and "$ok".Trim() -eq "True")
    } catch { return $false }
}

# ---------- Requisitos ----------
Write-Host "== Revisando requisitos ==" -ForegroundColor Cyan
if (-not $Python) {
    if (Probar-Python "python") { $Python = "python" }
    elseif (Probar-Python "py") { $Python = "py" }
    else { throw "No se encontro Python 3.11 o superior. Instalelo desde python.org (marque 'Add python.exe to PATH')." }
} elseif (-not (Probar-Python $Python)) {
    throw "El comando '$Python' no es Python 3.11 o superior."
}
Write-Host "   Python: $(& $Python --version)"

if (-not (Test-Path $Psql)) {
    $c = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\psql.exe" -ErrorAction SilentlyContinue |
         Sort-Object FullName -Descending | Select-Object -First 1
    if ($c) { $Psql = $c.FullName } else { throw "No se encontro psql.exe. Indique la ruta con -Psql 'C:\...\psql.exe'" }
}
Write-Host "   psql:   $Psql"

# ---------- 1/3 Archivos .env ----------
Write-Host "== 1/3 Archivos .env ==" -ForegroundColor Cyan
$jwt = Leer-Env "$Root\services\auth\.env" "JWT_SECRET"
if (-not $jwt -or $jwt -eq "cambiar_secreto_jwt") { $jwt = Nueva-Clave 48 }
$key = Leer-Env "$Root\services\orders\.env" "INTERNAL_API_KEY"
if (-not $key -or $key -eq "cambiar_clave_interna") { $key = Nueva-Clave 32 }

$pass = @{}
foreach ($s in $ConBD) {
    $p = Leer-Env "$Root\services\$s\.env" "DB_PASSWORD"
    if (-not $p -or $p -eq "cambiar_password") { $p = Nueva-Clave 20 }
    $pass[$s] = $p
}

function Completar([string]$texto, [string]$servicio) {
    $p = ""
    if ($pass.ContainsKey($servicio)) { $p = $pass[$servicio] }
    return $texto.Replace("cambiar_password", $p).Replace("cambiar_secreto_jwt", $jwt).Replace("cambiar_clave_interna", $key)
}

foreach ($s in $Servicios) {
    $envf = "$Root\services\$s\.env"
    $ejemplo = "$Root\services\$s\.env.example"
    if (-not (Test-Path $envf)) {
        $txt = Completar ([System.IO.File]::ReadAllText($ejemplo)) $s
        [System.IO.File]::WriteAllText($envf, $txt, $Utf8SinBom)
        Write-Host "   $s\.env creado"
        continue
    }
    # Ya existe: se conserva y solo se agregan las variables nuevas que falten
    $actual = [System.IO.File]::ReadAllText($envf)
    $nuevas = @()
    foreach ($linea in [System.IO.File]::ReadAllLines($ejemplo)) {
        if ($linea -match '^\s*$' -or $linea.StartsWith("#")) { continue }
        $clave = $linea.Split("=")[0]
        if ($actual -notmatch "(?m)^$([regex]::Escape($clave))=") { $nuevas += (Completar $linea $s) }
    }
    if ($nuevas.Count -gt 0) {
        $agregar = "`n# Variables agregadas por setup.ps1`n" + ($nuevas -join "`n") + "`n"
        [System.IO.File]::AppendAllText($envf, $agregar, $Utf8SinBom)
    }
    Write-Host "   $s\.env ya existe (se conserva, $($nuevas.Count) variables nuevas)"
}

# ---------- 2/3 Bases de datos ----------
Write-Host "== 2/3 Bases de datos ==" -ForegroundColor Cyan
$seguro = Read-Host "Contrasena del usuario '$PgUser' de PostgreSQL (la misma de pgAdmin)" -AsSecureString
$env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro))
$sql = Join-Path $Root "infra\postgres\01_crear_bases.sql"
& $Psql -h $PgHost -p $PgPort -U $PgUser -d postgres -q `
    -v "auth_pass=$($pass['auth'])" -v "events_pass=$($pass['events'])" -v "orders_pass=$($pass['orders'])" `
    -v "payments_pass=$($pass['payments'])" -v "tickets_pass=$($pass['tickets'])" `
    -v "checkin_pass=$($pass['checkin'])" -f $sql
$codigo = $LASTEXITCODE
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
if ($codigo -ne 0) { throw "No se pudieron crear las bases de datos. Revise la contrasena de '$PgUser' y que PostgreSQL este encendido." }
Write-Host "   Bases y usuarios listos"

# ---------- 3/3 Entornos virtuales ----------
Write-Host "== 3/3 Entornos virtuales y dependencias (puede tardar unos minutos) ==" -ForegroundColor Cyan
foreach ($s in $Servicios) {
    $dir = "$Root\services\$s"
    if (-not (Test-Path "$dir\.venv\Scripts\python.exe")) {
        & $Python -m venv "$dir\.venv"
        if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual de $s" }
    }
    & "$dir\.venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r "$dir\requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw "Fallo la instalacion de dependencias de $s" }
    Write-Host "   $s listo"
}

Write-Host ""
Write-Host "Preparacion terminada." -ForegroundColor Green
Write-Host "Inicie todo con:  powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1"
