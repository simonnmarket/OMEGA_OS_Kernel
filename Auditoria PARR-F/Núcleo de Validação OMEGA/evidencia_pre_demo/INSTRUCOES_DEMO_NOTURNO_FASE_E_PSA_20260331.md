# Instruções — Demo noturno (Fase E) e verificação matinal (PSA)

| ID | INST-DEMO-NOTURNO-20260331 |
|----|-----------------------------|
| **Destinatário** | PSA / Engenharia |
| **Finalidade** | Deixar **Ciclo 1 demo** a correr durante a noite e **validar amanhã** se o comportamento alinha com **V10.5** (λ, span, limiar Z, cool-down). |
| **Segurança** | **Nunca** gravar passwords, logins ou URLs de servidor em `.py`, `.md` ou Git. Usar `.env` local (ignorado pelo Git) ou cofre. |

---

## 1. Pré-requisitos (antes de iniciar)

| # | Item | Verificação |
|---|------|-------------|
| 1 | **MT5** instalado e **conta demo** ligada (sessão estável). | Terminal aberto; símbolos XAUUSD / XAGUSD visíveis. |
| 2 | **Máquina / VPS** não vai hibernar nem desligar à noite. | Energia; desactivar suspensão em Windows para o período. |
| 3 | **Paridade V10.5 no live** | `11_live_demo_cycle_1.py` usa **λ=0,9998**, **span=500**, **MIN_Z_ENTRY=2,0**, **min_hold=20** (alinhado ao stress). |
| 4 | **Barras** | Para ~8–10 h de mercado M1, usar **`--bars 500`** ou superior (ex.: **600–800**) conforme horas úteis esperadas; mercado fecha — contagem real pode ser **menor** que o limite. |
| 5 | **Manifesto** | Após gerar `DEMO_LOG_*.csv`, incluir entrada no `MANIFEST_RUN_*.json` e correr `verify_tier0_psa.py`. |

---

## 2. Comando sugerido (início à noite)

Na raiz `nebular-kuiper` (ou pasta do script), **a partir de `Auditoria PARR-F`**:

```powershell
cd "C:\...\nebular-kuiper\Auditoria PARR-F"
python 11_live_demo_cycle_1.py --bars 800
```

- Ajustar `--bars` ao tempo desejado (1 barra ≈ 1 minuto de mercado **quando** há nova barra M1 fechada).  
- O log será algo como:  
  `omega_core_validation\evidencia_demo_YYYYMMDD\DEMO_LOG_SWING_TRADE_YYYYMMDD_THHMM.csv`  
- Anotar **caminho completo** e **hora de início**.

**Smoke (opcional antes):** `python 11_live_demo_cycle_1.py --smoke` (10 barras).

---

## 3. Durante a noite (não obrigatório vigiar)

- Não fechar o **Terminal MT5** nem o **PowerShell** onde o Python corre.  
- Se o script terminar sozinho ao atingir `N` barras, está **OK**; o ficheiro CSV fica fechado.  
- Se houver **erro MT5**, o script pode parar — rever consola pela manhã.

---

## 4. Verificação pela manhã (obrigatória)

1. Localizar o **último** `DEMO_LOG_SWING_TRADE_*.csv` gerado.  
2. Executar o script de auditoria:

```powershell
cd "C:\...\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo"
python verificar_demo_apos_noturno.py --csv "CAMINHO\PARA\DEMO_LOG_....csv"
```

3. Copiar o **output integral** para `04_relatorios_tarefa/RT_E_VERIFICACAO_<YYYYMMDD>.md` (template abaixo).  
4. Correr `python verify_tier0_psa.py` após actualizar manifesto com o novo `DEMO_LOG`.  
5. **Critério de sucesso (mínimo):**  
   - Linhas > 0;  
   - **|Z|** com dispersão razoável (não colado artificialmente a zero em **todas** as linhas se o mercado se moveu);  
   - `signal_fired` True **≥ 0** (com limiar 2.0 pode haver poucos ou vários — comparar com janela e volatilidade).

**Não** exigir “igual ao stress offline” — demo é **regime diferente**; exigir **paridade de parâmetros** e **ausência de erro**.

---

## 5. Template RT-E (copiar para markdown)

```markdown
# RT-E — Verificação pós-demo noturno
**Data:** 
**CSV:** `...`
**Barras processadas:** 
**signal_fired True (soma):** 
**P50/P95 |Z| (script):** 
**verify_tier0_psa:** OK / FALHA
**Conclusão:** 
```

---

## 6. Problemas frequentes

| Sintoma | Causa provável |
|---------|----------------|
| 0 barras no log | MT5 desligado; símbolo errado; script não chegou ao primeiro `copy_rates` válido. |
| Pouquíssimas barras | Mercado fechado; fim-de-semana; apenas horas de baixa liquidez. |
| Z sempre ~0 | Verificar se pares e merge temporal estão corretos (já tratado no script). |

---

**Fim das instruções.**
