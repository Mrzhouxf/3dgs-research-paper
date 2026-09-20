import seed from '@/lib/seed.json';
import {database} from '@/lib/database';
export async function GET(){
 try {
  const db=await database();
  const row=await db.prepare('SELECT payload,updated_at FROM snapshots WHERE id=?').bind('latest').first<{payload:string;updated_at:string}>();
  if(row){const data=JSON.parse(row.payload);return Response.json({...data,message:`最近云端抓取：${row.updated_at}。${data.errors?.length?'部分数据源失败，请检查更新记录。':''}`});}
  return Response.json({papers:seed,message:'已核实论文的初始快照 · 每日云端更新等待接入。'});
 }catch{return Response.json({papers:seed,message:'云端数据库暂不可用，展示已核实的初始快照；不是实时结果。'});}
}
