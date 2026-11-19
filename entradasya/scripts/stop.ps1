<#
  EntradasYa v1 - Detiene todo en Windows (servicios, Nginx y Mailpit)
  Uso: powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1
#>

# Servicios: procesos de Python que ejecutan "app.main" y la ventana que los abrio
$procesos = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*-m app.main*" }
$ventanas = @()
foreach ($p in $procesos) {
    $padre = Get-CimInstance Win32_Process -Filter "ProcessId = $($p.ParentProcessId)" -ErrorAction SilentlyContinue
    if ($padre -and $padre.Name -eq "python.exe") {
        $padre = Get-CimInstance Win32_Process -Filter "ProcessId = $($padre.ParentProcessId)" -ErrorAction SilentlyContinue
    }
    if ($padre -and $padre.Name -eq "powershell.exe") { $ventanas += $padre.ProcessId }
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
foreach ($id in ($ventanas | Select-Object -Unique)) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
Write-Host "Servicios detenidos: $(@($procesos).Count) procesos"

Get-Process -Name nginx -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Nginx detenido"
Get-Process -Name mailpit -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Mailpit detenido"
