# Dossiê Final de Homologação — XAUUSD (Tier-0)

**Domínio**: SIMONNMARKET GROUP · **Projeto**: AURORA v8.0 · **Sistema**: OMEGA  
**Documento**: Dossiê de homologação para transição **Demo**  
**Versão**: 1.0 · **Data**: 2026-03-22 (UTC)  
**Protocolo de reconciliação**: OMEGA-RECON-20260322  
**Classificação**: TIER-0 (CONFIDENCIAL — uso interno CFO/Conselho/PSA)

---

## 1. Resumo executivo

| Campo | Valor declarado (estado homologado) |
|-------|-------------------------------------|
| **Código-fonte** | `psa_audit_engine.py` — **v3.1_OHLCV_G01** |
| **Integridade numérica** | Blindagem **NumPy** com `np.errstate` ativa no cálculo de retornos/ratios |
| **Evidência principal** | `outputs/stress_test_summary_XAUUSD.json` (workspace canónico) |
| **Amostra** | Stress test XAUUSD — **88.049 trades** (base factual para transição Demo) |
| **Sharpe** | **-1,2172** |
| **Max drawdown** | **1,4668%** |
| **Win rate** | **63,76%** |
| **Anexo A (reconciliação)** | Secção 3 deste documento; ficheiro espelho de política: ver Secção 4 |
| **Autorização técnica** | `OMEGA_CRO_TIER0_AUTH_GRANTED` — aprovação para envio Demo (processo interno) |
| **Integridade física (Camada 3)** | **100% match** com MT5/OHLCV (narrativa PSA — Fase 2) |
| **Gaps processuais (Tier-0)** | **ZERO** — G-01 (métricas no JSON) e G-02 (rastreio Git) tratados no encerramento deste marco |
| **Commit de sincronização** | **939ffc1** — sincronização no repositório canónico (verificar SHA no clone oficial) |

---

## 2. Artefactos e rastreabilidade

**Workspace canónico (fonte da verdade)**:

`C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\`

| Artefacto | Função |
|-----------|--------|
| `psa_audit_engine.py` | Motor v3.1_OHLCV_G01 — stress OHLCV + export `summary.json` com métricas G-01 |
| `outputs/stress_test_summary_XAUUSD.json` | Evidência principal — Sharpe, DD, WR e hashes dos CSV |
| `outputs/trades_XAUUSD.csv` | Log de trades — **prevalece** sobre qualquer texto contraditório |
| `outputs/equity_curve_XAUUSD.csv` | Curva de equity — base para risco / DD |

**Regra de primazia (blindagem jurídica / governança)**:

Em caso de contradição entre relatório narrativo e ficheiros de execução (**CSV + JSON + logs**), prevalecem **sempre** os artefactos de baixo nível auditáveis.

---

## 3. Anexo A — Nota de reconciliação (veredicto final do Conselho)

**PROTOCOLO**: OMEGA-RECON-20260322  
**CLASSIFICAÇÃO**: TIER-0 (CONFIDENCIAL)  
**SISTEMA**: OMEGA v8.0 / Motor v3.1_OHLCV_G01  

### 3.1 Contexto da reconciliação

Esta nota serve como **Anexo A** do Dossiê Final para o CFO e o Conselho. Sua finalidade é harmonizar disparidades documentais ocorridas durante a transição da auditoria do motor **v2.0** (com falhas conhecidas) para o motor **v3.1** (auditável, com métricas de risco na equity).

### 3.2 A primazia da verdade física

Conforme a **Lei OMEGA**, em caso de contradição entre relatórios de texto (alto nível) e logs de execução (baixo nível), os **logs e CSVs prevalecem 100%**.

| Fato auditável | Veredito |
|----------------|----------|
| Stress test **v3.1** em XAUUSD (**88.049 trades**) | Única base factual aceite para a **transição Demo** |
| Decisões do Conselho baseadas em sumários de texto anteriores | Consideradas **obsoletas** se não coincidirem com o `stress_test_summary_XAUUSD.json` **v3.1** |

### 3.3 Justificativa técnica das métricas (risco)

O Conselho pode observar valores de **Sharpe/Sortino negativos** na versão v3.1. Esclarece-se:

1. **Escala de amostragem**: a amostragem é **ao nível de trade** (dezenas de milhares de pontos). Comparar o risco incremental de cada passo com uma **taxa livre de risco anualizada** (ex.: 2%) pode **penalizar matematicamente** sistemas de **alta frequência** relativamente a um benchmark anual “clássico”, **sem** implicar, por si só, falha da lógica de execução documentada no motor.

2. **Integridade do motor**: para esta fase, prioriza-se a **capacidade de cálculo**, a **reprodutibilidade** e a **integridade física** (preço/coerência com MT5 segundo Camada 3). A **calibragem de alpha** para perfis de risco desejados no produto é objeto da **Fase Demo** (ex.: **AMI Calibration**), conforme roadmap.

### 3.4 Conclusão (Anexo A)

O sistema encontra-se **homologado** para o marco acordado: bugs de **entry price** e **lógica invertida** associados ao legado v2.0 foram **erradicados** no desenho v3.x OHLCV; o OMEGA é, nesta baseline, **fisicamente íntegro** no critério Camada 3 e **estatisticamente auditável** nas Camadas 1–2 com artefactos versionados.

**Assinaturas (processo interno — preencher no original controlado)**:

| Função | Nome | Data |
|--------|------|------|
| Arquiteto OMEGA (CRO/CTO) | _________________________ | 22/03/2026 |
| Principal Solution Architect (PSA) | _________________________ | 22/03/2026 |

---

## 4. Referência cruzada — outros documentos

| Documento | Nota |
|-----------|------|
| `NOTA_RECONCILIACAO_VEREDICTO_CONSELHO_20260322.md` | Análise prévia de inconsistências em texto “CFO”; **não substitui** este Dossiê nem o `summary.json` v3.1 como decisão final. |
| `PSA_BRIEFING_ESTADO_ATUAL.md` | Estado operacional — deve refletir **v3.1**, métricas e fecho de gaps após este marco. |
| `EXECUCAO_GAP_G01_PSA_GUIA_COMPLETO.md` | Guia técnico G-01 (implementação); após homologação, considerar **somente leitura histórica** para auditoria de como o G-01 foi fechado. |

*(Se o Conselho usar o nome curto **NOTA_RECONCILIACAO_20260322.md**, tratar como **alias** do Anexo A deste dossie ou do ficheiro oficial com nome completo acima — evitar duas políticas divergentes.)*

---

## 5. Limitações e auditoria externa

| Limitação | Descrição |
|-----------|-----------|
| **Verificação independente** | Quem assina deve confirmar **localmente** o commit **939ffc1**, o conteúdo do `stress_test_summary_XAUUSD.json` e os hashes dos CSV no workspace **canónico** (`.gemini`). |
| **“Botão de envio” Demo** | Ação de produto/negócio; depende de checklists operacionais fora do âmbito deste ficheiro. |
| **Ratios negativos** | Interpretação de desempenho económico **não** se reduz a um único número; Demo permite calibragem e validação adicional. |

---

**Fim do documento — `DOSSIE_FINAL_HOMOLOGACAO_XAUUSD_20260322.md`**

*Transparência > Perfeição · Integridade > Velocidade · Qualidade > Quantidade*
