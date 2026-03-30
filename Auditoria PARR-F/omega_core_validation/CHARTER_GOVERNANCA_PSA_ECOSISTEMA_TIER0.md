# Charter de governança — PSA, agentes e ecossistema OMEGA (Tier-0)

| Campo | Valor |
|--------|--------|
| Versão | 1.0 |
| Finalidade | Prompt blindado + critérios de entrega; uso por CEO/Tech Lead, PSA, auditoria e ferramentas de IA |
| Princípio | **Transparência sobre aparência de completude** — nenhum placeholder sem rótulo explícito |

---

## Parte A — Prompt operacional (copiar para instruções permanentes / briefing PSA)

Use o bloco abaixo como **instrução de sistema** ou **anexo obrigatório** a qualquer SOW / ordem de serviço.

```
══════════════════════════════════════════════════════════════════════════════
OMEGA — MANDATO DE ENTREGA TIER-0 (PSA / ENGENHARIA / IA)
══════════════════════════════════════════════════════════════════════════════

1) PROIBIÇÃO DE OCULTAÇÃO
   - É proibido entregar código, diagramas ou relatórios que contenham TODO,
     stub não substituível, "skeleton only", dados fictícios como se fossem reais,
     ou caminhos não implementados SEM um bloco visível:
       [PLACEHOLDER_EXPLÍCITO] + motivo + proprietário + data alvo + critério de remoção.
   - Usar "camadas", "módulos" ou "arquitectura" para diluir ausência de
     implementação é falha de conduta, não estilo de desenho.

2) DEFINIÇÃO DE "PRONTO"
   - "Pronto" = comportamento verificável: testes que passam no ambiente declarado,
     ou, para infra, checklist com comandos e outputs esperados anexados.
   - Demo, smoke, bench ou stub são "PRONTOS" apenas se rotulados como tal;
     nunca como substituto silencioso de produção.

3) EVIDÊNCIA MÍNIMA POR TIPO DE ENTREGA
   - Código: repositório + requirements + pytest (ou equivalente) + como reproduzir.
   - Dados: ficheiro + SHA3-256 (ou política aprovada) + manifesto de colunas.
   - Métrica: fórmula + implementação + limite de interpretação (o que NÃO prova).
   - Processo: diagrama ou SOP numerado + RACI + registo de excepções.

4) HIERARQUIA DE VERDADE
   - Código executável > documentação > narrativa.
   - Se documento e código divergem, prevalece o código até correção documentada.

5) PESQUISA E AUDITORIA
   - Toda conclusão externa (paper, vendor, benchmark) exige: fonte, data de acesso,
     trecho ou citação, e limitação ("não verificado no nosso ambiente").
   - Auditoria interna: achados classificados (crítico / alto / médio) com
     evidência (ficheiro:linha ou comando + output).

6) GESTÃO DE FICHEIROS E VERSÕES
   - Um único caminho canónico por artefacto ("fonte da verdade"); cópias devem
     declarar "espelho de … até data …".
   - Alteração de protocolo (ex.: DEFINICOES, núcleo de validação): bump de versão
     + nota de controlo; proibido mudar thresholds sem registo.

7) COMUNICAÇÃO SOB INCERTEZA
   - Dúvida ou risco não resolvido DEVE ser declarado na primeira página do entregável.
   - É preferível atrasar entrega com honestidade do que entregar com omissão.

8) CONSEQUÊNCIA DE DESVIO
   - Desvio de conduta (placeholder disfarçado, omissão de limitação, mistura de
     níveis demo/produção) implica: documento de assunção de responsabilidade,
     correcção prioritaria, e revalidação por terceiro ou ferramenta independente.

9) ALCANCE
   - Este mandato aplica-se a: ingestão de mercado (ex. ticks), motores de sinal,
     validação OMEGA, pipelines PSA, e qualquer integração MT5/broker.

10) ACEITAÇÃO
    - Quem executa trabalho sob este mandato confirma leitura e conformidade
      explícita (assinatura ou registo em ticket).
══════════════════════════════════════════════════════════════════════════════
```

---

## Parte B — Checklist de revisão independente (antes de aceitar entrega PSA)

| # | Verificação | Evidência exigida |
|---|-------------|-------------------|
| B1 | Cada `raise NotImplementedError` ou `pass` em caminho quente está listado no README ou relatório de gaps | Lista explícita |
| B2 | Testes de integração: Postgres/Redis reais ou contrato CI (docker-compose) documentado | Log ou pipeline |
| B3 | Variáveis de ambiente: obrigatórias vs opcionais; falha clara se faltar secreto | Tabela no doc |
| B4 | Métricas Prometheus: significado + unidade; não confundir contador com taxa | Doc ou HELP strings |
| B5 | Spill/circuit-breaker: dados sensíveis encriptados? rotação de chaves? | Threat model 1 página |
| B6 | Nenhuma afirmação "NASA-grade / production-ready" sem testes e dados citados | Matriz comprovação |

---

## Parte C — Engenharia de software (processo mínimo para fechar ecossistema)

1. **Trunk-based ou release branches** com tag semântica alinhada a `OMEGA-DEFINICOES` / núcleo.
2. **CI obrigatório:** lint + testes na pasta relevante; falha bloqueia merge.
3. **Dois olhos:** alteração em caminho crítico (HMAC, spill, PG) exige revisão por quem não escreveu o patch.
4. **Runbooks:** um ficheiro por serviço: start, stop, variáveis, healthcheck, rollback.
5. **Observabilidade:** logs estruturados correlacionáveis (trace_id / tick_id); alertas em SLO acordados.

---

## Parte D — Relação com documentos OMEGA existentes

| Documento | Função |
|-----------|--------|
| `DEFINICOES_TECNICAS_OFICIAIS.md` (v1.1+) | Métricas 1–10, taxonomia sinal/performance |
| `DOCUMENTO_TECNICO_NUCLEO_OMEGA_COMPLETO.md` | Núcleo RLS/spread/Z + matriz de testes |
| `SCRIPT_INSTALACAO_E_DIRETRIZES_PSA.md` (pasta Núcleo de Validação) | Procedimento PSA para pytest |
| Documento oficial de **assunção de culpa / desvio** (PSA) | Anexo legal/governança — manter referência cruzada a este Charter |

---

## Parte E — Nota técnica sobre entregas tipo `tick_recorder_agent_full.py` (lição)

Código volumoso num único ficheiro com comentários "minimal tests" exige **escrutínio extra**:

- Testes que **mockam** `asyncpg` ou Redis devem ser **lidos linha a linha**; padrões quebrados (ex.: `create_pool` substituído por objecto inválido) fazem passar `pytest` sem validar integração.
- **Smoke** com `DummyPool` não substitui prova de `INSERT` real na tabela `ticks`.
- Exigir, para aceitação: teste com Postgres de CI **ou** gravação de vídeo + log de `COPY`/`executemany` bem-sucedido.

*(Esta nota não substitui auditoria do teu ficheiro concreto; formaliza o tipo de falha que já identificaste.)*

---

## Parte F — Compromisso de assinatura (texto para anexar ao documento PSA)

> Eu, _______________________ (função: PSA / fornecedor / responsável técnico), declaro que li o **Charter de governança Tier-0** e o mandato da Parte A, que todas as limitações da entrega _________________ estão documentadas na secção _________________, e que não utilizei placeholders ocultos nem omiti dependências críticas. Data: ____/____/______.

---

**Fim do Charter v1.0** — actualizar versão quando o Conselho aprovar alterações materiais.
