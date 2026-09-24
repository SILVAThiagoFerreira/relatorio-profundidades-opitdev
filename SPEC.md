# Especificacao Tecnica

## Regra de negocio principal
- No modo DXF, a camada `Theoretical Hole` representa a profundidade prevista e a camada `Real Hole` representa a geometria realizada.
- O ID e lido da camada de texto configurada, atualmente `Number`, e associado espacialmente a cada geometria dentro da tolerancia configurada.
- A profundidade prevista e o comprimento 3D da entidade `LINE`; a realizada e o comprimento acumulado dos segmentos 3D da entidade `POLYLINE`.
- O fator de conversao entre unidade de desenho e metro e configurado em `inputs.dxf.drawing_units_to_meters`.
- O cruzamento ocorre pelo identificador do furo.
- O desvio e calculado como `realizada - prevista`.
- Um furo e aderente quando `abs(desvio) <= 0,30 m`.
- Um furo e outlier quando a profundidade prevista ou realizada e maior que `20 m`.

## Prioridade de classificacao
1. Outlier.
2. Aderente.
3. Acima do previsto.
4. Abaixo do previsto.

## Validacoes obrigatorias
- Arquivo de entrada existe e pode ser lido.
- Camadas configuradas existem e contem somente o tipo de entidade esperado.
- Os textos de ID podem ser associados sem ambiguidade as geometrias dentro da tolerancia configurada.
- Todas as geometrias teoricas possuem um ID; geometrias sem ID interrompem o processamento.
- IDs sao inteiros positivos.
- Profundidades sao numericas e positivas.
- Nao existem IDs duplicados dentro da mesma base.
- Ao menos um ID deve ser conciliado entre as bases.
- Uma geometria realizada ausente e registrada como ID previsto sem realizado, sem estimar profundidade.
- No modo workbook alternativo, linhas incompletas seguem `rules.incomplete_row_policy`.

## Comportamento esperado
- Registros conciliados entram na base analitica.
- Registros fora do cruzamento ficam identificados nas listas de divergencia e nos logs; valores ausentes nao sao estimados.
- Outliers permanecem no relatorio, mas sao excluidos do indicador principal.
- Saidas sao nomeadas com `run_id` para rastreabilidade.
- Linhas incompletas nao quebram a execucao; elas sao registradas em log e excluidas do processamento.
- O PDF apresenta somente a lista conciliada com ID, profundidade prevista, profundidade realizada e variacao (`realizada - prevista`), em ordem crescente de ID.
- O ID do plano configurado aparece acima da lista em cada pagina; a identidade visual usa fundo branco, logotipo ENAEX e detalhes vermelhos discretos.
- O CSV analitico permanece detalhado e inclui status, classificacao de outlier e linhas de origem.

## Tratamento de erros
- Erros de configuracao geram `ConfigError`.
- Erros de leitura geram `DataReadError`.
- Erros de validacao geram `ValidationError`.
- Falhas de comparacao geram `ProcessingError`.
- Falhas de escrita geram `OutputError`.

## Decisoes tecnicas
- Configuracao externa em JSON para evitar dependencias extras.
- Logs em arquivo e console para auditoria.
- CSV com separador `;` para facilitar abertura em Excel.
- PDF gerado via ReportLab.

## Limitacoes conhecidas
- A associacao entre texto e geometria depende da tolerancia espacial configurada.
- O comprimento de uma POLYLINE e medido pelos segmentos entre vertices 3D; curvas aproximadas por outros tipos de entidade nao sao aceitas neste modo.
- O relatorio depende de bibliotecas Python instaladas localmente.
- O GitHub Pages executa somente arquivos estaticos. Na interface, a validacao e o calculo ocorrem no navegador; a saida web em CSV usa ID, profundidades, desvio, status e outlier. O PDF web e uma tabela de consulta. O log persistente e a base CSV analitica completa continuam sendo entregues pelo pipeline Python local.

## Criterios de sucesso
- Arquivos gerados com nome identificavel.
- KPI calculado apenas sobre registros nao outliers.
- Testes cobrindo carga, validacao, processamento e saida.
