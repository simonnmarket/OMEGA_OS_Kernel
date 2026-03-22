# Execução Gap G-01 — Guia completo para o PSA (motor v3.1 + métricas de risco)

**Domínio**: SIMONNMARKET GROUP · **Projeto**: AURORA v8.0 · **Sistema**: OMEGA  
**Documento**: Guia técnico executável  
**Versão**: 1.0 · **Data**: 2026-03-22 (UTC)  
**Autoridade**: Alinhado a `DEFINICOES_TECNICAS_OFICIAIS.md` (equity curve), ratificação CTO/CRO (Nota de Reconciliação), `INSTRUCOES_PSA_TIER0_COMPLETAS.md`

---

## 1. Objetivo do G-01

| Item | Descrição |
|------|-----------|
| **Gap** | G-01 — ausência de Sharpe, Sortino e Calmar no `stress_test_summary_{SYMBOL}.json` |
| **Meta** | Atualizar `psa_audit_engine.py` para **v3.1**: calcular métricas **a partir da série de equity** (não a partir de PnL por trade isolado) e gravar no `summary.json` |
| **Critério de fecho** | Camada 2 pode validar itens 2.5–2.7 sem “PENDING”; `performance` contém `sharpe_ratio`, `sortino_ratio`, `calmar_ratio` (nomes podem ser os abaixo) |

---

## 2. Onde executar (obrigatório)

**Workspace canónico (fonte da verdade):**

```
C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\
```

**Ficheiros relevantes:**

| Ficheiro | Função |
|----------|--------|
| `Auditoria PARR-F\psa_audit_engine.py` | Motor — **editar aqui** (cópia canónica) |
| `Auditoria PARR-F\outputs\equity_curve_{SYMBOL}.csv` | Entrada lógica para métricas (série `equity`) |
| `Auditoria PARR-F\outputs\stress_test_summary_{SYMBOL}.json` | Saída — deve incluir bloco de risco |
| `Documentacao_Processo\PSA_BRIEFING_ESTADO_ATUAL.md` | Atualizar após run bem-sucedido |

**Ajuste de `BASE_ROOT`**: no ficheiro `psa_audit_engine.py`, confirme que `BASE_ROOT` aponta para **esta** `Auditoria PARR-F` no disco `.gemini` (não deixar path de `.cursor` no código de produção).

---

## 3. Pré-requisitos

- Python 3.10+ com `numpy`, `pandas` (já usados pelo motor).
- Backup do `psa_audit_engine.py` atual antes de editar:  
  `copy psa_audit_engine.py psa_audit_engine.py.bak_v3.0`

---

## 4. Método de cálculo (alinhamento documentação)

- **Definição oficial** (`DEFINICOES_TECNICAS_OFICIAIS.md`): Sharpe/Sortino sobre **retornos da curva de equity** (preferência por **log-returns** em períodos longos).
- **Implementação abaixo**: usa **log-returns** \( \ln(E_t / E_{t-1}) \) para Sharpe/Sortino; Calmar = retorno anualizado estimado / max drawdown (ver código).
- **Anualização**: pontos da equity são por **trade** (alta frequência). Usa-se **`periods_per_year`** configurável (ex.: 252 se reinterpretar como “dia”; para **passos de trade** o PSA pode ajustar após calibragem — documentar o valor escolhido no briefing).

**Se o Conselho exigir exatamente a fórmula do patch CTO (retornos simples `diff/equip[:-1]`)**, substituir o bloco interno de retornos pela versão “simples” documentada na Secção 8 (alternativa).

---

## 5. Script Python — função `calculate_risk_metrics_g01` (copiar para `psa_audit_engine.py`)

Colocar **após** os imports e **antes** da classe `PSAAuditEngineV3` (ou como função de módulo no topo, após `logger`).

```python
def calculate_risk_metrics_g01(
    equity_series: np.ndarray,
    periods_per_year: float = 252.0,
    risk_free_rate_annual: float = 0.02,
) -> Dict[str, Any]:
    """
    G-01: Sharpe / Sortino / Calmar a partir da curva de equity (log-returns).
    equity_series: valores estritamente positivos de equity, ordem temporal.
    """
    out = {
        "sharpe_ratio": None,
        "sortino_ratio": None,
        "calmar_ratio": None,
        "max_drawdown_pct": None,
        "total_return_pct": None,
        "methodology": "log_returns_equity_g01_v1",
        "periods_per_year": periods_per_year,
    }
    eq = np.asarray(equity_series, dtype=np.float64)
    if eq.size < 2 or np.any(eq <= 0) or not np.all(np.isfinite(eq)):
        logger.warning("G-01: série de equity inválida ou insuficiente.")
        return out

    # Log-returns
    returns = np.diff(np.log(eq))
    returns = returns[np.isfinite(returns)]
    if returns.size == 0:
        logger.warning("G-01: nenhum retorno log válido.")
        return out

    # Sharpe (anualizado): (mean - rf/periods) / std * sqrt(periods_per_year)
    rf_per_period = risk_free_rate_annual / periods_per_year
    mean_r = float(np.mean(returns))
    std_r = float(np.std(returns, ddof=1)) if returns.size > 1 else 0.0
    if std_r > 0:
        out["sharpe_ratio"] = round((mean_r - rf_per_period) / std_r * np.sqrt(periods_per_year), 4)
    else:
        out["sharpe_ratio"] = 0.0

    neg = returns[returns < 0]
    downside_std = float(np.std(neg, ddof=1)) if neg.size > 1 else (float(np.std(neg)) if neg.size == 1 else 0.0)
    if downside_std > 0:
        out["sortino_ratio"] = round((mean_r - rf_per_period) / downside_std * np.sqrt(periods_per_year), 4)
    else:
        out["sortino_ratio"] = 0.0

    # Max drawdown (peak-to-trough em %)
    peak = np.maximum.accumulate(eq)
    dd = (peak - eq) / peak
    max_dd = float(np.max(dd)) if dd.size else 0.0
    out["max_drawdown_pct"] = round(max_dd * 100.0, 4)

    total_return = float(eq[-1] / eq[0] - 1.0)
    out["total_return_pct"] = round(total_return * 100.0, 4)

    n = eq.size
    years = max(n / periods_per_year, 1e-12)
    if max_dd > 0:
        annual_return = (float(eq[-1] / eq[0]) ** (1.0 / years)) - 1.0
        out["calmar_ratio"] = round(annual_return / max_dd, 4) if max_dd > 0 else 0.0
    else:
        out["calmar_ratio"] = 0.0

    return out
```

**Nota**: `typing.Dict` e `Any` já estão importados em `from typing import List, Dict, Any`.

---

## 6. Integração no método `export()` da classe `PSAAuditEngineV3`

### 6.1. Proteger exportação vazia

No início de `export()`, se `not self.trades` ou `not self.equity_curve`, gravar JSON mínimo com erro e **return** (evitar `trades[0]` inexistente).

### 6.2. Extrair série de equity

```python
equity_vals = np.array([row["equity"] for row in self.equity_curve], dtype=np.float64)
risk = calculate_risk_metrics_g01(equity_vals, periods_per_year=252.0)  # ajustar após calibragem
```

### 6.3. Incluir no `summary`

Dentro de `summary["performance"]`, adicionar (exemplo):

```python
"performance": {
    "winrate": ...,
    "max_drawdown_pct": ...,
    "total_pnl": ...,
    "sharpe_ratio": risk.get("sharpe_ratio"),
    "sortino_ratio": risk.get("sortino_ratio"),
    "calmar_ratio": risk.get("calmar_ratio"),
    "risk_metrics": risk,  # opcional: objeto completo com methodology
},
```

### 6.4. Versão do motor

```python
"version": "psa_audit_engine_v3.1_OHLCV_G01"
```

---

## 7. Teste rápido (sem stress completo) — script opcional

Guardar como `Auditoria PARR-F/scripts/test_g01_risk_metrics.py` (criar pasta `scripts` se não existir):

```python
#!/usr/bin/env python3
"""Teste isolado G-01 — executar: python scripts/test_g01_risk_metrics.py"""
import numpy as np
import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Importar a função após estar em psa_audit_engine.py:
from psa_audit_engine import calculate_risk_metrics_g01

if __name__ == "__main__":
    eq = np.array([100_000.0, 100_500.0, 100_200.0, 101_000.0], dtype=np.float64)
    print(calculate_risk_metrics_g01(eq, periods_per_year=252.0))
```

---

## 8. Alternativa (retornos simples — patch CTO)

Se for necessário **alinhar byte-a-byte** ao patch CTO:

- Substituir `returns = np.diff(np.log(eq))` por:

```python
with np.errstate(invalid="ignore", divide="ignore"):
    returns = np.diff(eq) / eq[:-1]
returns = returns[np.isfinite(returns)]
```

- Recalcular Sharpe/Sortino com a mesma fórmula de anualização acima **ou** documentar ratios “raw”.

**Registar no briefing** qual variante está em produção.

---

## 9. Execução do stress test (após integração)

No PowerShell, **no diretório do projeto canónico**:

```powershell
cd "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
python psa_audit_engine.py --symbol XAUUSD --equity 100000 --risk_per_trade 0.0025
```

(Ajustar `--timeframes` e `--date_filter` conforme o vosso run oficial.)

**Verificar:**

1. `outputs\stress_test_summary_XAUUSD.json` contém `sharpe_ratio`, `sortino_ratio`, `calmar_ratio` (ou objeto `risk_metrics`).
2. Recalcular SHA3 dos CSVs e confirmar que o JSON lista hashes atualizados.

---

## 10. Atualização obrigatória do briefing

Editar **apenas** a cópia canónica: `PSA_BRIEFING_ESTADO_ATUAL.md`

- Secção **4**: novos hashes, total trades, winrate, DD, **e** valores Sharpe/Sortino/Calmar.
- Secção **6**: marcar **G-01** como **fechado** (data).
- Secção **9**: incrementar versão do briefing para **1.2**; registar versão do motor **v3.1** e commit Git (G-02).

---

## 11. Commit Git (sugestão)

```
feat(audit): G-01 risk metrics (Sharpe/Sortino/Calmar) from equity curve — v3.1

- calculate_risk_metrics_g01 + summary.json performance block
- version string psa_audit_engine_v3.1_OHLCV_G01
```

---

## 12. Checklist final (PSA)

- [ ] Edição feita em `psa_audit_engine.py` no **workspace .gemini**
- [ ] `BASE_ROOT` correto no ficheiro
- [ ] `export()` com guard para trades/equity vazios
- [ ] `stress_test_summary_*.json` com métricas G-01
- [ ] Stress test executado; hashes atualizados
- [ ] `PSA_BRIEFING_ESTADO_ATUAL.md` atualizado (canónico)
- [ ] Camada 2 reexecutada (ou script `audit_layer2`) se existir

---

**Fim do guia — `EXECUCAO_GAP_G01_PSA_GUIA_COMPLETO.md`**

*Transparência > Perfeição · Integridade > Velocidade · Qualidade > Quantidade*
