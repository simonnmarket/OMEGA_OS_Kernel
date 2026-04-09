# REQ-PARRF-COO-APRESENTACAO-FASE6-L1-FIN-SENSE-SSOT-V120-20260406

**ID oficial (completo):** `REQ-PARRF-COO-APRESENTACAO-FASE6-L1-FIN-SENSE-SSOT-V120-20260406`  

**Versão do pacote TIER-0 referenciado:** 1.2.0  
**Data do documento:** 2026-04-06  
**Classificação:** relatório executivo + sumário técnico (apresentação externa)  
**Pasta de artefactos:** `Auditoria PARR-F/`  

**Documentos correlatos (IDs completos):**

| ID completo | Função |
|-------------|--------|
| `REQ-PARRF-DIRETRIZES-CRITICAS-CODIGO-TIER0-V120-20260411` | Diretrizes, catálogo de falhas, contrato de código |
| `REQ-PARRF-AVALIACAO-TECH-LEAD-RELATORIO-CEO-V120-20260411` | Avaliação Tech Lead vs relatório CEO (L1 stub, SSOT) |
| `DOC-PARRF-REGISTO-OFICIAL-CONSOLIDADO-PSA-COO-FASE6-L1-FIN-SENSE-V120-20260410` | **Registo consolidado oficial** (envio único: PSA + COO + changelog + tabelas PASS/FAIL atualizadas) |
| `DOC-CEO-PSA-EXEC-REQ-PARRF-COO-APRESENTACAO-FASE6-L1-V120-20260409_2345` | PSA oficial de execução sequencial (SSOT + E2E L1 + relatório JSON) |

**Aprovação COO (registo):** 2026-04-09 23:45 CEST — documento de apresentação **10/10**; Conselho aprovado; rota PSA mantida. Título interno COO: `REQ-PARRF-COO-APRESENTACAO-FASE6-L1-V120` (apelido operacional; **ID completo deste dossiê** mantém-se na linha 3 deste ficheiro).

---

## 1. Identificação para envio

Ao anexar este ficheiro em e-mail ou repositório, use **exatamente** o seguinte como assunto ou etiqueta de versão:

```text
REQ-PARRF-COO-APRESENTACAO-FASE6-L1-FIN-SENSE-SSOT-V120-20260406
```

**Checksum de rastreio:** 
- **Commit SHA:** `5cae0a9dda67cc2652c11f86bd117146dcd65300`
- **Output resumido de status:**
```text
 M modules/__pycache__/omega_kernel_v5_1_refined.cpython-311.pyc
?? "Auditoria PARR-F/omega_audit_PARRF_*.json" (untracked audit trails)
```

---

## 2. Resumo executivo (COO)

- **Fase 6 L1 FIN-SENSE:** aprovada nos critérios de **falha segura** e **integração condicional** quando não existe DSN PostgreSQL ou dados: o pipeline não avança silenciosamente; JSON de auditoria reflete erros e bloqueios de risco de forma coerente.
- **Produção “L1 real”:** permanece **pendente** de **DSN de staging/produção validado**, **VIEW (ou equivalente) populada** e evidência arquivada de execução E2E com `layers.dos.errors` vazio para o símbolo alvo.
- **SSOT:** risco histórico de duas árvores (`Desktop\OMEGA_OS_Kernel` vs `nebular-kuiper`). **Ação obrigatória:** um único remoto/branch canónico; `git pull` e working tree alinhado em ambas as cópias antes de citar commits como “oficiais”.

---

## 3. Critérios de passagem (checklist de apresentação)

| Critério | Estado declarado | Nota |
|----------|------------------|------|
| Integração condicional `OMEGA_USE_FIN_SENSE_L1` + fallback stub | Pass | Flag `1` ativa L1; import/setup inválido cai no stub com log |
| JSON falha segura (`DOS_ERRORS` → `RISK_BLOCKED`) | Pass | Comportamento alinhado ao orquestrador v1.2.0 |
| Registo “L1 ativo” / proveniência | Pass | Logs + campos `l1_integration_requested`, `l1_class` no audit JSON |
| L1 PostgreSQL real + VIEW populada | Pendente | Exige credenciais e DDL acordados pelo CEO/Conselho |
| SSOT único Desktop = nebular-kuiper | Em alinhamento | Verificar `git remote -v` e mesmo HEAD após pull |

---

## 4. Artefactos de código (referência)

| Ficheiro | Papel |
|----------|--------|
| `omega_orquestrador_tier0_v120.py` | Orquestrador 4 camadas; factory L1 condicional; audit `omega_audit_PARRF_{trace_id}.json` |
| `fin_sense_l1_esqueleto_v120.py` | Contrato `compute_metrics(symbol)`; `FIN_SENSE_DSN`, `FIN_SENSE_L1_VIEW`; proveniência via hash canónico |

Variáveis de ambiente relevantes:

- `OMEGA_USE_FIN_SENSE_L1` — `1` para ativar camada FinSense L1.
- `FIN_SENSE_DSN` — connection string (nunca em código).
- `FIN_SENSE_L1_VIEW` — nome da VIEW (validação de identificador `[a-zA-Z0-9_]`).
- `OMEGA_AUDIT_DIR` — diretório dos JSON de auditoria (opcional; default `.`).

---

## 5. Comandos PSA (validação rápida)

**5.1 Alinhamento SSOT**

```powershell
cd "C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F"
git remote -v
git pull origin main
git status --porcelain
```

(Repetir na cópia `nebular-kuiper` com o mesmo critério.)

**5.2 E2E L1 com PostgreSQL real (staging)**

```powershell
cd "C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F"
$env:FIN_SENSE_DSN = "<DSN confirmado pelo CEO>"
$env:OMEGA_USE_FIN_SENSE_L1 = "1"
1..3 | ForEach-Object { python omega_orquestrador_tier0_v120.py }
```

**Correção obrigatória de sintaxe:** o interpretador Python exige extensão `.py` — usar `python omega_orquestrador_tier0_v120.py`, não `python omega_orquestrador_tier0_v120`.

---

## 6. Próximos passos (ordem sugerida)

1. Homologar DSN staging e nome final da VIEW (Conselho / DBA).
2. Garantir linha de dados para o símbolo de teste (ex.: `XAUUSD`) na VIEW.
3. Executar E2E 3×; arquivar os três JSON com `trace_id` e, se sucesso, `layers.dos.errors` vazio e `provenance_sha256` preenchido.
4. Fechar SSOT: commit único referenciado nos dois clones ou deprecar explicitamente o clone não canónico.

---

## 7. Limitações deste documento

- Este texto **não substitui** logs ou outputs de comando: o estado “em produção” só é demonstrável com evidências anexadas.
- Datas e SHAs citados por terceiros (ex.: ponto de verificação `5cae0a9dda67cc2652...`) devem ser **revalidados** com `git rev-parse HEAD` no repositório canónico no dia da apresentação.

---

## 8. Declaração de uso do ID

Para correspondência oficial, citar sempre o **ID completo**:

**`REQ-PARRF-COO-APRESENTACAO-FASE6-L1-FIN-SENSE-SSOT-V120-20260406`**

Fim do documento.
