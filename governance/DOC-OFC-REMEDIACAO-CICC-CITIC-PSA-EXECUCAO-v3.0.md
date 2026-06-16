# OMEGA — Remediação CICC/CITIC — Ordem de Execução PSA v3.0

> **STATUS:** **SUBSTITUÍDO por v3.1** — usar `DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.1.md` (CEO aprovou execução imediata 2026-05-20).

| Campo | Valor |
|-------|--------|
| **ID** | DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-v3.0 |
| **Estado** | **PENDENTE RE-AUDITORIA CEO / CONSELHO** |
| **Substitui** | Remediação v2.0 Desktop; veredito disperso; instruções fragmentadas |
| **Documento contrato** | `DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` (mesma pasta `governance/`) |
| **Data** | 2026-05-20 |
| **Destinatário** | PSA — execução **suspensa** até nova deliberação |
| **Aprovação** | CKO + CIO (arquivo) — **aguarda confirmação CEO pós re-auditoria** |
| **Classificação** | CRÍTICO — trading bloqueado até P0 completo **e** CEO autorizar v3.0 |
| **Prazo PSA** | **Indefinido** — retoma após decisão CEO |
| **Branch Git** | `fix/cicc-remediation-magic-mutex-20260520` (criar a partir de `main` ou branch RCV activa) |
| **Repositório** | `https://github.com/simonnmarket/OMEGA_OS_Kernel` |

---

## 0. Regra de ouro (ler primeiro)

1. **Um único commit atómico** com magic + mutex + logs + módulo mutex + boot CIO-VERIFY.  
2. **Zero posições Magic=0 no MT5** antes de qualquer `run_omega_24x7.ps1`.  
3. **Não** repetir sessão 20/05 (32 ativos, fallback ON, risco 0,5%).  
4. **PnL positivo não é critério de aceite** — critério é **magic 234001 + rastreio + logs**.

---

## 1. Mapa de documentos oficiais (onde guardar)

### 1.1 Sistema OMEGA (`C:\OMEGA_QUANTUM_LAB\SOURCE_CODE`)

| Prioridade | Ficheiro canónico | Caminho no repo |
|------------|-------------------|-----------------|
| **P0 — Lei** | Este documento (execução PSA) | `governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.0.md` |
| **P0 — Contrato** | Veredito Conselho v1.1 | `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` |
| **P0 — Registo** | Actualização DOC-OFC PSA | `governance/DOC-OFC-REGISTO-PSA-MUDANCAS-OPERACIONAIS-E-GOVERNANCA-20260518.md` Secção 13 |
| **P1 — Aprovações** | CKO + CIO | `docs/conselho_arquivo/aprovado_conselho_20260520/` |
| **P1 — Forense** | Resposta PSA + Provas de Fogo | `docs/conselho_arquivo/forensic_20260520/` |
| **P1 — Evidência runtime** | Pacote ZIP forense | `audit/forensic/OMEGA_FORENSIC_AUDIT_20260520/` (já existe) |
| **P2 — RCV P0** | Mandatos CKO | `docs/conselho_arquivo/OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX.md` |
| **P2 — Runbook** | CEO manual | `docs/conselho_arquivo/CEO_MANUAL_INICIO_OPERACOES.md` |

### 1.2 GitHub (obrigatório no mesmo PR)

- Todos os ficheiros da tabela acima incluídos no commit/PR.  
- `governance/MANIFESTO_DOCUMENTOS.json` — entrada nova (Secção 12 deste doc).  
- Evidência pós-patch: `audit/forensic/post_patch_20260520/` (criar com export Tier-0).  
- Relatório PSA: `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md` (template Secção 10).

### 1.3 Desktop CEO — apenas índice (não duplicar lei)

Após migração, a pasta Desktop mantém **só**:

- `Pendente/Auditoria/00_INDICE_CANONICO_REPO.md`  
- `Pendente/Auditoria/Aprovado/00_INDICE_APROVACOES_REPO.md`  

Todos os `.txt` / `.md` operacionais foram **arquivados no repo**; cópias duplicadas **removidas** do Desktop (2026-05-20).

---

## 2. Cláusulas CIO (obrigatórias — integradas)

| Cláusula | Exigência | Implementação PSA |
|----------|-----------|-------------------|
| **C1 — Firebreak** | Scripts legacy **fora** de `SOURCE_CODE` | Mover `inativo/` → `C:\OMEGA_QUANTUM_LAB\INATIVO_ARQUIVADO_20260520\` |
| **C2 — Canário** | Exposição ≤ USD 10.000 (48h) | Script verificação + log `[CIO-CANARY] exposure_usd=...` |
| **C3 — Auto-verify boot** | Abortar se magic ausente no dict teste | Função `cio_verify_boot()` — Secção 6 |
| **C4 — Hash patch** | `[FORENSIC] CODE_SHA3` = commit do PR | Já existe; validar após merge |

---

## 3. Fase 0 — OPS (CEO) — antes da Engenharia

| Passo | Acção | Comando / local | Critério PASS |
|-------|-------|-----------------|--------------|
| 0.1 | Parar runner | Ctrl+C na janela `run_omega_24x7.ps1` | Nenhum ciclo novo no log |
| 0.2 | Task Manager → Detalhes → Command Line | Filtrar `python3.11.exe` | Só `omega_paper_loop_24x7` / `shadow_loop` ou zero |
| 0.3 | MT5 → Positions | Fechar Magic=0 e comment sem `OV2\|` | Screenshot 0 órfãs |
| 0.4 | Guardar evidência | Screenshot → `audit/forensic/post_patch_20260520/MT5_POSICOES_ZERO_ORFAS.png` | Ficheiro existe |

**Bloqueante:** PSA **não** faz commit de código antes de 0.3 PASS (confirmar com CEO por escrito/chat).

---

## 4. Fase 1 — Engenharia (alta performance)

### 4.1 Criar módulo partilhado (evitar path errado)

**Novo ficheiro:** `modules/omega_system_mutex.py`

```python
"""Mutex global OMEGA — CICC remediation 20260520."""
from __future__ import annotations
import atexit
import os
from pathlib import Path

_OMEGA_ROOT = Path(os.getenv("OMEGA_ROOT", r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"))
GLOBAL_LOCK_PATH = _OMEGA_ROOT / "audit" / ".omega_system.lock"
_acquired = False

def acquire_global_mutex() -> bool:
    global _acquired
    try:
        GLOBAL_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(GLOBAL_LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        _acquired = True
        atexit.register(release_global_mutex)
        return True
    except FileExistsError:
        return False

def release_global_mutex() -> None:
    global _acquired
    if GLOBAL_LOCK_PATH.exists() and _acquired:
        try:
            GLOBAL_LOCK_PATH.unlink()
        except OSError:
            pass
    _acquired = False
```

**Performance:** um módulo, três entry points — sem copiar função em 3 ficheiros.

---

### 4.2 P0-ENG-1 — Magic Number

**Ficheiro:** `core_engines/shadow_loop.py` — `mt5_send_order`, dict `request` após `"comment"`:

```python
"magic": int(os.getenv("OMEGA_MAGIC_NUMBER", "234001")),
```

**Preventivo:** `main.py` → `execute_mt5_order` (mesma linha) se ficheiro permanecer.

**Verificação imediata:**

```powershell
Select-String -Path "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\core_engines\shadow_loop.py" -Pattern '"magic"' -Context 0,2
```

**PASS:** pelo menos 1 match dentro de `request = {`.

---

### 4.3 P0-ENG-2 — Mutex global

**Integrar em** (antes de `mt5.initialize()`):

1. `scripts/omega_paper_loop_24x7.py`  
2. `core_engines/shadow_loop.py` (se inicializa MT5 directamente)  
3. `main.py` — **remover** bloco `msvcrt` linhas ~24-29; substituir por:

```python
from modules.omega_system_mutex import acquire_global_mutex, release_global_mutex
if not acquire_global_mutex():
    sys.exit("FATAL: Outra instância OMEGA activa.")
```

**Teste PASS:**

```powershell
# Terminal A
Set-Location C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python -c "from modules.omega_system_mutex import acquire_global_mutex; print(acquire_global_mutex())"

# Terminal B (com A a correr)
python -c "from modules.omega_system_mutex import acquire_global_mutex; print(acquire_global_mutex())"
```

Esperado: A `True`, B `False`.

---

### 4.4 P0-ENG-3 — Logs gates

No caller de `pre_execution_safety_check()`:

```python
if not ok:
    log.warning("[%s %s] %s — %s", asset, tf, gate_status, gate_msg)
```

**PASS:**

```powershell
Select-String -Path "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log" -Pattern "SKIP_SPREAD_GUARD" | Select-Object -Last 3
```

(após ciclo de teste ou mock Prova 2-A)

---

### 4.5 P0-ENG-4 — Boot CIO-VERIFY (Cláusula C3)

**Novo ficheiro:** `modules/cio_boot_verify.py` ou bloco no arranque de `omega_paper_loop_24x7.py`:

```python
def cio_boot_verify(mt5_module, logger) -> bool:
    magic = int(os.getenv("OMEGA_MAGIC_NUMBER", "234001"))
    lock = os.getenv("OMEGA_ROOT", r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE") + r"\audit\.omega_system.lock"
    logger.info("[CIO-VERIFY] MAGIC_ENABLED = %s", magic)
    logger.info("[CIO-VERIFY] MUTEX_GLOBAL = %s", lock)
    # Dict seco — sem order_send
    test = {"symbol": "EURUSD", "magic": magic, "comment": "OV2|VERIFY|BOOT|H"}
    if test.get("magic") != magic:
        logger.critical("[CIO-VERIFY] FAIL — magic ausente no dict teste")
        return False
    logger.info("[CIO-VERIFY] PASS — dict contém magic=%s", magic)
    return True
```

Chamar **antes** do primeiro ciclo de trading; se `False` → `sys.exit(1)`.

---

### 4.6 P1-ISO — Firebreak (Cláusula C1)

```powershell
$src = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\inativo"
$dst = "C:\OMEGA_QUANTUM_LAB\INATIVO_ARQUIVADO_20260520"
New-Item -ItemType Directory -Force -Path $dst
if (Test-Path $src) { Move-Item -Path $src -Destination $dst -Force }
# Mover também scripts ghost da raiz:
@("omega_turing_live.py","live_drone_v5.py","omega_v550_realtime_mt5.py","omega_v550_realtime_mt5_v550.py") | ForEach-Object {
  $p = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\$_"
  if (Test-Path $p) { Move-Item $p $dst -Force }
}
Move-Item "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\core_engines\shadow_loop_v2.py" $dst -ErrorAction SilentlyContinue
```

---

### 4.7 P1-MAIN — main.py preventivo

Se `main.py` permanecer no repo:

```python
if __name__ == "__main__":
    if "--mode" not in sys.argv or "live" not in sys.argv:
        print("ERRO: main.py requer --mode live. Use scripts/run_omega_24x7.ps1")
        sys.exit(1)
```

---

### 4.8 Commit atómico (Adendo CKO C)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout -b fix/cicc-remediation-magic-mutex-20260520
git add modules/omega_system_mutex.py modules/cio_boot_verify.py core_engines/shadow_loop.py scripts/omega_paper_loop_24x7.py main.py governance/ docs/conselho_arquivo/
git commit -m "fix(core): CICC P0 — global mutex, magic on MT5 request, gate logs, CIO boot verify"
```

**Proibido:** dois commits separados só magic / só mutex neste ciclo.

---

## 5. Fase 2 — Script diagnóstico (obrigatório)

**Criar:** `scripts/run_omega_diagnostico_post_cicc.ps1`

```powershell
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_ROOT = (Get-Location).Path
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "1"
$env:OMEGA_RISK_PER_TRADE = "0.002"
$env:OMEGA_DD_DAILY_MAX = "0.05"
$env:OMEGA_MAX_POSITIONS = "3"
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY"
$env:OMEGA_DECISION_TRACE = "1"
python -u scripts/omega_paper_loop_24x7.py --timeframes H1 M15
```

**Cláusula C2 — Canário:** em `shadow_loop` ou script auxiliar, calcular soma `volume * contract_size * price` das posições OMEGA magic 234001; se > 10000 USD → log `[CIO-CANARY] HALT exposure=...` e não abrir novas.

---

## 6. Fase 3 — Validação (P0-VAL)

```powershell
Set-Location C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
python scripts/psa_export_mt5_tier0.py --days 1 --output audit/forensic/post_patch_20260520
```

**PASS:** CSV/relatório com **0** deals novas `magic=0`; **100%** magic `234001` (ou 999111–999130 se scale).

**Registar** em `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md`:

- Hash commit + linha `[FORENSIC] CODE_SHA3` do log  
- Contagem magic  
- Screenshot MT5  
- Resultado teste mutex  
- Confirmação CEO P0-OPS  

---

## 7. Checklist único PSA (marcar ☑)

### Bloqueantes

- [ ] P0-OPS: MT5 sem Magic=0  
- [ ] P0-ENG-1: magic no request  
- [ ] P0-ENG-2: mutex módulo + 3 entry points  
- [ ] P0-ENG-3: SKIP_* no runner.log  
- [ ] P0-ENG-4: CIO-VERIFY no boot  
- [ ] P1-ISO: Firebreak `INATIVO_ARQUIVADO_20260520`  
- [ ] Commit atómico + push branch  
- [ ] P0-VAL: export Tier-0 PASS  
- [ ] PR GitHub aberto + link no DOC-OFC Secção 13  
- [ ] Modo diagnóstico 48h (script Secção 5)  

### Não autorizado

- [ ] 32 ativos + fallback ON (sessão 20/05)  
- [ ] Restart sem relatório PSA Secção 10  

---

## 8. GitHub — procedimento PSA

1. Branch: `fix/cicc-remediation-magic-mutex-20260520`  
2. PR título: `fix(core): CICC/CITIC P0 — magic payload + global mutex + CIO verify`  
3. Corpo PR: link este doc + veredito v1.1 + checklist Secção 7 ☑  
4. Anexar: output `post_patch_20260520/`  
5. Pedir review CEO; **não merge** sem P0-VAL PASS  
6. Após merge: tag opcional `cicc-remediation-20260520`

**Actualizar** `governance/DOC-OFC-REGISTO-PSA-MUDANCAS-OPERACIONAIS-E-GOVERNANCA-20260518.md` Secção 13 (modelo abaixo).

---

## 9. Secção 13 — texto para DOC-OFC (copiar)

```markdown
## 13. Remediação CICC/CITIC (2026-05-20)

| Campo | Valor |
|-------|--------|
| ID | OMEGA-CICC-REMEDIATION-20260520 |
| Doc execução | governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.0.md |
| Veredito | governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md |
| Branch | fix/cicc-remediation-magic-mutex-20260520 |
| Commit | _(preencher após push)_ |
| PR | _(URL)_ |
| Estado | EM CURSO / VALIDADO |

Correcções: magic 234001 em mt5_send_order; mutex audit/.omega_system.lock; logs SKIP_*; CIO-VERIFY boot; firebreak inativo/.
```

---

## 10. Template relatório PSA

**Ficheiro:** `docs/requests/PSA_RELATORIO_VALIDACAO_CICC_20260520.md`

```markdown
# Relatório PSA — Validação CICC 20260520
- Data validação:
- Commit hash:
- CODE_SHA3 no boot:
- Deals 24h magic=0: (deve ser 0)
- Deals 24h magic=234001: (deve ser 100%)
- Mutex teste A/B: PASS/FAIL
- CIO-VERIFY boot: PASS/FAIL
- MT5 órfãs: PASS/FAIL (screenshot path)
- Canário 48h: exposure max USD
- Conclusão: APTO / NÃO APTO para modo diagnóstico
- Assinatura PSA:
```

---

## 11. Performance — padrão por correcção

| Correcção | Métrica de qualidade | Anti-padrão |
|-----------|---------------------|-------------|
| Magic | 100% deals novas etiquetadas | Magic só no log, não no request |
| Mutex | 1 processo MT5 | Dois locks coexistindo (msvcrt + O_EXCL) |
| Logs | SKIP_* grepável no runner.log | Só decision_trace |
| CIO-VERIFY | Boot aborta se dict sem magic | Continuar trading "à espera" |
| Firebreak | Zero scripts legacy na raiz | Só renomear, não mover fora SOURCE_CODE |
| Git | 1 commit P0 | PR só com docs sem código |

---

## 12. Entrada MANIFESTO_DOCUMENTOS.json

```json
{
  "id": "DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-v3.0",
  "path": "governance/DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.0.md",
  "tipo": "ordem_execucao_psa",
  "data": "2026-05-20",
  "bloqueia_trading": true
}
```

---

## 13. Referências cruzadas

| Documento | Localização repo |
|-----------|------------------|
| Veredito v1.1 | `governance/DOC-OFC-VEREDITO-CICC-20260520-FINAL-v1.1.md` |
| Aprovação CKO | `docs/conselho_arquivo/aprovado_conselho_20260520/REGISTO_APROVACAO_CKO_20260520.txt` |
| Aprovação CIO + cláusulas | `docs/conselho_arquivo/aprovado_conselho_20260520/VEREDITO_CIO_CICC_20260520.txt` |
| Resposta forense PSA | `docs/conselho_arquivo/forensic_20260520/RESPOSTA_PSA_FORENSIC_20260520.txt` |
| Provas de Fogo | `docs/conselho_arquivo/forensic_20260520/PSA_PROVAS_FOGO_20260520.txt` |
| Pacote evidência | `audit/forensic/OMEGA_FORENSIC_AUDIT_20260520/` |

---

*Fim — DOC-OFC-REMEDIACAO-CICC-CITIC-PSA-EXECUCAO-v3.0 — Documento único de execução para a PSA.*
