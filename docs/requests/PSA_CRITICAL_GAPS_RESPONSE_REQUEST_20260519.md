# Pedido de resposta PSA — Gaps críticos (prazo 2026-05-20 12:00 UTC)

**Para:** PSA Team / Operações OMEGA  
**De:** Red Team / Engenharia (via repositório)  
**Data do pedido:** 2026-05-19  
**Prazo de resposta:** **2026-05-20 12:00 UTC**

---

## Pergunta crítica (resposta obrigatória: Sim / Não / Parcial)

**Os três gaps abaixo podem ser fechados até 2026-05-20 12:00 UTC?**

1. **Série histórica `ks_daily_state`** (export diário completo, não só snapshot), **ou** documentação formal de indisponibilidade com justificativa.  
2. **`risk_config` completo** (`sl_pct`, `tp_pct`, `kill_switch_threshold`, `circuit_breaker_threshold` + regras efectivas), a partir de `shadow_loop.py` / env / configs reais.  
3. **`account_equity_eod.jsonl` fiável** (correcção da captura), **ou** confirmação explícita de que se mantém como **não confiável** e o diagnóstico de portfolio prossegue com essa limitação.

---

## Como responder (PSA)

Preencher **uma** das opções e copiar para o canal acordado (e-mail / chat / ticket):

### Opção A — **Sim** (entrega completa)

- Anexar ou apontar localização dos ficheiros actualizados (ou delta sobre `OMEGA_DIAGNOSTIC_DATA_20260518/`).  
- Indicar se o pacote foi regenerado com `build_omega_diagnostic_package_20260518.py` ou se os ficheiros foram substituídos manualmente.  
- Confirmar **offset de timezone** dos logs FlowSignal se aplicável (`--flow-signal-local-offset-hours`).

### Opção B — **Não** (parcial)

- Declarar quais dos **3** itens **não** serão entregues até ao prazo.  
- Para cada item não entregue: **motivo** + **ETA** revisada (se existir).  
- Actualizar ou validar o `README.md` do pacote com essas limitações (o CEO v2.0 prevê diagnóstico **parcial** com incerteza explícita).

### Opção C — **Parcial** (mistura)

- Especificar item a item: entregue / pendente / indisponível.  
- Anexar o que estiver pronto **hoje** (entrega incremental).

---

## Red Team

**Estado:** Aguarda **confirmação escrita da PSA** acima antes de tratar o pacote como “final” para validação formal e arranque da análise de diagnóstico sistemático.

**Após resposta PSA:**

- **Sim ou parcial com ficheiros:** validar reconciliação, UTC, completude dos campos pedidos no CEO v2.0.  
- **Não (só documentação):** validar que o `README.md` do pacote espelha os gaps; prosseguir com **diagnóstico parcial** nas camadas Risk/Portfolio com limitações explícitas no relatório.

---

## Suporte (se a PSA precisar)

A engenharia pode disponibilizar **scripts ou passos** para extrair KS histórico, matriz de env, ou correcção do pipeline EOD — abrir pedido com amostra de paths e permissões de onde correr os exports.

---

## Registo de resposta PSA (preencher)

| Pergunta | Resposta (Sim / Não / Parcial) |
| --- | --- |
| Série `ks_daily_state` até ao prazo? | |
| `risk_config` completo até ao prazo? | | 
| EOD corrigido ou aceite como não fiável até ao prazo? | |

**Nome / função:**  
**Data/hora (UTC):**  
**Link ou caminho dos ficheiros:**  

---

*Documento gerado para evitar ambiguidade entre equipas; não substitui assinatura no pedido CEO v2.0.*
