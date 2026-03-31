Handoff PSA — Instruções finais (pós-análise `Auditoria Conselho/`)

**Para:** PSA (execução operacional MACE-MAX / Antigravity)  
**De:** consolidação técnica + memorandos em `Auditoria PARR-F/Auditoria Conselho/`  
**Data:** 1 de abril de 2026  
**Estado:** encerramento do dia — retoma amanhã

---

## 1. Direccionamento correcto da tarefa

A **autoridade operacional** para o PSA **não** é a pasta `Auditoria Conselho/` sozinha: esses ficheiros são **pareceres e histórico**. A **fonte única executável** continua a ser:

`Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md`

(IDs lógicos: `PARAM-PSA-FECHAMENTO-FASE-FINAL` v3.0 + `PARAM-PSA-CONSELHO-20260331-v2`, conteúdo unificado.)

**Regra:** Conselho (CKO/COO/CQO/CIO) **orienta**; **scripts + manifesto + `git rev-parse HEAD`** **decidem** números, SHA e PASS/FAIL.

---

## 2. Análise completa dos documentos em `Auditoria Conselho/`

| Ficheiro | Papel | Valor para o PSA | Risco / nota |
|----------|--------|------------------|--------------|
| **CKO — Red Team.txt** | REDAUD: honestidade sobre o que não foi lido no código | **Alta:** GAP1 (warm-up &lt; 20k barras), GAP2 (lógica de saída), GAP3 (`--smoke`). Ordem: correr `--smoke`, não esconder tracebacks, reportar WARNING de histórico. | Não contradiz o Tier-0; reforça **prudência**. |
| **COO — Chief Operating Officer.txt** | GO demo, sequência PowerShell, tese P95 vs threshold | **Média:** alinhado ao livrete em **comandos** (`--smoke`, `--bars`, gate). | **HEAD `bfbcb217...` está desactualizado** — não usar como verdade; ver secção 4. |
| **CQO — Chief Quant Officer.txt** | Validação quant, KPIs Fase E, 30 dias, checklist longo | **Média:** parâmetros (222 sinais, P95/P99, threshold por barra) coerentes com o repositório **se** revalidados por `audit_trade_count.py`. | **Mesmo HEAD fixo `bfbcb217...` obsoleto.** No final do ficheiro há texto espúrio (`How can I help you today?`) — **ignorar**; não faz parte do parecer. |
| **CIO — Chief Information Officer.txt** | Suposto CIO | **Baixa operacional:** conteúdo **duplicado** do COO (mesmo parecer). Tratar como **histórico** até existir CIO distinto. | Evitar dupla leitura; não há instrução CIO adicional. |

**Síntese:** O **CKO** é o único que explicita **REDAUD** (dúvida razoável): útil para **não** confundir stress/custódia com “perfeição” em demo. **COO/CQO** dão **luz verde narrativa**; **valores de Git** nos `.txt` **não** prevalecem sobre o repo actual.

---

## 3. O que o PSA deve executar (sequência mínima)

Ordem **idêntica** à Parte A/B do livrete (secções 5.1–5.4). Resumo:

1. **Raiz do repo + env**  
   `Set-Location` para `nebular-kuiper`, `$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path`

2. **HEAD actual**  
   `git rev-parse HEAD` — copiar para RT-E / arquivo da sessão.

3. **Gate**  
   `python ...\psa_gate_conselho_tier0.py --out-relatorio "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt"`  
   Exigido: `GATE_GLOBAL: PASS` e `verify_tier0_psa` **ESTADO OK** (se FAIL, `psa_sync_manifest_from_disk.py` e alinhamento conforme `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md`).

4. **Demo MT5**  
   `python ...\11_live_demo_cycle_1.py --smoke`  
   depois `python ...\11_live_demo_cycle_1.py --bars 500` (ou N acordado).

5. **Pós-demo**  
   `verificar_demo_apos_noturno.py --csv "<caminho completo DEMO_LOG_*.csv>"`

6. **GAP1 CKO**  
   Confirmar no stdout a linha de barras sincronizadas; se **N** muito inferior a 20 000, documentar no RT-E (não assumir paridade com stress).

**Nota:** usar `--out-relatorio` **relativo** à pasta `evidencia_pre_demo` (ex.: `04_relatorios_tarefa/...`) para não criar caminhos duplicados.

---

## 4. Divergências a corrigir mentalmente (memos vs repo)

| Tema | Nos `.txt` (COO/CQO) | Verdade operacional |
|------|----------------------|----------------------|
| **Git HEAD** | Citam `bfbcb21752f38667c4a4bd4b736f03bf109f2fe6` | **Sempre** o output **actual** de `git rev-parse HEAD` e o campo `git_commit_sha` do `MANIFEST_RUN_20260329.json` após `psa_sync_manifest_from_disk.py`. |
| **G5 / P95** | Corrigido nos textos para “threshold por barra” | Manter: P95 global ≈ 1,886 **não** invalida \|Z\| ≥ 2 **na barra**. |
| **Flags** | `--live` removido nos memos | Correcto: só `--smoke` e `--bars N`. |
| **CIO** | Ficheiro = cópia COO | Não procurar instrução CIO separada. |

---

## 5. O que fazer **hoje** vs **madrugada** vs **amanhã**

### 5.1 Ainda hoje (antes de encerrar — ~15–30 min)

- [ ] Abrir o **livrete único** e confirmar que está a versão em `PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md` (não só os `.txt` do Conselho).
- [ ] No repo: `git status` — se houver alterações pendentes em manifesto/gate, decidir **commit** ou **psa_sync** conforme `DOC_PSA_FINAL_*` (evitar deixar working tree incoerente se amanhã o primeiro passo for gate).
- [ ] **Opcional:** correr só **`psa_gate_conselho_tier0.py`** + `verify_tier0_psa.py` para **registar** `GATE_GLOBAL` e `HEAD` no relatório da sessão (sem MT5).
- [ ] Anotar no RT-E: “Handoff 20260401 — próximo passo: demo MT5 sec. 5.2 após gate PASS”.

### 5.2 Esta madrugada (só se fizer sentido)

| Actividade | Recomendação |
|------------|----------------|
| **Demo MT5** (`--smoke` / `--bars`) | Só se **terminal MT5**, **conta demo** e **máquina** estiverem **estáveis** e **supervisionados** ou **politicamente aceite** correr sem vigília. **Não** há como validar daqui o estado do teu PC/MT5. |
| **Jobs longos** (stress, hashes) | Se já estiverem validados no Tier-0, **não** é obrigatório repetir só por passar a noite. |
| **Backup** | Útil: copiar `PSA_GATE_CONSELHO_ULTIMO.txt` + output `git rev-parse HEAD` para pasta de arquivo (como o livrete pede). |

**Prudência CKO:** se correr demo, guardar **log completo** e qualquer **WARNING** de histórico.

### 5.3 Amanhã (primeira prioridade)

1. `git rev-parse HEAD` + `psa_gate_conselho_tier0.py` (mesmo que tenha corrido hoje, se houver novos commits).
2. `--smoke` → `--bars N`.
3. `verificar_demo_apos_noturno.py` no CSV gerado.
4. Actualizar RT-E e alinhar manifesto se ficheiros rastreados mudarem.

---

## 6. Limitações (para não sobre-prometer)

- **Tier-0 PASS** e stress **não** garantem PnL nem ausência de bugs de mercado ou de API MT5.
- Memorandos **humanos** podem ficar **desactualizados** (ex.: SHA); **prevalecem** o livrete e os scripts.

---

## 7. Arquivo sugerido para o PSA

Guardar **junto** numa pasta de custódia da sessão:

- Este ficheiro: `HANDOFF_PSA_INSTRUCOES_FINAIS_20260401.md`
- Último `PSA_GATE_CONSELHO_ULTIMO.txt`
- Output de `git rev-parse HEAD` da mesma sessão em que o gate foi PASS

---

**Fim do handoff — retoma operacional conforme secção 5.3.**
