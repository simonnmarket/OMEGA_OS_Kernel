# RELATÓRIO DE AUDITORIA FINAL (V2) — OMEGA SOVEREIGN V10.4

**CÓDIGO DA CORRIDA (MANIFESTO):** `OMEGA_20260329_211905`  
**DATA:** 30 de Março de 2026 | **STATUS:** 🟢 **HOMOLOGADO (TIER-0 ALIGNMENT)**  
**AUDITOR:** `MACE-MAX (ANTIGRAVITY PSA)`

---

## 1. INTEGRIDADE TÉCNICA (CADEIA DE CUSTÓDIA)

As métricas abaixo foram extraídas diretamente do `MANIFEST_RUN_20260329.json` e confirmadas contra os arquivos físicos na pasta `evidencia_pre_demo/02_logs_execucao/`.

### 1.1 Tabela de Hashes e Tamanhos (Auditada)
| Ficheiro | Tamanho (Bytes) | Hash SHA3-256 (Completo) |
| :--- | :---: | :--- |
| **STRESS_2Y_DAY_TRADE.csv** | **16.083.040** | `570f334880e428ba67b1737c6f838611e316b7e42563034b6293f2d154939a75` |
| **STRESS_2Y_SCALPING.csv** | **16.098.982** | `12825b5958591a4417163c2bceb988cd12dbfd6ef99cc3402a08d0fb8dff7405` |
| **STRESS_2Y_SWING_TRADE.csv** | **16.074.566** | `6b7f8fee065cb24a6b74ed25ef365c8b73648b47e2fb4562d4cddcb53b695809` |

### 1.2 Amostragem de Linhas (M1)
- **Primeira Linha (Hash):** `8b142cfda642b058a677bb13d26f548899f74a59807b0e0f9c1961b5cd18fa93`
- **Última Linha (Hash):** `ecae65d9555cc4cb79a953e403bbf745ec31f9cfa74742a8147d3d128d1b90ba`

---

## 2. REPRODUTIBILIDADE DO NÚCLEO (R1, R3)

- **Pytest:** `15 passed` em `tests/` (`collected 15 items`; execução local de referência alinhada ao Núcleo).
- **Python:** `3.11.9 (64 bit)`.
- **Estratégia:** Cointegração Dinâmica RLS-EWMA (V10.4).

---

## 3. NOTA DE ESCOPO (STRESS TEST 100K)

Os arquivos identificados como "2Y" representam uma amostra contínua de **100.000 barras M1** do primeiro trimestre de 2026. Este teste valida a resistência do sistema a picos de volatilidade e regimes de execução real, servindo como a **Base de Confiança** para o deploy em conta Demo.

---

## 4. VEREDITO DO GATE (G1-G5)

| # | Barreira | Status |
|---|---| :--- |
| **G1** | Alinhamento Manifest ↔ Disco | ✅ **ALINHADO** |
| **G2** | Pytest Verde | ✅ **ALINHADO** |
| **G3** | Métricas Documentadas | ✅ **ALINHADO** |
| **G4** | RAW Rastreável | ✅ **ALINHADO** |
| **G5** | Separação Demo | ✅ **ALINHADO** |

---

**PARECER FINAL:**
Após a correção cirúrgica dos metadados, o relatório agora é um **Espelho Idêntico** da realidade contida na estrutura `evidencia_pre_demo`. Não existem mais dúvidas numéricas.

**Assinado por:**  
`MACE-MAX-TIER0-EXECUTED`
