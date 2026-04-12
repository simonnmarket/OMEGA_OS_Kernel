"""
ARBITRO_MULTITF_V1.py - Lógica de Veto Estrutural (RT-B2)
ID: DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414
Responsável: CQO / Tech Lead
"""


def arbitrate_signal(signal_low_tf: str, trend_high_tf: str) -> str:
    """
    Regra Multi-TF: o timeframe maior veta o menor se houver desalinhamento.
    Valores esperados: BUY | SELL | NEUTRAL (normalizar upstream).
    Retorno: PASS | VETO | HOLD (alinhado ao schema de auditoria).
    """
    s_low = (signal_low_tf or "").upper()
    t_high = (trend_high_tf or "").upper()

    if t_high == "NEUTRAL":
        return "HOLD"

    if s_low == t_high:
        return "PASS"

    return "VETO"


if __name__ == "__main__":
    assert arbitrate_signal("BUY", "BUY") == "PASS"
    assert arbitrate_signal("BUY", "SELL") == "VETO"
    assert arbitrate_signal("SELL", "NEUTRAL") == "HOLD"
    print("ARBITRO_MULTITF_V1: Unit tests passed.")
