param(
  [string]$Dsn = $env:FIN_SENSE_DSN,
  [int]$StartHour = 9,
  [int]$EndHour = 17,
  [string]$Mode = "paper"
)

function Fail($msg){ Write-Host "[-NOGO-] $msg" -ForegroundColor Red; exit 1 }
function Ok($msg){ Write-Host "[+GO+] $msg" -ForegroundColor Green }
function Warn($msg){ Write-Host "[!WARN!] $msg" -ForegroundColor Yellow }

# 0) Bloqueio Atômico de Mutex Excludente (Windows Global Lock)
$mtx = New-Object System.Threading.Mutex($false, "Global\OMEGA_TIER0_MUTEX_$env:USERNAME")
if (-not $mtx.WaitOne(0, $false)) {
  Fail "NOGO ATOMICO: Outra instancia do pipeline em execucao."
}
Ok "Mutex Lock Adquirido. Pipeline Atomico Exclusivo."

# 1) Janela
$hour = (Get-Date).Hour
if ($hour -lt $StartHour -or $hour -ge $EndHour) { Fail "Fora da janela ($StartHour-$EndHour)." }
Ok "Dentro da janela."

# 2) Live Autorizacao
if ($Mode -ieq "live") {
  if ($env:OMEGA_PROD_AUTHORIZATION -ne "CONSELHO_GO_2026") { Fail "Requer autorizacao." }
}

if ([string]::IsNullOrWhiteSpace($Dsn)) { 
  if (-not [string]::IsNullOrWhiteSpace($env:FIN_SENSE_DSN)) { $Dsn=$env:FIN_SENSE_DSN } 
  else { Fail "FIN_SENSE_DSN nao configurada." } 
}

# 4) DSN query bypass powershell string parser issues natively
$pyCheck = @"
import psycopg2, os, time, sys
dsn = os.environ.get('FIN_SENSE_DSN') if os.environ.get('FIN_SENSE_DSN') else '$Dsn'
if not dsn:
    print('NO_DSN')
    sys.exit(1)
t0 = time.time()
try:
    conn = psycopg2.connect(dsn, connect_timeout=5)
    cur = conn.cursor()
    cur.execute('SELECT 1')
    cur.fetchone()
    lat = (time.time()-t0)*1000
    conn.close()
    print('OK_DSN ' + str(lat))
except Exception as e:
    print('FAIL_DSN ' + str(e))
    sys.exit(1)
"@

$pyOut = $pyCheck | python -
if ($LASTEXITCODE -ne 0 -or $pyOut -match 'FAIL_DSN') { Fail "DSN query falhou: $pyOut" }
if ($pyOut -match 'OK_DSN\s+([\d\.]+)') {
  $lat = [double]$matches[1]
  if ($lat -gt 50) { Warn "Latencia DSN acima de 50ms: $lat ms" } else { Ok "DSN OK | lat_ms=$lat" }
}

# 5) Freshness do seed (arquivo CSV)
$csv = "$PSScriptRoot\Auditoria Conselho\FIN_SENSE_L1_SAMPLE.csv"
if (Test-Path $csv) {
  $ageHours = ((Get-Date) - (Get-Item $csv).LastWriteTime).TotalHours
  if ($ageHours -gt 4) { Fail "CSV stale > 4h" }
  Ok "CSV frescor OK"
} else { Fail "CSV nao encontrado: $csv" }

# 6) MT5 RTT
$pyMT5 = @"
import MetaTrader5 as mt5, time, sys
if not mt5.initialize():
    print('MT5_FAIL ' + str(mt5.last_error()))
    sys.exit(1)
t0 = time.time()
pos = mt5.positions_get(symbol='XAUUSD')
rtt = (time.time() - t0)*1000
info = mt5.symbol_info('XAUUSD')
vmin = info.volume_min if info else None
mt5.shutdown()
print('MT5_OK rtt_ms=' + str(rtt) + ' volume_min=' + str(vmin))
"@
$mt5Out = $pyMT5 | python -
if ($LASTEXITCODE -ne 0 -or $mt5Out -match 'MT5_FAIL') { Fail "MT5 ping falhou: $mt5Out" }
if ($mt5Out -match 'rtt_ms=([\d\.]+).*volume_min=([\d\.]+)') {
  $rtt = [double]$matches[1]; $vmin = [double]$matches[2]
  if ($rtt -gt 100) { Warn "RTT MT5 alto: $rtt ms" } else { Ok "MT5 RTT OK: $rtt ms" }
}

Ok "Preflight validado. O sistema pode seguir com sua execucao em $Mode."

# 7) Executar orquestrador + shadow_loop
Set-Location "$PSScriptRoot"
$env:NEBULAR_KUIPER_ROOT = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:PSA_AUDIT_BASE = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
Ok "Executando orquestrador ($Mode)..."
.\executar_omega_tier0_psa.ps1

Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
Ok "Executando shadow_loop ($Mode)..."
python core_engines\shadow_loop.py --mode $Mode --ativos XAUUSD --timeframes H1 H4 --equity 10000

Ok "Fluxo Ativo. Operadores Lógicos em Execução Contínua."
