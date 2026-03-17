import subprocess
import time
import os

log_file = "uniqueness_proof.log"

def run_uniqueness_test():
    print("🚀 Iniciando Prova de Unicidade OMEGA V5.5.0...")
    
    # 1. Iniciar Instância Alpha
    print("📥 Lançando Instância Alpha...")
    p1 = subprocess.Popen(["python", "omega_v550_realtime_mt5.py"], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    time.sleep(5) # Espera inicialização e lock do socket
    
    # 2. Tentar Iniciar Instância Beta (Deve ser bloqueada)
    print("📥 Tentando Lançar Instância Beta (Conflito)...")
    p2 = subprocess.Popen(["python", "omega_v550_realtime_mt5.py"], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Capturar saída da Instância Beta
    stdout_beta, stderr_beta = p2.communicate()
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== PROVA DE UNICIDADE OMEGA V5.5.0 ===\n")
        f.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("--- SAÍDA INSTÂNCIA BETA ---\n")
        f.write(stdout_beta)
        f.write(stderr_beta)
        f.write("\n--- FIM DA SAÍDA ---\n")
    
    print(f"✅ Prova de Unicidade Capturada em {log_file}")
    
    # Limpar Instância Alpha
    p1.terminate()

if __name__ == "__main__":
    run_uniqueness_test()
