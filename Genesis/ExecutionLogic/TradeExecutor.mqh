//+------------------------------------------------------------------+
//| TradeExecutor.mqh - Executor de Ordens                           |
//| Projeto: Genesis                                                |
//| Módulo: ExecutionLogic                                          |
//| Versão: v1.2 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __TRADE_EXECUTOR_MQH__
#define __TRADE_EXECUTOR_MQH__

#include <Controls/Label.mqh>
#include <Trade/Trade.mqh>
#include <Genesis/Core/TradeSignalEnum.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Risk/RiskProfile.mqh>
#include <Genesis/Analysis/MarketRegimeDetector.mqh>

// Compatibilidade
#define trade_signal ENUM_TRADE_SIGNAL
#define signal_to_string(sig) TradeSignalUtils::ToString(sig)

input bool Simulate = true;
input double RISK_PERCENT = 1.0;
input int SL_POINTS = 200;
input int TP_POINTS = 400;

class TradeExecutor
{
private:
   CTrade               m_trade;
   logger_institutional &m_logger;
   RiskProfile          &m_risk;
   MarketRegimeDetector &m_regime;
   string m_symbol;
   string m_execution_history[];
   CLabel *m_executor_label = NULL;

public:
   TradeExecutor(logger_institutional &logger, 
                 RiskProfile &risk, 
                 MarketRegimeDetector &regime, 
                 string symbol)
      : m_logger(logger), m_risk(risk), m_regime(regime)
   {
      m_symbol = symbol;
      m_logger.log_info("[EXECUTOR] Iniciando TradeExecutor com segurança TIER-0.");
      if(!is_executor_ready())
         ExpertRemove();
   }

   bool is_executor_ready()
   {
      if(!m_logger.is_initialized()) { Print("Erro: Logger não inicializado"); return false; }
      if(!m_risk.is_profile_ready()) { m_logger.log_error("RiskProfile não inicializado"); return false; }
      if(!m_regime.is_detector_ready()) { m_logger.log_error("MarketRegimeDetector não inicializado"); return false; }
      if(!SymbolInfoDouble(m_symbol, SYMBOL_BID)) { m_logger.log_error("Símbolo inválido: " + m_symbol); return false; }
      return true;
   }

   bool execute(trade_signal signal)
   {
      if(!is_safe_to_trade()) { m_logger.log_warning("[EXECUTOR] Ambiente não seguro ou sem conexão"); return false; }
      if(!is_signal_valid(signal)) { m_logger.log_error("[EXECUTOR] Sinal inválido: " + signal_to_string(signal)); return false; }
      double lot = calculate_lot_size(); double sl = 0.0, tp = 0.0; normalize_sl_tp(sl, tp);
      string context = "Execução de ordem | Símbolo: " + m_symbol; log_signal_emission(signal, context);
      update_executor_display(signal);
      switch(signal)
      {
         case SIGNAL_BUY:
         case SIGNAL_SCALP_BUY:
         case SIGNAL_REVERSE_BUY:
            return send_buy_order(lot, sl, tp);
         case SIGNAL_SELL:
         case SIGNAL_SCALP_SELL:
         case SIGNAL_REVERSE_SELL:
            return send_sell_order(lot, sl, tp);
         case SIGNAL_CLOSE:
            return close_all_positions();
         default:
            m_logger.log_info("[EXECUTOR] Nenhuma ação necessária: " + signal_to_string(signal));
            return true;
      }
   }

private:
   double calculate_lot_size()
   {
      double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double tick_value = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE);
      double risk_amount = account_balance * (RISK_PERCENT / 100.0);
      double lot = NormalizeDouble(risk_amount / (SL_POINTS * tick_value), 2);
      if(lot < 0.01) { m_logger.log_error("[EXECUTOR] Lote inválido: " + DoubleToString(lot)); return 0.01; }
      if(m_regime.is_chaotic()) { m_logger.log_warning("[EXECUTOR] Mercado caótico. Ajustando lote."); lot *= m_regime.get_volatility_factor(); }
      return MathMin(lot, m_risk.get_max_lot());
   }

   void normalize_sl_tp(double &sl, double &tp)
   {
      double price = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double point = SymbolInfoDouble(m_symbol, SYMBOL_POINT);
      sl = price - (SL_POINTS * point);
      tp = price + (TP_POINTS * point);
      if(!is_context_valid(sl, tp)) { m_logger.log_error("[EXECUTOR] Valores de SL/TP inválidos."); sl = 0.0; tp = 0.0; }
   }

   bool is_context_valid(double sl, double tp) { return sl > 0 && tp > 0; }

   bool is_market_connected() { if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { m_logger.log_error("Sem conexão com o servidor de mercado"); return false; } return true; }

   bool is_safe_to_trade()
   {
      if(Simulate) { m_logger.log_debug("[EXECUTOR] Modo simulado. Execução bloqueada."); return false; }
      if(!is_market_connected()) return false;
      if(!is_time_to_trade()) { m_logger.log_warning("[EXECUTOR] Fora do horário de operação institucional"); return false; }
      return true;
   }

   bool is_time_to_trade() { int hour = TimeHour(TimeCurrent()); return hour >= 3 && hour <= 22; }
   bool is_signal_valid(trade_signal signal) { return signal != SIGNAL_NONE; }

   void log_signal_emission(trade_signal signal, string context)
   {
      string signal_str = signal_to_string(signal);
      string entry = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + " | " + context + " | Sinal: " + signal_str;
      ArrayPushBack(m_execution_history, entry); m_logger.log_info(entry);
   }

   bool send_buy_order(double lot, double sl, double tp)
   {
      if(!is_market_connected()) return false;
      m_logger.log_info(StringFormat("[EXECUTOR] Enviando ordem de COMPRA | Lote: %.2f | SL: %.5f | TP: %.5f", lot, sl, tp));
      bool result = m_trade.Buy(lot, m_symbol, 0, sl, tp, "Compra Algorítmica");
      log_execution_result(result, "[EXECUTOR:COMPRA]");
      return result;
   }

   bool send_sell_order(double lot, double sl, double tp)
   {
      if(!is_market_connected()) return false;
      m_logger.log_info(StringFormat("[EXECUTOR] Enviando ordem de VENDA | Lote: %.2f | SL: %.5f | TP: %.5f", lot, sl, tp));
      bool result = m_trade.Sell(lot, m_symbol, 0, sl, tp, "Venda Algorítmica");
      log_execution_result(result, "[EXECUTOR:VENDA]");
      return result;
   }

   bool close_all_positions()
   {
      if(PositionsTotal() == 0) { m_logger.log_info("[EXECUTOR] Nenhuma posição aberta para fechar"); return true; }
      m_logger.log_info("[EXECUTOR] Encerrando todas as posições...");
      bool result = m_trade.PositionClose(m_symbol);
      log_execution_result(result, "[EXECUTOR:FECHAMENTO]");
      return result;
   }

   void log_execution_result(bool result, string context)
   {
      string status = result ? "SUCESSO" : "FALHA";
      string entry = context + " | Resultado: " + status;
      m_logger.log_info(entry);
   }

   void update_executor_display(trade_signal signal)
   {
      if(m_executor_label == NULL) m_executor_label = new CLabel("ExecutorLabel", 0, 10, 130);
      m_executor_label->text("SINAL: " + signal_to_string(signal));
      m_executor_label->color(
         signal == SIGNAL_QUANTUM_FLASH ? clrMagenta :
         signal == SIGNAL_DARKPOOL_CRITICAL ? clrRed :
         signal == SIGNAL_BUY ? clrLime :
         signal == SIGNAL_SELL ? clrRed : clrWhite
      );
   }
};

#endif // __TRADE_EXECUTOR_MQH__


