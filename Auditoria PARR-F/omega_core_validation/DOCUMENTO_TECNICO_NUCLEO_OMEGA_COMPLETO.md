# Documento técnico completo — núcleo de validação OMEGA (RLS, spread causal, Z)

| Campo | Valor |
|--------|--------|
| Versão do documento | 1.1 |
| Data / vigência | 2026-03-27 |
| Pacote | `omega_core_validation` |
| Âmbito | Núcleo de sinal (RLS, spread, Z) + **upgrade v1.1**: engajamento, paridade Z, alinhamento DEFINICOES v1.1.0 |

---

## 1. Esclarecimento sobre ficheiros e pastas (contagem real)

**Não** corresponde a “3 pastas e 5 ficheiros” no sentido de um pacote mínimo versionável.

**Estrutura intencional (excluindo `.pytest_cache`, gerado localmente):**

```
omega_core_validation/
├── rls_regression.py          # RLS 2D + OLS batch de referência
├── v821_batch.py              # Referência batch V8.2.1 (janela OLS + Z EWMA shift(1))
├── online_rls_ewma.py         # Motor online (RLS + EWMA causal em μ, v)
├── engagement_metrics.py      # Métrica 9 + n=0 + opportunity_cost (DEFINICOES v1.1)
├── parity_report.py           # Métrica 10.A/10.B — relatório de deriva Z
├── requirements.txt
├── DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md   # este ficheiro
├── TECH_SPEC_OMEGA_CORE_VALIDATION.md           # resumo técnico (legado / índice curto)
└── tests/
    ├── test_rls.py
    ├── test_v821_batch.py
    ├── test_online_engine.py
    ├── test_engagement_metrics.py
    └── test_parity_report.py
```

- **Pastas “de código”:** 2 (`omega_core_validation/`, `tests/`). A pasta `.pytest_cache/` **não** faz parte do pacote entregue; é criada ao correr `pytest`.
- **Ficheiros Python:** 10 (5 módulos + 5 ficheiros de teste).
- **Ficheiros de configuração / doc:** `requirements.txt` + 2 markdown técnicos.

**Confiança:** alta — inventário verificável listando o directório no repositório.

---

## 2. Âmbito e fronteira honesta (evitar análises infundadas)

### 2.1 O que este pacote **é**

Um **núcleo matemático reprodutível** que calcula:

1. **Spread causal** relativamente a uma relação linear \(y \approx \alpha + \beta x\), com duas especificações:
   - **Batch V8.2.1:** OLS numa janela móvel que **exclui** a barra corrente.
   - **Online:** inovação RLS \(s_t = y_t - \phi_t^\top \theta_{t-1}\) antes de actualizar \(\theta\).

2. **Score Z causal** (normalização do spread):
   - **Batch:** média e desvio EWMA do *pandas* com `shift(1)` sobre a série de spreads.
   - **Online:** normalização com \(\mu_{t-1}\) e \(\sqrt{v_{t-1}}\) (EWMA recursiva explícita), depois actualização de \(\mu_t, v_t\).

### 2.2 O que este pacote **não** é

| Tema | Estado |
|------|--------|
| Lucro, drawdown, Sharpe, winrate, custos, *slippage* | **Não implementados** aqui; definições oficiais em `Documentacao_Processo/DEFINICOES_TECNICAS_OFICIAIS.md` (métricas de validação de **estratégia / equity**). |
| ADF, Johansen, cointegração | **Fora** deste pacote (aparecem noutros relatórios do projecto). |
| MetaTrader 5, *ticks*, latência real | **Fora**; qualquer afirmação sobre produção exige logs e ambiente real. |
| Paridade numérica ponto-a-ponto **online vs batch pandas** | **Não exigida** nem testada; o código documenta que a variância EWMA recursiva **difere** de `pandas.Series.ewm(...).std()`. |

**Defesa metodológica:** só se pode “comprovar com testes” o que o código **define** e os testes **assertam**. Afirmações sobre P&L ou risco operacional sem código+testes+ *inputs* auditáveis são **fora de escopo** deste documento.

---

## 3. Glossário de variáveis e estado

### 3.1 Observações e vectores de desenho

| Símbolo | Nome no código | Tipo / shape | Significado |
|---------|----------------|--------------|-------------|
| \(y_t\) | `y` | `float` / `ndarray` | Série “dependente” (ex.: log-preço ou retorno de um activo). |
| \(x_t\) | `x` | `float` / `ndarray` | Série “explicativa” (ex.: segundo activo ou factor). |
| \(\phi_t\) | construído como `[1.0, x]` | \(\mathbb{R}^2\) | Vector de regressão com intercepto. |

**Unidade:** a mesma que a dos dados de entrada (o núcleo é **adimensional** na interface: não impõe se são preços ou logs).

### 3.2 RLS (`RLSRegression2D`)

| Símbolo | Atributo | Significado |
|---------|----------|-------------|
| \(\theta\) | `theta` | \([\alpha, \beta]^\top\) estimado por RLS. |
| \(P\) | `P` | Matriz \(2\times2\) associada ao algoritmo RLS (escala inicial `p0_scale·I`). |
| \(\lambda\) | `forgetting` / `lam` | Fator de esquecimento \(\in (0,1]\). \(\lambda=1\): sem esquecimento. |
| \(s_t\) | retorno de `innovation` / `update` | \(y_t - \phi_t^\top \theta_{t-1}\) **antes** da actualização com \((y_t,x_t)\). |
| \(\hat{y}_t\) | segundo valor de `innovation` | \(\phi_t^\top \theta_{t-1}\). |

**Justificativa do spread causal (online):** utilizar \(\theta_{t-1}\) garante que o erro na barra \(t\) não usa informação de \(y_t\) dentro de \(\theta\) — alinhado com uso de inovação em filtragem recursiva.

### 3.3 Batch V8.2.1 (`rolling_ols_spread`, `causal_z_ewma_shift1`)

| Símbolo | Parâmetro | Significado |
|---------|-----------|-------------|
| \(w\) | `window` | Comprimento da janela OLS: índices \([i-w, i)\) para estimar \((\alpha,\beta)\). |
| `spread[i]` | saída | \(y_i - (\hat\alpha_i + \hat\beta_i x_i)\) com \(\hat\alpha_i,\hat\beta_i\) só da janela passada. |
| `span` | `ewma_span` | Parâmetro `span` do `pandas.Series.ewm(span=..., adjust=False)`. |
| \(\varepsilon\) | `eps` | Constante no denominador do Z para estabilidade numérica. |
| \(Z_i\) | saída `causal_z_ewma_shift1` | \((s_i - \mu^{\text{shift}}_i)/(\sigma^{\text{shift}}_i + \varepsilon)\) com média/desvio EWMA **deslocados** (`shift(1)`). |

### 3.4 Motor online (`OnlineRLSEWMACausalZ`)

| Símbolo | Atributo | Significado |
|---------|----------|-------------|
| \(\alpha_{\text{ewma}}\) | `alpha` | \(2/(\text{ewma\_span}+1)\) — parâmetro da média móvel exponencial simples equivalente ao `span`. |
| \(\mu_t\) | `mu` | Média EWMA do spread **após** incorporar \(s_t\) no passo (ver ordem no código). |
| \(v_t\) | `var` | Variância EWMA recursiva; desvio usado na normalização é \(\sqrt{v_{t-1}}\) no passo corrente (para \(t>0\)). |
| `_n` | contador | Primeira observação: `z := 0` por convenção; inicialização de `mu`, `var`. |

**Ordem contratual no código** (`online_rls_ewma.py`): `innovation` → cálculo de `z` com estado **anterior** de \(\mu,v\) → `rls.update`.

---

## 4. “Métricas” neste núcleo — definição e defesa

Aqui **métrica** significa **funcional determinístico dos dados** implementado no pacote, **não** métrica de desempenho comercial.

### 4.1 Spread em janela (batch)

- **Definição:** para cada \(i \ge w\), \(\hat\theta_i = \text{OLS}(y_{i-w:i-1}, x_{i-w:i-1})\), depois \(\text{spread}_i = y_i - [1\ x_i]\hat\theta_i\).
- **Propriedade testada:** coincide com uma reimplementação explícita da OLS na mesma janela num índice de verificação (`test_rolling_spread_uses_only_past_window`).
- **Confiança:** alta para a propriedade “só usa dados passados na regressão”.

### 4.2 Z-score batch (EWMA + `shift(1)`)

- **Definição implementada:** replicação literal de `pandas`: `ewm.mean().shift(1)`, `ewm.std().shift(1)` no denominador.
- **Provas:**
  - Igualdade numérica com fórmula explícita no teste (`test_causal_z_matches_explicit_shift1_formula`).
  - Distinção **provada** relativamente à normalização **sem** `shift` (`test_z_differs_from_contemporaneous_ewma_when_series_moves`) — evita confundir “Z causal” com “Z usando a média do mesmo instante”.
- **Confiança:** alta para aderência ao contrato **pandas+shift(1)**.

### 4.3 Consistência do pipeline batch

- `v821_causal_spread_and_z` = `rolling_ols_spread` + `causal_z_ewma_shift1` (teste `test_v821_pipeline_matches_components`).
- **Confiança:** alta (igualdade exacta `atol=0` onde ambos finitos).

### 4.4 RLS \(\lambda=1\) vs OLS global

- **Afirmação comprovada (numéricamente):** após percorrer toda a série com \(\lambda=1\), \(\theta\) do RLS está próximo do OLS em **toda** a amostra (`batch_ols_alpha_beta`), com tolerância `rtol=5e-3, atol=5e-3` no teste.
- **Limitação:** é **convergência empírica** num cenário simulado (\(n=800\)); não é demonstração formal de teorema neste repositório.
- **Confiança:** alta para “comportamento esperado de RLS sem esquecimento em regressão estática bem condicionada”; média para generalizar a todos os DGP sem mais testes.

### 4.5 Inovação = \(y - \phi^\top\theta_{\text{antes}}\)

- **Teste:** `test_innovation_matches_y_minus_phi_theta` fixa \(\theta\) inicial conhecido (zero) e compara `innovation` à fórmula manual.
- **Confiança:** alta para a semântica da função `innovation` **tal como implementada**.

### 4.6 Motor online — estabilidade numérica básica

- **Teste:** `test_online_runs_without_nan_inf` — após 50 barras, todos os \(z_t\) são finitos num percurso longo com dados aleatórios (`seed` fixo).
- **O que **não** prova:** optimalidade, paridade com batch, lucro, robustez a *outliers* extremos.
- **Confiança:** média para “não explode neste cenário”; baixa para extrapolar a todos os mercados.

---

## 5. Matriz de comprovação (rastreável)

| # | Afirmação | Evidência | Ficheiro de teste |
|---|-----------|-----------|-------------------|
| 1 | RLS com \(\lambda=1\) aproxima OLS global (tolerância declarada) | `assert_allclose` | `tests/test_rls.py` — `test_rls_lambda1_matches_batch_ols` |
| 2 | `innovation(y,x)` usa \(\theta\) **antes** do update | igualdade a fórmula manual | `tests/test_rls.py` — `test_innovation_matches_y_minus_phi_theta` |
| 3 | Spread batch na barra \(i\) usa apenas \([i-w,i)\) na regressão | reconstrução OLS manual | `tests/test_v821_batch.py` — `test_rolling_spread_uses_only_past_window` |
| 4 | Z batch = fórmula pandas EWMA + `shift(1)` | `assert_allclose` com esperado explícito | `tests/test_v821_batch.py` — `test_causal_z_matches_explicit_shift1_formula` |
| 5 | Z batch \(\neq\) Z com média/desvio contemporâneos (caso construído) | `not np.allclose` | `tests/test_v821_batch.py` — `test_z_differs_from_contemporaneous_ewma_when_series_moves` |
| 6 | Pipeline composto = componentes | igualdade exacta | `tests/test_v821_batch.py` — `test_v821_pipeline_matches_components` |
| 7 | Online: \(z\) finito após warm-up | `np.isfinite` | `tests/test_online_engine.py` — `test_online_runs_without_nan_inf` |
| 8 | `engagement_rate`: N/A se zero sinais; valor se válido | `pytest` | `tests/test_engagement_metrics.py` |
| 9 | `opportunity_cost_points` só se sinal e não-fill | `pytest` | `tests/test_engagement_metrics.py` |
| 10 | Relatórios de paridade retornam MSE finito | `pytest` | `tests/test_parity_report.py` |

**Reprodução:**

```bash
cd omega_core_validation
pip install -r requirements.txt
python -m pytest tests -v
```

---

## 6. Parâmetros — papel e risco de interpretação

| Parâmetro | Onde | Efeito | Risco se ignorado |
|-----------|------|--------|-------------------|
| `forgetting` \(\lambda\) | RLS | \(\lambda<1\) dá mais peso a dados recentes; muda \(\theta_t\) e portanto \(s_t\). | Comparar números com \(\lambda=1\) e \(\lambda=0.98\) sem aviso = conclusões **não** comparáveis. |
| `p0_scale` | RLS | Influencia velocidade inicial de convergência da covariância. | \(\theta\) inicial e primeiras inovações dependem deste prior. |
| `window` | batch | Mais dados na OLS → menor variância de \(\hat\beta\), mais lag. | *Lookahead* se alguém erradamente incluir barra \(i\) na regressão — **explicitamente excluída** no código. |
| `ewma_span` | batch / online | Maior `span` → Z mais suave, reacção mais lenta. | “Z alto” não é universalmente “sinal forte” sem calibragem por activo e horizonte. |
| `eps` | batch / online | Evita divisão por zero. | Muito grande → comprime Z; muito pequeno → instabilidade se desvio EWMA \(\approx 0\). |

Nenhuma destas escolhas é “comprovada como óptima” neste pacote — apenas **documentada**.

---

## 7. Relação com `DEFINICOES_TECNICAS_OFICIAIS.md`

- **v1.1.0** (`OMEGA-DEFINICOES-v1.1.0`, 27/03/2026): inclui **taxonomia** Sinal / Performance / Execução / Engajamento / Paridade, convenções **n=0**, **Métrica 9** (engajamento) e **Métrica 10** (paridade Z + custo de oportunidade condicional), alinhadas aos achados em `OMEGA_OS_Kernel/.../AUDITORIA DE SISTEMA`.
- O núcleo continua a governar **métricas de sinal**; `engagement_metrics.py` e `parity_report.py` são **ponte normativa** para auditoria sem confundir com Sharpe/drawdown.
- **Regra de ouro:** não misturar conclusões: um Z-score bem definido **não** implica Sharpe elevado nem drawdown aceitável — seria violação de níveis de abstração (sinal vs P&L).

---

## 8. Limitações explícitas (checklist)

1. Testes usam majoritariamente dados **sintéticos** ou pequenas séries; não substituem validação em **dados reais** com manifestos e hashes.
2. `test_rls_lambda1_matches_batch_ols` usa tolerância finita — não é prova formal \(\|\theta_{\text{RLS}}-\theta_{\text{OLS}}\|=0\).
3. O motor online **não** está amarrado numericamente ao batch pandas; qualquer relatório que os trate como idênticos está **incorreto** salvo estudo de erro adicional.
4. A primeira barra do online fixa \(z=0\) por convenção — é escolha de interface, não propriedade estatística universal.

---

## 9. Referências conceituais (não substituem o código)

- RLS com fator de esquecimento: literatura padrão de filtragem / regressão recursiva (ver livros-texto de identificação/adaptative filters).
- Pandas EWMA: documentação oficial `Series.ewm` (`adjust=False`, `span`).

---

## 10. Citações de auditoria incorporadas (upgrade v1.1)

| Origem (pasta AUDITORIA DE SISTEMA) | Achado | Resposta no ecossistema OMEGA |
|-------------------------------------|--------|--------------------------------|
| **CQO** | Métricas não cobrem não-execução; opportunity cost sem fórmula; n=0 indefinido; hashes | Métrica **9** + **10.2** + convenções **n=0** + secção SHA3 em DEFINICOES |
| **CFO** | “Métrica” ambígua; falta ponte sinal→equity; thresholds sem base empírica | Taxonomia em DEFINICOES; ponte explícita **regras de trading fora do núcleo**; thresholds 1–6 marcados como **governo até calibração** |
| **CKO** | Paridade numérica batch vs live / Z inflado | Métrica **10.A/10.B** + `parity_report.py`; MSE **não** exigido ≈0 por defeito |
| **CIO** (resposta interna) | Defesa do núcleo | Mantida: comprovação = matriz secção 5 + testes; sem extrapolação para P&L |

---

## 11. Roadmap pós-instalação — evidência empírica (comprovação matemática no domínio real)

1. **Instalar** dependências (`requirements.txt`) e correr `pytest` (15 testes na v1.1) — comprova **coerência de código**.
2. **Carregar** séries reais (manifesto + hash) e gerar relatórios:
   - `parity_ewma_z_pandas_vs_recursive` na série de **spreads** efectivamente usada em backtest;
   - `parity_full_batch_vs_online` com os **mesmos** `window`, `ewma_span`, `forgetting` previstos para produção.
3. **Arquivar** CSV + SHA3-256 + parâmetros + versão do protocolo (`OMEGA-DEFINICOES-v1.1.0`).
4. **Só então** relacionar com Sharpe/drawdown (Métricas 1–6) na **mesma** janela temporal e com **engagement** (Métrica 9) preenchido a partir de logs.

---

## 12. Declaração de integridade

Este documento foi construído a partir dos ficheiros Python e de testes presentes em `omega_core_validation` no momento da redacção. Qualquer afirmação de “comprovado” remete à matriz da secção 5; comprovação **empírica em mercado** exige o roadmap da secção 11.

Para alterações futuras: actualizar primeiro o código e os testes, depois esta matriz e `DEFINICOES_TECNICAS_OFICIAIS.md` — nunca o inverso.
