import argparse
import subprocess
import sys
import shlex
import os

# Configurações de caminhos baseados na estrutura do usuário
BASE = r"C:\Users\Lenovo\.cursor\OMEGA_OS_Kernel\Auditoria PARR-F\Sistema AMI v2.1"
BATCH = os.path.join(BASE, "omega_turing_batch.py")
CAL   = os.path.join(BASE, "omega_turing_calibrate.py")
OPS   = os.path.join(BASE, "omega_ami_ops_calibrate.py")

DEFAULT_OUTPUT_DIR = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\outputs\causal_reports"

def run(cmd):
    print(f"\n[RUNNING] {cmd}")
    try:
        # Usando shell=True para lidar melhor com espaços em caminhos e variáveis no Windows se necessário
        # Mas subprocess.run com shell=False e shlex.split é mais seguro. 
        # No Windows, shlex.split pode ter problemas com barras invertidas duplas, então tratamos os caminhos.
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        print(res.stdout)
        if res.stderr:
            print(f"--- ERRORS/WARNINGS ---\n{res.stderr}", file=sys.stderr)
        
        if res.returncode != 0:
            print(f"Command failed with exit code {res.returncode}")
            sys.exit(res.returncode)
            
    except Exception as e:
        print(f"Execution Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Sistema AMI v2.1 - Orchestrator Runner")
    parser.add_argument("--symbols", default="XAUUSD", help="Ativos (ex: XAUUSD,EURUSD)")
    parser.add_argument("--timeframes", default="H1", help="Timeframes (ex: H1,M15)")
    args = parser.parse_args()

    # 1. Executar Batch (Geração de relatórios)
    batch_cmd = f'python "{BATCH}" --symbols {args.symbols} --timeframes {args.timeframes} --output_dir "{DEFAULT_OUTPUT_DIR}"'
    run(batch_cmd)

    # 2. Executar Calibrate (Agregação Turing)
    # Nota: omega_turing_calibrate.py usa paths default internos baseados em BASE_ROOT no seu script
    cal_cmd = f'python "{CAL}"'
    run(cal_cmd)

    # 3. Executar Ops Calibrate (Parâmetros Operacionais)
    ops_cmd = f'python "{OPS}"'
    run(ops_cmd)

    print("\n[AMI v2.1] Orquestração concluída com sucesso.")

if __name__ == "__main__":
    main()
