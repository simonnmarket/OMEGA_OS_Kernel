ID: DOC-EXEC-OMEGA-GENESIS-PSA-20260418  
Destinatário: PSA / Conselho / CEO  
Status: Pronto para execução (fase paper)  

### 1) Objetivo e métrica-alvo  
- Meta operacional (demo/paper): 0.1%–0.5% a.d. com DD ≤5%.  
- Target aspiracional $1k/dia em $10k fica apenas como potencial, não objetivo diário.  

### 2) SLO/GO-NOGO (cortes físicos)  
- DSN Postgres p95 ≤20 ms (alerta 20–50 ms; NOGO >50 ms).  
- RTT MT5: <100 ms paper; <20 ms live.  
- Seed L1 fresco <4h.  
- Janela 09:00–17:00 local.  
- Guardrails: DD ≤5%; lote ≤0.01; máx. 3 retcodes falhos; PANIC_FLAT_ALL pronto.  

### 3) Pipeline obrigatório (mutex)  
- Execução única via `preflight_and_run_prod.ps1` com mutex global (exclusão mútua).  
- Proibido rodar orquestrador/shadow em paralelo ou fora do preflight.  

### 4) Pré-requisitos técnicos  
- PgBouncer em transaction pooling entre app e Postgres (ativar antes do live; recomendado já em paper).  
- Observabilidade ativa: p95/p99, lock waits, rollbacks, conexões, cache hit (Prom/Grafana/alertas).  
- Filtro “cínico” no L1 (Postgres):  
  - regime HIGH_VOLATILITY/KILL_SWITCH → bloquear (DEAD_MAN_OUT).  
  - |momentum_1m_pct| < 0.80 → HOLD.  
  - Caso contrário → LIVE.  
- PANIC_FLAT_ALL: IOC com deviation 10–50; executar imediato, registrar em audit.  

### 5) Procedimento diário (fase paper, 3 dias)  
1. Garantir DSN real e seed <4h.  
2. Garantir mutex habilitado no preflight.  
3. Rodar preflight + execução (paper) apenas pelo script abaixo.  
4. Coletar artefatos em `Auditoria PARR-F/Auditoria Conselho`:  
   - `omega_audit_*.json`, `audit_run_*.log`, `paper_loop_*.log`, `manifest.json`, `resumo_metricas_demo_YYYYMMDD.json` (com hashes).  
5. Se qualquer SLO quebrar → NOGO e registrar motivo.  

### 6) Script oficial de execução (PowerShell)  
```powershell
# Caminho base
Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"

# DSN real
$env:FIN_SENSE_DSN = "postgresql://finsense_user:staging_pass@localhost:5433/finsense_staging"

# Janela / mutex / preflight + run (modo padrão: paper)
.\preflight_and_run_prod.ps1 -Mode "paper"

# Live somente após 3 dias verdes + hashes canônicos + autorização explícita:
# $env:OMEGA_PROD_AUTHORIZATION = "CONSELHO_GO_2026"
# .\preflight_and_run_prod.ps1 -Mode "live"
```

### 7) GO/NOGO rápido (paper)  
- GO: DSN p95 ≤20 ms; RTT MT5 <100 ms; seed <4h; janela ok; guardrails ok; pipeline único.  
- NOGO: DSN p95 >50 ms; RTT MT5 >100 ms; seed stale; janela violada; mutex ausente; qualquer guardrail rompido.  

### 8) Transição para live (após 3 dias paper verdes)  
- Requer: hashes canônicos aprovados; `OMEGA_PROD_AUTHORIZATION=CONSELHO_GO_2026`; DSN p95 ≤20 ms; RTT MT5 <20 ms (migrar para VPS/colo se preciso); PgBouncer + observabilidade ativos; manifest atualizado com status GO.  

### 9) Notas de risco  
- RTT <20 ms só viável com hosting dedicado (NY4/LD4/VPS de baixa latência).  
- PANIC_FLAT_ALL deve permanecer no caminho mínimo (sem lógica pesada).  
- Qualquer execução fora do script acima invalida auditoria e deve ser tratada como NOGO.
