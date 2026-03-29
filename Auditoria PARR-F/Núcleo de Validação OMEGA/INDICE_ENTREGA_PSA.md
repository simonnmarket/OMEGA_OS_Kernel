# Índice da entrega — Núcleo de Validação OMEGA

Pasta destinada ao **PSA** para instalação, execução de testes e trilho de auditoria.

## Começar aqui

0. **`ORDEM_OFICIAL_EXECUCAO_PSA_NUCLEO_V1_1.md`** — **instrução vinculativa**: o que executar, artefactos A1–A4 e critério para encerrar sem re-auditoria interpretativa.
1. **`SCRIPT_INSTALACAO_E_DIRETRIZES_PSA.md`** — passos de instalação, `pytest`, e regras de governança.
2. **`DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md`** — especificação v1.1 e matriz afirmação → teste.
3. **`DEFINICOES_TECNICAS_OFICIAIS.md`** — protocolo **OMEGA-DEFINICOES-v1.1.0** (métricas 1–10).

## Código

Módulos na raiz desta pasta; testes em `tests/`. A pasta **`omega_core_validation`** original no repositório pode continuar a existir como cópia de trabalho; **esta pasta é o pacote a enviar ao PSA** (espelho + documentação + definições).

## Critério de sucesso imediato

```bash
pip install -r requirements.txt
python -m pytest tests -v
```

Resultado esperado: **15 passed** (verificar no output).

## Fase empírica (dados reais, histórico completo no merge)

4. **`INSTRUCAO_EXECUCAO_EMPIRICA_PSA.md`** — procedimento completo e critérios de entrega.
5. **`run_empirical_parity_real_data.py`** — gera `RELATORIO_EMPIRICO_PARIDADE.json`, `.txt` e `serie_alinhada_merge.csv` a partir de **dois CSV reais** (`inner join` em `time`, sem projeção).
