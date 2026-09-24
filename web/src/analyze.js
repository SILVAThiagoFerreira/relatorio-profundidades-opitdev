import DxfParser from 'dxf-parser';

const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, (a.z || 0) - (b.z || 0));
const point = entity => entity.type === 'TEXT' ? entity.startPoint : entity.vertices?.[0];

function associate(labels, geometries, tolerance, optional, role) {
  const used = new Set();
  const result = new Map();
  for (const label of labels) {
    const matches = geometries.map((geometry, index) => ({index, d: distance(point(label), point(geometry))})).sort((a,b) => a.d - b.d);
    if (!matches.length || matches[0].d > tolerance) {
      if (optional) continue;
      throw new Error(`Furo ${label.text}: geometria ${role} não encontrada dentro da tolerância.`);
    }
    if (matches[1] && Math.abs(matches[1].d - matches[0].d) <= 1e-7) throw new Error(`Furo ${label.text}: associação ${role} ambígua.`);
    if (used.has(matches[0].index)) throw new Error(`Mais de um ID associado à mesma geometria ${role}.`);
    used.add(matches[0].index);
    const vertices = geometries[matches[0].index].vertices;
    if (vertices.length < 2) throw new Error(`Furo ${label.text}: geometria ${role} incompleta.`);
    let depth = 0;
    for (let i = 1; i < vertices.length; i++) depth += distance(vertices[i-1], vertices[i]);
    if (!Number.isFinite(depth) || depth <= 0) throw new Error(`Furo ${label.text}: profundidade ${role} inválida.`);
    result.set(Number(label.text.trim()), depth);
  }
  if (used.size !== geometries.length) throw new Error(`${geometries.length - used.size} geometrias ${role} sem ID associado.`);
  return result;
}

export function analyzeDxf(source, config) {
  const dxf = new DxfParser().parseSync(source);
  if (!dxf?.entities?.length) throw new Error('O DXF não contém entidades legíveis.');
  const settings = config.inputs.dxf;
  const byLayer = (layer, type) => {
    const all = dxf.entities.filter(e => e.layer?.toLowerCase() === layer.toLowerCase());
    if (!all.length) throw new Error(`Camada “${layer}” ausente ou vazia no DXF.`);
    if (all.some(e => e.type !== type)) throw new Error(`Camada “${layer}” contém tipos de entidade diferentes de ${type}.`);
    return all;
  };
  const labels = byLayer(settings.id_layer, settings.id_entity_type);
  const ids = new Set();
  for (const label of labels) {
    const id = Number(label.text?.trim());
    if (!Number.isInteger(id) || id <= 0) throw new Error(`ID inválido na camada ${settings.id_layer}: ${label.text}`);
    if (ids.has(id)) throw new Error(`ID duplicado: ${id}.`);
    ids.add(id);
  }
  const tolerance = settings.id_match_tolerance_m / settings.drawing_units_to_meters;
  const planned = associate(labels, byLayer(settings.planned.layer_name, settings.planned.entity_type), tolerance, false, 'prevista');
  const realized = associate(labels, byLayer(settings.realized.layer_name, settings.realized.entity_type), tolerance, true, 'realizada');
  if (!realized.size) throw new Error('Nenhum furo previsto foi conciliado com o realizado.');
  const scale = settings.drawing_units_to_meters;
  const rows = [...planned.keys()].sort((a,b) => a-b).map(id => {
    const prevista = planned.get(id) * scale;
    const realizada = realized.has(id) ? realized.get(id) * scale : null;
    const variacao = realizada == null ? null : realizada - prevista;
    const outlier = realizada != null && (prevista > config.rules.outlier_threshold_m || realizada > config.rules.outlier_threshold_m);
    const status = realizada == null ? 'Sem realizado' : outlier ? 'Outlier' : Math.abs(variacao) <= config.rules.depth_tolerance_m ? 'Aderente' : variacao > 0 ? 'Acima' : 'Abaixo';
    return {id, prevista, realizada, variacao, status, outlier};
  });
  const analyzed = rows.filter(r => r.realizada != null && !r.outlier);
  return {rows, metrics: {planned: planned.size, realized: realized.size, matched: realized.size, missing: planned.size-realized.size, outliers: rows.filter(r => r.outlier).length, adherence: analyzed.length ? analyzed.filter(r => r.status === 'Aderente').length/analyzed.length : null}};
}
