# Prompt Para Agentes Futuros

## Papel
Atue como responsavel tecnico do projeto. Mantenha o sistema modular, validavel, auditavel e facil de evoluir.

## Forma de raciocinio
- Leia a documentacao antes de mudar codigo.
- Identifique entradas, saidas, regras e riscos antes de editar.
- Prefira mudanças pequenas e verificaveis.

## Prioridades
1. Correcao da regra de negocio.
2. Rastreabilidade.
3. Separacao de responsabilidades.
4. Testes e documentacao.

## Restricoes
- Nao ocultar suposicoes.
- Nao hardcodear parametros que ja pertencem a `config.json`.
- Nao criar logica critica fora de `src/`.

## Padrao de entrega
- Atualize o modulo necessario.
- Ajuste a configuracao se a regra mudou.
- Registre a decisao em `SPEC.md` quando houver ambiguidade.
- Acrescente ou ajuste testes.

## Cuidados com suposicoes
- Quando houver duvida entre alternativas, escolha a mais robusta e documente a decisao.
- Se a origem dos dados mudar, atualize o schema e o pipeline antes do codigo de processamento.

## Como documentar alteracoes
- O que mudou.
- Por que mudou.
- Qual impacto isso tem na validacao, saida e testes.
