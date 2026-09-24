import '../style.css';
import { analyzeDxf } from './analyze.js';
import { exportCsv, exportPdf } from './export.js';
import config from '../../config.json';

const $ = selector => document.querySelector(selector);
const fmt = value => value == null ? '—' : value.toFixed(2).replace('.', ',');
let result = null;
let runId = '';
let file = null;

$('#app').innerHTML = `<header class="topbar"><div class="top-inner"><div class="brand"><img src="${import.meta.env.BASE_URL}openblast-mark.png" alt=""><strong>Open<span>Blast</span></strong></div><strong class="top-title">Relatório de profundidades</strong></div></header>
<main class="container"><div class="intro"><div><p class="eyebrow">PROCESSAMENTO LOCAL</p><h1>Comparar profundidades<br>previstas e realizadas</h1><p class="subtitle">Leia o DXF do OPITDEV, confira cada furo e baixe o relatório rastreável.</p></div><div class="local-badge"><span></span> Processado neste navegador</div></div>
<details class="help"><summary><span class="help-icon">i</span><span><strong>O que anexar</strong><small>DXF com IDs, furos teóricos e furos realizados</small></span><b>⌄</b></summary><div class="help-body">Selecione o arquivo DXF exportado do OPITDEV. O arquivo deve conter as camadas <strong>Number</strong>, <strong>Theoretical Hole</strong> e <strong>Real Hole</strong>. A planilha PP é uma entrada de referência do trabalho original; este comparativo calcula as profundidades diretamente das geometrias do DXF.</div></details>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">ETAPA 1</p><h2>Anexe o arquivo</h2></div><small>O arquivo permanece no seu dispositivo.</small></div><label class="dropzone" id="dropzone" for="file"><span class="upload-icon">↑</span><strong>Escolha o DXF do plano</strong><small>Arraste aqui ou clique para selecionar · .dxf</small></label><input id="file" type="file" accept=".dxf" hidden><p id="file-name" class="file-name">Nenhum arquivo selecionado</p><div class="divider"></div><div class="section-heading"><div><p class="eyebrow">ETAPA 2</p><h2>Identifique o plano</h2></div></div><label class="field"><span>ID / nome do plano</span><input id="plan-id" autocomplete="off" maxlength="60" value="${config.outputs.report_plan_id}" placeholder="Ex.: PC590926"><small>O ID aparece nos arquivos baixados e no PDF.</small></label><button id="analyze" class="primary" type="button">Validar e gerar relatório <span>→</span></button><p id="error" class="error" role="alert" hidden></p></section>
<section id="results" class="results" hidden><div class="section-heading"><div><p class="eyebrow">RESULTADO</p><h2>Relatório pronto</h2></div><small id="run-label"></small></div><div class="stats"><div><strong id="planned">—</strong><span>Previstos</span></div><div><strong id="realized">—</strong><span>Realizados</span></div><div><strong id="missing">—</strong><span>Sem realizado</span></div><div><strong id="adherence">—</strong><span>Aderência*</span></div></div><p class="metric-note">* Furos até ${config.rules.outlier_threshold_m} m, tolerância de ±${config.rules.depth_tolerance_m.toFixed(2).replace('.', ',')} m. Outliers: <span id="outliers">—</span>.</p><div class="download-row"><button id="pdf" class="primary">Baixar PDF</button><button id="csv" class="secondary">Baixar CSV</button></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Prevista (m)</th><th>Realizada (m)</th><th>Variação (m)</th><th>Situação</th></tr></thead><tbody id="rows"></tbody></table></div></section></main><footer>OpenBlast · Relatório de profundidades</footer>`;

const setFile = selected => {file=selected; $('#file-name').textContent=selected ? `${selected.name} · ${(selected.size/1024).toFixed(0)} KB` : 'Nenhum arquivo selecionado';};
$('#file').addEventListener('change', e => setFile(e.target.files[0]));
const drop = $('#dropzone');
drop.addEventListener('dragover', e => {e.preventDefault();drop.classList.add('dragging');});
drop.addEventListener('dragleave', () => drop.classList.remove('dragging'));
drop.addEventListener('drop', e => {e.preventDefault();drop.classList.remove('dragging');setFile(e.dataTransfer.files[0]);});
$('#analyze').addEventListener('click', async () => {
  $('#error').hidden=true;$('#results').hidden=true;result=null;
  const planId=$('#plan-id').value.trim();
  try {
    if(!file || !/\.dxf$/i.test(file.name)) throw new Error('Selecione um arquivo .dxf para continuar.');
    if(!/^[\p{L}\p{N}._ -]{1,60}$/u.test(planId)) throw new Error('Informe um ID de plano com letras, números, espaços, ponto, hífen ou sublinhado.');
    $('#analyze').disabled=true;$('#analyze').textContent='Lendo e validando DXF…';
    result=analyzeDxf(await file.text(),config);
    runId=new Date().toISOString().replace(/[-:]/g,'').replace('T','_').slice(0,15);
    $('#planned').textContent=result.metrics.planned;$('#realized').textContent=result.metrics.realized;$('#missing').textContent=result.metrics.missing;$('#outliers').textContent=result.metrics.outliers;
    $('#adherence').textContent=result.metrics.adherence==null?'—':`${(result.metrics.adherence*100).toFixed(1).replace('.',',')}%`;
    $('#run-label').textContent=`Plano ${planId} · ${runId}`;
    $('#rows').replaceChildren(...result.rows.map(r=>{const tr=document.createElement('tr');[r.id,fmt(r.prevista),fmt(r.realizada),r.variacao==null?'—':`${r.variacao>0?'+':''}${fmt(r.variacao)}`,r.status].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});return tr;}));
    $('#results').hidden=false;$('#results').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(error) {$('#error').textContent=error.message || 'Não foi possível ler o arquivo DXF.';$('#error').hidden=false;}
  finally {$('#analyze').disabled=false;$('#analyze').innerHTML='Validar e gerar relatório <span>→</span>';}
});
$('#pdf').addEventListener('click',()=>exportPdf(result,$('#plan-id').value.trim(),runId));
$('#csv').addEventListener('click',()=>exportCsv(result,$('#plan-id').value.trim(),runId));
