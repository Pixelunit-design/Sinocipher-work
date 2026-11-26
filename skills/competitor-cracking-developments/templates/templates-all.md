# 模板一：周期动态报告 HTML 骨架（templates/report-html-skeleton.md）

文件命名：`2026年X月第N周竞品动态调研报告（MM.DD-MM.DD）.html`，存 outputs/。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: "Microsoft YaHei", sans-serif; max-width: 1080px; margin: 0 auto; color: #222; }
  .header { background: linear-gradient(135deg, #1a3a5c, #2c6e9e); color: #fff; padding: 32px; border-radius: 12px; }
  .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }
  .card { background: #f5f8fb; border-radius: 8px; padding: 14px; text-align: center; }
  h2.sec { border-left: 5px solid #2c6e9e; padding-left: 10px; margin-top: 36px; }
  .co { border: 1px solid #e3e9ef; border-radius: 8px; padding: 14px 16px; margin: 12px 0; }
  .co.prio { border-top: 3px solid #e67e22; }          /* 重点企业橙顶边 */
  .co-name { font-weight: bold; font-size: 1.05em; }
  .badge { display: inline-block; font-size: 0.75em; padding: 1px 8px; border-radius: 10px; margin-left: 8px; }
  .badge.hot  { background: #fdecea; color: #c0392b; } /* 重大 */
  .badge.warn { background: #fef5e7; color: #b9770e; } /* 风险 */
  .badge.new  { background: #e8f6f3; color: #148f77; } /* 新品 */
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  th, td { border: 1px solid #dde5ec; padding: 7px 10px; font-size: 0.92em; text-align: left; }
  tr:nth-child(even) { background: #f7fafc; }           /* 斑马纹 */
  .insight { background: #eef4fb; border-left: 4px solid #2c6e9e; padding: 12px 16px; margin: 16px 0; }
</style>
</head>
<body>
  <div class="header">
    <h1>2026年X月第N周竞品动态调研报告</h1>
    <p>监测区间：2026-MM.DD — MM.DD ｜ 出具日期：… ｜ 与上期（报告名）去重</p>
  </div>
  <div class="cards"><!-- 4个数据卡片：企业动态条数/中标条数/政策条数/国际条数 --></div>

  <h2 class="sec">〇、本期一句话</h2>
  <div class="insight">…</div>

  <h2 class="sec">一、中标与订单</h2><!-- 表：日期/企业/项目与金额/形态信号 -->
  <h2 class="sec">二、产品发布与技术动作</h2><!-- .co 条目，重点 .co.prio -->
  <h2 class="sec">三、政策与标准</h2><!-- 表：日期/事项/意义 -->
  <h2 class="sec">四、资质与认证</h2>
  <h2 class="sec">五、安全事件与风险警示</h2>
  <h2 class="sec">六、市场情绪（可选）</h2>
  <h2 class="sec">七、对中安云科的启示</h2><!-- .insight 盒，每条可执行 -->
  <h2 class="sec">八、待复核</h2><!-- 单一信源条目集中列出 -->
  <!-- 注意：按动态属性分类，不按密码/身份/数据/零信任业务方向分章（2026-11-26定稿） -->
</body>
</html>
```

要点：重点条目用 `.co.prio`；中标订单必须表格化且含"形态信号"列（解读采购形态规律）；每条必须有日期；单一信源加"（待复核）"或集中列在待复核章。

---

# 模板二：台账每日记录五段式（templates/ledger-template.md）

```markdown
## 2026年X月X日（周X）竞品动态调研

**2.1 今日调研主题**：一句话（对应报告文件名，出具日期）

**竞品动态观察**

| 方向 | 企业 | 动态要点 | 时间 |
| --- | --- | --- | --- |
| 密码安全 | … | … | … |

**市场机会判断**
- …（落在投标/选题/商务跟进）

**营销启发**
- …

**可沉淀选题**
1. 《…》——一句话角度
2. …

**观察结论**
一句话总判断。
```

## 模板三：台账周度汇总（templates/ledger-template.md §周度）

```markdown
## 2026 年 X 月（MM.DD—MM.DD）      ← 按日期区间命名，不用"第X周"

来源：《报告文件名》（出具日期，outputs 目录）。

| 项目 | 内容 |
| --- | --- |
| 本期调研重点 | … |
| 新增企业动态 | … |
| 新增产品/事件 | … |
| 新增政策/标准 | … |
| 新增技术线索 | … |
| 待复核信息 | …（单一信源条目列此） |
| 下期重点 | … |

### 3.1 本期竞品动态

| 能力方向 | 企业 | 动态 | 时间 | 是否进入月报 |
| --- | --- | --- | --- | --- |

### 3.2 本期判断

| 能力方向 | 本期发现 | 后续动作 |
| --- | --- | --- |
```

---

# 模板四：每期固定检索词组（templates/search-prompts.md）

全部加 `freshness`（周报d7/半月m1/快报d5）：

1. 核心竞品**逐家独立检索**（不得混搜，workflows.md §检索纪律）：`三未信安 密码 中标 发布 2026年X月`、`格尔软件 密码 中标 2026年X月`、`信安世纪 密码 中标 2026年X月`……（每家一条，从 config/companies.json priority=core 依次生成）
2. `深信服 安恒信息 绿盟科技 天融信 奇安信 零信任 AI安全 发布 中标 2026年X月`
3. `芯盾时代 竹云 数字认证 CFCA 北京CA 电子认证 身份安全 2026年X月`
4. `美创科技 天空卫士 明朝万达 闪捷信息 数据安全 新品 2026年X月`
5. `国家密码管理局 商用密码 政策 标准 密评 发布 2026年X月`
6. `Thales Entrust DigiCert Keyfactor HSM PKI post-quantum announcement <月份> 2026`
7. （事件追查）`电子认证业务规则 整改 备案 CA机构 2026年X月` / `三季报` / `<展会名> 网络安全 密码 新品`

---

# 模板五：文字总结口吻（templates/summary-style.md）

开头：报告名+监测区间+条数 → **三条最重要线索**（每条加粗小标题+2-4句展开，含对中安云科的直接含义）→ "其他要点速览"表 → "今天就能做的N件事" → 结尾二选一询问（回填台账/压周报/起草选题）。
语言：大白话+精确数字；比喻可用但克制（如"讲抗量子的人没赚到钱，做的人赚到了"）。
