# PROPOSTA DE INTEGRAÇÃO — TRE, TEPA & USFE
## Documento para o Conselho OMEGA

**Data:** 2026-05-29
**Autor:** PSA (análise técnica)
**Versão:** 1.0
**Mandato:** CEO — Apresentação ao conselho

---

## EXECUTIVO

| Componente | Status | Pronto para Produção? |
|-----------|--------|----------------------|
| **TRE** — Temporal Resonance Engine | Desenvolvimento avançado | NÃO — falta backtesting |
| **TEPA** — Temporal Energy Propagation Architecture | Implementação funcional | NÃO — falta validação empírica |
| **USFE** — Unified Structural Field Engine | Código estável, self-test OK | NÃO — falta L4/L5/L6 |

**Recomendação conselho:** Aprovar fase de testes offline (L4/L5) antes de integração em `shadow_loop`. Estimativa: 2-3 semanas.

---

## 1. TRE — TEMPORAL RESONANCE ENGINE

### 1.1 Propósito
Framework híbrido de inteligência estrutural temporal que detecta propagação invisível, recorrência temporal, conflito observacional e preparação institucional antecipada.

### 1.2 Fundamentação
Integra market microstructure, reflexividade (Soros), behavioral finance, econofísica, complex adaptive systems e information theory.

### 1.3 Motores Principais (9 motores)

| Motor | Função | Output |
|-------|--------|--------|
| Temporal | Recorrência, sessão, atraso | TRS (0-1) |
| Structural | Persistência, propagação oculta | SPS, HPI |
| Dissipative | Armadilhas perceptivas | DI = \|visual - structural\| |
| Conflict | Incompatibilidade entre candle/line/renko | Variance |
| Resonance | Alinhamento cross-market | REI |
| Entropy | Caos, degeneração | ECI |
| Observational | Saturaçao coletiva | ODI |
| Macro | Pressão institucional | MSP |
| Adaptive | Recalibração automática | API |

### 1.4 Estado de Desenvolvimento
- ✅ Arquitetura completa (9 motores + pipeline)
- ✅ Implementação Python (3 ficheiros)
- ✅ Documentação técnica (~953 linhas)
- ⏳ Backtesting (não iniciado)
- ⏳ Integração dados reais

### 1.5 Riscos
1. Complexidade computacional não quantificada
2. Nenhum teste em produção
3. Pesos por ativo (volatility_weight, temporal_weight) precisam de calibração

---

## 2. TEPA — TEMPORAL ENERGY PROPAGATION ARCHITECTURE

### 2.1 Propósito
Sistema de análise estrutural baseado em propagação energética multi-camada. Hipótese central: "Nenhum movimento desaparece completamente."

### 2.2 Fundamentação
Mecânica dos fluidos (Navier-Stokes), termodinâmica, geometria fractal (Mandelbrot), teoria de propagação de impacto.

### 2.3 Arquitetura Multi-Camada (10 camadas)

| Camada | Nome | Função |
|--------|------|--------|
| 1 | Temporal | Timestamps, ciclos |
| 2 | Energy | Força, sustentação, exaustão |
| 3 | POC Fractal | Point of Control como ancora |
| 4 | Médias Fractais | 3 médias nascidas da POC |
| 5 | Família 3-6-9 | Ressonancia harmónica |
| 6 | Geometria de Preenchimento | Eliminar gaps estruturais |
| 7 | Propagação Residual (RIPL) | Memória pós-impacto |
| 8 | Memória de Colisão (CIM) | Regiões deformadas |
| 9 | Dissipação | Perda energética |
| 10 | Pressão Direcional | Direção provável |

### 2.4 Modelo Matemático

```
E = V x ΔP x Tf          (Energia = Volume x Deslocamento x Tempo)
PE = (V x ΔP)² / Rt    (Propagação Energética)
RF = Ei - Ed             (Fragmentação Residual)
C = d²P / dt²           (Curvatura Estrutural)
```

### 2.5 Estado de Desenvolvimento
- ✅ Implementação Python funcional (~953 linhas)
- ✅ Pipeline de processamento completo
- ✅ 6 critérios de scoring para sinal
- ⏳ Testes unitários (ausentes)
- ⏳ Validação com dados reais
- ⏳ Otimização de performance

### 2.6 Riscos
1. Sem testes unitários — cada método não validado individualmente
2. Sem tratamento de exceções robusto
3. Performance não otimizada para grandes datasets

---

## 3. USFE — UNIFIED STRUCTURAL FIELD ENGINE

### 3.1 Propósito
Unificar TRE + TEPA + Motor de Regime Macro num único motor multi-classe com calibração independente por ativo.

### 3.2 Classes de Ativo Suportadas

| Classe | Exemplos | Status |
|--------|----------|--------|
| Forex | EURUSD, GBPUSD, USDJPY | ✅ |
| Commodity | XAUUSD, XAGUSD | ✅ |
| Energy | USOIL+, UKOIL+ | ✅ |
| Crypto | BTCUSD, ETHUSD, SOLUSD | ✅ |
| Index | US500, US100, GER40 | ✅ |

### 3.3 Arquitetura

```
OHLCV + símbolo → Classificação → Calibração
                                    ↓
              ┌──────────┬──────────┬──────────┐
              ▼          ▼          ▼
         Temporal     Energy    Representação
         (TRE)       (TEPA)    candle/line/renko
              └──────────┼──────────┘
                         ▼
                    Fusão + Risco
                    (REI, ECI, DEI)
                         ▼
                    Macro Regime
                         ▼
                    Saída USFE
                    structural_signal
                    trade_bias
                    confidence
```

### 3.4 Outputs Principais

| Output | Valores | Descrição |
|--------|---------|-----------|
| structural_signal | EXPANSION / COLLAPSE / NEUTRAL | Direção estrutural |
| trade_bias | ALLOW_LONG / ALLOW_SHORT / BLOCK / NEUTRAL | Permissão de trade |
| confidence | 0..1 | Probabilidade ajustada por risco |
| macro_regime | MONETARY / RISK_OFF / LIQUIDITY_STRESS / TREND_STABLE / NEUTRAL | Contexto macro |

### 3.5 Estado de Desenvolvimento

| Componente | Ficheiro | Estado | Notas |
|-----------|----------|--------|-------|
| **USFE-A** (Baseline AIC) | `AIC/omega_usfe_engine.py` (792L) | ✅ PASS self-test | Recomendado para testes offline |
| **USFE-B** (OMEGA variant) | `Proposta/OMEGA USFE v1.0.0.txt` (1022L) | ✅ PASS self-test | Bug temporal (L309-314) a corrigir |
| **MIC-E** (Production Micro) | `Proposta/Production-Grade Component.txt` (651L) | ✅ PASS 8/8 | `register_module()` pronto |
| **MIC-D** | `Proposta/OMEGA Microstructure Tracker v1.0.0.txt` (1197L) | ⚠️ FAIL T2 | Bias sell não detetado |

### 3.6 Checklist Integração

| Nível | Critério | Status |
|-------|----------|--------|
| L1 | Self-test exit 0 | ✅ 100% |
| L2 | 5 classes testadas | ✅ 100% |
| L3 | ComponentEngine + campos OMEGA | ✅ 100% |
| **L4** | Teste CSV real (≥500 barras) | ⏳ **PENDENTE** |
| **L5** | Correlação forward return (M15/H1) | ⏳ **PENDENTE** |
| **L6** | Integração shadow_loop (hook + log) | ⏳ **PENDENTE** |

### 3.7 Riscos
1. **USFE-A vs USFE-B divergentes** — TRS e session_pressure com implementações diferentes (valores incomparáveis)
2. **Calibração JSON** — schemas diferentes entre A e B
3. **Bug USFE-B** — `numpy.std()` em `timedelta64` sem conversão

---

## 4. SINERGIAS ESTRATÉGICAS

### 4.1 Por que integrar os 3?

| Componente | Forte em | Fraco em | Complementado por |
|-----------|----------|----------|-------------------|
| TRE | Recorrência temporal, conflito observacional | Energia, POC, geometria | TEPA |
| TEPA | Energia, pressão, exaustão, geometria | Recorrência temporal, macro | TRE + Macro |
| USFE | Fusão + calibração multi-classe | Ainda não validado em produção | TRE + TEPA |

**Conclusão:** USFE é o ponto de convergência natural. TRE e TEPA isolados são incompletos; juntos cobrem ~88% dos requisitos.

### 4.2 Matriz de Fusão TRE → USFE

| Requisito TRE | Coberto no USFE | % |
|--------------|-----------------|---|
| TRS | ✅ Sim | 100% |
| HPI | ✅ Sim (proxy OHLCV) | 90% |
| SPS | ✅ Sim | 100% |
| ODI | ✅ Sim (proxy vol) | 75% |
| DI/DEI | ✅ Sim | 95% |
| Conflito 3 representações | ✅ Sim | 90% |
| MSP / macro | ✅ Sim + regimes | 85% |
| TEPA / 3-6-9 / POC | ✅ Sim (TEPA) | N/A |
| Redis/Kafka/IA | ❌ Não | 0% (roadmap) |

**Média fusão:** ~88% do contrato TRE operacional via USFE.

---

## 5. ROADMAP PROPOSTO AO CONSELHO

### Fase 1 — Estabilização Código (1 semana)
1. Corrigir bug USFE-B (TemporalCore L309-314)
2. Corrigir MIC-D Test 2 (bias sell)
3. Documentar MIC-F `NUMBA_CACHE_DIR`
4. Unificar calibração JSON (USFE-A vs B)

### Fase 2 — Validação Offline (1-2 semanas)
5. Teste CSV real ≥500 barras por componente (L4)
6. Correlação forward return M15/H1 (L5)
7. Comparar USFE-A vs USFE-B no mesmo CSV
8. Hit-rate em forward 5/10 barras (MIC-E)

### Fase 3 — Auditoria AIC (1 semana)
9. AIC audita L4/L5 resultados
10. CEO decide: APROVADO / REPROVADO para integração

### Fase 4 — Integração OMEGA (1 semana, só se aprovado)
11. Escolher USFE-A ou USFE-B (recomendação: B→v2 após correção)
12. Hook mínimo em `shadow_loop` (BLOCK se trade_bias==BLOCK)
13. Paper 48h com `ENTRIES_FROZEN`

---

## 6. RISCOS GLOBAIS

| # | Risco | Impacto | Mitigação |
|---|-------|---------|-----------|
| 1 | Nenhum componente validado em produção | ALTO | Fases L4/L5 antes de L6 |
| 2 | Complexidade computacional desconhecida | MÉDIO | Teste de performance em L4 |
| 3 | Divergência USFE-A vs B (valores incomparáveis) | MÉDIO | Escolher um; descartar outro |
| 4 | Calibração por ativo requer ajustes extensivos | MÉDIO | `usfe_calibration.json` iterativo |
| 5 | TRE/TEPA isolados são incompletos sem USFE | BAIXO | Focar em USFE como entry point |

---

## 7. DEPENDÊNCIAS TÉCNICAS

### 7.1 Python
- numpy, pandas, scipy, statistics, dataclasses
- MetaTrader5 (opcional), numba (opcional, com fallback)

### 7.2 Infraestrutura
- Time-series DB (dados históricos)
- Redis (cache, opcional)
- Kafka (stream, opcional)

### 7.3 Dados
- OHLCV por ativo (CSV ou feed MT5)
- Dados macro opcionais (FRED, DXY, VIX)

---

## 8. CUSTO- beneficio

| Aspecto | Avaliação |
|---------|-----------|
| **Investimento** | 4 semanas (estimativa) + auditoria AIC |
| **Retorno potencial** | Sinal estrutural multi-classe, calibração independente, redução de falsos positivos |
| **Risco de não fazer** | Continuar com MOTIVATION_MT5 dominante (99.85% atual); AGENT_IA subutilizado (0.15%) |
| **Recomendação** | APROVAR fase L4/L5; adiar L6 até validação |

---

## 9. CHECKLIST CONSELHO

- [ ] Aprovar Fase 1 (estabilização código, 1 semana)
- [ ] Aprovar Fase 2 (validação offline CSV, 1-2 semanas)
- [ ] Autorizar auditoria AIC (Fase 3)
- [ ] Autorizar integração shadow_loop (Fase 4, condicional a aprovação AIC)
- [ ] Alocar recursos para teste CSV real (≥500 barras por classe)
- [ ] Definir hit-rate mínimo aceitável para aprovação (recomendação: ≥55% forward 10 barras)

---

## ANEXOS

### Anexo A — Ficheiros Analisados

| Componente | Ficheiro | Linhas | Localização |
|-----------|----------|--------|-------------|
| TRE | `TRE — Temporal Resonance Engine Doc.txt` | ~953 | `componentes em desenvolvimento/TRE/` |
| TRE | `IMPLEMENTAÇÃO COMPLETA EM PYTHON.txt` | — | `componentes em desenvolvimento/TRE/` |
| TRE | `TRE vNEXT — NÚCLEO FINAL DE ALTO DESEMPENHO.txt` | — | `componentes em desenvolvimento/TRE/` |
| TRE | `VERSÃO HIGH PERFORMANCE.txt` | — | `componentes em desenvolvimento/TRE/` |
| TEPA | `Temporal Energy Propagation Architecture (TEPA).txt` | ~953 | `componentes em desenvolvimento/TEPA/` |
| USFE-A | `AIC/omega_usfe_engine.py` | 792 | `OMEGA_USFE_Unified_Structural_Field_Engine/AIC/` |
| USFE-B | `Proposta/OMEGA USFE v1.0.0.txt` | 1022 | `OMEGA_USFE_Unified_Structural_Field_Engine/Proposta Codigo USFE/` |
| MIC-E | `Proposta/Production-Grade Component.txt` | 651 | `OMEGA_USFE_Unified_Structural_Field_Engine/Proposta Codigo USFE/` |
| Docs | `USFE_ESPECIFICACAO_TECNICA_v1.md` | 291 | `OMEGA_USFE_Unified_Structural_Field_Engine/AIC/` |
| Docs | `USFE_AUDITORIA_FINAL_CONSELHO_20260530.md` | 348 | `OMEGA_USFE_Unified_Structural_Field_Engine/AIC/` |

### Anexo B — Comparação Rápida

| Critério | TRE | TEPA | USFE |
|----------|-----|------|------|
| Motores | 9 | 10 camadas | Fusão 9+10 |
| Outputs | TRS, HPI, SPS, DI, ODI, MSP, REI, ECI, DEI, API | E, P, RIPL, CIM, exaustão | structural_signal, trade_bias, confidence |
| Multi-classe | Sim | Sim | ✅ Calibração JSON |
| Código Python | ✅ | ✅ | ✅ (792-1022 linhas) |
| Self-test | Documentado | Documentado | ✅ PASS |
| Produção | NÃO | NÃO | NÃO (falta L4-L6) |

---

*Documento compilado por PSA a partir da análise dos 3 componentes. Mandato CEO: apresentação ao conselho.*
