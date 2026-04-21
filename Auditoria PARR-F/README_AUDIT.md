# DOCUMENTAÇÃO DE BY-PASS - MOD #4 (HASH BASELINE)

## Contexto

O script `test_psa_compliance.ps1` fornecido pelo CQO continha um paradoxo criptográfico
("Paradoxo de Quine"): exigia que o hash SHA-256 do arquivo `hunter.json` fosse calculado
e armazenado dentro do próprio arquivo, e depois comparado com o hash do arquivo modificado.

Matematicamente, após a inserção do campo `hash_verificacao`, o arquivo é alterado,
tornando impossível a igualdade `hash_antes == hash_depois`.

## Ação Tomada

Para permitir a continuidade dos testes sem violar a integridade do processo, foi aplicado
um by-pass sintático local que:

1. Calcula o hash do arquivo ANTES da inserção do campo
2. Armazena este hash no campo `hash_verificacao`
3. Para verificações futuras, compara o hash armazenado com um hash do arquivo
   excluindo o campo `hash_verificacao` do cálculo

## Justificativa

Esta abordagem preserva a intenção do requisito (baseline de integridade) sem incorrer
no paradoxo matemático do script original.

## Aprovação

Este by-pass foi documentado e está disponível para auditoria.
