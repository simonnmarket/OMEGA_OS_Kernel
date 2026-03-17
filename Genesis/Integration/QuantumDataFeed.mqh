//+------------------------------------------------------------------+
//| quantum_data_feed.mqh - Feed de Dados Quântico-Institucional     |
//| Projeto: Genesis                                                |
//| Pasta: Include/Integration/                                     |
//| Versão: v8.1 (GodMode Final + IA Ready)                         |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_DATA_FEED_MQH__
#define __QUANTUM_DATA_FEED_MQH__

#include <Controls/Label.mqh>
#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Quantum/QuantumEntanglementSimulator.mqh>
#include <Genesis/Quantum/QuantumDataProcessor.mqh>

enum ENUM_QUANTUM_FEED_SOURCE {
   QFEED_BLOOMBERG_QUANTUM,
   QFEED_REUTERS_ENTANGLED,
   QFEED_DARK_POOL_STREAM,
   QFEED_HFT_SUPERPOSITION,
   QFEED_SIMULATED
};

struct QuantumMarketData {
   double price[2];
   double volume;
   double spread;
   double entanglement;
   datetime timestamp;
   double volatility;
   double market_entropy;
};

struct QuantumFeedResult {
   datetime timestamp;
   string symbol;
   ENUM_QUANTUM_FEED_SOURCE source_used;
   bool quantum_connected;
   double latency_ns;
   int data_points_received;
   double signal_to_noise_ratio;
   double market_entropy;
   string status_message;
};

class QuantumDataFeed {
private:
   logger_institutional          &m_logger;
   QuantumEntanglementSimulator &m_quantum_link;
   QuantumDataProcessor         &m_data_processor;
   string                       m_symbol;
   ENUM_QUANTUM_FEED_SOURCE     m_feed_source;
   bool                         m_quantum_connected;
   double                       m_quantum_latency;
   datetime                     m_last_update;
   QuantumFeedResult m_connection_history[];
   CLabel *m_feed_label = NULL;

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { m_logger.log_error("[QFEED] Sem conexão com o servidor de mercado"); return false; }
      if(!SymbolInfoInteger(m_symbol, SYMBOL_SELECT)) { m_logger.log_error("[QFEED] Símbolo inválido: " + m_symbol); return false; }
      if(!m_quantum_link.IsQuantumReady()) { m_logger.log_warning("[QFEED] Simulador de entrelaçamento não está pronto"); return false; }
      if(!m_data_processor.IsInitialized()) { m_logger.log_warning("[QFEED] Processador de dados não inicializado"); return false; }
      return true;
   }

   bool EstablishQuantumConnection() {
      if(!is_valid_context()) return false;
      m_quantum_latency = MathMax(1.0, MathMin(10.0, MathRand() % 100 / 10.0));
      m_quantum_connected = m_quantum_link.ConnectToFeed(m_symbol, m_feed_source, m_quantum_latency);
      if(m_quantum_connected) { m_logger.log_info(StringFormat("[QFEED] Conexão quântica estabelecida com %s | Latência: %.2f ns", EnumToString(m_feed_source), m_quantum_latency)); }
      else { m_logger.log_warning("[QFEED] Falha na conexão quântica. Usando modo clássico."); }
      return m_quantum_connected;
   }

   double CalculateMarketEntropy()
   {
      MqlRates rates[]; CopyRates(m_symbol, PERIOD_M1, 0, 20, rates);
      double entropy = 0.0, sum = 0.0; for(int i = 0; i < ArraySize(rates); i++) sum += rates[i].close;
      if(sum <= 0) return 0.0; for(int i = 0; i < ArraySize(rates); i++) { double p = rates[i].close / sum; if(p > 0) entropy -= p * MathLog(p); }
      return NormalizeDouble(entropy, 4);
   }

   void updateFeedDisplay(bool connected, double entanglement)
   {
      if(m_feed_label == NULL) m_feed_label = new CLabel("FeedLabel", 0, 10, 310);
      m_feed_label->text(StringFormat("FEED: %s | Ent:%.2f", connected ? "ON" : "OFF", entanglement));
      m_feed_label->color(!connected ? clrRed : entanglement > 0.8 ? clrMagenta : entanglement > 0.5 ? clrOrange : clrLime);
   }

public:
   QuantumDataFeed(logger_institutional &logger, QuantumEntanglementSimulator &quantum_link, QuantumDataProcessor &data_processor, string symbol, ENUM_QUANTUM_FEED_SOURCE source = QFEED_BLOOMBERG_QUANTUM, double max_latency = 5.0)
      : m_logger(logger), m_quantum_link(quantum_link), m_data_processor(data_processor), m_symbol(symbol), m_feed_source(source), m_quantum_latency(max_latency), m_quantum_connected(false), m_last_update(0)
   {
      if(!m_logger.is_initialized()) { Print("[QFEED] Logger não inicializado"); ExpertRemove(); }
      if(!m_quantum_link.IsQuantumReady() || !m_data_processor.IsInitialized()) { m_logger.log_error("[QFEED] Subsistema quântico não inicializado"); ExpertRemove(); }
      EstablishQuantumConnection();
      m_logger.log_info(StringFormat("[QFEED] Feed quântico inicializado para %s | Fonte: %s | Quântico: %s", m_symbol, EnumToString(m_feed_source), m_quantum_connected ? "Ativo" : "Inativo"));
   }

   bool GetQuantumMarketData(QuantumMarketData &data) {
      if(!is_valid_context()) { m_logger.log_warning("[QFEED] Contexto inválido. Retornando falso."); return false; }
      if(!m_quantum_connected && !EstablishQuantumConnection()) { m_logger.log_warning("[QFEED] Usando dados clássicos - conexão quântica indisponível"); return false; }
      if(!m_quantum_link.GetSuperposedPrices(m_symbol, data.price[0], data.price[1])) { m_logger.log_error("[QFEED] Falha ao obter preços quânticos"); return false; }
      if(DoubleIsNaN(data.price[0]) || DoubleIsNaN(data.price[1])) { m_logger.log_error("[QFEED] Preço quântico inválido. Usando valor clássico."); data.price[0] = SymbolInfoDouble(m_symbol, SYMBOL_BID); data.price[1] = SymbolInfoDouble(m_symbol, SYMBOL_ASK); }
      data.volume = m_quantum_link.GetEntangledVolume(m_symbol); if(DoubleIsNaN(data.volume) || data.volume <= 0) data.volume = Volume[0];
      data.spread = MathAbs(data.price[1] - data.price[0]);
      data.entanglement = m_data_processor.CalculateEntanglement(data.price[0], data.price[1], data.volume);
      data.timestamp = TimeCurrent(); data.volatility = iATR(m_symbol, PERIOD_H1, 14, 0); data.market_entropy = CalculateMarketEntropy();
      QuantumFeedResult result; result.timestamp = TimeCurrent(); result.symbol = m_symbol; result.source_used = m_feed_source; result.quantum_connected = m_quantum_connected; result.latency_ns = m_quantum_latency; result.data_points_received = 4; result.signal_to_noise_ratio = 1.0 / (data.market_entropy + 0.1); result.market_entropy = data.market_entropy; result.status_message = "OK"; ArrayPushBack(m_connection_history, result);
      m_logger.log_info(StringFormat("[QFEED] Dados quânticos: Bid=%.5f | Ask=%.5f | Spread=%.1f | Volume=%.0f | Ent=%.2f | Volatilidade=%.5f", data.price[0], data.price[1], data.spread, data.volume, data.entanglement, data.volatility));
      updateFeedDisplay(m_quantum_connected, data.entanglement);
      return true;
   }

   bool GetQuantumOrderFlow(double &bid_flow[], double &ask_flow[], int depth=10) {
      if(!is_valid_context()) { m_logger.log_warning("[QFEED] Contexto inválido. Inicializando arrays vazios."); ArrayResize(bid_flow, depth); ArrayResize(ask_flow, depth); ArrayInitialize(bid_flow, 0.0); ArrayInitialize(ask_flow, 0.0); return false; }
      if(depth <= 0) depth = 10; ArrayResize(bid_flow, depth); ArrayResize(ask_flow, depth);
      if(!m_quantum_link.GetQuantumOrderFlow(m_symbol, bid_flow, ask_flow, depth)) { m_logger.log_error("[QFEED] Falha ao obter fluxo quântico"); return false; }
      for(int i=0; i<depth; i++) { bid_flow[i] = m_data_processor.ApplyQuantumCorrelation(bid_flow[i]); ask_flow[i] = m_data_processor.ApplyQuantumCorrelation(ask_flow[i]); if(DoubleIsNaN(bid_flow[i])) bid_flow[i] = 0.0; if(DoubleIsNaN(ask_flow[i])) ask_flow[i] = 0.0; }
      m_logger.log_info(StringFormat("[QFEED] Fluxo quântico obtido | Profundidade: %d", depth));
      return true;
   }

   bool IsConnected() const { return m_quantum_connected && TerminalInfoInteger(TERMINAL_CONNECTED); }
   double GetQuantumVolatility(int period = 14) { double atr = iATR(m_symbol, PERIOD_H1, period, 0); double avg_price = (SymbolInfoDouble(m_symbol, SYMBOL_ASK) + SymbolInfoDouble(m_symbol, SYMBOL_BID)) / 2.0; return atr / avg_price; }
};

#endif // __QUANTUM_DATA_FEED_MQH__


