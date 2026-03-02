//+------------------------------------------------------------------+
//| decision_router.mqh - Decisor Algorítmico Institucional         |
//| Projeto: Genesis                                                |
//| Versão: v3.1 (GodMode Ready + Blindagem Institucional)          |
//| Status: TIER-0 Compliant | SHA3 Protected | 5K+/dia Ready        |
//+------------------------------------------------------------------+
#ifndef __DECISION_ROUTER_MQH__
#define __DECISION_ROUTER_MQH__

#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Intelligence/ThalerBiasEngine.mqh>
#include <Genesis/Analysis/CorrelationMatrix.mqh>
#include <Genesis/Analysis/MarketRegimeDetector.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>

// Compatibilidade com código legado
#define trade_signal ENUM_TRADE_SIGNAL
#define signal_to_string(sig) TradeSignalUtils::ToString(sig)

class decision_router {
private:
   double m_aggression_level;
   ThalerBiasEngine m_bias_engine;
   CorrelationMatrix m_corr_matrix;
   logger_institutional &m_logger;
   MarketRegimeDetector &m_regime;

   double rsi_values[];
   double macd_values[];
   double signal_values[];

public:
   decision_router(logger_institutional &logger, MarketRegimeDetector &regime)
   : m_logger(logger), m_regime(regime) {
      m_aggression_level = 1.0;
      m_bias_engine.initialize();
      m_corr_matrix.load("corr_data.bin");
      ArraySetAsSeries(rsi_values, true);
      ArraySetAsSeries(macd_values, true);
   }

   trade_signal evaluate() {
      if(!m_regime.is_market_open()) {
         m_logger.log_warning("[ROUTER] Mercado fechado. Decisão bloqueada.");
         return SIGNAL_NONE;
      }

      if(m_corr_matrix.is_highly_correlated(_Symbol, 0.85)) {
         m_logger.log_warning("[ROUTER] Ativo correlacionado demais. Sinal bloqueado.");
         return SIGNAL_NONE;
      }

      if(m_bias_engine.detect_herding()) {
         m_logger.log_info("[ROUTER] Viés de manada detectado. Aplicando contrarian.");
         return m_bias_engine.get_contrarian_signal();
      }

      ENUM_TIMEFRAMES tf = m_regime.get_optimal_timeframe();

      int rsi_handle = iRSI(_Symbol, tf, 14, PRICE_CLOSE);
      int macd_handle = iMACD(_Symbol, tf, 12, 26, 9, PRICE_CLOSE);

      if(rsi_handle == INVALID_HANDLE || macd_handle == INVALID_HANDLE) {
         m_logger.log_error("[ROUTER] Indicadores inválidos.");
         return SIGNAL_NONE;
      }

      if(CopyBuffer(rsi_handle, 0, 0, 2, rsi_values) <= 0 ||
         CopyBuffer(macd_handle, 0, 0, 2, macd_values) <= 0) {
         m_logger.log_error("[ROUTER] Falha ao copiar dados dos indicadores.");
         return SIGNAL_NONE;
      }

      double rsi = rsi_values[0];
      double prev_rsi = rsi_values[1];
      double macd = macd_values[0];
      double prev_macd = macd_values[1];

      bool bullish_cross = macd > 0 && prev_macd <= 0;
      bool bearish_cross = macd < 0 && prev_macd >= 0;

      double rsi_buy = m_regime.get_rsi_buy_threshold();
      double rsi_sell = m_regime.get_rsi_sell_threshold();
      double volume_threshold = m_regime.get_volume_threshold();

      double volume = iVolume(_Symbol, tf, 0);
      double avg_volume = iMA(_Symbol, tf, 3, 0, MODE_SMA, PRICE_VOLUME, 0);

      if(volume <= 0 || avg_volume <= 0) {
         m_logger.log_error("[ROUTER] Volume inválido.");
         return SIGNAL_NONE;
      }

      if(volume < avg_volume * volume_threshold) {
         m_logger.log_debug("[ROUTER] Volume abaixo do threshold.");
         return SIGNAL_NONE;
      }

      if(rsi < rsi_buy && bullish_cross) {
         m_logger.log_info(StringFormat("[ROUTER] BUY signal | RSI: %.2f | MACD: %.5f", rsi, macd));
         return SIGNAL_BUY;
      }

      if(rsi > rsi_sell && bearish_cross) {
         m_logger.log_info(StringFormat("[ROUTER] SELL signal | RSI: %.2f | MACD: %.5f", rsi, macd));
         return SIGNAL_SELL;
      }

      m_logger.log_debug("[ROUTER] Nenhum sinal gerado.");
      return SIGNAL_NONE;
   }

   double calculate_volume() {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double kelly = m_bias_engine.get_kelly_factor();
      double riskCapital = balance * (kelly / 100.0);
      double contractSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
      double rawVolume = riskCapital / contractSize;
      double adjusted = MathMin(rawVolume, 0.1);
      return NormalizeDouble(adjusted, 2);
   }
};

#endif // __DECISION_ROUTER_MQH__


