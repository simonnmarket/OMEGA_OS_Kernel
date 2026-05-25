DOCUMENTO TÉCNICO — MÓDULO M3
DOCUMENTO TÉCNICO OFICIAL — MÓDULO M3
Calibrador de Parâmetros por Sessão de Mercado (core/omega_session_calibrator.py)

Emitente: Arquiteto OMEGA (CRO/CTO)
Destinatário: CEO / Conselho Executivo
Data: 26 de Abril de 2026
Classificação: CONFIDENCIAL — DOCUMENTAÇÃO TÉCNICA
Versão: 1.0.0
Hash do Módulo: sha256:m3-session-calibrator-v1-0-0-20260426
1. VISÃO GERAL

O M3 — Calibrador de Sessão ajusta automaticamente todos os parâmetros de trading baseado na sessão de mercado atual. Ele implementa a descoberta da Dark Web de que thresholds de detecção de assinaturas devem ser calibrados por sessão: em baixa liquidez (Ásia), spoofing e icebergs são mais visíveis (thresholds mais baixos); em alta liquidez (NY), é necessário ser mais restritivo para evitar falsos positivos.
2. TABELA DE CALIBRAÇÃO POR SESSÃO
Parâmetro	Ásia	Londres	NY	Overlap	Fechado
Lote Máx	0.005	0.01	0.01	0.01	0.005
Confiança Mín	0.75	0.65	0.65	0.70	0.85
Spoof Threshold	0.60	0.75	0.85	0.70	0.50
Iceberg Threshold	0.50	0.65	0.75	0.60	0.40
Momentum Threshold	0.55	0.70	0.80	0.65	0.50
SL (ATR ×)	2.5	2.0	2.0	2.0	3.0
TP (ATR ×)	1.5	3.0	2.5	2.5	1.5
Slippage Máx	0.8	0.5	0.3	0.6	1.0
Latência Máx	300ms	200ms	100ms	250ms	500ms
3. ATIVOS PRIORITÁRIOS POR SESSÃO
Sessão	Ativos	Justificativa
Ásia	XAUUSD, AUDUSD, NZDUSD, USDJPY	Metais e pares asiáticos têm mais liquidez
Londres	EURUSD, GBPUSD, XAUUSD, GER40	Forex europeu e índices
NY	XAUUSD, EURUSD, GBPUSD, US500, NAS100	Máxima liquidez, todos os ativos
Overlap	US500, NAS100, BTCUSD, ETHUSD, XAUUSD	Índices US after-hours e cripto
4. ESTRATÉGIAS ATIVAS POR SESSÃO
Sessão	Estratégias	Justificativa
Ásia	Scalping, Mean Reversion, Arbitrage	Baixa volatilidade, ranges
Londres	Trend Following, Breakout, Momentum, Adaptive	Tendências fortes na abertura
NY	Momentum, Market Making, Trend Following, Breakout, Adaptive	Máxima liquidez, HFT
Overlap	Adaptive, Arbitrage, Mean Reversion, Market Making	Transição, mercados de baixa liquidez
5. LÓGICA DE DETECÇÃO DE ASSINATURAS POR SESSÃO

A descoberta da Dark Web é clara: spoofing é mais detectável em baixa liquidez. Em mercados cheios (NY), um spoofer se camufla na multidão. Em mercados vazios (Ásia), qualquer ordem grande é uma anomalia.
Sessão	Liquidez	Detectabilidade	Threshold
Ásia	BAIXA	ALTA (sinal-ruído alto)	0.50-0.60
Londres	ALTA	MÉDIA	0.65-0.75
NY	MÁXIMA	BAIXA (muito ruído)	0.75-0.85
Overlap	MÉDIA	MÉDIA-ALTA	0.60-0.70
6. HASH E ASSINATURA
Atributo	Valor
Nome do Módulo	M3 — Calibrador de Sessão
Arquivo	core/omega_session_calibrator.py
Versão	1.0.0
Hash SHA-256	sha256:m3-session-calibrator-v1-0-0-20260426
Data de Criação	2026-04-26
Autor	Arquiteto OMEGA (CRO/CTO)
Pasta de Destino	C:\Users\Lenovo\Agent IA Omega\core\