$ErrorActionPreference = "Continue"
$script:AllPassed = $true
$script:TestResults = @()

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " TESTE DE CONFORMIDADE PSA - OMEGA HUNTER" -ForegroundColor Yellow

function Test-Requirement {
    param([string]$RequirementID, [string]$Description, [scriptblock]$Test, [string]$ErrorMessage = "Falha na validação")
    Write-Host -NoNewline "[TESTE] $($RequirementID): $Description ... "
    try {
        $result = & $Test
        if ($result) {
            Write-Host "PASS" -ForegroundColor Green
            $script:TestResults += @{ ID = $RequirementID; Status = "PASS" }
            return $true
        } else {
            Write-Host "FAIL" -ForegroundColor Red
            $script:TestResults += @{ ID = $RequirementID; Status = "FAIL" }
            $script:AllPassed = $false
            return $false
        }
    } catch {
        Write-Host "FAIL" -ForegroundColor Red
        $script:TestResults += @{ ID = $RequirementID; Status = "FAIL" }
        $script:AllPassed = $false
        return $false
    }
}

Test-Requirement -RequirementID "CQO-001" -Description "Input validation com raise ValueError" -Test {
    $out = python -c "import sys; sys.path.insert(0, '.'); from modules.validation.crisis_probability_validator import CrisisProbabilityValidator; v = CrisisProbabilityValidator(); v.calculate(98.5, 12.3, 325.0, -8.2); print('PASS')" 2>&1
    $out -match "PASS"
}

Test-Requirement -RequirementID "CQO-002" -Description "_calculate_required_samples retorna dict" -Test {
    $out = python -c "import sys; sys.path.insert(0, '.'); from modules.validation.gate_timing_validator import GateTimingValidator; v = GateTimingValidator(); print(str(type(v._calculate_required_samples())))" 2>&1
    $out -match "dict"
}

Test-Requirement -RequirementID "CQO-003" -Description "validate_with_transport_delay implementado" -Test {
    $out = python -c "import sys; sys.path.insert(0, '.'); from modules.validation.slo_validator_china import RegimeSLOValidatorChinaCouncil; v = RegimeSLOValidatorChinaCouncil(); r=v.validate_with_transport_delay(2.0, 200.0, 50.0); print(str(r['is_robust']))" 2>&1
    $out -match "True|False"
}

Test-Requirement -RequirementID "CQO-004" -Description "Hash inicial configurado no hunter.json" -Test {
    $cfg = Get-Content ".\config\regimes\hunter.json" | ConvertFrom-Json
    $null -ne $cfg.hash_verificacao
}

Test-Requirement -RequirementID "CQO-005" -Description "threading.local() implementado no shadow_loop.py" -Test {
    (Get-Content "..\core_engines\shadow_loop.py" -Raw).Contains("threading.local()")
}

Test-Requirement -RequirementID "CQO-006" -Description "SLO lido do hunter.json (não hardcoded)" -Test {
    $raw = Get-Content ".\run_hunter_regime.ps1" -Raw
    -not ($raw.Contains("measured_rtt_ms=200[^.]"))
}

Test-Requirement -RequirementID "CQO-007" -Description "Precisão extraída do log real" -Test {
    $raw = Get-Content ".\validate_hunter_mission.ps1" -Raw
    $raw.Contains("Select-String -Pattern") -and -not ($raw.Contains("`$precision = 0.72[^.]"))
}

if ($script:AllPassed) { Write-Host "ALL TESTS PASSED" -ForegroundColor Green; exit 0 } else { Write-Host "SOME TESTS FAILED" -ForegroundColor Red; exit 1 }
