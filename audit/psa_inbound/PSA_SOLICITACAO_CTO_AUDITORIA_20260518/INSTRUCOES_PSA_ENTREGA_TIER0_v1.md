# Instruções PSA — Pacote Tier‑0 (auditoria CTO / CEO)

**Versão:** 1.0  
**Data UTC:** 2026-05-18  
**Destinatário:** PSA (operações / dados)  
**Remetente:** Engenharia OMEGA (CTO)  
**Finalidade:** Entregar **dados brutos e manifestos** para fechar lacunas da auditoria **sem narrativa subjetiva** nem alteração pós‑export.

---

## 1) Pasta de entrega (obrigatório)

1. Criar um directório **novo** (nunca reutilizar pacotes antigos):

   `SOURCE_CODE/audit/psa_inbound/PSA_PACOTE_TIER0_<YYYYMMDD>_<HHMMSS>Z/`

   Exemplo: `.../PSA_PACOTE_TIER0_20260519_143000Z/`

2. **Proibições (anti‑contaminação)**

   - **Não editar** ficheiros CSV/JSON depois de exportados (qualquer correção = novo export + novo `package_id`).
   - **Não acrescentar** secções de “análise”, “conclusões” ou “parecer” **dentro** dos ficheiros classificados como **RAW** (`mt5_*`, `account_*`). Opinião só em ficheiro separado `PSA_NOTAS_SEPARADAS.md` **opcional**, claramente rotulado como *não integrável em métricas*.
   - **Não sobrescrever** `audit/paper/trade_feedback.jsonl` nem outros logs de runtime do motor.

3. **Integridade**

   - Preencher `PSA_MANIFEST.json` conforme template nesta pasta.
   - Gerar `PSA_MANIFEST.sha256` = SHA‑256 (hex minúsculo, uma linha + LF) dos bytes UTF‑8 de `PSA_MANIFEST.json`.

---

## 2) Janela temporal (CEO)

| Artefacto | Janela mínima |
|-----------|----------------|
| Deals / Orders MT5 | **2026-05-04 00:00 UTC** → **2026-05-18 23:59:59 UTC** (14 dias) + **dia 18 completo** |
| Snapshots conta | **EOD por dia** (18 linhas mínimo na janela; preferível série completa) |

Se o servidor MT5 usar **outro fuso**, declarar em `runtime_manifest.json` → `mt5_server_timezone` e manter **timestamps em ISO‑8601 com offset explícito** nos CSV (nunca só “hora local” sem offset).

---

## 3) Ficheiros obrigatórios

| Ficheiro | Classe | Conteúdo |
|----------|--------|-----------|
| `PSA_MANIFEST.json` | CONTROL | Lista de ficheiros, hashes SHA‑256, janela, conta, versão export. |
| `PSA_MANIFEST.sha256` | CONTROL | Hash do manifesto. |
| `mt5_deals_raw.csv` | **RAW** | **Todos** os deals no intervalo; **uma linha por deal**; colunas mínimas na secção 4. |
| `mt5_orders_raw.csv` | **RAW** | Ordens no mesmo intervalo (incl. pendentes/canceladas se exportáveis). |
| `runtime_manifest.json` | **RAW** | Ver secção 5. |
| `account_equity_eod.jsonl` | **RAW** | Uma linha JSON por dia: data, balance, equity, margin, moeda (valores numéricos apenas). |

**Opcional (recomendado):** `mt5_positions_history_raw.csv` se o export da corretora o permitir.

---

## 4) Colunas mínimas — `mt5_deals_raw.csv`

Encoding: **UTF‑8**. Separador: **`,`** (vírgula). Decimal: **`.`**

**Inglês (export MT5 típico):** incluir pelo menos as colunas equivalentes a:

`Time`, `Deal`, `Order`, `Position ID`, `Symbol`, `Type`, `Direction`, `Volume`, `Price`, `Commission`, `Fee`, `Swap`, `Profit`, `Magic`, `Comment`, `Reason`

**Português:** se o terminal estiver em PT, manter **cabeçalhos originais** e declarar em `PSA_MANIFEST.json` → `"csv_locale": "pt"` — o validador mapeia sinónimos.

**Regra:** incluir coluna **`Reason`** (código / texto do motivo do deal no MT5) **sem reinterpretação**. Se não existir no export, preencher manifesto `deals_export_notes` com a razão técnica (ex.: “build MT5 X não expõe Reason no CSV”).

---

## 5) `runtime_manifest.json` (schema mínimo)

```json
{
  "generated_at_utc": "ISO-8601",
  "package_id": "igual ao nome da pasta",
  "git_head": "sha completo do SOURCE_CODE no momento do export (git rev-parse HEAD)",
  "mt5_terminal_build": "número",
  "mt5_account_login": 0,
  "mt5_server": "string",
  "mt5_server_timezone": "IANA ou offset broker",
  "export_tool": "MT5_REPORTS_MANUAL | MT5_SCRIPT_NAME | OTHER",
  "operator_id": "iniciais PSA — não substitui log técnico"
}
```

**Não** incluir passwords ou tokens. Variáveis de ambiente: apenas **nomes** (`OMEGA_*`) se relevantes, **sem valores**.

---

## 6) `account_equity_eod.jsonl`

Uma linha por dia (UTC ou com offset explícito):

```json
{"date":"2026-05-18","balance":1250.8,"equity":1250.8,"margin":0,"currency":"USD","source":"MT5_ACCOUNT_HISTORY"}
```

Valores **copiados** do MT5; sem projeções.

---

## 7) Validação automática (após colocar ficheiros)

Na raiz `SOURCE_CODE`, executar:

```bash
python scripts/validate_psa_tier0_package.py --package audit/psa_inbound/PSA_PACOTE_TIER0_<...>/
```

O script escreve `PSA_VALIDATION_REPORT.json` **no interior do pacote** (artefacto de tooling, não narrativa PSA). Se `status != PASS`, corrigir **export** (não “editar à mão” linhas de deal).

---

## 8) O que a engenharia fará depois

Após `status: PASS`, a engenharia consome o pacote, cruza com `audit/paper/trade_feedback.jsonl`, classifica motivos de fecho **por regra** (TP/SL/parcial/…) e emite **documento CEO actualizado** com rastreio completo.

---

*Documento operacional interno OMEGA.*
