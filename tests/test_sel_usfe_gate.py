from core_engines.sel_usfe_gate import evaluate_sel_usfe_gate, sel_usfe_enforcement_active


def test_enforcement_off_by_skip(monkeypatch):
    monkeypatch.setenv("OMEGA_SKIP_SEL_USFE_ENFORCE", "1")
    monkeypatch.setenv("OMEGA_ENFORCE_SEL_USFE_GATE", "1")
    ok, st, _ = evaluate_sel_usfe_gate(sel_audit_veto=True, usfe_bias="BLOCK")
    assert ok is True


def test_sel_veto_blocks_when_enabled(monkeypatch):
    monkeypatch.delenv("OMEGA_SKIP_SEL_USFE_ENFORCE", raising=False)
    monkeypatch.setenv("OMEGA_ENFORCE_SEL_USFE_GATE", "1")
    monkeypatch.setenv("OMEGA_SEL_ENABLED", "1")
    monkeypatch.setenv("OMEGA_USFE_BLOCK", "0")
    ok, st, msg = evaluate_sel_usfe_gate(sel_audit_veto=True, usfe_bias="NEUTRAL")
    assert ok is False
    assert st == "SKIP_SEL_AUDIT_VETO"


def test_usfe_block_when_switch_on(monkeypatch):
    monkeypatch.delenv("OMEGA_SKIP_SEL_USFE_ENFORCE", raising=False)
    monkeypatch.setenv("OMEGA_ENFORCE_SEL_USFE_GATE", "1")
    monkeypatch.setenv("OMEGA_SEL_ENABLED", "1")
    monkeypatch.setenv("OMEGA_USFE_BLOCK", "1")
    ok, st, _ = evaluate_sel_usfe_gate(sel_audit_veto=False, usfe_bias="BLOCK")
    assert ok is False
    assert st == "SKIP_USFE_BIAS_BLOCK"
