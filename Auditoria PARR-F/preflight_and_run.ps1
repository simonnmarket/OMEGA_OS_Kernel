param(
  [string]$Dsn = $env:FIN_SENSE_DSN,
  [int]$StartHour = 9,
  [int]$EndHour = 17
)

function Fail($msg) { Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }
function Ok($msg) { Write-Host "✅ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "⚠️  $msg" -ForegroundColor Yellow }

# 1) Janela
$hour = (Get-Date).Hour
if ($hour -lt $StartHour -or $hour -ge $EndHour) {
  Fail "Fora da janela demo ($StartHour-$EndHour). Atual: $hour"
}
Ok "Dentro da janela demo ($StartHour-$EndHour)."

# 2) DSN reachability
if (-not $Dsn -or [string]::IsNullOrWhiteSpace($Dsn)) {
  Fail "FIN_SENSE_DSN não configurada."
}
$port = ([Uri]$Dsn).Port
if (-not (Test-NetConnection -ComputerName ([Uri]$Dsn).Host -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded) {
  Fail "Porta $port inacessível."
}
Ok "Porta $port acessível."

# 3) DSN query (timeout)
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
    print(f'OK {lat:.2f}')
except Exception as e:
    print(f'FAIL {e}')
    sys.exit(1)
"@
$pyOut = $pyCheck | python -
if (-not $LASTEXITCODE -eq 0 -or $pyOut -like "*FAIL*") {
  Fail "DSN query falhou: $pyOut"
}
if ($pyOut -match "OK\s+([\d\.]+)") {
  $lat = [double]$matches[1]
  if ($lat -gt 50) { Warn "Latência DSN acima de 50ms: $lat ms" } else { Ok "DSN OK | lat_ms=$lat" }
}
else {
  Fail "DSN resposta inesperada: $pyOut"
}

# 4) MT5 ping
$pyMT5 = @"
import MetaTrader5 as mt5, sys
if mt5.initialize():
    info = mt5.terminal_info()
    ping = getattr(info, 'ping_last', 'n/a')
    print(f'MT5_OK {ping}')
    mt5.shutdown()
else:
    print(f'MT5_FAIL {mt5.last_error()}')
    sys.exit(1)
"@
$mt5Out = $pyMT5 | python -
if (-not $LASTEXITCODE -eq 0 -or $mt5Out -like "MT5_FAIL*") {
  Fail "MT5 ping falhou: $mt5Out"
}
else { Ok "MT5 OK: $mt5Out" }

# 5) Execução
Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
$env:FIN_SENSE_DSN = $Dsn
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
$env:PSA_AUDIT_BASE = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
Ok "Executando orquestrador..."
.\executar_omega_tier0_psa.ps1

Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
Ok "Executando shadow_loop (paper)..."
python core_engines\shadow_loop.py --mode paper `
  --ativos XAUUSD `
  --timeframes H1 H4 `
  --equity 10000

Ok "Fluxo concluído. Coletar artefatos e validar métricas."
