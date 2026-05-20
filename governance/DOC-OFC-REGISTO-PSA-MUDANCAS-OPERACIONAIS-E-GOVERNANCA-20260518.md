# Registo PSA — Mudanças operacionais e de governança (OMEGA QUANTUM LAB)

| Campo | Valor |
|-------|--------|
| **ID documento** | DOC-OFC-PSA-REGISTO-MUDANCAS-v1.1 |
| **Data emissão** | 2026-05-18 |
| **Para** | PSA Lead |
| **Cc** | CEO, Tech Lead, CKO, CIO |
| **Assunto** | Registo único de alterações recentes (bridge, trilho modo real, relógio de sessão, memorandos, flags 24/7, **teto SL por regime**) para arquivo e auditoria |
| **Branch** | `feature/nebular-integration-phase1` |
| **Repositório remoto** | `origin` (último push inclui commit `4875a67` na data deste registo) |

---

## 1. Finalidade deste documento

Centralizar para o **PSA** todas as mudanças **documentadas e persistidas em Git** que afectam:

- integração **Execution Bridge v2.2** e **runner Opção B**;
- **governança B6** (desbloqueio Opção A);
- **trilho modo real** (checklist Fase A, memorando de fecho, envio oficial);
- módulo **`omega_session_clock`** (Fase A A4);
- **operação 24/7** (reactivação do **MOMENTUM_FALLBACK**);
- **risco de execução — SL** (teto `OMEGA_SL_MAX_*` aplicado em todo o pipeline até `mt5_send_order`).

Evita dispersão por vários e-mails: este ficheiro é a **fonte canónica** do registo `DOC-OFC-PSA-REGISTO-MUDANCAS-v1.1`. Actualizações futuras: **editar este ficheiro** (Secção 11) — **não** duplicar com o mesmo ID.

---

## 2. Linha do tempo — commits (ordem anti-cronológica recente → mais antiga relevante)

| Commit | Resumo |
|--------|--------|
| `4875a67` | **Risco SL (CEO):** `core_engines/shadow_loop.py` — função `apply_regime_sl_cap`; teto `OMEGA_SL_MAX_*` após `sanitize_sl_tp` e após **Tesseract** XAU M5; SL da **IA** limitado a `_max_sl_pre`; cap em **`mt5_send_order`** após `min_dist+50` (evita SL 600+ pts em XAUUSD / commodity). |
| `3fe5a1a` | **Governança:** criação deste registo consolidado PSA (v1.0 inicial). |
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

## 7.1 Correcção — teto de stop-loss por regime (XAUUSD / commodity)

| Campo | Valor |
|-------|--------|
| **Commit** | `4875a67` |
| **Ficheiro** | `core_engines/shadow_loop.py` |
| **Problema** | SL em **600+ pontos** em XAUUSD: o teto `OMEGA_SL_MAX_METAL` (defeito **250** para `commodity`) aplicava-se só a `_pre_sl`; **IA** (`stop_loss_pips`), **`sanitize_sl_tp`** (piso ATR) e **Tesseract** podiam ignorar o teto; **`mt5_send_order`** ainda podia inflar com `min_dist + 50`. |
| **Correcção** | `apply_regime_sl_cap()`; cap após sanitize e após Tesseract; IA `min(ia_sl, _max_sl_pre)`; cap final no envio MT5 + log `[MT5_SEND_SL_CONFLICT]` se cap < distância mínima do broker. |
| **Ajuste fino** | Variável de ambiente **`OMEGA_SL_MAX_METAL`** (ex. `180`) — precedência via código existente de env. |
| **Ops** | `git pull` + **reiniciar** runner 24x7 para carregar o `shadow_loop.py` corrigido. |

---

## 8. Contexto operacional (registo — não alterado por commits isolados acima)

| Tema | Nota para PSA |
|------|----------------|
| **Motor V3 / 0xC0000005** | Crash de subprocess (ACCESS VIOLATION) reportado em **2026-05-16**; runner parou (“dados obsoletos proibidos”). **Não** é corrigido pelo commit `e449cc8`; exige RCA (WER, binário, inputs). |
| **Audit gate Tier-0** | Pré-ciclo (baseline SHA3, equity/DD, strict); **não** substitui monitorização de crash **durante** subprocess — lacuna já identificada pelo Conselho (watchdog / alerta). |
| **Modo** | `run_omega_24x7.ps1` mantém `OMEGA_24X7_MODE=paper` e parâmetros de risco conforme cabeçalho do script — **verificar** alinhamento com ordem CEO actual. |

---

## 9. Pedido de acções ao PSA

1. **Arquivar** este documento como `DOC-OFC-PSA-REGISTO-MUDANCAS-v1.1` (path Secção 10).
2. **Confirmar** no remoto os hashes da Secção 2 (`git fetch` + `git log`) — **incluir** `4875a67`.
3. **Validar** com Eng/Ops que o runner 24x7 foi **reiniciado** após `e449cc8` **e** após `4875a67` (código SL).
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
| v1.1 | 2026-05-18 | Eng / CEO | Secção 7.1 — correcção teto SL (`4875a67`); actualização Secção 2 e pedidos PSA; ID v1.1. |
| v1.2 | 2026-05-20 | PSA | Secção 12 — RCV P0 Mandatos CKO; commit `76af476`; branch `fix/rcv-p0-execution-20260520`. |
| v1.3 | 2026-05-20 | PSA/AIC | Secção 13 — Remediação CICC/CITIC; doc execução v3.0; veredito v1.1; pasta `aprovado_conselho_20260520/`. |

---

## 13. Remediação CICC/CITIC (2026-05-20)

| Campo | Valor |
|-------|--------|
| **ID** | OMEGA-CICC-REMEDIATION-20260520 |
| **Doc execução (canónico PSA)** | `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.0.md` |
| **Veredito Conselho** | `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` |
| **Aprovações** | `docs/conselho_arquivo/aprovado_conselho_20260520/` |
| **Forense** | `docs/conselho_arquivo/forensic_20260520/` + `audit/forensic/OMEGA_FORENSIC_AUDIT_20260520/` |
| **Branch prevista** | `fix/cicc-remediation-magic-mutex-20260520` |
| **Commit / PR** | _(preencher PSA após push)_ |
| **Relatório validação** | `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md` |
| **Estado** | **EM EXECUÇÃO** — v3.1 CEO; patch magic/mutex aplicado em SOURCE_CODE |
| **Doc v3.1** | `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` |

**Correcções P0:** magic `234001` em `mt5_send_order`; mutex `audit/.omega_system.lock` via `modules/omega_system_mutex.py`; logs `SKIP_*`; boot `[CIO-VERIFY]`; firebreak `INATIVO_ARQUIVADO_20260520`.

**Desktop CEO:** apenas índices `00_INDICE_*.md` — documentos operacionais arquivados no repo (2026-05-20).

---

## 12. RCV P0 — Mandatos CKO (2026-05-20)

| Campo | Valor |
|-------|-------|
| **ID** | OMEGA-RCV-20260520-P0 |
| **Ref memorando** | PSA-MEMO-20260520-OMEGA-P0 |
| **Branch** | `fix/rcv-p0-execution-20260520` |
| **Commit** | `76af476` |
| **Push** | `origin fix/rcv-p0-execution-20260520` |
| **PR GitHub** | https://github.com/simonnmarket/OMEGA_OS_Kernel/pull/new/fix/rcv-p0-execution-20260520 |
| **Autorização** | CEO (oral) 2026-05-20 |
| **Estado** | COMMITADO/PUSHED — aguarda validação demo MT5 (T3) |

### Mandatos implementados

| Mandato | Ficheiro | Descrição |
|---------|----------|-----------|
| M1 | `core_engines/shadow_loop.py` | Spread Guard — bloqueia ordem se spread > SL distance |
| M2 | `core_engines/shadow_loop.py` | Rollover Blackout — bloqueia abertura em ±5min de 00:00 UTC |
| M3 | `core_engines/shadow_loop.py` | MOMENTUM_FALLBACK DISABLED — signal_source=NULL não abre posições |
| M4 | `core_engines/shadow_loop.py` | INVALID_STOPS Guard — valida SL/TP vs SYMBOL_TRADE_STOPS_LEVEL |
| —  | `scripts/run_omega_24x7.ps1` | Modo diagnóstico CKO com flags de gate activos |

### Artefactos arquivados

| Artefacto | Caminho |
|-----------|---------|
| Documento RCV-P0 CKO | `docs/conselho_arquivo/OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX.md` |
| Matriz componentes | `docs/conselho_arquivo/COMPONENT_HEALTH_MATRIX.md` |
| Runbook CEO | `docs/conselho_arquivo/CEO_MANUAL_INICIO_OPERACOES.md` |
| 4 TXT Desktop CEO | `docs/conselho_arquivo/desktop_originais_20260520/*.txt` |
| Snapshot JSON | `audit/component_health/component_health_20260520.json` |

### GAP-02 (risk_config efectivo)
Marcado como dependência do patch ATR (Cenário B CKO). Resolução prevista: pós-validação demo T3 (extracção `shadow_loop.py` valores efectivos `sl_pct`, `tp_pct`, `kill_switch_threshold`, `circuit_breaker_threshold`).

---

---

## Secção 13 — Remediação CICC/CITIC — Magic + Mutex Global (2026-05-20)

| Campo | Valor |
|-------|-------|
| **ID** | OMEGA-PSA-EXEC-v3.1-20260520 |
| **Ref documento** | `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` |
| **Veredito** | `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` |
| **Branch** | `fix/cicc-remediation-magic-mutex-20260520` |
| **Autorização** | CEO 2026-05-20 — execução imediata |
| **Prazo** | 2026-05-21 12:00 UTC |
| **Estado** | COMMITADO/PUSHED — aguarda P0-VAL manhã |

### Problemas corrigidos (veredito CICC)

| Componente | Veredito | Correcção |
|------------|----------|-----------|
| IA / imports BAU | EXONERADO | — |
| Gates RCV (Spread, SL/TP) | EXONERADO | — |
| `magic` no request `mt5_send_order` | CONDENADO → CORRIGIDO | `"magic": int(os.getenv("OMEGA_MAGIC_NUMBER", "234001"))` em `shadow_loop.py:1358` |
| Mutex global (dois sistemas em paralelo) | CONDENADO → CORRIGIDO | `modules/omega_system_mutex.py` + integrado em `run_loop` |

### Ficheiros alterados

| Ficheiro | Acção |
|----------|--------|
| `modules/omega_system_mutex.py` | CRIADO — mutex global O_EXCL `audit/.omega_system.lock` |
| `modules/cio_boot_verify.py` | CRIADO — verificação boot CIO (magic presente no dict) |
| `core_engines/shadow_loop.py` | MODIFICADO — magic no request; mutex+CIO em `run_loop` |
| `scripts/omega_paper_loop_24x7.py` | MODIFICADO — `OMEGA_DIAGNOSTIC_MODE` relaxa gate portfolio |
| `scripts/run_omega_diagnostico_post_cicc.ps1` | CRIADO — modo diagnóstico madrugada (5 símbolos, risco 0.2%) |
| `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` | ARQUIVADO |
| `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` | ARQUIVADO |

### Provas de Fogo executadas

| Prova | Resultado |
|-------|-----------|
| P1 — Isolamento BAU | PASS — 0 contaminações nos 42 módulos OMEGA |
| P2A — Spread Guard | PASS — SKIP_SPREAD_GUARD bloqueou SL=2pts < 9pts |
| P2B — Magic no request | FAIL (pré-patch) → CORRIGIDO — magic=234001 confirmado |
| P3 — Mutex inter-processo | VULNERABILIDADE detectada → CORRIGIDA com mutex global |

### Parâmetros modo diagnóstico (restart madrugada)

| Env | Valor |
|-----|--------|
| `OMEGA_MAGIC_NUMBER` | 234001 |
| `OMEGA_RISK_PER_TRADE` | 0.002 |
| `OMEGA_DD_DAILY_MAX` | 0.05 |
| `OMEGA_MAX_POSITIONS` | 3 |
| `OMEGA_DIAGNOSTIC_MODE` | 1 |
| `OMEGA_LOOP_INTERVAL_SEC` | 30 |
| Ativos | EURUSD GBPUSD USDJPY XAUUSD BTCUSD |

### Validação P0-VAL (manhã 2026-05-21)

Critério PASS: 0% deals novas com magic=0; 100% magic=234001.  
Relatório: `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md`

---

*Fim do registo PSA v1.3.*
