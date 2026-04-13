# DOCUMENTO_OFICIAL_OPERACIONALIZACAO_ECOSISTEMA_COMPLETO_PSA

## 1. Visão Global
Este documento dita a orquestração noturna do OMEGA TIER-0 v1.2.0, assegurando a implantação na conta demo com o Arbitro Multi-TF e Física de Lote.

## 2. Padrões de Ambiente
- **NEBULAR_KUIPER_ROOT**: `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper`
- **PSA_AUDIT_BASE**: `$NEBULAR_KUIPER_ROOT\Auditoria PARR-F`

## 3. Passo a Passo Técnico
1. Executar `PSA_RUN_NIGHT_STACK.ps1`.
2. O script deverá levantar as dependências live.
3. Inicializar `omega_orquestador_tier0_v120.py`.
4. Reportar o status num artefato legível.

## 4. Checklist Fim de Turno (Preenchimento PSA)
- [x] Binários Sincronizados (Pull)
- [x] Variáveis Globais de Caminho Injetadas
- [x] Motor de Física e Arbitro Ativos no Orquestrador
- [x] MT5 Loop Noturno Disparado sem Segredos
- [x] Evidências geradas e pushes executados
