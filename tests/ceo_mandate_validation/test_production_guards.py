"""
OMEGA v4.0 — Production Guards Test Suite
==========================================
CEO Mandate 2026-05-26 | Blindagem pós-PSA

Estes testes falham IMEDIATAMENTE se os dois erros críticos corrigidos
voltarem a ser introduzidos no codebase, por qualquer razão:

  GUARD-1: RiskBudgetManager.update_atr() nunca aceita valores não-pontos MT5
           (price_diff, margem USD, zero, negativos)

  GUARD-2: _GLOBAL_QUEUE nunca é importado fora de async_position_orchestrator.py
           (evita injecção de sinais falsos na fila de produção)

  GUARD-3: shadow_loop.py nunca usa margin_used como proxy de ATR para update_atr()

  GUARD-4: dedup_signals() é função pura — mesmo input produz sempre mesmo output,
           sem acesso a estado global

Os testes são intencionalmente simples e rápidos (< 0.5s total).
Se algum falhar: STOP. Nao continuar para produção.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

# Raiz do projecto
_ROOT = Path(__file__).resolve().parent.parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# GUARD-1: update_atr() rejeita valores que não são pontos MT5
# ─────────────────────────────────────────────────────────────────────────────

class TestAtrUnitGuard:
    """
    Garante que RiskBudgetManager.update_atr() rejeita qualquer valor
    que claramente não é ATR em pontos MT5.

    Se este teste falhar: alguém removeu a validação de unidades de
    risk_budget.py. Restaurar imediatamente _ATR_GUARD_MIN_POINTS e a
    lógica de raise ValueError.
    """

    def _make_mgr(self):
        from core_engines.risk_budget import RiskBudgetManager, RiskBudgetConfig
        return RiskBudgetManager(cfg=RiskBudgetConfig(
            max_drawdown_pct=0.02,
            risk_per_position_pct=0.005,
            default_lot=0.10,
            hard_cap=8,
        ))

    def test_rejects_zero(self):
        """ATR = 0 é impossível — deve levantar ValueError."""
        mgr = self._make_mgr()
        with pytest.raises(ValueError, match="PONTOS MT5"):
            mgr.update_atr("EURUSD", 0.0)

    def test_rejects_negative(self):
        """ATR negativo não tem sentido físico."""
        mgr = self._make_mgr()
        with pytest.raises(ValueError, match="PONTOS MT5"):
            mgr.update_atr("EURUSD", -100.0)

    def test_rejects_price_diff_eurusd(self):
        """
        0.005 é price_diff (5 pips) para EURUSD, nunca ATR em pontos.
        ATR correcto seria 500.0 pts.
        """
        mgr = self._make_mgr()
        with pytest.raises(ValueError, match="PONTOS MT5"):
            mgr.update_atr("EURUSD", 0.005)

    def test_rejects_price_diff_xauusd(self):
        """
        2.5 como price_diff de XAUUSD é plausível, mas como ATR em pontos
        seria absurdamente pequeno (XAUUSD ATR real >= 1500 pts).
        Abaixo de _ATR_GUARD_MIN_POINTS=1.0 deve ser rejeitado.
        """
        mgr = self._make_mgr()
        with pytest.raises(ValueError, match="PONTOS MT5"):
            mgr.update_atr("XAUUSD", 0.5)

    def test_accepts_valid_eurusd_atr(self):
        """500 pontos é ATR realista para EURUSD 5-decimal — deve aceitar."""
        mgr = self._make_mgr()
        mgr.update_atr("EURUSD", 500.0)   # sem excepção

    def test_accepts_valid_xauusd_atr(self):
        """2000 pontos é ATR realista para XAUUSD — deve aceitar."""
        mgr = self._make_mgr()
        mgr.update_atr("XAUUSD", 2000.0)  # sem excepção

    def test_accepts_valid_us500_atr(self):
        """1500 pontos é ATR realista para US500 — deve aceitar."""
        mgr = self._make_mgr()
        mgr.update_atr("US500", 1500.0)   # sem excepção

    def test_cache_populated_only_on_valid(self):
        """Cache só deve ser actualizado quando o valor é válido."""
        from core_engines.risk_budget import RiskBudgetManager
        mgr = RiskBudgetManager()
        # tentativas inválidas não devem poluir o cache
        for bad in [0.0, -1.0, 0.001]:
            try:
                mgr.update_atr("GBPUSD", bad)
            except ValueError:
                pass
        assert "GBPUSD" not in mgr._atr_cache, (
            "Cache foi populado com valores invalidos — guard falhou"
        )
        # valor válido deve popular o cache
        mgr.update_atr("GBPUSD", 700.0)
        assert "GBPUSD" in mgr._atr_cache
        assert mgr._atr_cache["GBPUSD"] == [700.0]


# ─────────────────────────────────────────────────────────────────────────────
# GUARD-2: _GLOBAL_QUEUE nunca importado fora do orchestrador
# ─────────────────────────────────────────────────────────────────────────────

class TestGlobalQueueEncapsulation:
    """
    Garante que nenhum ficheiro Python fora de async_position_orchestrator.py
    importa _GLOBAL_QUEUE directamente.

    Se este teste falhar: um ficheiro está a aceder à fila de produção e pode
    injectar sinais falsos que disparam fechamentos de posições reais.
    Remover imediatamente o import e usar dedup_signals() ou drain_fastloop_signals().
    """

    _ORCHESTRATOR = _ROOT / "core_engines" / "async_position_orchestrator.py"
    # Excluir ficheiros de testes (os guards vivem em código de produção),
    # o próprio orchestrador, backups e artefactos gerados.
    _SKIP_PATTERNS = ("BACKUP", "__pycache__", ".git", ".pytest_cache", "tests" + "/",
                      "tests" + "\\")
    # Apenas código de produção é varrido — directorias relevantes:
    _PROD_DIRS = ("core_engines", "modules", "scripts", "agent_ia")

    def _prod_py_files(self):
        """Itera apenas ficheiros de produção (exclui testes e backups)."""
        for prod_dir in self._PROD_DIRS:
            d = _ROOT / prod_dir
            if not d.exists():
                continue
            for f in d.rglob("*.py"):
                if f.resolve() == self._ORCHESTRATOR.resolve():
                    continue
                if any(p in str(f) for p in self._SKIP_PATTERNS):
                    continue
                yield f

    def test_no_direct_import_of_global_queue(self):
        """
        Nenhum ficheiro de PRODUCAO (core_engines/, modules/, scripts/, agent_ia/)
        excepto o próprio orchestrador deve conter '_GLOBAL_QUEUE' no seu texto.

        Ficheiros de teste são excluídos desta verificação — o risco real é
        código de produção que injecta na fila e dispara ordens reais.
        Para testes, usar dedup_signals() (função pura).
        """
        violations: list = []
        for py_file in self._prod_py_files():
            try:
                src = py_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "_GLOBAL_QUEUE" in src:
                violations.append(str(py_file.relative_to(_ROOT)))

        assert not violations, (
            "GUARD-2 FAIL: acesso directo a _GLOBAL_QUEUE em codigo de producao.\n"
            "Ficheiros em violacao:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nNo shadow_loop use drain_fastloop_signals()."
            "\nEm testes use dedup_signals() (funcao pura, zero estado global)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GUARD-3: shadow_loop.py nunca usa margin_used como ATR
# ─────────────────────────────────────────────────────────────────────────────

class TestNoMarginUsedAsAtr:
    """
    Garante que shadow_loop.py não passa margin_used (margem USD) como argumento
    de update_atr() (que espera PONTOS MT5).

    Se este teste falhar: o erro crítico de unidade foi re-introduzido.
    Corrigir imediatamente usando get_execution_tf_atr(asset, tf)["atr_pts"].
    """

    _SHADOW_LOOP = _ROOT / "core_engines" / "shadow_loop.py"
    # Padrão: qualquer chamada a update_atr que contenha margin_used no argumento
    _FORBIDDEN_PATTERN = re.compile(
        r"update_atr\s*\([^)]*margin_used[^)]*\)",
        re.DOTALL,
    )

    def test_margin_used_not_passed_to_update_atr(self):
        """
        Detecta o padrão proibido: update_atr(...margin_used...) em shadow_loop.py.
        """
        src = self._SHADOW_LOOP.read_text(encoding="utf-8", errors="replace")
        match = self._FORBIDDEN_PATTERN.search(src)
        assert match is None, (
            "GUARD-3 FAIL: margin_used passado como ATR em update_atr().\n"
            f"Trecho proibido encontrado:\n  {match.group(0)}\n\n"
            "margin_used e margem USD, nao ATR em pontos MT5.\n"
            "Correccao: use get_execution_tf_atr(asset, tf)[\"atr_pts\"]."
        )

    def test_no_guard_bypass_via_getenv(self):
        """
        Garante que update_atr não é chamado com os.getenv ou env vars como ATR.
        (padrão: update_atr(...os.getenv...) que contornaria o guard de tipo)
        """
        src = self._SHADOW_LOOP.read_text(encoding="utf-8", errors="replace")
        bad_pattern = re.compile(
            r"update_atr\s*\([^)]*os\.getenv[^)]*\)",
            re.DOTALL,
        )
        match = bad_pattern.search(src)
        assert match is None, (
            "GUARD-3b FAIL: os.getenv passado directamente como ATR em update_atr().\n"
            f"Trecho: {match.group(0)}\n"
            "Env vars sao strings/floats arbitrarios, nao ATR em pontos validado."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GUARD-4: dedup_signals() é função pura
# ─────────────────────────────────────────────────────────────────────────────

class TestDedupSignalsPurity:
    """
    Garante que dedup_signals() é uma função pura:
      - Mesmo input → mesmo output (determinístico)
      - Não modifica a lista de input
      - Não acede a _GLOBAL_QUEUE nem a qualquer estado global
    """

    def _make_signals(self):
        from core_engines.async_position_orchestrator import FastLoopSignal
        return [
            FastLoopSignal(ticket=100, symbol="EURUSD", action="CLOSE_PARTIAL",
                           reason="PEAK_PARTIAL", points_context=300.0, partial_pct=0.5),
            FastLoopSignal(ticket=100, symbol="EURUSD", action="CLOSE_FULL",
                           reason="PEAK_DRAWDOWN", points_context=250.0, partial_pct=1.0),
            FastLoopSignal(ticket=200, symbol="XAUUSD", action="CLOSE_FULL",
                           reason="AI_REVERSAL", points_context=1200.0),
        ]

    def test_idempotent(self):
        """Chamadas repetidas com o mesmo input produzem output idêntico."""
        from core_engines.async_position_orchestrator import dedup_signals
        raw = self._make_signals()
        result_1 = dedup_signals(list(raw))
        result_2 = dedup_signals(list(raw))
        assert [(s.ticket, s.action) for s in result_1] == \
               [(s.ticket, s.action) for s in result_2]

    def test_does_not_mutate_input(self):
        """dedup_signals não deve modificar a lista recebida."""
        from core_engines.async_position_orchestrator import dedup_signals
        raw = self._make_signals()
        original_len = len(raw)
        original_actions = [s.action for s in raw]
        dedup_signals(raw)
        assert len(raw) == original_len, "dedup_signals modificou o tamanho da lista input"
        assert [s.action for s in raw] == original_actions, "dedup_signals modificou elementos do input"

    def test_close_full_wins(self):
        """CLOSE_FULL deve sempre vencer CLOSE_PARTIAL para o mesmo ticket."""
        from core_engines.async_position_orchestrator import dedup_signals, FastLoopSignal
        # Ordem: primeiro CLOSE_PARTIAL, depois CLOSE_FULL
        raw = [
            FastLoopSignal(ticket=42, symbol="GBPUSD", action="CLOSE_PARTIAL",
                           reason="R1", points_context=100.0, partial_pct=0.5),
            FastLoopSignal(ticket=42, symbol="GBPUSD", action="CLOSE_FULL",
                           reason="R2", points_context=80.0),
        ]
        result = dedup_signals(raw)
        assert len(result) == 1
        assert result[0].action == "CLOSE_FULL"

    def test_close_full_wins_regardless_of_order(self):
        """Mesmo se CLOSE_FULL vier primeiro, resultado deve ser CLOSE_FULL."""
        from core_engines.async_position_orchestrator import dedup_signals, FastLoopSignal
        raw = [
            FastLoopSignal(ticket=42, symbol="GBPUSD", action="CLOSE_FULL",
                           reason="R1", points_context=100.0),
            FastLoopSignal(ticket=42, symbol="GBPUSD", action="CLOSE_PARTIAL",
                           reason="R2", points_context=80.0, partial_pct=0.5),
        ]
        result = dedup_signals(raw)
        assert len(result) == 1
        assert result[0].action == "CLOSE_FULL"

    def test_empty_input(self):
        """Lista vazia deve retornar lista vazia, sem excepção."""
        from core_engines.async_position_orchestrator import dedup_signals
        assert dedup_signals([]) == []

    def test_no_global_queue_access(self):
        """
        Verifica estaticamente que dedup_signals() não referencia _GLOBAL_QUEUE.
        Análise AST do source do módulo.
        """
        orchestrator_path = _ROOT / "core_engines" / "async_position_orchestrator.py"
        src = orchestrator_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)

        # Encontrar a função dedup_signals
        dedup_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "dedup_signals":
                dedup_func = node
                break

        assert dedup_func is not None, "dedup_signals nao encontrada no modulo"

        # Verificar que dentro da função não há acesso a _GLOBAL_QUEUE
        func_src_lines = src.split("\n")[dedup_func.lineno - 1: dedup_func.end_lineno]
        func_src = "\n".join(func_src_lines)
        assert "_GLOBAL_QUEUE" not in func_src, (
            "GUARD-4 FAIL: dedup_signals() acede a _GLOBAL_QUEUE — deixou de ser pura.\n"
            "Qualquer acesso a estado global contamina a funcao e invalida o isolamento de testes."
        )
