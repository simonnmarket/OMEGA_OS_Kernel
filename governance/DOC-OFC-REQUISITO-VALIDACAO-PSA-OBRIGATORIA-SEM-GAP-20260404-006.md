# Documento Oficial — Requisito de Validação PSA (Eliminação de Gap de Governança)

| Campo | Valor |
|--------|--------|
| **ID** | `DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006` |
| **Versão** | 1.0 |
| **Data** | 4 de abril de 2026 |
| **Classificação** | **Crítico** — Risco de gap sistémico se não aplicado |
| **Destinatário** | Principal Solution Architect (PSA) |
| **Relaciona com** | `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` |

---

## 1. Declaração de importância

A **validação formal pelo PSA** não é um passo burocrático opcional: é **crucial** para o encerramento integral da etapa FIN-SENSE.

**Se o PSA não validar** (não preencher e arquivar a rubrica prevista no **DOC-005**, secção 5, ou equivalente aprovado internamente), o sistema de governança fica com um **GAP** — uma **lacuna auditável** entre:

- o que foi **executado** (código, dados, Git, documentos), e  
- o que foi **homologado por autoridade de arquitectura** (PSA).

Esse gap compromete:

- **Continuidade** perante auditoria externa ou due diligence;
- **Responsabilização** clara (quem assinou o encerramento?);
- **Confiança** de que não existem cópias não autorizadas ou caminhos divergentes.

---

## 2. O que constitui “validação PSA” (critério mínimo)

O PSA deve, no mínimo:

1. **Rever** localmente os caminhos canónicos indicados no DOC-005 (secção 2).
2. **Rever** no GitHub (`origin`) a branch `main`, a tag `finsense-psa-cycle-20260404` e o conteúdo sob `governance/`, `modules/FIN_SENSE_DATA_MODULE/`, `FIN_SENSE_DATA/`.
3. **Assinar** (processo interno) o quadro da secção 5 do DOC-005 — ou registar aprovação equivalente (ticket, acta, assinatura electrónica institucional).

Até estes pontos estarem **concluídos e arquivados**, o estado correcto a declarar é:

> **Encerramento técnico e documental executado; homologação PSA pendente.**

**Não** declarar “homologação completa” sem validação PSA.

---

## 3. Responsabilidade

| Papel | Responsabilidade |
|-------|------------------|
| **PSA** | Executar a validação e fechar o gap no prazo definido pelo Conselho / CEO. |
| **Engenharia** | Manter artefactos nos caminhos canónicos; não criar SSOT paralelo. |
| **Auditoria** | Tratar qualquer auditoria de etapa FIN-SENSE como **incompleta** se DOC-005 secção 5 estiver em branco. |

---

## 4. Ligação ao encerramento

- O **DOC-005** é o instrumento onde a validação PSA deve materializar-se.  
- O **DOC-004** comprova execução técnica e Git; **não** substitui a rubrica PSA.  
- Este **DOC-006** existe para que **ninguém** assuma que o ciclo está “fechado” ao nível de **homologação** sem passo PSA explícito.

---

**Fim do documento `DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006`.**
