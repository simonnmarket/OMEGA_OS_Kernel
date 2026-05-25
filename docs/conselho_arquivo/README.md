# Arquivo do Conselho — OMEGA (espelho governança + GitHub)

Pasta canónica no repositório para documentos que o CEO/CKO/Conselho aprovam.
A pasta Desktop `Arquivos Pendentes Auditoria\Pendente\Auditoria` pode ser limpa após cópia aqui.

## Índice (2026-05-20)

| ID | Ficheiro | Descrição |
| --- | --- | --- |
| RCV-P0 | [OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX.md](OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX.md) | RCA execução — 4 mandatos não negociáveis |
| ANA-RCV | [../requests/OMEGA_RCV_20260520_P0_ARQUITECTURAL_FIX_ANALISE.md](../requests/OMEGA_RCV_20260520_P0_ARQUITECTURAL_FIX_ANALISE.md) | Análise técnica vs código |
| CMP | [COMPONENT_HEALTH_MATRIX.md](COMPONENT_HEALTH_MATRIX.md) | Matriz componente × status (gerada por script) |
| PSA | [../requests/PSA_MEMORANDO_GITHUB_REGISTO_20260520.md](../requests/PSA_MEMORANDO_GITHUB_REGISTO_20260520.md) | Pedido PSA: commit + registo memória |
| CEO | [CEO_MANUAL_INICIO_OPERACOES.md](CEO_MANUAL_INICIO_OPERACOES.md) | **Só após OK PSA** — start MT5/runner |
| Desktop | [desktop_originais_20260520/](desktop_originais_20260520/) | Cópia dos 4 TXT da pasta Auditoria |

## Regenerar matriz de componentes

```bash
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
python scripts/omega_component_health_matrix.py ^
  --json audit/component_health/component_health_20260520.json ^
  --md docs/conselho_arquivo/COMPONENT_HEALTH_MATRIX.md
```

## Código P0 aplicado (nível 1)

- `core_engines/shadow_loop.py` — Mandatos 1–4 (RCV 2026-05-20)
- `scripts/run_omega_24x7.ps1` — modo diagnóstico CKO (sem `--equity 10000`)

**Restart:** só após validação em demo (log 10016 + gates + equity MT5 real).
