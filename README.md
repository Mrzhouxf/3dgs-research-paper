# GS Observatory

## 扩展收录范围

AI 主会：NeurIPS、ICML、ICLR、AAAI、IJCAI、ACM MM；保留原 CVPR、ICCV、ECCV、SIGGRAPH / Asia。
期刊：TPAMI、IJCV、TOG、TVCG、TIP、JMLR、Artificial Intelligence。白名单为领域精选，不声称统一分级。
NeurIPS 和 ICML 使用正式论文集；ICLR 从 2024 年起使用官方 OpenReview 已录用 venueid 与录用状态双校验；期刊使用 Crossref ISSN 和完整刊名双校验。Crossref 收录可能滞后或缺失，不能保证全覆盖。Workshop、未录用投稿、预印本不混入主列表。
页面新增出版类型和期刊筛选，保持每天北京时间 09:17 云端更新。原文链接及来源核验说明随条目展示。

在线网站：https://gs-rendering-observatory.gyvideo.chatgpt.site

GitHub Actions 每天北京时间 09:17 在云端检索，去重后提交给网站的 D1 数据库；无需本机开机，没有本地定时任务。GitHub 调度可能延迟，公开仓库长期无活动也可能被平台暂停定时运行，运行记录请查看 Actions。

来源：CVPR/ICCV 官方 CVF，ECCV 官方 ECVA；SIGGRAPH / SIGGRAPH Asia 使用 DBLP，异常时回退 Crossref 出版商会议元数据。排除 workshop、poster、course，TOG 期刊形式的会议技术论文未全面覆盖。规则筛选存在漏检，不能保证全网实时或全部论文覆盖。

网页区分渲染加速候选与训练、压缩等相关方向。主会归属来源可追溯；最新收录日期不等于发表日期。API 返回数据源异常，失败不覆盖历史结果。

工作流：`.github/workflows/daily-papers.yml`，支持手动运行。变量 `SITE_URL` 和 Secrets `INGEST_TOKEN`、`SITES_ACCESS_TOKEN` 已用于提交。密钥到期或轮换后需在云端重新配置。不要写入代码。

开发：`npm ci`、`npm run dev`、`npm run build`。部署使用 Sites。常规论文刷新不需要重新部署网站。
