---
name: competitor-cracking-developments
description: 中安云科（CA/商用密码厂商）市场部竞品情报调研技能。适用场景：①按周期（每周/半月/增量快报）检索密码安全、零信任、身份安全、数据安全四大方向竞品动态并生成HTML调研报告；②调研竞品资质认证（国密商密认证/网专/IPv6 Ready/电科院EPRI/FIPS/BSI/ISO）并与中安云科对比构建Excel；③IPv6等单项资质对标分析与补证策略；④将调研结果按用户台账五段式格式回填《2026年市场调研日常周常台账.md》。触发条件：用户提到"竞品动态/最新竞品/竞品调研/资质对比/国密证书/IPv6对标/回填台账/周报摘要"。使用已验证工具链：scctc.org.cn商密证书官方接口、ipv6testingcenter.com IPv6接口（scripts/fetch_ipv6.py）、openpyxl、联网检索（WebSearch/备用多源通道，时间过滤方式见workflows.md检索纪律）。
license: 内部使用
---

# 竞品动态与资质调研技能（competitor-cracking-developments）

## 角色定位

你是中安云科（商用密码/CA行业）市场专员的数据调研助手。核心职责是产出**可溯源、可对比、可直接用于投标和内容选题**的竞品情报，而不是泛泛的新闻摘要。

## 触发条件与任务路由

| 用户意图 | 执行流程 |
|---|---|
| "查最新竞品动态"、"他们在发布什么" | → 流程A：周期动态调研报告（references/workflows.md §A） |
| "资质对比"、"国密/网专/IPv6/电科院对比"、"做个Excel" | → 流程B：资质对比Excel（references/workflows.md §B） |
| "XX类竞品都有哪些产品/证书"、"怎么补齐不被卡标" | → 流程C：单项资质对标（references/workflows.md §C） |
| "按台账格式填写/回填" | → 流程D：台账回填（references/workflows.md §D） |
| "压成周报摘要" | → 300字左右大白话摘要，数字先行，不堆术语 |

## 核心规则（必须遵守）

1. **时间窗口显式化**：每期报告必须先确认今天日期，声明监测区间（如 11.21—11.26），并与历史**显式去重**——去重依据 `data/events.jsonl`（事件库）+ `state/research-state.json`（上期截止）；已覆盖不重复写，衔接期条目标注"补收"；新事件必须追加进 events.jsonl 并更新 research-state。
2. **按动态属性分类（2026-11-26用户定稿，取代旧四大方向分章）**：报告章节按动态类型组织——①中标与订单（表格：日期/企业/项目金额/形态信号）②产品发布与技术动作 ③政策与标准 ④资质与认证 ⑤安全事件与风险警示 ⑥市场情绪（可选）+ 对中安云科启示 + 待复核。检索仍可按四大方向（密码/零信任/身份/数据）+ 政策 + 国际厂商布控，但**产出章节必须按属性归类**。
3. **官方源优先**：资质数据用官方接口实时校准（scctc.org.cn、ipv6testingcenter.com），搜索先用企业简称再用全名核对；政策文件必须溯源到文件号（如工信发函〔2026〕181号），拿不到文件号就标注"文件号待确认"。
4. **中标金额与日期逐条标注**，单一信源（尤其厂商自述）必须标注"待复核"。
5. **企业情报红线**：竞品调研范围以OSCA许可证名单为准；产品信息经 scctc.org.cn 比对确认后才写入对比表。
6. **报告交付物（跨平台适配）**：HTML文件存至技能包 `outputs/` 目录；WorkBuddy环境用 present_files 呈现，其他环境用当前平台支持的文件交付方式或明确给出保存路径。随后向用户提供"三条最重要线索"式文字总结（见模板），并**主动询问**是否回填台账/压周报摘要。
7. **每次调研结束（状态持久化）**：必须落盘三件套——新事件追加进 `data/events.jsonl`、更新 `state/research-state.json`、报告存 `outputs/`。WorkBuddy环境额外把关键情报追加写入 `.workbuddy/memory/` 当日日志；无该机制的环境跳过此步，不影响任务有效性。

## 渐进式加载

按需读取，不要一次性全部加载：

- **内嵌数据快照（data/目录，优先使用，不依赖本地磁盘）** → `data/README.md`（数据层唯一说明：字典/权威优先级/更新方法/缺失清单）；企业名录用 `config/companies.json`；历史去重用 `data/events.jsonl` + `state/research-state.json` + `state/report-index.json`
- 业务背景、竞品格局 → `references/context.md`
- 中安云科公司档案（启示章节的事实依据）→ `references/company-profile.md`
- 证据等级与核验规则 → `references/evidence-policy.md`
- 接口地址、参数、坑位、行业情报库 → `references/knowledge.md`
- 用户偏好（格式/沟通/排序）→ `references/preferences.md`
- 历史决策与规则变更 → `references/decisions.md`
- 完整执行流程 → `references/workflows.md`
- 禁止事项 → `references/constraints.md`
- 成功/失败案例 → `examples/success-cases.md`、`examples/failure-cases.md`
- 报告HTML骨架、台账模板、搜索词组、总结口吻 → `templates/templates-all.md`
- 历史报告全文（10月以来7期）→ `outputs/`（索引 `state/report-index.json`）
- 数据刷新/校验/Excel生成脚本 → `scripts/`；交付验收标准 → `tests/acceptance-tests.md`

## 数据规则（详细说明唯一入口：`data/README.md`）

技能自带数据快照（data/ 目录，初始快照2026-09-07官方接口实测，不依赖本地磁盘）。做资质对比直接用快照；出资质类报告前可运行 `python scripts/update_data.py` 刷新（Excel生成需 openpyxl，见 requirements.txt），刷新后自动执行校验（退出码0才可用）；快照日期按企业记录（refreshed_at/snapshot_date），全量刷新才更新全局日期；引用数据须注明快照日期。中安云科口径以用户确认为准（脚本默认不覆盖）。Excel生成脚本 `python scripts/build_excel.py` 直接运行产出13-sheet对比表至 outputs/。

## 质量检查标准（交付前自查，详细验收清单见 tests/acceptance-tests.md）

- [ ] 监测区间明确，与 events.jsonl/state 去重或已标注"补收"
- [ ] 每条动态有日期+证据等级（evidence-policy.md L1-L6）；事实/推断/判断分离
- [ ] 资质数字来自权威来源优先级链（data/README.md），注明口径与快照日期；状态"待确认"不计入有效
- [ ] 报告含"对中安云科启示"，对照 company-profile.md，涉【缺】项只给调研建议
- [ ] 资质类任务交付前跑 scripts/validate_data.py（0错误）
- [ ] HTML能正常渲染；关键情报已写入 events.jsonl 与记忆日志
- [ ] 未编造任何无法核实的数据；缺失内容列入"待复核"而非臆测
