#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bias_audit.py (v2.0 tier0)
- Detecta viés BUY/SELL (Wilson + p-value).
- Lista ativos liberados (trade_mode FULL) e bloqueados.
- Checa regime/janelas (TRADICIONAL/HUNTER/NIGHT_PASS).
- Integra validadores CQO (crisis prob., SLO RTT).
- Gera SHA3-256 e integra audit trail.
"""
import os, json, hashlib
from datetime import datetime
from collections import defaultdict
import numpy as np
from scipy import stats
from pathlib import Path
try:
    import MetaTrader5 as mt5
except ImportError:
    print("[FALHA] MetaTrader5 não instalado. Instale com: python -m pip install MetaTrader5")
    raise SystemExit(1)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# ---------------- Regime / janela ----------------
def regime_windows():
    regime = os.getenv("OMEGA_REGIME", "TRADICIONAL").lower()
    night_pass = os.getenv("OMEGA_NIGHT_PASS", "").upper() == "AUTHORISED_BY_CEO"
    if night_pass:
        return "NIGHT_PASS", [(0, 24)]
    if regime == "hunter":
        return "HUNTER", [(0, 8), (17, 23)]
    return "TRADICIONAL", [(0, 24)]


def in_window(windows):
    h = datetime.now().hour
    return any(start <= h < end for start, end in windows), h


# ---------------- Símbolos liberados/bloqueados ----------------
def symbol_status():
    allowed, blocked = [], []
    symbols = mt5.symbols_get()
    for s in symbols:
        if s.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
            allowed.append(s.name)
        else:
            blocked.append(s.name)
    return allowed, blocked


# ---------------- Bias bruto ----------------
def bias_report():
    buys = defaultdict(int)
    sells = defaultdict(int)
    positions = mt5.positions_get()
    if positions:
        for p in positions:
            if p.type == mt5.POSITION_TYPE_BUY:
                buys[p.symbol] += 1
            elif p.type == mt5.POSITION_TYPE_SELL:
                sells[p.symbol] += 1
    orders = mt5.orders_get()
    if orders:
        for o in orders:
            if o.type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_LIMIT,
                          mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_BUY_STOP_LIMIT):
                buys[o.symbol] += 1
            elif o.type in (mt5.ORDER_TYPE_SELL, mt5.ORDER_TYPE_SELL_LIMIT,
                            mt5.ORDER_TYPE_SELL_STOP, mt5.ORDER_TYPE_SELL_STOP_LIMIT):
                sells[o.symbol] += 1
    report = []
    symbols = set(list(buys.keys()) + list(sells.keys()))
    for sym in sorted(symbols):
        b, s = buys[sym], sells[sym]
        bias = "NEUTRO"
        if b > 0 and s == 0:
            bias = "SOMENTE_BUY"
        elif s > 0 and b == 0:
            bias = "SOMENTE_SELL"
        report.append({"symbol": sym, "buy": b, "sell": s, "bias": bias})
    return report


# ---------------- Validação estatística (Wilson + p-value) ----------------
def validate_bias_statistical_significance(bias_report, confidence_level=0.95):
    z_score = stats.norm.ppf((1 + confidence_level) / 2)
    validated = []
    for item in bias_report:
        n = item['buy'] + item['sell']
        if n == 0:
            item['statistical_validation'] = {
                'significant': False,
                'reason': 'No trades observed',
                'wilson_ci_95': None,
                'p_value': None,
                'bias_classification': 'NOT_SIGNIFICANT'
            }
            validated.append(item)
            continue
        p_buy = item['buy'] / n
        denominator = 1 + z_score**2 / n
        center = (p_buy + z_score**2 / (2*n)) / denominator
        margin = z_score * np.sqrt((p_buy*(1-p_buy) + z_score**2/(4*n)) / n) / denominator
        wilson_lower = max(0, center - margin)
        wilson_upper = min(1, center + margin)
        expected_p = 0.5
        se = np.sqrt(expected_p * (1 - expected_p) / n) if n > 0 else 0
        z_stat = (p_buy - expected_p) / se if se > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        is_significant = (p_value < 0.05) and (wilson_lower > 0.5 or wilson_upper < 0.5)
        if is_significant:
            bias_class = 'SIGNIFICANT_BUY_BIAS' if p_buy > 0.5 else 'SIGNIFICANT_SELL_BIAS'
        else:
            bias_class = 'NOT_SIGNIFICANT'
        item['statistical_validation'] = {
            'total_trades': n,
            'buy_proportion': round(p_buy, 4),
            'wilson_ci_95': [round(wilson_lower, 4), round(wilson_upper, 4)],
            'z_statistic': round(z_stat, 4),
            'p_value': round(p_value, 6),
            'significant': is_significant,
            'bias_classification': bias_class,
            'expected_under_null': 0.5
        }
        validated.append(item)
    return validated


# ---------------- Validadores CQO ----------------
def validate_with_cqo_validators():
    validators_status = {}
    # Crisis Probability — inputs from config/market_data.json (V3 fix)
    try:
        from modules.validation.crisis_probability_validator import CrisisProbabilityValidator
        mkt_cfg_path = Path("./config/market_data.json")
        if mkt_cfg_path.exists():
            with open(mkt_cfg_path, "r", encoding="utf-8") as f:
                mkt = json.load(f)
        else:
            mkt = {"DXY_change_pct": -2.0, "XAU_change_pct": 12.3,
                   "Buffett_cash_B": 325.0, "BlackRock_equities_change_pct": -8.2}
        crisis_v = CrisisProbabilityValidator()
        crisis_r = crisis_v.calculate(
            DXY=mkt["DXY_change_pct"],
            XAU_change_pct=mkt["XAU_change_pct"],
            Buffett_cash_B=mkt["Buffett_cash_B"],
            BlackRock_equities_change_pct=mkt["BlackRock_equities_change_pct"])
        validators_status['crisis_probability'] = {
            'status': 'PASS' if crisis_r['probability'] >= 0.70 else 'FAIL',
            'value': crisis_r['probability'],
            'risk_level': crisis_r.get('risk_level', '?'),
            'ci_95': [crisis_r.get('ci_95_lower'), crisis_r.get('ci_95_upper')],
            'threshold': 0.70,
            'inputs': mkt,
        }
    except Exception as e:
        validators_status['crisis_probability'] = {'status': 'ERROR', 'error': str(e)}
    # SLO Validator (RTT)
    try:
        from modules.validation.slo_validator_china import RegimeSLOValidatorChinaCouncil
        slo_v = RegimeSLOValidatorChinaCouncil()
        import time
        t0 = time.perf_counter()
        mt5.symbol_info('XAUUSD')
        rtt_ms = (time.perf_counter() - t0) * 1000
        slo_r = slo_v.validate(decision_timescale_sec=2.0, measured_rtt_ms=rtt_ms)
        validators_status['slo_validator'] = {
            'status': 'PASS' if slo_r['overall_adequate'] else 'FAIL',
            'rtt_ms': round(rtt_ms, 2),
            'adequate': slo_r['overall_adequate']
        }
    except Exception as e:
        validators_status['slo_validator'] = {'status': 'ERROR', 'error': str(e)}
    return validators_status


# ---------------- Alertas quantificados ----------------
def generate_bias_alerts(bias_validated, thresholds=None):
    if thresholds is None:
        thresholds = {
            'significant_bias_symbols_max': 3,
            'buy_sell_ratio_warning': 2.0,
            'buy_sell_ratio_critical': 5.0,
            'concentration_warning': 0.50,
            'concentration_critical': 0.80,
        }
    alerts = []
    significant_bias_symbols = [
        item for item in bias_validated
        if item.get('statistical_validation', {}).get('significant', False)
    ]
    if len(significant_bias_symbols) > thresholds['significant_bias_symbols_max']:
        alerts.append({
            'severity': 'CRITICAL',
            'type': 'EXCESSIVE_SIGNIFICANT_BIAS',
            'message': f"{len(significant_bias_symbols)} símbolos com bias significativo "
                       f"(max: {thresholds['significant_bias_symbols_max']})",
            'symbols': [item['symbol'] for item in significant_bias_symbols]
        })
    total_buys = sum(item['buy'] for item in bias_validated)
    total_sells = sum(item['sell'] for item in bias_validated)
    if total_sells > 0:
        buy_sell_ratio = total_buys / total_sells
        if buy_sell_ratio >= thresholds['buy_sell_ratio_critical']:
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'EXTREME_BUY_SELL_RATIO',
                'message': f"Ratio BUY/SELL = {buy_sell_ratio:.2f} "
                           f"(critical: {thresholds['buy_sell_ratio_critical']})",
                'value': buy_sell_ratio
            })
        elif buy_sell_ratio >= thresholds['buy_sell_ratio_warning']:
            alerts.append({
                'severity': 'WARNING',
                'type': 'ELEVATED_BUY_SELL_RATIO',
                'message': f"Ratio BUY/SELL = {buy_sell_ratio:.2f} "
                           f"(warning: {thresholds['buy_sell_ratio_warning']})",
                'value': buy_sell_ratio
            })
    total_trades = total_buys + total_sells
    if total_trades > 0:
        for item in bias_validated:
            symbol_trades = item['buy'] + item['sell']
            concentration = symbol_trades / total_trades
            if concentration >= thresholds['concentration_critical']:
                alerts.append({
                    'severity': 'CRITICAL',
                    'type': 'EXCESSIVE_CONCENTRATION',
                    'message': f"{item['symbol']} concentra {concentration*100:.1f}% dos trades "
                               f"(critical: {thresholds['concentration_critical']*100}%)",
                    'symbol': item['symbol'],
                    'concentration': concentration
                })
            elif concentration >= thresholds['concentration_warning']:
                alerts.append({
                    'severity': 'WARNING',
                    'type': 'ELEVATED_CONCENTRATION',
                    'message': f"{item['symbol']} concentra {concentration*100:.1f}% dos trades "
                               f"(warning: {thresholds['concentration_warning']*100}%)",
                    'symbol': item['symbol'],
                    'concentration': concentration
                })
    return alerts


# ---------------- Audit trail (logs/manifest) ----------------
def integrate_with_audit_trail(output):
    audit_dir = Path("./logs/bias_audit")
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_id = f"BIAS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    output['audit_id'] = audit_id
    output_file = audit_dir / f"{audit_id}.json"
    checksum_file = audit_dir / f"{audit_id}.sha3"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    with open(checksum_file, 'w', encoding='utf-8') as f:
        f.write(output['audit_trail']['sha3_256'])
    manifest_path = Path("./logs/manifest.json")
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            if 'bias_audits' not in manifest:
                manifest['bias_audits'] = []
            manifest['bias_audits'].append({
                'audit_id': audit_id,
                'timestamp': output['timestamp'],
                'sha3_256': output['audit_trail']['sha3_256'],
                'alerts_count': len(output.get('alerts', [])),
                'significant_bias_count': len([
                    item for item in output.get('bias_report', [])
                    if item.get('statistical_validation', {}).get('significant', False)
                ])
            })
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
            output['audit_integration'] = {
                'manifest_updated': True,
                'manifest_path': str(manifest_path)
            }
        except Exception as e:
            output['audit_integration'] = {
                'manifest_updated': False,
                'error': str(e)
            }
    output['audit_files'] = {
        'output_json': str(output_file),
        'checksum_sha3': str(checksum_file)
    }
    return output


# ---------------- Main ----------------
def main():
    if not mt5.initialize():
        print("[FALHA] MT5 não inicializou:", mt5.last_error())
        return

    regime, windows = regime_windows()
    ok, hora = in_window(windows)
    allowed, blocked = symbol_status()
    bias = bias_report()
    bias_validated = validate_bias_statistical_significance(bias)
    alerts = generate_bias_alerts(bias_validated)
    validators = validate_with_cqo_validators()

    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "regime": regime,
        "windows": windows,
        "hora_atual": hora,
        "em_janela": ok,
        "symbols_allowed_count": len(allowed),
        "symbols_blocked_count": len(blocked),
        "bias_report": bias_validated,
        "alerts": alerts,
        "cqo_validators": validators,
        "audit_trail": {
            "sha3_256": None,
            "version": "bias_audit_v2.0_tier0",
            "validator": "PSA-WIND + CQO"
        }
    }

    # SHA3-256 (custom encoder for numpy types)
    output_json = json.dumps(output, sort_keys=True, ensure_ascii=False, cls=NumpyEncoder)
    output['audit_trail']['sha3_256'] = hashlib.sha3_256(output_json.encode('utf-8')).hexdigest()

    # Integrar audit trail
    output = integrate_with_audit_trail(output)

    # Print final
    print(json.dumps(output, indent=2, ensure_ascii=False, cls=NumpyEncoder))
    print(f"\n[OK] Checksum SHA3-256: {output['audit_trail']['sha3_256'][:16]}...")

    mt5.shutdown()


if __name__ == "__main__":
    main()
