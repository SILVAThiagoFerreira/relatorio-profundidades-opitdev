# Pipeline de Execucao

## Interface no navegador

1. O usuario anexa um DXF local e informa o ID do plano.
2. O navegador le `Number` / `Theoretical Hole` / `Real Hole` conforme `config.json`.
3. O modulo `web/src/analyze.js` valida estrutura, IDs, associacoes espaciais e profundidades antes de calcular.
4. O resultado mostra totais e todos os furos previstos, inclusive os sem realizado.
5. `web/src/export.js` carrega o logotipo, gera o PDF no layout do modelo fornecido e o CSV para download com identificador da execucao. Falhas aparecem na tela; arquivos operacionais nao sao enviados ao Pages.

### Gerar exemplo

1. `outputs.web_example` configura o DXF fictício e o ID de demonstração.
2. O botão `Gerar exemplo` carrega esse DXF estático, valida e processa pelas mesmas regras de `web/src/analyze.js`.
3. A interface identifica o resultado como demonstração e habilita a exportação de amostra em PDF/CSV.
4. Escolher ou soltar um DXF local remove o resultado anterior e seu aviso.

## Pipeline Python local

1. Carregar `config.json`, incluindo o formato e as regras de leitura.
2. Resolver caminhos e gerar `run_id`.
3. Inicializar logs.
4. No modo DXF, carregar IDs da camada configurada e associar cada texto a geometrias previstas e realizadas pela posicao.
5. Medir profundidade prevista pelo comprimento 3D da linha e realizada pelo comprimento 3D acumulado da polilinha, aplicando o fator de unidades configurado.
6. Validar IDs, profundidades, duplicatas e correspondencias; registrar IDs sem geometria do outro tipo.
7. Conciliar os registros por ID e calcular variacao, aderencia e outliers.
8. Gerar CSV analitico, PDF de lista e log com `run_id`.
9. Encerrar a execucao com status final documentado.

## Regras de falha
- Se a configuracao for invalida, a execucao para antes da leitura.
- Se a leitura falhar, a execucao para antes do processamento.
- Se a validacao falhar, nada e processado.
- Camada ausente, entidade com tipo incorreto, associacao espacial ambigua ou geometria sem ID interrompe a execucao com erro claro.
- Uma geometria realizada ausente para um ID previsto e mantida como divergencia: o PDF mostra o ID e a profundidade prevista com os campos de realizada vazios, e o log registra o ID.
- Se a escrita falhar, o erro e registrado no log e a execucao retorna falha.
