# Protocolo anti-fraude — execução PSA (fase de correção OMEGA)

| Campo | Valor |
|--------|--------|
| **Identificação** | PAF-PSA-20260330 |
| **Versão** | 1.0 |
| **Data** | 30 de março de 2026 |
| **Status** | Mandatório para qualquer trabalho PSA nesta fase |
| **Documentos relacionados** | `CHARTER_GOVERNANCA_PSA_ECOSISTEMA_TIER0.md`, `verify_tier0_psa.py`, `AUDITORIA_TECNICA_FORENSE_OMEGA_V10_4_20260330.md`, `RELATORIO_CONVERGENCIA_RESOLUCAO_OMEGA_V10_4_20260330.md` |

---

## 0. Contexto e finalidade

Foi alegado que entregas anteriores associadas ao PSA incorreram em **dados e relatórios com números inflados ou não comprovados**, **métricas sem definição verificável** e **placeholders** apresentados como factos. **Este protocolo não julga processos nem responsabilidades legais**; define **controles mínimos** para que novas execuções sejam **reproduzíveis, auditáveis e resistentes a fraude técnica** (omissão, substituição de evidência, métricas sem base).

**Objetivo:** permitir que o PSA **execute** trabalhos de correção e validação **somente** sob regras que impeçam repetir esses modos de falha.

---

## 1. Definições operacionais

| Termo | Definição |
|--------|------------|
| **Fraude técnica** (âmbito deste protocolo) | Afirmar resultado quantitativo, integridade ou desempenho **sem** cadeia de evidência reprodutível; **inflar** contagens ou métricas face ao que os ficheiros/comandos mostram; usar **placeholder**, dado sintético ou estimativa **sem rótulo explícito**; **misturar** resultados de corridas ou versões diferentes sem declaração. |
| **Número comprovado** | Valor que pode ser **reconstruído** a partir de: (i) ficheiro bruto versionado ou hash; (ii) comando e *output* completo; (iii) script que reproduz o cálculo a partir da fonte. |
| **Métrica admitida** | Grandeza com: **definição matemática**, **implementação** (fórmula ou código referenciado), **interpretação** e **limitações** (o que **não** prova). |
| **Placeholder permitido** | Apenas se etiquetado como `[PLACEHOLDER_EXPLÍCITO]`, com **proprietário**, **data alvo** e **critério de remoção** (alinhado ao Charter). |
| **Relatório de tarefa (RT)** | Documento obrigatório **ao concluir cada tarefa** (secção 6), antes de avançar para a seguinte. |

---

## 2. Princípios não negociáveis

1. **Nenhum número de desempenho ou de volumetria** (trades, sinais, PF, drawdown, latência) entra em relatório executivo **sem** anexo técnico que mostre **origem**.  
2. **Nenhuma métrica** “oficial” sem entrada no **registo de métricas** (secção 4.2) com fórmula e código.  
3. **Nenhum ficheiro** citado como prova **sem** integridade verificável (bytes + SHA3-256 no manifesto, ou processo equivalente).  
4. **Hierarquia de verdade:** código executável e *outputs* anexos **prevalecem** sobre narrativa. Divergência ⇒ **incidente documentado** antes de conclusões.  
5. **Um relatório por tarefa concluída** — sem excepção que não seja aprovada por escrito pelo Tech Lead / auditor.

---

## 3. Cadeia de custódia e integridade (comprovação técnica)

### 3.1 Manifesto e Git

| Controlo | Como cumprir | Ferramenta / artefacto |
|----------|----------------|-------------------------|
| **Commit explícito** | Todo pacote de evidência referencia `git_commit_sha` que existe no repositório | `git rev-parse HEAD`; manifesto JSON |
| **Objeto commit válido** | SHA resolve para objeto tipo `commit` | `git cat-file -t <sha>` |
| **Integridade de ficheiros** | Cada ficheiro listado: `bytes` e `sha3_256_full` conferidos | `verify_tier0_psa.py` |
| **Caminhos canónicos** | Uma “fonte da verdade” por artefacto; espelhos etiquetados | `PATHS_E_DEPLOY_PSA.md` + nota no RT |

**Execução:** na raiz configurada (`NEBULAR_KUIPER_ROOT` se necessário):

```bash
python "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/verify_tier0_psa.py"
```

**Falha (exit code ≠ 0)** ⇒ **não** homologar entrega; corrigir manifesto ou ficheiros antes de qualquer comunicação externa.

### 3.2 Volumetria de sinais (anti-inflação / anti-silêncio)

| Controlo | Descrição |
|----------|-----------|
| **Contagem reprodutível** | `signal_fired` (ou coluna oficial) contada por script versionado, não à mão. |
| **Coerência com limiar** | Número de linhas com `\|z\| ≥ Z₀` deve **coincidir** com a definição de sinal no código (se aplicável). |
| **Valores patológicos** | Percentil ou contagens de `\|z\|` acima de limite sanity (ex.: `1e6`) reportados como **achado**, não absorvidos em médias. |

*Script base:* pode usar o anexo do relatório ATF ou um `audit_trade_count.py` aprovado; **obrigatório** anexar *output* ao RT.

### 3.3 Dados históricos (≥ 2 anos)

| Controlo | Descrição |
|----------|-----------|
| **Proveniência** | Origem (MT5 export, vendor), intervalo temporal **[t₀, t₁]**, símbolos, timeframe. |
| **Merge** | Critério de alinhamento temporal documentado; contagem de linhas perdidas / gaps. |
| **Versão do dataset** | Nome de ficheiro + hash; **proibido** “aproximadamente 2 anos” sem datas explícitas. |

---

## 4. Registo de métricas (anti-métrica fantasma)

### 4.1 Proibições

- Citar **Sharpe, Sortino, PF, DD, win rate** sem coluna de equity ou trades **definida** e **ligada** ao código que calcula.  
- Usar **“Tier-0 OK”** como proxy de **qualidade estatística** — Tier-0 aqui cobre **integridade**, não **edge** de trading.  
- **Placeholders** em células de relatório (ex.: `TBD`, `—`, `N/A` sem explicação) em métricas **obrigatórias** ⇒ entrega **rejeitada**.

### 4.2 Tabela mínima por métrica usada no relatório

Para **cada** métrica, preencher:

| ID | Nome | Fórmula | Ficheiro:função ou script | Unidade | O que prova | O que **não** prova |
|----|------|---------|----------------------------|---------|-------------|---------------------|
| M1 | … | … | … | … | … | … |

Anexar ao RT da tarefa que introduz ou altera métricas.

---

## 5. Estrutura de fases e tarefas (esta correção)

Ordem sugerida (alinhada ao `RELATORIO_CONVERGENCIA_*`):

| Fase | Tarefas (exemplos) | Gate |
|------|---------------------|------|
| **A — Custódia** | Inventário CSVs; reconciliar contagens; fechar discrepância 0 vs N sinais | RT-A + `verify_tier0_psa` OK |
| **B — Histórico longo** | Dataset 2Y+ versionado; stress/replay | RT-B + hashes + resumo estatístico |
| **C — Parâmetros** | Grelhas λ / Z / span; escolha documentada | RT-C + tabela de sensibilidade |
| **D — QA mandatório** | Scripts de gate; falhas bloqueiam pipeline | RT-D |
| **E — Demo** | Logs; paridade BT vs demo | RT-E |

**Regra:** **não** iniciar fase **N+1** sem RT da fase **N** aprovado (Tech Lead / auditor).

---

## 6. Relatório obrigatório por conclusão de tarefa (RT)

Cada tarefa (ticket ou subtarefa identificável) fecha com **um** ficheiro:

**Nome:** `RT_PSA_<FASE>_<TAREFA_ID>_<YYYYMMDD>.md`  
**Local sugerido:** `evidencia_pre_demo/04_relatorios_tarefa/` (criar se necessário)

### 6.1 Conteúdo mínimo do RT

1. **Identificação:** ID da tarefa, responsável, data, commit(s).  
2. **Objetivo:** uma frase.  
3. **Execução:** comandos exatos (ou referência a script), ambiente (OS, Python).  
4. **Evidências:** lista de ficheiros com caminho relativo ao repo + hash SHA3-256.  
5. **Resultados:** números **copiados** de *output* ou tabela gerada por script — **proibido** só “resumo verbal” para métricas críticas.  
6. **Métricas:** referência ao registo (secção 4.2) se aplicável.  
7. **Incerteza e limitações:** o que **não** foi testado.  
8. **Próximo passo:** tarefa seguinte ou bloqueio.  
9. **Declaração de conformidade** (copiar e assinar digitalmente ou por nome):

```
Declaro que os números e conclusões desta tarefa têm base nos ficheiros e comandos listados,
que não utilizei placeholders como substituto de dados reais sem etiqueta explícita,
e que qualquer estimativa está identificada como tal.
Responsável: _______________  Data: _______________
```

---

## 7. Lista de verificação anti-fraude (antes de fechar qualquer RT)

- [ ] Todos os números críticos têm **fonte** (ficheiro + comando ou script).  
- [ ] Nenhuma métrica nova sem linha na tabela 4.2.  
- [ ] `verify_tier0_psa.py` executado se o pacote inclui manifesto alterado.  
- [ ] Nenhum gráfico ou tabela “demonstrativa” sem legenda **DADOS REAIS** vs **SIMULADO**.  
- [ ] Comparações temporais usam **mesma versão** de código e **mesmo** dataset (ou diferença declarada).  
- [ ] Conflitos entre relatórios antigos e novos medicções estão **explicitados**, não ignorados.

---

## 8. Após as correções: bateria de testes para “descobrir o incoberto”

Objetivo: **após** implementar correções paramétricas e QA, **procurar** o que ainda não foi apresentado (lacunas, regressões, edge cases).

| # | Teste / inspeção | O que pode revelar |
|---|------------------|-------------------|
| 1 | Reexecutar **stress completo** (3 perfis) + `audit_trade_count` + percentis de Z | Silêncio, explosão de sinais, caudas estranhas |
| 2 | Comparar **distribuição Z** stress vs **demo** (mesma build) | Feed, sessão, merge |
| 3 | **Warm-up:** métricas com e sem exclusão das primeiras *N* barras | Transientes e Z patológico |
| 4 | **Sensibilidade** a um parâmetro de cada vez (λ, Z₀, span) | Instabilidade |
| 5 | **Reconciliação** manifesto vs diretório de logs | Ficheiros trocados ou não arquivados |
| 6 | **Diff** de `git` entre versão homologada e candidata | Alterações não documentadas |

**RT obrigatório:** `RT_PSA_POS_CORRECAO_BATERIA_<YYYYMMDD>.md` com tabela pass/fail e anexos.

---

## 9. Instruções para o PSA executar esta fase

1. **Ler** integralmente este protocolo e o `CHARTER_GOVERNANCA_PSA_ECOSISTEMA_TIER0.md`.  
2. **Criar** pasta `04_relatorios_tarefa/` se não existir; **não** eliminar RTs — apenas versionar.  
3. Para **cada** tarefa: executar trabalho → gerar evidências → preencher **RT** → submeter revisão.  
4. **Atualizar** manifesto (`03_hashes_manifestos/`) sempre que ficheiros de prova mudarem; **nunca** comunicar SHA “de memória”.  
5. **Proibir** envio ao Conselho de números agregados **sem** o RT de suporte anexado ou linkado no repositório.  
6. Em caso de **impossibilidade** de provar um número (ex.: dado externo indisponível), **declarar** no RT e **não** preencher a célula com estimativa sem etiqueta `ESTIMATIVA — não verificada`.

---

## 10. Sanções de processo (governança interna)

| Gravidade | Exemplo | Acção típica |
|-----------|---------|----------------|
| **Leve** | RT sem hash de um ficheiro secundário | Correcção e reenvio |
| **Média** | Métrica sem definição | Rejeição até registo 4.2 |
| **Grave** | Número inflado ou não reprodutível face aos anexos | Reabertura da tarefa + revisão independente obrigatória |

*(Ajustar à política interna Simonsen Miller; este quadro é operacional, não jurídico.)*

---

## 11. Declaração final do protocolo

Este documento entra em vigor na data indicada e aplica-se a **todas** as entregas PSA na **fase de correção OMEGA** até revogação explícita. A sua observância **não** substitui auditoria legal ou forense externa; **reduz** o risco de repetição de falhas de evidência e de comunicação enganosa.

**Fim do protocolo PAF-PSA-20260330**
