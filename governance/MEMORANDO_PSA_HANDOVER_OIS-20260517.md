# Memorando PSA — Handover técnico OIS-20260517 (encerramento 2026-05-17)

**Para:** PSA / arquivo institucional  
**De:** Engenharia (sessão Cursor) alinhada ao `DOC-OFC-REGISTO-ALINHAMENTO-DOCUMENTAL-SHADOW-PAPER-OIS-20260517`  
**Branch:** `feature/nebular-integration-phase1`

---

## 1. Resumo executivo

- O pacote modular **`modules/omega_audit/`** e **`scripts/omega_audit_cli.py`** passaram a estar **rastreados no Git** (pendência PSA §4.1 — resolvida).
- Calendário de ativos: **`config/omega_asset_schedule.json`** + **`modules/omega_asset_schedule.py`** — versionados.
- Entrada **shadow** via **`main.py`** usa `resolve_shadow_loop_assets`; comentários MT5 alinhados a **`modules/mt5_position_tag.py`**.
- Entrega **OIS-20260517** em código: **`core_engines/shadow_loop.py`** (gate audit Tier-0, exit reason, KS ignora **10018**), **`scripts/omega_paper_loop_24x7.py`** (lock), **`scripts/OMEGA_AUDIT_ENGINE.py`** (legado documentado), **`modules/risk_valves_v31.py`**.
- **Chore Git:** remoção de bytecode `.pyc` do índice; `.gitignore` com exclusão de estado runtime em `audit/paper/` (`cycle_exit.json`, `evaluation_timeline.jsonl`, `omega_runner.lock`).

---

## 2. Commits desta cadência (ordem cronológica)

| Curto | Mensagem |
|-------|----------|
| `41e75f6` | feat(audit): Tier-0 modular omega_audit package and omega_audit_cli |
| `3a7bdad` | feat(schedule): omega_asset_schedule JSON and resolver module |
| `55b4c37` | feat(mt5): position tag helpers for V2 comments and tracked positions |
| `5adcf6f` | feat(kernel): shadow uses asset schedule; MT5 comments via position tags |
| `65a5b89` | feat(ois-20260517): shadow_loop audit gate, cycle exit, KS 10018 skip; runner lock; risk valves; legacy audit doc |
| `cdae393` | chore(git): stop tracking bytecode; ignore paper runtime state files |
| `aa0ff4b` | governance(doc-ofc): fecho memorando PSA + actualização DOC-OFC + synthesis CEO |

*HEAD exacto após esta cadência: `aa0ff4b` (confirmar com `git rev-parse HEAD` no clone canónico).*

---

## 3. Fora do âmbito deste handover

Ficam de fora **alterações locais não OIS** (ex.: muitos `audit/paper/**/PaperReport_*.json`, pastas `agent_ia/**`, backups `*_BACKUP_*`, incidentes em `audit/`). Recomenda-se triagem em **PRs temáticos**; não bloqueiam a linha OIS-20260517 entregue acima.

---

## 4. Runbook — Paper 24h + MT5 (próxima janela operacional)

Não é pré-requisito para **code-freeze** desta data; é **evidência operacional** a recolher quando o CEO abrir a janela.

| Artefacto | Caminho (repo) |
|-----------|----------------|
| Log runner (quando existir) | `audit/paper/omega_24x7_runner.log` |
| Exit / calendário | `audit/paper/cycle_exit.json` |
| Sumário | `audit/paper/paper_summary.json` |
| Linha de tempo | `audit/paper/evaluation_timeline.jsonl` |
| Journal MT5 | Export manual → CSV (Account History) |

Critérios A1–F1: **`docs/OMEGA_GOVERNANCE_DELIVERY_20260517.md`** §3.

---

## 5. Ratificação de pesos e `omega_session_clock`

- **Pesos** `OIS-EVAL-CALENDAR-v1`: baseline de engenharia **em produção de código**; alteração institucional apenas por novo **DOC-OFC** ou acta Conselho (versão `v*`).
- **`omega_session_clock`:** backlog **P1** — especificação no sprint seguinte; **sem** dependência do merge desta cadência.

---

*Documento emitido para fecho da secção 5 do DOC-OFC (memorando PSA).*
