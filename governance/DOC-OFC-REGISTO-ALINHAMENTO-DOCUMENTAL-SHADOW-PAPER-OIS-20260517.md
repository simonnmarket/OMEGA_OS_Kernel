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

---

## 3. Artefactos de código e documentação (resumo)

| Componente | Local no repositório |
|------------|----------------------|
| Motor | `core_engines/shadow_loop.py` — KS ignora streak em **10018**; `classify_cycle_exit_reason`; `cycle_exit.json`; `evaluation_timeline.jsonl`; logs `[CYCLE_EXIT]` / `[EVAL_CONTEXT]`; correcção ramo MT5 offline |
| Calendário / peso de evidência | `core_engines/omega_evaluation_context.py` — regra **OIS-EVAL-CALENDAR-v1** |
| Runner 24x7 | `scripts/omega_paper_loop_24x7.py` — lock **O_EXCL** + PID; `[EVAL_CONTEXT]` por ciclo; validação **EURUSD + XAUUSD + BTCUSD** |
| Inventário | `scripts/OMEGA_AUDIT_ENGINE.py` |
| Synthesis CEO (anexo técnico) | `audit/CEO_SYNTHESIS_OMEGA_INTELLIGENCE_AUDIT_20260517.md` |
| Anexo operacional em `docs/` | `docs/OMEGA_GOVERNANCE_DELIVERY_20260517.md` — **subordinado** a este DOC-OFC; mantém checklist útil; alterações de **regra** devem reflectir-se primeiro aqui |

---

## 4. O que não é fechado por Git (evidência obrigatória)

- Paper prolongado (24 h) e cruzamento com **Journal MT5**.
- Ratificação formal dos **pesos** `0.92 / 0.42 / 0.38` pelo Conselho (ou nova versão `OIS-EVAL-CALENDAR-v*`).
- Módulo único de **horário operacional** (pendência na synthesis).

---

## 5. Procedimento em caso de novo comando que “contradiga” este registo

1. **Não** implementar silenciosamente: abrir issue / PR com referência a este ID.  
2. Se o comando for válido, emitir **novo DOC-OFC** ou actualização CEO que **revogue ou emende** explicitamente a secção afecta.  
3. Actualizar `governance/README.md` e regenerar `MANIFESTO_DOCUMENTOS.json` com `python scripts/verify_governance_refs.py --write-manifest`.

---

## 6. Assinatura documental

**Estado:** `ACTIVO` — documento integrado no índice de governança OMEGA (`governance/README.md`) e no manifesto JSON.

---

*Documento OMEGA Investment Systems — canal oficial `DOC-OFC`.*
