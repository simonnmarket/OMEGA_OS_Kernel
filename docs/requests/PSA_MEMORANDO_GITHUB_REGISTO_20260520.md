# MEMORANDO — PSA / REGISTO E GITHUB

**ID:** PSA-MEMO-20260520-OMEGA-P0  
**De:** Tech Lead / Engenharia OMEGA (via Agente Cursor)  
**Para:** PSA — Processamento, Arquivo e Integração  
**CC:** CEO, CKO, Conselho de Administração  
**Data:** 2026-05-20  
**Assunto:** Pedido formal — commit GitHub, registo de memória institucional e apoio à validação P0

---

## 1. BLUF

A Engenharia implementou no repositório local os **4 mandatos P0** do documento `OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX` e criou a pasta canónica `docs/conselho_arquivo/`. Solicita-se à **PSA** que execute o **commit/push GitHub**, registe o pacote na **memória institucional** (governança DOC-OFC) e, se possível, apoie a **validação demo MT5** pós-patch.

---

## 2. ENTREGÁVEIS NO REPOSITÓRIO (prontos para commit)

| Caminho | Conteúdo |
| --- | --- |
| `docs/conselho_arquivo/OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX.md` | Documento CKO arquivado |
| `docs/conselho_arquivo/COMPONENT_HEALTH_MATRIX.md` | Matriz componente × status |
| `docs/conselho_arquivo/README.md` | Índice do arquivo Conselho |
| `docs/requests/OMEGA_RCV_20260520_P0_ARQUITECTURAL_FIX_ANALISE.md` | Análise técnica |
| `docs/requests/OMEGA_DESKTOP_AUDITORIA_ANALISE_20260520_v3.md` | Histórico Desktop |
| `core_engines/shadow_loop.py` | Mandatos M1–M4 |
| `scripts/run_omega_24x7.ps1` | Modo diagnóstico CKO |
| `scripts/omega_component_health_matrix.py` | Auditoria componentes |
| `audit/component_health/component_health_20260520.json` | Snapshot JSON |
| `docs/conselho_arquivo/desktop_originais_20260520/*.txt` | 4 documentos Desktop CEO (espelho) |
| `docs/conselho_arquivo/CEO_MANUAL_INICIO_OPERACOES.md` | Runbook CEO pós-commit |

**Origem Desktop (CEO confirmou 4 ficheiros ainda presentes):**  
`C:\Users\Lenovo\Desktop\File Desktop\Arquivos Pendentes Auditoria\Pendente\Auditoria\`

---

## 3. TAREFAS SOLICITADAS À PSA

**Sequência acordada com CEO:** PSA conclui T1–T2 (+ memória) **antes** do CEO iniciar MT5/runner na máquina local.

### T1 — GitHub (obrigatório)

```bash
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git status
git add docs/conselho_arquivo/ docs/requests/OMEGA_RCV_* docs/requests/OMEGA_DESKTOP_* docs/requests/PSA_MEMORANDO_*
git add docs/conselho_arquivo/desktop_originais_20260520/
git add core_engines/shadow_loop.py scripts/run_omega_24x7.ps1 scripts/omega_component_health_matrix.py
git add audit/component_health/component_health_20260520.json
git commit -m "fix(execution): RCV P0 mandatos CKO + matriz componentes + arquivo conselho"
git push origin HEAD
```

**Branch sugerida:** `fix/rcv-p0-execution-20260520` (PR para `main` com revisão Conselho).

### T2 — Registo memória / governança

- Indexar `OMEGA-RCV-20260520-P0` em `governance/DOC-OFC-REGISTO-PSA-MUDANCAS-OPERACIONAIS-E-GOVERNANCA-20260518.md` (secção P0 Execução).
- Marcar **GAP-02** (`risk_config` efectivo) como dependência do patch ATR (Cenário B CKO).

### T3 — Validação demo (se PSA tiver acesso MT5)

1. Backup + remover `audit/risk/ks_daily_anchor.json` (Opção B CKO) — **só com OK CEO**.
2. MT5 demo aberto → `scripts/run_omega_24x7.ps1`.
3. Confirmar nos primeiros 5 min em `audit/paper/omega_24x7_runner.log`:
   - `[EQUITY] Equity MT5 real: $...`
   - `[MOMENTUM_FALLBACK] DISABLED`
   - Eventual `SKIP_SPREAD_GUARD` / `SKIP_ROLLOVER_BLACKOUT` (prova gates activos)
   - `ATOMIC_EXEC: order_check INVALID_STOPS` em símbolo com SL inválido (teste controlado)
4. Regenerar matriz: `python scripts/omega_component_health_matrix.py --md docs/conselho_arquivo/COMPONENT_HEALTH_MATRIX.md`

### T4 — Apoio opcional à Engenharia

- Cruzar `decision_trace.jsonl` com matriz de componentes (skips por gate).
- Entregar `OMEGA_DIAGNOSTIC_risk_config_EFFECTIVE_20260520.json` (GAP-02).

---

## 4. O QUE A PSA **NÃO** DEVE ASSUMIR SEM EVIDÊNCIA

- Sistema “operacional” em produção — apenas **código** alterado; restart depende validação demo.
- Win rate ou PnL — requer 24h pós-gates com trace limpo.

---

## 5. RESPOSTA ESPERADA DA PSA

1. URL do commit/PR GitHub  
2. ID de registo DOC-OFC  
3. **Mensagem explícita:** `CEO_AUTORIZADO_INICIAR_DEMO` (sim/não + motivo)  
4. Data prevista GAP-02  

**Nota:** Validação MT5 no Passo T3 pode ser feita pela PSA **ou** pelo CEO usando `docs/conselho_arquivo/CEO_MANUAL_INICIO_OPERACOES.md` — não duplicar start em duas máquinas ao mesmo tempo.

---

## 6. CONTACTO / ESCALAÇÃO

Se a PSA precisar de apoio do Agente Cursor: CEO pode autorizar sessão com acesso ao repo e logs MT5.

---

*Memorando gerado 2026-05-20 — nível 1 código; nível 4 execução pendente validação humana.*
