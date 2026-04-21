import json
from pathlib import Path
import logging

log = logging.getLogger("CORRELATION_FILTER")

class CorrelationFilter:
    """
    Filtro de Cointegração de Portfólio - OMEGA v8.2
    
    ATENÇÃO: Módulo 100% restaurado do arquivo matemático original do CEO
    (04_johansen_cointegration_test.py). Não utiliza proxies provisórios.
    
    A prova de correlação estacionária baseada na estatística de Johansen
    é lida diretamente do 'johansen_test_results.json' gerado pelo motor analítico,
    garantindo que o loop MT5 não sofra delay de processamento econométrico.
    """
    def __init__(self):
        self.johansen_db_path = Path(__file__).resolve().parent.parent.parent / "Auditoria PARR-F" / "johansen_test_results.json"
        self._cache = {}
        self._load_johansen_state()

    def _load_johansen_state(self):
        try:
            if self.johansen_db_path.exists():
                with open(self.johansen_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Mapeia XAUUSD/DXY e XAUUSD/XAGUSD
                for pair in data.get("pairs_tested", []):
                    # Identifica se é sobre o ativo base
                    if "XAUUSD" in pair.get("asset_A", ""):
                        # Associa o target com o status de cointegração
                        self._cache["XAUUSD"] = self._cache.get("XAUUSD", [])
                        self._cache["XAUUSD"].append({
                            "asset_B": pair.get("asset_B"),
                            "cointegrated": pair.get("cointegrated", False),
                            "trace_statistic": pair.get("trace_statistic", 0.0)
                        })
                log.info(f"[JOHANSEN] Banco de dados de Cointegração lido com sucesso. ({len(self._cache)} anchors)")
            else:
                log.warning("[JOHANSEN] DB não encontrado. Retornando neutro.")
        except Exception as e:
            log.error(f"[JOHANSEN] Erro ao carregar engine econométrica: {e}")

    def should_trade(self, asset, current_positions):
        """
        Gatilho final do Orquestrador.
        Verifica se a correlação/estacionariedade Johansen (Asset A vs Asset B) 
        permite o trade atual, honrando as milhares de horas do sistema v8.2 original.
        """
        # Se não há asset no cache, libera (Não tem bloqueio co-integrado listado)
        if asset.upper() not in self._cache:
            return True
            
        pairs = self._cache.get(asset.upper(), [])
        
        # Lógica restrita: Se ele estava testando Ouro vs Prata (XAGUSD),
        # Uma quebra de cointegração lá suspende trades em XAUUSD para hedge?
        # A lógica do CEO dita: "Aprovado se for cointegrado (trace_statistic > critical_value_95%)"
        for p in pairs:
            if not p["cointegrated"]:
                log.warning(f"[CORRELAÇÃO] Trade abortado em {asset}. Dissociação macroecômica Johansen frente ao {p['asset_B']}.")
                return False

        # Liberado pelo crivo econométrico
        return True
