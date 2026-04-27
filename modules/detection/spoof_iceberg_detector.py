class SpoofIcebergDetector:
    def __init__(self):
        self._last_scores: dict = {}

    def analyze(self, asset: str) -> dict:
        # Análise baseada no cost_oracle. Retorna um 'spoof_score' ou dict simulado
        result = {"score": 0, "status": "CLEAN"}
        self._last_scores = {
            "SPOOFER_LAYER": 0.0,
            "ICEBERG_HIDDEN": 0.0,
            "MOMENTUM_IGNITION": 0.0,
            "QUOTE_STUFFING": 0.0,
        }
        return result

    def get_signature_scores(self) -> dict:
        """Returns latest signature scores for orchestrator/shadow_loop integration.

        Stub implementation — returns zero scores (full microstructure detection pending).
        Keys mirror orchestrator thresholds: SPOOFER_LAYER, ICEBERG_HIDDEN,
        MOMENTUM_IGNITION, QUOTE_STUFFING.
        """
        return dict(self._last_scores) if self._last_scores else {
            "SPOOFER_LAYER": 0.0,
            "ICEBERG_HIDDEN": 0.0,
            "MOMENTUM_IGNITION": 0.0,
            "QUOTE_STUFFING": 0.0,
        }
