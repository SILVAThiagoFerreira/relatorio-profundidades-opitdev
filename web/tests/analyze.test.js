import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { analyzeDxf } from '../src/analyze.js';
const config = JSON.parse(fs.readFileSync(new URL('../../config.json', import.meta.url)));
const source = fs.readFileSync(new URL('./fixture.dxf', import.meta.url),'utf8');
test('DXF fixture produces the expected cardinality and missing record',()=>{
  const result=analyzeDxf(source,config);
  assert.equal(result.metrics.planned,2);
  assert.equal(result.metrics.realized,1);
  assert.equal(result.metrics.missing,1);
  assert.equal(result.rows.length,2);
  assert.equal(result.rows[0].status,'Aderente');
});
test('invalid and incomplete DXF fails visibly',()=>{
  assert.throws(()=>analyzeDxf('invalid',config));
  assert.throws(()=>analyzeDxf(source.replaceAll('Theoretical Hole','Removed Hole'),config),/Theoretical Hole/);
});
test('operational DXF matches Python pipeline when available locally', {skip: !fs.existsSync(new URL('../../imput/opit.dxf', import.meta.url))},()=>{
  const actual=analyzeDxf(fs.readFileSync(new URL('../../imput/opit.dxf', import.meta.url),'utf8'),config);
  assert.deepEqual([actual.metrics.planned,actual.metrics.realized,actual.metrics.missing],[105,104,1]);
  assert.equal(actual.rows.find(r=>r.id===49).realizada,null);
  const reference=new URL('../../output/RELATORIO_PROFUNDIDADES_WEB_REFERENCE_20260924_BASE_ANALITICA.csv',import.meta.url);
  if(fs.existsSync(reference)) {
    const csv=fs.readFileSync(reference,'utf8').replace(/^\ufeff/,'').trim().split(/\r?\n/).slice(1);
    assert.equal(csv.length,104);
    for(const line of csv) {
      const [id,prevista,realizada]=line.split(';');
      const row=actual.rows.find(r=>r.id===Number(id));
      assert.ok(Math.abs(row.prevista-Number(prevista.replace(',','.')))<=0.0051);
      assert.ok(Math.abs(row.realizada-Number(realizada.replace(',','.')))<=0.0051);
    }
  }
});
