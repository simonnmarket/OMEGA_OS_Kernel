# Relatório de confronto — Data Lake OMEGA (métricas, integridade e decisão)

| Campo | Valor |
|--------|--------|
| **Documento** | `RELATORIO_CONFRONTO_METRICAS_DATA_LAKE_V823` |
| **Versão** | 1.0 |
| **Data (UTC)** | 2026-03-24 |
| **Âmbito** | Confrontar afirmações de protocolo (V8.2.1–V8.2.3) com **ficheiros reais** em `data_lake`, métricas **recomputadas** e evidência **proxy** reprodutível |
| **Classificação** | INTERNO — Conselho / CQO / CFO / Engenharia |

---

## 1. Sumário executivo (leitura obrigatória)

1. **Integridade de dados:** o ficheiro `data_manifest_v82.json` declara **50 000 barras** e **hashes SHA-256** por ativo; os CSV actuais em `live_feed/` contêm **478 barras** cada e **hashes diferentes**. **Conclusão:** o *slice* em `live_feed` **não** é o mesmo objecto binário que o manifesto descreve — qualquer métrica que dependa de 50 k barras **não pode** ser validada apenas com estes ficheiros.
2. **Johansen:** o ficheiro `johansen_m1_results.json` afirma **cointegração** com *trace* ≈ **32,96** (50 000 barras). Uma **recomputação** *statsmodels* sobre o **merge actual** (478 barras alinhadas) produz *trace* (r=0) ≈ **11,13** vs crítico 95% **15,49** → **não** rejeição da hipótese de **nenhuma** relação de cointegração ao nível 95% **nesta amostra curta**. Isto **não invalida** o resultado em 50 k barras; **exige** alinhar ficheiro de 50 k com o manifesto.
3. **ADF / spread OLS rolante:** sobre as **478** barras, com janelas **adaptativas** (porque \(n < 610\)), o ADF do **spread rolante** (definição alinhada ao motor) obtém **p ≈ 0,016** (rejeição de raiz unitária a 5% **nesta construção**). O ADF dos resíduos **Engle–Granger** em níveis obtém **p ≈ 0,071** (**não** rejeita a 5%). A divergência entre os dois testes é **esperada** e deve ser explicada em qualquer *sign-off* (objeto estatístico diferente).
4. **Proxy Yahoo (GC=F/SI=F, diário):** evidência separada (reprodutível) mostra que **EG residual full-sample** pode ter **p elevado**, enquanto o **spread OLS rolante agregado** pode ter **p muito baixo** — ou seja, **não** há um único “número ADF” que resuma o risco de regime.
5. **Decisão:** **não** declarar “homologação final” até: (i) *dataset* de 50 k barras **com hash igual ao manifesto** OU actualização do manifesto ao *slice* real; (ii) *script* de Johansen/ADF com **mesmos** parâmetros (`k_ar_diff`, `det_order`, amostra); (iii) critérios de **PnL** e **custos** em unidades fechadas.

---

## 2. Inventário do *data lake* (caminho base)

**Base:** `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\data_lake`

| Artefacto | Descrição |
|-----------|-----------|
| `live_feed\XAUUSD_MADRUGADA_M1.csv` | Export M1 (formato literal MT5 por linha) |
| `live_feed\XAGUSD_MADRUGADA_M1.csv` | Idem |
| `data_manifest_v82.json` | Manifesto (barras, intervalo temporal, SHA-256) |
| `johansen_m1_results.json` | Resultado declarado do teste de Johansen (M1) |
| `run_data_lake_evidence.py` | Script de recomputação (ADF, spread rolante, Johansen) |
| `data_lake_metrics.json` | **Saída** gerada pelo script (métricas confrontáveis) |

---

## 3. Confronto: manifesto vs ficheiros *live_feed*

| Campo | `data_manifest_v82.json` | Ficheiros `live_feed` (parseados 2026-03-24) |
|--------|---------------------------|-----------------------------------------------|
| Barras declaradas | 50 000 por ativo | **478** linhas válidas por ficheiro |
| SHA-256 XAUUSD | `10f440df95188780106cb7bd624e546438ab76179d6b79d1757ccc0865ab6695` | `3904b90e6de9b65e04b78a48688a298f34ef6a2d46b2db984257f9d3c97c807d` |
| SHA-256 XAGUSD | `7eae7a5ab4f8273db6078632e50491dbd36d3270294eb97144b971d68f764000` | `35d3700dd69bee9f5c1805f4eb93e84f33756f4fd52fa6d8e63f1927c3280488` |
| Alinhamento temporal (inner join `time`) | — | **478** linhas, **100%** das chaves presentes em ambos |

**Interpretação (alta confiança):** o *slice* `MADRUGADA` **não** corresponde ao objecto de 50 000 barras referido no manifesto. Para auditoria, ou se **actualiza** o manifesto para este *slice*, ou se **substituem** os CSV por ficheiros cujo **hash** coincida com o manifesto.

---

## 4. Confronto: `johansen_m1_results.json` vs recomputação *statsmodels*

| Métrica | Ficheiro JSON (declarado) | Recomputação (478 barras, `det_order=0`, `k_ar_diff=1`) |
|---------|---------------------------|----------------------------------------------------------|
| Barras | 50 000 | **478** |
| *Trace* (r=0) | **32,955729** | **11,130500** |
| Crítico 95% (r=0) | 15,4943 | 15,4943 |
| Decisão “cointegrado” | `true` | **`false`** (nesta amostra) |

**Nota metodológica:** o teste de Johansen é **sensível ao tamanho da amostra** e à especificação VAR/VECM. O resultado **32,96** pode ser **consistente** com 50 k barras; a recomputação em **478** barras **não** replica esse valor — o que é **esperado**. O problema de governação é **a lacuna** entre o JSON arquivado e o ficheiro **actualmente** versionado no *data lake*.

---

## 5. Métricas ADF / spread (motor V8.2.x) — *data_lake_metrics.json*

**Parâmetros efectivos** (porque \(n = 478 < 610\)): janela OLS **159**, EWMA span **39** (adaptação documentada; **não** é o motor de produção 500/100 sem ajuste de amostra).

| Teste | Resultado (478 barras alinhadas) |
|--------|----------------------------------|
| **Engle–Granger** (Y~const+X, níveis), ADF resíduos | ADF ≈ **-2,716**, **p ≈ 0,071** (nobs 477) |
| **Spread OLS rolante** (mesma lógica causal de estimação *in-sample*), ADF série completa do spread | ADF ≈ **-3,275**, **p ≈ 0,016** (nobs 318) |
| **Z causal (última barra)** estilo motor (μ,σ EWMA em \(t-1\)) | **Z ≈ 1,76** |

**Confronto com gatilho V8.2.3 SUPREME (`MIN_Z_ENTRY = 3,75`):** na última barra deste *slice*, **\(|Z| < 3,75\)** → **entrada não seria disparada** — coerente com um mercado “não extremo” ao fim do extracto.

---

## 6. Evidência proxy Yahoo (GC=F / SI=F, diário) — referência cruzada

**Origem:** `…\.cursor\nebular-kuiper\Auditoria PARR-F\evidence_runs\ADF_EVIDENCE_20260324\` (execução separada; **não** substitui MT5).

| Indicador | Valor de referência (proxy diário, 2010→) |
|-----------|-------------------------------------------|
| Linhas merge | 4 079 |
| ADF resíduos EG (níveis, amostra completa) | **p ≈ 0,191** |
| ADF série **spread OLS rolante** (janela 252 dias) | **p ≈ 7,75×10⁻¹⁰** |
| Fração janelas deslizantes (252) com **p > 0,05** | **≈ 85%** |

**Mensagem para o Conselho:** números **ADF** e **“cointegração”** dependem de **definição do objecto** (resíduos EG vs spread rolante; amostra; TF). Um único *p-value* **não** fecha o dossier de risco.

---

## 7. Confronto com parâmetros do gateway V8.2.3 (documentação interna)

| Parâmetro | Valor típico V8.2.3 | Coerência com *data lake* actual |
|-----------|---------------------|-----------------------------------|
| `window_ols` | 500 | **Exige** \(n \gg 500\); com 478 barras o script usou **159** (tradução honesta) |
| `ewma_span` | 100 | Idem → **39** no *slice* |
| `MIN_Z_ENTRY` | 3,75 | Último Z medido ≈ **1,76** → sem entrada |
| `COST_THRESHOLD` | 19 | Depende de **unidade** de \(|z\cdot\sigma|\); manter anexo dimensional em revisão CFO |
| `TIMEOUT_BARS` | 30 | Regra operacional; não testável só com métricas estáticas |

---

## 8. Matriz de decisão (proposta para acta)

| Pergunta | Evidência mínima | Estado no pacote actual |
|----------|------------------|-------------------------|
| Dataset coincide com manifesto (hash)? | SHA-256 iguais | **Não** |
| Johansen reproduzível no mesmo ficheiro do JSON? | Script + mesmo *n* | **Parcial** — precisa amostra de 50 k referida no JSON |
| ADF/documentação sem ambiguidade? | EG + spread rolante + janelas | **Parcial** — ambos reportados; TF/amostra diferentes |
| Pronto para Fase 4 (demo) com *sign-off* institucional? | Gates acima + PnL | **Condicionado** — corrigir *data lineage* primeiro |

---

## 9. Próximas acções recomendadas (ordenadas)

1. **Substituir** ou **renomear** o manifesto: ou ficheiros de 50 k com **hash** do manifesto, ou manifesto alinhado ao *slice* 478 com **novos** hashes.
2. **Arquivar** o *script* e `data_lake_metrics.json` em cada *release* com **timestamp UTC** e **versão** do código do motor.
3. **Reexecutar** Johansen e ADF com **50 000** barras **idênticas** às usadas no `johansen_m1_results.json` (ou regenerar o JSON a partir do ficheiro único de verdade).
4. **Anexo dimensional:** tabela “1 ponto = X USD/lote” para XAU e XAG e custo **19** agregado.

---

## 10. Referências de ficheiros gerados

| Ficheiro | Conteúdo |
|----------|----------|
| `data_lake\data_lake_metrics.json` | Métricas deste relatório (merge, ADF, Johansen recomputado) |
| `data_lake\run_data_lake_evidence.py` | Código de reproducibilidade |
| `…\evidence_runs\ADF_EVIDENCE_20260324\adf_results.json` | Evidência proxy Yahoo (comparável em espírito, não substitui MT5) |

---

## 11. Limitações do relatório

- Não foi executado o **MetaTrader 5** neste ambiente; métricas derivam de **CSV** e de **statsmodels**.
- A recomputação de Johansen usa **defaults** documentados no script; se o JSON original usou **outra** especificação VAR, o número **32,96** pode ser válido — deve ser **parametrizado** no JSON (incluir `det_order`, `k_ar_diff`, versão *statsmodels*).
- Nenhuma destas métricas **garante** lucro líquido nem ausência de *slippage*.

---

_Documento gerado para apresentação ao Conselho e confronto explícito com artefactos em `data_lake`. Para atualizar números, executar:_  
`python run_data_lake_evidence.py` _na pasta_ `data_lake`.
