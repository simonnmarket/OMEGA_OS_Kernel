# PSA — Complemento AIC Etapa 2A (Instruções + Regras Operacionais)

**ID:** `PSA_COMPLEMENTO_AIC_ETAPA2A_20260604`  
**Origem:** AIC — Chief Audit Intelligence  
**Para:** PSA — Principal Solution Architect  
**Data recebida:** 2026-06-04 (sessão nocturna 03/Jun)  
**Documento AIC de referência:** `AIC-ACTA-FECHAMENTO-ETAPA1-20260604.md`  
**Status Etapa 1:** FECHADA (técnica) — E1.7 push remoto confirmado (`2ff0d69`)  
**Status Etapa 2A:** ACTIVA — janela 24h desde 21:52:26 UTC 03/Jun

---

## 1. INSTRUÇÃO AIC — TEXTO ORIGINAL

> PSA,
>
> AIC aceita o handoff 03/Jun (wire + hot-reload, PID 9972, FastLoop 21:52:26).
> Etapa 1: FECHADA (técnica). Etapa 2A: ACTIVA — prova G1 batimento cardíaco.
>
> Instruções adicionais:
> 1. Não reiniciar PID 9972 salvo FATAL ou ordem CEO.
> 2. Commit em shadow_loop/async_position_orchestrator → restart obrigatório (sem hot-reload).
> 3. add=True → DISPATCH em ~5 linhas; silêncio = escalado imediato.
> 4. 08:00 UTC: psa_capture_session_report.ps1 — uma linha batimento, sem PnL.
>    AGUARDA MERCADO (zero add=True) não é FAIL.
> 5. Proibido "validado" / "pipeline LIVE" até EXEC OK ou EXEC FAIL pós-DISPATCH.
>
> Entregáveis 08:00: linha batimento | PID lock | git log+status | contagens add/DISPATCH/EXEC.
>
> Doc: governance/PSA_COMPLEMENTO_AIC_ETAPA2A_20260604.md
> GO live: NÃO autorizado.
>
> AIC

---

## 2. REGRAS OPERACIONAIS (PSA — vigência Etapa 2A)

### 2.1 Runner PID 9972

| Regra | Condição de excepção |
|-------|----------------------|
| NÃO reiniciar | Salvo FATAL no log ou ordem explícita CEO |
| Restart obrigatório se commit em `shadow_loop.py` ou `async_position_orchestrator.py` | Python sem hot-reload — código novo = restart |
| Restart via `psa_capture_session_go.ps1 -Background` | Preflight py_compile + pytest antes |

### 2.2 Monitorização G1 — Batimento Cardíaco

```
[PYRAMID_EVAL] ... add=True ...
   ↓ ~5 linhas seguintes obrigatórias:
[PYRAMID_DISPATCH] ... parent=#... symbol=... layer=... lot=...   (APO)
[PYRAMID_DISPATCH] ... source=FASTLOOP_DRAIN ...                  (shadow_loop drain)
[MT5_ORDERSEND] pyramid parent=#...
[PYRAMID] ... EXEC OK  ←── G1 PASS
         ou EXEC FAIL  ←── G1 PASS (tentativa registada, retcode analisado)
```

**Silêncio após add=True** (ausência de DISPATCH em ~5 linhas) = **escalado imediato** ao CEO.

### 2.3 Linguagem proibida até G1 PASS

| Proibido | Permitido |
|----------|-----------|
| "validado" | "tecnicamente operacional" |
| "pipeline LIVE" | "código activo, aguarda trigger mercado" |
| "capture activa" | "Etapa 2A em curso" |
| "pyramid funcional" | "batimento pendente confirmação mecânica" |
| "PnL capturado" em relatório 08:00 | Apenas linha veredito batimento |

---

## 3. ENTREGÁVEIS 08:00 UTC 04/JUN

### Comando

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\psa_capture_session_report.ps1
```

### Formato entregável (4 itens obrigatórios)

```
1. LINHA BATIMENTO:
   ✅ BATIMENTO     — add=True → DISPATCH → ORDERSEND → EXEC OK/FAIL
   ⏳ AGUARDA MERCADO — zero add=True (não é FAIL)
   ❌ SILÊNCIO CARDÍACO — add=True + zero DISPATCH (FAIL G1)

2. PID LOCK:
   audit/paper/omega_runner.lock = <PID>

3. GIT LOG+STATUS:
   HEAD = <hash> | remote = origin/hotfix/... | dirty files = <N>

4. CONTAGENS (desde 21:52:26 UTC):
   add=True: <N> | DISPATCH: <N> | ORDERSEND pyramid: <N> | EXEC OK: <N> | EXEC FAIL: <N>
```

---

## 4. INTERPRETAÇÃO VEREDITO 08:00

| Resultado | Significado | Próximo passo |
|-----------|-------------|---------------|
| ✅ BATIMENTO | G1 PASS — sequência broker confirmada | Planear Etapa 2B (CEO autoriza) |
| ⏳ AGUARDA MERCADO | Zero add=True na janela — pipeline saudável, sem trigger | Estender 24h; G1 aberto |
| ❌ SILÊNCIO CARDÍACO | add=True + zero DISPATCH | FAIL G1; Eng. convocada para reunião CEO |

**Etapa 2B** (5 dias estatísticos): só após G1 PASS + E1.7 fechado (remoto em sync).  
**GO live**: NÃO autorizado.

---

## 5. GATES ETAPA 2A (referência rápida)

| Gate | PASS | FAIL |
|------|------|------|
| G1 Batimento | `add=True → DISPATCH → ORDERSEND → EXEC OK/FAIL` | add=True sem DISPATCH |
| G3 Relatório | Linha 08:00 entregue | Ausente |
| G4 Git | Remote = HEAD | Branch ahead sem push |
| G5 Runner | PID 9972 vivo, mode=paper | Morto ou shadow |

---

## 6. REGISTO ACEITAÇÃO PSA

PSA aceita integralmente as 5 instruções AIC. Registo de recebimento:

| Instrução | Recebida | Implementada |
|-----------|----------|-------------|
| 1. Não reiniciar PID 9972 salvo FATAL/CEO | SIM | SIM — PID 9972 em curso |
| 2. Commit core → restart obrigatório | SIM | SIM — regra documentada |
| 3. add=True → DISPATCH em ~5 linhas; silêncio = escalado | SIM | SIM — monitor activo |
| 4. 08:00 UTC — uma linha batimento, sem PnL | SIM | PENDENTE — 08:00 UTC |
| 5. Proibido "validado"/"pipeline LIVE" até EXEC OK/FAIL | SIM | SIM — linguagem ajustada |

---

*PSA — Principal Solution Architect | AIC_TIER0_RULES_v4 | Etapa 2A activa | 2026-06-04*
