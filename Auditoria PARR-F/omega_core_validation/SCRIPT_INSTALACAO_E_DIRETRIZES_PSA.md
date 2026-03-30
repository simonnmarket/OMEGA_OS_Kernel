# Script de instalação e diretrizes — Núcleo de Validação OMEGA (entrega PSA)

| Campo | Valor |
|--------|--------|
| Destinatário | PSA (validação / reprodutibilidade) |
| Pasta de entrega | `Núcleo de Validação OMEGA` |
| Protocolo métricas | `OMEGA-DEFINICOES-v1.1.0` (ficheiro incluído) |
| Documento técnico núcleo | `DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md` (v1.1) |

---

## 1. Objectivo desta etapa

1. **Instalar** o ambiente Python e dependências.
2. **Executar** a suíte de testes automatizados e **registar** o resultado (log).
3. **Não** interpretar ainda lucro ou decisão comercial — apenas **comprovar** que o código do núcleo e as métricas auxiliares (engajamento, paridade) passam nos testes no ambiente PSA.
4. **Preparar** a fase seguinte: testes empíricos com dados reais + hashes (fora do âmbito mínimo deste script, mas listados nas diretrizes finais).

---

## 2. Pré-requisitos

| Item | Requisito |
|------|-----------|
| SO | Windows 10/11 (ou Linux/macOS com ajuste de caminhos) |
| Python | **3.10+** recomendado; **3.11** validado no desenvolvimento |
| Rede | Apenas para `pip install` (numpy, pandas, pytest) |
| Permissões | Leitura/escrita na pasta de entrega |

**Verificar versão:**

```powershell
python --version
```

Se `python` não existir, usar `py -3.11 --version` ou o launcher instalado no sistema.

---

## 3. Instalação (ordem obrigatória)

### 3.1. Abrir terminal na pasta correta

No PowerShell:

```powershell
Set-Location -LiteralPath "<CAMINHO_COMPLETO>\Núcleo de Validação OMEGA"
```

Exemplo no ambiente de origem:  
`C:\Users\Lenovo\.cursor\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA`  
(Ajuste se a pasta for movida para outro disco, VM ou repositório PSA.)

### 3.2. Ambiente virtual (recomendado)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Se a execução de scripts estiver bloqueada:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3.3. Dependências do núcleo

```powershell
pip install -r requirements.txt
```

Conteúdo esperado: `numpy`, `pandas`, `pytest` (conforme `requirements.txt` da entrega).

### 3.4. Validação da instalação

```powershell
python -c "import numpy, pandas, pytest; print('OK', numpy.__version__, pandas.__version__)"
```

---

## 4. Execução dos testes (critério de sucesso mínimo)

Na **raiz** desta pasta (onde estão `rls_regression.py`, `requirements.txt`, pasta `tests/`):

```powershell
python -m pytest tests -v --tb=short
```

**Sucesso:** `15 passed` (ou o número indicado no `TECH_SPEC_OMEGA_CORE_VALIDATION.md` se futuramente alterado).

**Falha:** copiar **todo** o output do terminal para o relatório PSA; não alterar código sem autorização do Tech Lead.

### 4.1. Registo obrigatório para o PSA

Guardar ficheiro de texto, por exemplo `PSA_RESULTADO_PYTEST_YYYYMMDD.txt`, contendo:

- Data/hora UTC
- `python --version`
- `pip freeze` (ou lista das versões principais)
- Output completo de `pytest -v`

---

## 5. Diretrizes de trabalho (governança)

1. **Não misturar camadas:** métricas de **sinal** (spread, Z no código Python) ≠ métricas de **performance** (Sharpe, drawdown no `DEFINICOES_TECNICAS_OFICIAIS.md`). A taxonomia está na secção **TAXONOMIA OFICIAL** das definições v1.1.
2. **Paridade batch vs online:** o relatório `parity_report.py` **quantifica** diferenças; MSE alto **pode** ser estrutural (OLS em janela vs RLS). Não concluir “bug” sem análise — ver Métrica 10 nas definições.
3. **n=0 trades:** usar convenções oficiais (`engagement_metrics.performance_placeholders_when_n_trades_zero`); não reportar winrate fictício.
4. **Reprodutibilidade:** quando usar dados reais na fase seguinte, calcular **SHA3-256** por ficheiro e anexar ao relatório (requisito citado nas definições v1.1).
5. **Alterações ao código:** qualquer patch deve vir acompanhado de **novos ou actualizados testes** e actualização do `DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md` (matriz de comprovação).

---

## 6. Estrutura desta entrega (o que está na pasta)

| Caminho / ficheiro | Função |
|--------------------|--------|
| `rls_regression.py`, `v821_batch.py`, `online_rls_ewma.py` | Núcleo matemático |
| `engagement_metrics.py`, `parity_report.py` | Métricas 9 e 10 (DEFINICOES) |
| `tests/*.py` | Provas automatizadas |
| `requirements.txt` | Dependências pip |
| `DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md` | Especificação e matriz de comprovação |
| `TECH_SPEC_OMEGA_CORE_VALIDATION.md` | Índice curto |
| `DEFINICOES_TECNICAS_OFICIAIS.md` | Métricas 1–10 e taxonomia v1.1.0 |
| `SCRIPT_INSTALACAO_E_DIRETRIZES_PSA.md` | Este ficheiro |

---

## 7. Após sucesso dos testes — próximos passos (empíricos)

Estes itens **não** bloqueiam a validação mínima de instalação, mas são **obrigatórios** antes de conclusões sobre mercado real:

1. Carregar séries `y`, `x` reais (formato acordado com Tech Lead).
2. Correr `parity_ewma_z_pandas_vs_recursive` e `parity_full_batch_vs_online` (ver `parity_report.py`) com **parâmetros de produção** documentados.
3. Arquivar CSV + hashes + parâmetros + versão `OMEGA-DEFINICOES-v1.1.0`.
4. Só então cruzar com métricas 1–6 e engajamento (Métrica 9) a partir de logs de execução.

---

## 8. Contacto e escalação

- **Bloqueio técnico** (import errors, versão Python, pytest): anexar log completo e versões.
- **Dúvida de interpretação** métrica vs sinal: consultar primeiro `DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md` secções 2, 7 e 10.

---

**Fim do script de instalação e diretrizes — entrega para PSA.**
