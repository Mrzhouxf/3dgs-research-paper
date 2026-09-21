'use client';
import {Table,TableHeader,TableBody,TableRow,TableHead,TableCell,TableCaption} from '@/components/ui/table';
import facts from '@/lib/conference-facts.json';
import venues from '@/lib/venues.json';
import {beijingTime,candidateCount,candidateShare,isHeld,nextEdition,sourceHealthy,type Deadline,type Edition,type ResearchPaper} from '@/lib/conference-metrics';

const editions:Edition[]=facts.editions;
function Source({href,children}:{href:string;children:React.ReactNode}){
  return <a className="underline underline-offset-4" href={href} target="_blank" rel="noreferrer">{children} ↗</a>;
}
function DeadlineCell({edition,year,held=true}:{edition?:Edition;year:number;held?:boolean}){
  if(!held)return <span>该年不举办</span>;
  const deadline:Deadline|undefined=edition?.deadline;
  if(!deadline)return <div className="max-w-64 whitespace-normal"><span>{year} 届：{edition?.deadlineNote||'尚无已核实日期'}</span>{edition?.deadlineSource&&<div><Source href={edition.deadlineSource}>官方日期页</Source></div>}</div>;
  const closed=Date.parse(deadline.full)<Date.now();
  return <div className="flex flex-col gap-1 whitespace-normal min-w-48 max-w-64">
    <strong>{year} 届 · {closed?'已截止':'全文尚未截止'}</strong>
    <span>全文：<time dateTime={deadline.full}>{beijingTime(deadline.full)}</time></span>
    <span>摘要/注册：{deadline.abstract?<time dateTime={deadline.abstract}>{beijingTime(deadline.abstract)}</time>:'尚未核实'}</span>
    {deadline.abstract&&Date.parse(deadline.abstract)<Date.now()&&!closed&&<span>摘要/注册已截止，未注册者不能新投稿。</span>}
    <details><summary>原时区与来源</summary><p>原时区：{deadline.zone}</p><p>全文原始时间：{deadline.full}</p>{deadline.abstract&&<p>摘要/注册原始时间：{deadline.abstract}</p>}{deadline.note&&<p>{deadline.note}</p>}<Source href={deadline.source}>官方投稿要求</Source></details>
  </div>;
}
export function ConferenceOverview({papers,selectedYear,sourcesOk,errors,isLive}:{papers:ResearchPaper[];selectedYear:string;sourcesOk:string[];errors:string[];isLive:boolean}){
  const year=selectedYear==='all'?facts.defaultYear:Number(selectedYear);
  return <section className="conference-overview" aria-labelledby="conference-overview-title">
    <h2 id="conference-overview-title">{year} 年 · 会议占比与投稿日历</h2>
    <p className="overview-note">{selectedYear==='all'?`未限定年份时展示 ${facts.defaultYear} 年；选择上方年份可切换。`:''}统计始终比较全部 11 个会议，不受关键词、出版类型或会议筛选影响。</p>
    <p className="overview-note">本站已收录的渲染加速候选数 ÷ 同届主会录用总数 × 100%。这不是会议录用率，也不代表该领域完整真实占比；候选存在漏检与误判。训练和压缩相关方向不计入分子。同名论文去重。</p>
    <Table>
      <TableCaption>时间统一为北京时间（Asia/Shanghai，UTC+8）。下一届是相对所选年份的下一次举办；不按往年日期推算。录用总数和日期为 {facts.checkedAt} 人工核验快照，非自动核验；投稿前请再次查看官方页面。候选数随每日论文库更新。</TableCaption>
      <TableHeader><TableRow><TableHead>会议</TableHead><TableHead>本站渲染候选</TableHead><TableHead>主会录用总数</TableHead><TableHead>本站候选占比</TableHead><TableHead>所选届截稿 · 北京时间</TableHead><TableHead>下一届截稿 · 北京时间</TableHead></TableRow></TableHeader>
      <TableBody>{venues.conference.map(venue=>{
        const edition=editions.find(e=>e.venue===venue&&e.year===year);
        const next=nextEdition(venue,year);
        const held=isHeld(venue,year);
        const count=candidateCount(papers,venue,year);
        const healthy=isLive&&sourceHealthy(venue,year,sourcesOk,errors);
        const graphics=venue.startsWith('SIGGRAPH');
        const share=candidateShare(count,edition?.accepted?.count??null,held&&healthy&&!graphics);
        const reason=!held?'该年不举办':!isLive?'论文库尚未就绪':!healthy?'来源未完成或不可用':graphics?'TOG 与会议轨归属尚未完整核实':!edition?.accepted?'录用总数待核实':'仅本站已收录候选；非全量统计';
        return <TableRow key={venue}>
          <TableHead scope="row">{venue}</TableHead>
          <TableCell>{!held?'—':!isLive?'待加载':healthy?count:`${count}（不完整）`}</TableCell>
          <TableCell className="whitespace-normal"><div className="min-w-32 max-w-56">{!held?'不适用':edition?.accepted?<><strong>{edition.accepted.count.toLocaleString('en-US')}</strong><div><Source href={edition.accepted.source}>官方统计</Source></div><details><summary>统计口径</summary>{edition.accepted.note}</details></>:<><span>待核实</span>{edition?.acceptedNote&&<details><summary>原因</summary>{edition.acceptedNote}{edition.acceptedSource&&<div><Source href={edition.acceptedSource}>官方来源</Source></div>}</details>}</>}</div></TableCell>
          <TableCell className="whitespace-normal"><div className="min-w-32 max-w-52"><strong>{share===null?'暂不计算':share>0&&share<0.001?'<0.001%':share.toFixed(3)+'%'}</strong>{share!==null&&<div>{count} / {edition!.accepted!.count} × 100%</div>}<p>{reason}</p></div></TableCell>
          <TableCell><DeadlineCell edition={edition} year={year} held={held}/></TableCell>
          <TableCell><DeadlineCell edition={editions.find(e=>e.venue===venue&&e.year===next)} year={next}/></TableCell>
        </TableRow>;
      })}</TableBody>
    </Table>
    <details className="mt-5"><summary>当前已核实的 2027 届投稿日期</summary><p className="overview-note">以下只展示已核实的公告，不代表这些会议均仍接受新投稿；摘要截止可能早于全文截止。</p><div className="flex flex-wrap gap-8 mt-4">{editions.filter(e=>e.year===2027&&e.deadline).map(e=><div key={e.venue}><h3>{e.venue}</h3><DeadlineCell edition={e} year={e.year}/></div>)}</div></details>
  </section>;
}
