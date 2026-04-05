# Documento Oficial — Ordem de encerramento definitivo: homologação PSA (ciclo FIN-SENSE)

| Campo | Valor |
|--------|--------|
| **ID completo** | `DOC-OFC-ORDEM-ENCERRAMENTO-DEFINITIVO-PSA-HOMOLOGACAO-FINSENSE-20260331-009` |
| **Referência curta** | `DOC-OFC-009` |
| **Versão** | **1.0 DEFINITIVA** |
| **Data de emissão** | 31 de março de 2026 |
| **Classificação** | **Ordem executável final** — sem passos intermédios adicionais após publicação |
| **Efeito jurídico-institucional** | Ao ser **integralmente executada** pelo PSA, **encerra** o **gap de governança** referido no **DOC-006** e formaliza a **homologação** do ciclo FIN-SENSE ao nível **DOC-005 / README**, sem reabrir **DOC-001–007** (salvo ordem CEO). |
| **Repositório** | `OMEGA_OS_Kernel` — `https://github.com/simonnmarket/OMEGA_OS_Kernel.git` |
| **Branch** | `main` |
| **Tag de arquivo** | `finsense-psa-cycle-20260404` |

---

## Autoridade e cadeia normativa (ordem de leitura)

| Prioridade | Documento | Função |
|------------|-----------|--------|
| 1 | `DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006` | Define **porquê** a rubrica é obrigatória. |
| 2 | `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` | **Onde** rubricar (secção 5). |
| 3 | `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` | **Como** actualizar README e commit único (Anexo A). |
| 4 | `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008` | Comandos **PowerShell** e checklist detalhado. |
| **5** | **Este documento (009)** | **Ordem única de encerramento** — consolidar intenção e responsabilidade PSA. |

**Este DOC-009 não substitui os anteriores:** integra-os num **único mandato de execução**.

---

## Mandato ao PSA (executar em sequência, sem omissões)

### M1 — Verificação mínima (Git + remoto)

- `git fetch origin && git checkout main && git pull origin main`
- Confirmar `origin` → `https://github.com/simonnmarket/OMEGA_OS_Kernel.git`
- Confirmar tag `finsense-psa-cycle-20260404` listável
- Confirmar `HEAD` alinhado com `origin/main`

*(Detalhe de comandos: **DOC-008**, Passo 1.)*

### M2 — Verificação física (caminhos canónicos)

Confirmar existência na raiz do repositório:

- `modules/FIN_SENSE_DATA_MODULE/`
- `FIN_SENSE_DATA/`
- `governance/`

*(Detalhe: **DOC-008**, Passo 2.)*

### M3 — Rubrica obrigatória

- Abrir `governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md`
- Preencher **secção 5** na **totalidade** (cinco confirmações **Sim**, nome/função, data, identificador interno se aplicável)
- Arquivar evidência institucional (acta / ticket / compliance) e obter **REF** para o README

### M4 — Índice mestre (uma substituição)

- Abrir `governance/README.md`
- Substituir **apenas** o bloco do **topo** que ainda indica **PENDENTE** / **Pronto para rubrica** pelo texto do **Anexo A** (abaixo), com placeholders preenchidos
- **Não** reescrever a tabela DOC-001–008 nem a secção Fase 2 salvo erro factual

### M5 — Publicação (commit único)

```text
git add governance/README.md governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md
git commit -m "governance: homologacao PSA concluida (DOC-005 sec.5); README estado final; ref DOC-007"
git push origin main
```

*Excepção:* se o DOC-005 preenchido **não** puder ser versionado, commitar só o `README` e declarar no commit: `rubrica arquivada em [REF]`.*

### M6 — Prova de conclusão

- `git log -1 --oneline`
- `git status` limpo em `main`
- Confirmar no GitHub web que `main` contém o commit e o README actualizado

---

## Anexo A — Texto para o `governance/README.md` (substitui o bloco PENDENTE)

```markdown
**Homologação PSA:** **CONCLUÍDA** em [DATA_AAAA-MM-DD] — rubrica em `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` secção 5. Responsável: [NOME_PSA]. Arquivo institucional: [REF_TICKET_OU_ACTA].

**Estado operacional:** **Homologado** ao nível institucional para o ciclo FIN-SENSE (governança + estrutura + Git). Gap de governança **fechado**.

**Transição:** ver secção "Fase 2" no `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` (DOC-007) para integração de alta performance (fora do âmbito da rubrica).
```

---

## Declaração de encerramento (preencher após M1–M6)

O PSA declara, sob a presente ordem **DOC-009**, que:

- [ ] Os mandatos **M1 a M6** foram **executados sem omissão**  
- [ ] A homologação institucional do ciclo FIN-SENSE está **formalmente concluída** nos termos do **DOC-006**  
- [ ] Não são necessários **outros documentos** para este encerramento no âmbito **DOC-001–007**  

**Nome / função PSA:** _____________________________________________  

**Data e hora (local):** ____ / ____ / ______  ___:___  

**Identificador de arquivo institucional (opcional):** _____________________________________________  

**Assinatura / carimbo digital (conforme política interna):** _____________________________________________  

---

## Limitação de âmbito (clareza institucional)

| Incluído neste encerramento | Excluído (outros contratos) |
|-----------------------------|-----------------------------|
| Governança + estrutura + Git + rubrica PSA + README | Implementação técnica **Fase 2** (ex.: `DOC-OFC-FASE2-FATIA1-…`) |
| Fecho do **gap** DOC-006 para este ciclo | PnL, produção MT5, ou métricas de trading — **fases futuras** |

---

## Fim do documento

**`DOC-OFC-ORDEM-ENCERRAMENTO-DEFINITIVO-PSA-HOMOLOGACAO-FINSENSE-20260331-009` — versão 1.0 DEFINITIVA — sem anexos obrigatórios além dos referidos na cadeia normativa.**
