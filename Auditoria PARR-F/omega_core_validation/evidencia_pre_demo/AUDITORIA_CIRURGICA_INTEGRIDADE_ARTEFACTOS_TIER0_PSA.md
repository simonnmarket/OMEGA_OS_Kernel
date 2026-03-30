# Auditoria cirúrgica — Integridade de artefactos Tier-0 (encaminhamento ao PSA)

| Campo | Valor |
|--------|--------|
| **Documento** | `AUDITORIA_CIRURGICA_INTEGRIDADE_ARTEFACTOS_TIER0_PSA` |
| **Versão** | 1.0.0 |
| **Data** | 30 de Março de 2026 |
| **Emitido para** | PSA / Engenharia (Antigravity) — resposta obrigatória sob prazo |
| **Classificação** | Achados técnicos; **não** é conclusão jurídica sobre fraude |

---

## 1. Objetivo

Determinar, com **evidência reprodutível**, se existem **inconsistências materiais** entre:

- o ficheiro `MANIFEST_RUN_20260329.json` (campo `git_commit_sha`), e  
- a árvore Git real em `nebular-kuiper`;  

e entre **documentação de métricas** e **código** do gateway V10.4.

**Âmbito:** integridade de metadados e alinhamento código–documento. **Fora de âmbito:** tribunais, sanções, ou rotular intenção (erro de processo vs. outro).

---

## 2. Metodologia (comandos executados)

Ambiente de verificação: `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper` (repositório Git presente).

| # | Comando / acção | Resultado observado |
|---|-----------------|----------------------|
| V1 | `git rev-parse HEAD` | `eb7e0379a75bb4c1ebb5a1b28a3da7174f57d3b1` |
| V2 | `git log -1 --oneline` | `eb7e0379a75bb4c1ebb5a1b28a3da7174f57d3b1` — `feat(omega-v8): Lancamento Demo Fase 0 (1st Wave)...` — data **2026-03-23** |
| V3 | `git cat-file -t <sha_do_manifesto>` ou `git log -1 <sha>` | `fatal: unknown revision` para `f38157c7ad9248af90ffaabee8b9f71f1a2b3c4d` |
| V4 | Leitura de `MANIFEST_RUN_20260329.json` | Campo `"git_commit_sha": "f38157c7ad9248af90ffaabee8b9f71f1a2b3c4d"` |
| V5 | Comparar `DEFINICOES_METRICAS_RUN.md` §1.3 com `10_mt5_gateway_V10_4_OMNIPRESENT.py` | Ver secção 3 |

---

## 3. Achados factuais

### F1 — `git_commit_sha` do manifesto **não** existe no repositório local verificado

- **Manifesto:** `git_commit_sha` = `f38157c7ad9248af90ffaabee8b9f71f1a2b3c4d`  
- **HEAD actual:** `eb7e0379a75bb4c1ebb5a1b28a3da7174f57d3b1`  
- **Teste Git:** o objecto `f38157c7…` **não** resolve no repositório (`unknown revision`).

**Implicação:** o manifesto **não** amarra, por si só, a árvore de ficheiros ao **commit** real que o Git conhece neste clone. Isto viola o requisito de **reprodutibilidade forte** (Q1) até que seja explicado ou corrigido.

### F2 — Padrão suspeito no digest (revisão humana obrigatória)

O sufixo hexadecimal `…1a2b3c4d` assemelha-se a **sequência ordinal** em vez de um digest típico de `git rev-parse`. **Não** prova má intenção; **exige** explicação do autor do campo ou substituição por SHA real obtido por `git rev-parse HEAD` no momento do build.

### F3 — Desalinhamento entre documentação de métricas e código (Q3)

- **Ficheiro:** `evidencia_pre_demo/04_metricas_rol/DEFINICOES_METRICAS_RUN.md`  
  - §1.3 descreve Opportunity Cost como  
    \(|\text{Price}_{\text{signal}} - \text{Price}_{\text{current}}| \times \text{Size}\).

- **Ficheiro:** `Auditoria PARR-F/10_mt5_gateway_V10_4_OMNIPRESENT.py` (linha ~63)  
  - `engagement['opportunity_cost'] = abs(z_val * 0.1)  # Proxy de pontos`

**Implicação:** documentação e código **divergem**. Qualquer relatório que invoque “alinhamento métrica–código” para Q3 está **incorreto** até unificação.

### F4 — Estado do working tree (reprodutibilidade)

`git status` no clone verificado mostra **muitos ficheiros não rastreados** (`??`) sob `Auditoria PARR-F/`, incluindo `Núcleo de Validação OMEGA/`, gateway V10.4, etc.

**Implicação:** mesmo com um `git_commit_sha` válido, **ficheiros não commitados** não são recuperáveis pelo SHA. O PSA deve **commitar** ou **documentar** o pacote exacto (hash de artefacto ou arquivo zip assinado).

---

## 4. Classificação de risco (governança interna)

| ID | Risco | Severidade |
|----|--------|------------|
| R1 | Metadados de build **falsamente** alinhados ao Git | **Alta** (integridade de cadeia de custódia) |
| R2 | Métricas documentadas ≠ código | **Alta** (decisões de Conselho sobre base errada) |
| R3 | Árvore não commitada | **Média** (reprodutibilidade) |

**Nota:** “Fraude técnica” no sentido de **política interna Tier-0** (afirmar verificação sem evidência) pode corresponder a **R1+R2** até correcção; **não** implica automaticamente fraude no sentido legal.

---

## 5. Pedidos obrigatórios ao PSA (prazo: resposta escrita + artefactos)

1. **Explicar** a origem de `f38157c7ad9248af90ffaabee8b9f71f1a2b3c4d` (outro clone, outro remoto, geração manual, erro de copiar/colar). Se for erro, **substituir** no manifesto pelo output de `git rev-parse HEAD` no **mesmo** ambiente onde o stress foi gerado.  
2. **Anexar** captura de ecrã ou ficheiro de texto com:  
   `git rev-parse HEAD`  
   `git status -sb`  
   imediatamente antes de regenerar o manifesto.  
3. **Corrigir** `DEFINICOES_METRICAS_RUN.md` para que a secção Opportunity Cost coincida **literalmente** com o ramo de código que produz `opp_cost` (incluindo `abs(z_val * 0.1)` se for essa a regra definitiva), **ou** alterar o código para a fórmula documentada — **uma** verdade só.  
4. **Commitar** ou **empacotar** o conjunto mínimo de ficheiros que reproduzem o stress (script + versões), com registo no manifesto (`build_id` ou hash de ficheiro ZIP).  
5. **Declarar** sob responsabilidade (uma linha no manifesto ou `README_BUILD.txt`):  
   *“Nenhum campo de identificação Git foi introduzido manualmente sem corresponder a `git rev-parse`.”*

---

## 6. Comandos de verificação (PSA deve repetir e arquivar)

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
git rev-parse HEAD
git cat-file -t <SHA_EXTRAIDO_DO_MANIFESTO>
```

Se `git cat-file` falhar, o manifesto está **desalinhado** com o repositório até nova correção.

---

## 7. Conclusão para o Conselho / PSA

Existem **achados objectivos** (F1–F4) que **impedem** declarar “cadeia de custódia fechada” e “métricas alinhadas ao código” sem as correcções da secção 5.

O PSA deve **responder** ao presente documento com **evidência anexa**, não apenas narrativa.

---

**Fim — AUDITORIA_CIRURGICA_INTEGRIDADE_ARTEFACTOS_TIER0_PSA v1.0.0**
