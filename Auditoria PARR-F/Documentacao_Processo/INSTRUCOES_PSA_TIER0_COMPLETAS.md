# Instruções completas e objetivas — PSA (Tier-0)

**Domínio**: SIMONNMARKET GROUP · **Projeto**: AURORA v8.0 · **Sistema**: OMEGA  
**Destinatário**: PSA (Principal Solution Architect)  
**Tipo**: Instruções operacionais — **ler e seguir**; manter alinhado ao briefing vivo  
**Versão**: 1.0 · **Data**: 2026-03-22 (UTC)

> **Ficheiro canónico** — path oficial: este diretório sob `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\`.

---

## 1. Onde trabalhar (obrigatório)

| Item | Path canónico |
|------|----------------|
| **Raiz do projeto** | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\` |
| **Auditoria PARR-F** | `...\nebular-kuiper\Auditoria PARR-F\` |
| **Outputs** | `...\Auditoria PARR-F\outputs\` |
| **Logs** | `...\Auditoria PARR-F\logs\` |
| **Documentação de processo** | `...\Auditoria PARR-F\Documentacao_Processo\` |

**Regra**: uma única fonte da verdade; não editar cópia paralela em `.cursor` como oficial.

---

## 2. Documentos — *como* vs *estado agora*

| Tipo | Ficheiros |
|------|-----------|
| Procedimentos | SOP, Checklist, Definições, Template, Protocolo de Auditoria |
| Estado vivo | `PSA_BRIEFING_ESTADO_ATUAL.md` |
| Instruções objetivas | `INSTRUCOES_PSA_TIER0_COMPLETAS.md` (este ficheiro) |

---

## 3. Responsabilidades do PSA

1. Manter e executar `psa_audit_engine.py` (OHLCV-driven).  
2. Garantir AMI + OHLCV e paths no workspace canónico.  
3. Gerar: trades, equity, summary + hashes após cada run oficial.  
4. Camada 3 (MT5/OHLCV) quando exigido; relatório em `logs/`.  
5. **G-01**: Sharpe/Sortino/Calmar na equity no `summary.json` (v3.1 ou equivalente).  
6. **G-02**: Registar Git (repo, branch, SHA) no briefing.  
7. Atualizar briefing após cada marco relevante.

---

## 4. Ordem de trabalho (novo ativo / re-run)

1. Workspace canónico.  
2. Validar entradas (SOP/Checklist).  
3. Executar motor; validar contagens e ficheiros.  
4. Hashes no summary.  
5. Camadas 1 e 2.  
6. Camada 3.  
7. Atualizar `PSA_BRIEFING_ESTADO_ATUAL.md`.

---

## 5. Gaps

- **G-01** aberto — métricas equity no summary.  
- **G-02** aberto — SHA no briefing.  
- **G-03** fechado — diretório único `.gemini`.

---

## 6. Não fazer

- Artefactos sem path canónico sem nota.  
- Sharpe/Sortino/Calmar só a partir de trades.  
- Camada 3 sem validação real.  
- Briefing desatualizado após stress test.

---

## 7. Texto para envio ao PSA

> PSA: instruções em `Documentacao_Processo/INSTRUCOES_PSA_TIER0_COMPLETAS.md`; estado em `PSA_BRIEFING_ESTADO_ATUAL.md`. Trabalhar só em `...\nebular-kuiper\` (`.gemini`). Próximo: G-01 (v3.1), G-02 (Git no briefing).

---

| Versão | Data | Notas |
|--------|------|--------|
| 1.0 | 2026-03-22 | Criação |

---

**Fim — `INSTRUCOES_PSA_TIER0_COMPLETAS.md`**
