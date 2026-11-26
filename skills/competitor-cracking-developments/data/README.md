# 数据层说明（data/README.md）

> **本文件是技能数据层的唯一集中说明**：数据字典、权威来源优先级、更新方法、缺失数据清单都在这里，其他文件只留指引不重复。
>
> **数据日期说明（按数据源分别记录，2026-11-26起）**：
> - **数据库建立日**：2026-09-07（全部JSON首次落盘）
> - **各企业商密最近刷新日**：见 `competitor_gm.json` 各条目的 `refreshed_at`（最新实测：2026-11-26 三未信安刷新）
> - **其他资质维度核验日**：网专/IPv6/FIPS/EPRI = 2026-07汇总表口径，无自动刷新
> - **最近全量刷新日**：2026-11-26（由 update_data.py 自动写入）
- **最近完整校验**：见运行日志；`python scripts/validate_data.py` 随时可复验
>
> 本目录让技能**自带数据、离线可查、可自行更新**，不依赖任何本地磁盘文件。部分刷新**不会**修改全局快照日期（防止误读为全库更新）。

## 文件清单与结构

| 文件 | 内容 | 结构与口径说明 |
|---|---|---|
| `zayk_certs.json` | 中安云科资质快照 | `gm`(商密92条) / `cac`(网专,空) / `ipv6`(6条)；商密字段：no/name/model/ver/type/level/issue/until/status；**IPv6记录字段不同**：logo_id/vendor_name/product_name/extended_test_category 等（来源接口不同，属正常差异） |
| `competitor_gm.json` | 竞品商密证书**汇总计数**（10家，含total与status分布） | `{企业全称: {total, status{...}, assignors{...}, snapshot_date, refreshed_at?}}`——**有效数的权威来源**；status字典只含状态键，备注在 status_note；snapshot_date/refreshed_at 按企业独立记录 |
| `competitor_gm_detail.json` | 9家竞品商密证书**明细**（1116条） | `{简称: [记录...]}`；状态码见下方映射；江南科友刷新后也会写入此文件（build_excel 优先读它） |
| `jnkf_gm_detail.json` | 江南科友商密明细（103条，有效44） | `[记录...]`（历史种子；科友经脚本刷新后与 competitor_gm_detail 同步更新） |
| `competitor_other_detail.json` | 10家竞品网专/IPv6/FIPS/EPRI明细 | `{简称: [{src,no,ptype,cat,name,model,ver,org,date,valid}...]}` |
| `summary_all.json` | **163家企业全量汇总**（182行分类记录） | `[{cat, short, full, wz, ipv6, gm, fips, epri}...]`——**gm/wz等为证书总数口径，非有效数**；同一企业可属多个方向（182行=163家企业的方向分类行），去重以 full 全称为准 |
| `events.jsonl` | **历史动态事件库**（去重依据，36条种子） | 每行一个JSON：event_id/company/company_id/event_type/event_date/title/summary/source(结构化对象：type/publisher/title/url/published_at/verified_at/evidence_level)/report_id/verification_status/first_seen/last_verified；**历史URL缺失保留null标待核验，不编造** |
| `backup/<日期>/` | 刷新脚本自动备份 | 同日多次运行只留首份 |
| `ipv6_ready.json` | IPv6 Ready 证书快照（fetch_ipv6.py 抓取） | meta.fetched_at 为抓取日；certs[].keyword 为匹配关键词；**首次抓取2026-11-26，10家竞品94条+中安云科，解决了此前"IPv6明细缺失"** |

状态码映射（scctc certificateStatus）：**0=有效，1=注销，4=过期，3=待确认**（实测见过1条吉大正元状态3，已统一标注"待确认"不计入有效）。

## 权威来源优先级（防止多文件口径冲突）

1. **中安云科**：用户确认口径（商密92=有效34/过期36/注销22、网专19、IPv6 6、EPRI 0）> 脚本刷新结果（仅旁证）
2. **竞品有效数**：`competitor_gm.json` 的 `status.有效`（逐企业取 snapshot_date/refreshed_at 最新）> 明细文件实数 > summary_all（总数口径，**禁止当有效数排名**）
3. **企业名录/全称**：`config/companies.json`（163家，与 summary_all 全称集合一致，由其派生）
4. **历史动态去重**：`events.jsonl`（event_id 唯一；重复判定=企业+事件时间+标题相似度三者综合，任一单独不构成判定）
5. **注意**：有效证书数据已核验的仅11家（10竞品+中安云科）。163家全量有效排行**数据不存在**，任何输出不得伪造；缺数据企业标"未核验"，绝不按零处理。

## 如何更新数据

### 路A：脚本刷新（商密证书；含安全机制）

```bash
python scripts/update_data.py            # 刷新10家竞品（默认排除中安云科）；完成后自动校验
python scripts/update_data.py 三未信安   # 只刷新一家
python update_data.py 中安云科           # 显式刷新中安云科（覆盖用户口径，慎用）
python scripts/validate_data.py          # 独立校验（0错误退出码0）
```

退出码：0=全部成功且校验通过；1=部分企业失败/被保护拒绝；2=刷新后校验失败。

安全机制：响应结构校验（异常不落盘）、数量骤降保护（<旧70%拒绝写入，旧数量按企业取正确数据源：中安云科=zayk_certs、江南科友=jnkf/明细）、未知状态码→"待确认"+告警、自动备份到 backup/<日期>/、原子写入、**按企业**记录 snapshot_date/refreshed_at；仅全量刷新成功才更新顶部全局日期。

**范围限制（如实声明）**：脚本只刷新商密证书。IPv6 Ready（ipv6testingcenter.com 按vendor_name查）、网专（CAC无公开API）、FIPS/EPRI/ISO/BSI（人工渠道）**均无自动刷新**，需按对应流程人工更新。

### 路B：手动规则（接口变更时）

```
接口: https://www.scctc.org.cn/ucenter/api/certificate/pageList
参数: certificateCategory=1 & assignorName=<企业全称> & current=<页> & size=50
状态: certificateStatus 0=有效 1=注销 3=待确认 4=过期
必须: ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
```

### 更新原则

1. 资质对比类任务前刷新+校验；动态周报不强制。
2. 校验0错误才能进对比流程；校验失败禁止发布正式快照。
3. 企业名录变更（新增/改名）需用户确认后同步改 summary_all.json 与 config/companies.json。
4. 数据冲突时按上方"权威来源优先级"裁决；无法裁决的标注双口径待用户确认。

## 缺失数据清单（不编造）

- 中安云科网专19条：仅计数无明细（CAC无公开API，用户截图口径）
- ~~IPv6逐条产品明细~~（已解决：fetch_ipv6.py + data/ipv6_ready.json）：仅对标结论（87 vs 6、缺口分类），需明细时重跑 ipv6testingcenter 接口
- 7月/8月/BSI三份历史报告原件：未嵌入，索引见 state/report-index.json
- events.jsonl 为种子库（36条），未逐条覆盖7期报告全部动态；历史来源URL未逐条存档（source.url=null待核验），溯源需重搜