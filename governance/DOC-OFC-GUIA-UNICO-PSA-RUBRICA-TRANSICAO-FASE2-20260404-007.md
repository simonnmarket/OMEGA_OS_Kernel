# Documento Oficial — Guia Único: Rubrica PSA, Homologação e Transição (Fase 2)

| Campo | Valor |
|--------|--------|
| **ID** | `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` |
| **Versão** | 1.0 |
| **Data** | 4 de abril de 2026 |
| **Classificação** | Operacional — **Passagem única** (evita ciclos de reenvio e micro-alterações) |
| **Finalidade** | Concentrar **tudo** o que o PSA e a engenharia precisam para: (1) rubricar sem ambiguidade, (2) actualizar o índice **uma vez**, (3) iniciar a fase técnica seguinte sem reabrir a governança do ciclo FIN-SENSE |

---

## Regra de ouro (congelamento)

Após o **único commit pós-rubrica** descrito na secção 4, **não** voltar a editar `governance/README.md` nem os DOC-001 a 007 **salvo**:

- ordem explícita do **CEO** para revisão de versão (ex.: índice v2.0), ou  
- nova **iniciativa documental** com novo `DOC-OFC-*` (outro projecto).

Isto evita o padrão “enviar → reavaliar → enviar de novo” no mesmo ciclo.

---

## 1. Verificação pré-rubrica (PSA — uma vez)

Executar no clone actualizado (`main`):

```bash
git pull origin main
git tag -l "finsense*"
ls governance/DOC-OFC-*20260404*.md
```

Confirmar existência física dos ficheiros referidos no `README.md` (IDs 001 a 006 e este 007).

Confirmar caminhos no workspace:

- `modules/FIN_SENSE_DATA_MODULE/`
- `FIN_SENSE_DATA/hub/` (ou pasta `FIN_SENSE_DATA/` conforme política)
- `governance/`

---

## 2. Acto de rubrica (humano — DOC-005)

1. Abrir: `governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md`
2. Preencher **secção 5** (tabela: marcar **Sim** nas cinco linhas; nome; data; identificador interno se existir).
3. **Arquivar** evidência (acta, ticket, sistema de compliance) — referência a guardar para o Anexo A.

**Não** é necessário outro documento além do DOC-005 para a rubrica em si.

---

## 3. Actualização do índice (README) — **substituição única**

Após a rubrica, substituir no ficheiro `governance/README.md` **apenas** o bloco de estado no topo (linhas que descrevem homologação e “Pronto para rubrica”) pelo texto do **Anexo A**, preenchendo os placeholders.

**Não** refazer o resto da tabela de IDs salvo erro factual.

---

## 4. Commit único pós-rubrica (Git)

Uma única mensagem sugerida:

```text
governance: homologacao PSA concluida (DOC-005 sec.5); README estado final; ref DOC-007
```

```bash
git add governance/README.md governance/DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005.md
git commit -m "governance: homologacao PSA concluida (DOC-005 sec.5); README estado final; ref DOC-007"
git push origin main
```

*(Se o DOC-005 só existir preenchido localmente e não for commitável por política, commitar só o README com nota "rubrica arquivada em [REF]" no corpo do commit.)*

---

## Anexo A — Bloco para colar no `README.md` (topo, após rubrica)

Substituir as linhas que ainda dizem **PENDENTE** / **Pronto para rubrica** por:

```markdown
**Homologação PSA:** **CONCLUÍDA** em [DATA_AAAA-MM-DD] — rubrica em `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` secção 5. Responsável: [NOME_PSA]. Arquivo institucional: [REF_TICKET_OU_ACTA].

**Estado operacional:** **Homologado** ao nível institucional para o ciclo FIN-SENSE (governança + estrutura + Git). Gap de governança **fechado**.

**Transição:** ver secção "Fase 2" neste documento (DOC-007) para integração de alta performance (fora do âmbito da rubrica).
```

Manter as linhas de **ciclo técnico-documental ENCERRADO** e **Tag Git** como estão.

---

## 5. Fase 2 — Integração de alta performance (definição única, sem reabrir 001–006)

**Âmbito:** evolução técnica do hub (ex.: **Kafka/Redis** para eventos, **S3** ou equivalente para object storage, **Parquet**, políticas de **RBAC** e observabilidade).

**Regra:** esta fase é **nova iniciativa de engenharia**. Não reescreve a trilha 001–007. Quando o CEO aprovar o arranque:

1. Abrir **novo** `DOC-OFC-*` de arranque de fase (escopo, riscos, critérios de pronto).  
2. Implementar em ramos/feature; manter `modules/FIN_SENSE_DATA_MODULE/` como contrato; evoluir conectores e infra.

**Nada disto bloqueia** a rubrica do DOC-005: a homologação do **ciclo de governança** e a **fase técnica seguinte** são camadas diferentes.

---

## 6. Encerramento do guia único

Com a execução das secções 1–4 e o congelamento da secção 0, a etapa de **documentação iterativa** deste ciclo fica **definitivamente** substituída por **um procedimento único** reprodutível.

**Fim do documento `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007`.**
