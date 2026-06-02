# ENT-05 — POSIÇÕES LEGADAS & P-04
**ID:** `OMEGA-PSA-AUDIT-CLOSE-20260602 / ENT-05`  
**Título:** Estado das posições legacy (não-OMEGA) e pendências P-03/P-04  
**Referência:** PSA_MEMORIA_INTERNA §12 | `audit/forensic/FORCE_NOW_20260601/tickets_to_close.json`

---

## 1. POSIÇÕES LEGACY IDENTIFICADAS (MT5 — sem mark OMEGA)

Estas posições são **visíveis no MT5** mas **não geridas pelo runner OMEGA** (sem comment OMEGA → não aparecem no `MT5 State Sync` do runner). Abertas em sessões anteriores à janela CKO v2.

| Ticket | Ativo | Pendência | Estado |
|--------|-------|-----------|--------|
| #192653640 | EURUSD | — | Aberto — sem gestão OMEGA |
| #192470725 | UKOIL+ | **P-03** | Aberto — fechar na abertura de mercado (aguarda CEO) |
| #192253913 | US500 | **P-04** | Aberto — Fase 2 fecho legacy (aguarda CEO APROVADO) |

> **Nota P-03:** UKOIL+ #192470725 era #191908751 em sessões anteriores — ticket actualizado. Fecho aguarda ordem CEO explícita (conforme mandato CKO v2 §6).

---

## 2. IMPACTO DAS POSIÇÕES LEGACY NA EQUITY

O runner OMEGA não tem visibilidade directa sobre o PnL das posições legacy. No entanto:

- A equity do MT5 reflecte **todas** as posições abertas (OMEGA + legacy)
- O KS do runner usa a equity total para calcular DD
- Às 07:48 UTC: `equity=$10,610` com `DD=1.21%` — inclui float de posições legacy

**Risco activo das posições legacy:**
- Sem SL gerido pelo OMEGA runner → exposição não controlada
- Sem trailing stop automático → maior risco de erosão em tendências adversas
- Recomendação: fechar conforme P-04 assim que CEO autorizar

---

## 3. PENDÊNCIAS FORMAIS PSA §12

| ID | Item | Estado Actual | Próximo Passo |
|----|------|---------------|---------------|
| P-03 | Fechar UKOIL+ #192470725 | **PENDENTE** — aguarda CEO | CEO emite ordem → fechar na abertura do mercado |
| P-04 | Fase 2 fecho legacy completo | **PENDENTE** — aguarda CEO APROVADO | CEO aprova → executar `tickets_to_close.json` |
| P-05 | SEL-1 report RP>0.75 vs MT5 | Dias 9-12 CKO | AIC compila quando solicitado |
| P-07 | OMEGA_RUPTURE_CAPTURE=1 | Aguarda dia 13+ CKO | CEO/CKO decisão |

---

## 4. FICHEIRO DE FECHO PREPARADO

O ficheiro `audit/forensic/FORCE_NOW_20260601/tickets_to_close.json` contém a lista de tickets para fecho da Fase 2. Aguarda aprovação CEO para execução.

---

## 5. RECOMENDAÇÃO AIC

Enquanto P-03 e P-04 não forem aprovados:
- **Monitorizar equity DD** — se posições legacy deteriorarem significativamente, o DD do KS pode aproximar-se do threshold
- **Não alterar** env/código/TF — mandato CEO activo
- **Registar** qualquer mudança de equity >2% para relatório intercalar

---

*Fonte: `audit/paper/omega_24x7_runner.log`, `governance/PSA_MEMORIA_INTERNA_COMPLETA_20260601.md`, `audit/forensic/FORCE_NOW_20260601/tickets_to_close.json`*  
*Gerado: 2026-06-02 19:10 UTC*
