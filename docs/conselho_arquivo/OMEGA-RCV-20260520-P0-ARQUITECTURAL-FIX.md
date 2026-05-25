# DOCUMENTO TÉCNICO DEFINITIVO — CONSELHO DE ADMINISTRAÇÃO

**ID:** OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX  
**De:** Gabinete do CKO / Arquiteto Red Team  
**Para:** Conselho de Administração / CEO  
**Data:** 2026-05-20  
**Classificação:** Confidencial — Risco Existencial de Capital  
**Assunto:** RCA Final — Falha na Camada de Execução, Risco de Spike e Plano de Remediação Não Negociável

---

## 1. RESUMO EXECUTIVO PARA O CONSELHO (BLUF)

O sistema OMEGA encontra-se em **paragem de segurança imediata e obrigatória**.

A investigação conjunta entre o CEO, o CKO e a PSA concluiu que a degradação de capital **não foi causada** por falha no modelo de Inteligência Artificial, nem nas estratégias quantitativas. O problema reside exclusivamente na **ponte de execução (Execution Bridge)** que liga o motor algorítmico ao broker.

Foi identificada uma falha de arquitectura de risco inaceitável: mecanismo de execução que, em cenários de rejeição ou latência, pode deixar posições sem SL nativo no broker durante micro-janelas. Se ocorrer um spike de liquidez nesse intervalo, o risco é existencial.

Este documento detalha a anatomia do erro, o mecanismo de perda de capital e as **4 regras de engenharia não negociáveis** antes de o sistema voltar a operar.

---

## 2. A FALHA EXISTENCIAL: EXECUÇÃO NÃO ATÓMICA (RISCO DE SPIKE)

**Problema (padrão proibido):** Entrada com `sl=0` / `tp=0` seguida de `PositionModify` para anexar SL.

**Risco:** Janela sem proteção no servidor do broker entre passo 1 e 2.

**Veredito CKO:** Proibida abertura sem SL/TP no **primeiro** pacote `order_send`. Se broker rejeitar (10016 INVALID_STOPS), **cancelar** — não modificar depois.

---

## 3. MICROESTRUTURA VS. STOP LOSS CURTO

Evidência PSA (perfil temporal): grande maioria de SL em **< 1 minuto** — assinatura de SL vs spread/rollover, não de estratégia lenta.

**Causa:** SL curto vs spread (rollover ~00:05 UTC) sem Spread Guard adequado.

---

## 4. TELEMETRIA — FONTE NULL

| Fonte do Sinal | Trades SL (PSA) | % |
| --- | ---: | ---: |
| NULL | 689 | 77,9% |
| MOMENTUM_MT5 | 174 | 19,7% |
| SYNC_RECOVERY | 22 | 2,5% |
| Agent IA | ~0 | 0% |

**Interpretação:** Perdas concentradas em caminho sem etiqueta / fallback — não no motor IA documentado.

---

## 5. PLANO DE REMEDIAÇÃO — 4 MANDATOS

| # | Mandato | Regra |
| --- | --- | --- |
| M1 | Execução atómica | SL/TP no primeiro `order_send`; 10016 → abort |
| M2 | Spread Guard | `SL_pts >= 3 × spread` → senão `SKIP_SPREAD_GUARD` |
| M3 | Blackout rollover | 23:55–00:10 UTC → `SKIP_ROLLOVER_BLACKOUT` |
| M4 | Bloqueio NULL | `signal_source` NULL/SYNC → abort |

---

## 6. CONDIÇÃO DE RESTART

Log de teste: ordem **rejeitada** 10016 **sem** posição desprotegida; ordens aceites com SL visível no MT5.

---

## 7. ESTADO DE IMPLEMENTAÇÃO (Engenharia 2026-05-20)

| Mandato | Ficheiro | Estado |
| --- | --- | --- |
| M1–M4 | `core_engines/shadow_loop.py` | **Implementado** (nível código) |
| Diagnóstico 24h | `scripts/run_omega_24x7.ps1` | **0,2% / 5 pos / sem --equity** |
| Validação broker | Demo MT5 | **Pendente** (CEO/OPS) |

Ver análise: `docs/requests/OMEGA_RCV_20260520_P0_ARQUITECTURAL_FIX_ANALISE.md`

---

*Documento arquivado em `docs/conselho_arquivo/` para GitHub via PSA.*
