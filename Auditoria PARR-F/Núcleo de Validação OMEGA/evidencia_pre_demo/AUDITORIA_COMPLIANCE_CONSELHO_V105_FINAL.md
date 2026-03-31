# Dossiê executivo de auditoria, compliance de dados e governança Tier-0

**Projeto OMEGA — Transição V10.4 → V10.5 (SWING)**

| Campo | Valor |
|-------|--------|
| **Classificação** | Confidencial / Nível Conselho Executivo (Board Level) |
| **ID do documento** | AUDIT-COMPLIANCE-BOARD-V10.5-FINAL |
| **Data da auditoria** | 31 de março de 2026 |
| **Engenharia (PSA)** | Antigravity MACE-MAX |
| **Rastreabilidade Git HEAD (Tier-0)** | `1632010c59aec1724ed25031d5637db83a546641` |

---

## I. Introdução e declaração de verdade mestra

Este dossiê atesta a conformidade, integridade criptográfica e sanitização algorítmica do núcleo quantitativo OMEGA V10.5. Instituiu-se a **Verdade Unificada** (`PACOTE-PSA-VU-20260331`), determinando que **nenhuma métrica** apresentada a este Conselho baseia-se em extrações subjetivas, palpites ou estatísticas infladas por erro de medição.

Todos os valores, percentis e contagens aqui listados foram obtidos por **scripts autónomos** de compliance (`audit_trade_count.py`, `verify_tier0_psa.py`) e ancorados nos hashes **SHA3-256** presentes no manifesto central (`MANIFEST_RUN_20260329.json`), **desde que** o `HEAD` do repositório e o manifesto estejam sincronizados no momento da verificação (ver Anexo A).

---

## II. Gestão de chaves e custódia do motor limitador (parâmetros)

As premissas foram emparelhadas ao orquestrador live (`11_live_demo_cycle_1.py`, versão **1.3.0**), com paridade de intenção entre laboratório e ponte MT5.

| Parâmetro de integridade | Valor blindado | Descrição (visão Board) |
|---------------------------|----------------|-------------------------|
| Ativos (cointegração) | XAUUSD / XAGUSD | Metais de liquidez profunda pareados pelo motor. |
| Ponto gravitacional (λ) | 0.9998 | Memória efectiva \(N \approx 1/(1-\lambda)\) → ordem de **5000** barras (referência teórica). |
| Estabilizador EWMA (span) | 500 | Alisamento da variância no ramo EWMA (código: `SPAN_WARMUP`). |
| Gatilho de disparo (Z) | \|Z\| ≥ 2.0 | Limite fixo; substitui a configuração anterior mais restritiva (ex.: 3.75 em contextos históricos). |
| Proteção de aquecimento | 20.000 barras M1 | Histórico por ativo antes do ciclo live (evita variância inicial patológica). |
| VitalSignsMonitor | Desvio-padrão de \|Z\| na janela inferior a 0,05 (30 barras) | **SystemError** se \|Z\| ficar “plano” na janela — mitigação de flatline sem ordem humana. |

---

## III. Fase C — Compliance de stress histórico (V10.5 SWING)

### 1. Dados probatórios (input/output)

| Item | Valor |
|------|--------|
| Ficheiro analisado | `STRESS_V10_5_SWING_TRADE.csv` |
| Assinatura SHA3-256 (ficheiro completo) | `112b5958dfc3e9c4e157d63304f500d5cb02e07a8fe1a47f723d08027d0d36df` |
| Condição da base | 100.000 linhas no stress de referência; integridade temporal conforme pipeline de geração (sem “vazamento” deliberado de futuro). |

### 2. Resultados objectivos (stdout do validador)

| Métrica | Valor atestado |
|---------|----------------|
| Total de barras (linhas) | 100.000 |
| `signal_fired_true` | **222** |

*Nota comparativa:* contagens de **outros** ficheiros de stress (ex.: V10.4 / limiares distintos) **não** são o mesmo universo estatístico; comparações “222 vs 402” exigem explicitar **dois** CSVs e **duas** configurações.

### 3. Parecer sobre a distribuição do Z-Score (percentis)

| Estatística | Valor (script) |
|-------------|----------------|
| P50 (\|Z\|) | ≈ 0.6957 |
| P95 (\|Z\|) | ≈ **1.8858** |

Os disparos com \|Z\| ≥ 2.0 ocorrem onde a regra de negócio e o motor coincidem; a narrativa de “sniper” é **interpretativa**; o **número** 222 é **facto** reprodutível via `audit_trade_count.py`.

---

## IV. Fases D e E — Mitigação no feed ao vivo (demo MT5)

**Protecções aplicadas (hotfixes):**

1. **Trava anti-drift (sincronia M1):** não processar barra se o timestamp de XAGUSD ≠ timestamp de XAUUSD (evita spread cointegrado com desalinhamento temporal).
2. **PnL / métricas:** qualquer métrica de PnL “bonita” sem extrato de broker permanece **fora** do âmbito deste dossiê; o registo `05_metrics_registry.csv` documenta definições; a prova operacional final exige **extrato** do broker quando aplicável.

---

## V. Veredito oficial de governança (Tier-0)

Com base no manifesto `MANIFEST_RUN_20260329.json` e no protocolo `verify_tier0_psa.py`, certifica-se que a árvore digital, relatórios, geradores de logs e ficheiros Python **rastreados** foram auditados pelo **processo** Tier-0.

**Critério de sucesso objectivo:** execução de `verify_tier0_psa.py` com **última linha** `ESTADO: OK (Tier-0 verificação automática passou)` e **código de saída 0**.

O sistema encontra-se **rastreável** ao nível de ficheiros e hashes; a continuidade da **Fase E** (demo) depende de **execução** live adicional à custódia de disco.

---

**MACE-MAX | Antigravity**  
Lead Architect & Auditoria forense independente

---

## Anexo A — Comandos de verificação (para o Conselho ou auditor externo)

**Definir raiz do repositório (PowerShell):**

```powershell
Set-Location -LiteralPath "<RAIZ_NEBULAR_KUIPER>"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
```

**1) Integridade Tier-0 (manifesto + HEAD + SHA3 dos ficheiros listados):**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verify_tier0_psa.py"
```

**2) Métricas objectivas do CSV de stress (copiar stdout integral para arquivo):**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\audit_trade_count.py" `
  --csv "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao\STRESS_V10_5_SWING_TRADE.csv"
```

**3) Confirmar SHA do HEAD local:**

```powershell
git rev-parse HEAD
```

*O valor deve coincidir com `git_commit_sha` no manifesto e com a linha “Rastreabilidade Git HEAD” deste dossiê **após** o PSA sincronizar o manifesto e o repositório.*

---

## Anexo B — Limitações declaradas (não opcionais)

- Este dossiê **não** prova lucro futuro nem desempenho em conta real; prova **custódia** e **processo** de verificação.
- Números de stress **offline** não substituem **log** de demo MT5 (`DEMO_LOG_*.csv`) para paridade E2E.
- Se o `HEAD` do repositório divergir do citado no cabeçalho, prevalece a **verificação** na máquina do auditor (`git rev-parse` + `verify_tier0_psa.py`).

---

*Fim do documento AUDIT-COMPLIANCE-BOARD-V10.5-FINAL*
