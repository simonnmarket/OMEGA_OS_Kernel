# CEO — Decisão de Roteiro P0 (pós-alinhamento AIC ↔ PSA)

| Campo | Valor |
|-------|--------|
| **Documento** | CEO-ROTEIRO-P0-20260523 |
| **Data** | 2026-05-23 |
| **Contexto** | `AIC_PSA_RECONCILIACAO_ALINHAMENTO_20260523.md`, `CHECKLIST_EXECUCAO_20260523.md` |
| **Veredito** | **Alinhamento confirmado** — governança P0 encerrada; smoke CEO em curso |

---

## 1. Decisões executivas

| ID | Tema | Decisão CEO |
|----|------|-------------|
| **D1** | `partial_taken` no `_pos_ledger` (T-D5) | **Opção A** — T-D5 **PASS funcional** (UT-6 + engine). Flag no ledger = **primeira tarefa não-bloqueante da Fase 1** (Patch ATR). Sem ajuste de escopo P0. |
| **D2** | T-W2 (schedule por ciclo) | **Opcional** — T-W3 resolve bloqueio crítico de fim-de-semana. Não reescrever loop antes do smoke. Risco aceite se runner 24×7 não for reiniciado no FDS. |
| **Roteiro** | Fases 1–3 Router / ATR | **Proibidas** até veredito CEO pós-smoke + validação AIC (`AIC_VALIDACAO_PSA_P0_ABC_20260523.md`) |

---

## 2. Mensagem oficial (CEO → AIC + PSA)

```
AIC e PSA,

Revisão do alinhamento concluída. Excelente trabalho na checagem cruzada.

Decisões de Roteiro:

    D1 (partial_taken): Aceito a Opção A. T-D5 está PASS funcionalmente. A implementação
    da flag no _pos_ledger será incorporada como primeira tarefa não-bloqueante no início
    da Fase 1 (Patch ATR). Não precisamos de ajuste de escopo agora.

    T-W2: Mantido como opcional/recomendado. O T-W3 resolveu o bloqueio crítico do
    fim de semana.

Veredito de Roteiro: Alinhamento Confirmado.

Estou iniciando o Smoke Test MT5 (Seções 4, 5 e 6 do relatório PSA) agora. O próximo
contato de vocês comigo deve ser apenas para ler o relatório preenchido.

Lembrete: Fases 1, 2 e 3 permanecem estritamente proibidas até o meu veredito
pós-smoke e a validação final da AIC.
```

---

## 3. Próximas ações por papel

| Papel | Acção | Quando |
|-------|--------|--------|
| **CEO** | Smoke SM-1..7, P2a; reconcile; preencher `PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` Sec. 4–7 | Agora |
| **AIC** | Ler relatório preenchido; emitir `AIC_VALIDACAO_PSA_P0_ABC_20260523.md`; actualizar inventário ABC | Após CEO colar evidências |
| **PSA** | Aguardar; commit final / inventário se CEO pedir; **não** iniciar Fase 1 até AIC APROVADO | Pós-smoke |

---

## 4. Referência smoke (mandato Sec. 5.3)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:PYTHONIOENCODING = "utf-8"

python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD GBPJPY XAUUSD --timeframes H1 --equity 10000
python scripts/psa_position_pnl_reconcile.py --since "2026-05-23 00:00:00"
```

**Relatório a preencher:** `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md`

---

*Registo CEO — cópia Desktop Auditoria sincronizada com governance.*
