//+------------------------------------------------------------------+
//|                                              MultiAssetTrader.mq5 |
//|                                  Copyright 2024, Seu Nome Aqui    |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024"
#property link      ""
#property version   "1.00"
#property strict

// Inclusão de arquivos necessários
#include <Trade/Trade.mqh>
#include <Trade/SymbolInfo.mqh>
#include <Trade/PositionInfo.mqh>

// Handles dos indicadores
int ma_fast_handle;
int ma_slow_handle;
int rsi_handle;

// Parâmetros de entrada
input group "Configurações Gerais"
input string   Symbols = "EURUSD,GBPUSD,USDJPY";  // Símbolos para trading
input double   LotSize = 0.1;                     // Tamanho do lote
input int      StopLoss = 100;                    // Stop Loss em pontos
input int      TakeProfit = 200;                  // Take Profit em pontos

input group "Configurações dos Indicadores"
input int      MA_Fast_Period = 20;               // Período da MA Rápida
input int      MA_Slow_Period = 50;               // Período da MA Lenta
input int      RSI_Period = 14;                   // Período do RSI
input int      RSI_UpperLevel = 70;               // Nível Superior do RSI
input int      RSI_LowerLevel = 30;               // Nível Inferior do RSI

// Variáveis globais
CTrade trade;
string symbol_array[];
int total_symbols;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Inicializa o objeto de trading
    trade.SetExpertMagicNumber(123456);
    
    // Divide a string de símbolos em um array
    StringSplit(Symbols, ',', symbol_array);
    total_symbols = ArraySize(symbol_array);
    
    // Inicializa os indicadores para cada símbolo
    for(int i = 0; i < total_symbols; i++)
    {
        ma_fast_handle = iMA(symbol_array[i], PERIOD_CURRENT, MA_Fast_Period, 0, MODE_SMA, PRICE_CLOSE);
        ma_slow_handle = iMA(symbol_array[i], PERIOD_CURRENT, MA_Slow_Period, 0, MODE_SMA, PRICE_CLOSE);
        rsi_handle = iRSI(symbol_array[i], PERIOD_CURRENT, RSI_Period, PRICE_CLOSE);
        
        if(ma_fast_handle == INVALID_HANDLE || ma_slow_handle == INVALID_HANDLE || rsi_handle == INVALID_HANDLE)
        {
            Print("Erro ao inicializar indicadores para ", symbol_array[i]);
            return INIT_FAILED;
        }
    }
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Libera os handles dos indicadores
    IndicatorRelease(ma_fast_handle);
    IndicatorRelease(ma_slow_handle);
    IndicatorRelease(rsi_handle);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Verifica sinais para cada símbolo
    for(int i = 0; i < total_symbols; i++)
    {
        CheckForSignals(symbol_array[i]);
    }
}

//+------------------------------------------------------------------+
//| Verifica sinais de trading                                       |
//+------------------------------------------------------------------+
void CheckForSignals(string symbol)
{
    double ma_fast[], ma_slow[], rsi[];
    ArraySetAsSeries(ma_fast, true);
    ArraySetAsSeries(ma_slow, true);
    ArraySetAsSeries(rsi, true);
    
    // Copia dados dos indicadores
    if(CopyBuffer(ma_fast_handle, 0, 0, 2, ma_fast) <= 0) return;
    if(CopyBuffer(ma_slow_handle, 0, 0, 2, ma_slow) <= 0) return;
    if(CopyBuffer(rsi_handle, 0, 0, 2, rsi) <= 0) return;
    
    // Verifica condições de compra
    if(ma_fast[0] > ma_slow[0] && ma_fast[1] <= ma_slow[1] && rsi[0] < RSI_LowerLevel)
    {
        OpenPosition(symbol, ORDER_TYPE_BUY);
    }
    
    // Verifica condições de venda
    if(ma_fast[0] < ma_slow[0] && ma_fast[1] >= ma_slow[1] && rsi[0] > RSI_UpperLevel)
    {
        OpenPosition(symbol, ORDER_TYPE_SELL);
    }
}

//+------------------------------------------------------------------+
//| Abre uma nova posição                                            |
//+------------------------------------------------------------------+
void OpenPosition(string symbol, ENUM_ORDER_TYPE order_type)
{
    double price = (order_type == ORDER_TYPE_BUY) ? 
                   SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                   SymbolInfoDouble(symbol, SYMBOL_BID);
                   
    double sl = (order_type == ORDER_TYPE_BUY) ? 
                price - StopLoss * _Point : 
                price + StopLoss * _Point;
                
    double tp = (order_type == ORDER_TYPE_BUY) ? 
                price + TakeProfit * _Point : 
                price - TakeProfit * _Point;
    
    trade.PositionOpen(symbol, order_type, LotSize, price, sl, tp);
} 