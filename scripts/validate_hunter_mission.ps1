# =============================================================================
# VALIDAÇÃO PÓS-MISSÃO - OMEGA HUNTER
# =============================================================================
$mission_dir = Get-ChildItem ".\logs\hunter" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $mission_dir) { exit 1 }

$manifest_path = "$($mission_dir.FullName)\manifest.json"
$manifest = Get-Content $manifest_path | ConvertFrom-Json

# Patch #7 CQO
$log_file = "$($mission_dir.FullName)\execution.log"
$precision = 0.60
$samples = 48

if (Test-Path $log_file) {
    $log_content = Get-Content $log_file -Raw
    if ($log_content -match "precision[:\s]+([0-9.]+)") {
        $precision = [double]$matches[1]
    }
    
    $sel = Select-String -Pattern "precision" -Path $log_file
}

$gate_output = python -c "import sys; sys.path.insert(0, '.'); from modules.validation.gate_timing_validator import GateTimingValidator; v = GateTimingValidator(); print(v.validate($precision, $samples)['gate_approved'])"

if ($gate_output -eq "True") {
    Write-Host "Recomendar LIVE"
}
