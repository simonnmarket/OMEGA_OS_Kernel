# Relatório ao Conselho — Auditoria independente Tier-0 (pré-DEMO)

| Campo | Valor |
|--------|--------|
| **Documento** | `RELATORIO_CONSELHO_AUDITORIA_INDEPENDENTE_TIER0_20260330` |
| **Versão** | 1.0.0 |
| **Data** | 30 de Março de 2026 |
| **Emitido por** | Revisão técnica independente (Cursor / assistente de engenharia) |
| **Objecto** | Correlação entre `MANIFEST_RUN_20260329.json`, ficheiros em disco e relatório de stress `V10.4` |
| **Run ID** | `OMEGA_20260329_211905` |

**Nota de governança:** este texto não substitui parecer jurídico, de risco financeiro nem de compliance regulatório. Documenta **verificações técnicas** e **limitações** para deliberação do Conselho.

---

## 1. Sumário executivo

1. **Cadeia de custódia (hashes e tamanhos):** Os metadados de `MANIFEST_RUN_20260329.json` para os três CSVs de stress (`STRESS_2Y_*`) e **RAW** (`XAUUSD_M1_RAW.csv`, `XAGUSD_M1_RAW.csv`) estão **consistentes** entre si e **repetíveis** a partir do manifesto publicado.
2. **Verificação independente:** Para `STRESS_2Y_DAY_TRADE.csv`, foi **recomputado** `SHA3-256` do ficheiro completo no ambiente local; o digest **coincidiu** com o manifesto (`570f334…939a75`).
3. **Correcção documental:** Uma versão anterior de relatório (não alinhada) usava **outros** tamanhos, hashes truncados e outro `run_id`. A versão **V2** (`RELATORIO_FINAL_STRESS_TEST_2026.md`) foi **alinhada** ao manifesto; a linha **pytest** foi corrigida de `8 passed` para **`15 passed`**, coerente com o pacote `omega_core_validation` (`collected 15 items`).
4. **Escopo:** Os ficheiros nomeados com prefixo `STRESS_2Y_*` contêm **100.000** linhas por perfil (não um histórico completo de 24 meses). A nomenclatura “2Y” deve ser interpretada como **rótulo de projeto**, não como cobertura temporal de dois anos, salvo prova adicional.
5. **Demo:** Aprovação de **conta demo** e **injeção de ordens** é **decisão do Conselho e da operação**, não deste relatório. **Não** há validação aqui de PnL futuro, slippage real ou adequação regulatória.

---

## 2. Metodologia de revisão

| Passo | Descrição |
|--------|-----------|
| M1 | Leitura de `MANIFEST_RUN_20260329.json` na árvore canónica (`gemini`). |
| M2 | Comparação com `RELATORIO_FINAL_STRESS_TEST_2026.md` (V2). |
| M3 | Recomputação `SHA3-256` do ficheiro `STRESS_2Y_DAY_TRADE.csv` (Python `hashlib.sha3_256`). |
| M4 | Execução de `python -m pytest tests -v` em `omega_core_validation` (espelho Cursor) para contagem de testes. |
| M5 | Cruzamento com `EVIDENCIA_PRE_DEMO_TIER0_CHECKLIST.md` (requisitos M1–M4, Q1–Q3, R1–R3, G1–G5). |

---

## 3. Tabela de integridade — manifesto completo (fonte: `MANIFEST_RUN_20260329.json`)

### 3.1 Logs de stress (100.000 linhas cada)

| Ficheiro | Bytes | SHA3-256 (ficheiro completo) |
|----------|------:|------------------------------|
| `STRESS_2Y_DAY_TRADE.csv` | 16.083.040 | `570f334880e428ba67b1737c6f838611e316b7e42563034b6293f2d154939a75` |
| `STRESS_2Y_SCALPING.csv` | 16.098.982 | `12825b5958591a4417163c2bceb988cd12dbfd6ef99cc3402a08d0fb8dff7405` |
| `STRESS_2Y_SWING_TRADE.csv` | 16.074.566 | `6b7f8fee065cb24a6b74ed25ef365c8b73648b47e2fb4562d4cddcb53b695809` |

**Primeira / última linha (SHA3 por linha) — apenas `DAY_TRADE` (manifesto):**

- Primeira: `8b142cfda642b058a677bb13d26f548899f74a59807b0e0f9c1961b5cd18fa93`
- Última: `ecae65d9555cc4cb79a953e403bbf745ec31f9cfa74742a8147d3d128d1b90ba`

### 3.2 RAW MT5 (manifesto)

| Ficheiro | Bytes | SHA3-256 |
|----------|------:|----------|
| `XAUUSD_M1_RAW.csv` | 5.199.973 | `50bd0e2b68d4340205b72f77e6709b8f8a499c8868a5b3bb4767dacd0b878154` |
| `XAGUSD_M1_RAW.csv` | 4.855.796 | `bead7b55a34b5e5e683f70d8ebebdb5d11fe861e1ca2c7faad525e3ca63f54e2` |

### 3.3 Metadados do manifesto

| Campo | Valor |
|--------|--------|
| `version` | `V10.4 OMNIPRESENT` |
| `python_version` | `3.11.9` (detalhe completo no JSON) |
| `ts_audit` | `2026-03-29T21:19:05.641018Z` |

---

## 4. Reprodutibilidade do núcleo (`omega_core_validation`)

| Verificação | Resultado |
|-------------|-----------|
| Comando de referência | `python -m pytest tests -v` na pasta `Auditoria PARR-F/omega_core_validation` |
| Resultado observado | **15 passed** (`collected 15 items`) |
| Interpretação | Validação do **núcleo** de regressão/EWMA/paridade; **não** cobre gateway MT5 em tempo real nem `ExecutionManager` completo, se existir noutro repositório. |

---

## 5. Avaliação do gate (G1–G5) — checklist

| ID | Critério | Avaliação | Notas |
|----|----------|-----------|--------|
| **G1** | Hashes completos; manifest ↔ disco | **Satisfeito** para os digest e tamanhos do JSON; **DAY_TRADE** verificado por recomputação. Recomenda-se repetir o mesmo procedimento para **SCALPING** e **SWING** antes de homologação final. |
| **G2** | Pytest verde no mesmo pacote que o stress | **Satisfeito** para o núcleo `omega_core_validation` (`15 passed`). **Não** prova que o binário/script de stress e o núcleo são o mesmo commit **sem** `git_commit` no manifesto. |
| **G3** | Métricas documentadas (Sharpe, MDD, engagement, etc.) | **Parcial.** Existe `04_metricas_rol/DEFINICOES_METRICAS_RUN.md` no pacote de evidência; o Conselho deve confirmar que as definições **coincidem** com o código que gerou os CSVs. |
| **G4** | RAW rastreável (origem MT5, intervalo) | **Parcial.** O manifesto fixa tamanho e hash dos RAW; a **proveniência** (broker, servidor, datas de primeira/última barra) deve constar **por escrito** (nota em `01_raw_mt5/` ou manifesto estendido). |
| **G5** | Separação backtest vs demo | **Declaratório.** Depende de `DECISAO_*.md` e de **não** misturar ficheiros de PnL; sem logs de demo separados, o critério fica **não verificável** além do texto. |

---

## 6. Questões em aberto (para o Conselho)

1. **Ligação de código:** Incluir no manifesto (ou anexo) **`git commit`** ou hash do pacote que executou o stress, para amarrar G2 ao mesmo artefacto.
2. **Verificação total:** Correr `verify` / script de manifesto para **todos** os ficheiros listados (não só DAY_TRADE) e anexar saída em `05_screenshots_terminal/` ou `03_hashes_manifestos/VERIFY_LOG.txt`.
3. **Nomenclatura:** Esclarecer publicamente se “2Y” é **apenas nome de projeto** ou se haverá **segunda corrida** com janela de 24 meses completa.
4. **Demo:** Definir política de **slippage** (registo de `signal_price` vs `fill_price`), limites de posição e horário de operação **antes** de escalar volume.
5. **Métricas de PnL:** Qualquer número de PnL/Drawdown em relatórios anteriores **não** foi revalidado neste documento; o Conselho deve pedir **código + ficheiro** que reproduzam esses números.

---

## 7. Limitações explícitas (não alegar)

- **Não** foi verificado o ambiente **MetaTrader** nem a conta **demo** nesta sessão.
- **Não** há garantia de desempenho futuro, **nem** em demo nem em real.
- **Não** confundir integridade de **ficheiros** com verdade de **modelo** (overfitting, regime de mercado, custos).

---

## 8. Localização dos artefactos

| Papel | Caminho |
|--------|---------|
| Canónico (fonte operacional) | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\` |
| Espelho (desenvolvimento) | `C:\Users\Lenovo\.cursor\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\` |

Ficheiros principais: `03_hashes_manifestos/MANIFEST_RUN_20260329.json`, `RELATORIO_FINAL_STRESS_TEST_2026.md`, `06_gate_demo/DECISAO_20260329.md`.

---

## 9. Conclusão para deliberação

A **estrutura de evidência** (manifesto com hashes completos, relatório V2 alinhado, correção de pytest para **15 passed**, e verificação independente de SHA3 do `DAY_TRADE`) **suporta** uma decisão informada de **avançar para fase demo** **do ponto de vista de integridade de artefactos e documentação**, com as **ressalvas** das secções 5 e 6.

A decisão final sobre **capital**, **risco**, **demo vs real** e **cronograma** permanece com o **Conselho**.

---

**Fim do relatório — v1.0.0**
