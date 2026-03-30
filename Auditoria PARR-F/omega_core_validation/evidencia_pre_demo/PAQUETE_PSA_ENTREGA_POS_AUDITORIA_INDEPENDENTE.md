# Pacote PSA — Pós-auditoria independente Tier-0 (instruções e entregáveis)

| Campo | Valor |
|--------|--------|
| **Documento** | `PAQUETE_PSA_ENTREGA_POS_AUDITORIA_INDEPENDENTE` |
| **Versão** | 1.0.0 |
| **Data** | 30 de Março de 2026 |
| **Destinatário** | PSA / Engenharia (Antigravity MACE-MAX) |
| **Âmbito** | Fechamento de ações após `RELATORIO_CONSELHO_AUDITORIA_INDEPENDENTE_TIER0_20260330.md` |

---

## 1. Âmbito explícito (o que a auditoria independente cobre)

As análises da **auditoria independente** referem-se **apenas** ao documento:

`RELATORIO_CONSELHO_AUDITORIA_INDEPENDENTE_TIER0_20260330.md`

Esse parecer **não** valida, por si só:

- números de PnL, Sharpe, Kurtosis ou Drawdown de relatórios de marketing;
- aprovação “NASA/ISO” genérica;
- conteúdo de ficheiros `Auditoria Conselho\CIO*.txt`, `CKO*.txt`, `CQO*.txt` **salvo** onde reproduzam **exactamente** o manifesto verificado.

**Correção documental obrigatória:** em `Auditoria Conselho\CIO - Chief Information Officer.txt`, a **tabela 2.1** (stress CSV) ainda mostra **tamanhos e hashes truncados incorretos** (~21 MB). O **único** valor canónico para stress logs é o de `MANIFEST_RUN_20260329.json` (≈16 MB por ficheiro, hashes completos de 64 hex). O PSA deve **substituir** essa tabela pela tabela do manifesto ou apagar a secção errada para evitar **dupla verdade** perante investidores/regulador interno.

---

## 2. O que o PSA deve receber / manter (checklist de pacote)

| # | Artefacto | Caminho (canónico gemini) | Nota |
|---|-----------|---------------------------|------|
| P1 | Relatório independente | `...\evidencia_pre_demo\RELATORIO_CONSELHO_AUDITORIA_INDEPENDENTE_TIER0_20260330.md` | Fonte do parecer |
| P2 | Relatório de stress V2 | `...\evidencia_pre_demo\RELATORIO_FINAL_STRESS_TEST_2026.md` | Alinhado manifesto |
| P3 | Manifesto | `...\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json` | Verdade de hashes/tamanhos |
| P4 | Gate demo | `...\evidencia_pre_demo\06_gate_demo\DECISAO_20260329.md` | Declaratório |
| P5 | Checklist Tier-0 | `...\EVIDENCIA_PRE_DEMO_TIER0_CHECKLIST.md` | Requisitos M*, Q*, R*, G* |
| P6 | Definições métricas (corrida) | `...\evidencia_pre_demo\04_metricas_rol\DEFINICOES_METRICAS_RUN.md` | G3 — confirmar vs código |
| P7 | Logs stress | `...\evidencia_pre_demo\02_logs_execucao\STRESS_2Y_*.csv` | 3 × 100k linhas |
| P8 | RAW MT5 | `...\evidencia_pre_demo\01_raw_mt5\XAUUSD_M1_RAW.csv`, `XAGUSD_M1_RAW.csv` | G4 |
| P9 | Núcleo + testes | `...\omega_core_validation\` | pytest 15 passed |
| P10 | Verificação integridade (linha) | `...\Declaracoes\verify_integrity.py` | Se o formato for compatível |

**Espelho Cursor:** mesma árvore sob `C:\Users\Lenovo\.cursor\nebular-kuiper\Auditoria PARR-F\...`.

---

## 3. Questões em aberto — para o PSA responder com evidência

| ID | Questão | Acção PSA | Evidência esperada |
|----|---------|-----------|---------------------|
| Q1 | `git_commit` ausente no manifesto | Incluir `git_rev` ou `source_tree_hash` no próximo `MANIFEST_*.json` | JSON actualizado + comando usado |
| Q2 | SHA3 só recomputado para DAY_TRADE (auditoria) | Recomputar SHA3-256 **ficheiro completo** para SCALPING e SWING | `VERIFY_LOG.txt` com 3 linhas OK |
| Q3 | G3 parcial | Demonstrar que `DEFINICOES_METRICAS_RUN.md` = código gerador dos CSVs | diff ou referência de linha de código |
| Q4 | G4 parcial | Documentar proveniência RAW: broker, servidor, primeira/última barra | `01_raw_mt5/README_PROVENIENCIA.md` |
| Q5 | G5 declaratório | Logs **demo** separados (quando existirem) | pasta `evidencia_demo_*/` |
| Q6 | Nomenclatura “2Y” | Renomear internamente (ex.: `QUARTER_STRESS_TEST_V10.4`) conforme Conselho | commit + nota no README |
| Q7 | Tabela errada no CIO | Corrigir `CIO - Chief Information Officer.txt` secção 2.1 | ficheiro revisto |

---

## 4. Scripts e comandos (procedimento)

### 4.1 Pytest (núcleo)

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation"
python -m pytest tests -v --tb=short
```

**Esperado:** `15 passed` (confirmar com a versão actual do pacote).

### 4.2 SHA3-256 de ficheiro completo (verificação manual)

```powershell
python -c "import hashlib, pathlib; p=pathlib.Path(r'CAMINHO\STRESS_2Y_SCALPING.csv'); h=hashlib.sha3_256(); h.update(p.read_bytes()); print(p.stat().st_size, h.hexdigest())"
```

Repetir para `STRESS_2Y_SWING_TRADE.csv`. Comparar com `MANIFEST_RUN_20260329.json`.

### 4.3 Saída para anexo

Guardar stdout em:

`evidencia_pre_demo\03_hashes_manifestos\VERIFY_LOG.txt`

Formato sugerido (uma linha por ficheiro):

`OK <filename> <bytes> <sha3_256_full>`

---

## 5. Métricas: o que está coberto pelo parecer independente

| Tópico | Coberto pelo relatório independente? |
|--------|--------------------------------------|
| Bytes + SHA3 dos ficheiros listados no manifesto | Sim (tabela; DAY_TRADE verificado por recomputação) |
| 15 testes `omega_core_validation` | Sim (referência; reexecutar antes de cada release) |
| PnL / Sharpe / Kurtosis de tabelas “Soberania” antigas | **Não** — exige revalidação com código + CSV |
| Demo / MT5 em tempo real | **Não** |

---

## 6. Sugestões de correção e governança

1. **Single source of truth:** qualquer PDF ou “RELATÓRIO-CONSOLIDADO” deve **gerar-se** a partir de `MANIFEST_RUN_*.json` (script), não copiar tabelas à mão.
2. **Conselho / CIO:** alinhar o ficheiro CIO à secção 3 deste pacote (remover hashes truncados e tamanhos errados).
3. **Demo:** métrica principal sugerida pelo Conselho — **consistência de execução** (sinal enviado vs preço de fill), não promessa de PnL; registar em CSV separado com hashes.

---

## 7. Contacto de fechamento

O PSA deve **devolver** ao Conselho:

1. `VERIFY_LOG.txt` completo (Q2).  
2. `README_PROVENIENCIA.md` (Q4).  
3. CIO corrigido ou nota de substituição (Q7).  
4. Próximo manifesto com `git_rev` (Q1), quando disponível.

---

**Fim — PAQUETE_PSA_ENTREGA_POS_AUDITORIA_INDEPENDENTE v1.0.0**
