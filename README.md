# OMEGA OS Kernel — Quant Fund Institutional Suite (V5.9.0)
=========================================================

Este repositório contém o kernel estratégico e os módulos de auditoria do **OMEGA Quantitative Fund**, homologados sob o protocolo **PSA V5.9.0 (NASA-STD)**.

## 🚀 Status do Projeto
- **Versão Atual:** V5.9.0 (Atomic Reconciliation)
- **Status SRE:** Homologado (+85.44% Retorno | 19.75% MDD)
- **Certificação:** PSA Forensic Grade (SHA-256 Verified)

## 📁 Estrutura de Arquivos
- `modules/omega_parr_f_engine.py`: Motor principal de análise (L0-L3).
- `omega_reconciliation_v590.py`: Script de auditoria e reconciliação definitiva.
- `omega_kpi_validator_v590.py`: Validador independente de KPIs (NASA Forensic).
- `RECONCILIATION_AUDIT_V5.9.0.md`: Memorial técnico da reconciliação final.

## ⚙️ Requisitos
- Python 3.8+
- Bibliotecas: `numpy`, `pandas`, `scipy` (veja `requirements.txt`)

## 🛠️ Como Auditar e Rodar
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Certifique-se de que os dados OHLCV (XAUUSD H4) estão no caminho configurado no script:
   Default: `C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv`
3. Execute a Reconciliação PSA V5.9.0:
   ```bash
   python omega_reconciliation_v590.py
   ```
4. Verifique o Checksum do CSV gerado com o validador:
   ```bash
   python omega_kpi_validator_v590.py
   ```

## 🔐 Camadas de Auditoria (Tier-0)
- **L0 (Fractal):** Higuchi Fractal Dimension ($2 + slope$).
- **L1 (Liquidity):** Volume Flow Profiling (POC/Density).
- **L2 (V-Flow):** Vectorial Momentum (Z-Metrics).
- **L3 (Inertia):** Heikin-Ashi Precision Timing.

---
**Assinado:** *Omega Engineering Team*
**Data:** 2026-03-15
