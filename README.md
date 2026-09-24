# Sistema de Relatorio de Profundidades

## Proposito
Este projeto gera um relatorio PDF e uma base CSV usando as geometrias teoricas e realizadas do arquivo DXF do plano.

## Problema que resolve
O sistema le geometrias previstas e realizadas de um DXF, valida IDs e profundidades, calcula aderencia com tolerancia definida em configuracao e separa outliers do KPI principal.

## Arquitetura
- `main.py` orquestra a execucao.
- `src/config_loader.py` carrega e normaliza a configuracao.
- `src/logger_setup.py` inicializa logs de execucao.
- `src/data_reader.py` le planilhas quando configurado no modo workbook.
- `src/dxf_reader.py` associa IDs e mede as geometrias nas camadas DXF configuradas.
- `src/validator.py` valida estrutura e semantica.
- `src/processor.py` calcula o comparativo e os indicadores.
- `src/output_writer.py` gera CSV, PDF e artefatos auxiliares.
- `src/exceptions.py` centraliza erros tipados.
- `generate_relatorio_profundidades_reg260526.py` e um wrapper legado para compatibilidade.

## Fluxo de uso
1. Ajuste `config.json` se necessario.
2. Garanta que `input/opit.dxf` exista e contenha as camadas configuradas.
3. Execute `python main.py --config config.json`.
4. Consulte os arquivos gerados em `output/` e `logs/`.

## Entrada esperada
- `imput/opit.dxf`, com os IDs na camada `Number`, geometrias teoricas na `Theoretical Hole` e geometrias realizadas na `Real Hole`. A pasta `imput` preserva o nome legado dos arquivos fornecidos.
- A profundidade prevista e o comprimento 3D das entidades `LINE` teoricas; a realizada e a soma dos comprimentos 3D dos segmentos de cada `POLYLINE` real.
- O fator de conversao de unidades, os nomes das camadas, tipos de entidade e tolerancia de associacao entre o texto do ID e a geometria ficam em `config.json`.
- Se um ID nao tiver geometria real correspondente, o PDF mantem o ID e a profundidade prevista e deixa profundidade realizada e variacao em branco; a ausencia fica registrada no log.

## Saidas geradas
- PDF simples, em fundo branco, com identidade visual ENAEX, contendo IDs e profundidades extraidos do DXF e variacao; o ID do plano aparece acima da tabela em todas as paginas.
- CSV analitico com o comparativo linha a linha.
- Log textual da execucao.

## Configuracao
Toda regra ajustavel fica em `config.json`: fonte de entrada, nomes de arquivo e camadas, tipos de entidade, fator de unidades, tolerancia de associacao, tolerancia de aderencia, limite de outlier, ID do plano, rotulos da tabela, arquivo do logotipo e linhas por pagina. O logotipo usado pelo relatorio fica em `assets/enaex_logo.png`.

## Como executar
```bash
python main.py --config config.json
```
Opcionalmente, passe `--run-id <id>` para fixar o identificador da execucao. Use apenas letras, numeros, ponto, sublinhado e hifen.

## Como instalar dependencias
```bash
python -m pip install ezdxf openpyxl reportlab
```

## Como validar
```bash
python -m unittest discover -s tests
```

## Interface GitHub Pages

A interface em `web/` processa um DXF selecionado pelo usuário no próprio navegador. Ela mostra os furos, a aderência, as ausências e permite baixar PDF e CSV. Nenhum DXF, planilha ou relatório operacional é enviado ao servidor ou incluído na publicação. O ID do plano pode ser editado antes da análise. A planilha `imput/pp.xlsx` é uma referência da execução original; as profundidades desta ferramenta vêm das geometrias do DXF.

```bash
npm ci --prefix web
npm test --prefix web
npm run build --prefix web
```

O GitHub Pages publica `web/dist` pelo workflow `.github/workflows/pages.yml`. `dxf-parser` interpreta o DXF no navegador, `jsPDF` gera o PDF e Vite empacota a página; as três dependências são necessárias para hospedagem estática sem servidor. O pipeline Python permanece disponível para saída local com log. Os formatos web de PDF e CSV incluem os campos de consulta; o CSV Python continua sendo a base analítica detalhada.

## Evolucao
Para adicionar novas fontes, novas regras ou novos formatos de saida, atualize primeiro `config.json`, depois `SPEC.md`, `DATA_SCHEMA.md` e os testes correspondentes.
