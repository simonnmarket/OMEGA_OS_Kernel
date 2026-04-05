# Documento Oficial — Fase 2, Fatia 1: Pipeline zero-loss CSV → PostgreSQL

| Campo | Valor |
|--------|--------|
| **ID** | `DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412` |
| **Referência curta** | `DOC-OFC-FASE2-FATIA1` |
| **Versão** | 1.0 CONGELADA |
| **Data** | 12 de abril de 2026 |
| **Prazo operacional** | Execução Fatia 1 até **12/04/2026**; auditoria CKO/CTO **13/04/2026** |
| **Classificação** | Nova iniciativa de engenharia — **independente** do congelamento DOC-001–007 (ciclo FIN-SENSE PSA) |
| **Responsável técnico** | MACE-MAX |

---

## 1. Objetivo

Pipeline canónico **zero-loss**: `DEMO_LOG_SWING_TRADE_*.csv` (OMEGA V10.5) → `modules/FIN_SENSE_DATA_MODULE/` → PostgreSQL local, com **SHA3-256 por linha**, observabilidade total e segredo via `os.getenv()`.

---

## 2. Não-objectivos

- Sem Kafka / RabbitMQ  
- Sem latência sub-ms  
- Sem alteração do CSV Fase E  
- Sem cloud (Windows, 16 GB RAM, local)

---

## 3. Escopo técnico

| Item | Definição |
|------|------------|
| **Caminho CLI** | `modules/FIN_SENSE_DATA_MODULE/scripts/ingest_pipeline.py` (ao lado de `ingest_demo_to_bronze.py`) |
| **Fluxo** | CSV (pandas) → parse → SHA3-256(payload canónico por linha) → Postgres **COPY** |
| **Dados de referência** | `DEMO_LOG_SWING_TRADE_20260401_T0046.csv` |
| **Tabela** | `bronze.demo_log_swing_trade` (schema v1.2) |
| **Batch** | 1000 linhas (fixo) |
| **Schema** | FIN_SENSE_DATA_MODULE v1.2 ULTIMATE HUB (referência interna file:442) |

---

## 4. Critérios de aceitação (bloqueadores)

| ID | Critério | Validação | Bloqueio |
|----|----------|-----------|----------|
| **A1** | Zero loss | `len(df_csv) == SELECT COUNT(*) FROM bronze.demo_log_swing_trade` (após ingestão de teste acordada; ver nota A1) | Sim |
| **A2** | Reprodutibilidade | SHA3-256(payload_canónico_por_linha) idêntico entre corridas | Sim |
| **A3** | Latência CPU batch | `time.process_time()` **< 100 ms** por batch de **1000** linhas (parse + SHA + preparação buffer) | Sim |
| **A4** | Observabilidade | `errors.log` com connection / timeout / parse | Sim |
| **A5** | Segurança | `DB_PASSWORD = os.getenv('PGPASS')` (nunca em código) | Sim |

**Nota A1:** Para testes repetíveis, usar **BD de teste** ou **TRUNCATE** da tabela alvo antes do run, **ou** filtro por `ingest_run_id` se já existir na implementação — o contrato exige igualdade de contagens **no contexto do teste documentado** no `DOC-TESTES-FASE2-FATIA1.md`.

---

## 5. Métricas obrigatórias (relatório)

Ambiente de referência: Windows 10/11, PostgreSQL 16.x local, SSD, 16 GB RAM.

| # | Métrica | Alvo |
|---|---------|------|
| 1 | Throughput | > 5000 linhas/s (batch = 1000, Windows SSD) |
| 2 | Erro commit | < 0,1 % (falhas SQL / retries) |
| 3 | Latência P99 | < 150 ms (**COPY flush**, I/O) |
| 4 | Integridade | 100 % das linhas com `sha3_line` válido |
| 5 | CPU | < 30 % single-core (classe i7 / Ryzen 7, ingestão) |

**Separação A3 vs métrica 3:** A3 = CPU por batch; métrica 3 = P99 do flush COPY (não misturar no mesmo número).

---

## 6. Gate técnico (engenharia → PSA)

- [ ] `modules/FIN_SENSE_DATA_MODULE/scripts/ingest_pipeline.py` executável e documentado  
- [ ] `tests/stress_test_10k.py` — 100 % PASS  
- [ ] A1–A5 validados com **10k linhas sintéticas**  
- [ ] `DOC-TESTES-FASE2-FATIA1.md` anexado com outputs e ambiente  

**Responsável:** MACE-MAX | **Data:** ____/____/2026 | **Hash commit (opcional):** ________________

---

## 7. Assinatura PSA (governança)

- [ ] Pacote recebido: `modules/FIN_SENSE_DATA_MODULE/` (incl. `scripts/`) + `tests/` + `DOC-TESTES-FASE2-FATIA1.md`  
- [ ] Tier-0 PAF-PSA: conforme processo  
- [ ] Não valida PnL (fases futuras)  

**Assinatura:** ____________________ | **Data:** ____/____/2026  

---

## 8. Escalão Conselho

- **Fatia 1:** não aplica escalão routine.  
- **Escalona apenas:** custos PostgreSQL > orçamento Fase 1 **ou** excepção técnica (`DOC-EXC-*`).

---

## 9. Entregas exactas (repositório)

```
REPOSITORIO/
├── modules/
│   └── FIN_SENSE_DATA_MODULE/
│       ├── fin_sense_data_module/
│       │   ├── schemas/
│       │   ├── storage/
│       │   └── __init__.py
│       ├── scripts/
│       │   ├── ingest_pipeline.py      # NOVO: CSV → Postgres
│       │   └── ingest_demo_to_bronze.py
│       └── pyproject.toml
├── tests/
│   ├── stress_test_10k.py
│   └── validate_a1_a5.py
├── DOC-TESTES-FASE2-FATIA1.md         # Raiz repo (ou governance/ — ver nota)
└── governance/
    └── DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412.md   # este ficheiro
```

**Nota:** `DOC-TESTES-FASE2-FATIA1.md` pode viver na **raiz** do repositório (como listado nas entregas operacionais) **ou** em `governance/` — uma única localização; referenciar no gate.

---

## 10. Comandos de execução (PowerShell)

```powershell
# SETUP
cd "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
pip install -e modules/FIN_SENSE_DATA_MODULE/

# TESTE STRESS
python tests/stress_test_10k.py
python tests/validate_a1_a5.py

# INGEST REAL (ajustar caminho do CSV se necessário)
python modules/FIN_SENSE_DATA_MODULE/scripts/ingest_pipeline.py --file "DEMO_LOG_SWING_TRADE_20260401_T0046.csv"
```

---

## 11. Roadmap Fase 2 (6 fatias)

| Fatia | Conteúdo |
|-------|----------|
| **1** | Pipeline zero-loss CSV → Postgres (este documento) |
| **2** | Idempotência + reprocessamento (`run_id` / `batch_id`) |
| **3** | Qualidade + quarentena (`rejects.csv`) |
| **4** | Live demo → CSV → DB incremental |
| **5** | Gold views + reconciliação PnL |
| **6** | Performance (índices / COPY / tuning) |

**Imutáveis:** CSV Fase E | schema v1.2 | Tier-0 PAF-PSA  

**Dependências:** Fatia N+1 requer gate PASS da Fatia N.  

**Documentação:** `DOC-OFC-FASE2-FATIA[2-6]-*.md` (sequencial, quando abertas).

---

## 12. Mudanças incorporadas (v1.0)

- `ingest_pipeline.py` em `modules/FIN_SENSE_DATA_MODULE/scripts/`  
- A1 com tabela explícita `bronze.demo_log_swing_trade`  
- A3 (100 ms CPU batch) vs métrica 3 (150 ms COPY) separados  
- Estrutura real do repo (`fin_sense_data_module/` + `scripts/`)  
- Roadmap com dependências lineares  

---

## 13. Pendências institucionais (ciclo FIN-SENSE — paralelo)

O **encerramento de homologação PSA** do ciclo **DOC-001–007** (rubrica DOC-005, Anexo A no `governance/README.md`) **não** é substituído por este documento. Tratam-se de **processos independentes**: este DOC cobre **engenharia Fase 2 Fatia 1**; o PSA continua a poder fechar o gap de governança conforme **DOC-007**.

---

**Fim do documento `DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412`.**
