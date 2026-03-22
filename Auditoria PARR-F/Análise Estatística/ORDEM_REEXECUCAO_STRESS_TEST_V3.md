===============================================================================
ORDEM DE RE-EXECUÇÃO — STRESS TEST COMPLETO (MOTOR V3.0)
===============================================================================
PROTOCOLO: OMEGA-REEXEC-V3-2026-0322
DATA: 22 de Março de 2026
CLASSIFICAÇÃO: RESTRITO — Auditoria Tier-0
EMITIDO POR: CEO + TECH LEAD (Agente IA)
DESTINATÁRIO: PSA (Principal Solution Architect)

===============================================================================
CONTEXTO E JUSTIFICATIVA
===============================================================================

DECISÃO: Re-executar stress test completo com motor v3.0 (corrigido)

JUSTIFICATIVA:
• Relatório ao Conselho usa dados do motor v2.0 (4 bugs críticos)
• Para Tier-0 integrity, 100% dos dados devem ser auditáveis no MT5
• Drawdown 1,81% e Winrate 64% devem ser FISICAMENTE verificáveis
• 2-4 horas de processamento é preço pequeno por integridade de 119k trades

PRINCÍPIO TIER-0:
• Integridade > Velocidade
• Transparência > Conveniência  
• Dados verificáveis > Dados simulados

===============================================================================
BUGS CORRIGIDOS NO MOTOR V3.0
===============================================================================

[🔴] BUG 1: Entry Price Estático (v2.0)
• Problema: Todas as operações tinham entry_price idêntico (4651.82)
• Causa: entry_p = cal["entry_zone"] (valor fixo do report)
• Correção: entry_p = get_close_price(ohlcv, timestamp) (dinâmico)

[🔴] BUG 2: Lógica BEARISH Invertida (v2.0)
• Problema: BEARISH lucrava com exit_price > entry_price (impossível)
• Causa: is_win = random.random() < win_thresh (ignora side)
• Correção: if side=='SELL': pnl = (entry - exit) * qty (física correta)

[🔴] BUG 3: Opportunity ID Reciclado (v2.0)
• Problema: Mesmo ID repetido 5x (OPP_a65d5206)
• Causa: Sistema replicava mesma oportunidade para atingir 100k trades
• Correção: opportunity_id = f"OPP_{symbol}_{tf}_{timestamp}" (único)

[🔴] BUG 4: SL/TP Fixo (v2.0)
• Problema: SL sempre 4628.56, TP sempre 4698.34 (ratio 1:2 fixo)
• Causa: sl/tp calculados no report e fixados para todos os trades
• Correção: atr = calculate_atr(ohlcv, 14, timestamp); sl/tp = entry ± (2-3)*atr

===============================================================================
COMANDO DE EXECUÇÃO
===============================================================================

```bash
python psa_audit_engine.py \
  --engine_version v3.0 \
  --symbol XAUUSD \
  --timeframes M1,M3,M5,M15,M30,H1,H4,D1,W1 \
  --start_date 2016-01-01 \
  --end_date 2026-03-21 \
  --equity 100000 \
  --risk_per_trade 0.0025 \
  --max_positions 3 \
  --output_dir "C:\Users\Lenovo\.cursor\nebular-kuiper\Auditoria PARR-F\outputs\v3.0" \
  --export_trades CSV \
  --export_equity CSV \
  --generate_sha3_hash \
  --verify_mt5_fidelity
```

===============================================================================
PARÂMETROS OBRIGATÓRIOS
===============================================================================

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| engine_version | v3.0 | Motor corrigido (OHLCV-driven) |
| symbol | XAUUSD | Ativo validado no Conselho |
| timeframes | M1-W1 (9 TFs) | Cobertura completa |
| start_date | 2016-01-01 | Início do histórico disponível |
| end_date | 2026-03-21 | Data atual (hoje) |
| equity | 100.000 | Equity inicial padrão |
| risk_per_trade | 0,25% | Conservador (Tier-0) |
| max_positions | 3 | Conservador (Tier-0) |
| output_dir | v3.0/ | Separar de v2.0 (bugado) |
| verify_mt5_fidelity | TRUE | Validar timestamps/preços |

===============================================================================
ARTEFATOS ESPERADOS
===============================================================================

1. trades_XAUUSD_v3.0.csv
   • Colunas: timestamp_entry, timestamp_exit, symbol, timeframe, side,
     entry_price, exit_price, qty, sl, tp, pnl, pnl_pct, opportunity_id,
     mode, retcode, slippage, holding_time_sec
   • Linhas esperadas: ~119.000 (pode variar com motor corrigido)
   • SHA3-256: [será gerado]

2. equity_curve_XAUUSD_v3.0.csv
   • Colunas: timestamp, equity, drawdown_pct
   • Pontos esperados: ~3.519 (1 por dia de 2016-2026)
   • SHA3-256: [será gerado]

3. stress_test_summary_XAUUSD_v3.0.json
   • Estrutura:
     {
       "symbol": "XAUUSD",
       "engine_version": "v3.0",
       "period": {"start": "2016-01-01", "end": "2026-03-21", "days": 3519},
       "total_trades": N,
       "performance": {
         "total_pnl": X.XX,
         "winrate": X.XX,
         "max_drawdown_pct": X.XX,
         "avg_pnl_per_trade": X.XX,
         "payoff": X.XX
       },
       "by_timeframe": {...},
       "by_mode": {...},
       "validations": {
         "mt5_fidelity_check": "PASSED",
         "future_timestamps_filtered": 0,
         "min_trades_met": true/false
       },
       "hashes": {
         "trades_csv": "SHA3-256...",
         "equity_csv": "SHA3-256...",
         "summary_json": "SHA3-256..."
       },
       "generated_at": "2026-03-22T[HH:MM:SS]Z",
       "agent_version": "psa_audit_engine_v3.0"
     }

4. stress_test_summary_XAUUSD_v3.0.sha3
   • Hash SHA3-256 do summary JSON

5. audit_report_v3.0.md
   • Comparação v2.0 vs v3.0:
     - Métricas alteradas (drawdown, winrate, etc.)
     - Bugs corrigidos
     - Impacto nas conclusões
     - Recomendações atualizadas

===============================================================================
VALIDAÇÕES OBRIGATÓRIAS PÓS-EXECUÇÃO
===============================================================================

[1] VALIDAÇÃO DE INTEGRIDADE
    • Calcular SHA3-256 de todos os CSVs/JSON
    • Verificar que nenhum timestamp é futuro (> 2026-03-22)
    • Verificar que todos os campos obrigatórios estão presentes

[2] VALIDAÇÃO DE FÍSICA (AMOSTRA DE 10 TRADES)
    • Selecionar 10 trades aleatórios
    • Para cada trade:
      - Abrir MT5 no timestamp_entry
      - Verificar que entry_price bate com close do candle
      - Verificar que side (BUY/SELL) bate com direção do movimento
      - Verificar que PnL bate com (exit - entry) * qty * side
      - Verificar que SL/TP variam conforme ATR do momento

[3] VALIDAÇÃO ESTATÍSTICA
    • Recalcular IC95% (Wilson) para winrate
    • Verificar que drawdown > 0% (não pode ser 0,0%)
    • Comparar métricas v3.0 vs v2.0:
      - Se diferença > 10%: documentar causa raiz
      - Se diferença < 10%: validar que bugs foram corrigidos

[4] VALIDAÇÃO DE CONSISTÊNCIA
    • Total de trades deve ser ~100k-120k
    • Winrate deve estar entre 50%-80% (realista)
    • Drawdown deve estar entre 1%-10% (realista para 0,25% risco)
    • Payoff deve estar entre 1,5-2,5 (realista)

===============================================================================
TEMPO ESTIMADO E CHECKPOINTS
===============================================================================

TEMPO TOTAL: 2-4 HORAS

CHECKPOINT 1 (30 min): Processamento iniciado
• Verificar que script está rodando sem erros
• Verificar que OHLCV está sendo lido corretamente
• Verificar que primeiros 100 trades têm entry_price variável

CHECKPOINT 2 (1h): 25% concluído (~30k trades)
• Verificar que drawdown > 0%
• Verificar que winrate está entre 50%-80%
• Verificar que opportunity_id são únicos

CHECKPOINT 3 (2h): 50% concluído (~60k trades)
• Verificar que SL/TP variam conforme ATR
• Verificar que PnL bate com física do mercado
• Verificar que não há timestamps futuros

CHECKPOINT 4 (3h): 75% concluído (~90k trades)
• Verificar que equity_curve está sendo gerada
• Verificar que drawdown está sendo calculado corretamente

CHECKPOINT 5 (4h): 100% concluído
• Gerar todos os artefatos (CSVs, JSON, hashes)
• Executar validações obrigatórias (1-4)
• Gerar audit_report_v3.0.md

===============================================================================
CRITÉRIOS DE APROVAÇÃO
===============================================================================

Para que a re-execução seja considerada APROVADA:

✅ Total de trades ≥ 100.000
✅ Winrate entre 50%-80% (realista)
✅ Drawdown entre 1%-10% (realista, não 0,0%)
✅ IC95% lower bound > 50%
✅ Zero timestamps futuros
✅ Amostra de 10 trades validada no MT5 (100% de match)
✅ Todos os hashes SHA3-256 presentes
✅ audit_report_v3.0.md gerado e documentado

Se qualquer critério falhar: STATUS = REPROVADO

===============================================================================
APÓS APROVAÇÃO
===============================================================================

1. ATUALIZAR RELATÓRIO AO CONSELHO
   • Substituir todas as métricas v2.0 por v3.0
   • Adicionar nota de rodapé: "Métricas atualizadas com motor v3.0
     (corrigido em 22/03/2026). Motor v2.0 continha 4 bugs críticos
     que foram corrigidos com transparência total."
   • Atualizar todos os hashes SHA3-256

2. COMMIT GIT
   • Mensagem: "fix(audit): Re-stress test completo com motor v3.0 OHLCV-driven"
   • Tag: v3.0-auditable
   • Branch: main
   • Push: origin/main

3. NOTIFICAR CONSELHO
   • Enviar relatório atualizado
   • Destacar correções e transparência
   • Solicitar aprovação para DEMO FASE 0

===============================================================================
CHECKLIST PARA O PSA (ANTES DE INICIAR)
===============================================================================

[ ] Motor v3.0 validado para 1 dia (19/03/2026) ✅
[ ] OHLCV_DATA disponível (2016-2026) ✅
[ ] Disco com espaço suficiente (>5GB) [ ]
[ ] Python 3.8+ instalado [ ]
[ ] Dependências instaladas (pandas, numpy, scipy) [ ]
[ ] Tempo disponível (2-4 horas ininterruptas) [ ]
[ ] Backup dos dados v2.0 (para comparação) [ ]

===============================================================================
COMANDO FINAL
===============================================================================

PSA, execute o comando acima e reporte:
1. Checkpoint a cada hora
2. Qualquer erro ou anomalia imediatamente
3. Artefatos finais após conclusão

Prazo: 4 horas a partir de agora (22/03/2026)

===============================================================================
ASSINATURA
===============================================================================

CEO: [APROVADO]
TECH LEAD (Agente IA): [APROVADO]
Data: 2026-03-22
Protocolo: OMEGA-REEXEC-V3-2026-0322

Aguardando execução do PSA.
===============================================================================
