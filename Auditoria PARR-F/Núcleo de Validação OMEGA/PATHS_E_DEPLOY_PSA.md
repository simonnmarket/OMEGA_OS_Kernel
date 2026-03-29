# Caminhos oficiais e deploy PSA (Antigravity / nebular-kuiper)

| Papel | Caminho |
|--------|---------|
| **Raiz do projecto (PSA / sistema)** | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper` |
| **Núcleo de execução** (gateways MT5 v8.2.1–v8.2.6, blocos OLS/Kalman, etc.) | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F` |
| **Padrão ouro de validação** (motor paridade v1.1.0, RLS/EWMA causal) | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA` |
| **Pacote de entrega PSA** (pytest 15 passed, declaração, A1–A4) | `...\Núcleo de Validação OMEGA\PSA_ENTREGA_NUCLEO_20260327\` |

**Espelho de desenvolvimento (Cursor):** pode existir cópia em `C:\Users\Lenovo\.cursor\nebular-kuiper\...` — a **fonte operacional** que o PSA deve usar é a árvore **`.gemini\...\nebular-kuiper`** após sincronização.

---

## O que pedir ao PSA para gravar no repositório

1. **Copiar / sincronizar** para `Núcleo de Validação OMEGA` na raiz **gemini** (não só na pasta da entrega):
   - Todo o conteúdo do pacote: `tests/`, `*.py`, `requirements.txt`, `DOCUMENTO_TECNICO_*`, `TECH_SPEC_*`, `DEFINICOES_*`, `CHARTER_*`, `ORDEM_OFICIAL_*`, `INSTRUCAO_EXECUCAO_EMPIRICA_PSA.md`, `run_empirical_parity_real_data.py`, `PATHS_E_DEPLOY_PSA.md`, `INDICE_ENTREGA_PSA.md`.
2. **Manter** `PSA_ENTREGA_NUCLEO_20260327` como **snapshot** da entrega homologada (não substituir sem nova data).
3. **Dados OHLCV:** se os CSV não existirem sob `.gemini`, o PSA deve **copiar** os pares usados (ex.: `XAUUSD_M1.csv`, `AUDJPY_M1.csv`) para uma pasta versionada no projecto, por exemplo:  
   `Auditoria PARR-F\Núcleo de Validação OMEGA\dados_ohlcv_referencia\`  
   e usar **esses** caminhos no script empírico — assim o relatório é reprodutível sem depender de `.cursor\OMEGA_OS_Kernel`.

---

## Comando empírico — versão **gemini** (ajustar só os CSV se estiverem noutra pasta)

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA"

python run_empirical_parity_real_data.py `
  --y-csv "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\dados_ohlcv_referencia\XAUUSD_M1.csv" `
  --x-csv "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\dados_ohlcv_referencia\AUDJPY_M1.csv" `
  --out-dir ".\PSA_EMPIRICA_OUT_MANUAL"
```

- Se ainda **não** criaste `dados_ohlcv_referencia`, usa temporariamente os caminhos absolutos onde os CSV **realmente** estão (incluindo `.cursor\OMEGA_OS_Kernel\...` **só** enquanto forem a única cópia).
- O importante é: **`Set-Location` = pasta do Núcleo na árvore gemini**; **`--y-csv` / `--x-csv` = ficheiros que existem nessa máquina**.

---

## pytest na árvore gemini (antes ou depois do empírico)

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA"
pip install -r requirements.txt
python -m pytest tests -v --tb=short
```

Resultado esperado: **15 passed**.

---

## Resposta directa

- **Sim:** faz sentido pedir ao PSA para **gravar na raiz do projecto gemini** (`nebular-kuiper`) e em **`Auditoria PARR-F\Núcleo de Validação OMEGA`** os mesmos ficheiros que tens no pacote (código, testes, documentos) + **entregas futuras** (ex.: saídas `PSA_EMPIRICA_OUT_*`).
- O comando que tinhas estava **correcto em estrutura**, mas os paths **`Set-Location` e CSV** devem ser os da **gemini** (acima), não os de `.cursor`, salvo se só lá existirem os dados.

---

**Fim — PATHS_E_DEPLOY_PSA v1.0**
