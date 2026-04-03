Documento oficial — Envio ao PSA (mandato de execução)

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-OFC-ENVIO-PSA-20260327` |
| **Versão** | 1.0 |
| **Tipo** | Instrução **oficial** ao executor **PSA** — sujeita a provas REQ/PRF e registo em `PSA_RUN_LOG.jsonl` |
| **Emitido por** | Núcleo de Validação OMEGA / Comando (cadeia de auditoria `DOC-AUD-CONCLUSAO-PROCESSO-20260403` v1.2) |
| **Destinatário** | **PSA** — único executor de alterações in-repo neste programa |
| **Data referência** | 2026-03-27 (emissão); estado de artefactos conforme auditoria até commit **`c3ea3be…`** |

---

## 1. Documentos normativos (obrigatoriamente em vigor)

O PSA deve seguir, nesta ordem de precedência em caso de dúvida:

| ID | Ficheiro (pasta base: `04_relatorios_tarefa/`) |
|----|-----------------------------------------------|
| MESTRE | `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` (`DOC-UNICO-PSA-MESTRE-20260403`) |
| PROVAS | `DOCUMENTO_OFICIAL_PSA_PROVAS_E_AUDITORIA.md` (`DOC-OFC-PSA-PROVAS-AUD-20260403`) |
| SOL/TAR/DEC | `DOCUMENTO_OFICIAL_MODELO_SOLICITACAO_APROVACAO_TAREFA.md` (`DOC-OFC-MODELO-TAR-20260403`) |
| AUDITORIA | `DOCUMENTO_UNICO_AUDITORIA_CONCLUSAO_E_FALHAS_PROCESSO.md` (`DOC-AUD-CONCLUSAO-PROCESSO-20260403` **v1.2**) |

**Regra:** nenhum “PASS” ou “concluído” sem **PRF** validada por `python psa_refutation_checklist.py --validate <ficheiro.json>` (exit 0) e linha correspondente na matriz, salvo **PENDENTE** explícito documentado (como KPI-06 no catálogo).

---

## 2. Estado do programa (snapshot para o PSA)

| Fase | Estado | Nota executiva |
|------|--------|----------------|
| **0**, **PH-FS-01** | CONCLUÍDO_COM_PROVA | Inventário + trilho em `PSA_RUN_LOG.jsonl` |
| **PH-FS-02** | **PARCIAL_COM_PROVA** | `CATALOGO_OHLCV_PLANO_v1.md` com §4 **KPI-06 PENDENTE**; PRF `prova_PRF-PHFS02-20260403-001.json` com `--validate` PASS (`REQ-UNICO-030`). **Não** fechar métrica até `KPI_REPORT_*.json`. |
| **PH-FS-03** | **NÃO_EXECUTADO** | Artefacto alvo: **`MAP-DEMO-TBL_v1.md`** (ainda ausente). |
| **PH-FS-04** | NÃO_EXECUTADO | Batch KPI / relatórios formais. |
| **Gate Tier-0** | **Atenção** | `PSA_GATE_CONSELHO_ULTIMO.txt` pode estar **desalinhado** do `git HEAD` actual; `verify_tier0` pode falhar por ficheiros em falta no manifesto — **reexecutar** gate após correcções e novo commit. |

---

## 3. Ordem de trabalho imediata (PSA)

1. **Emitir** solicitação e tarefa na malha oficial: **SOL-*** / **TAR-PHFS03-*** (identificadores únicos, coerentes com o modelo TAR).
2. **Produzir** `MAP-DEMO-TBL_v1.md` conforme roteiro FIN-SENSE (tabela de mapeamento demo, sem analytics dentro do módulo de dados além do especificado no MESTRE).
3. **Gerar PRF** nova (ex.: `prova_PRF-PHFS03-YYYYMMDD-001.json`) com `req_id` válido para o validador, `git_head` no momento do commit, e campos obrigatórios do schema.
4. **Executar** validação:  
   `python psa_refutation_checklist.py --validate templates_auditoria_psa/prova_PRF-PHFS03-….json` → **exit 0**.
5. **Actualizar** `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv`: nova linha com `req_id`, `proof_id`, `veredito_tarefa`, `dec_id` quando aplicável, `notas` objectivas.
6. **Registar** em `PSA_RUN_LOG.jsonl` pelo menos: `git rev-parse HEAD`, `file_saved` ou `phase_complete`, e **`audit_record`** ou **`head_reconciled_post_commit`** se houver reconciliação de HEAD.
7. **Opcional recomendado:** após estabilizar ficheiros, correr pipeline do gate e actualizar `PSA_GATE_CONSELHO_ULTIMO.txt` para refletir o HEAD corrente.

---

## 4. Proibições (anti-F1)

- Não substituir **prova** por **reconfirmação narrativa** de procedimentos.
- Não declarar PH-FS-02 **concluída em métrica** sem **`KPI_REPORT`** (KPI-06 permanece **PENDENTE** no plano até lá).
- Não avançar **PH-FS-04** antes de existir trilho PRF/matriz para **PH-FS-03**, salvo decisão explícita **DEC-*** documentada.

---

## 5. Fecho

Este documento constitui o **pacote oficial de envio ao PSA** para execução da próxima frente (**PH-FS-03**), em conformidade com **`DOC-AUD-CONCLUSAO-PROCESSO-20260403` v1.2**.  
Qualquer desvio deve ser registado como **PARCIAL** ou **PENDENTE** com **ID** e **artefacto** referenciado.

---

*Fim — `DOC-OFC-ENVIO-PSA-20260327` v1.0*
