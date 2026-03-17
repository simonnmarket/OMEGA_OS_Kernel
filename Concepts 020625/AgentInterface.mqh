//+------------------------------------------------------------------+
//| AgentInterface.mqh                                               |
//| Interface simples para comunicação de agentes externos           |
//+------------------------------------------------------------------+
#ifndef __AGENT_INTERFACE_MQH__
#define __AGENT_INTERFACE_MQH__

// Função de envio de mensagens de agente (placeholder para IA ou outros)
void iaAGENT_SendMessage(string tipo, string conteudo)
{
    PrintFormat(">> AGENTE >> [%s] %s", tipo, conteudo);
    // Ponto para expandir: JSON, arquivos, buffers, pipes, etc.
}

#endif // __AGENT_INTERFACE_MQH__
