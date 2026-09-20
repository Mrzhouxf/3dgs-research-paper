import {env} from 'cloudflare:workers';
import {database} from '@/lib/database';
export async function POST(request:Request){
 const key=(env as unknown as {INGEST_TOKEN?:string}).INGEST_TOKEN;
 if(!key||request.headers.get('Authorization')!==`Bearer ${key}`)return new Response('Unauthorized',{status:401});
 const raw=await request.text();
 if(raw.length>2000000)return new Response('Payload too large',{status:413});
 let data;
 try{data=JSON.parse(raw)}catch{return new Response('Invalid JSON',{status:400})}
 if(!Array.isArray(data.papers)||!data.papers.length||data.papers.some((p:any)=>!p.title||!['CVPR','ICCV','ECCV','SIGGRAPH','SIGGRAPH Asia'].includes(p.venue)||!/^https:\/\/(openaccess\.thecvf\.com|www\.ecva\.net|dblp\.org)\//.test(p.url)||!Number.isInteger(p.year)))return new Response('Invalid paper records',{status:400});
 const db=await database();
 const previous=await db.prepare('SELECT payload FROM snapshots WHERE id=?').bind('latest').first<{payload:string}>();
 if(previous){const old=JSON.parse(previous.payload);const merged=new Map((old.papers||[]).map((p:any)=>[p.url,p]));for(const p of data.papers){const prior:any=merged.get(p.url);merged.set(p.url,{...p,first_seen:prior?.first_seen||p.first_seen});}data.papers=Array.from(merged.values());}
 await db.prepare('INSERT INTO snapshots(id,payload,updated_at) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at').bind('latest',JSON.stringify(data),new Date().toISOString()).run();
 return Response.json({saved:data.papers.length});
}
