# RT-E — Mandato VitalSigns (Cycle 2 — condição COO)

**ID:** RT_E_VITALSIGNS_MANDATO_20260331  
**Data:** 31 de março de 2026  
**Referência:** `AUDITORIA FORENSE PSA` / AFC; mandato CEO (verificação final).

---

## 1. Implementação

| Item | Valor |
|------|--------|
| Ficheiro | `Auditoria PARR-F/11_live_demo_cycle_1.py` |
| Versão script | **1.3.0** |
| Classe | `VitalSignsMonitor` |
| Parâmetros | `window_size=30`, `volatility_floor=0.05` |
| Chamada | `vitals.check_pulse(z)` após cada `motor.step` no loop live |

**Comportamento:** se, com janela cheia, o desvio-padrão de |Z| na janela for inferior ao piso, levanta `SystemError` (flatline) — para o ciclo sem “silêncio” prolongado sem alarme.

---

## 2. Template de Verdade Unificada (próximos relatórios ao Conselho)

1. **Cabeçalho:** SHA do commit Git (preencher após `git commit`).
2. **Dados:** nome do ficheiro + hash SHA3-256 (manifesto ou `sha3_256` por linha no log).
3. **Métricas:** números **copiados** da saída de `verify_tier0_psa.py` ou `audit_trade_count.py` (sem reescrita manual).
4. **Conclusão:** CQO/CIO só assinam se os números coincidirem com o item 2.

**Exemplo de números SWING V10.5 (stress em disco):** `STRESS_V10_5_SWING_TRADE.csv` — `signal_fired == True` em **222** linhas (validar com script antes de publicar).

---

## 3. Itens ainda pendentes (COO 19:46 CET — não confundir com este patch)

- **Heartbeat** por tempo sem sinal (ex.: 4 h) — não incluído neste RT-E.
- **Threshold adaptativo** — decisão de produto; não alterado no código (mantém-se `MIN_Z_ENTRY = 2.0`).
- **Correção documental** CQO/CIO (47 vs 222) — obrigatória antes de nova assinatura.

---

## 4. Estado do projeto

**Recuperação controlada:** monitoramento cardíaco mínimo (flatline) **ativo** no demo live; Cycle 2 depende ainda de checklist COO (heartbeat, coerência documental, paridade threshold) conforme parecer unificado.

**Assinatura técnica:** PSA — implementação conforme mandato; **SHA Git:** a9fdb7a63232045f3662017bcd3bed8334205b81


**Handoff 20260401 — próximo passo: demo MT5 sec. 5.2 após gate PASS**
