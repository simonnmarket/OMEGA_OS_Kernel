# Pendências Unificadas — DOS_MODULE v1.1.0

Status atual: pronto para pesquisa/backtesting. Para produção institucional, resolver os itens abaixo.

## Críticas (bloqueiam produção)
- Precisão financeira: substituir `float` por `Decimal` em preços/SL/TP (trading/dos_trading_v1).
- Backtest: manter sem look-ahead (já removido), mas acrescentar custos variáveis/slippage configurável e validar saída SL/TP bar-a-bar; remover qualquer viés remanescente.
- Segurança Postgres: reforçar autenticação/autorização a nível de chamada; evitar expansão futura de SQL por concatenação (adotar query builder/ORM ou padrões de parametrização auditados).
- PnL sintético (FIN-SENSE): rotular explicitamente como hipotético até existir livro/posições reais; impedir uso como PnL realizado em relatórios executivos.

## Altas
- Logging e observabilidade: migrar para logs estruturados (JSON) com trace/correlation-id; métricas de performance e de erros; opcionalmente tracing (OTel).
- Vetorização total de sinais: já sem iterrows na montagem, mas ainda cria objetos um a um; considerar saída vetorizada ou dataclass em lote para grandes volumes.
- Validar schema MT5 rigidamente (tipos/dtypes, outliers) e rejeitar CSVs malformados.
- Retry/backoff configurável no Postgres com telemetria de falha.

## Médias
- Digest/escala: digest incremental já feito; para datasets enormes, avaliar streaming completo e clustering/rolling em modo chunk/amostragem.
- Bins de volatilidade (regimes): hoje fixos (0/0.005/0.015); calibrar por ativo/regime ou torná-los configuráveis.
- Backtrader opcional: sem chunking para séries longas; ajustar se usar históricos muito grandes.
- Segurança de entrada MT5: enforcement de dtypes e saneamento de valores extremos (NaN/inf/outliers).

## Baixas
- Logs não mascaram credenciais por padrão; garantir masking se forem habilitados para Postgres.
- Mensagens de documentação divergentes entre arquivos de auditoria (alguns “Production Ready”, outros “aprovado condicional”); unificar o wording.
- Warning sklearn em clustering quando dados são constantes (1 cluster): lidar com fallback ou aviso controlado.

## Checklist sugerido para hardening
1) Decimal em preços/SL/TP; custos/slippage configuráveis; logs JSON.  
2) Validação rígida de schema MT5 + bins de vol configuráveis; vetorização de saída de sinais.  
3) Digest/streaming para volumes grandes; observabilidade (métricas + tracing); retry/backoff parametrizado.  
4) Revisão de segurança Postgres + masking; unificar documentação e avisos de PnL sintético.  
5) (Opcional) Backtrader: chunking ou amostragem para históricos massivos.

## Pré-go-live (produção)
- Executar suite de testes + testes de carga (FIN-SENSE e trading) no ambiente alvo.
- Validar que PnL sintético não é apresentado como resultado realizado.
- Verificar SLOs acordados (latência, memória) nos datasets reais.
