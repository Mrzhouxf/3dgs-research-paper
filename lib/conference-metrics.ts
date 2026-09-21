export type ResearchPaper = {title:string; venue:string; year:number; category:string; url:string};
export type Deadline = {full:string; abstract:string|null; zone:string; source:string; note?:string};
export type Edition = {venue:string; year:number; deadline?:Deadline; deadlineNote?:string; deadlineSource?:string; accepted?:{count:number; source:string; note:string}; acceptedNote?:string; acceptedSource?:string};

export function isHeld(venue:string,year:number){
  return venue==='ICCV'?year%2===1:venue==='ECCV'?year%2===0:true;
}
export function nextEdition(venue:string,year:number){
  let next=year+1;
  while(!isHeld(venue,next))next++;
  return next;
}
export function beijingTime(iso:string){
  if(!/(Z|[+-]\d{2}:\d{2})$/.test(iso)||!Number.isFinite(Date.parse(iso)))return '时间待核实';
  return new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(iso));
}
export function candidateCount(papers:ResearchPaper[],venue:string,year:number){
  return new Set(papers.filter(p=>p.venue===venue&&p.year===year&&p.category==='渲染加速候选')
    .map(p=>p.title.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu,''))).size;
}
export function sourceHealthy(venue:string,year:number,ok:string[],errors:string[]){
  const key=['CVPR','ICCV'].includes(venue)?`${venue} ${year}`:venue.startsWith('SIGGRAPH')?'SIGGRAPH / SIGGRAPH Asia':venue;
  if(!ok.includes(key))return false;
  return !errors.some(e=>e.startsWith(key+':')||(venue==='CVPR'||venue==='ICCV')&&e.includes(`/content/${venue}${year}/`));
}
export function candidateShare(n:number,total:number|null,available:boolean){
  if(!available||total===null||!Number.isInteger(total)||total<=0||!Number.isInteger(n)||n<0||n>total)return null;
  return (n/total)*100;
}
