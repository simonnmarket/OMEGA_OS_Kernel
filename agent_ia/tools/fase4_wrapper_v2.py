"""
fase4_wrapper_v2.py - Wrapper para shadow_loop_v2 (PSA-WIND Refatoração Segura)
Testa v2 em paralelo com v1 para comparação de resultados.

Uso:
    python agent_ia/tools/fase4_wrapper_v2.py --symbols EURUSD GBPUSD XAUUSD --cycles 5

Autor: PSA-WIND
Data: 2026-04-30
Versão: 2.0.0-alpha
"""

import sys
import os
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Adicionar path para importar shadow_loop_v2
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core_engines"))

from shadow_loop_v2 import run_loop_v2

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/fase4_v2.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
OMEGA_MAGIC = 234001
CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"]
FOREX_SYMBOLS  = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
INDEX_SYMBOLS  = ["US500", "NAS100"]
XAU_SYMBOLS    = ["XAUUSD"]
ALL_SYMBOLS    = FOREX_SYMBOLS + XAU_SYMBOLS + INDEX_SYMBOLS + CRYPTO_SYMBOLS
EQUITY = 10000.0

# =============================================================================
# LOCK FILE
# =============================================================================
LOCK_FILE = Path("OMEGA_FASE4_V2.lock")

def acquire_lock():
    """Adquire lock file para evitar múltiplas instâncias."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text())
            try:
                os.kill(pid, 0)  # Verificar se processo existe
                log.error(f"Lock já existe (PID={pid}) - outra instância rodando")
                return False
            except OSError:
                # Processo não existe, remover lock antigo
                LOCK_FILE.unlink()
        except (ValueError, OSError):
            LOCK_FILE.unlink()
    
    LOCK_FILE.write_text(str(os.getpid()))
    log.info(f"Lock adquirido (PID={os.getpid()})")
    return True

def release_lock():
    """Libera lock file."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
        log.info("Lock liberado")

# =============================================================================
# WRAPPER PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Fase4 Wrapper V2 - PSA-WIND")
    parser.add_argument("--symbols", nargs="+", default=FOREX_SYMBOLS + XAU_SYMBOLS,
                        help="Lista de ativos para processar")
    parser.add_argument("--mode", default="paper", choices=["paper", "live"],
                        help="Modo de execução")
    parser.add_argument("--equity", type=float, default=EQUITY,
                        help="Equity inicial")
    parser.add_argument("--cycles", type=int, default=1,
                        help="Número de ciclos para rodar")
    parser.add_argument("--sleep-between-cycles", type=int, default=300,
                        help="Segundos de espera entre ciclos")
    parser.add_argument("--label", default="V2_TEST",
                        help="Label para identificação nos logs")
    
    args = parser.parse_args()
    
    log.info("=" * 80)
    log.info("FASE4 WRAPPER V2 - PSA-WIND Refatoração Segura")
    log.info("=" * 80)
    log.info(f"Label: {args.label}")
    log.info(f"Símbolos: {args.symbols}")
    log.info(f"Mode: {args.mode}")
    log.info(f"Equity: ${args.equity:.2f}")
    log.info(f"Cycles: {args.cycles}")
    log.info(f"Sleep entre ciclos: {args.sleep_between_cycles}s")
    
    # Adquirir lock
    if not acquire_lock():
        sys.exit(1)
    
    try:
        # Configurar variáveis de ambiente
        os.environ["OMEGA_NIGHT_PASS"] = "AUTHORISED_BY_CEO"
        os.environ["OMEGA_MAX_POSITIONS"] = "20"
        os.environ["OMEGA_DD_DAILY_MAX"] = "0.01"
        os.environ["OMEGA_RISK_PER_TRADE"] = "0.001"
        
        # Rodar ciclos
        all_results = []
        for cycle in range(1, args.cycles + 1):
            log.info("=" * 80)
            log.info(f"CICLO {cycle}/{args.cycles}")
            log.info("=" * 80)
            
            result = run_loop_v2(
                ativos=args.symbols,
                mode=args.mode,
                equity=args.equity
            )
            
            all_results.append(result)
            
            log.info(f"Ciclo {cycle} concluído:")
            log.info(f"  Execuções: {result.get('exec_count', 0)}")
            log.info(f"  SKIPs: {result.get('skip_count', 0)}")
            log.info(f"  Assets abertos: {len(result.get('cycle_opened_assets', []))}")
            
            if cycle < args.cycles:
                log.info(f"Aguardando {args.sleep_between_cycles}s antes do próximo ciclo...")
                time.sleep(args.sleep_between_cycles)
        
        # Resumo final
        log.info("=" * 80)
        log.info("RESUMO FINAL V2")
        log.info("=" * 80)
        total_exec = sum(r.get('exec_count', 0) for r in all_results)
        total_skip = sum(r.get('skip_count', 0) for r in all_results)
        log.info(f"Total execuções: {total_exec}")
        log.info(f"Total SKIPs: {total_skip}")
        log.info(f"Total ciclos: {args.cycles}")
        
        # Salvar resultados em JSON
        results_file = f"audit/fase4_v2_results_{args.label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("audit").mkdir(exist_ok=True)
        with open(results_file, 'w') as f:
            import json
            # Convert numpy types to native Python types for JSON serialization
            def convert_types(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                return obj
            
            json.dump({
                "label": args.label,
                "symbols": args.symbols,
                "mode": args.mode,
                "equity": args.equity,
                "cycles": args.cycles,
                "results": all_results,
                "total_exec": total_exec,
                "total_skip": total_skip
            }, f, indent=2, default=convert_types)
        log.info(f"Resultados salvos em: {results_file}")
        
        log.info("V2 concluído com sucesso")
        
    except Exception as e:
        log.critical("ERRO CRÍTICO no wrapper V2:\n%s", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        release_lock()

if __name__ == "__main__":
    main()
