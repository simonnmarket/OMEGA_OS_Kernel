//+------------------------------------------------------------------+
//| safe_mode_manager.mqh - Gerenciador de Modo Seguro              |
//| Projeto: Genesis                                                |
//| Versão: v1.2 (GodMode Final + Blindagem Institucional)          |
//+------------------------------------------------------------------+
#ifndef __SAFE_MODE_MANAGER_MQH__
#define __SAFE_MODE_MANAGER_MQH__

#include <Controls/Label.mqh>
#include <Trade/Trade.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Analysis/MarketRegimeDetector.mqh>

// Macros institucionais de segurança
// Macro local evitando colisão
#ifndef SAFE_EXEC_SAFE
#define SAFE_EXEC_SAFE(x) if(!(x)) { \
   if(m_logger != NULL) m_logger->log_error("[SAFE] Falha em " + #x); \
   return false; \
}
#endif

#define VALIDATE_POINTER(ptr) if(ptr == NULL) { \
   if(m_logger != NULL) m_logger->log_error("[SAFE] Ponteiro NULL: " + #ptr); \
   return false; \
}

#define VALIDATE_ARRAY(arr) if(ArraySize(arr) <= 0) { \
   if(m_logger != NULL) m_logger->log_error("[SAFE] Array vazio: " + #arr); \
   return false; \
}

class SafeModeManager
{
private:
   logger_institutional  *m_logger;
   MarketRegimeDetector  *m_regime;
   bool m_safe_mode_enabled;
   datetime m_last_error_time;
   int m_error_count;
   int m_max_errors;
   datetime m_safe_mode_activation_time;
   bool m_initialized;
   struct ErrorLog { datetime timestamp; int error_code; string description; bool critical; };
   ErrorLog m_error_history[];
   CLabel *m_safe_label;

   // Configurações (substituem inputs globais em headers)
   bool m_simulate;
   int m_reintegration_wait_time;
   bool m_enable_emergency_shutdown;
   int m_max_spread;

public:
   SafeModeManager(logger_institutional &logger, MarketRegimeDetector &regime)
      : m_logger(&logger), m_regime(&regime), m_initialized(false)
   {
      VALIDATE_POINTER(m_logger);
      VALIDATE_POINTER(m_regime);
      m_safe_mode_enabled = false;
      m_last_error_time = TimeCurrent();
      m_error_count = 0;
      m_max_errors = 3;
      m_reintegration_wait_time = 60;
      m_enable_emergency_shutdown = true;
      m_max_spread = 25;
      m_simulate = false;
      m_safe_mode_activation_time = 0;
      m_safe_label = NULL;
      log_operation("Construtor", true, "Safe mode manager criado com sucesso");
   }

   void initialize()
   {
      if(m_initialized) { if(m_logger != NULL) m_logger->log_warning("[SAFE] Já inicializado"); return; }
      VALIDATE_POINTER(m_logger);
      VALIDATE_POINTER(m_regime);
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { log_operation("Inicialização", false, "Terminal offline"); if(m_logger != NULL) m_logger->log_critical("[SAFE] Terminal offline"); return; }
      if(m_logger != NULL) m_logger->log_info("[SAFE] Iniciando gerenciador de modo seguro...");
      m_safe_label = new CLabel("SafeModeLabel", 0, 10, 90);
      if(m_safe_label != NULL) { m_safe_label->Text("Modo: Operação Normal"); m_safe_label->Color(clrLime); /* fonte opcional */ }
      m_initialized = true;
      log_operation("Inicialização", true, "Gerenciador de modo seguro inicializado");
      if(m_logger != NULL) m_logger->log_info("[SAFE] Inicialização concluída com sucesso");
   }

   void on_trade_error(int error_code)
   {
      if(!m_initialized) { if(m_logger != NULL) m_logger->log_error("[SAFE] Tentativa de on_trade_error sem inicialização"); return; }
      VALIDATE_POINTER(m_logger);
      VALIDATE_POINTER(m_regime);
      if(m_simulate) { if(m_logger != NULL) m_logger->log_debug("[SAFE] Modo simulado. Erro registrado, mas modo seguro não ativado."); return; }
      if(error_code <= 0) { if(m_logger != NULL) m_logger->log_warning("[SAFE] Código de erro inválido: " + IntegerToString(error_code)); return; }
      if(m_logger != NULL) m_logger->log_error("[SAFE] Erro de trade detectado: " + IntegerToString(error_code));
      m_error_count++; m_last_error_time = TimeCurrent();
      log_error(error_code, get_error_description(error_code), is_critical_error(error_code));
      if(m_error_count >= m_max_errors) { activate_safe_mode(); }
   }

   void activate_safe_mode()
   {
      if(m_safe_mode_enabled) { if(m_logger != NULL) m_logger->log_warning("[SAFE] Modo seguro já está ativo"); return; }
      VALIDATE_POINTER(m_logger);
      if(m_logger != NULL) m_logger->log_critical("[SAFE] Modo seguro ativado após " + IntegerToString(m_max_errors) + " erros.");
      m_safe_mode_enabled = true; m_safe_mode_activation_time = TimeCurrent();
      log_safe_mode_activation(); update_chart_display();
      if(m_enable_emergency_shutdown) { safe_mode_fallback(); }
   }

   void safe_mode_fallback()
   {
      VALIDATE_POINTER(m_logger);
      if(m_logger != NULL) m_logger->log_critical("[SAFE] Iniciando fallback seguro...");
      m_error_count = 0; m_safe_mode_enabled = false; m_safe_mode_activation_time = 0; update_chart_display();
      if(m_logger != NULL) m_logger->log_info("[SAFE] Sistema reinicializado com segurança.");
      log_operation("Fallback", true, "Sistema reinicializado com segurança");
   }

   void reset_errors() { VALIDATE_POINTER(m_logger); m_error_count = 0; m_last_error_time = TimeCurrent(); if(m_logger != NULL) m_logger->log_info("[SAFE] Contador de erros reiniciado."); log_operation("Reset", true, "Contador de erros reiniciado"); }
   bool is_safe_mode_active() const { return m_safe_mode_enabled; }
   int get_error_count() const { return m_error_count; }
   datetime get_last_error_time() const { return m_last_error_time; }
   bool is_initialized() const { return m_initialized; }

   void evaluate_conditions()
   {
      if(!m_initialized) { if(m_logger != NULL) m_logger->log_error("[SAFE] Tentativa de evaluate_conditions sem inicialização"); return; }
      VALIDATE_POINTER(m_logger); VALIDATE_POINTER(m_regime);
      if(!is_market_safe()) { if(m_logger != NULL) m_logger->log_warning("[SAFE] Condições de mercado não seguras"); return; }
      if(m_safe_mode_enabled && m_safe_mode_activation_time > 0) {
         datetime current_time = TimeCurrent();
         if(current_time - m_safe_mode_activation_time >= m_reintegration_wait_time) { if(m_logger != NULL) m_logger->log_info("[SAFE] Tempo de reativação atingido. Desativando modo seguro."); m_safe_mode_enabled = false; m_safe_mode_activation_time = 0; update_chart_display(); }
      }
   }

   void update_chart_display()
   {
      if(m_safe_label == NULL) { m_safe_label = new CLabel("SafeModeLabel", 0, 10, 90); }
      if(m_safe_label != NULL) { m_safe_label->Text(m_safe_mode_enabled ? "MODO SEGURO ATIVADO" : "Modo: Operação Normal"); m_safe_label->Color(m_safe_mode_enabled ? clrRed : clrLime); }
   }

private:
   void log_error(int error_code, string description, bool critical)
   {
      if(m_logger == NULL) return;
      int size = ArraySize(m_error_history); ArrayResize(m_error_history, size + 1);
      m_error_history[size].timestamp = TimeCurrent();
      m_error_history[size].error_code = error_code;
      m_error_history[size].description = description;
      m_error_history[size].critical = critical;
      if(critical) { m_logger->log_error(StringFormat("[SAFE] Erro crítico: %d - %s", error_code, description)); }
      else { m_logger->log_warning(StringFormat("[SAFE] Erro: %d - %s", error_code, description)); }
   }

   void log_safe_mode_activation()
   {
      if(m_logger == NULL) return;
      string entry = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + " | Modo seguro ativado";
      m_logger->log_info("[SAFE] Modo seguro registrado no histórico: " + entry);
      log_operation("Ativação", true, "Modo seguro ativado após " + IntegerToString(m_max_errors) + " erros");
   }
   
   void log_operation(string operation, bool success, string details)
   {
      if(m_logger == NULL) return;
      if(success) m_logger->log_info(StringFormat("[SAFE] %s: %s", operation, details));
      else m_logger->log_error(StringFormat("[SAFE] %s: %s", operation, details));
   }

   bool is_market_safe()
   {
      if(m_regime == NULL) return false;
      int spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
      int hour = TimeHour(TimeCurrent());
      bool spread_ok = spread <= m_max_spread;
      bool time_ok = (hour >= 3 && hour <= 22);
      bool regime_ok = m_regime->get_max_spread() >= spread;
      return spread_ok && time_ok && regime_ok;
   }

   string get_error_description(int error_code)
   {
      switch(error_code) {
         case 10004: return "Requisição de negociação rejeitada";
         case 10006: return "Requisição cancelada pelo trader";
         case 10007: return "Requisição cancelada pelo sistema de negociação";
         case 10010: return "Requisição cancelada por timeout";
         case 10011: return "Requisição cancelada por erro interno";
         case 10012: return "Requisição cancelada por erro de preço";
         case 10013: return "Requisição cancelada por erro de volume";
         case 10014: return "Requisição cancelada por erro de mercado";
         case 10015: return "Requisição cancelada por erro de sistema";
         default: return "Erro desconhecido";
      }
   }
   
   bool is_critical_error(int error_code)
   {
      int critical_errors[] = {10011, 10012, 10013, 10014, 10015};
      for(int i = 0; i < ArraySize(critical_errors); i++) { if(error_code == critical_errors[i]) return true; }
      return false;
   }
};

#endif // __SAFE_MODE_MANAGER_MQH__


