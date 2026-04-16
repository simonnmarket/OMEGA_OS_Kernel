# executar_omega_tier0_psa.ps1
# Orquestrador de Alta Performance - Auditoria PARR-F

$ErrorActionPreference = "Stop"

$root = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$psa_base = "$root\Auditoria PARR-F"
$cons_base = "$psa_base\Auditoria Conselho"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log_path = "$psa_base\audit_run_$ts.log"

Write-Host "--- OMEGA TIER-0 HIGH PERFORMANCE EXECUTION ---" -ForegroundColor Cyan
Write-Host "[*] Timestamp: $ts"
Write-Host "[*] Log: $log_path"

# 1. Configurar Ambiente de Dados
# Nota: Se FIN_SENSE_DSN não estiver no sistema, o esqueleto v120 usará FIN_SENSE_L1_CSV
$env:FIN_SENSE_L1_CSV = "$cons_base\FIN_SENSE_L1_SAMPLE.csv"
$env:OMEGA_USE_FIN_SENSE_L1 = "1"
$env:OMEGA_MOMENTUM_THRESHOLD = "0.001"
$env:OMEGA_AUDIT_DIR = "$psa_base\00_PROVAS_AUDITORIA\tier0_night_runs"

if (-not $env:FIN_SENSE_DSN) {
    Write-Host "[!] DSN não detectada. Utilizando Fallback CSV: $env:FIN_SENSE_L1_CSV" -ForegroundColor Yellow
} else {
    Write-Host "[+] DSN Detectada: $($env:FIN_SENSE_DSN.Substring(0, 15))..." -ForegroundColor Green
}

# 2. Executar Orquestrador Tier-0 (Gerador de Sinais e Auditoria Imutável)
Write-Host "[*] Iniciando Orquestrador Tier-0 v1.2.0..."
python "$psa_base\omega_orquestador_tier0_v120.py" | Tee-Object -FilePath $log_path

# 3. Executar Shadow Paper Loop (Simulação de Execução Contínua)
Write-Host "[*] Iniciando Shadow Paper Loop..."
python "$psa_base\shadow_paper_loop.py" >> $log_path

Write-Host "[OK] Execucao de Alta Performance Concluida." -ForegroundColor Green
