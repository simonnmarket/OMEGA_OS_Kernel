# TECH_SPEC — índice curto (núcleo OMEGA)

Versão pacote **1.1** — ver **[DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md](./DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md)** (matriz de comprovação, roadmap empírico, citações de auditoria).

**DEFINICOES alinhadas:** `Documentacao_Processo/DEFINICOES_TECNICAS_OFICIAIS.md` — **OMEGA-DEFINICOES-v1.1.0**.

## Testes

```bash
pip install -r requirements.txt
python -m pytest tests -v
```

*(15 testes na v1.1.)*

## Módulos

| Módulo | Papel |
|--------|--------|
| `rls_regression.py` | RLS 2D, `innovation` / `update`, OLS batch |
| `v821_batch.py` | Batch V8.2.1: OLS janela exclui barra atual; Z `ewm` + `shift(1)` |
| `online_rls_ewma.py` | RLS + EWMA recursiva; Z com estado do passo anterior |
| `engagement_metrics.py` | Métrica 9, n=0, opportunity cost condicional |
| `parity_report.py` | Métrica 10.A/10.B — MSE / deriva entre pipelines de Z |
