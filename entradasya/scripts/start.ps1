<#
  EntradasYa v1 - Inicia todo en Windows
    - Mailpit (correo de prueba)
    - Los 8 servicios, cada uno en su propia ventana (ahi se ven sus logs)
    - Nginx, la unica puerta de entrada: http://localhost:8080

  Uso (desde la carpeta entradasya):
    powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
  Opciones:
    -NginxDir "C:\nginx"   -Mailpit "C:\mailpit\mailpit.exe"
#>
param(
    [string]$NginxDir = "C:\nginx",
    [string]$Mailpit = "C:\mailpit\mailpit.exe"
)

$Root = Split-Path -Parent $PSScriptRoot
$Orden = @("auth", "events", "payments", "tickets", "notifications", "orders", "checkin", "web")
$Puertos = [ordered]@{ web = 8000; auth = 8001; events = 8002; orders = 8003; payments = 8004; tickets = 8005; notifications = 8006; checkin = 8007 }

# ---------- Mailpit ----------
if (Test-Path $Mailpit) {
    if (-not (Get-Process -Name mailpit -ErrorAction SilentlyContinue)) {
        Start-Process -FilePath $Mailpit -WindowStyle Minimized
    }
    Write-Host "Mailpit iniciado: http://localhost:8025" -ForegroundColor Green
} else {
    Write-Warning "No se encontro Mailpit en $Mailpit. La compra funciona igual, pero el correo no se enviara."
}

# ---------- Servicios ----------
foreach ($s in $Orden) {
    $dirReal = Join-Path $Root "services\$s"
    $dir = $dirReal.Replace("'", "''")
    if (-not (Test-Path "$dirReal\.venv\Scripts\python.exe")) {
        Write-Warning "$s no tiene entorno virtual. Ejecute primero scripts\setup.ps1"
        continue
    }
    $cmd = "`$Host.UI.RawUI.WindowTitle = 'EntradasYa - $s'; Set-Location -LiteralPath '$dir'; & '.\.venv\Scripts\python.exe' -m app.main"
    $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
    Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-EncodedCommand", $enc -WindowStyle Minimized
    Write-Host "Iniciando $s..."
}

# ---------- Chequeos de salud ----------
Write-Host ""
Write-Host "Esperando a que los servicios respondan..."
foreach ($s in $Puertos.Keys) {
    $estado = "sin respuesta"
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$($Puertos[$s])/health" -TimeoutSec 2
            $estado = "OK ($($r.StatusCode))"; break
        } catch {
            if ($_.Exception.Response) { $estado = "ERROR ($([int]$_.Exception.Response.StatusCode))"; break }
            Start-Sleep -Milliseconds 750
        }
    }
    $color = if ($estado -like "OK*") { "Green" } else { "Yellow" }
    Write-Host ("  {0,-14} {1,-6} {2}" -f $s, $Puertos[$s], $estado) -ForegroundColor $color
}

# ---------- Nginx ----------
$nginxExe = Join-Path $NginxDir "nginx.exe"
if (Test-Path $nginxExe) {
    Get-Process -Name nginx -ErrorAction SilentlyContinue | Stop-Process -Force
    $conf = (Join-Path $Root "infra\nginx\nginx.local.conf") -replace '\\', '/'
    $prefix = (($NginxDir -replace '\\', '/').TrimEnd('/')) + '/'
    Start-Process -FilePath $nginxExe -ArgumentList "-p `"$prefix`" -c `"$conf`"" -WorkingDirectory $NginxDir -WindowStyle Hidden
    Start-Sleep -Seconds 1
    if (Get-Process -Name nginx -ErrorAction SilentlyContinue) {
        Write-Host ""
        Write-Host "Listo. Abra http://localhost:8080" -ForegroundColor Green
    } else {
        Write-Warning "Nginx no arranco. Revise $NginxDir\logs\error.log"
    }
} else {
    Write-Warning "No se encontro Nginx en $nginxExe. Sin Nginx la web no puede llegar a los servicios."
}
Write-Host "Correos de prueba (Mailpit): http://localhost:8025"
Write-Host "Para detener todo: powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1"
