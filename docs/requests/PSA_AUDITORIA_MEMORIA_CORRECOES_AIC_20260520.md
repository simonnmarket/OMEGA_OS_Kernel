# PSA — Auditoria de Memória — Correções AIC (CICC P0)

| Campo | Valor |
|-------|--------|
| **ID** | OMEGA-AIC-MEMORY-AUDIT-20260520 |
| **Para** | Principal Solution Architect (PSA) |
| **De** | AIC (sessão CEO) + registo para arquivo |
| **Data** | 2026-05-20 |
| **Branch** | `fix/cicc-remediation-magic-mutex-20260520` |
| **Commit PSA (base)** | `b71ee35` — *fix(core): CICC P0 — global mutex, magic on MT5 request, gate logs, CIO verify* |
| **Doc execução** | `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` |

---

## 0. Instrução PSA (obrigatório)

**Todas as alterações listadas neste documento devem ser auditadas, commitadas no GitHub e referenciadas na Secção 13 do DOC-OFC-REGISTO.**

Correções **após** `b71ee35` existem apenas no working tree local — **não estão no PR** até a PSA fazer commit de follow-up.

---

## 1. Commit `b71ee35` (já no branch — PSA/AIC sessão anterior)

| Ficheiro | Alteração | Motivo CICC |
|----------|-----------|-------------|
| `core_engines/shadow_loop.py` | `"magic": int(os.getenv("OMEGA_MAGIC_NUMBER","234001"))` no `request` MT5; logs gate; mutex + `cio_boot_verify` no `run_loop` | P0 — órfãs magic=0 |
| `modules/omega_system_mutex.py` | **NOVO** — lock global `audit/.omega_system.lock` | P0 — corrida main vs runner |
| `modules/cio_boot_verify.py` | **NOVO** — `[CIO-VERIFY]` sem `mt5_module` | Aceite CKO v3.1 |
| `scripts/omega_paper_loop_24x7.py` | `OMEGA_DIAGNOSTIC_MODE` relaxa gate portfolio | Modo diagnóstico |
| `scripts/run_omega_diagnostico_post_cicc.ps1` | **NOVO** — env diagnóstico (5 ativos, 0,2% risco, magic 234001) | CEO madrugada |
| `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` | **NOVO** — lei de execução | Canónico |
| `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` | **NOVO** | Conselho |
| `governance/DOC-OFC-REGISTO-PSA-...-20260518.md` | Secção 13 CICC | Registo |
| `audit/forensic/post_patch_20260520/.gitkeep` | Pasta evidências | P0-VAL |
| `docs/conselho_arquivo/aprovado_conselho_20260520/.gitkeep` | Pasta aprovações | Arquivo |

---

## 2. Correções AIC **pós-`b71ee35`** — PENDENTE COMMIT PSA

**Contexto:** Durante arranque CEO (23:25–23:29), runner falhava com `export terminou com código 1` em loop. Causa: `UnicodeEncodeError` no Windows (consola cp1252) ao imprimir `→` e travessões em scripts.

### 2.1 `scripts/export_ohlcv_mt5.py`

| Mudança | Detalhe |
|---------|---------|
| **FIX crítico** | Substituir `→` e `—` por `->` e `-` em todos os `print()` (linhas ~99, 126, 134, 155) |
| **Efeito** | Export passa de `rc=1` para `Exportados: 10 \| Falhas: 0` no modo diagnóstico |
| **Outras alterações no mesmo ficheiro** (já no working tree) | `--strict-exit`; exit parcial se `ok>0`; lista `ALL_SYMBOLS` alargada; TFs M5/M15/M30/D1; docstring uso Motor V3 |

**Evidência CEO (2026-05-20 23:29):**
```
Exportando 5 simbolos x 2 TFs | 12000 candles
Exportados: 10 | Pulados: 0 | Falhas: 0
ciclo 1 | shadow_loop…
```

### 2.2 `scripts/run_omega_diagnostico_post_cicc.ps1`

| Mudança | Detalhe |
|---------|---------|
| **FIX crítico** | Remover caracteres Unicode no `Write-Host` (em-dash `—` → `-`) |
| **Efeito** | Script executável no PowerShell Windows sem `TerminatorExpectedAtEndOfString` |

---

## 3. Acções CEO (não são código — registo operacional)

| Acção | Data/hora | Estado |
|-------|-----------|--------|
| MT5 — fechar posições magic=0 / sem `OV2\|` | ~23:20 | Feito (0 positions sync) |
| Apagar `audit/risk/ks_daily_anchor.json` | ~23:25 | Feito — backup em `ks_daily_anchor_BACKUP_20260520.json` |
| Arranque `run_omega_diagnostico_post_cicc.ps1` | 23:28:57 | OK — 5 ativos, export 10/10, shadow_loop ciclo 1 |
| Reinício runner após fix export | 23:28+ | PID novo (singleton) |

**Nota:** Apagar âncora KS **não** está no git — só evidência em `audit/risk/` (backup JSON).

---

## 4. O que a PSA deve fazer agora

1. **Rever diff local:**
   ```powershell
   cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
   git diff b71ee35 -- scripts/export_ohlcv_mt5.py scripts/run_omega_diagnostico_post_cicc.ps1
   ```
2. **Commit follow-up** (sugestão de mensagem):
   ```
   fix(scripts): Windows cp1252 — ASCII em export OHLCV e runner diagnostico CICC
   ```
3. **Push** para `fix/cicc-remediation-magic-mutex-20260520` e **atualizar PR**.
4. **Atualizar** `governance/DOC-OFC-REGISTO-PSA-...-20260518.md` — sub-entrada v1.3.1:
   - Data 2026-05-20 noite
   - Ficheiros: `export_ohlcv_mt5.py`, `run_omega_diagnostico_post_cicc.ps1`
   - Ref: este documento
5. **Manhã:** P0-VAL em `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md`

---

## 5. Checklist auditoria de memória PSA

- [ ] Commit `b71ee35` revisto (magic, mutex, CIO, docs)
- [ ] Commit follow-up AIC (export + ps1 encoding) incluído no PR
- [ ] Secção 13 DOC-OFC actualizada
- [ ] Nenhuma correção AIC apenas “oral” — tudo no GitHub
- [ ] P0-VAL preenchido após noite diagnóstico
- [ ] PR merge **apenas** se magic 234001 = 100%

---

## 6. Ficheiros que **não** são correção CICC AIC (ignorar neste pacote)

O working tree tem centenas de alterações em `audit/paper/`, agentes, backups — **runtime/ruído**. Para este pacote CICC, commitar **apenas**:

- `scripts/export_ohlcv_mt5.py`
- `scripts/run_omega_diagnostico_post_cicc.ps1`

(opcional: este ficheiro de auditoria de memória)

---

**Assinatura AIC:** registo gerado 2026-05-20 para arquivo PSA.  
**CEO:** encaminhar este ficheiro à PSA com o pedido de commit follow-up antes do merge.
