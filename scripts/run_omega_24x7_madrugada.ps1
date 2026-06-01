# OMEGA MADRUGADA — define env SEL/USFE enforcement e delega ao runner standard
$ErrorActionPreference = "Stop"
$env:OMEGA_ENFORCE_SEL_USFE_GATE = "1"
$env:OMEGA_SEL_ENABLED = "1"
$env:OMEGA_USFE_BLOCK = "1"
$env:OMEGA_SKIP_SEL_USFE_ENFORCE = "0"
$env:OMEGA_LOOP_INTERVAL_SEC = "15"
. "$PSScriptRoot\run_omega_24x7.ps1"
