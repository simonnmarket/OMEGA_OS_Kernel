//+------------------------------------------------------------------+
//| GenesisConfig.mqh - Configurações Centrais do Projeto            |
//+------------------------------------------------------------------+
#ifndef __GENESIS_CONFIG_MQH__
#define __GENESIS_CONFIG_MQH__

// Atualizações/intervalos
#define CFG_QNF_UPDATE_MS            150
#define CFG_QWT_UPDATE_MS            200
#define CFG_QDP_UPDATE_MS            200
#define CFG_QMDQ_UPDATE_MS            50

// Parâmetros quânticos gerais
#define CFG_QUBITS_WAVELET           256
#define CFG_QUBITS_PROCESSING        512
#define CFG_ENTROPY_THRESHOLD       0.15
#define CFG_ENABLE_Q_DENOISE        true
#define CFG_ENABLE_Q_FILTER         true
#define CFG_MAX_LATENCY_NS          10.0
#define CFG_QNF_FILTER_STRENGTH     0.8

#endif // __GENESIS_CONFIG_MQH__


