# DOC-PARRF-PSA-TESTE-MOTOR-HISTORICO-2Y-GRAFICOS-V120-20260415

| Campo | Valor |
|--------|--------|
| **ID oficial** | `DOC-PARRF-PSA-TESTE-MOTOR-HISTORICO-2Y-GRAFICOS-V120-20260415` |
| **Versão** | 1.0.0 |
| **Data** | 2026-04-15 |
| **Estado** | **EXECUTÁVEL** — instruções para PSA |
| **Destinatário** | **PSA**, Tech Lead |
| **Objetivo** | Testar o “motor” sobre **histórico liberado**, gerar **gráfico de linhas** e **gráfico de velas (sintético)**, avaliar relatórios, cumprir **janela mínima de 2 anos** quando o dataset o permitir, e arquivar tudo na estrutura oficial + Git. |

---

## 1. Âmbito e limitações (honestidade técnica)

- **Gráfico de linhas:** série temporal `y` e `spread` (e curvas derivadas no `visualizer_tier0.py`).  
- **Gráfico em velas:** **OHLC sintético** derivado de `y` e `x` por barra (definição no script `motor_historico_2y_graficos_psa.py`). **Não** substitui feed OHLCV de mercado oficial; serve para **observação visual** do motor sobre o mesmo histórico.  
- **Janela ≥ 2 anos:** medida por `span_days = (max(ts) - min(ts))` em dias UTC. O ficheiro pode chamar-se `STRESS_2Y_*.csv` e **mesmo assim** cobrir menos tempo — **o gate é numérico**, não o nome do ficheiro.  
- **Evidência no repositório (nebular-kuiper, amostra verificada):** os CSV em `omega_core_validation\evidencia_pre_demo\02_logs_execucao\` apresentam **~103 dias** de span para **~100k** barras M1 — **abaixo de 730 dias**. Portanto, com `--min-days 730` o PSA deve esperar **exit code 1** até existir **dataset alargado** ou **excepção** assinada (ver secção 8).

---

## 2. Artefactos e módulos já liberados (paths oficiais)

| Papel | Localização |
|--------|-------------|
| **Dados STRESS** (origem) | `omega_core_validation\evidencia_pre_demo\02_logs_execucao\STRESS_2Y_SCALPING.csv`, `STRESS_2Y_DAY_TRADE.csv`, `STRESS_2Y_SWING_TRADE.csv` **ou** espelho em `Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao\` |
| **Cópia operacional** | `logs\STRESS_2Y_<PERFIL>.csv` (o script copia automaticamente) |
| **Motor visual + métricas equity** | `visualizer_tier0.py` — lê `logs\`, grava PNG e `Declaracoes\STRESS_TEST_METRICS.md` |
| **Gate motor + linha + velas** | `protocol\PSA\motor_historico_2y_graficos_psa.py` |
| **Auditoria recente (opcional pós-motor)** | `validar_fase7.py` sobre `omega_audit_PARRF_*.json` em `00_PROVAS_AUDITORIA\orchestrator_runs\` |
| **Provas deste teste** | `00_PROVAS_AUDITORIA\motor_historico_2y\` (PNG + `motor_historico_report_*.json`) |

---

## 3. Variáveis de ambiente

| Variável | Função |
|----------|--------|
| `OMEGA_PARRF_ROOT` | Raiz absoluta de `Auditoria PARR-F` no clone em uso (**obrigatório** no Desktop). O `visualizer_tier0.py` usa esta variável em vez de path fixo. |

---

## 4. Pré-requisitos

```powershell
cd <PARRF_AUDIT_TREE_ROOT>
pip install -r requirements-psa.txt
```

Inclui `pandas`, `matplotlib`, e demais dependências PSA já acordadas.

---

## 5. Procedimento PSA — teste completo (ordem)

### 5.1 Gate oficial de janela (≥ 730 dias)

```powershell
set OMEGA_PARRF_ROOT=<caminho absoluto para Auditoria PARR-F>
python protocol/PSA/motor_historico_2y_graficos_psa.py --min-days 730
```

- **Exit 0:** todos os perfis com `span_days >= 730` e gráficos gerados.  
- **Exit 1:** pelo menos um perfil abaixo do mínimo — **registar na ata** com valores de `motor_historico_report_*.json`.

### 5.2 Execução de observação (dataset actual ~103 dias) — só com ata explícita

Se o Conselho autorizar **teste de motor sem cumprir 2 anos** (ex.: até chegar dataset longo):

```powershell
python protocol/PSA/motor_historico_2y_graficos_psa.py --min-days 90 --run-visualizer
```

- Gera **linha** + **velas sintéticas** + relatório JSON.  
- `--run-visualizer` chama `visualizer_tier0.py` (equity + métricas em `Declaracoes\Assets\` e `STRESS_TEST_METRICS.md`).

**Na ata:** declarar *“Gate 730d NÃO aplicado; execução 5.2 com `--min-days 90` por autorização [assinatura].”*

### 5.3 (Opcional) Orquestrador seco + validação de audits

```powershell
python protocol/PSA/smoke_orchestrator_l07.py --runs 3
python validar_fase7.py 00_PROVAS_AUDITORIA\orchestrator_runs
python protocol/PSA/validate_audit_batch.py --schema Conselho/AUDIT_JSON_SCHEMA_V1.0.json --glob "00_PROVAS_AUDITORIA/orchestrator_runs/omega_audit_PARRF_*.json" --max 200 --json-summary 00_PROVAS_AUDITORIA/l04_pos_motor.json
```

---

## 6. Saídas obrigatórias para arquivo

| Artefacto | Descrição |
|-----------|-----------|
| `00_PROVAS_AUDITORIA/motor_historico_2y/motor_historico_report_*.json` | Métricas `span_days`, flags `span_gate_ok`, paths PNG |
| `00_PROVAS_AUDITORIA/motor_historico_2y/LINE_*.png` | Gráfico **linha** (pré-processado para plot) |
| `00_PROVAS_AUDITORIA/motor_historico_2y/CANDLES_SYNTH_*.png` | Gráfico **velas sintéticas** |
| `Declaracoes/Assets/EQUITY_*.png` | Se `--run-visualizer` |
| `Declaracoes/STRESS_TEST_METRICS.md` | Se `--run-visualizer` |

---

## 7. GitHub

1. `git status` — confirmar **sem** CSV/DSN com segredos extra.  
2. Adicionar: `Conselho\DOC-PARRF-PSA-TESTE-MOTOR-HISTORICO-2Y-GRAFICOS-V120-20260415.md`, `protocol\PSA\motor_historico_2y_graficos_psa.py`, alterações a `visualizer_tier0.py`, `requirements-psa.txt`, provas em `00_PROVAS_AUDITORIA\motor_historico_2y\`, `Declaracoes\` se aplicável.  
3. `git commit` + `git push` com mensagem referenciando este **ID**.

---

## 8. Critérios de aceite (resumo)

| Critério | PASS |
|----------|------|
| Gráfico linha gerado para cada perfil | Ficheiro `LINE_*.png` existente |
| Gráfico velas (sintético) gerado | Ficheiro `CANDLES_SYNTH_*.png` existente |
| Janela ≥ 2 anos | `span_gate_ok: true` com `--min-days 730` **ou** excepção escrita para execução 5.2 |
| Rastreabilidade | `motor_historico_report_*.json` arquivado |

---

## 9. Registo de versões

| Versão | Data | Notas |
|--------|------|--------|
| 1.0.0 | 2026-04-15 | Primeira emissão: motor histórico, 2y gate, linha + velas sintéticas, integração visualizer + OMEGA_PARRF_ROOT. |

---

**Fim do documento** — `DOC-PARRF-PSA-TESTE-MOTOR-HISTORICO-2Y-GRAFICOS-V120-20260415`
