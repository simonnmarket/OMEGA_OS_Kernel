//+------------------------------------------------------------------+
//|                                        VolumeSurgeAgent.mqh       |
//|                  Copyright 2024, MetaQuotes Ltd.                  |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "2.6"
#property strict

#include "..\\Core\\CAgentBase.mqh"
#include "..\\Quantum\\CQuantumMarketPhysics.mqh"

//+------------------------------------------------------------------+
//| Classe para agente de surto de volume                             |
//+------------------------------------------------------------------+
class CVolumeSurgeAgent : public CAgentBase
{
private:
   int m_period;
   double m_surge_threshold;
   double m_volume_ma;
   double m_volume_std;
   datetime m_last_update_time;
   double m_confidence;
   CQuantumMarketPhysics* m_quantum_state;
   double m_volume_state;
   double m_quantum_coherence;
   
public:
   // Construtor
   CVolumeSurgeAgent(string symbol, ENUM_TIMEFRAMES timeframe, CLogger* logger)
      : CAgentBase(symbol, timeframe, logger)
   {
      m_period = 20;
      m_surge_threshold = 2.0;
      m_volume_ma = 0.0;
      m_volume_std = 0.0;
      m_last_update_time = 0;
      m_confidence = 0.0;
      m_quantum_state = NULL;
      m_volume_state = 0.0;
      m_quantum_coherence = 0.0;
   }
   
   // Define parâmetros
   void SetParameters(int period, double surge_threshold)
   {
      m_period = period;
      m_surge_threshold = surge_threshold;
      m_logger.Info("Parâmetros do agente de volume atualizados");
   }
   
   // Atualiza métricas
   void Update() override
   {
      // Calcula média móvel e desvio padrão do volume
      long volumes[];
      ArraySetAsSeries(volumes, true);
      
      if(CopyTickVolume(m_symbol, m_timeframe, 0, m_period, volumes) > 0)
      {
         double sum = 0.0;
         double sum2 = 0.0;
         
         for(int i = 0; i < m_period; i++)
         {
            sum += volumes[i];
            sum2 += volumes[i] * volumes[i];
         }
         
         m_volume_ma = sum / m_period;
         double variance = (sum2 - sum * sum / m_period) / (m_period - 1);
         m_volume_std = MathSqrt(variance);
         
         // Atualiza estados quânticos
         if(m_quantum_state != NULL)
         {
            m_volume_state = m_quantum_state.GetQuantumState();
            m_quantum_coherence = m_quantum_state.GetCoherence();
         }
      }
      
      m_last_update_time = TimeCurrent();
   }
   
   // Obtém sinal
   double GetSignal() override
   {
      long current_volume = 0;
      
      if(CopyTickVolume(m_symbol, m_timeframe, 0, 1, &current_volume) > 0)
      {
         if(m_volume_std > 0)
         {
            double z_score = (current_volume - m_volume_ma) / m_volume_std;
            
            if(z_score > m_surge_threshold)
               return 1.0;   // Sinal de compra
            else if(z_score < -m_surge_threshold)
               return -1.0;  // Sinal de venda
         }
      }
      
      return 0.0;  // Sem sinal
   }
   
   // Obtém confiança
   double GetConfidence() override
   {
      long current_volume = 0;
      
      if(CopyTickVolume(m_symbol, m_timeframe, 0, 1, &current_volume) > 0)
      {
         if(m_volume_std > 0)
         {
            double z_score = MathAbs((current_volume - m_volume_ma) / m_volume_std);
            m_confidence = MathMin(z_score / m_surge_threshold, 1.0);
            
            // Ajusta confiança baseado no estado quântico
            if(m_quantum_state != NULL)
            {
               m_confidence *= m_quantum_coherence;
            }
            
            return m_confidence;
         }
      }
      
      return 0.0;
   }
   
   // Obtém média móvel do volume
   double GetVolumeMA()
   {
      return m_volume_ma;
   }
   
   // Obtém desvio padrão do volume
   double GetVolumeStd()
   {
      return m_volume_std;
   }
   
   // Obtém Z-score do volume atual
   double GetCurrentVolumeZScore()
   {
      long current_volume = 0;
      
      if(CopyTickVolume(m_symbol, m_timeframe, 0, 1, &current_volume) > 0)
      {
         if(m_volume_std > 0)
            return (current_volume - m_volume_ma) / m_volume_std;
      }
      
      return 0.0;
   }
   
   // Obtém tempo da última atualização
   datetime GetLastUpdateTime()
   {
      return m_last_update_time;
   }
};
//+------------------------------------------------------------------+
