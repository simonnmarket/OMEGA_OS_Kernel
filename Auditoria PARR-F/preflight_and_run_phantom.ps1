param(
  [string]$Csv = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Auditoria Conselho\FIN_SENSE_L1_SAMPLE.csv",
  [int]$StartHour = 9,
  [int]$EndHour = 17
)

function Fail($m){Write-Host "❌ $m" -ForegroundColor Red; exit 1}
function Ok($m){Write-Host "✅ $m" -ForegroundColor Green}
function Warn($m){Write-Host "⚠️ $m" -ForegroundColor Yellow}

$hour=(Get-Date).Hour
if($hour -lt $StartHour -or $hour -ge $EndHour){
  if($env:OMEGA_NIGHT_PASS -ne "AUTHORISED_BY_CEO"){Fail "Fora da janela ($StartHour-$EndHour) e sem night pass"}
  Warn "Night pass ativo (DEMO_ONLY)."
} else { Ok "Dentro da janela ($StartHour-$EndHour)" }

if(-not (Test-Path $Csv)){Fail "CSV não encontrado: $Csv"}
Ok "CSV OK: $Csv"

$pyDuck = @"
import duckdb, os, sys, time
import pandas as pd
csv=r'$Csv'
if not csv or not os.path.exists(csv):
    print('FAIL CSV')
    sys.exit(1)
t0=time.time()
try:
    df = pd.read_csv(csv)
    con = duckdb.connect(':memory:')
    con.execute('CREATE TABLE tbl AS SELECT * FROM df')
    cnt = con.execute('SELECT COUNT(*) FROM tbl').fetchone()[0]
    lat = (time.time()-t0)*1000
    print(f'OK CSV_ROWS {cnt} LAT_MS {lat:.2f}')
    con.close()
except Exception as e:
    print(f'FAIL DUCK: {e}')
    sys.exit(1)
"@

$pyOut = $pyDuck | python -
if($LASTEXITCODE -ne 0 -or $pyOut -like "*FAIL*"){Fail "DuckDB/CSV check falhou: $pyOut"}
Ok "Motor Phantom L1 Integrado: $pyOut"

Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
$env:FIN_SENSE_CSV_PATH = $Csv
$env:OMEGA_USE_FIN_SENSE_L1 = "1"
$env:NEBULAR_KUIPER_ROOT = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:PSA_AUDIT_BASE = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"

Ok "Executando orquestrador (phantom)..."
.\executar_omega_tier0_psa.ps1

Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
Ok "Executando shadow_loop (paper)..."
python core_engines\shadow_loop.py --mode paper `
  --ativos XAUUSD `
  --timeframes H1 H4 `
  --equity 10000

Ok "Fluxo concluído. Phantom Protocol encerrado."
