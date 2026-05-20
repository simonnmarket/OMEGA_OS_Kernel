# OMEGA — Remediação CICC/CITIC — Execução PSA v3.1 (APROVADO CEO)

---

## MEMORANDO PSA — Entrega e arquivamento (ler antes de executar)

**Para:** Principal Solution Architect (PSA)  
**De:** CEO / Conselho (documento único aprovado)  
**Assunto:** Onde guardar este pacote no sistema OMEGA e no GitHub  
**Data:** 2026-05-20

### O que é este ficheiro

Este é o **único documento operacional** enviado na pasta `Auditoria\Aprovado\`. Todos os outros rascunhos, índices e versões anteriores foram **retirados** — não usar ficheiros antigos do Desktop.

### Onde a PSA deve salvar (obrigatório)

| # | Acção | Caminho no PC | GitHub |
|---|--------|---------------|--------|
| 1 | Copiar **este ficheiro** | `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\governance\DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` | Incluir no PR |
| 2 | Veredito Conselho (já no repo) | `...\governance\DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` | Incluir no PR |
| 3 | Registo DOC-OFC — actualizar Secção 13 | `...\governance\DOC-OFC-REGISTO-PSA-MUDANCAS-OPERACIONAIS-E-GOVERNANCA-20260518.md` | Incluir no PR |
| 4 | Aprovações CKO/CIO (arquivo) | `...\docs\conselho_arquivo\aprovado_conselho_20260520\` | Incluir no PR |
| 5 | Forense PSA | `...\docs\conselho_arquivo\forensic_20260520\` | Incluir no PR |
| 6 | Relatório validação (preencher após P0) | `...\docs\requests\PSA_RELATORIO_VALIDACAO_CICC_20260520.md` | Incluir no PR |
| 7 | Evidências pós-patch | `...\audit\forensic\post_patch_20260520\` | Incluir no PR (screenshots + export Tier-0) |
| 8 | Pacote ZIP forense (já existe) | `...\audit\forensic\OMEGA_FORENSIC_AUDIT_20260520\` | Não duplicar |

### Branch e PR

- **Branch:** `fix/cicc-remediation-magic-mutex-20260520`  
- **Repositório:** `https://github.com/simonnmarket/OMEGA_OS_Kernel`  
- **Commit:** único atómico (magic + mutex + módulos + scripts — ver Secção 4)  
- **Não fazer merge** sem P0-VAL PASS e relatório Secção 6 preenchido.

### Desktop CEO (após arquivar no repo)

A pasta `C:\Users\Lenovo\Desktop\File Desktop\Arquivos Pendentes Auditoria\Pendente\Auditoria\Aprovado\` deve conter **apenas** uma cópia deste documento. Não criar novos `.txt` dispersos.

### Confirmação PSA (checklist entrega)

- [ ] Ficheiros 1–3 commitados em `governance/`  
- [ ] Pastas 4–5 em `docs/conselho_arquivo/`  
- [ ] PR aberto com link neste memorando  
- [ ] CEO notificado quando P0-VAL estiver PASS  

*Fim do memorando — a seguir: ordem de execução técnica.*

---

| Campo | Valor |
|-------|--------|
| **ID** | OMEGA-PSA-EXEC-v3.1-20260520 |
| **Estado** | **APROVADO — EXECUÇÃO IMEDIATA** (CEO 2026-05-20) |
| **Substitui** | v3.0 (suspenso), Desktop disperso |
| **Veredito** | `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` |
| **Branch** | `fix/cicc-remediation-magic-mutex-20260520` |
| **Prazo** | 2026-05-21 12:00 UTC |

> **Anexo AIC:** Secção 12 — auditoria do v3.1 e plano **madrugada 24/7**.

---

## 0. Regra de ouro

1. Commit **único** atómico: magic + mutex + logs + `cio_boot_verify` + módulos.  
2. **Zero** posições Magic=0 no MT5 antes do restart.  
3. **Não** repetir sessão 20/05 (32 ativos, fallback ON, 0,5% risco).  
4. Aceite = **magic 234001 + logs + CIO-VERIFY** (PnL não obrigatório).

---

## 1. Veredito resumido (inalterado)

| Componente | Status |
|------------|--------|
| IA / imports BAU | EXONERADO |
| Gates RCV (Spread, SL/TP) | EXONERADO |
| Magic no request | CONDENADO → **corrigir agora** |
| Mutex global | CONDENADO → **corrigir agora** |

---

## 2. Overrides CKO (v3.1)

| Ponto CIO | Decisão v3.1 |
|-----------|--------------|
| `cio_boot_verify` sem `mt5_module` | ✅ Aceite |
| PowerShell Task Manager automático | ❌ Manual apenas |
| Canário no código | ❌ Script externo; exposição diag. ~USD 7,50/posição |
| Script validação auto P2 | Adiar |

---

## 3. Fase 0 — OPS (CEO) — 15–20 min

| # | Acção | PASS |
|---|--------|------|
| 0.1 | `Ctrl+C` no runner actual | Log parou de crescer |
| 0.2 | Task Manager → Command Line → só 0 ou 1 `omega_paper_loop` | OK |
| 0.3 | MT5: fechar **todas** posições Magic=0 / sem `OV2\|` | Screenshot |
| 0.4 | Guardar screenshot em `audit/forensic/post_patch_20260520/MT5_ZERO_ORFAS.png` | Ficheiro existe |
| 0.5 | **Âncora kill-switch (crítico para madrugada)** — ver Secção 8 | Ver abaixo |

---

## 4. Fase 1 — Engenharia PSA (código)

### 4.1 Ficheiros (estado após implementação AIC 2026-05-20)

| Ficheiro | Acção |
|----------|--------|
| `modules/omega_system_mutex.py` | **CRIADO** |
| `modules/cio_boot_verify.py` | **CRIADO** (sem `mt5_module`) |
| `core_engines/shadow_loop.py` | `magic` no request; `log.warning` gates; mutex+CIO no `run_loop` |
| `scripts/omega_paper_loop_24x7.py` | `OMEGA_DIAGNOSTIC_MODE` relaxa portfolio gate |
| `scripts/run_omega_diagnostico_post_cicc.ps1` | **CRIADO** |

### 4.2 Magic — linha exacta

Em `mt5_send_order`, dict `request`:

```python
"magic": int(os.getenv("OMEGA_MAGIC_NUMBER", "234001")),
```

**Nota:** `comment` usa `build_v2_order_comment(tf, direction)` — não alterar.

### 4.3 Verificação pós-patch

```powershell
Select-String -Path "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\core_engines\shadow_loop.py" -Pattern '"magic"'
```

### 4.4 Commit atómico

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout -b fix/cicc-remediation-magic-mutex-20260520
git add modules/omega_system_mutex.py modules/cio_boot_verify.py core_engines/shadow_loop.py scripts/omega_paper_loop_24x7.py scripts/run_omega_diagnostico_post_cicc.ps1 governance/
git commit -m "fix(core): CICC P0 — global mutex, magic on MT5 request, gate logs, CIO verify"
git push -u origin fix/cicc-remediation-magic-mutex-20260520
```

---

## 5. Fase 2 — Restart modo diagnóstico (madrugada 24/7)

```powershell
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
.\scripts\run_omega_diagnostico_post_cicc.ps1
```

**Parâmetros activos:**

| Env | Valor |
|-----|--------|
| OMEGA_DISABLE_MOMENTUM_FALLBACK | 1 (OFF) |
| OMEGA_RISK_PER_TRADE | 0.002 |
| OMEGA_DD_DAILY_MAX | 0.05 |
| OMEGA_MAX_POSITIONS | 3 |
| OMEGA_MAGIC_NUMBER | 234001 |
| OMEGA_LOOP_INTERVAL_SEC | 30 |
| Ativos | EURUSD GBPUSD USDJPY XAUUSD BTCUSD |

**Monitorizar:**

```powershell
Get-Content "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log" -Wait -Tail 40
```

**Procurar no log:** `[CIO-VERIFY] PASS`, `legacy_magic`, `ORDER DONE`, **sem** `KILL_SWITCH` DD repetido.

---

## 6. Fase 3 — Validação P0-VAL (manhã)

```powershell
python scripts/psa_export_mt5_tier0.py --days 1 --output audit/forensic/post_patch_20260520
```

Preencher `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md`.

**PASS:** 0% deals novas com magic=0; 100% magic=234001.

---

## 7. Checklist PSA ☑

### Bloqueantes

- [ ] 0.3 MT5 órfãs fechadas  
- [ ] 0.5 Âncora KS (Secção 8)  
- [ ] Commit push + PR  
- [ ] Boot com `[CIO-VERIFY] PASS`  
- [ ] Primeira ordem com magic=234001 no MT5  
- [ ] P0-VAL export  

### Madrugada

- [ ] Runner diagnóstico activo ≥ 6h sem HALT DD em loop  

---

## 8. Âncora kill-switch — obrigatório para operar à noite

**Problema:** `ks_daily_anchor.json` tem `anchor_equity: 1250.80` e saldo ~1094 → **HALT imediato** em cada ciclo.

**Solução CEO (escolher uma):**

**A — Novo dia calendário (automático)**  
Se já for **2026-05-21** local, o sistema recria âncora no primeiro boot.

**B — Reset manual para diagnóstico (mesmo dia):**

```powershell
Copy-Item "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\risk\ks_daily_anchor.json" "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\risk\ks_daily_anchor_BACKUP_$(Get-Date -Format yyyyMMdd_HHmm).json"
Remove-Item "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\risk\ks_daily_anchor.json" -ErrorAction SilentlyContinue
```

No **primeiro** ciclo pós-restart, a âncora será o **equity actual** MT5 (~1094). DD diário recomeça em 0%.

**C — Não operar** até novo dia sem reset (runner ficará em HALT loop).

---

## 9. GitHub / DOC-OFC

- PR com este documento + veredito v1.1 + evidências `post_patch_20260520/`  
- Actualizar Secção 13 do `DOC-OFC-REGISTO-PSA-...md` (v1.3 → v1.4 com v3.1 EXECUTANDO)

---

## 10. Não autorizado

- 32 ativos + fallback ON (sessão 20/05)  
- Restart sem fechar órfãs  
- Dois commits separados só magic / só mutex  

---

## 11. Mensagem PSA

v3.1 é o contrato único. Código base já contém módulos mutex/CIO e patch magic (validar com grep). PSA: Fase 0 CEO → commit → `run_omega_diagnostico_post_cicc.ps1` → relatório manhã.

**Assinaturas:** CKO + CIO + CEO autorização execução imediata.

---

## 12. Anexo AIC — Auditoria v3.1 e decisão madrugada

### 12.1 Avaliação do documento Desktop v3.1

| Critério | Resultado |
|----------|-----------|
| Alinhamento forense (magic, mutex) | ✅ Correto |
| Overrides CKO | ✅ Razoáveis |
| Exemplo `request` no texto | ⚠️ Simplificado; código real usa `build_v2_order_comment(tf, direction)` |
| Script diagnóstico "já existe" | ❌ **Era falso** — **criado** `scripts/run_omega_diagnostico_post_cicc.ps1` |
| Portfolio 3 pares só | ⚠️ Runner bloqueava sem XAU/BTC — **corrigido** `OMEGA_DIAGNOSTIC_MODE` |
| "Bloqueio trading até P0" vs madrugada CEO | ⚠️ Resolvido: P0 código aplicado; restart **após** 0.3+0.5 |

**Confiança técnica v3.1:** **Alta (92%)** para execução.

### 12.2 Operação madrugada — sequência recomendada

| Hora | Acção |
|------|--------|
| T+0 | CEO: Fase 0 (órfãs + âncora Secção 8) |
| T+15min | PSA: commit + push (se ainda não feito) |
| T+20min | `.\scripts\run_omega_diagnostico_post_cicc.ps1` em janela PowerShell dedicada |
| T+20min → manhã | Runner 24/7; ciclos ~30s; 5 símbolos; fallback OFF |
| Manhã | P0-VAL export + relatório PSA |

**Risco overnight:** mercado volátil; modo diagnóstico limita exposição. **Não** é garantia de lucro.

### 12.3 O que verificar ao acordar

1. Log: `[CIO-VERIFY] PASS` no arranque  
2. `ORDER DONE` com deals magic=234001 no MT5  
3. Ausência de loop `KILL_SWITCH DD diario 12%`  
4. `signal_source` preenchido nos novos fechos (melhor que NULL histórico)

---

*Fim v3.1 — DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md*
