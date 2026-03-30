# ADDENDUM RT-B — SUPERAÇÃO DO GATE PRÉ-STRESS (B1 e C3)
**Data:** 31 de Março de 2026  
**Responsável (PSA):** Antigravity MACE-MAX  
**Evidência Cruzada:** `GRIDSEARCH_V105_RUN_20260331.txt`  

Este anexo serve para dar liquidação estrita aos itens pendentes do check-list **GATE-PRE-STRESS-20260331** emanado pelo Conselho.

### 1. Item B1: Motor Único e Código Canônico
Declaro para todos os fins de homologação, auditoria e stress (presentes e futuros) que existe **apenas uma fonte canônica** do motor de Cointegração e Mean Reversion a ser acoplada pelos testadores.
*   **Path Canônico:** `Auditoria PARR-F/omega_core_validation/online_rls_ewma.py` (Classe `OnlineRLSEWMACausalZ`).
*   **Ação Tomada:** O script de estresse e extração de malha (`gridsearch_v105.py`) foi modificado para utilizar caminhos diretos (sem absolute links da máquina do developer), referenciando dinamicamente a pasta relativa `../../omega_core_validation`. 

Qualquer outra cópia da biblioteca em pastas alheias, como `Núcleo de Validação OMEGA/rls`, caso exista e seja executada em testes, será tratada como falsificação estatística.

### 2. Item C3: Definição Explícita de "Sinais"
A contagem de ocorrências de Sinais reportadas no RT-B (tanto no Grid da Tarefa quanto no Output original em bloco TXT) foram apuradas não por permanência, mas por **CROSSING** (cruzamento do limiar estático).

*   **Definição Operacional V10.5 ("Sinal de Entrada"):** Entende-se unicamente como o momento onde a barra (minuto) **cruza** o limite estabelecido (ex: `|Z| >= 2.0`), originando-se num instante imediatamente prévio em que `|Z| < 2.0`.
*   **Objetivo da Retificação:** Dissipar o enviesamento de contagens inchadas (quando 1.000 barras seguidas permanecem acima da banda sem cool_down). Um evento de "Trade" significa uma oportunidade tática executável única. O código `count_crosses` implementado no script respeita estritamente esta premissa.

**Status dos Gates B1 e C3:** Atendidos e devidamente documentados. O GridSearch gerencial com o seu respetivo `stdout` também já foi arquivado fisicamente em `.txt` sob a égide documental `C2`.
