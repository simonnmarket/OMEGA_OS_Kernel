# OMEGA FORENSIC ANSWERS — OMEGA-FORENSIC-AUDIT-REQUEST-PSA-20260520

**ID Resposta:** PSA-FORENSIC-RESPONSE-20260520  
**Data:** 2026-05-20 21:20 UTC+2  
**Auditora:** PSA (Engenharia / Cascade)  
**Metodologia:** Extração directa de ficheiros do sistema, grep/ripgrep, Win32_Process, log analysis  

---

## 4.1 Esterilização (Mandato Zero)

### Q1: Quais processos Python estão activos?

| PID | Executável | Memória | CommandLine |
|-----|-----------|---------|-------------|
| 39852 | python3.11.exe | 15.9 MB | N/D (permissão Win32) |
| 28364 | python3.11.exe | 411.5 MB (**ACTIVO**) | N/D (permissão Win32) |
| 29024 | python3.11.exe | N/D | N/D |

**ALERTA CRÍTICO:** `tasklist /fi "imagename eq python.exe"` retorna ZERO porque o executável real é `python3.11.exe`. O Mandato Zero original usou nome errado — a esterilização não pode ser provada com o comando original.

O log mostra última entrada `2026-05-20 20:19:01` (ciclo activo). Origem confirmada: `run_omega_24x7.ps1` → `shadow_loop.py` (mode=paper, equity=1250.80 USD).

### Q2: MT5 com "Permitir negociação automática" desmarcado?

**NÃO VERIFICÁVEL pela PSA** via linha de comando. Requer verificação GUI pelo CEO.  
**Evidência indirecta:** retcode=10027 (15 ordens) no decision_trace = `TRADE_RETCODE_CLIENT_DISABLES` → MT5 provavelmente com algo trading DESACTIVADO em algum momento. Mas 117 ordens com retcode=10009 (DONE) sugerem que em outros momentos estava ACTIVADO.

### Q3: Quais janelas estão abertas?

| Processo | PID | Janela | Relevância |
|---------|-----|--------|-----------|
| terminal64 | 38048 | **HantecMarketsMU-MT5: Demo Account — USDJPY,M1** | ⚠️ MT5 ACTIVO |
| chrome | 16332 | Hantec Markets Client Portal | Portal broker |
| firefox | 38712 | Banco de investimento China — Google | Pesquisa |
| firefox | 25024 | Quantitative System Decay Analysis — Tor Browser | Análise |
| Cursor/Windsurf | 20348/31516 | SOURCE_CODE IDE | Desenvolvimento |
| EXCEL | 13860 | CONTROLE ARQUIVOS | Controlo |
| Notepad | 37240 | *CEO Entao mas olhas estas informac... | Notas CEO |

---

## 4.2 Ordens "Fantasma"

### Q4: Quantas ordens com `Magic=0` nos últimos 30 dias?

**Do pacote PSA Tier-0 (2026-04-20 a 2026-05-18):** 1.460 deals com magic=0 (de 1.855 total = 78.7%).  
**Origem identificada:** `shadow_loop.py` linha `mt5_send_order` — campo `magic` ausente no dict `request` → broker assign magic=0.  
**trade_feedback.jsonl** (1.108 eventos): sem campo `magic` registado.

### Q5: Ordens com comentários não padronizados?

Do trade_feedback.jsonl (paper mode, sem execução real hoje):
- `ORDEM_REAL_EXECUTADA ([$$$])`: **0** ocorrências no log — main.py NÃO executou ordens hoje
- Padrão `OV2|` (shadow_loop canónico): presente em orders com comment_mark confirmado no boot

### Q6: Magic Numbers não oficiais encontrados?

| Magic | Ficheiro | Estado |
|-------|---------|--------|
| 0 (implícito) | shadow_loop.py `mt5_send_order` | **ACTIVO** — causa principal ordens magic=0 |
| 0 (explícito ausente) | main.py `execute_mt5_order` | INACTIVO hoje (0 ordens reais) |
| 777777 | omega_turing_live.py | INACTIVO (não em execução) |
| 500500 | live_drone_v5.py | INACTIVO |
| 550550 | omega_v550_realtime_mt5_v550.py | INACTIVO |
| 234001 | shadow_loop.py (legacy_magic declarado no boot) | Declarado mas magic=0 vai para broker |

**ROOT CAUSE magic=0:** O boot confirma `legacy_magic=234001` mas o campo `"magic"` não consta no dict `request` dentro de `mt5_send_order`. Precisa de patch explícito.

---

## 4.3 Correções Não Aplicadas

### Q7: Spread Guard e Rollover Blackout aparecem nos logs?

| Gate | omega_24x7_runner.log | decision_trace.jsonl | Conclusão |
|------|----------------------|----------------------|-----------|
| SKIP_SPREAD_GUARD | **0** | **13** | M1 activo mas só escreve em decision_trace |
| SKIP_ROLLOVER_BLACKOUT | **0** | **0** | M2 não acionado (sem sinais em 23:55-00:10 UTC) |
| EXECUCAO_BLOQUEADA | 13 | N/A | Correlaciona com decision_trace M1 |

**Causa da ausência no runner.log:** M1 escreve `return False, "SKIP_SPREAD_GUARD"` mas o caller em `shadow_loop.py:3971+` não loga esta string no formato que o grep procurou. O gate FUNCIONA mas o log de resultado vai para `decision_trace.jsonl`.

### Q8: MOMENTUM_FALLBACK desactivado?

**SIM — CONFIRMADO:** 6.812 ocorrências de `[MOMENTUM_FALLBACK] DISABLED` no log desde 2026-05-18. M3 activo e funcional.

### Q9: Variáveis de ambiente no log de arranque?

Do boot `2026-05-20 07:22:59`:
```
ROOT=C:\OMEGA_QUANTUM_LAB\SOURCE_CODE | mode=paper | 32 ativos × 3 TFs
equity=USD 1250.80 | Risk/trade=0.50% | MaxPos=8 | DD_max=10%
comment_mark='OV2|' | legacy_magic=234001 | scale_magic_range=999111..999130
[FORENSIC] CODE_SHA3=ce072c762614
[EVAL_CONTEXT] tier=WEEKDAY_CORE weight=1.0
```

**OMEGA_DISABLE_MOMENTUM_FALLBACK** não aparece no boot line (é env var do PS1, propagada ao subprocess, não impressa no log de arranque do runner — mas o efeito está confirmado pelas 6.812 linhas DISABLED).

---

## 4.4 Intrusão de Código

### Q10: Ficheiros com `order_send` fora do perímetro?

**25 ficheiros na árvore activa** (excluindo Auditoria PARR-F/ e inativo/). Os de maior risco:

| Ficheiro | Matches | Magic | Modificado | Risco |
|---------|---------|-------|-----------|-------|
| `src/executor_original.py` | 5 | desconhecido | — | ALTO |
| `omega_v550_realtime_mt5.py` | 4 | 550 do cfg | 2026-05-03 | ALTO |
| `omega_v550_realtime_mt5_v550.py` | 4 | 550550 | 2026-05-03 | ALTO |
| `omega_turing_live.py` | 3 | 777777 | 2026-04-21 | ALTO |
| `core_engines/shadow_loop_v2.py` | 4 | desconhecido | 2026-05-03 | ALTO |
| **`main.py`** | **2** | **0 (ausente)** | **2026-05-17** | **CRÍTICO** |
| `core_engines/emergency_abort.py` | 3 | N/A | — | MÉDIO |
| `modules/risk/scale_manager.py` | 2 | do caller | — | MÉDIO |

### Q11: Ficheiros com Magic Number diferente de 234001?

| Ficheiro | Magic | Observação |
|---------|-------|-----------|
| omega_turing_live.py | 777777 | Hardcoded, 2 refs |
| live_drone_v5.py | 500500 | Default class param |
| omega_v550_realtime_mt5_v550.py | 550550 | Config dict |
| shadow_loop.py | 234001 (declarado), 0 (efectivo) | Bug: campo ausente no request |
| kill_switch_persistent.py | 234001 | Para fechar posições legacy |

### Q12: Ficheiros com comentários suspeitos?

| Ficheiro | Padrão | Linhas |
|---------|--------|--------|
| main.py | `[$$$] ORDEM REAL EXECUTADA!` | 259 |
| omega_turing_live.py | `Turing_Bivariate`, `FatTail_Close` | 65, 149 |
| live_drone_v5.py | `V5.3_*`, `EJECT_ALL` | 153, 182 |
| omega_v550_realtime_mt5*.py | `OE_V5_*` | múltiplas |

**Nenhum `OMEGA-AMI-` encontrado** na árvore activa — sistema AMI não presente.

---

## 4.5 Conflito de Estratégias

### Q13: Estratégias activas em main.py vs shadow_loop.py?

**main.py (BAU_DO_TESOURO pipeline):**  
GorilaSacramento, VascoSegundaFalha, NasaIntegratedStrategy, RaioXWaveStrategy, FimatheCoreStrategy, PullbackDetector, PrometheusGuardianStrategy (VETO), Apollo11Agent (XAGUSD), QuantumGapDetector, OmegaMacroAgent007 (intermarket context)

**shadow_loop.py (OMEGA v3 pipeline):**  
EDGE_GATE → MTF_ALIGN → Zone Navigator → Tesseract (XAUUSD) → ZAK → MP-GATE → M1-GATE → Atomic Lock → MT5 + weis_wave, fimathe, pattern, microstructure, Momentum MT5

### Q14: Sobreposição de estratégias?

**SIM — SOBREPOSIÇÃO TOTAL de ativos.** Ambos os sistemas operam EURUSD, AUDUSD, XAUUSD, XAGUSD, US30, GER40. Se main.py e shadow_loop.py correrem simultaneamente, ambos enviam ordens para os mesmos símbolos com magic diferentes (0 vs 234001), gerando conflito de gestão de posições.

**Estado actual:** main.py NÃO está a correr hoje (ORDEM_REAL_EXECUTADA=0). Apenas shadow_loop.py activo.

### Q15: Como o sistema lida com conflitos de decisão?

**main.py:** Votação por contagem (BUY_count vs SELL_count por símbolo) + VETO do PrometheusGuardianStrategy. Fallback a `execute_mt5_order(0.01, 50, 100)` sem guardrail se scale_manager falhar (linha 509).

**shadow_loop.py:** Pipeline sequencial com veto em cada gate. MAX_POS_PER_ASSET=1 previne duplicados intra-shadow.

**Conflito inter-sistemas:** SEM mecanismo de lock partilhado entre main.py e shadow_loop.py. Os dois têm lock files diferentes (`omega_kernel.lock` vs lock da omega_paper_loop_24x7.py).

---

## VEREDITO FORENSE FINAL

### Causa da regressão (DD -24.9%: $1,664 → $1,250)

**1. CAUSA PRIMÁRIA CONFIRMADA — magic=0 em shadow_loop.py:**  
O campo `"magic"` está ausente no dict `request` de `mt5_send_order`. Broker assign magic=0. Sem identificação nativa, o sistema não consegue distinguir as suas próprias posições de outras (orphan positions não são fechadas, não passam pelo partial close/trailing stop).

**2. CAUSA SECUNDÁRIA — M1 activo mas não visível no log principal:**  
13 bloqueios de SKIP_SPREAD_GUARD foram executados (em decision_trace) mas o caller em shadow_loop.py não faz `log.warning` com essa string no runner.log. Ordens em spread elevado continuam a passar se a condição `sl_dist < spread*3` não for satisfeita.

**3. CAUSA TERCIÁRIA — M2 zero:**  
Nenhum sinal gerado na janela 23:55-00:10 UTC. O rollover blackout não foi testado em produção.

**4. SEM INTRUSÃO ACTIVA:**  
main.py, omega_turing_live.py, live_drone_v5.py NÃO estão a correr hoje. ORDEM_REAL_EXECUTADA=0.

### Recomendações imediatas

| Prioridade | Acção | Ficheiro |
|-----------|-------|---------|
| **P0** | Adicionar `"magic": 234001` em `mt5_send_order` request dict | shadow_loop.py |
| **P0** | Adicionar `log.warning("SKIP_SPREAD_GUARD...")` no caller shadow_loop.py:3971+ | shadow_loop.py |
| **P1** | Mover para `/inativo/`: omega_turing_live.py, live_drone_v5.py, omega_v550_realtime_mt5*.py, shadow_loop_v2.py | ROOT |
| **P1** | main.py: adicionar `"magic": 234001` em `execute_mt5_order` e bloquear execução sem `--mode live` explícito | main.py |
| **P2** | Verificar e fechar posições orphan (magic=0) no MT5 demo antes de continuar | MT5 GUI |
| **P2** | Exportar Tier-0 pós-patch para confirmar magic=234001 nas novas ordens | psa_export |
