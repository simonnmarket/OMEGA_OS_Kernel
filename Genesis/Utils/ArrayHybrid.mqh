//+------------------------------------------------------------------+
//| ArrayHybrid.mqh - Estratégia Híbrida de Crescimento de Arrays    |
//| Projeto: Genesis                                                 |
//| Finalidade: Balancear performance (HFT) e rastreabilidade        |
//+------------------------------------------------------------------+
#ifndef __GENESIS_ARRAY_HYBRID_MQH__
#define __GENESIS_ARRAY_HYBRID_MQH__

// Tuning de crescimento padrão (alterável por build config)
#ifndef ARRAY_GROWTH_CHUNK
  #define ARRAY_GROWTH_CHUNK 50
#endif

// Caminho de logging opcional (quando disponível)
#include <Controls\Label.mqh>

// Implementação baseada em macro para suportar arrays de qualquer tipo
// Uso: ArrayPushBack(arr, value);
#ifdef USE_ARRAYRESIZE_OPTIMIZED
  // Otimizado para HFT: prioriza ArrayResize com chunk
  #define ArrayPushBack(arr, val) \
    ArrayResize(arr, ArraySize(arr)+1, ARRAY_GROWTH_CHUNK); \
    (arr)[ArraySize(arr)-1] = (val)
#else
  // Híbrido: ainda usa ArrayResize com chunk generoso; logging opcional via macro dedicada
  #define ArrayPushBack(arr, val) \
    ArrayResize(arr, ArraySize(arr)+1, ARRAY_GROWTH_CHUNK); \
    (arr)[ArraySize(arr)-1] = (val)
#endif

// Variante com logging contextual quando um logger estiver disponível
// Uso: ArrayPushBackCtx(arr, value, logger, "Contexto")
#define ArrayPushBackCtx(arr, val, logger, ctx) \
  ArrayResize(arr, ArraySize(arr)+1, ARRAY_GROWTH_CHUNK); \
  (arr)[ArraySize(arr)-1] = (val); \
  logger.log_info(StringFormat("[ArrayPushBack] %s | size=%d", ctx, ArraySize(arr)))

#endif // __GENESIS_ARRAY_HYBRID_MQH__


