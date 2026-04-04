# Documento Oficial — Desvio de Padrão Estrutural: Modules vs Raiz

| Campo | Valor |
|--------|--------|
| **ID do documento** | `DOC-OFC-DESVIO-PADRAO-ESTRUTURAL-MODULES-FINSENSE-20260404-002` |
| **Versão** | 1.0 |
| **Data** | 4 de abril de 2026 |
| **Classificação** | Interno — Governança OMEGA |
| **Emitido por** | PSA (IA Agent) |
| **Assunto** | Diagnóstico de desvio de localização de módulos e dados do FIN-SENSE |

---

## 1. Diagnóstico do Desvio

Foi identificado que, durante a materialização e conclusão inicial do módulo **FIN-SENSE DATA MODULE**, houve um **desvio do padrão estrutural** do sistema OMEGA:

1. **Localização do Código:** O módulo foi colocado na raiz do workspace (`nebular-kuiper\FIN_SENSE_DATA_MODULE`) e duplicado em `Auditoria Conselho`, quando o padrão institucional exige que módulos residam em `modules\`.
2. **Localização de Dados:** Dados demo e de teste foram dispersos entre `Auditoria Conselho\data\hub` e a raiz, sem um Hub centralizado único em `FIN_SENSE_DATA\hub`.
3. **Documentação:** Documentos de governança (`DOC-OFC`) foram mantidos em pastas de auditoria (trânsito) em vez de uma pasta dedicada e imutável de governança.

## 2. Impacto e Risco

A manutenção deste desvio gera risco de **deriva de código**, **conflitos de importação** e **falha em auditorias de longo prazo** pela dispersão de provas documentais.

## 3. Plano de Realinhamento (Proposto)

- Mover SSOT do código para `modules\FIN_SENSE_DATA_MODULE\`.
- Criar diretório `governance\` na raiz para todos os `DOC-OFC`.
- Centralizar o Data Lake em `FIN_SENSE_DATA\hub\`.

---
**Fim do diagnóstico.**
