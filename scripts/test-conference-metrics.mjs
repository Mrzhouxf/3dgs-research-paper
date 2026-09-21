import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {beijingTime,candidateCount,candidateShare,isHeld,nextEdition,sourceHealthy} from '../lib/conference-metrics.ts';
const facts=JSON.parse(readFileSync(new URL('../lib/conference-facts.json',import.meta.url),'utf8'));
test('AoE crosses to next day at 19:59 Beijing; browser zone is irrelevant',()=>{
  assert.equal(beijingTime('2026-09-25T23:59:00-12:00'),'2026-09-26 19:59');
  assert.equal(beijingTime('2025-03-07T23:59:00-10:00'),'2025-03-08 17:59');
  assert.equal(beijingTime('2026-01-22T22:00:00Z'),'2026-01-23 06:00');
  assert.equal(beijingTime('2026-03-05T23:00:00+01:00'),'2026-03-06 06:00');
  assert.equal(beijingTime('2026-01-29T12:00:00Z'),'2026-01-29 20:00');
  assert.equal(beijingTime('2026-01-29T12:00:00'),'时间待核实');
});
test('Biennial conferences are never displayed as zero accepted',()=>{
  assert.equal(isHeld('ICCV',2026),false); assert.equal(isHeld('ECCV',2025),false);
  assert.equal(nextEdition('ICCV',2025),2027); assert.equal(nextEdition('ECCV',2024),2026);
  assert.equal(nextEdition('ECCV',2025),2026); assert.equal(nextEdition('CVPR',2025),2026);
});
test('Numerator deduplicates titles and ignores training, other years and journals',()=>{
  const p={title:'Fast-GS!',venue:'CVPR',year:2025,category:'渲染加速候选',url:'https://example.test/1'};
  assert.equal(candidateCount([p,{...p,title:'fast gs',url:'https://example.test/2'},{...p,year:2024},{...p,category:'训练/重建加速（相关方向）'},{...p,venue:'TOG'}],'CVPR',2025),1);
});
test('Ratios require healthy data and exact positive denominator',()=>{
  assert.equal(candidateShare(5,1000,true),0.5);
  assert.equal(candidateShare(0,1000,true),0);
  for(const denominator of [null,0,-1])assert.equal(candidateShare(5,denominator,true),null);
  assert.equal(candidateShare(5,1000,false),null);
  assert.equal(candidateShare(1001,1000,true),null);
});
test('Failed and unattempted sources do not become zero-percent claims',()=>{
  assert.equal(sourceHealthy('ICLR',2025,[],['ICLR: HTTP Error 403']),false);
  assert.equal(sourceHealthy('CVPR',2025,['CVPR 2024'],[]),false);
  assert.equal(sourceHealthy('CVPR',2025,['CVPR 2025'],['https://openaccess.thecvf.com/content/CVPR2025/html/a.html: timed out']),false);
  assert.equal(sourceHealthy('ICML',2025,['ICML'],[]),true);
});
test('Every stored fact has a unique edition, timezone, valid source and consistent deadlines',()=>{
  const ids=new Set();
  for(const e of facts.editions){
    const key=e.venue+e.year; assert.ok(!ids.has(key));ids.add(key);
    assert.ok(isHeld(e.venue,e.year));
    if(e.accepted){assert.ok(Number.isInteger(e.accepted.count)&&e.accepted.count>0);assert.equal(new URL(e.accepted.source).protocol,'https:');}
    if(e.deadline){assert.notEqual(beijingTime(e.deadline.full),'时间待核实');assert.equal(new URL(e.deadline.source).protocol,'https:');if(e.deadline.abstract)assert.ok(Date.parse(e.deadline.abstract)<=Date.parse(e.deadline.full));}
  }
});
