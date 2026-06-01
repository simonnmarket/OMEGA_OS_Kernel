# AIC — Acta de incidente: falhas críticas após auditorias “APROVADO”

| Campo | Valor |
|-------|--------|
| **ID** | INC-AUDIT-20260525-001 |
| **Data** | 2026-05-25 |
| **Classificação** | Incidente de governança + gap de integração (não regressão P0 isolada) |
| **Severidade** | Alta — decisão DEMO desalinhada com objectivo CEO (IA como bússola) |
| **Estado** | **FECHADO** — INTEGRAÇÃO PASS (PSA 2026-05-25, HEAD `f51b087`) |
| **Responsável fecho** | PSA + CEO (reinício runner + gate integração) |

---

## 1. Resumo executivo (CEO)

As auditorias **Chave de Ouro**, **P0-ABC**, **Fase 1 Router** e **go-live DEMO** foram **válidas no âmbito em que foram pedidas**.  
Elas **não** incluíam verificação de **um único ecossistema de decisão** (PSA + Orquestrador + Fusão + runner 16 ativos + limite de posições).

O sistema **corria** (runner saudável, 2 ordens crypto, magic correcto), mas com **motores em conflito**:

| Sintoma em runtime | Causa raiz |
|--------------------|------------|
| `PSA_FEED BUY` no log + Orquestrador `HOLD` | Dois núcleos sem fusão activa / shadow mode |
| Entradas só `MOMENTUM_MT5` | IA em HOLD; fallback era a única via de execução |
| Portfolio IA ~7 ativos vs runner 16 | `priority_assets` sessão OVERLAP desalinhado |
| `max_positions=2` (IA) vs `8` (runner) | Calibrador vs `run_omega_24x7.ps1` |
| Relatórios “APROVADO” | Métrica = pytest + smoke 1 ativo + runner OK |

**Conclusão:** Não é fraude de código nos testes P0; é **falha de processo** — fecho de sprint confundido com fecho de **integração Tier-0**.

---

## 2. Cronologia

| Momento | Evento |
|---------|--------|
| Sprint P0 + Fase 1 | pytest 34/34, smokes EURUSD/XAUUSD, PRs #1 #2 |
| Chave de Ouro | Documento declara “Produção 24×7 Tier-0 plena” = **baixa confiança** |
| Go-live DEMO | `omega_demo_go_live.ps1` PASS; runner 16 símbolos |
| PSA relatório ~21:54 | Runner OK; ETH/XRP trailing; HEAD `ffa9fdc` / anterior |
| Análise log 24×7 | ~762 HOLD IA, ~504 EDGE_GATE; 0× `AGENT_IA` exec; 2× momentum |
| Pacote unificado | `omega_ecosystem_unified.py` + envs em `run_omega_24x7.ps1` |
| **Pendente** | Reinício runner com código unified + gate integração |

---

## 3. O que cada auditoria validou vs o que faltou

### 3.1 Validado (manter como PASS — não reabrir P0)

- ATR por TF do sinal (`get_execution_tf_atr`)
- `partial_taken` no ledger
- Comment MT5 ≤31 chars, magic `234001`
- `is_market_open`, schedule T-W1/T-W2
- pytest 34/34
- Runner não crasha; `[SCHEDULE]` 16 ativos

### 3.2 Não validado (origem do incidente)

| ID | Item | Porque passou |
|----|------|----------------|
| GAP-1 | Fusão PSA+OMEGA em modo live | `OMEGA_USE_SIGNAL_FUSION` / `PSA_SHADOW_MODE` fora do checklist |
| GAP-2 | Portfolio IA = portfolio runner | Smokes usam 1–2 ativos |
| GAP-3 | `max_positions` único no stack | Nunca stress-test com 8 posições IA |
| GAP-4 | `% execuções `AGENT_IA` vs `MOMENTUM_MT5` | Sucesso = “houve ordem” |
| GAP-5 | Manifesto `ecosystem_unified_manifest.json` | Ficheiro não existia antes do patch |
| GAP-6 | Comunicação CEO | “APROVADO sprint” lido como “ecossistema integrado” |

---

## 4. Evidências (referência)

| Evidência | Caminho |
|-----------|---------|
| Log runner 24×7 | `audit/paper/omega_24x7_runner.log` |
| Relatório Chave de Ouro (baixa confiança 24×7) | `governance/AIC_VALIDACAO_CHAVE_OURO_SPRINT_20260525.md` §4 |
| Registo fallback momentum (decisão histórica) | `governance/DOC-OFC-REGISTO-PSA-MUDANCAS-OPERACIONAIS-E-GOVERNANCA-20260518.md` §7 |
| CEO ecossistema | `governance/CEO_ECOSISTEMA_UNIFICADO_20260525.md` |
| Manifesto pós-reinício | `audit/paper/ecosystem_unified_manifest.json` |

---

## 5. Acções correctivas (permanentes)

| ID | Acção | Dono | Estado |
|----|-------|------|--------|
| CA-1 | Gate integração obrigatório antes de “DEMO OK” | AIC | Doc: `GATE_INTEGRACAO_ECOSISTEMA_OBRIGATORIO_20260525.md` |
| CA-2 | Script `scripts/omega_integration_gate.ps1` | AIC | Implementado |
| CA-3 | Comando PSA definitivo (reinício + validação 1h) | AIC | `PSA_COMANDO_DEFINITIVO_ECOSISTEMA_20260525.md` |
| CA-4 | Separar vereditos: **Sprint P0 FECHADO** ≠ **Integração FECHADA** | AIC+PSA | Esta acta |
| CA-5 | PSA reiniciar runner com HEAD ≥ pacote unified | PSA | **Concluído** |
| CA-6 | Relatório 1h pós-reinício com KPIs decisão | PSA | **Concluído** — `PSA_RELATORIO_INTEGRACAO_ECOSISTEMA_20260525.md` |

---

## 6. O que NÃO fazer (evitar repetir o ciclo)

1. **Não** marcar “resolvido” só com pytest 34/34.  
2. **Não** remover `OMEGA_ECOSYSTEM_UNIFIED=1` nem repor `max_positions=2` / lista 7 ativos no calibrador.  
3. **Não** activar `PSA_SHADOW_MODE=1` em DEMO discovery (mata confluência PSA quando Omega HOLD).  
4. **Não** substituir gate integração por smoke single-asset.  
5. **Não** confundir “momentum executou” com “IA é a bússola”.

---

## 7. Critério de fecho do incidente

Incidente **FECHADO** — checklist cumprido (2026-05-25):

- [x] `git pull` — `modules/omega_ecosystem_unified.py` presente  
- [x] Runner reiniciado via `scripts/run_omega_24x7.ps1`  
- [x] `omega_integration_gate.ps1` → PASS (preflight + runtime + kpi)  
- [x] Log: `[ECOSYSTEM_UNIFIED] manifesto=` @ 23:33:30  
- [x] Manifesto: 16 ativos, `max_positions`: 8  
- [x] KPI amostra: PSA_FEED 232, AGENT_IA 46, MOMENTUM 60, EDGE 106  
- [x] `governance/PSA_RELATORIO_INTEGRACAO_ECOSISTEMA_20260525.md`

---

## 8. Assinaturas / registo

| Papel | Acção |
|-------|--------|
| AIC | Acta emitida — gap documentado |
| CEO | Autoriza execução PSA conforme comando definitivo |
| PSA | Executa + reporta checklist §7 |

---

*AIC — Incidente INC-AUDIT-20260525-001 — Não reabre sprint P0; abre linha de integração Tier-0.*
