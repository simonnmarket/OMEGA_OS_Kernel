# PSA — Envio imediato + registo para auditoria (2026-05-18 / 2026-05-19)

**Objectivo:** (1) Saber **exactamente** o que enviar **agora** à PSA para ela poder **executar e responder**. (2) Ter **um único registo** com tudo o que a engenharia alterou/gerou, para **memória institucional** e auditorias futuras.

---

## 1. O que enviar **agora** à PSA (sugestão mínima)

| Prioridade | Documento | Para quê |
| --- | --- | --- |
| **P0 — obrigatório** | `docs/requests/PSA_CRITICAL_GAPS_RESPONSE_REQUEST_20260519.md` | Pergunta **Sim / Não / Parcial** sobre os **3 gaps** até **2026-05-20 12:00 UTC**; modelo de resposta no fim do ficheiro. **Sem isto a PSA não tem “tarefa fechada” com prazo.** |
| **P0 — especificação** | `docs/requests/OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v2.0_20260518.md` | Pedido CEO **v2.0** (estrutura do pacote, campos, agregados, README). |
| **P1 — registo do dia + índice** | **Este ficheiro:** `docs/requests/OMEGA_PSA_ENVIO_IMEDIATO_E_AUDITORIA_20260519.md` | **Capa / índice** + changelog + lista de artefactos para auditoria. |

**Opcional mas recomendado** (PSA e Red Team alinhados no mesmo “pacote mental”):

| Anexo | Ficheiro |
| --- | --- |
| Avaliação final v2.0 (inglês, contagens) | `docs/requests/OMEGA_TRADING_SYSTEM_FINAL_EVALUATION_AND_NEXT_STEPS_v2.0_20260518.md` |
| Review de script + next steps | `docs/requests/OMEGA_TRADING_SYSTEM_SCRIPT_REVIEW_AND_NEXT_STEPS_20260518.md` |

**Resumo em uma frase para o e-mail/chat:**  
*“Segue em anexo o pedido de resposta PSA (prazo 2026-05-20 12:00 UTC), o pedido CEO v2.0, e o registo de engenharia/auditoria do dia com índice de todos os artefactos.”*

---

## 2. O “documento de memória” para auditoria (o que pediu)

**Não precisa ser um segundo e-mail misterioso:** use **este documento** (`OMEGA_PSA_ENVIO_IMEDIATO_E_AUDITORIA_20260519.md`) como **registo único**. Ele concentra:

- O que a PSA deve fazer **já** (secção 1).  
- **Changelog** do trabalho de engenharia (secção 3).  
- **Inventário** de ficheiros tocados/gerados (secção 4).  
- **Como reproduzir** o pacote (secção 5).

Se quiser **arquivo físico** para arquivo da PSA: compactar num `.zip` a pasta `docs/requests/` **filtrada** aos ficheiros listados na secção 4 + (se política permitir) uma cópia do `README.md` já gerado dentro de `OMEGA_DIAGNOSTIC_DATA_20260518/`.

---

## 3. Changelog — engenharia (memória do dia)

*Ordem aproximada do que foi feito no ciclo “diagnóstico CEO v2.0 + review + avaliação final”.*

| Área | Alteração |
| --- | --- |
| **Script** | `scripts/build_omega_diagnostic_package_20260518.py`: pacote `OMEGA_DIAGNOSTIC_DATA_20260518/`; deals/orders enriquecidos; backfill `exit_reason`; `cycle_exit` a partir de `evaluation_timeline.jsonl`; manifest `git_head`; EOD com `reliability_flag`; `risk_config` com chaves CEO (valores `null` onde não há fonte). |
| **Sinais** | FlowSignal: filtro `MOMENTUM` / `SEM_FONTE` / `SYNC_RECOVERY`; CLI `--flow-signal-local-offset-hours`; proxy **SEM_FONTE** a partir de `trade_feedback` (dedupe; `--no-sem-fonte-null-proxy`); **SYNC_RECOVERY** desde `trade_feedback` quando não há FlowSignal; CSVs com `provenance`, `position_ticket`, offset aplicado. |
| **Qualidade código** | Reparo de regressões (ex.: função `pearson`, cabeçalhos CSV vazios, regex `sl`/`tp` em comentários). |
| **README gerado** | Secção **§1.1 contagens**; texto explícito `cycle_exit` (N `run_end`); origem SEM/SYNC; link ao doc de avaliação v2.0. |
| **Documentação** | CEO v2.0 request; script review; avaliação final v2.0; pedido de resposta PSA; avaliação PT (supersedida); **este índice**. |
| **Pacote** | Saída: `audit/psa_inbound/OMEGA_DIAGNOSTIC_DATA_20260518/` (raw + aggregated + signals + README). |

---

## 4. Inventário de artefactos (caminhos no repo)

### 4.1 Documentos (`docs/requests/`)

| Ficheiro | Nota |
| --- | --- |
| `PSA_CRITICAL_GAPS_RESPONSE_REQUEST_20260519.md` | **Envio imediato** — resposta PSA. |
| `OMEGA_PSA_ENVIO_IMEDIATO_E_AUDITORIA_20260519.md` | **Este ficheiro** — capa + auditoria. |
| `OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v2.0_20260518.md` | Especificação CEO v2.0. |
| `OMEGA_TRADING_SYSTEM_SCRIPT_REVIEW_AND_NEXT_STEPS_20260518.md` | Review do script. |
| `OMEGA_TRADING_SYSTEM_FINAL_EVALUATION_AND_NEXT_STEPS_v2.0_20260518.md` | Avaliação final + contagens + gaps. |
| `OMEGA_DIAGNOSTIC_FINAL_EVALUATION_AND_NEXT_STEPS_20260518.md` | Versão PT anterior; **supersedida** pelo v2.0 EN. |
| `OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v1.0_20260518.md` | Histórico v1.0. |

### 4.2 Código

| Ficheiro |
| --- |
| `scripts/build_omega_diagnostic_package_20260518.py` |

### 4.3 Pacote gerado (não versionar no git se política for “artefacto binário”; para PSA pode ir como ZIP à parte)

| Caminho |
| --- |
| `audit/psa_inbound/OMEGA_DIAGNOSTIC_DATA_20260518/` |

---

## 5. Como a PSA (ou vós) reproduzem o pacote

Na raiz `SOURCE_CODE`:

```bash
python scripts/build_omega_diagnostic_package_20260518.py
```

Se o broker confirmar que o prefixo de tempo nos logs FlowSignal é **UTC+3** em relação ao UTC:

```bash
python scripts/build_omega_diagnostic_package_20260518.py --flow-signal-local-offset-hours 3
```

---

## 6. Sugestão prática (resposta directa às tuas duas questões)

1. **“Qual documento envio *agora* para a PSA executar?”**  
   → Envie **primeiro** `PSA_CRITICAL_GAPS_RESPONSE_REQUEST_20260519.md` **junto com** `OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v2.0_20260518.md` (senão a PSA não sabe *o quê* entregar além de responder Sim/Não).

2. **“Deve conter tudo o que fizemos hoje para memória / auditoria?”**  
   → Sim. Use **`OMEGA_PSA_ENVIO_IMEDIATO_E_AUDITORIA_20260519.md`** como **documento-mãe**: na mesma mensagem, indique que o changelog e o inventário estão **na secção 3 e 4** desse ficheiro, e anexe (ou zip) os outros `.md` listados em 4.1 se a política da empresa for “anexos explícitos”.

**Não é obrigatório** enviar o ZIP do pacote **neste primeiro contacto** se ainda não houver resposta aos gaps — mas **é útil** anexar o `README.md` já gerado ou o caminho interno do servidor onde o pacote `OMEGA_DIAGNOSTIC_DATA_20260518/` está, para a PSA alinhar com o que já existe.

---

*Documento preparado para envio institucional; ajuste destinatários e canais conforme governança OMEGA.*
