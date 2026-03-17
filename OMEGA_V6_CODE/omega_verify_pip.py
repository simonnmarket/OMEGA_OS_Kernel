"""
omega_verify_pip.py — Gate 0 :: Verificação de Pip Value XAUUSD
EXECUTAR ANTES DE QUALQUER TESTE.

Resultado guardado em omega_verify_pip.log (JSON) para dossiê de auditoria.
Repetir se corretora ou tipo de conta MT5 mudar (ECN vs Standard).
"""

import json
import MetaTrader5 as mt5
from datetime import datetime, timezone

LOG_FILE = "omega_verify_pip.log"

def run_pip_verification() -> dict:
    """Verifica e classifica o pip value XAUUSD. Retorna dict com resultado."""
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": "XAUUSD",
        "status": None,
        "scenario": None,
        "tick_value": None,
        "tick_size": None,
        "pip_size": 0.10,  # Padrão XAUUSD: 10 ticks = 1 pip (verificar via sym.point * 10 se mudar)
        "pip_value_001_lot": None,
        "risk_50_pips": None,
        "trades_per_day_at_133usd": None,
        "action": None,
    }

    if not mt5.initialize():
        result["status"] = "FAIL"
        result["action"] = "MT5 não inicializado — verificar instalação e credenciais"
        return result

    sym = mt5.symbol_info("XAUUSD")
    if sym is None:
        mt5.shutdown()
        result["status"] = "FAIL"
        result["action"] = "XAUUSD não encontrado na corretora — verificar símbolo"
        return result

    tick_value = sym.trade_tick_value
    tick_size  = sym.trade_tick_size
    pip_size   = result["pip_size"]

    pip_val_std = tick_value * (pip_size / tick_size)
    pip_val_001 = pip_val_std * 0.01
    risk_50     = pip_val_001 * 50

    result["tick_value"]            = round(tick_value, 6)
    result["tick_size"]             = round(tick_size, 6)
    result["pip_value_001_lot"]     = round(pip_val_001, 6)
    result["risk_50_pips"]          = round(risk_50, 4)
    result["trades_per_day_at_133usd"] = int(133 / risk_50) if risk_50 > 0 else None

    if abs(pip_val_001 - 0.10) < 0.02:
        result["status"]   = "PASS"
        result["scenario"] = "A"
        result["action"]   = "Plano actual OK — Lote 0.01 correcto. ~26 perdas antes do limite diário de $133."
    elif abs(pip_val_001 - 1.00) < 0.15:
        result["status"]   = "RECALIBRATE"
        result["scenario"] = "B"
        result["action"]   = "RECALIBRAR URGENTE — Reduzir lote para 0.001. Com 0.001 lote: 50 pips = $0.50 risco/trade."
    else:
        lote_ideal = round(5.0 / risk_50 * 0.01, 4) if risk_50 > 0 else None
        result["status"]   = "ATYPICAL"
        result["scenario"] = "C"
        result["action"]   = f"Valor atípico — Lote ideal para $5/50pips: {lote_ideal}. Rever plano de risco completo."
        result["ideal_lot_for_5usd_risk"] = lote_ideal

    mt5.shutdown()
    return result


def print_report(r: dict) -> None:
    """Imprime relatório formatado na consola."""
    sep = "=" * 55
    print(sep)
    print("  PIP VALUE XAUUSD — GATE 0 VERIFICAÇÃO")
    print(sep)
    print(f"  Timestamp UTC       : {r['timestamp_utc']}")
    print(f"  Tick value (1 lote) : ${r['tick_value']:.6f}")
    print(f"  Tick size           : {r['tick_size']:.6f}")
    print(f"  Pip size (ref.)     : {r['pip_size']:.2f}")
    print(f"  Pip value 0.01 lote : ${r['pip_value_001_lot']:.6f} por pip")
    print(f"  Risco 50 pips       : ${r['risk_50_pips']:.4f}")
    if r['trades_per_day_at_133usd']:
        print(f"  Trades/dia ($133)   : {r['trades_per_day_at_133usd']}")
    print()

    icons = {"PASS": "✅", "RECALIBRATE": "🔴", "ATYPICAL": "⚠️", "FAIL": "❌"}
    print(f"  {icons.get(r['status'], '?')} CENÁRIO {r.get('scenario', '—')} — {r['status']}")
    print(f"  → {r['action']}")
    print()
    print(f"  Resultado guardado em: {LOG_FILE}")
    print(sep)


if __name__ == "__main__":
    result = run_pip_verification()

    # Guardar em JSON para dossiê de auditoria (acrescenta ao log existente)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"AVISO: Não foi possível escrever {LOG_FILE}: {e}")

    print_report(result)

    # Exit code: 0 = OK, 1 = requer acção
    import sys
    sys.exit(0 if result["status"] == "PASS" else 1)
