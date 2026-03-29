import numpy as pd
import pandas as pd
import numpy as np
import statsmodels.api as sm
import os

class PairsTradingMathBlock:
    """
    Motor Matemático V8.2 (Tier-0) - Fase 2 Auditável
    Constrói a regressão OLS rolante, Spread Residual e Z-Score EWMA
    para o par XAUUSD e XAGUSD sem executar ordens de mercado.
    """
    
    def __init__(self, asset_y_name="XAUUSD", asset_x_name="XAGUSD", window_ols=500, ewma_span=100):
        self.asset_y = asset_y_name # Ativo Dependente
        self.asset_x = asset_x_name # Ativo Independente (Hedge)
        self.window_ols = window_ols
        self.ewma_span = ewma_span
        
    def fit_rolling_ols(self, df_y, df_x):
        """
        Calcula o Beta Dinâmico (Hedge Ratio) e Alpha via OLS rolante.
        """
        print(f"[*] Iniciando OLS Regressão ({self.window_ols} barras) para {self.asset_y} vs {self.asset_x}...")
        
        # Alinhando dados temporais
        df = pd.DataFrame({'Y': df_y['close'], 'X': df_x['close']}).dropna()
        
        if len(df) < self.window_ols:
            raise ValueError("Dados insuficientes para a janela OLS rolante.")
            
        betas = np.full(len(df), np.nan)
        alphas = np.full(len(df), np.nan)
        
        # Otimização: OLS Rolante
        # Para produção HFT, usaremos um Kalman Filter C++, mas para o protótipo auditável, 
        # OLS estrito valida a premissa matemática.
        y_vals = df['Y'].values
        x_vals = df['X'].values
        
        for i in range(self.window_ols, len(df)):
            y_window = y_vals[i-self.window_ols:i]
            x_window = x_vals[i-self.window_ols:i]
            
            # Adicionando constante para Alpha
            X_with_const = sm.add_constant(x_window)
            model = sm.OLS(y_window, X_with_const).fit()
            
            alphas[i] = model.params[0]
            betas[i] = model.params[1]
            
        df['Alpha'] = alphas
        df['Beta'] = betas
        
        # Passo 2 do Protocolo: Calcular o Spread (Resíduo do Hedge)
        # S_t = Y_t - (Alpha + Beta * X_t)
        df['Spread'] = df['Y'] - (df['Alpha'] + df['Beta'] * df['X'])
        
        return df.dropna()

    def calc_z_score_ewma(self, df):
        """
        Aplica o modelo EWMA para modelagem da heterocedasticidade 
        e conversão do Spread absoluto para Coeficiente Normalizado (Z-Score).
        """
        print(f"[*] Calculando Z-Score EWMA (span={self.ewma_span})...")
        
        # Média e Desvio Padrão Movél Exponencial (EWMA)
        ewma_mean = df['Spread'].ewm(span=self.ewma_span, adjust=False).mean()
        ewma_std = df['Spread'].ewm(span=self.ewma_span, adjust=False).std()
        
        # Z-Score = (Spread Constante - Media) / Desvio Padrao
        df['Z_Score'] = (df['Spread'] - ewma_mean) / ewma_std
        
        return df

if __name__ == "__main__":
    print("="*60)
    print("MACE-MAX TIER-0 | AUDITORIA DE BLOCO MATEMÁTICO (FASE 2)")
    print("="*60)
    
    # 1. Carregar dados isolados da FASE 1 (Sem conexão com a corretora)
    try:
        df_xau = pd.read_parquet("data_lake/XAUUSD_M1_HISTORICO.parquet").set_index('time')
        df_xag = pd.read_parquet("data_lake/XAGUSD_M1_HISTORICO.parquet").set_index('time')
    except Exception as e:
        print(f"❌ Falha ao carregar banco de dados Parquet local: {e}")
        print("💡 O Robô da Fase 1 precisa ter gerado a base corretamente.")
        exit()

    # 2. Instanciar o Bloco
    # Usando janela M1 menor para demonstração rápida em OOS simulado
    motor = PairsTradingMathBlock(window_ols=500, ewma_span=100)
    
    # 3. Executar o Pipeline Analítico Matemático
    df_result = motor.fit_rolling_ols(df_xau, df_xag)
    df_result = motor.calc_z_score_ewma(df_result)
    
    # 4. Gerar Artefato Estrito de Auditoria
    os.makedirs("audit_blocks", exist_ok=True)
    df_result[['Y', 'X', 'Beta', 'Spread', 'Z_Score']].tail(2000).to_csv("audit_blocks/math_block_v82_sample.csv")
    
    print("\n[✔] BLOCO MATEMÁTICO CONCLUÍDO COM SUCESSO.")
    print(f"   ► Beta Médio Histórico OLS: {df_result['Beta'].mean():.4f}")
    print(f"   ► Spread Volatilidade Atual: {df_result['Spread'].std():.4f}")
    print(f"   ► O Z-Score Oscilou de {df_result['Z_Score'].min():.2f} a {df_result['Z_Score'].max():.2f}")
    print("\n[+] Um artefato de auditoria rigorosa (2000 barras) foi gerado em: audit_blocks/math_block_v82_sample.csv")
    print("    Solicita-se aprovação da Tese do Z-Score ao Chief Quant Officer antes de prosseguir.")
