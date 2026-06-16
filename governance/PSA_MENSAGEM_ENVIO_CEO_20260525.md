# Mensagem CEO → PSA (copiar e enviar)

**Assunto:** OMEGA — Comando definitivo ecossistema unificado — executar hoje — incidente auditoria

**Para:** PSA (Devin)  
**Prioridade:** Crítica  
**Data:** 2026-05-25

---

PSA,

Fechámos a análise de **porque falhas críticas permaneceram após auditorias APROVADO**. Não é regressão P0 — é **gap de integração** (motores PSA / Orquestrador / fusão / runner desalinhados). O código de correção **já está no repositório**; o runner em DEMO **ainda pode estar com processo antigo** até reiniciares.

**Executar apenas este pacote (v3.0) — não reimplementar P0:**

| # | Documento |
|---|-----------|
| 1 | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\governance\PSA_COMANDO_DEFINITIVO_ECOSISTEMA_20260525.md` |
| 2 | `governance\AIC_INCIDENTE_AUDITORIA_SCOPE_GAP_20260525.md` (acta — contexto) |
| 3 | `governance\GATE_INTEGRACAO_ECOSISTEMA_OBRIGATORIO_20260525.md` (critérios PASS/FAIL) |

**Resumo execução:**

1. `git pull` branch `feat/execution-router-atr-20260523` — confirmar `modules\omega_ecosystem_unified.py` existe  
2. **Parar** runner 24×7 actual  
3. `pytest` 34/34 + `.\scripts\omega_integration_gate.ps1 -Phase preflight`  
4. `.\scripts\omega_demo_go_live.ps1`  
5. `.\scripts\run_omega_24x7.ps1`  
6. Após 3 ciclos: `.\scripts\omega_integration_gate.ps1 -Phase runtime`  
7. Após 1h: `.\scripts\omega_integration_gate.ps1 -Phase kpi -LogHours 1`  
8. Criar relatório: `governance\PSA_RELATORIO_INTEGRACAO_ECOSISTEMA_20260525.md` (template no comando §6)

**Só dizer “resolvido” ao CEO com veredito INTEGRAÇÃO PASS** (gate runtime OK + relatório 1h).

**Proibido:** remover `OMEGA_ECOSYSTEM_UNIFIED`, repor 7 ativos / max_positions=2 no calibrador, `PSA_SHADOW_MODE=1`.

Dúvidas: enviar `git log -1`, saída do integration_gate, manifesto JSON e últimas 100 linhas do log.

— CEO / AIC
