//+------------------------------------------------------------------+
//| crisis_protocol.mqh - Protocolo de Crise Institucional           |
//| Projeto: Genesis                                                |
//| Pasta: Include/Security/                                        |
//| Versão: v1.1                                                    |
//+------------------------------------------------------------------+
#ifndef __GENESIS_CRISIS_PROTOCOL_MQH__
#define __GENESIS_CRISIS_PROTOCOL_MQH__

#include <Controls/Label.mqh>

class CGenesisCrisisProtocol
{
private:
   string   m_symbol;
   datetime m_crisis_start;
   enum ENUM_CRISIS_LEVEL { CRISIS_LEVEL_NONE, CRISIS_LEVEL_WARNING, CRISIS_LEVEL_ALERT, CRISIS_LEVEL_EMERGENCY };
   ENUM_CRISIS_LEVEL m_crisis_level;
   string m_crisis_label_name; string m_crisis_details_name;

   bool is_valid_context()
   { if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { Print("[CRISIS] Sem conexão com o servidor"); return false; } return true; }

   void updateCrisisDisplay(ENUM_CRISIS_LEVEL level, string details)
   {
      if(m_crisis_label_name == "")
      { m_crisis_label_name = "CrisisLabel_" + IntegerToString(ChartID()); ObjectCreate(0, m_crisis_label_name, OBJ_LABEL, 0, 0, 0); ObjectSetString(0, m_crisis_label_name, OBJPROP_TEXT, "CRISE: NENHUMA"); ObjectSetInteger(0, m_crisis_label_name, OBJPROP_COLOR, clrGray); ObjectSetInteger(0, m_crisis_label_name, OBJPROP_XDISTANCE, 10); ObjectSetInteger(0, m_crisis_label_name, OBJPROP_YDISTANCE, 1800); }
      if(m_crisis_details_name == "")
      { m_crisis_details_name = "CrisisDetails_" + IntegerToString(ChartID()); ObjectCreate(0, m_crisis_details_name, OBJ_LABEL, 0, 0, 0); ObjectSetString(0, m_crisis_details_name, OBJPROP_TEXT, "DETALHES: ?"); ObjectSetInteger(0, m_crisis_details_name, OBJPROP_COLOR, clrGray); ObjectSetInteger(0, m_crisis_details_name, OBJPROP_XDISTANCE, 10); ObjectSetInteger(0, m_crisis_details_name, OBJPROP_YDISTANCE, 1820); }
      string level_str = (level==CRISIS_LEVEL_NONE?"NENHUMA":level==CRISIS_LEVEL_WARNING?"ALERTA":level==CRISIS_LEVEL_ALERT?"ALERTA":"EMERGÊNCIA");
      ObjectSetString(0, m_crisis_label_name, OBJPROP_TEXT, "CRISE: " + level_str);
      ObjectSetInteger(0, m_crisis_label_name, OBJPROP_COLOR, level == CRISIS_LEVEL_NONE ? clrLime : level == CRISIS_LEVEL_WARNING ? clrYellow : level == CRISIS_LEVEL_ALERT ? clrRed : clrRed);
      ObjectSetString(0, m_crisis_details_name, OBJPROP_TEXT, "DETALHES: " + details);
      ObjectSetInteger(0, m_crisis_details_name, OBJPROP_COLOR, level > CRISIS_LEVEL_NONE ? clrRed : clrGray);
   }

public:
   CGenesisCrisisProtocol(){ m_symbol = _Symbol; m_crisis_level = CRISIS_LEVEL_NONE; m_crisis_start = 0; m_crisis_label_name = ""; m_crisis_details_name = ""; Print("[CRISIS] Protocolo de Crise Genesis inicializado para " + m_symbol); }
   bool ActivateCrisisProtocol(ENUM_CRISIS_LEVEL level, string reason)
   { if(!is_valid_context()) return false; m_crisis_level = level; m_crisis_start = TimeCurrent(); Print("[CRISIS] Protocolo de crise ativado: " + IntegerToString(level) + " | Motivo: " + reason); updateCrisisDisplay(level, reason); return true; }
   bool DeactivateCrisisProtocol()
   { if(m_crisis_level == CRISIS_LEVEL_NONE) return true; Print("[CRISIS] Protocolo de crise desativado"); m_crisis_level = CRISIS_LEVEL_NONE; m_crisis_start = 0; updateCrisisDisplay(CRISIS_LEVEL_NONE, "Normal"); return true; }
   ENUM_CRISIS_LEVEL GetCrisisLevel() const { return m_crisis_level; }
   bool IsInCrisis() const { return m_crisis_level > CRISIS_LEVEL_WARNING; }
   bool ValidateCrisisIntegrity() { if(!is_valid_context()) { Print("[CRISIS] Falha na validação de contexto"); return false; } if(m_symbol == "") { Print("[CRISIS] Símbolo não definido"); return false; } Print("[CRISIS] Integridade validada com sucesso"); return true; }
};

#endif // __GENESIS_CRISIS_PROTOCOL_MQH__


