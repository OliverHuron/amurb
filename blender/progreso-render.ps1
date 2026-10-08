# Muestra en vivo el avance del render del recorrido: frames hechos / total, porcentaje y tiempo restante.
# Uso: powershell -NoExit -File blender\progreso-render.ps1   (Ctrl+C para salir; el render sigue aunque cierres esto)
#      Subframes:  powershell -NoExit -File blender\progreso-render.ps1 -Total 137 -Carpeta recorrido-sub -Log subframes.log
param(
    [int]$Total = 540,
    [int]$Intervalo = 5,
    [string]$Carpeta = 'recorrido',
    [string]$Log = 'recorrido.log'
)

$raiz = Split-Path -Parent $PSScriptRoot
$carpeta = Join-Path $raiz "blender\render\$Carpeta"
$log = Join-Path $raiz "blender\render\$Log"
$Host.UI.RawUI.WindowTitle = 'Render recorrido AmUrb'

while ($true) {
    $hechos = (Get-ChildItem $carpeta -Filter 'frame_*.png' -ErrorAction SilentlyContinue).Count
    $pct = [math]::Round(100 * $hechos / $Total, 1)

    # promedio de los últimos 20 frames según el log ("frame N/540 en 13.3s")
    $tiempos = Get-Content $log -Tail 20 -ErrorAction SilentlyContinue |
        ForEach-Object { if ($_ -match 'en ([\d.]+)s') { [double]$Matches[1] } }
    $promedio = if ($tiempos) { ($tiempos | Measure-Object -Average).Average } else { 13 }
    $restante = [timespan]::FromSeconds(($Total - $hechos) * $promedio)

    $estado = '{0}/{1} frames ({2}%) · {3:N1} s/frame · faltan ~{4}h {5:D2}m' -f $hechos, $Total, $pct, $promedio, [int]$restante.TotalHours, $restante.Minutes
    Write-Progress -Activity 'Render del recorrido AmUrb' -Status $estado -PercentComplete ([math]::Min(100, $pct))
    Write-Host ("`r[{0}] {1}   " -f (Get-Date -Format 'HH:mm:ss'), $estado) -NoNewline

    if ($hechos -ge $Total) {
        Write-Host "`n¡Render completo! $hechos/$Total frames." -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds $Intervalo
}
