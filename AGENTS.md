# Regras Permanentes Para Agentes

## Comportamento esperado
- Ler `README.md`, `SPEC.md`, `DATA_SCHEMA.md` e `config.json` antes de alterar a solucao.
- Tratar o projeto como um sistema completo, nao como um script isolado.
- Registrar qualquer decisao tecnica relevante em documentacao local.

## Restricoes tecnicas
- Nao hardcode caminhos, tolerancias, nomes de saida ou colunas de negocio fora de `config.json`.
- Nao misturar leitura, validacao, processamento e escrita no mesmo modulo.
- Nao modificar os arquivos de entrada em lugar nenhum.
- Nao introduzir comportamento silencioso quando houver falha de estrutura ou semantica.

## Padroes de qualidade
- Validar tudo antes de processar.
- Preferir falha explicita com mensagem clara a suposicoes implícitas.
- Garantir rastreabilidade por meio de log e nomes de arquivo com `run_id`.
- Manter testes minimos sempre atualizados.

## Regras de modificacao
- Mudanca de regra de negocio exige atualizacao de `SPEC.md`, `DATA_SCHEMA.md`, `TASK.md` e `config.json`.
- Mudanca de fluxo exige atualizacao de `PIPELINE.md`.
- Mudanca de saida exige atualizacao de `README.md` e testes.

## Proibicoes
- Nao criar logica critica fora de `src/`.
- Nao criar arquivo principal monolitico com toda a regra.
- Nao assumir nomes de colunas ou planilhas sem registrar a premissa.

## Evolucao segura
- Acrescentar novos modulos em `src/` ao inves de ampliar o arquivo principal.
- Cobrir qualquer nova regra com pelo menos um teste automatizado.
- Preservar a execucao unica por `main.py`.
