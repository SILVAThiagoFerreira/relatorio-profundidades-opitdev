# Schema de Dados

## Fonte DXF ativa
- Arquivo local: `imput/opit.dxf`, selecionado por `inputs.format`, `directories.input` e `inputs.dxf.file_name`. No site, o usuario seleciona um DXF com a mesma estrutura; nenhum exemplo operacional e publicado.
- IDs: entidades de texto do tipo configurado na camada `Number`.
- Profundidade prevista: entidade `LINE` da camada `Theoretical Hole`; medida pelo comprimento 3D entre os pontos inicial e final.
- Profundidade realizada: entidade `POLYLINE` da camada `Real Hole`; medida pela soma dos comprimentos 3D entre vertices consecutivos.
- O texto do ID e associado a geometria mais proxima dentro de `inputs.dxf.id_match_tolerance_m`. Empates, geometrias orfas e tipos de entidade inesperados sao erros explicitos.
- Comprimentos sao multiplicados por `inputs.dxf.drawing_units_to_meters`. O DXF declara unidades unitless; o fator atual e `1.0`, consistente com os textos da camada `Length`, que conferem com os comprimentos teoricos dentro do arredondamento de duas casas.
- Se nao houver geometria realizada dentro da tolerancia para um ID, o PDF mantem o ID e a profundidade prevista e deixa profundidade realizada e variacao em branco. A ausencia e registrada no log.

## Alternativa de entrada workbook
O modo `inputs.format = "workbook"` continua disponivel. Nesse modo, cada fonte define arquivo, aba, linha de cabecalho e colunas de ID e profundidade dentro de `config.json`.

## Saida analitica CSV
- `ID` | inteiro conciliado.
- `Prevista_m` | profundidade prevista com duas casas.
- `Realizada_m` | profundidade realizada com duas casas.
- `Desvio_m` | realizado menos previsto, com sinal.
- `Status` | classificacao de aderencia.
- `Outlier` | `Sim` ou `Nao`.
- `Motivo_outlier` | motivo da classificacao de outlier.
- `Prevista_linha` e `Realizada_linha` | posicoes originais da fonte.

## Saida de consulta PDF
- Lista ordenada pela uniao dos IDs previstos e realizados.
- Colunas: ID, profundidade prevista, profundidade realizada e variacao (`realizada - prevista`).
- O ID do plano configurado aparece acima da tabela em cada pagina.
- Quando faltar uma das profundidades, o PDF mantem o ID e deixa o valor ausente e a variacao em branco.
- O CSV contem os pares conciliados; IDs sem par ficam registrados no log.

## Saida web

- Tabela e PDF: uniao de IDs previstos, com ID, profundidade prevista, realizada e variacao; ausencias ficam vazias. O PDF replica a tabela A4 do relatorio de referencia, com 53 registros por pagina, cabecalho repetido e pagina numerada.
- CSV web: `ID;Prevista_m;Realizada_m;Desvio_m;Status;Outlier`, uma linha por furo previsto, inclusive ausencias.
- A aderencia exclui outliers e considera `abs(variacao) <= rules.depth_tolerance_m`; outliers usam `rules.outlier_threshold_m`.

## Amostra demonstrativa web

- `outputs.web_example.dxf_file` aponta para um DXF sintético público, sem dados de operação.
- `outputs.web_example.plan_id` identifica downloads e relatório como demonstração.
- O exemplo passa pelo mesmo leitor, validador e comparador do DXF operacional.
