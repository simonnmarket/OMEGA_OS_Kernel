# Solicitação formal — Pacote Tier-0 (auditoria OMEGA)

**Para:** PSA (Operações / Dados)  
**De:** CEO / Conselho (encaminhamento)  
**Assunto:** Entrega de extracts MT5 + manifestos — janela 14 dias e fecho 2026-05-18  
**Prioridade:** Alta  
**Versão do pedido:** 1.0  
**Data:** 2026-05-18  

---

## 1. Objectivo

Gerar e depositar **um único pacote** de dados **brutos**, **verificáveis por hash** e **livres de interpretação**, para a engenharia concluir a **auditoria institucional** (motivo de fecho por operação, reconciliação com logs internos, série de equity).  

**Não** é solicitado parecer de mercado, recomendações de trading nem edição de relatórios já entregues.

---

## 2. Onde gravar o pacote

Na máquina / repositório OMEGA (`SOURCE_CODE`), criar uma pasta **nova** com nome exacto no padrão:

`audit/psa_inbound/PSA_PACOTE_TIER0_<YYYYMMDD>_<HHMMSS>Z/`

**Exemplo:** `audit/psa_inbound/PSA_PACOTE_TIER0_20260519_143000Z/`

**Regra de integridade:** qualquer correção após export ⇒ **nova pasta** + novo `package_id` (não sobrescrever pacotes anteriores).

---

## 3. Anti-contaminação (obrigatório)

| Permitido | Proibido |
|-----------|----------|
| Export MT5 → CSV/JSON **uma vez**, depois **só leitura** | Alterar à mão linhas de `mt5_*` para “bater certo” |
| Ficheiro opcional `PSA_NOTAS_SEPARADAS.md` **fora** da cadeia de métricas | Inserir conclusões ou comentários **dentro** dos ficheiros classificados como RAW |
| Copiar valores numéricos do terminal | Valores inventados ou arredondados sem espelhar o MT5 |
| Validar com o script oficial | Modificar `audit/paper/trade_feedback.jsonl` ou outros logs do motor |

---

## 4. Janela temporal dos exports

| Dado | Intervalo mínimo (UTC) |
|------|-------------------------|
| Deals e ordens MT5 | **2026-05-04 00:00:00** → **2026-05-18 23:59:59** |
| Snapshots de conta (EOD) | **Uma linha por dia civil** cobrindo a mesma janela (mínimo 15 dias de linhas se disponível) |

Se a conta MT5 usar **outro fuso**, declarar em `runtime_manifest.json` o campo `mt5_server_timezone` e usar **timestamps com offset explícito** nos CSV quando o export o permitir.

---

## 5. Ficheiros obrigatórios dentro do pacote

| # | Nome do ficheiro | Tipo | Descrição |
|---|------------------|------|-----------|
| 1 | `PSA_MANIFEST.json` | CONTROL | Lista de ficheiros, `package_id`, janela, conta, `sha256` de cada artefacto (ver template no repositório). |
| 2 | `PSA_MANIFEST.sha256` | CONTROL | Uma linha: SHA-256 **em hex minúsculo** do ficheiro `PSA_MANIFEST.json` (gerar com `scripts/psa_seal_manifest.ps1` — secção 7). |
| 3 | `mt5_deals_raw.csv` | **RAW** | Todos os deals no intervalo; **UTF-8**, separador `,`. Incluir coluna de **motivo** (Reason / Motivo) **tal como o MT5 exporta**, sem reinterpretação. |
| 4 | `mt5_orders_raw.csv` | **RAW** | Ordens no mesmo intervalo. |
| 5 | `runtime_manifest.json` | **RAW** | Ver secção 6. |
| 6 | `account_equity_eod.jsonl` | **RAW** | Uma linha JSON por dia: `date`, `balance`, `equity`, `margin` (se disponível), `currency`, `source`. |

**Opcional:** `mt5_positions_history_raw.csv` se a corretora exportar histórico de posições de forma fiável.

**Template e instruções técnicas detalhadas** (colunas, exemplos):  
`audit/psa_inbound/PSA_SOLICITACAO_CTO_AUDITORIA_20260518/INSTRUCOES_PSA_ENTREGA_TIER0_v1.md`  
`audit/psa_inbound/PSA_SOLICITACAO_CTO_AUDITORIA_20260518/PSA_MANIFEST.template.json`

---

## 6. Conteúdo mínimo de `runtime_manifest.json`

Campos obrigatórios (valores reais; **sem** passwords ou secrets):

- `generated_at_utc` (ISO-8601)  
- `package_id` (igual ao nome da pasta do pacote)  
- `git_head` (saída de `git rev-parse HEAD` na raiz `SOURCE_CODE` no momento do export)  
- `mt5_terminal_build`  
- `mt5_account_login`  
- `mt5_server`  
- `mt5_server_timezone`  
- `export_tool` (ex.: `MT5_REPORTS_MANUAL` ou nome do script MQL5, se aplicável)  
- `operator_id` (iniciais PSA — apenas rastreabilidade humana)

---

## 7. Ordem de execução recomendada (alta cadência)

1. Exportar do MT5 para `mt5_deals_raw.csv` e `mt5_orders_raw.csv` (janela da secção 4).  
2. Preencher `runtime_manifest.json` e `account_equity_eod.jsonl` com **cópia literal** dos valores da plataforma.  
3. Copiar `PSA_MANIFEST.template.json` → `PSA_MANIFEST.json`; preencher metadados e lista `files` com **sha256** de cada ficheiro de dados (não incluir hash circular do próprio manifesto no corpo antes de selar).  
4. Na raiz `SOURCE_CODE`, executar:

   ```powershell
   .\scripts\psa_hash_artifacts.ps1 -PackageDir "audit\psa_inbound\PSA_PACOTE_TIER0_<...>Z"
   ```

   Copiar os `sha256` devolvidos para as entradas correspondentes em `PSA_MANIFEST.json` e gravar.

5. Selar o manifesto:

   ```powershell
   .\scripts\psa_seal_manifest.ps1 -PackageDir "audit\psa_inbound\PSA_PACOTE_TIER0_<...>Z"
   ```

6. Validação final:

   ```text
   python scripts/validate_psa_tier0_package.py --package audit/psa_inbound/PSA_PACOTE_TIER0_<...>Z/
   ```

   O resultado tem de ser **`"status": "PASS"`** no ficheiro gerado `PSA_VALIDATION_REPORT.json` **dentro** do pacote. Se for `FAIL`, repetir export (não editar dados “à pressa”).

---

## 8. Entrega

- **Preferencial:** commit Git com a pasta do pacote + notificação ao CTO (caminho + `package_id`).  
- **Alternativa:** arquivo ZIP com a **mesma árvore** de ficheiros + envio por canal aprovado pelo CEO; o ZIP **não** substitui a obrigação de hashes no `PSA_MANIFEST.json`.

---

## 9. O que acontece a seguir

Com `PSA_VALIDATION_REPORT.json` em **PASS**, a engenharia produz o **documento de auditoria CEO completo e actualizado** (cruzamento MT5 ↔ `trade_feedback`, taxonomia de fechos TP/SL/parcial/KS/manual, atribuição por versão de código).

---

## 10. Contacto / dúvidas técnicas

Dúvidas sobre colunas ou falhas de validação: **CTO / engenharia OMEGA**, referindo sempre o `package_id` e anexando `PSA_VALIDATION_REPORT.json`.

---

*Documento operacional — OMEGA Investment Systems. Pode ser reencaminhado integralmente ao PSA.*
