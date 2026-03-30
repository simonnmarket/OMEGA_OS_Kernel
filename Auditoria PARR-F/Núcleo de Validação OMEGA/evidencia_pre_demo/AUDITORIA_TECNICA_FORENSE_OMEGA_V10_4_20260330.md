# Auditoria Técnica e Forense — OMEGA V10.4 (Cointegração / Mean Reversion)

| Campo | Valor |
|--------|--------|
| **Identificação do documento** | ATF-OMEGA-V10.4-20260330 |
| **Versão** | 1.0 |
| **Data de emissão** | 30 de março de 2026 |
| **Classificação de sensibilidade** | Uso interno — Conselho / CEO |
| **Objeto** | Motor RLS + EWMA causal Z (`OnlineRLSEWMACausalZ`) integrado ao gateway `10_mt5_gateway_V10_4_OMNIPRESENT.py` |
| **Escopo declarado pelo mandante** | Operacionalidade da Demo (≈14 h) e consistência com Stress Backtest 2 anos (100k barras M1 por perfil) |
| **Base de evidência principal** | Ficheiros CSV em `evidencia_pre_demo/02_logs_execucao/` e código-fonte referenciado abaixo |

---

## 1. Sumário executivo

1. **Reproducibilidade quantitativa (Stress 2Y):** Com base na leitura programática dos três ficheiros `STRESS_2Y_*.csv` presentes neste repositório (caminho indicado na secção 3), **não se verifica** a alegação de que `signal_fired == True` ocorre zero vezes. Os contagens observadas foram: **SWING 402**, **DAY 197**, **SCALPING 375** (em 100 000 linhas cada). O número de linhas com **|Z| ≥ 3,75** coincide exatamente com essas contagens, o que alinha a variável `signal_fired` com o limiar codificado no gateway.

2. **Inconsistência documental:** Qualquer relatório forense que afirme **zero** sinais nestes artefactos **entra em conflito direto** com os dados agora medidos. Isso não exclui falhas noutro conjunto de ficheiros, cópia desatualizada ou erro de coluna / encoding — mas **impõe** reabrir a cadeia de custódia dos CSVs citados no relatório original.

3. **Risco matemático e de parametrização (plausível, a validar em experimento):** A combinação **λ (forgetting do RLS)** + **`ewma_span`** + **limiar |Z| = 3,75** pode, em certos regimes de mercado, produzir **poucos disparos** ou **Z colado a zero** na Demo, especialmente se a memória efetiva do RLS for curta face ao horizonte de “swing” desejado. Isto é **hipótese técnica** a confirmar com logs de Demo e com ensaio controlado — não substitui a evidência numérica dos stress files acima.

4. **Achado de estabilidade numérica:** Em cada ficheiro de stress existe **uma** observação com Z de magnitude extrema (ordem **10⁷**), compatível com **instabilidade pontual** (ex.: variância EWMA muito pequena no denominador, ou transiente inicial). Tal valor **não representa** interpretação financeira estável sem truncagem, *winsorização* ou política explícita de *sanity bounds*.

5. **Lacuna de governança de QA:** Integridade Tier-0 (hashes, ausência de exceções) **não equivale** a validação estatística da **volumetria de sinais** nem à calibração económica do limiar. A ausência de *gate* do tipo “mínimo de `signal_fired` por pipeline” constitui **defeito de processo** passível de classificação como **negligência de validação** ao nível organizacional (definição de critérios de aceitação), sem imputação individual neste documento.

---

## 2. Metodologia

| Etapa | Descrição |
|--------|------------|
| **Inventário** | Localização dos `STRESS_2Y_*.csv` e do gateway V10.4. |
| **Medição** | `pandas.read_csv` + soma booleana de `signal_fired`; contagem de `|z| ≥ 3.75`; deteção de valores de `z` fora de faixa “razoável” (proxy ±10⁶). |
| **Revisão de código** | Leitura de `10_mt5_gateway_V10_4_OMNIPRESENT.py` e `online_rls_ewma.py` para mapear variáveis e contratos. |
| **Limitações** | Não foi reexecutado o stress nesta auditoria; não foram analisados neste documento todos os `DEMO_LOG_*.csv` linha a linha. |

---

## 3. Bases e evidências (ficheiros)

**Caminho analisado (workspace atual):**

`Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/02_logs_execucao/`

| Ficheiro | Linhas | `signal_fired == True` | Linhas com `|z| ≥ 3.75` | `z` min (observado) | `z` max (observado) | Linhas com `|z| > 10⁶` |
|-----------|--------|-------------------------|---------------------------|---------------------|---------------------|-------------------------|
| `STRESS_2Y_SWING_TRADE.csv` | 100 000 | **402** | **402** | ≈ −4,32×10⁷ | ≈ 13,78 | **1** |
| `STRESS_2Y_DAY_TRADE.csv` | 100 000 | **197** | **197** | ≈ −4,32×10⁷ | ≈ 10,65 | **1** |
| `STRESS_2Y_SCALPING.csv` | 100 000 | **375** | **375** | ≈ −4,32×10⁷ | ≈ 32,49 | **1** |

**Interpretação (alta confiança, com base nos números acima):** No pipeline que gerou estes CSVs, **`signal_fired` é verdadeiro sempre que o lado não é `FLAT`**, o que ocorre quando **|Z| cruza 3,75** (ver código citado na secção 5). Logo, **os stress tests aqui arquivados não são “silenciosos” no sentido de zero sinais.**

**Interpretação (média confiança):** O **único** valor absurdamente grande de |Z| por ficheiro sugere **revisão obrigatória** de política numérica (piso de variância `eps`, *clipping* de Z, ou warm-up excluído de métricas).

---

## 4. Arquitetura lógica (níveis de abstração)

| Componente | Ficheiro / classe | Função |
|-------------|-------------------|--------|
| **Motor estatístico** | `online_rls_ewma.py` — `OnlineRLSEWMACausalZ` | Por passo: inovação `s` via RLS; **Z causal** com μ e σ do **passo anterior**; atualização EWMA de μ e variância; depois atualização de θ no RLS. |
| **Regressão recursiva** | `rls_regression.RLSRegression2D` (import) | Estima dinamicamente o hedge **β** (e intercepto) com fator de esquecimento λ. |
| **Gateway / orquestração** | `10_mt5_gateway_V10_4_OMNIPRESENT.py` — `OmegaOmnipresent` | Perfis `(span, λ, min_hold)`; geração de `side` a partir de Z; escrita de logs com SHA3-256 por linha. |
| **Execução simulada** | `ExecutionManagerV104` | Cooldown, *opportunity cost* proxy `abs(y - 0.5*x)`, ordens MT5 apenas em `DEMO_LIVE`. |

**Possível falha de arquitetura de validação (não de infraestrutura):** O sistema separa bem **código** e **logging**, mas **não possui**, no desenho analisado, um **serviço de QA** que falhe o *build* se o stress não produzir uma **distribuição mínima** de sinais alinhada ao desenho quantitativo. Isso é **omissão de critério de aceitação**, não necessariamente falha de *runtime* MT5.

---

## 5. Variáveis, métricas e parâmetros críticos

### 5.1 Perfis no gateway (fonte de verdade do código)

Trecho relevante de `10_mt5_gateway_V10_4_OMNIPRESENT.py`:

```211:215:C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\10_mt5_gateway_V10_4_OMNIPRESENT.py
        profiles = [
            ("SCALPING", 20, 0.995, 3),
            ("DAY_TRADE", 100, 0.985, 5),
            ("SWING_TRADE", 500, 0.960, 20)
        ]
```

| Perfil | `ewma_span` | λ (RLS forgetting) | `min_hold` (barras) | Memória efetiva RLS *N* ≈ 1/(1−λ) |
|--------|-------------|---------------------|----------------------|-----------------------------------|
| SCALPING | 20 | 0.995 | 3 | **200** barras |
| DAY_TRADE | 100 | 0.985 | 5 | **≈ 67** barras |
| SWING_TRADE | 500 | 0.960 | 20 | **25** barras |

**Nota:** A fórmula *N ≈ 1/(1−λ)* é **heurística padrão** para memória de filtros recursivos; o RLS bidimensional pode exibir dinâmica ligeiramente diferente, mas a **ordem de grandeza** permanece relevante para *design*.

### 5.2 Disparo de sinal

```160:163:C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\10_mt5_gateway_V10_4_OMNIPRESENT.py
            if z >= 3.75: side = "SHORT"
            elif z <= -3.75: side = "LONG"
```

- **Limiar:** 3,75 σ (no sentido do Z produzido pelo motor, não necessariamente Gaussianidade estrita).
- **Consequência:** Poucos eventos extremos ⇒ poucos `signal_fired` mesmo com motor “saudável”.

### 5.3 Contrato do motor `OnlineRLSEWMACausalZ`

- **α (EWMA):** `alpha = 2 / (ewma_span + 1)` — ver `online_rls_ewma.py`.
- **Z na primeira barra:** forçado a **0** (`_n == 0`).
- **Ordem causal:** Z usa **μ e variância do passo anterior**, depois atualiza μ e variância, depois atualiza θ no RLS.

---

## 6. Hipótese de “Z colado a zero” na Demo (análise qualitativa)

**Premissas:** Se, na Demo, o utilizador observou Z quase nulo durante horas enquanto o preço se deslocou fortemente, causas **não mutuamente exclusivas** incluem:

1. **Desalinhamento memória RLS vs horizonte de trade:** λ=0,960 implica memória curta (~25 barras no modelo heurístico) enquanto `min_hold` exige 20 barras — o *spread* pode ser rapidamente “reabsorvido” pelo ajuste de β, reduzindo inovações persistentes.

2. **Limiar 3,75:** Eventos reversíveis frequentes podem **não** atingir 3,75 em Z causal se σ EWMA não for pequena o suficiente (ou se o spread for pequeno face ao denominador).

3. **Par XAU/XAG e sincronização:** Desvio na qualidade do *merge* temporal ou diferenças de microestrutura podem alterar o spread versus o obtido no stress offline.

4. **Confusão de evidência:** O stress local **mostra** centenas de disparos; a Demo precisa de **log próprio** para conciliar.

**O que esta auditoria não afirma:** Que a Demo “não operou” por um único motivo isolado — isso exige **log da Demo** e eventual reprodução com os mesmos parâmetros.

---

## 7. Omissões, vieses de processo e “negligência” (quadro organizacional)

| Tema | Descrição | Severidade |
|------|-----------|------------|
| **Critério de aceitação cego** | Aprovar versão apenas por **0 exceções**, **hash OK** e **drawdown 0** ignora **volumetria de sinais** e **plausibilidade estatística**. | Alta |
| **Testes automatizados** | Testes que só verificam **convergência vetorial / formato** não substituem `assert` sobre **mínimo de trades ou de `signal_fired`** em stress representativo. | Alta |
| **Viés de confirmação interpretativo** | Atribuir Z≈0 a “falta de volatilidade” sem cruzar **range de preço** vs **série de Z** é **falha de metodologia de leitura**, não de mercado. | Média |
| **Custódia de artefactos** | Discrepância entre relatório (“0 sinais”) e medição atual (**centenas**) exige **controlo de versão** dos CSVs e **rastreio** (commit, hash, comando de geração). | Alta |

**Nota legal / ética:** O termo **negligência** aqui designa **defeito de dever de cuidado em processos de validação quantitativa**, no sentido de engenharia e governança de risco. **Não** constitui conclusão jurídica.

---

## 8. Recomendações técnicas e de governança

1. **Reconciliação imediata:** Executar script de auditoria (ver anexo) sobre **os mesmos ficheiros** citados no relatório forense que alegou zero sinais; se os números divergirem, **declarar incidente de custódia de dados**.

2. **Gate de QA (`audit_trade_count.py` ou equivalente):** Falha de pipeline se, por exemplo, `signal_fired.sum() == 0` **ou** abaixo de um **mínimo** definido por perfil e por dataset de referência.

3. **Sanidade numérica:** Política explícita para Z (ex.: *clip* a ±20 após warm-up, ou exclusão das primeiras *N* barras das métricas).

4. **Calibração:** Reavaliar **λ**, **`ewma_span`** e **limiar Z** em conjunto — qualquer alteração deve ser **registada** com *backtest* e análise de **falsos positivos**.

5. **Demo:** Arquivar CSV completo com **timestamp**, **perfil**, **versão git**, e **parâmetros**; comparar distribuição de Z com stress.

---

## 9. Limitações desta auditoria

- Não foi verificado o **relatório forense original** nem a sua **cadeia de custódia** fora deste workspace.
- Não foi reexecutado o motor sobre dados crus **nesta** sessão.
- Os valores extremos de **Z** não foram decompostos barra a barra (exige depuração dedicada).

---

## 10. Anexo — Script de reprodução das métricas

```python
"""Reproduz contagens ATF-OMEGA-V10.4-20260330 — ajustar BASE se necessário."""
import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
            r"\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao")

for name in ["STRESS_2Y_SWING_TRADE.csv", "STRESS_2Y_DAY_TRADE.csv", "STRESS_2Y_SCALPING.csv"]:
    df = pd.read_csv(BASE / name)
    sf = int(df["signal_fired"].sum())
    thr = int((df["z"].abs() >= 3.75).sum())
    wild = int((~df["z"].between(-1e6, 1e6)).sum())
    print(f"{name}: signal_fired_True={sf} |z|>=3.75={thr} pathological_z={wild}")
```

---

## 11. Tabela “O que pode / não pode ser afirmado”

| Afirmação | Nível de confiança | Base |
|-----------|-------------------|------|
| Nos três CSVs listados na secção 3, existem centenas de `signal_fired` verdadeiros. | Alta | Contagem direta |
| `signal_fired` coincide com `|z| ≥ 3.75` nesses ficheiros. | Alta | Igualdade numérica das contagens |
| O relatório que alega **zero** sinais referiu-se aos **mesmos** ficheiros agora medidos. | Baixa | Não verificado o pacote original |
| A Demo não gerou ordens **apenas** por λ=0,960. | Baixa | Falta análise do log de Demo |
| Existe omissão de *gate* de volumetria de sinais no processo de QA descrito. | Média | Ausência no desenho revisto + boas práticas |

---

**Fim do documento ATF-OMEGA-V10.4-20260330**
