# OMEGA  --  Gate integração ecossistema (obrigatório pós-unified)
# Ref: governance/GATE_INTEGRACAO_ECOSISTEMA_OBRIGATORIO_20260525.md
#
# Uso:
#   & .\scripts\omega_integration_gate.ps1 -Phase preflight
#   & .\scripts\omega_integration_gate.ps1 -Phase runtime
#   & .\scripts\omega_integration_gate.ps1 -Phase kpi -LogHours 1

param(
    [ValidateSet("preflight", "runtime", "kpi", "all")]
    [string]$Phase = "all",
    [int]$LogHours = 1
)

$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { Get-Location }
Set-Location $Root

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $Root "audit\integration_gate"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "INTEGRATION_GATE_${Phase}_$ts.txt"

$failures = @()

function Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $Report -Value $line
}

function Fail($id, $msg) {
    $script:failures += "${id}: $msg"
    Log "FAIL $id  --  $msg"
}

function Pass($id, $msg) {
    Log "PASS $id  --  $msg"
}

Log "=== OMEGA INTEGRATION GATE phase=$Phase ==="
Log "ROOT=$Root"

function Test-Preflight {
    Log "--- PREFLIGHT ---"
    $unifiedPy = Join-Path $Root "modules\omega_ecosystem_unified.py"
    if (-not (Test-Path $unifiedPy)) {
        Fail "A1" "modules/omega_ecosystem_unified.py ausente  --  git pull necessario"
    } else {
        Pass "A1" "omega_ecosystem_unified.py presente"
    }

    $runner = Join-Path $Root "scripts\run_omega_24x7.ps1"
    $content = Get-Content $runner -Raw -ErrorAction SilentlyContinue
    if ($content -notmatch 'OMEGA_ECOSYSTEM_UNIFIED\s*=\s*"1"') {
        Fail "A2" "OMEGA_ECOSYSTEM_UNIFIED nao definido em run_omega_24x7.ps1"
    } else { Pass "A2" "OMEGA_ECOSYSTEM_UNIFIED=1 no runner" }

    foreach ($pair in @(
        @("A3", "OMEGA_USE_SIGNAL_FUSION", '"1"'),
        @("A4", "PSA_SHADOW_MODE", '"0"'),
        @("A5", "OMEGA_ASSET_PROFILE", '"ceo_discovery_full"')
    )) {
        $id, $name, $needle = $pair
        if ($content -notmatch [regex]::Escape($name)) {
            Fail $id "$name nao encontrado em run_omega_24x7.ps1"
        } elseif ($needle -and $content -notmatch "$name\s*=\s*$([regex]::Escape($needle))") {
            Fail $id "$name valor inesperado (esperado $needle)"
        } else {
            Pass $id "$name OK"
        }
    }

    Log "pytest gate (opcional rapido)..."
    $env:PYTHONPATH = $Root
    $pytestOut = python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q --tb=no 2>&1
    $pytestOut | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0) {
        Fail "A6" "pytest falhou"
    } else {
        Pass "A6" "pytest PASS"
    }
}

function Test-Runtime {
    Log "--- RUNTIME ---"
    $manifest = Join-Path $Root "audit\paper\ecosystem_unified_manifest.json"
    if (-not (Test-Path $manifest)) {
        Fail "B1" "ecosystem_unified_manifest.json ausente  --  runner reiniciado com unified?"
    } else {
        Pass "B1" "manifesto existe"
        try {
            $j = Get-Content $manifest -Raw | ConvertFrom-Json
            if (-not $j.unified) { Fail "B2" "unified=false no manifesto" } else { Pass "B2" "unified=true" }
            $n = @($j.portfolio).Count
            if ($n -lt 16) { Fail "B3" "portfolio count=$n (esperado 16)" } else { Pass "B3" "portfolio count=$n" }
            $mp = $j.max_positions
            if ($mp -lt 1) { Fail "B4" "max_positions invalido" } else { Pass "B4" "max_positions=$mp" }
        } catch {
            Fail "B1-parse" "manifesto JSON invalido: $_"
        }
    }

    $log = Join-Path $Root "audit\paper\omega_24x7_runner.log"
    if (-not (Test-Path $log)) {
        Fail "B5" "omega_24x7_runner.log ausente"
    } else {
        $tail = Get-Content $log -Tail 500 -ErrorAction SilentlyContinue
        $eco = $tail | Select-String -Pattern '\[ECOSYSTEM_UNIFIED\]'
        if (-not $eco) {
            Fail "B5" "sem [ECOSYSTEM_UNIFIED] nas ultimas 500 linhas"
        } else {
            Pass "B5" "[ECOSYSTEM_UNIFIED] presente no log"
        }
        $sched = $tail | Select-String -Pattern '\[SCHEDULE\]'
        if (-not $sched) {
            Fail "B6" "sem [SCHEDULE] nas ultimas 500 linhas"
        } else {
            Pass "B6" "[SCHEDULE] presente"
        }
        $inv = $tail | Select-String -Pattern 'Invalid comment'
        if ($inv) { Fail "B7" "Invalid comment nas ultimas 500 linhas" } else { Pass "B7" "sem Invalid comment" }
    }
}

function Test-Kpi {
    Log "--- KPI (amostra log) ---"
    $log = Join-Path $Root "audit\paper\omega_24x7_runner.log"
    if (-not (Test-Path $log)) {
        Fail "C0" "log ausente para KPI"
        return
    }
    $lines = Get-Content $log -ErrorAction SilentlyContinue
    # Log lines may not have parseable dates  --  use tail heuristic: last 3000 lines ~ 1h dense
    $sample = $lines | Select-Object -Last 3000

    $psa = ($sample | Select-String -Pattern 'PSA_FEED').Count
    $ia = ($sample | Select-String -Pattern 'Sinal aprovado|DECISION=AGENT_IA|source=AGENT_IA').Count
    $mom = ($sample | Select-String -Pattern 'MOMENTUM_MT5').Count
    $edge = ($sample | Select-String -Pattern 'EDGE_GATE').Count
    $hold = ($sample | Select-String -Pattern 'Sinal rejeitado|IA.*HOLD').Count

    Log "KPI amostra (~ultimas 3000 linhas ou ~${LogHours}h):"
    Log "  PSA_FEED lines: $psa"
    Log "  AGENT_IA/aprovado lines: $ia"
    Log "  MOMENTUM_MT5 lines: $mom"
    Log "  EDGE_GATE lines: $edge"
    Log "  HOLD/rejeitado lines: $hold"

    $kpiFile = Join-Path $OutDir "KPI_$ts.json"
    @{
        sample_lines = $sample.Count
        psa_feed = $psa
        agent_ia = $ia
        momentum = $mom
        edge_gate = $edge
        hold_reject = $hold
    } | ConvertTo-Json | Set-Content $kpiFile -Encoding UTF8
    Pass "C-report" "KPI escrito em $kpiFile"

    if ($ia -eq 0 -and $mom -gt 0) {
        Log "WARN C3: execucoes momentum sem linha AGENT_IA na amostra  --  documentar no relatorio PSA (pode ser gates/mercado)"
    }
}

switch ($Phase) {
    "preflight" { Test-Preflight }
    "runtime"   { Test-Runtime }
    "kpi"       { Test-Kpi }
    "all"       { Test-Preflight; Test-Runtime; Test-Kpi }
}

Log ""
Log "Relatorio: $Report"
if ($failures.Count -gt 0) {
    Log "=== VEREDITO: INTEGRACAO FAIL ($($failures.Count) itens) ==="
    $failures | ForEach-Object { Log "  $_" }
    exit 1
}
Log "=== VEREDITO: INTEGRACAO PASS (fase $Phase) ==="
exit 0
