# DOC-OFC — Registo de alinhamento documental (shadow / paper / OIS 20260517)

**ID:** `DOC-OFC-REGISTO-ALINHAMENTO-DOCUMENTAL-SHADOW-PAPER-OIS-20260517`  
**Tipo:** registo oficial de governança (canal `governance/`, não substituível por instruções informais)  
**Data:** 2026-05-17  
**Referências:** OIS-CEO-PRIORITIES-20260517 · OIS-CIO-FINAL-ASSESSMENT-20260517 · OIS-CIO-AGENT-DELIVERY-ASSESSMENT-20260517  

---

## 1. Finalidade (anti-contaminação e anti-conflito bilateral)

Este documento fixa **um único ponto de verdade** no repositório para a entrega **shadow_loop / omega_paper_loop_24x7** associada às decisões OIS de 2026-05-17, de modo a:

1. **Evitar supra-informações bilaterais** — ordens ou resumos fora do Git que contradizem o estado versionado não prevalecem sobre este registo sem novo **DOC-OFC** ou ordem CEO explícita.
2. **Permitir restauração cognitiva** — qualquer interveniente pode regressar a este ficheiro + ao commit indicado para saber **o que foi decidido, o que foi codificado e o que ficou pendente de evidência**.
3. **Separar canais:** a pasta `governance/` e o prefixo **`DOC-OFC-`** são o canal **oficial** de governança OMEGA (SOP alinhado a `verify_governance_refs.py`). Outros caminhos (`docs/`, chat, e-mail) são **auxiliares**; em caso de divergência, **prevalece este DOC-OFC** e o commit Git referenciado.

---

## 2. Ponto de restauração (Git)

| Campo | Valor |
|--------|--------|
| Repositório remoto | `https://github.com/simonnmarket/OMEGA_OS_Kernel` |
| Branch de integração | `feature/nebular-integration-phase1` |
| Commit de entrega (baseline técnica) | `fba65ab` — mensagem: `governance(omega): KS 10018 streak skip, exit reason, runner lock, eval calendar` |

**Nota:** merges posteriores podem avançar o `HEAD`; para auditoria, usar `git show fba65ab` como baseline da entrega OIS-20260517.

**Cadeia de commits (entrega documentada — `feature/nebular-integration-phase1`):**

| Commit | Conteúdo |
|--------|-----------|
| `fba65ab` | Código: KS 10018, exit reason, lock, inventário, synthesis inicial |
| `63a3600` | DOC-OFC + índice `governance/README.md` v2.5 + manifesto + anexo `docs/` subordinado |
| `2f7d378` | Secção 5: pendência memorando PSA (registo CEO) |
| `ba885e9` | Secção 8: declaração de encerramento do pacote (CEO); secção 5 refinada (PSA só no fecho do dia) |
| `79bab70` | DOC-OFC: actualização da tabela de commits (governance) |
| `41e75f6` | Pacote modular `modules/omega_audit/` + `scripts/omega_audit_cli.py` integrados no Git |
| `3a7bdad` | `config/omega_asset_schedule.json` + `modules/omega_asset_schedule.py` |
| `55b4c37` | `modules/mt5_position_tag.py` — comentários / posições rastreadas |
| `5adcf6f` | `main.py` — resolução de ativos via calendário na entrada shadow; comentários MT5 |
| `65a5b89` | `shadow_loop` / `omega_paper_loop_24x7` / `OMEGA_AUDIT_ENGINE` / `risk_valves_v31` (OIS-20260517) |
| `cdae393` | Bytecode `.pyc` removido do índice Git; `.gitignore` para estado runtime em `audit/paper/` |

*Selo temporal de encerramento CEO (secção 8): usar o commit Git mais recente que alterou este ficheiro com a secção 8 presente (`git log -1 -- governance/DOC-OFC-REGISTO-ALINHAMENTO-DOCUMENTAL-SHADOW-PAPER-OIS-20260517.md`). Para a **cadência técnica** de integração Git acima, usar `git show <hash>` por linha.*

---

## 3. Artefactos de código e documentação (resumo)

| Componente | Local no repositório |
|------------|----------------------|
| Motor | `core_engines/shadow_loop.py` — KS ignora streak em **10018**; `classify_cycle_exit_reason`; `cycle_exit.json`; `evaluation_timeline.jsonl`; logs `[CYCLE_EXIT]` / `[EVAL_CONTEXT]`; correcção ramo MT5 offline |
| Calendário / peso de evidência | `core_engines/omega_evaluation_context.py` — regra **OIS-EVAL-CALENDAR-v1** |
| Runner 24x7 | `scripts/omega_paper_loop_24x7.py` — lock **O_EXCL** + PID; `[EVAL_CONTEXT]` por ciclo; validação **EURUSD + XAUUSD + BTCUSD**; fallback de lista de ativos via calendário quando sem `--ativos` / env |
| Inventário (legado CLI) | `scripts/OMEGA_AUDIT_ENGINE.py` — deprecado em favor do pacote modular |
| Pacote audit Tier-0 | `modules/omega_audit/` + `scripts/omega_audit_cli.py` — baseline SHA3, pré-ciclo, registo forense |
| Calendário de ativos (24/7 + classes) | `config/omega_asset_schedule.json` + `modules/omega_asset_schedule.py` — telemetria `audit/paper/asset_schedule.jsonl` |
| Synthesis CEO (anexo técnico) | `audit/CEO_SYNTHESIS_OMEGA_INTELLIGENCE_AUDIT_20260517.md` |
| Anexo operacional em `docs/` | `docs/OMEGA_GOVERNANCE_DELIVERY_20260517.md` — **subordinado** a este DOC-OFC; mantém checklist útil; alterações de **regra** devem reflectir-se primeiro aqui |

---

## 4. Trilhos pós-code-freeze (não bloqueiam arranque técnico)

Estes itens **não** são pré-requisitos para continuar desenvolvimento na branch de integração após a cadência Git `41e75f6`…`cdae393` (secção 2). São **evidência operacional** ou **governança institucional** com calendário próprio.

- **Paper 24 h + Journal MT5** — runbook e critérios em `docs/OMEGA_GOVERNANCE_DELIVERY_20260517.md` §3; artefactos esperados listados em `governance/MEMORANDO_PSA_HANDOVER_OIS-20260517.md` §4.
- **Ratificação formal dos pesos** `0.92 / 0.42 / 0.38` — baseline de engenharia **OIS-EVAL-CALENDAR-v1** já em código; Conselho pode emitir `v*` ou acta sem bloquear merges técnicos.
- **Módulo único `omega_session_clock`** — backlog **P1** (especificação no sprint seguinte).

### 4.1 Quadro de estado (síntese — 2026-05-17 fim de sessão técnica)

| Item | Estado | Nota |
|------|--------|------|
| **Memorando PSA** | **FECHADO** | `governance/MEMORANDO_PSA_HANDOVER_OIS-20260517.md` |
| **Pacote audit modular + CLI no Git** | **FECHADO** | commits `41e75f6` … `cdae393` |
| **Paper 24 h + evidência MT5** | **Trilho operacional** | Primeira janela útil quando CEO autorizar; não bloqueia código |
| **Ratificação dos pesos** | **Institucional** | Não bloqueia código; alteração só com novo DOC-OFC ou acta |
| **`omega_session_clock`** | **Backlog P1** | Especificação dedicada |
| **Working tree “limpo” global** | **Parcial** | Fora do âmbito OIS: triagem contínua em PRs temáticos (ver memorando §3) |

---

## 5. Memorando PSA — handover técnico (registo de memória auditável)

**Estado:** `FECHADO` (2026-05-17 — ordem CEO: encerramento sem pendência técnica bloqueante para domingo / arranque seguinte).

**Documento:** `governance/MEMORANDO_PSA_HANDOVER_OIS-20260517.md` — contém lista de commits da cadência técnica, runbook Paper 24 h, e delimitação do que ficou fora do handover (ruído local / outros domínios).

**Efeito:** o agente PSA dispõe de **pacote único** referenciado no Git para auditoria futura da linha OIS-20260517, sem dependência de “fecho da noite” adicional para o núcleo código+OFC aqui descrito.

---

## 6. Procedimento em caso de novo comando que “contradiga” este registo

1. **Não** implementar silenciosamente: abrir issue / PR com referência a este ID.  
2. Se o comando for válido, emitir **novo DOC-OFC** ou actualização CEO que **revogue ou emende** explicitamente a secção afecta.  
3. Actualizar `governance/README.md` e regenerar `MANIFESTO_DOCUMENTOS.json` com `python scripts/verify_governance_refs.py --write-manifest`.

---

## 7. Assinatura documental

**Estado:** `ACTIVO` — documento integrado no índice de governança OMEGA (`governance/README.md`) e no manifesto JSON.

---

## 8. Declaração de encerramento do pacote (CEO — 2026-05-17)

**Âmbito:** entrega **OIS-20260517** (motor `shadow_loop`, runner, calendário de evidência, inventário, synthesis, canal `DOC-OFC`, anexo `docs/`, commits listados na secção 2).

**Declarado:**

1. O pacote encontra-se **implementado e versionado** na branch `feature/nebular-integration-phase1`, incluindo a cadência técnica `41e75f6`…`cdae393` (secção 2) e a actualização deste DOC-OFC com memorando PSA em `governance/MEMORANDO_PSA_HANDOVER_OIS-20260517.md`.
2. **Não** há pendências **obrigatórias** dentro deste DOC-OFC que bloqueiem continuação técnica ou arranque pós‑fim‑de‑semana: memorando PSA (secção 5) encontra-se **fechado**; núcleo `omega_audit` + CLI + calendário de ativos + integrações listadas estão **no Git**.
3. Itens em **trilhos pós-code-freeze** (secção 4) — paper 24 h com evidência MT5, ratificação formal de pesos pelo Conselho, módulo `omega_session_clock`, ecossistema secundário MT5 — seguem com **calendário operacional / institucional próprio** e **não** contam como atraso da entrega código+OFC nem como bloqueio de merge da linha OIS-20260517.

**Efeito:** evita ambiguidade de “supra-informação” — o estado oficial do pacote OIS-20260517 é o Git + este documento; alterações futuras exigem novo registo ou DOC-OFC.

---

*Documento OMEGA Investment Systems — canal oficial `DOC-OFC`.*
