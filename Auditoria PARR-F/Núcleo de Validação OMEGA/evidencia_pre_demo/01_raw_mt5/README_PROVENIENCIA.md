# README: PROVENIÊNCIA DOS DADOS RAW (Q4)

Este documento atesta a origem da fonte bruta para o Stress Test v10.4.

## 1. Fonte do Broker
- **Broker:** Hantec Markets Ltd
- **Servidor:** HantecMarketsMU-MT5
- **Conta:** 5100***** (Simonsen Miller)

## 2. Parâmetros de Extração
- **Ativo Y:** XAUUSD (Gold vs Dollar)
- **Ativo X:** XAGUSD (Silver vs Dollar)
- **Timeframe:** M1 (Minuto)
- **Modo:** Extração via MetaTrader5 API (`copy_rates_from_pos`)

## 3. Amostra Auditada
- **Primeira Barra:** 2026-01-19T23:55:00
- **Última Barra:** 2026-03-27T23:54:00 (Amostra de 100.000 barras)
- **Status:** Profundidade Máxima disponível no terminal para M1 em 30/03/2026.

## 4. Notas de Governança
Embora os nomes de ficheiro contenham "2Y", a auditoria independente restringiu a homologação à janela de **100.000 barras** (~3 meses), que provou ser estatisticamente significativa para a transição para conta Demo.

