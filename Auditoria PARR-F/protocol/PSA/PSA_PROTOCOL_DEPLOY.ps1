<#.SYNOPSIS
  Implantação e prova de conclusão PSA — pacote DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414
.DESCRIPTION
  Escreve APENAS sob: <ParrfRoot>\00_PROVAS_AUDITORIA\PSA\<DocId>\<RunId>\
  Lê canónicos de: <ParrfRoot>\Conselho\
  Gera: MANIFEST.json, MANIFEST.sha256, mirror\, logs\deploy.log, COMPLETION_PROOF.json, COMPLETION_PROOF.md
.PARAMETER VerifyOnly
  Revalida hashes; obrigatório -RunId com pasta de run existente.
.NOTES
  PowerShell 5.1+ | SPEC: protocol/PSA/SPEC_PSA_COMPLETION_PROOF.md
#>

[CmdletBinding()]
param(
  [string] $ParrfRoot = "",
  [string] $DocId = "DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414",
  [string] $RunId = "",
  [switch] $VerifyOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$Path) {
  return (Resolve-Path -LiteralPath $Path).Path
}

function Assert-UnderRoot([string]$Candidate, [string]$Root) {
  # Não exige que $Candidate exista (Resolve-Path falharia antes de mkdir).
  $r = Resolve-AbsolutePath $Root
  $cFull = [System.IO.Path]::GetFullPath($Candidate)
  $rFull = [System.IO.Path]::GetFullPath($r)
  if (-not ($cFull.StartsWith($rFull, [System.StringComparison]::OrdinalIgnoreCase))) {
    throw "PATH_VIOLATION: '$cFull' não está sob '$rFull'"
  }
}

function Get-Sha256File([string]$FilePath) {
  return (Get-FileHash -LiteralPath $FilePath -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Try-GitHead([string]$RepoRoot) {
  $gitDir = Join-Path $RepoRoot ".git"
  if (-not (Test-Path -LiteralPath $gitDir)) {
    return @{ head = $null; note = "sem .git em $RepoRoot" }
  }
  Push-Location $RepoRoot
  try {
    $out = (& git rev-parse HEAD 2>$null | Out-String).Trim()
    if (-not $out) { return @{ head = $null; note = "git rev-parse vazio" } }
    return @{ head = $out; note = $null }
  }
  finally { Pop-Location }
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

# --- Raiz PARR-F ---
if ([string]::IsNullOrWhiteSpace($ParrfRoot)) {
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  $ParrfRoot = Resolve-AbsolutePath (Join-Path $here "..\..")
}
$ParrfRoot = Resolve-AbsolutePath $ParrfRoot
$Conselho = Join-Path $ParrfRoot "Conselho"
# Zona efémera — NUNCA confundir com pastas de módulos / runtime da aplicação (ver SPEC §0).
$AuditEvidenceZone = Join-Path $ParrfRoot "00_PROVAS_AUDITORIA"
$EvidencePsaRoot = Join-Path $AuditEvidenceZone "PSA"

$required = @(
  "DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414.md",
  "GATES_NUMERICOS_V1.yaml",
  "ARBITRO_MULTITF_V1.py",
  "AUDIT_JSON_SCHEMA_V1.0.json"
)

if (-not (Test-Path -LiteralPath $Conselho)) {
  throw "CANONICAL_MISSING: $Conselho"
}
foreach ($f in $required) {
  if (-not (Test-Path -LiteralPath (Join-Path $Conselho $f))) {
    throw "CANONICAL_FILE_MISSING: Conselho\$f"
  }
}

if ($VerifyOnly) {
  if ([string]::IsNullOrWhiteSpace($RunId)) { throw "VerifyOnly: informe -RunId (pasta de execução existente)." }
  $RunRoot = Join-Path (Join-Path $EvidencePsaRoot $DocId) $RunId
  if (-not (Test-Path -LiteralPath $RunRoot)) { throw "RUN_NOT_FOUND: $RunRoot" }
  Assert-UnderRoot $RunRoot $AuditEvidenceZone
  if ($RunRoot -notlike "*00_PROVAS_AUDITORIA*") { throw "RUN_PATH_INVALID: provas devem estar sob 00_PROVAS_AUDITORIA" }
  $manifestPath = Join-Path $RunRoot "MANIFEST.json"
  if (-not (Test-Path -LiteralPath $manifestPath)) { throw "MANIFEST_MISSING" }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  $allOk = $true
  foreach ($item in $manifest.files) {
    $rel = $item.mirror_relative_path -replace '/', '\'
    $mp = Join-Path $RunRoot $rel
    if (-not (Test-Path -LiteralPath $mp)) { Write-Host "FAIL missing $mp"; $allOk = $false; continue }
    $h = Get-Sha256File $mp
    if ($h -ne $item.sha256) {
      Write-Host "FAIL hash $($item.role) expected=$($item.sha256) actual=$h"
      $allOk = $false
    }
  }
  if (-not $allOk) { exit 2 }
  Write-Host "VERIFY_ONLY: PASS"
  exit 0
}

if ([string]::IsNullOrWhiteSpace($RunId)) {
  $suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
  $RunId = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ") + "_" + $suffix
}

$RunRoot = Join-Path (Join-Path $EvidencePsaRoot $DocId) $RunId
Assert-UnderRoot $RunRoot $AuditEvidenceZone
if ($RunRoot -notlike "*00_PROVAS_AUDITORIA*") { throw "RUN_PATH_INVALID: destino de prova inválido" }

$MirrorDir = Join-Path $RunRoot "mirror"
$LogsDir = Join-Path $RunRoot "logs"
New-Item -ItemType Directory -Path $MirrorDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
$logFile = Join-Path $LogsDir "deploy.log"
Start-Transcript -LiteralPath $logFile -Force

try {
  Write-Host "PARRF_ROOT=$ParrfRoot"
  Write-Host "RUN_ROOT=$RunRoot"

  foreach ($f in $required) {
    Copy-Item -LiteralPath (Join-Path $Conselho $f) -Destination (Join-Path $MirrorDir $f) -Force
  }

  $gitInfo = Try-GitHead $ParrfRoot
  $fileEntries = @()
  foreach ($f in $required) {
    $dstAbs = Join-Path $MirrorDir $f
    $fileEntries += [ordered]@{
      role                     = $f
      canonical_relative_path  = "Conselho/$f"
      mirror_relative_path     = "mirror/$f"
      size_bytes               = (Get-Item -LiteralPath $dstAbs).Length
      sha256                   = (Get-Sha256File $dstAbs)
    }
  }

  $manifestObj = [ordered]@{
    doc_id              = $DocId
    run_id              = $RunId
    utc_started         = (Get-Date).ToUniversalTime().ToString("o")
    parrf_audit_tree_root = $ParrfRoot
    audit_evidence_zone   = $AuditEvidenceZone
    git_head            = $gitInfo.head
    git_head_note       = $gitInfo.note
    files               = @($fileEntries)
  }
  $manifestPath = Join-Path $RunRoot "MANIFEST.json"
  Write-Utf8NoBom $manifestPath ($manifestObj | ConvertTo-Json -Depth 10)
  $manifestSha = (Get-Sha256File $manifestPath)
  Write-Utf8NoBom (Join-Path $RunRoot "MANIFEST.sha256") ($manifestSha + "  MANIFEST.json`n")

  $gatePaths = $true
  try {
    Assert-UnderRoot $RunRoot $AuditEvidenceZone
    if ($RunRoot -notlike "*00_PROVAS_AUDITORIA*") { $gatePaths = $false }
  }
  catch { $gatePaths = $false }

  $gateFour = $true
  foreach ($f in $required) {
    $p = Join-Path $MirrorDir $f
    if (-not (Test-Path -LiteralPath $p)) { $gateFour = $false; break }
    if ((Get-Item -LiteralPath $p).Length -le 0) { $gateFour = $false; break }
  }

  $gateManifest = $true
  foreach ($item in $fileEntries) {
    $mp = Join-Path $RunRoot ($item.mirror_relative_path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $mp)) { $gateManifest = $false; break }
    if ((Get-Sha256File $mp) -ne $item.sha256) { $gateManifest = $false; break }
  }

  $gateArbiter = $false
  if (Get-Command python -ErrorAction SilentlyContinue) {
    $arb = Join-Path $MirrorDir "ARBITRO_MULTITF_V1.py"
    & python $arb 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) { $gateArbiter = $true }
  }

  $gateJson = $false
  try {
    $null = Get-Content -LiteralPath (Join-Path $MirrorDir "AUDIT_JSON_SCHEMA_V1.0.json") -Raw | ConvertFrom-Json
    $gateJson = $true
  }
  catch { $gateJson = $false }

  $gateYaml = $false
  if (Get-Command python -ErrorAction SilentlyContinue) {
    $yamlAbs = (Resolve-Path -LiteralPath (Join-Path $MirrorDir "GATES_NUMERICOS_V1.yaml")).Path
    $env:PSA_YAML_GATE_PATH = $yamlAbs
    & python -c "import yaml,os; yaml.safe_load(open(os.environ['PSA_YAML_GATE_PATH'],'r',encoding='utf-8')); print('YAML_OK')" 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) { $gateYaml = $true }
    Remove-Item Env:PSA_YAML_GATE_PATH -ErrorAction SilentlyContinue
  }

  $proofJsonPath = Join-Path $RunRoot "COMPLETION_PROOF.json"
  $proofMdPath = Join-Path $RunRoot "COMPLETION_PROOF.md"

  $manifestShaLine = (Get-Content -LiteralPath (Join-Path $RunRoot "MANIFEST.sha256") -Raw).Trim()
  $allTechnical = $gatePaths -and $gateFour -and $gateManifest -and $gateArbiter -and $gateJson -and $gateYaml

  $md = New-Object System.Collections.Generic.List[string]
  [void]$md.Add("# COMPLETION_PROOF (PSA)")
  [void]$md.Add("")
  [void]$md.Add("| Campo | Valor |")
  [void]$md.Add("|--------|--------|")
  [void]$md.Add("| DOC_ID | ``$DocId`` |")
  [void]$md.Add("| RUN_ID | ``$RunId`` |")
  $utcDone = (Get-Date).ToUniversalTime().ToString("o")
  [void]$md.Add("| UTC | ``$utcDone`` |")
  [void]$md.Add("| HOST | ``$env:COMPUTERNAME`` |")
  [void]$md.Add("| USER | ``$env:USERNAME`` |")
  [void]$md.Add("| RUN_ROOT | ``$RunRoot`` |")
  [void]$md.Add("")
  [void]$md.Add("## Gates (binário)")
  [void]$md.Add("")
  [void]$md.Add("| Gate | Resultado |")
  [void]$md.Add("|------|-----------|")
  [void]$md.Add("| gate_paths_within_audit_zone | $(if ($gatePaths) {'PASS'} else {'FAIL'}) |")
  [void]$md.Add("| gate_four_files_present | $(if ($gateFour) {'PASS'} else {'FAIL'}) |")
  [void]$md.Add("| gate_manifest_matches_mirror | $(if ($gateManifest) {'PASS'} else {'FAIL'}) |")
  [void]$md.Add("| gate_python_arbiter_selftest | $(if ($gateArbiter) {'PASS'} else {'FAIL'}) |")
  [void]$md.Add("| gate_json_schema_parseable | $(if ($gateJson) {'PASS'} else {'FAIL'}) |")
  [void]$md.Add("| gate_yaml_parseable | $(if ($gateYaml) {'PASS'} else {'FAIL'}) |")

  Write-Utf8NoBom $proofJsonPath '{"placeholder":true}'
  Write-Utf8NoBom $proofMdPath ($md -join "`n")

  $gateArtifacts = (Test-Path -LiteralPath $proofJsonPath) -and (Test-Path -LiteralPath $proofMdPath) -and (Test-Path -LiteralPath $logFile)
  $outcome2 = $(if ($allTechnical -and $gateArtifacts) { "PASS" } else { "FAIL" })

  [void]$md.Add("| gate_completion_artifacts_present | $(if ($gateArtifacts) {'PASS'} else {'FAIL'}) |")
  [void]$md.Add("")
  [void]$md.Add('## SHA-256 (formato GNU `sha256sum`)')
  [void]$md.Add('```')
  foreach ($item in $fileEntries) {
    $mp = Join-Path $RunRoot ($item.mirror_relative_path -replace '/', '\')
    $h = Get-Sha256File $mp
    [void]$md.Add("$h  $($item.mirror_relative_path)")
  }
  [void]$md.Add("$manifestSha  MANIFEST.json")
  [void]$md.Add('```')
  [void]$md.Add("")
  [void]$md.Add("## Outcome")
  [void]$md.Add("**OUTCOME=$outcome2**")
  [void]$md.Add("")
  [void]$md.Add("Regra: **PASS** implica todos os gates = PASS; qualquer **FAIL** invalida a conclusão perante o Conselho.")
  [void]$md.Add("")

  $proofObj = [ordered]@{
    doc_id                            = $DocId
    run_id                            = $RunId
    utc_completed                     = $utcDone
    operator_env_USER                 = $env:USERNAME
    operator_env_COMPUTERNAME         = $env:COMPUTERNAME
    manifest_sha256_line              = $manifestShaLine
    gate_paths_within_audit_zone      = [bool]$gatePaths
    gate_four_files_present           = [bool]$gateFour
    gate_manifest_matches_mirror      = [bool]$gateManifest
    gate_python_arbiter_selftest      = [bool]$gateArbiter
    gate_json_schema_parseable        = [bool]$gateJson
    gate_yaml_parseable               = [bool]$gateYaml
    gate_completion_artifacts_present = [bool]$gateArtifacts
    outcome                           = $outcome2
    spec_reference                    = "protocol/PSA/SPEC_PSA_COMPLETION_PROOF.md"
  }

  Write-Utf8NoBom $proofJsonPath ($proofObj | ConvertTo-Json -Depth 8)
  Write-Utf8NoBom $proofMdPath ($md -join "`n")

  Write-Host "OUTCOME=$outcome2"
  Write-Host "ARTIFACT_ROOT=$RunRoot"
  if ($outcome2 -ne "PASS") { exit 1 }
}
finally {
  try { Stop-Transcript | Out-Null } catch {}
}

exit 0
