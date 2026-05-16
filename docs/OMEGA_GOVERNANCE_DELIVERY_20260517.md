# OMEGA — Pacote de governança e entrega técnica (2026-05-17)

**Classificação:** interno OMEGA — anexo operacional (checklist)  
**Fonte canónica de governança (prevalece em caso de divergência):**  
`governance/DOC-OFC-REGISTO-ALINHAMENTO-DOCUMENTAL-SHADOW-PAPER-OIS-20260517.md`  

**Referências cruzadas:** OIS-CEO-PRIORITIES-20260517 · OIS-CIO-FINAL-ASSESSMENT-20260517 · OIS-CIO-AGENT-DELIVERY-ASSESSMENT-20260517  

Este ficheiro em `docs/` existe para **acesso rápido** ao checklist e ao resumo técnico. **Regras, anti-contaminação bilateral e ponto de restauração Git** estão no **DOC-OFC** indicado acima — não duplicar decisões novas só aqui; actualizar primeiro o canal `governance/`.

Este documento descreve o que foi **entregue em código** e o que permanece **governação / evidência em ambiente real**, para auditoria pelo Conselho e PSA.

---

## 1. Componentes versionados (código)

| Componente | Ficheiro | Função |
|------------|----------|--------|
| Motor shadow/paper | `core_engines/shadow_loop.py` | KS ignora streak em **10018**; `classify_cycle_exit_reason`; `paper_summary` + `cycle_exit.json`; `evaluation_timeline.jsonl`; logs `[CYCLE_EXIT]` / `[EVAL_CONTEXT]`; correcção MT5 offline sem `ks` indefinido |
| Calendário e peso de evidência | `core_engines/omega_evaluation_context.py` | Regra **OIS-EVAL-CALENDAR-v1**: UTC, dia PT, semana ISO, `evidence_tier`, `evidence_weight` (tabela fixa); override opcional `OMEGA_EVAL_EVIDENCE_WEIGHT_OVERRIDE` |
| Runner 24x7 | `scripts/omega_paper_loop_24x7.py` | Lock **O_EXCL** + PID; aviso se `OMEGA_RUNNER_MAX_PARALLEL=0`; `[EVAL_CONTEXT] runner_cycle=`; validação **EURUSD + XAUUSD + BTCUSD** obrigatória |
| Inventário estático | `scripts/OMEGA_AUDIT_ENGINE.py` | `--root`, `--no-strict`, `--out-dir` (exclui `venv` / `site-packages` / etc.) |
| Synthesis CEO | `audit/CEO_SYNTHESIS_OMEGA_INTELLIGENCE_AUDIT_20260517.md` | Decisões, pendências, regra de peso |

**Execução:** modo paper/shadow requer `PYTHONPATH` = raiz `SOURCE_CODE` (o runner define ao subprocessar).

---

## 2. O que não fecha só com Git (evidência operacional)

| Item | Responsável | Evidência esperada |
|------|-------------|-------------------|
| Paper 24 h (sábado / segunda) | CEO / PSA | Logs + `cycle_exit.json` + Journal MT5 |
| Cruzamento forense | PSA | Timeline + retcodes / comentários broker |
| Ratificação pesos 0.92 / 0.42 / 0.38 | Conselho | Acta ou nova versão `OIS-EVAL-CALENDAR-v*` |
| Módulo horário operacional | Tech Lead | Especificação + código (pendência na synthesis) |
| Observabilidade externa | DevOps | Roadmap (opcional) |

---

## 3. Checklist pós–paper 24 h (governação)

Preencher **Sim / Não / N/A**. Caminhos relativos à raiz `SOURCE_CODE`.

| # | Critério | Sim/Não | Onde |
|---|----------|---------|------|
| A1 | Arranque sem `[STARTUP_BLOCK]` | | `audit/paper/omega_24x7_runner.log` |
| A2 | Lock singleton respeitado | | `audit/paper/omega_runner.lock` + log |
| A3 | `EVAL_CONTEXT` por volta runner | | `grep` / `Select-String` em `omega_24x7_runner.log` |
| B1 | `exit_reason` + calendário no summary | | `audit/paper/paper_summary.json` |
| B2 | `cycle_exit.json` alinhado ao último run | | `audit/paper/cycle_exit.json` |
| B3 | `evaluation_timeline.jsonl` actualizado | | `audit/paper/evaluation_timeline.jsonl` |
| B4 | Log do motor por run | | campo `log_file` dentro de `paper_summary.json` |
| C1 | KS não disparou por streak só com **10018** | | logs + Journal |
| C2 | Se KS activo, motivo auditável | | `cycle_exit.json` + Journal |
| D1 | Cruzamento com Journal MT5 | | manual |
| E1 | Peso fim‑de‑semana reconhecido (`WEEKEND_PARTIAL`) | | `paper_summary.json` → `evaluation_calendar_run_end` |
| F1 | Peso ratificado ou follow-up aberto | | acta Conselho |

---

## 4. Comando paper sábado (mínimo — inclui EURUSD obrigatório)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
# ... variáveis OMEGA_* conforme CIO ...
python scripts/omega_paper_loop_24x7.py --mode paper `
  --ativos BTCUSD ETHUSD SOLUSD XRPUSD XAUUSD EURUSD `
  --timeframes H1 M15 H4 --bars 12000
```

**Nota:** sem `EURUSD` o runner bloqueia por desenho (`ASSETS_REQUIRED`).

---

## 5. Relação com outros protocolos

- **`OMEGA_AUDIT_PROTOCOL.md`** (raiz): protocolo de auditoria de módulos PSA/CURSOR — complementar a este pacote; não substitui evidência de paper.

---

*Documento gerado para versionamento em Git no âmbito OMEGA Investment Systems.*
