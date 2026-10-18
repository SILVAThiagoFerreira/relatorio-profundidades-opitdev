import { jsPDF } from 'jspdf';

const n = value => value == null ? '' : value.toFixed(2).replace('.', ',');
const signed = value => value == null ? '' : `${value >= 0 ? '+' : ''}${n(value)}`;
const download = (blob, name) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
};

export function exportCsv(result, planId, runId) {
  const header = ['ID','Prevista_m','Realizada_m','Desvio_m','Status','Outlier'];
  const lines = result.rows.map(r => [r.id,n(r.prevista),n(r.realizada),signed(r.variacao),r.status,r.outlier?'Sim':'Nao'].join(';'));
  download(new Blob(['\ufeff',header.join(';'),'\r\n',lines.join('\r\n')], {type:'text/csv;charset=utf-8'}), `RELATORIO_PROFUNDIDADES_${planId}_${runId}.csv`);
}

export function buildPdf(result, planId, runId, config, logoDataUrl) {
  const pdf = new jsPDF({unit:'mm',format:'a4',compress:true});
  const style = config.outputs.web_pdf_style;
  if (!logoDataUrl?.startsWith('data:image/png;base64,')) throw new Error('Logotipo PNG do relatório não informado.');
  if (!Number.isInteger(config.rules.detail_rows_per_page) || config.rules.detail_rows_per_page < 1 ||
      !Array.isArray(style?.column_widths_mm) || style.column_widths_mm.length !== 4 ||
      style.column_widths_mm.some(width => !Number.isFinite(width) || width <= 0)) {
    throw new Error('Configuração visual do PDF inválida.');
  }
  const pageWidth = pdf.internal.pageSize.getWidth();
  const tableX = style.page_margin_mm + style.table_inset_mm;
  const widths = style.column_widths_mm;
  const bounds = [tableX];
  widths.forEach(width => bounds.push(bounds.at(-1) + width));
  const tableWidth = bounds.at(-1) - tableX;
  const headerBottom = style.table_header_top_mm + style.table_header_height_mm;
  const rowsPerPage = config.rules.detail_rows_per_page;
  const pages = Math.max(1, Math.ceil(result.rows.length / rowsPerPage));
  pdf.setProperties({title:`${config.outputs.report_plan_label} ${planId}`,author:'ENAEX Brasil'});

  for (let page = 0; page < pages; page++) {
    if (page) pdf.addPage();
    pdf.addImage(logoDataUrl,'PNG',pageWidth - style.page_margin_mm - style.logo_width_mm,style.logo_top_mm,style.logo_width_mm,style.logo_height_mm);

    const planX = tableX + 2.12;
    pdf.setFont('helvetica','bold');pdf.setFontSize(15);pdf.setTextColor(style.red);
    const title = `${config.outputs.report_plan_label} ${planId}`.toUpperCase();
    pdf.text(title,planX,style.plan_baseline_mm);
    pdf.setFont('helvetica','normal');pdf.setFontSize(8.5);pdf.setTextColor(style.subtitle);
    pdf.text(config.outputs.report_subtitle,planX,style.subtitle_baseline_mm);

    pdf.setFontSize(8.2);pdf.setTextColor(style.navy);
    pdf.setFont('helvetica','bold');
    const headings = Object.values(config.outputs.report_table_headers);
    headings.forEach((heading,i)=>pdf.text(heading,(bounds[i]+bounds[i+1])/2,style.table_header_top_mm+4.85,{align:'center'}));
    pdf.setDrawColor(style.navy);pdf.setLineWidth(0.28);
    pdf.line(tableX,headerBottom,bounds.at(-1),headerBottom);

    pdf.setFont('helvetica','normal');pdf.setFontSize(8.1);pdf.setTextColor(style.text);
    result.rows.slice(page*rowsPerPage,(page+1)*rowsPerPage).forEach((row,index)=>{
      const top=headerBottom+index*style.table_row_height_mm;
      const bottom=top+style.table_row_height_mm;
      const baseline=top+3.06;
      pdf.text(String(row.id),(bounds[0]+bounds[1])/2,baseline,{align:'center'});
      pdf.text(n(row.prevista),bounds[2]-2.12,baseline,{align:'right'});
      if(row.realizada!=null)pdf.text(n(row.realizada),bounds[3]-2.12,baseline,{align:'right'});
      if(row.variacao!=null)pdf.text(signed(row.variacao),bounds[4]-2.12,baseline,{align:'right'});
      pdf.setDrawColor(style.rule);pdf.setLineWidth(0.123);
      pdf.line(tableX,bottom,bounds.at(-1),bottom);
    });

    pdf.setDrawColor(style.dark_rule);pdf.setLineWidth(0.14);
    pdf.line(style.page_margin_mm,style.footer_rule_mm,pageWidth-style.page_margin_mm,style.footer_rule_mm);
    pdf.setFont('helvetica','normal');pdf.setFontSize(7);pdf.setTextColor(style.muted);
    pdf.text(`${planId} · PÁGINA ${page+1}`.toUpperCase(),pageWidth-style.page_margin_mm,style.footer_page_baseline_mm,{align:'right'});
  }
  return pdf;
}

async function loadLogo(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('Não foi possível carregar o logotipo do relatório.');
  const blob = await response.blob();
  return await new Promise((resolve,reject)=>{
    const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error('Não foi possível ler o logotipo do relatório.'));reader.readAsDataURL(blob);
  });
}

export async function exportPdf(result, planId, runId, config, baseUrl) {
  const logo=await loadLogo(`${baseUrl}${config.outputs.web_pdf_style.logo_file}`);
  buildPdf(result, planId, runId, config, logo).save(`RELATORIO_PROFUNDIDADES_${planId}_${runId}.pdf`);
}
