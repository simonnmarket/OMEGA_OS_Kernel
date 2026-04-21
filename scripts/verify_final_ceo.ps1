# =============================================================================
# VERIFICAÇÃO FINAL DO CEO - TOPOLOGIA CORRIGIDA
# Executar após Lift-and-Shift
# =============================================================================

Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " VERIFICAÇÃO FINAL CEO - TOPOLOGIA CORRIGIDA" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan

$evidencias = @()
$falhas = @()

# -----------------------------------------------------------------------------
# MOD #1: Input Validation
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #1] Input Validation" -ForegroundColor Magenta
$path1 = ".\modules\validation\crisis_probability_validator.py"
if (Test-Path $path1) {
    $linhas = Select-String -Path $path1 -Pattern "raise ValueError"
    if ($linhas.Count -ge 4) {
        Write-Host "[OK] $($linhas.Count) validações encontradas" -ForegroundColor Green
        $evidencias += "MOD1"
    } else {
        Write-Host "[FALHA] Apenas $($linhas.Count) validações" -ForegroundColor Red
        $falhas += "MOD1"
    }
} else {
    Write-Host "[FALHA] Arquivo não encontrado: $path1" -ForegroundColor Red
    $falhas += "MOD1"
}

# -----------------------------------------------------------------------------
# MOD #2: GateTiming dict
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #2] GateTiming dict return" -ForegroundColor Magenta
$path2 = ".\modules\validation\gate_timing_validator.py"
if (Test-Path $path2) {
    $linhas = Select-String -Path $path2 -Pattern "samples_per_group"
    if ($linhas) {
        Write-Host "[OK] Dict return encontrado" -ForegroundColor Green
        $evidencias += "MOD2"
    } else {
        Write-Host "[FALHA] Dict return não encontrado" -ForegroundColor Red
        $falhas += "MOD2"
    }
} else {
    Write-Host "[FALHA] Arquivo não encontrado: $path2" -ForegroundColor Red
    $falhas += "MOD2"
}

# -----------------------------------------------------------------------------
# MOD #3: Transport Delay
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #3] Transport Delay" -ForegroundColor Magenta
$path3 = ".\modules\validation\slo_validator_china.py"
if (Test-Path $path3) {
    $linhas = Select-String -Path $path3 -Pattern "transport_delay"
    if ($linhas) {
        Write-Host "[OK] Transport delay encontrado" -ForegroundColor Green
        $evidencias += "MOD3"
    } else {
        Write-Host "[FALHA] Transport delay não encontrado" -ForegroundColor Red
        $falhas += "MOD3"
    }
} else {
    Write-Host "[FALHA] Arquivo não encontrado: $path3" -ForegroundColor Red
    $falhas += "MOD3"
}

# -----------------------------------------------------------------------------
# MOD #4: Documentação de By-Pass
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #4] Documentação de By-Pass" -ForegroundColor Magenta
$path4 = ".\Auditoria PARR-F\README_AUDIT.md"
if (Test-Path $path4) {
    $conteudo = Get-Content $path4 -Raw
    if ($conteudo -match "Paradoxo de Quine" -and $conteudo -match "by-pass") {
        Write-Host "[OK] Documentação de by-pass encontrada" -ForegroundColor Green
        $evidencias += "MOD4"
    } else {
        Write-Host "[FALHA] Documentação incompleta" -ForegroundColor Red
        $falhas += "MOD4"
    }
} else {
    Write-Host "[FALHA] README_AUDIT.md não encontrado" -ForegroundColor Red
    $falhas += "MOD4"
}

# -----------------------------------------------------------------------------
# MOD #5: Thread-Safety (shadow_loop.py)
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #5] Thread-Safety" -ForegroundColor Magenta
$path5 = ".\core_engines\shadow_loop.py"
if (Test-Path $path5) {
    $linhas = Select-String -Path $path5 -Pattern "threading\.local"
    if ($linhas) {
        Write-Host "[OK] threading.local() encontrado em $path5" -ForegroundColor Green
        $evidencias += "MOD5"
    } else {
        Write-Host "[FALHA] threading.local() não encontrado" -ForegroundColor Red
        $falhas += "MOD5"
    }
} else {
    Write-Host "[FALHA] Arquivo não encontrado: $path5" -ForegroundColor Red
    $falhas += "MOD5"
}

# -----------------------------------------------------------------------------
# MOD #6: SLO Dinâmico
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #6] SLO Dinâmico" -ForegroundColor Magenta
$path6 = ".\scripts\run_hunter_regime.ps1"
if (Test-Path $path6) {
    $linhas = Select-String -Path $path6 -Pattern '\$config\.slo\.'
    if ($linhas) {
        Write-Host "[OK] SLO lido do JSON" -ForegroundColor Green
        $evidencias += "MOD6"
    } else {
        Write-Host "[FALHA] SLO não lido do JSON" -ForegroundColor Red
        $falhas += "MOD6"
    }
} else {
    Write-Host "[FALHA] Arquivo não encontrado: $path6" -ForegroundColor Red
    $falhas += "MOD6"
}

# -----------------------------------------------------------------------------
# MOD #7: Precisão do Log
# -----------------------------------------------------------------------------
Write-Host "`n[MOD #7] Precisão do Log" -ForegroundColor Magenta
$path7 = ".\scripts\validate_hunter_mission.ps1"
if (Test-Path $path7) {
    $linhas = Select-String -Path $path7 -Pattern "Select-String.*precision"
    if ($linhas) {
        Write-Host "[OK] Precisão extraída do log" -ForegroundColor Green
        $evidencias += "MOD7"
    } else {
        Write-Host "[FALHA] Precisão não extraída do log" -ForegroundColor Red
        $falhas += "MOD7"
    }
} else {
    Write-Host "[FALHA] Arquivo não encontrado: $path7" -ForegroundColor Red
    $falhas += "MOD7"
}

# -----------------------------------------------------------------------------
# VERIFICAÇÃO DE TOPOLOGIA
# -----------------------------------------------------------------------------
Write-Host "`n[TOPOLOGIA] Verificação da nova estrutura" -ForegroundColor Magenta
$topologia_ok = $true
$paths_verificar = @(
    ".\config\regimes\hunter.json",
    ".\modules\validation\__init__.py",
    ".\core_engines\shadow_loop.py",
    ".\scripts\run_hunter_regime.ps1",
    ".\Auditoria PARR-F\logs\hunter"
)

foreach ($p in $paths_verificar) {
    if (Test-Path $p) {
        Write-Host "[OK] $p" -ForegroundColor Green
    } else {
        Write-Host "[FALHA] $p" -ForegroundColor Red
        $topologia_ok = $false
    }
}

if ($topologia_ok) {
    $evidencias += "TOPOLOGIA"
} else {
    $falhas += "TOPOLOGIA"
}

# -----------------------------------------------------------------------------
# RESUMO FINAL
# -----------------------------------------------------------------------------
Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host " RESUMO FINAL DA VERIFICAÇÃO" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan

$total_ok = $evidencias.Count
$total_falhas = $falhas.Count

Write-Host "`nModificações aprovadas ($total_ok):" -ForegroundColor Green
foreach ($e in $evidencias) { Write-Host "  ✅ $e" -ForegroundColor Green }

if ($total_falhas -gt 0) {
    Write-Host "`nModificações pendentes ($total_falhas):" -ForegroundColor Red
    foreach ($f in $falhas) { Write-Host "  ❌ $f" -ForegroundColor Red }
}

Write-Host "`n============================================================================" -ForegroundColor Cyan

if ($total_ok -ge 8 -and $topologia_ok) {
    Write-Host " ✅ VERIFICAÇÃO COMPLETA - TODAS AS CONDIÇÕES ATENDIDAS" -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "DECISÃO DO CEO:" -ForegroundColor Yellow
    Write-Host " Medidas cautelares SUSPENSAS." -ForegroundColor White
    Write-Host " Paper tracking AUTORIZADO." -ForegroundColor White
    Write-Host ""
    Write-Host "COMANDO DE EXECUÇÃO:" -ForegroundColor Yellow
    Write-Host " .\scripts\run_hunter_regime.ps1 -Mode paper" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host " ❌ VERIFICAÇÃO INCOMPLETA - CORRIJA AS FALHAS ACIMA" -ForegroundColor Red
    Write-Host "============================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host " Medidas cautelares MANTIDAS até correção." -ForegroundColor Red
    Write-Host ""
}
