# Instrução completa — execução empírica objetiva (dados reais, sem projeção)

| Campo | Valor |
|--------|--------|
| Documento | INSTRUCAO_EXECUCAO_EMPIRICA_PSA |
| Versão | 1.0 |
| Alinhamento | `OMEGA-DEFINICOES-v1.1.0` Métrica 10; `DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md` §11 |
| Script | `run_empirical_parity_real_data.py` (na raiz desta pasta) |

---

## 1. Objectivo

Executar, de forma **repetível e auditável**, o relatório de **paridade / deriva** entre:

- **10.A** — EWMA pandas `shift(1)` vs recursiva **no mesmo spread** produzido pelo batch V8.2.1;
- **10.B** — Pipeline batch completo (OLS em janela + Z) vs motor **online** (RLS + EWMA),

usando **apenas** séries lidas de ficheiros CSV já colectados — **sem** interpolação, **sem** preenchimento de buracos, **sem** simulação de preços futuros.

O alinhamento temporal é **`INNER JOIN`** na coluna `time` (string exact match). Se não houver intersecção, o script termina com erro explícito.

---

## 2. Pré-requisitos

1. Pasta **`Núcleo de Validação OMEGA`** (ou cópia entregue ao PSA) com o código e `requirements.txt`.
2. Python 3.10+ e `pip install -r requirements.txt` (inclui `pandas`).
3. **Dois** CSV no formato já usado pelo projecto:
   - Coluna temporal: `time` (por defeito).
   - Coluna de valor: `linha` (por defeito — séries “grafico_linha” em `OMEGA_OS_Kernel/OHLCV_DATA`).

---

## 3. Dados reais de referência (máquina de desenvolvimento)

Caminhos típicos **neste workspace** (ajustar se o PSA usar outro disco):

```text
C:\Users\Lenovo\.cursor\OMEGA_OS_Kernel\OHLCV_DATA\grafico_linha\XAUUSD_M1.csv
C:\Users\Lenovo\.cursor\OMEGA_OS_Kernel\OHLCV_DATA\grafico_linha\AUDJPY_M1.csv
```

**Regra:** o par (y, x) deve ser **definido e documentado** (ex.: ouro vs AUDJPY como proxy macro) — não é “projeção”, são dois ficheiros observados. Se o Conselho preferir outro par (mesmo timeframe), alterar apenas os caminhos, mantendo o mesmo script.

---

## 4. Comando de execução (PowerShell)

Na raiz da pasta do núcleo:

```powershell
Set-Location -LiteralPath "<CAMINHO>\Núcleo de Validação OMEGA"

python run_empirical_parity_real_data.py `
  --y-csv "C:\Users\Lenovo\.cursor\OMEGA_OS_Kernel\OHLCV_DATA\grafico_linha\XAUUSD_M1.csv" `
  --x-csv "C:\Users\Lenovo\.cursor\OMEGA_OS_Kernel\OHLCV_DATA\grafico_linha\AUDJPY_M1.csv" `
  --window-ols 500 `
  --ewma-span 100 `
  --forgetting 0.995 `
  --out-dir ".\PSA_EMPIRICA_OUT_MANUAL"
```

Parâmetros opcionais úteis:

| Argumento | Significado |
|-----------|-------------|
| `--time-col` | Nome da coluna de tempo se diferente de `time` |
| `--value-col` | Nome da coluna de preço se diferente de `linha` |
| `--window-ols` | Janela OLS batch (padrão 500) |
| `--ewma-span` | Span EWMA (padrão 100) |
| `--forgetting` | \(\lambda\) RLS online (padrão 0.995) |
| `--p0-scale` | Prior RLS (padrão 1e4) |
| `--eps` | Estabilidade denominador Z |

Se `--out-dir` for omitido, cria-se automaticamente `PSA_EMPIRICA_OUT_<timestamp UTC>` nesta pasta.

---

## 5. Artefactos gerados (entrega PSA)

Na pasta de saída:

| Ficheiro | Conteúdo |
|----------|----------|
| `RELATORIO_EMPIRICO_PARIDADE.json` | Metadados, SHA-256 dos CSV, parâmetros, estatísticas de merge, dicionários 10.A e 10.B |
| `RELATORIO_EMPIRICO_PARIDADE.txt` | Mesmo conteúdo legível para arquivo |
| `serie_alinhada_merge.csv` | **Histórico completo** após inner join (reprodução do universo usado no cálculo) |

---

## 6. Critérios de sucesso da execução (objectivos)

1. O script **termina sem excepção** e imprime `Concluído. Pasta de saída: ...`.
2. `merge_stats.n_rows_after_inner_join` > 0 e coerente com o esperado (ordem de grandeza ~ dezenas de milhares se M1 completo).
3. Os campos `sha256_y` e `sha256_x` no JSON permitem verificar integridade dos ficheiros de origem.
4. **Não** se exige MSE ≈ 0 em 10.B — interpretação conforme notas no JSON e Métrica 10 nas DEFINIÇÕES.

---

## 7. O que NÃO fazer

- Não usar CSV gerado por modelo preditivo ou “fill forward” artificial sem ordem explícita.
- Não alterar timestamps para forçar merge — isso invalida a auditoria.
- Não confundir este relatório com P&L, Sharpe ou backtest de estratégia.

---

## 8. Arquivamento

1. ZIP da pasta `--out-dir` + cópia dos **dois** CSV de entrada (ou registo dos hashes se os CSV já estiverem em arquivo imutável).
2. Anexar o JSON ao dossiê da fase empírica.

---

**Fim da instrução v1.0**
