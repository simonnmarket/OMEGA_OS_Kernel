# Registo PSA — Mudanças operacionais e de governança (OMEGA QUANTUM LAB)

| Campo | Valor |
|-------|--------|
| **ID documento** | DOC-OFC-PSA-REGISTO-MUDANCAS-v1.0 |
| **Data emissão** | 2026-05-18 |
| **Para** | PSA Lead |
| **Cc** | CEO, Tech Lead, CKO, CIO |
| **Assunto** | Registo único de alterações recentes (bridge, trilho modo real, relógio de sessão, memorandos, flags 24/7) para arquivo e auditoria |
| **Branch** | `feature/nebular-integration-phase1` |
| **Repositório remoto** | `origin` (último push inclui commit `e449cc8` na data deste registo) |

---

## 1. Finalidade deste documento

Centralizar para o **PSA** todas as mudanças **documentadas e persistidas em Git** que afectam:

- integração **Execution Bridge v2.2** e **runner Opção B**;
- **governança B6** (desbloqueio Opção A);
- **trilho modo real** (checklist Fase A, memorando de fecho, envio oficial);
- módulo **`omega_session_clock`** (Fase A A4);
- **operação 24/7** (reactivação do **MOMENTUM_FALLBACK**).

Evita dispersão por vários e-mails: este ficheiro é a **fonte canónica** do registo `DOC-OFC-PSA-REGISTO-MUDANCAS-v1.0`. Actualizações futuras: **editar este ficheiro** (Secção 11) ou emitir `v1.1` com novo ID — **não** duplicar com o mesmo ID.

---

## 2. Linha do tempo — commits (ordem anti-cronológica recente → mais antiga relevante)

| Commit | Resumo |
|--------|--------|
| `e449cc8` | **Operação 24/7:** `OMEGA_DISABLE_MOMENTUM_FALLBACK=0` em `config/live_flags.json` + `scripts/run_omega_24x7.ps1` (env com precedência; rollback documentado no commit). |
| `24cdd9e` | **Envio PSA Fase A:** criação `DOC-OFC-ENVIO-PSA-FECHO-FASE-A-TRILHO-MODO-REAL-20260517.md` (ID `DOC-OFC-ENVIO-PSA-FECHO-FASE-A-v1.0`). |
| `a9f957d` | **Checklist v1.0.3** + **GOV-MEMO §6.1:** Secção 9 (fonte canónica `omega_session_clock` + regra Pendente); consolidação memorando duplicado. |
| `4682fb8` | **Checklist v1.0.2:** A4 fechada; **Fase A 4/4**. |
| `d321006` | **`omega_session_clock`:** integração em `modules/omega_session_clock.py` + `modules/__init__.py`. |
| `27d2a4d` | **Checklist v1.0.1:** arquivo checklist + A1–A3 com evidência e hashes. |
| `ba4d742` | **Memorando:** `GOV-MEMO-PSA-FECHO-BRIDGE-v1.0.md` — fecho secção governança bridge. |
| `8d07809` | **GOV-B6:** `DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md` (GOV-BRIDGE-B6-UNLOCK-v1.0) + evidência `audit/bridge/bridge_runner.jsonl` (dry-run). |
| `5fc18c0` | **Runner Opção B:** `scripts/omega_bridge_runner.py` v1.0.0 + narrativa versões em `modules/__init__.py`. |
| `dcdd949` | **Bridge v2.2:** `modules/omega_execution_bridge_v2_2.py` + `modules/__init__.py` (pacote `2.5.1` vs componente `v2.2` — numerações independentes). |

*(Commits anteriores a `dcdd949` na mesma linha OIS/DIAG — ex. `1ac3586`, `b74b1bb` — referem-se à auditoria OIS-20260517 e flags P0; não repetimos aqui o diff completo; permanecem no histórico Git.)*

---

## 3. Execution Bridge v2.2 + Runner Opção B + GOV-B6

| Item | Detalhe |
|------|---------|
| **Módulo** | `SOURCE_CODE/modules/omega_execution_bridge_v2_2.py` — PSA-EXEC-BRIDGE-v2.2; self-tests T00–T04; sem integração directa no `shadow_loop` sem desenho (doc §5). |
| **Runner** | `SOURCE_CODE/scripts/omega_bridge_runner.py` — poll `audit/bridge/signals/OMEGA_SIGNAL.*.json`, `--dry-run`, `--self-test`, JSONL `audit/bridge/bridge_runner.jsonl`. |
| **B6** | `SOURCE_CODE/governance/DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md` — **ID** GOV-BRIDGE-B6-UNLOCK-v1.0; Opção A no `shadow_loop` **bloqueada** até critérios §3 + assinaturas §5. |
| **Decisão Conselho** | Opção **B** primeiro; Opção **A** condicionada a desenho + `OMEGA_FILE_BRIDGE_AFTER_DECISION=1` + anti-duplicação `mt5_send_order`. |

---

## 4. Governança — memorando de fecho Bridge e correcção de duplicado

| Item | Detalhe |
|------|---------|
| **Memorando canónico** | `SOURCE_CODE/governance/GOV-MEMO-PSA-FECHO-BRIDGE-v1.0.md` — ID `GOV-MEMO-PSA-FECHO-BRIDGE-v1.0`. |
| **Problema corrigido** | Existiu ficheiro duplicado `MEMO_PSA_FECHO_SECCAO_GOVERNANCA_BRIDGE_v1.md` (mesmo propósito) — **removido**; registo em **§6.1** do memorando canónico. |
| **Regra** | Antes de criar novo `.md` em `governance/`: verificar ID existente; **actualizar** em vez de duplicar. |

---

## 5. Trilho modo real — checklist e envio PSA Fase A

| Documento | Path | ID |
|-----------|------|-----|
| Checklist | `governance/DOC-OFC-CHECKLIST-VALIDACAO-MODO-REAL-COMPONENTES-OMEGA-20260517.md` | DOC-OFC-CHECKLIST-MODO-REAL-v1.0 |
| Envio Fase A | `governance/DOC-OFC-ENVIO-PSA-FECHO-FASE-A-TRILHO-MODO-REAL-20260517.md` | DOC-OFC-ENVIO-PSA-FECHO-FASE-A-v1.0 |

**Fase A:** **4/4** com commits `5fc18c0`, `dcdd949`, `8d07809`, `d321006` (ver checklist Secção 4 e registo Secção 8).

**Secção 9 (checklist):** fonte canónica `SOURCE_CODE/modules/omega_session_clock.py`; pasta **Pendente** no Desktop = arquivo de trabalho apenas (sem sync sem decisão).

---

## 6. Módulo `omega_session_clock` (MOD-SESSION-CLOCK-001)

| Item | Detalhe |
|------|---------|
| **Path canónico** | `SOURCE_CODE/modules/omega_session_clock.py` |
| **Pacote** | Entrada `omega_session_clock` em `modules/__init__.py` + bloco documental `[SESSION CLOCK — TIER-0]`. |
| **Validação** | `python modules/omega_session_clock.py` → `[OK] omega_session_clock self-test passed` |
| **Env opcional** | `OMEGA_POLICY_TZ`, `OMEGA_BROKER_TZ`, `OMEGA_BROKER_OFFSET_MINUTES`, `OMEGA_TERMINAL_TZ`, `OMEGA_SOURCE_ROOT` |
| **Config opcional** | `config/omega_session_clock.json` (`holidays` por venue), relativo a `OMEGA_SOURCE_ROOT` / raiz do processo. |

---

## 7. Operação 24/7 — reactivação MOMENTUM_FALLBACK (2026-05-18)

| Antes | Depois |
|-------|--------|
| `config/live_flags.json` → `"OMEGA_DISABLE_MOMENTUM_FALLBACK": "1"` | `"0"` |
| Runner sem env explícita herdava bloqueio via JSON | `scripts/run_omega_24x7.ps1` define `$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "0"` (precedência sobre JSON). |

**Motivo:** Com P0-A = `1`, quando `AGENT_IA` não produz trade utilizável, o ramo de fallback momentum era **SKIP** → **0 execuções** apesar de confluência/sinais internos.

**Risco (PSA):** reactivar o fallback **reexpõe** o risco documentado em **OIS-20260517 / PSA-015** (inversão / divergência IA vs momentum). **Rollback:** repor `"1"` em `live_flags.json`, remover ou ajustar a linha no `.ps1`, **reiniciar** o processo do runner.

**Acção operacional obrigatória:** qualquer processo Python do loop **já em execução** tem de ser **reiniciado** após `git pull` para carregar env + ficheiros actualizados.

---

## 8. Contexto operacional (registo — não alterado por commits isolados acima)

| Tema | Nota para PSA |
|------|----------------|
| **Motor V3 / 0xC0000005** | Crash de subprocess (ACCESS VIOLATION) reportado em **2026-05-16**; runner parou (“dados obsoletos proibidos”). **Não** é corrigido pelo commit `e449cc8`; exige RCA (WER, binário, inputs). |
| **Audit gate Tier-0** | Pré-ciclo (baseline SHA3, equity/DD, strict); **não** substitui monitorização de crash **durante** subprocess — lacuna já identificada pelo Conselho (watchdog / alerta). |
| **Modo** | `run_omega_24x7.ps1` mantém `OMEGA_24X7_MODE=paper` e parâmetros de risco conforme cabeçalho do script — **verificar** alinhamento com ordem CEO actual. |

---

## 9. Pedido de acções ao PSA

1. **Arquivar** este documento como `DOC-OFC-PSA-REGISTO-MUDANCAS-v1.0` (path Secção 10).
2. **Confirmar** no remoto os hashes da Secção 2 (`git fetch` + `git log`).
3. **Validar** com Eng/Ops que o runner 24x7 foi **reiniciado** após `e449cc8`.
4. **Rubrificar** no checklist (Secção 6) ciência da **Fase A** se ainda em aberto; **Fase B** continua dependente de **EA MQL5** (GOV-B6).
5. **Decisão Conselho pendente (opcional):** fallback **condicional** (Opção B técnica) vs manter fallback pleno — este registo apenas documenta o estado **actual** (fallback **activo**).

---

## 10. Path canónico deste registo

`SOURCE_CODE/governance/DOC-OFC-REGISTO-PSA-MUDANCAS-OPERACIONAIS-E-GOVERNANCA-20260518.md`

---

## 11. Registo de revisões deste documento

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| v1.0 | 2026-05-18 | Eng / Conselho | Emissão inicial — registo consolidado pós-push `e449cc8`. |

---

*Fim do registo PSA v1.0.*
