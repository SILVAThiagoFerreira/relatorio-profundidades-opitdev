# Tarefa Atual

## Contexto

Entrega web: publicar uma interface OpenBlast em repositorio proprio no GitHub Pages. A interface usa o DXF fornecido pelo usuario sem carregar dados operacionais no site, valida as camadas e IDs, compara profundidades e oferece PDF/CSV. A configuracao unica `config.json` fornece camadas, tolerancias, ID inicial e rotulos. O arquivo DXF original permanece em `imput/` e nao integra o repositorio publico.
O projeto precisa gerar um relatorio reutilizavel para comparar profundidade prevista e realizada a partir das camadas de um arquivo DXF.

## Objetivo
Construir uma base organizada, auditavel e extensivel para:
- ler IDs e geometrias nas camadas DXF configuradas;
- validar a estrutura e os valores;
- calcular aderencia com tolerancia de `0,30 m`;
- tratar como outlier qualquer furo acima de `20 m`;
- gerar PDF, CSV e log com nome rastreavel.
- apresentar no PDF somente a lista de IDs, profundidades prevista e realizada e variacao, identificada pelo ID do plano e no padrao visual ENAEX.
- preservar na lista IDs sem geometria correspondente e sinalizar com campos de profundidade ausentes, registrando a divergencia no log.
- ignorar, com aviso e registro em log, linhas incompletas que nao contenham os dois campos-chave configurados.

## Escopo
- Estrutura modular em `src/`.
- Configuracao externa em `config.json`.
- Documentacao operacional e tecnica.
- Testes minimos automatizados.

## Fora de escopo
- Alterar o arquivo DXF de origem.
- Corrigir dados de campo.
- Criar novos formatos de saida alem de PDF e CSV.

## Entregaveis
- Arquivos de documentacao solicitados.
- `config.json`.
- `main.py` como ponto unico de execucao.
- Modulos em `src/`.
- Testes em `tests/`.

## Criterios de aceite
- A execucao gera saidas nomeadas por `run_id`.
- O processamento so ocorre apos validacao.
- As regras de aderencia e outlier sao configuraveis e documentadas.
- Nenhum arquivo obrigatorio fica vazio.
