import { jsPDF } from 'jspdf';

const n = value => value == null ? '' : value.toFixed(2).replace('.', ',');
const signed = value => value == null ? '' : `${value > 0 ? '+' : ''}${n(value)}`;
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

export function buildPdf(result, planId, runId) {
  const pdf = new jsPDF({unit:'mm',format:'a4'});
  const perPage = 44;
  const pages = Math.ceil(result.rows.length / perPage);
  for(let page=0;page<pages;page++) {
    if(page) pdf.addPage();
    pdf.setFillColor(56,66,75); pdf.rect(0,0,210,17,'F');
    pdf.setTextColor(255); pdf.setFont('helvetica','bold');pdf.setFontSize(10);pdf.text('OpenBlast',14,11);
    pdf.text('Relatorio de profundidades',196,11,{align:'right'});
    pdf.setFillColor(226,6,19);pdf.rect(0,17,210,0.8,'F');
    pdf.setTextColor(38,52,64);pdf.setFontSize(16);pdf.text('Comparativo de profundidades',14,31);
    pdf.setFontSize(9);pdf.setFont('helvetica','normal');pdf.text(`Plano ${planId}   |   ${result.metrics.planned} previstos   |   ${result.metrics.realized} realizados`,14,38);
    pdf.setFillColor(242,245,247);pdf.rect(14,44,182,8,'F');pdf.setFont('helvetica','bold');pdf.setFontSize(8);
    [['ID',17],['Prevista (m)',55],['Realizada (m)',101],['Variacao (m)',149]].forEach(([t,x])=>pdf.text(t,x,49.5));
    pdf.setFont('helvetica','normal');
    result.rows.slice(page*perPage,(page+1)*perPage).forEach((r,i)=>{
      const y=58+i*5.1;
      if(i%2){pdf.setFillColor(250,251,252);pdf.rect(14,y-3.5,182,5.1,'F');}
      pdf.text(String(r.id),17,y);pdf.text(n(r.prevista),55,y);pdf.text(n(r.realizada),101,y);pdf.text(signed(r.variacao),149,y);
    });
    pdf.setDrawColor(210,218,225);pdf.line(14,282,196,282);pdf.setFontSize(8);pdf.setTextColor(90);pdf.text(`Gerado localmente  |  ${runId}`,14,287);pdf.text(`${page+1}/${pages}`,196,287,{align:'right'});
  }
  return pdf;
}

export function exportPdf(result, planId, runId) {
  buildPdf(result, planId, runId).save(`RELATORIO_PROFUNDIDADES_${planId}_${runId}.pdf`);
}
