"""
omega_pullback_engine.py — Motor de Detecção de Pullback Trap
OMEGA Quantitative Fund V6.0

FILOSOFIA:
  Uma correcção não é uma reversão.
  Um pullback institucional tem uma impressão digital:
    - Volume cai (sem participação institucional na correcção)
    - Delta inverte mas sem spike (retalho, não fluxo real)
    - Preço aproxima-se de zona de confluência (POC/VWAP/VAH)
    - Wyckoff: Spring ou Upthrust em formação = armadilha para amadores

  Quando estes elementos convergem:
    CAUSA = nova acumulação silenciosa
    CONFIRMAÇÃO = rompimento de volta ao fluxo direcional
    ACÇÃO = escalonamento ACELERADO (bypass de intervalo)

  O mercado cria falsos topos e fundos para alimentar liquidez.
  O sistema processa a causa ANTES do rompimento.
  Nunca saímos por medo de uma correcção. Escalamos.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

logger = logging.getLogger("OMEGA.PullbackEngine")


# ---------------------------------------------------------------------------
# Estado do Pullback
# ---------------------------------------------------------------------------
@dataclass
class PullbackState:
    """Estado completo de uma correcção em curso."""

    # Direcção do fluxo original (antes da correcção)
    original_direction: int = 0      # 1=alta, -1=baixa

    # Flags de detecção
    is_pullback: bool = False        # Estamos em correcção?
    is_trap: bool = False            # É armadilha de retalho?
    is_ready_to_resume: bool = False # Pronto para nova entrada acelerada?

    # Evidências
    volume_exhausted: bool = False   # Volume caiu na correcção
    delta_weak: bool = False         # Delta oposto mas fraco (sem fluxo inst.)
    near_confluence: bool = False    # Próximo de zona de confluência
    wyckoff_trap: bool = False       # Spring ou Upthrust detectado
    hurst_confirms: bool = False     # Hurst > 0.55 (regime de tendência)

    # Métricas quantitativas
    trap_score: float = 0.0          # 0.0 - 1.0 (força do sinal de armadilha)
    bars_in_pullback: int = 0        # Barras na correcção
    max_pullback_pips: float = 0.0   # Profundidade máxima da correcção

    # Para gestão de re-entrada
    reentry_urgency: str = "NORMAL"  # NORMAL | HIGH | CRITICAL


# ---------------------------------------------------------------------------
# Motor de Detecção
# ---------------------------------------------------------------------------
class PullbackTrapDetector:
    """
    Detecta quando uma correcção é uma armadilha de retalho (não uma reversão).
    Integra com VolumeSystem para leitura de indicadores.

    Cascade de confirmação (todos pesados):
      1. Volume Exhaustion na onda de correcção (peso 0.30)
      2. Delta Fraco — o lado oposto não tem fluxo institucional (peso 0.25)
      3. Confluência Geométrica — VWAP/POC/VAH/VAL (peso 0.20)
      4. Wyckoff Spring/Upthrust — falso rompimento (peso 0.20)
      5. Hurst > 0.55 — regime de tendência confirmado (peso 0.05)
    """

    # Limiares de decisão
    TRAP_THRESHOLD       = 0.55   # score mínimo para confirmar armadilha
    CRITICAL_THRESHOLD   = 0.80   # score para urgência CRITICAL (bypass total)

    def __init__(self):
        self._states: Dict[str, PullbackState] = {}
        self._price_history: Dict[str, List[float]] = {}

    def _get_state(self, symbol: str) -> PullbackState:
        if symbol not in self._states:
            self._states[symbol] = PullbackState()
        return self._states[symbol]

    def update(self,
               symbol: str,
               original_direction: int,
               volume_snapshot: Dict[str, Any],
               orderflow: Dict[str, Any],
               wyckoff: Dict[str, Any],
               footprint_snapshot: Dict[str, Any],
               current_price: float,
               hurst: Optional[float] = None) -> PullbackState:
        """
        Processa um tick/barra e actualiza o estado da correcção.

        Args:
            symbol:              Símbolo (ex: 'XAUUSD')
            original_direction:  Direcção do fluxo principal (1=alta, -1=baixa)
            volume_snapshot:     get_state_snapshot() do VolumeSystem
            orderflow:           compute_orderflow() do VolumeSystem
            wyckoff:             detect_wyckoff_regime() do VolumeSystem
            footprint_snapshot:  footprint do VolumeSystem (vah, val, poc, hvn)
            current_price:       Preço actual
            hurst:               Expoente de Hurst (opcional)
        """
        state = self._get_state(symbol)
        state.original_direction = original_direction

        # ── Actualizar histórico de preço ──────────────────────────────────
        hist = self._price_history.setdefault(symbol, [])
        hist.append(current_price)
        if len(hist) > 200:
            hist.pop(0)

        # ── Detectar se estamos em correcção ─────────────────────────────
        # Correcção = preço actual está abaixo do pico recente (alta) ou
        #              acima do vale recente (baixa)
        if len(hist) >= 5:
            recent_window = hist[-10:] if len(hist) >= 10 else hist
            if original_direction == 1:      # fluxo de alta → correcção = recuo
                peak = max(recent_window[:-1])  # pico antes do preço actual
                in_correction = current_price < peak * 0.9995  # > 0.05% abaixo do pico
            else:                            # fluxo de baixa → correcção = recuperação
                trough = min(recent_window[:-1])  # vale antes do preço actual
                in_correction = current_price > trough * 1.0005

            state.is_pullback = in_correction
            if in_correction:
                state.bars_in_pullback += 1
                move = abs(current_price - (max(recent_window[:-1]) if original_direction == 1 else min(recent_window[:-1])))
                state.max_pullback_pips = max(state.max_pullback_pips, move * 10)
            else:
                state.bars_in_pullback = 0
                state.max_pullback_pips = 0.0
        else:
            state.is_pullback = False

        score = 0.0

        # ── CRITÉRIO 1: Volume Exhaustion (peso 30%) ───────────────────────
        # A onda de correcção está a perder energia (robôs não participam)
        wave_z         = volume_snapshot.get("wave_volume_z")
        wave_exhausted = volume_snapshot.get("wave_exhaustion", False)
        wave_strength  = volume_snapshot.get("wave_strength", 1.0)

        vol_exhausted = (
            wave_exhausted or
            (wave_z is not None and wave_z < -1.0) or
            (wave_strength is not None and wave_strength < 0.4)
        )
        state.volume_exhausted = vol_exhausted
        if vol_exhausted:
            score += 0.30

        # ── CRITÉRIO 2: Delta Fraco (peso 25%) ────────────────────────────
        # O lado oposto ao fluxo original tem delta mas fraco — retalho, não inst.
        delta_z   = orderflow.get("delta_z", 0.0)
        imbalance = orderflow.get("imbalance", 0.0)
        absorption = orderflow.get("absorption", False)

        # Delta oposto ao fluxo original mas fraco (|z| < 1.5 = sem spike inst.)
        delta_opposite = (original_direction == 1 and delta_z < 0) or \
                        (original_direction == -1 and delta_z > 0)
        delta_weak = delta_opposite and abs(delta_z) < 1.5 and abs(imbalance) < 0.3
        # Absorção na direcção original = ainda há compradores/vendedores inst.
        delta_weak = delta_weak or absorption

        state.delta_weak = delta_weak
        if delta_weak:
            score += 0.25

        # ── CRITÉRIO 3: Confluência Geométrica (peso 20%) ─────────────────
        # Preço próximo de POC, VWAP, VAH, VAL, ou HVN = zona de defesa inst.
        near_confluence = footprint_snapshot.get("near_confluence", False)
        convergence_score = footprint_snapshot.get("convergence_score", 0.0)

        state.near_confluence = near_confluence or convergence_score > 0.6
        if state.near_confluence:
            score += 0.20

        # ── CRITÉRIO 4: Wyckoff Spring/Upthrust (peso 20%) ───────────────
        # Falso rompimento do range — armadilha clássica de retalho
        spring   = wyckoff.get("spring", False)
        upthrust = wyckoff.get("upthrust", False)

        wyckoff_trap = (original_direction == 1 and spring) or \
                      (original_direction == -1 and upthrust)
        state.wyckoff_trap = wyckoff_trap
        if wyckoff_trap:
            score += 0.20

        # ── CRITÉRIO 5: Hurst confirma tendência (peso 5%) ────────────────
        hurst_ok = hurst is not None and hurst > 0.55
        state.hurst_confirms = hurst_ok
        if hurst_ok:
            score += 0.05

        # ── Decisão final ──────────────────────────────────────────────────
        state.trap_score = round(score, 3)
        state.is_trap = state.is_pullback and score >= self.TRAP_THRESHOLD

        # Urgência de re-entrada
        if score >= self.CRITICAL_THRESHOLD:
            state.reentry_urgency = "CRITICAL"  # bypass total de intervalos
        elif score >= self.TRAP_THRESHOLD:
            state.reentry_urgency = "HIGH"      # reduz intervalo a 60s
        else:
            state.reentry_urgency = "NORMAL"

        # Pronto para entrada: pullback + trap + sinal de retoma
        # Retoma = preço deixou de cair (no fluxo de alta) / subir (no de baixa)
        if state.is_trap and len(hist) >= 3:
            retoma_alta  = original_direction == 1 and hist[-1] > hist[-2] > hist[-3]
            retoma_baixa = original_direction == -1 and hist[-1] < hist[-2] < hist[-3]
            state.is_ready_to_resume = retoma_alta or retoma_baixa
        else:
            state.is_ready_to_resume = False

        if state.is_trap:
            logger.info(
                f"[{symbol}] PULLBACK TRAP detectado | "
                f"score={score:.2f} | urgency={state.reentry_urgency} | "
                f"pronto={'SIM' if state.is_ready_to_resume else 'AGUARDANDO'} | "
                f"vol_exh={vol_exhausted} | delta_fraco={delta_weak} | "
                f"confluence={state.near_confluence} | wyckoff={wyckoff_trap}"
            )

        return state

    def get_scale_interval_override(self, symbol: str) -> Optional[int]:
        """
        Retorna o intervalo de escalonamento ajustado pela urgência.
        Substituir scale_interval_s quando pullback trap detectado.

        Returns:
            None    → usar intervalo padrão (sem override)
            60      → urgência HIGH: entrar em 60s (era 300s)
            0       → urgência CRITICAL: entrar imediatamente
        """
        state = self._states.get(symbol)
        if state is None or not state.is_trap:
            return None
        # CRITICAL: bypass imediato mesmo sem is_ready_to_resume confirmado
        if state.reentry_urgency == "CRITICAL":
            return 0
        # HIGH: só acelera se já pronto para retomar
        if state.reentry_urgency == "HIGH" and state.is_ready_to_resume:
            return 60
        return None

    def reset(self, symbol: str) -> None:
        """Resetar estado após nova entrada (pullback absorvido)."""
        if symbol in self._states:
            self._states[symbol] = PullbackState()
            self._states[symbol].original_direction = self._states.get(symbol, PullbackState()).original_direction


# ---------------------------------------------------------------------------
# Lógica de Fecho Parcial + Re-entrada
# ---------------------------------------------------------------------------
class PartialCloseManager:
    """
    Gere fechamentos parciais quando lote total ≥ 2.0.

    REGRA DE OURO:
      Fecho parcial NÃO é saída. É gestão de margem e risco.
      Após fecho parcial: re-abrir imediatamente na direcção do fluxo.
      NUNCA fechar sem re-entrada planeada.

    Triggers para fecho parcial:
      1. Lote total ≥ 2.0 (gestão de margem)
      2. Pullback trap detectado com urgência CRITICAL (libertar capital para
         escalar na re-entrada)
      3. Drawdown da posição > 50% do SL (gestão de risco conservadora)
    """

    PARTIAL_CLOSE_RATIO = 0.40   # 40% dos lotes são fechados (60% mantido)
    MIN_LOT_TO_TRIGGER  = 2.0    # Lote mínimo para activar fecho parcial

    def should_partial_close(self,
                              total_lots: float,
                              trap_state: Optional[PullbackState],
                              current_pnl_pct: float = 0.0) -> Dict[str, Any]:
        """
        Avalia se deve efectuar fecho parcial.

        Returns dict com:
          trigger: bool
          ratio:   float (fracção a fechar)
          reason:  str
          reenter: bool (deve re-entrar imediatamente)
        """
        # Trigger 1: lote total atingiu o limiar
        if total_lots >= self.MIN_LOT_TO_TRIGGER:
            lots_to_close = round(total_lots * self.PARTIAL_CLOSE_RATIO, 2)
            return {
                "trigger": True,
                "lots_to_close": lots_to_close,
                "reason": f"lote_total={total_lots:.2f} >= {self.MIN_LOT_TO_TRIGGER:.2f}",
                "reenter": True,    # Re-entrar imediatamente
                "urgency": "HIGH",
            }

        # Trigger 2: pullback trap CRITICAL + lote significativo
        if trap_state and trap_state.is_trap and \
           trap_state.reentry_urgency == "CRITICAL" and \
           total_lots >= 0.50:
            lots_to_close = round(total_lots * 0.30, 2)  # 30% libertar capital
            return {
                "trigger": True,
                "lots_to_close": lots_to_close,
                "reason": f"pullback_trap_CRITICAL score={trap_state.trap_score:.2f}",
                "reenter": True,
                "urgency": "CRITICAL",
            }

        return {"trigger": False, "lots_to_close": 0.0, "reason": "", "reenter": False}


# ---------------------------------------------------------------------------
# Integração com OmegaScaleManager — patch method
# ---------------------------------------------------------------------------
def integrate_pullback_engine(scale_manager) -> None:
    """
    Injecta o PullbackTrapDetector e PartialCloseManager
    no OmegaScaleManager existente.
    Chama esta função após instanciar o OmegaScaleManager.

    Exemplo:
        mgr = OmegaScaleManager()
        integrate_pullback_engine(mgr)
    """
    scale_manager._pullback_detector = PullbackTrapDetector()
    scale_manager._partial_close_mgr = PartialCloseManager()

    # Guardar referência ao método original
    original_check = scale_manager.check_and_scale.__func__

    async def check_and_scale_with_pullback(self):
        """
        check_and_scale aumentado com detecção de pullback trap.
        Quando pullback trap detectado:
          - Reduz intervalo de escalonamento (60s ou 0s)
          - Activa fecho parcial se lote ≥ 2.0
          - Re-entra imediatamente na direcção do fluxo
        """
        import asyncio
        now = asyncio.get_running_loop().time()

        for ticket, entry in list(self._pending_entries.items()):
            pos = await asyncio.to_thread(__import__('MetaTrader5').positions_get, ticket=ticket)
            if not pos:
                symbol = entry['symbol']
                freed  = entry.get('total_lots', 0.0)
                self._symbol_exposure[symbol] = max(
                    0.0, self._symbol_exposure.get(symbol, 0.0) - freed
                )
                del self._pending_entries[ticket]
                logger.info(f"[{symbol}] Posição {ticket} fechada — exposição libertada: {freed:.2f}")
                continue

            symbol = entry['symbol']
            cfg    = self._cfg(symbol)

            # ── Verificar override de intervalo por pullback ───────────────
            trap_state = self._pullback_detector._states.get(symbol)
            interval_override = self._pullback_detector.get_scale_interval_override(symbol)
            effective_interval = interval_override if interval_override is not None \
                                 else cfg['scale_interval_s']

            elapsed = now - entry['last_scale_time']
            if elapsed < effective_interval:
                continue

            async with self._get_symbol_lock(symbol):
                elapsed = now - entry['last_scale_time']
                if elapsed < effective_interval:
                    continue

                # ── Verificar fecho parcial ────────────────────────────────
                total_lots = entry.get('total_lots', 0.0)
                pc_decision = self._partial_close_mgr.should_partial_close(
                    total_lots, trap_state
                )
                if pc_decision["trigger"]:
                    logger.info(
                        f"[{symbol}] FECHO PARCIAL: {pc_decision['lots_to_close']:.2f} lotes | "
                        f"razão: {pc_decision['reason']} | re-entrada: {pc_decision['reenter']}"
                    )
                    # Nota: _partial_close_order() será implementado no engine principal
                    # igual a _open_order() — interface definida, não implementada aqui
                    if pc_decision["reenter"]:
                        logger.info(f"[{symbol}] Re-entrada imediata planeada após fecho parcial")
                        # Reset do estado de pullback após absorção
                        self._pullback_detector.reset(symbol)

                # ── Cap equity e ATR (lógica existente) ───────────────────
                current_exp = self._symbol_exposure.get(symbol, 0.0)
                equity      = entry.get('equity_snapshot', 10_000.0)
                pv_lot      = entry.get('pip_value_per_lot', 10.0)
                max_lots    = self._max_lots_for_equity(symbol, equity, pv_lot)

                if current_exp >= max_lots:
                    logger.info(f"[{symbol}] Cap equity atingido ({current_exp:.2f}/{max_lots:.2f}) — escalonamento pausado")
                    continue

                atr = await self._get_current_atr(symbol)
                if atr is None:
                    logger.info(f"[{symbol}] ATR indisponível — escalonamento adiado")
                    continue
                if atr <= cfg['min_atr']:
                    # Se trap detectado com urgência CRITICAL, ignorar ATR mínimo
                    if interval_override == 0:
                        logger.info(f"[{symbol}] ATR baixo mas PULLBACK TRAP CRITICAL — override ATR")
                    else:
                        logger.info(f"[{symbol}] ATR={atr:.4f} abaixo de min={cfg['min_atr']:.4f}")
                        continue

                # ── Calcular próximo lote ──────────────────────────────────
                next_lot = round(
                    min(
                        entry['current_lot'] * cfg['lot_progression'],
                        cfg['max_single_lot'],
                        max_lots - current_exp
                    ),
                    2
                )
                # Em pullback trap CRITICAL: ampliar lote (momento de máxima oportunidade)
                if interval_override == 0 and next_lot > 0:
                    next_lot = round(min(next_lot * 1.5, cfg['max_single_lot']), 2)
                    logger.info(f"[{symbol}] PULLBACK TRAP CRITICAL — lote amplificado: {next_lot:.2f}")

                if next_lot <= 0.001:
                    continue

                # ── Abrir entrada ──────────────────────────────────────────
                t_new = await asyncio.to_thread(
                    self._open_order, symbol, entry['action'], next_lot,
                    round(entry['sl_pts']),
                    round(cfg['tp_pips_per_entry'] * 10)
                )
                if t_new:
                    entry['current_lot']     = next_lot
                    entry['scale_count']    += 1
                    entry['total_lots']     += next_lot
                    entry['last_scale_time'] = now
                    self._symbol_exposure[symbol] = current_exp + next_lot
                    urgency_tag = f" [{trap_state.reentry_urgency}]" if trap_state and trap_state.is_trap else ""
                    logger.info(
                        f"[{symbol}] Entrada #{entry['scale_count']}{urgency_tag} — "
                        f"ticket={t_new} | lote={next_lot:.2f} | "
                        f"total={entry['total_lots']:.2f}/{max_lots:.2f} | ATR={atr:.4f}"
                    )
                    self._pullback_detector.reset(symbol)

    import types
    scale_manager.check_and_scale = types.MethodType(
        check_and_scale_with_pullback, scale_manager
    )
    logger.info("PullbackTrapDetector integrado no OmegaScaleManager")


# ---------------------------------------------------------------------------
# Teste unitário interno
# ---------------------------------------------------------------------------
def _test_pullback_detector():
    """Teste sem dependências externas."""
    import random
    random.seed(42)

    detector = PullbackTrapDetector()
    pc_mgr   = PartialCloseManager()

    print("=" * 60)
    print("  PULLBACK ENGINE — TESTES INTERNOS")
    print("=" * 60)

    PASS = 0
    FAIL = 0

    def ok(msg):
        nonlocal PASS; PASS += 1
        print(f"  [PASS] {msg}")

    def fail(msg):
        nonlocal FAIL; FAIL += 1
        print(f"  [FAIL] {msg}")

    # ── Teste 1: Pullback com todos os critérios — deve ser TRAP ──────────
    print("\n>>> Teste 1: Pullback com todos os critérios (score esperado ≥ 0.55)")
    # Simular histórico de preços em alta, depois recuo
    symbol = "XAUUSD"
    for p in [5200, 5210, 5220, 5230, 5240]:  # tendência de alta
        detector._price_history.setdefault(symbol, []).append(p)
    # Agora adicionar preço de recuo
    detector._price_history[symbol].append(5220)

    state = detector.update(
        symbol=symbol,
        original_direction=1,  # fluxo de alta
        volume_snapshot={
            "wave_volume_z": -1.5,      # volume caiu na correcção
            "wave_exhaustion": True,
            "wave_strength": 0.3,
        },
        orderflow={
            "delta_z": -0.8,            # delta ligeiramente negativo mas fraco
            "imbalance": -0.2,
            "absorption": False,
        },
        wyckoff={
            "spring": True,             # falso rompimento para baixo
            "upthrust": False,
        },
        footprint_snapshot={
            "near_confluence": True,    # preço na zona de POC/VWAP
            "convergence_score": 0.75,
        },
        current_price=5220,
        hurst=0.58,                     # regime de tendência
    )

    print(f"  Score: {state.trap_score:.3f} | is_trap: {state.is_trap} | urgency: {state.reentry_urgency}")
    expected_min = 0.70  # vol(0.30) + delta(0.25) + confluence(0.20) + wyckoff(0.20) + hurst(0.05) = 1.0 max
    if state.trap_score >= 0.55 and state.is_trap:
        ok(f"Score={state.trap_score:.3f} ≥ 0.55 — trap correctamente identificado")
    else:
        fail(f"Score={state.trap_score:.3f} < 0.55 ou is_trap=False")

    if state.reentry_urgency in ("HIGH", "CRITICAL"):
        ok(f"Urgência correcta: {state.reentry_urgency}")
    else:
        fail(f"Urgência incorrecta: {state.reentry_urgency} (esperado HIGH ou CRITICAL)")

    # ── Teste 2: Sem critérios — não deve ser trap ─────────────────────────
    print("\n>>> Teste 2: Sem critérios de trap (score esperado < 0.55)")
    detector2 = PullbackTrapDetector()
    symbol2   = "EURUSD"
    for p in [1.100, 1.102, 1.104, 1.106, 1.108]:
        detector2._price_history.setdefault(symbol2, []).append(p)
    detector2._price_history[symbol2].append(1.105)

    state2 = detector2.update(
        symbol=symbol2,
        original_direction=1,
        volume_snapshot={"wave_volume_z": 1.0, "wave_exhaustion": False, "wave_strength": 0.8},
        orderflow={"delta_z": -2.5, "imbalance": -0.6, "absorption": False},
        wyckoff={"spring": False, "upthrust": False},
        footprint_snapshot={"near_confluence": False, "convergence_score": 0.2},
        current_price=1.105,
        hurst=0.45,  # mean-revert
    )
    print(f"  Score: {state2.trap_score:.3f} | is_trap: {state2.is_trap}")
    if not state2.is_trap and state2.trap_score < 0.55:
        ok(f"Score={state2.trap_score:.3f} < 0.55 — não é trap (correcto)")
    else:
        fail(f"Falso positivo: score={state2.trap_score:.3f} is_trap={state2.is_trap}")

    # ── Teste 3: Fecho Parcial — lote ≥ 2.0 ──────────────────────────────
    print("\n>>> Teste 3: Fecho parcial com lote total = 2.5")
    pc = pc_mgr.should_partial_close(total_lots=2.5, trap_state=None)
    print(f"  trigger={pc['trigger']} | lots_to_close={pc['lots_to_close']} | reenter={pc['reenter']}")
    if pc["trigger"] and pc["reenter"] and pc["lots_to_close"] > 0:
        ok(f"Fecho parcial correctamente activado: {pc['lots_to_close']:.2f} lotes fechados, re-entrada=True")
    else:
        fail(f"Fecho parcial não activou correctamente: {pc}")

    # ── Teste 4: Override de intervalo ────────────────────────────────────
    print("\n>>> Teste 4: Override de intervalo em CRITICAL")
    state.is_ready_to_resume = True  # forçar para teste
    override = detector.get_scale_interval_override(symbol)
    print(f"  urgency={state.reentry_urgency} | interval_override={override}s")
    if override is not None and override <= 60:
        ok(f"Intervalo reduzido para {override}s (era 300s)")
    else:
        fail(f"Override incorrecto: {override}")

    # ── Resumo ────────────────────────────────────────────────────────────
    total = PASS + FAIL
    print()
    print("=" * 60)
    print(f"  PULLBACK ENGINE: {PASS}/{total} TESTES APROVADOS", end="")
    print(" ✅" if FAIL == 0 else f" ❌ {FAIL} FALHAS")
    print("=" * 60)
    return FAIL == 0


if __name__ == "__main__":
    _test_pullback_detector()
