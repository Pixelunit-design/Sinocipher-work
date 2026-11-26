# competitor-cracking-developments

中安云科市场部竞品情报调研技能包 v1.0.0（从 2026-09 至 2026-11 真实工作会话中提炼封装）。

## 这个技能做什么

1. **周期竞品动态调研**：按周/半月/快报节奏，检索竞品动态，按**动态属性**分类（中标订单/产品发布/政策标准/资质认证/安全事件）生成带监测区间、逐条溯源、与上期去重的 HTML 报告，并给出对中安云科可执行的启示。
2. **资质对比 Excel**：国密（商密认证）/网专/IPv6 Ready/电科院EPRI/FIPS/BSI/ISO 多维度竞品对比，官方接口实时校准，13-sheet 标准结构。
3. **单项资质对标**：如 IPv6 补证策略（P0/P1/P2 路线 + 投标应急对策）。
4. **台账回填**：按用户既有五段式格式追加《2026年市场调研日常周常台账.md》。

## 数据自包含

技能内置数据快照，装上即可用，不需要访问本地电脑；数据刷新靠自带脚本。数据日期按数据源分别记录：数据库建立日 2026-09-07，商密最近全量刷新 2026-11-26（`update_data.py` 刷新后自动更新），IPv6 明细可随时用 `fetch_ipv6.py` 实时拉取。**数据层说明（数据字典、权威来源优先级、更新方法、缺失清单）全部集中在一个文件：`data/README.md`。**

## 安装

将整个 `competitor-cracking-developments/` 文件夹放入 Agent Skills 技能目录：
- 用户级：`~/.workbuddy/skills/competitor-cracking-developments/`
- 项目级：`{workspace}/.workbuddy/skills/competitor-cracking-developments/`

运行期依赖：
- Python3 标准库：`update_data.py`（刷新）、`validate_data.py`（校验）与 `fetch_ipv6.py`（IPv6抓取）无需任何第三方包
- **`build_excel.py`（Excel生成）需要 openpyxl**：`pip install -r requirements.txt`
- WebSearch 类联网检索工具（动态调研任务）

## 调用方式

对 AI 说以下任意一类话即可触发：

- 「查询最新竞品动态」「看看他们都在发布什么」→ 周期动态报告
- 「帮我做竞品资质对比 Excel」「国密证书对比」→ 资质对比表
- 「查一下 IPv6 各家都有什么产品，怎么补齐不被卡标」→ 单项对标
- 「把报告按台账格式回填」「压成周报摘要」→ 台账/摘要

调用示例（新会话冷启动）：

> "查询最近一周竞品动态" —— AI 会读取 SKILL.md → 按 workflows.md 流程A 执行 → 需要接口细节时读 knowledge.md §1 → 输出 HTML 报告 + 三条线索总结 + 主动询问回填台账。

## 文件结构

```
competitor-cracking-developments/
├── SKILL.md                    # 技能入口（YAML front matter + 核心规则 + 数据规则）
├── README.md                   # 本文件
├── CHANGELOG.md                # 版本记录（用户确认定稿前不得升级版本）
├── config/
│   └── companies.json          # ★163家重点企业结构化名单（core/watch优先级+方向分类）
├── data/                       # ★内嵌数据快照（装上即用）
│   ├── README.md               # ★数据层说明唯一入口（字典/权威优先级/更新/缺失清单）
│   ├── zayk_certs.json         # 中安云科：商密92条 + 网专19条 + IPv6 6条（含实抓9条待裁决）
│   ├── competitor_gm.json      # 竞品商密计数（有效数权威来源，2026-11-26全量刷新）
│   ├── competitor_gm_detail.json / jnkf_gm_detail.json # 竞品商密明细1116+103条
│   ├── competitor_other_detail.json # 网专/IPv6/FIPS/EPRI明细
│   ├── ipv6_ready.json         # IPv6 Ready明细（10家竞品94条+中安云科9条，fetch_ipv6.py产出）
│   ├── summary_all.json        # 163家全量汇总（总数口径）
│   └── events.jsonl            # ★历史动态事件库（去重依据）
├── state/
│   ├── research-state.json     # ★调研状态（上期截止/待办/去重规则）
│   ├── report-index.json       # 历史报告索引
│   └── search-coverage.json    # 检索覆盖记录（已检索/未检索可审计）
├── scripts/
│   ├── update_data.py          # ★数据刷新（结构校验/骤降保护/备份/原子写入/自动复验/退出码）
│   ├── validate_data.py        # ★数据一致性校验（有效数交叉/状态和/编号重复/覆盖/时间戳）
│   ├── build_excel.py          # ★资质对比Excel生成（包内相对路径，直接运行；需openpyxl）
│   └── fetch_ipv6.py           # IPv6 Ready证书抓取（官方接口，仅标准库）
├── requirements.txt            # Python依赖（openpyxl）
├── tests/
│   ├── acceptance-tests.md     # ★五类任务验收标准 + 冷启动验收标准
│   └── test_all.py             # ★自动化测试脚本（python tests/test_all.py 直接执行）
├── references/                 # context / company-profile / evidence-policy / knowledge / preferences / decisions / workflows / constraints
├── examples/                   # success-cases.md / failure-cases.md
├── templates/
│   └── templates-all.md        # 报告HTML骨架/台账模板/检索词组/总结口吻
├── outputs/                    # 2026年10月以来8期报告全文（去重原文依据）
├── assets/
│   └── README.md               # 未嵌入资源清单（无编造）
└── archive/
    └── conversation.md         # 原始对话压缩时间线
```

## 完整性说明

- 技能**数据自包含**：资质类任务开箱即用（快照），联网刷新可选（脚本）。
- 无法获取的内容已在 `assets/README.md` 与 `data/README.md` 明确列出，未做任何编造。
- 行业情报快照截至 2026-11-20，执行时必须重新检索验证（constraints.md 时效声明）。
