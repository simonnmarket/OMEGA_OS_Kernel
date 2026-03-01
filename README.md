# OMEGA OS - PROJETO EXECUTAVEL (BASE DO BAU)

## Conteudo
- risk_engine.py (VaR/CVaR, backtesting, stress tests, kill switch)
- agent_system_original.py (7 agentes, voto/veto, SQLite)
- executor_original.py (loop MT5, filtros tecnicos, position manager)

## Uso
`
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py --mode demo
`

Atenção: Modo live não habilitado neste runner; para operar MT5, faça em conta demo e integre manualmente.
