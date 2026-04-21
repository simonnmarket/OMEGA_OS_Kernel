# =============================================================================
# OMEGA STRESS TEST - RELATÓRIO DE CALIBRAÇÃO
# =============================================================================

Write-Host "============================================================================" -ForegroundColor Red
Write-Host " OMEGA STRESS TEST - RELATÓRIO DE CALIBRAÇÃO" -ForegroundColor Yellow
Write-Host " Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Red

$reportDir = ".\Auditoria PARR-F\reports"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportFile = "$reportDir\stress_test_48h_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# Coletar todos os PaperReports
$paperReports = Get-ChildItem ".\audit\paper\*\PaperReport_*.json" -Recurse | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-50) }

$calibration = @{
    report_generated = (Get-Date -Format 'o')
    total_reports = $paperReports.Count
    ativos_metrics = @{}
    recomendacoes_calibracao = @()
    modulos_performance = @{}
}

foreach ($report in $paperReports) {
    try {
        $contentRaw = Get-Content -Raw $report.FullName
        $data = ConvertFrom-Json $contentRaw
        $asset = $data.asset
        
        if (-not $calibration.ativos_metrics.ContainsKey($asset)) {
            $calibration.ativos_metrics[$asset] = @{
                trades = 0
                hit_rates = @()
                slippages = @()
                latencies = @()
                lot_medio = 0
            }
        }
        
        $metrics = $calibration.ativos_metrics[$asset]
        $metrics.trades++
        $metrics.hit_rates += $data.engines.harmonic.metrics.'134_stats'.hit_rate
        $metrics.slippages += $data.execution.slippage_pts
        $metrics.latencies += $data.execution.latency_ms
        $metrics.lot_medio += $data.lot_info.lot
    } catch {}
}

# Calcular médias e recomendações
foreach ($asset in $calibration.ativos_metrics.Keys) {
    $m = $calibration.ativos_metrics[$asset]
    if ($m.hit_rates.Count -gt 0) { $m.hit_rate_medio = [math]::Round(($m.hit_rates | Measure-Object -Average).Average, 2) } else { $m.hit_rate_medio = 0 }
    if ($m.slippages.Count -gt 0) { $m.slippage_medio = [math]::Round(($m.slippages | Measure-Object -Average).Average, 2) } else { $m.slippage_medio = 0 }
    if ($m.latencies.Count -gt 0) { $m.latencia_media = [math]::Round(($m.latencies | Measure-Object -Average).Average, 1) } else { $m.latencia_media = 0 }
    if ($m.trades -gt 0) { $m.lot_medio = [math]::Round($m.lot_medio / $m.trades, 2) } else { $m.lot_medio = 0 }
    
    # Recomendações de calibração
    if ($m.hit_rate_medio -lt 65) {
        $calibration.recomendacoes_calibracao += "$asset : Hit Rate baixo ($($m.hit_rate_medio)%) - Aumentar confianca_minima ou remover"
    }
    if ($m.slippage_medio -gt 1.0) {
        $calibration.recomendacoes_calibracao += "$asset : Slippage alto ($($m.slippage_medio) pts) - Reduzir lote_maximo ou evitar horários"
    }
    if ($m.latencia_media -gt 100) {
        $calibration.recomendacoes_calibracao += "$asset : Latência alta ($($m.latencia_media) ms) - Verificar conexão MT5"
    }
    if ($m.trades -lt 5) {
        $calibration.recomendacoes_calibracao += "$asset : Poucos trades ($($m.trades)) - Dados insuficientes"
    }
}

$calibration | ConvertTo-Json -Depth 4 | Set-Content $reportFile

# Exibir resumo
Write-Host "`n[RESUMO POR ATIVO]" -ForegroundColor Magenta
foreach ($asset in ($calibration.ativos_metrics.Keys | Sort-Object)) {
    $m = $calibration.ativos_metrics[$asset]
    $color = if ($m.hit_rate_medio -ge 70) { "Green" } elseif ($m.hit_rate_medio -ge 60) { "Yellow" } else { "Red" }
    Write-Host "  $asset : $($m.trades) trades | HR: $($m.hit_rate_medio)% | Slip: $($m.slippage_medio) pts | Lat: $($m.latencia_media)ms" -ForegroundColor $color
}

Write-Host "`n[RECOMENDAÇÕES DE CALIBRAÇÃO]" -ForegroundColor Magenta
foreach ($rec in $calibration.recomendacoes_calibracao) {
    Write-Host "  ⚠️ $rec" -ForegroundColor Yellow
}

Write-Host "`n[RELATÓRIO SALVO]" -ForegroundColor Green
Write-Host "  $reportFile" -ForegroundColor White
