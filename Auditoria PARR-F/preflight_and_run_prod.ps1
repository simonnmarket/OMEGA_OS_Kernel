param(
  [string]$Dsn = $env:FIN_SENSE_DSN,
  [int]$StartHour = 9,
  [int]$EndHour = 17,
  [string]$Mode = "paper"  # "paper" ou "live" (live requer autorização)
)

function Fail($msg){ Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }
function Ok($msg){ Write-Host "✅ $msg" -ForegroundColor Green }
function Warn($msg){ Write-Host "⚠️ $msg" -ForegroundColor Yellow }

# 1) Janela
$hour = (Get-Date).Hour
if ($hour -lt $StartHour -or $hour -ge $EndHour) { Fail "Fora da janela ($StartHour-$EndHour). Atual: $hour" }
Ok "Dentro da janela ($StartHour-$EndHour)."

# 2) Autorização para live
if ($Mode -ieq "live") {
  if ($env:OMEGA_PROD_AUTHORIZATION -ne "CONSELHO_GO_2026") { Fail "Modo live requer OMEGA_PROD_AUTHORIZATION=CONSELHO_GO_2026" }
  $confirm = Read-Host "⚠️ Confirmar modo LIVE? (yes/no)"
  if ($confirm.ToLower() -ne "yes") { Fail "Live abortado por falta de confirmação" }
}

# 3) DSN / porta
if (-not $Dsn -or [string]::IsNullOrWhiteSpace($Dsn)) { Fail "FIN_SENSE_DSN não configurada." }
$host = ([Uri]$Dsn).Host
$port = ([Uri]$Dsn).Port
if (-not (Test-NetConnection -ComputerName $host -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded) {
  Fail "Porta $port inacessível em $host."
}
Ok "Porta $port acessível em $host."

# 4) DSN query (timeout)
$pyCheck = @"
import psycopg2, os, time, sys
dsn = os.environ.get('FIN_SENSE_DSN')
if not dsn:
    print('NO_DSN'); sys.exit(1)
t0 = time.time()
try:
    conn = psycopg2.connect(dsn, connect_timeout=5)
    cur = conn.cursor(); cur.execute('SELECT 1'); cur.fetchone()
    lat = (time.time()-t0)*1000
    conn.close()
    print(f'OK_DSN {lat:.2f}')
except Exception as e:
    print(f'FAIL_DSN {e}')
    sys.exit(1)
"@
$pyOut = $pyCheck | python -
if ($LASTEXITCODE -ne 0 -or $pyOut -like "*FAIL_DSN*") { Fail "DSN query falhou: $pyOut" }
if ($pyOut -match "OK_DSN\s+([\d\.]+)") {
  $lat = [double]$matches[1]
  if ($lat -gt 50) { Warn "Latência DSN acima de 50ms: $lat ms" } else { Ok "DSN OK | lat_ms=$lat" }
}

# 5) Freshness do seed (arquivo CSV)
$csv = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Auditoria Conselho\FIN_SENSE_L1_SAMPLE.csv"
if (-not (Test-Path $csv)) { Fail "CSV não encontrado: $csv" }
$ageHours = ((Get-Date) - (Get-Item $csv).LastWriteTime).TotalHours
if ($ageHours -gt 4) { Fail "CSV stale: $([math]::Round($ageHours,2))h > 4h" }
Ok "CSV frescor OK: $([math]::Round($ageHours,2))h"

# 6) MT5 RTT e volume_min
$pyMT5 = @"
import MetaTrader5 as mt5, time, sys
if not mt5.initialize():
    print(f'MT5_FAIL {mt5.last_error()}'); sys.exit(1)
t0 = time.perf_counter()
pos = mt5.positions_get(symbol='XAUUSD')
rtt = (time.perf_counter() - t0)*1000
info = mt5.symbol_info('XAUUSD')
vmin = info.volume_min if info else None
mt5.shutdown()
print(f'MT5_OK rtt_ms={rtt:.2f} volume_min={vmin}')
"@
$mt5Out = $pyMT5 | python -
if ($LASTEXITCODE -ne 0 -or $mt5Out -like "*MT5_FAIL*") { Fail "MT5 ping falhou: $mt5Out" }
if ($mt5Out -match "rtt_ms=([\d\.]+).*volume_min=([\d\.]+)") {
  $rtt = [double]$matches[1]; $vmin = [double]$matches[2]
  if ($rtt -gt 100) { Warn "RTT MT5 alto: $rtt ms" } else { Ok "MT5 RTT OK: $rtt ms" }
  if ($vmin -gt 0.01) { Warn "volume_min=$vmin > 0.01; ajustar lote se live" } else { Ok "volume_min OK: $vmin" }
}

# 7) Executar orquestrador + shadow_loop
Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
$env:FIN_SENSE_DSN = $Dsn
$env:NEBULAR_KUIPER_ROOT = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:PSA_AUDIT_BASE = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
Ok "Executando orquestrador ($Mode)..."
.\executar_omega_tier0_psa.ps1

Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
Ok "Executando shadow_loop ($Mode)..."
python core_engines\shadow_loop.py --mode $Mode `
  --ativos XAUUSD `
  --timeframes H1 H4 `
  --equity 10000

Ok "Fluxo concluído. Coletar artefatos em Auditoria Conselho."
