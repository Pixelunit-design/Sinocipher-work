# 更新日志

## v1.0.0（2026-11-26）✅ 已定稿

首次封装定稿。来源：2026-09-07 至 2026-11-20 真实工作会话（BSI认证调研 → 资质对比Excel → IPv6对标 → 六期竞品动态报告 → 台账回填）。

> **定稿状态**：2026-11-26 经三轮外部审查修复后用户确认定稿。定稿ZIP：`outputs/competitor-cracking-developments-v1.0.0.zip`（45文件/427KB，剔除 data/backup、__pycache__、包内测试日志）。数据快照：商密2026-11-26全量刷新；IPv6明细94+9条入库 data/ipv6_ready.json；事件库54条。待决事项：①中安云科IPv6实抓9条 vs 用户确认6条口径待裁决；②GB/T 35275-2026起草单位身份待核验。后续修订须升级版本号并经用户确认。

### 包含
- SKILL.md：YAML front matter（name/description）+ 任务路由 + 7条核心规则 + 数据规则（详见 data/README.md）+ 质量检查清单
- **data/**（数据自包含层，说明唯一入口 data/README.md）：6个数据快照JSON（中安云科92+6条、11家竞品1116+103条明细、163家企业全称对照，快照日2026-09-07）+ 数据字典与更新指南
- **scripts/update_data.py**：可独立运行的数据刷新脚本（直连scctc官方接口，含旧版TLS兼容，全刷/单刷），已实测拉通（验证时三未信安实时180条 vs 快照179条）；单刷模式并入现有数据不覆盖
- references/×6：context / knowledge / preferences / decisions / workflows / constraints
- examples/×2：5个成功案例、13个错误修正
- templates/×1：报告HTML骨架、台账五段式与周度模板、固定检索词组、总结口吻
- archive/conversation.md：会话压缩时间线 + 缺失清单
- assets/README.md：未嵌入资源清单

### 已知边界
- 行业情报快照截至 2026-11-20，需执行时重新验证
- 中安云科截图原件、用户文档原件、build_qual_xlsx.py 全文未嵌入（清单见 assets/README.md）

### 修订记录（v1.0.0 内，2026-11-26 第三轮 · 依据第二轮审查报告（78/100）修复，全部P0落地+自动化实测）

**P0修复**：
- build_excel.py 路径重构：移除C/F盘硬编码，改为 `Path(__file__)` 包内相对定位（输入 data/、输出 outputs/），冷启动直接运行实测通过
- build_excel.py 排行榜口径修正：国密榜拆分为【有效证书榜】（仅已核验11家，中安云科=34，快照2026-09-07）与【历史总量榜】（163家总数口径独立成榜）；152家未核验企业不进有效榜、不按零处理；网专/IPv6/EPRI/FIPS标明记录数口径
- build_excel.py 数据优先级：江南科友双数据源冲突消除（competitor_gm_detail.json 优先，jnkf_gm_detail.json 为种子；刷新后Excel自动用新数据——T10实测）
- README 依赖说明修正 + 新增 requirements.txt（build_excel 需 openpyxl）
- competitor_gm.json 数据治理：补齐渔翁/科友计数（明细同源）、逐企业 snapshot_date、吉大正元状态"3"统一为"待确认"
- update_data.py v1.2：中安云科/江南科友旧数量从正确文件读取（骤降保护全覆盖）；未知状态码→"待确认"+告警；刷新后自动运行校验；退出码0/1/2；按企业记录快照日期，仅全量成功才更新全局日期
- validate_data.py v3 强制校验：汇总status计数和==total、有效数汇总vs明细交叉核对、证书编号重复、企业覆盖、refreshed_at完整性、必填字段、未知状态、中安云科口径34核对

**P1修复**：
- events.jsonl 来源字段结构化（type/publisher/title/url/published_at/verified_at/evidence_level；历史URL缺失留null标待核验不编造）+ company_id/last_verified 字段
- evidence-policy.md v2：来源权威性/信息性质/核验状态三维拆分，澄清 L3官方披露 vs L6厂商自述 vs L2单一官方公告的边界
- 检索覆盖审计：companies.json 纳入检索流程（core逐家独立检索/watch方向级合并）；新增 state/search-coverage.json
- 跨平台适配：SKILL.md 规则6/7改为通用文件交付+状态持久化三件套（events/state/报告），present_files 与 .workbuddy/memory 降级为WorkBuddy可选
- ZIP打包改用 python zipfile 正斜杠路径（T12实测无反斜杠路径、CRC完整）

**自动化测试**：新增 tests/test_all.py（冷启动临时副本执行），21项测试全部通过（T1-T12，含Excel生成/13sheet顺序/中安云科34/有效口径11家/接口异常不破坏数据/骤降保护/科友新数据生效），日志 tests/test-log-2026-11-26.txt。

**未解决（如实）**：events.jsonl 36条为种子库未逐条覆盖7期报告全部动态；历史来源URL不可恢复；WebSearch覆盖率无法程序化保证；company-profile 产品矩阵等【缺】项待用户补充。

### 修订记录（v1.0.0 内，2026-11-26 第二轮 · 依据第一轮审查报告（64/100）修复）

**P0修复**：
- 自包含冲突清除：workflows.md 流程B改为"data/快照优先+降级策略"，流程D台账不可访问时生成回填块交付，不再强制依赖 D盘/F盘文件
- 模板引用统一：report-html-skeleton/ledger-template 等失效引用全部改为 templates/templates-all.md
- 历史去重基础设施：新增 data/events.jsonl（36条事件种子库）+ state/research-state.json（调研状态）+ state/report-index.json（报告索引）+ outputs/（7期报告全文嵌入）
- update_data.py 四项逻辑缺陷修复：①中安云科默认排除（用户口径保护）②快照日期自动更新 ③响应结构校验+数量骤降保护+备份+原子写入 ④范围限制如实声明
- 数据口径统一：data/README.md 建立权威来源优先级链；明确 summary_all 为总数口径禁作有效数排名；状态码补"3=待确认"（快照中1条已修正）；IPv6字段结构差异说明
- 规则冲突清理：D10 澄清（台账用日期区间/报告文件名可用第N周）；刷新规则统一为"资质类必刷+校验，动态类可选"

**P1补充**：
- 新增 references/company-profile.md（公司档案，【缺】项显式标注，启示输出规则）
- 新增 references/evidence-policy.md（L1-L6证据等级 + 事实/推断/判断分离规则）
- 新增 config/companies.json（163家结构化名单，core 10家/watch 153家）
- 新增 scripts/validate_data.py（7类一致性检查）+ tests/acceptance-tests.md（T1-T5验收标准+冷启动验收标准）
- 新增 scripts/build_excel.py（13-sheet Excel生成脚本全文嵌入，来自实际会话产物）

**已知边界（更新）**：网专19条仍无明细；IPv6明细缺失；7月/8月/BSI报告未嵌入；公司产品矩阵/研发路线等仍为【缺】待用户补充。

### 修订记录（v1.0.0 内，2026-11-26 第一轮）
- **报告分类框架变更（D15）**：动态报告章节改为按动态属性分类（中标订单/产品发布/政策标准/资质认证/安全事件/市场情绪），不再按四大业务方向分章；SKILL.md规则2、workflows.md流程A、templates骨架同步更新。
- 新增备用检索路径记录：WebSearch被审批拦截时改用 domain_search 多源调研通道（2026-11-26实测可用）。
- 首个实测报告：`outputs/2026年11月末竞品动态快报（11.21-11.26）.html`。

### 版本规则
- **用户确认定稿前不得升级版本号**；所有变更先以草稿形式向用户提交确认。


### 第三轮修订（2026-11-26 晚 · 依据第三轮外部审查报告）

**P0（全部修复并实测）**
- requirements.txt 第4行 `pip install openpyxl>=3.0` → `openpyxl>=3.0`（原写法pip直接报错）；T13新增依赖合法性测试
- build_excel.py 硬编码冲突清零：①改为读取 competitor_gm.json（权威有效数/快照日期源），"差距①~③"文本全部动态生成（三未88→81随数据自动更新）；②各处写死的"快照2026-09-07"改为 REFRESH_NOTE 动态拼接（逐企业 refreshed_at）；③EPRI权威口径统一为用户汇总表（北京CA 0vs1 跨Sheet打架消除）；④吉大正元"待确认"状态计入标题（56+51+16+1=124 对齐）；⑤排行榜 render_block 的 zayk_in 改查 top 而非 lst（中安云科50名外静默消失+死代码修复）；⑥区分"用户确认0条（EPRI）"与"未核验"
- 中安云科网专19条明细自脚本硬编码迁入 data/zayk_certs.json cac 字段（文档三处"仅计数无明细"说法同步收口）
- 包内预生成Excel已用刷新后数据重新生成，表内数字与说明文字一致（T14a自动校验）

**P1**
- update_data.py：update_readme_date() 适配新版README（不匹配旧前缀则追加"最近全量刷新日"行）；未知企业名/空目标退出码3（原静默0）；新增别名表（数字认证→北京CA等）；实测全量刷新成功（10家竞品2026-11-26刷新：北京CA 58→60、吉大正元 56→58、信安世纪 71→66、格尔 41→44），validate 0错误
- test_all.py：T11a按文件实际存在计数（原误报11期嵌入）；T12改为测真实发布ZIP；新增T13依赖检查、T14a差距文本一致性、T14b公司sheet标题计数加总、T14c EPRI跨Sheet一致；测试日志改写包外outputs/（源码目录不再污染）；28项测试全部通过
- events.jsonl：32条证据等级按 evidence-policy v2 重定级（L1×13/L2×15/L3/L5×6/L6×12）；company_id统一全称；last_verified补齐；11.26快报补查后入库54条
- 11.26增量快报修复：HTML多余</td>；每块标注证据等级；删除越界的"ML-DSA+ML-KEM软件升级"承诺（改调研建议）；补查4家漏查核心竞品（江南天安/海泰方圆/江南科友/数盾），10家核心全覆盖
- **流程C落地**：新增 scripts/fetch_ipv6.py（接口实测直接返回JSON total=907；分页+vendor_name过滤+零结果拒写），10家竞品94条+中安云科9条入库 data/ipv6_ready.json——"IPv6明细缺失"正式解决（中安云科实抓9条 vs 用户确认6条，差异已标注待用户裁决）
- 11.26补查重大发现：GB/T 35275-2026国标起草单位名单含中安云科（L2待核验）

**P2**
- context.md 公司全称统一为中安云科科技发展（山东）有限公司；"四大方向"标注为业务范围而非报告分类框架（对齐D15）
- templates-all.md 组合搜索词改逐家独立（对齐检索纪律）；companies.json 渔翁云简称+重复分类清理
- knowledge.md build_qual提及更新（已嵌入scripts/build_excel.py）+状态码补3=待确认；README 7期→8期
- SKILL.md/workflows.md/knowledge.md 检索承诺软化：核心10家逐家必查、watch按轮转+如实记录未覆盖；freshness为平台参数、通用平台用时间词+逐条核对
