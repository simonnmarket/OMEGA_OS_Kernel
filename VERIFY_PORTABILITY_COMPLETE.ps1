param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'

function Write-Section([string]$Title) {
  Write-Host "" 
  Write-Host ("=" * 80)
  Write-Host $Title -ForegroundColor Cyan
  Write-Host ("=" * 80)
}

Write-Section "[C4] OMEGA Portability Verification"
Write-Host "RepoRoot: $RepoRoot"

# 1) Hardcoded path scan
Write-Section "[1/3] Running hardcoded path detector"
$detector = Join-Path $RepoRoot 'ANALYZE_HARDCODED_PATHS.py'
if (!(Test-Path $detector)) {
  throw "Missing detector: $detector"
}

python $detector

$reportPath = Join-Path $RepoRoot 'path_analysis_report.txt'
if (Test-Path $reportPath) {
  Write-Host "[OK] Detector report: $reportPath" -ForegroundColor Green
} else {
  throw "Detector report not found after execution: $reportPath"
}

# 2) Temporary directory execution (smoke test)
Write-Host "`n[2/3] Smoke test em diretório temporário (com isolamento de env vars)..." -ForegroundColor Magenta
$tmpBase = if ($env:OMEGA_TMP_PATH) { $env:OMEGA_TMP_PATH } else { [System.IO.Path]::GetTempPath() }
$runDir = Join-Path $tmpBase ("omega_portability_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
Write-Host "Temp run dir: $runDir"
$excludes = @('.git','venv','.venv','__pycache__','node_modules','BACKUP','BACKUPS','backup','archive','Auditoria PARR-F','inativo')
Get-ChildItem -LiteralPath $RepoRoot -Force | ForEach-Object {
  if ($excludes -contains $_.Name) { return }
  Copy-Item -LiteralPath $_.FullName -Destination $runDir -Recurse -Force
}
Write-Host "[ISOLAMENTO] Configurando variáveis de ambiente para diretório temporário..." -ForegroundColor Cyan
$original_env = @{
  'OMEGA_BAU_PATH'      = $env:OMEGA_BAU_PATH
  'OMEGA_DATA_ROOT'     = $env:OMEGA_DATA_ROOT
  'OMEGA_PROJETO_PATH'  = $env:OMEGA_PROJETO_PATH
  'OMEGA_OHLCV_PATH'    = $env:OMEGA_OHLCV_PATH
  'OMEGA_TMP_PATH'      = $env:OMEGA_TMP_PATH
  'OMEGA_AUDIT_BASE'    = $env:OMEGA_AUDIT_BASE
  'OMEGA_MANIFEST_PATH' = $env:OMEGA_MANIFEST_PATH
  'PYTHONUTF8'          = $env:PYTHONUTF8
  'PYTHONIOENCODING'    = $env:PYTHONIOENCODING
}
$original_output_encoding = [Console]::OutputEncoding
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:OMEGA_BAU_PATH      = Join-Path $runDir 'bau'
$env:OMEGA_DATA_ROOT     = Join-Path $runDir 'data'
$env:OMEGA_PROJETO_PATH  = Join-Path $runDir 'data/projeto'
$env:OMEGA_OHLCV_PATH    = Join-Path $runDir 'data/ohlcv/XAUUSD_H4.csv'
$env:OMEGA_TMP_PATH      = Join-Path $runDir 'tmp'
$env:OMEGA_AUDIT_BASE    = Join-Path $runDir 'audit'
$env:OMEGA_MANIFEST_PATH = Join-Path $runDir 'bau/06_MANIFEST'
@('bau','data/projeto','data/ohlcv','tmp','audit','bau/06_MANIFEST') | ForEach-Object {
  $dir = Join-Path $runDir $_
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}
$source_ohlcv = Join-Path $RepoRoot 'data/ohlcv/XAUUSD_H4.csv'
$dest_ohlcv   = Join-Path $runDir   'data/ohlcv/XAUUSD_H4.csv'
if (Test-Path $source_ohlcv) { Copy-Item -LiteralPath $source_ohlcv -Destination $dest_ohlcv -Force }
Push-Location $runDir
$mainPy = Join-Path $runDir 'main.py'
if (Test-Path $mainPy) {
  Write-Host "Running: python main.py --help (isolated env)" -ForegroundColor Yellow
  $job = Start-Job -ScriptBlock { param($mainPy) python $mainPy --help 2>&1; $LASTEXITCODE } -ArgumentList $mainPy
  $completed = Wait-Job $job -Timeout 30
  if ($completed) {
    $output = Receive-Job $job
    $code = ($output | Select-Object -Last 1)
    Remove-Job $job -Force
    Write-Host $output
  } else {
    Stop-Job $job -Force; Remove-Job $job -Force
    Write-Host "[TIMEOUT] main.py excedeu 30 segundos" -ForegroundColor Red
    $code = -1
  }
  if ($code -eq 0) { Write-Host "[OK] main.py executou com sucesso em diretório temporário" -ForegroundColor Green }
  else { Write-Host "[FALHA] main.py falhou em diretório temporário (exit code: $code)" -ForegroundColor Red }
} else {
  Write-Host "[AVISO] main.py não encontrado em temp copy; skipping run" -ForegroundColor Yellow
}
Pop-Location
foreach ($key in $original_env.Keys) {
  if ($null -eq $original_env[$key]) { Remove-Item "env:$key" -ErrorAction SilentlyContinue }
  else { Set-Item "env:$key" -Value $original_env[$key] }
}
[Console]::OutputEncoding = $original_output_encoding
if (Test-Path $runDir) { Remove-Item -Path $runDir -Recurse -Force }

# 3) Summary
Write-Section "[3/3] Summary"
Write-Host "- Report: $reportPath"
Write-Host "- TempDir: $runDir"
Write-Host "Done." -ForegroundColor Green
