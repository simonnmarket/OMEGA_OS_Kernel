"""
P0-ABC 20260522 — Teste runner só v1 (T-P2b)
Verifica que omega_paper_loop_24x7.py não referencia shadow_loop_v2.py
"""
import re
from pathlib import Path


def test_runner_targets_v1_only():
    """T-P2b: runner só v1; v2 bloqueado"""
    runner_file = Path("scripts/omega_paper_loop_24x7.py")
    
    if not runner_file.exists():
        pytest.skip("runner file not found")
    
    content = runner_file.read_text(encoding="utf-8", errors="replace")
    
    # Verificar que não referencia shadow_loop_v2
    assert "shadow_loop_v2" not in content, "Runner não deve referenciar shadow_loop_v2"
    
    # Verificar que referencia shadow_loop.py (v1)
    assert "shadow_loop.py" in content or "shadow_loop" in content, "Runner deve referenciar shadow_loop v1"
    
    # Verificar PS1 comment
    ps1_file = Path("scripts/run_omega_madrugada_pos_p0.ps1")
    if ps1_file.exists():
        ps1_content = ps1_file.read_text(encoding="utf-8", errors="replace")
        assert "OMEGA_USE_V2=0" in ps1_content or "PROIBIDO" in ps1_content, "PS1 deve ter comment proibindo v2"


if __name__ == "__main__":
    test_runner_targets_v1_only()
    print("T-P2b: PASS")
