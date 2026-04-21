import pandas as pd
from sqlalchemy import create_engine
import time

csv_path = r'C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Auditoria Conselho\FIN_SENSE_L1_SAMPLE.csv'
df = pd.read_csv(csv_path)

# Wait a second for postgres to be ready
time.sleep(2)
engine = create_engine('postgresql://finsense_user:staging_pass@localhost:5433/finsense_staging')

# retry block
for i in range(10):
    try:
        df.to_sql('v_omega_l1_features', engine, if_exists='replace', index=False)
        print('✅ Seed concluído')
        break
    except Exception as e:
        print(f"Retrying connection: {e}")
        time.sleep(2)
