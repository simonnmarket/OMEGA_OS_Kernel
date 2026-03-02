//+------------------------------------------------------------------+
//| quantum_firewall.mqh - Firewall Quântico (stub mínimo)           |
//+------------------------------------------------------------------+
#ifndef __QUANTUM_FIREWALL_MQH__
#define __QUANTUM_FIREWALL_MQH__

class logger_institutional;
class QuantumBlockchain;

class QuantumFirewall
{
public:
   QuantumFirewall(logger_institutional * /*logger*/, QuantumBlockchain * /*blockchain*/) {}
   bool IsReady() const { return true; }
   bool IsActive() const { return true; }
   void LogTransaction(string data, string event) { /* no-op stub */ }
};

#endif // __QUANTUM_FIREWALL_MQH__


