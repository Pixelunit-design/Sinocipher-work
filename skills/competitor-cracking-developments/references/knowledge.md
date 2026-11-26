# 专业知识与业务规则（references/knowledge.md）

## 1. 官方数据接口（已验证可用）

### 1.1 商用密码认证证书（scctc.org.cn）

```
POST/GET: https://www.scctc.org.cn/ucenter/api/certificate/pageList
参数: certificateCategory=1 & assignorName=<企业全称> & current=<页码> & size=50
关键字段: certificateCode(证书编号) / productName / productModel / productVersion /
         productType / productSecurityLevel / issueDate / effectiveDate / certificateStatus
状态码: 0=有效, 1=注销, 4=过期, 3=待确认（吉大正元历史数据出现1条；详见 scripts/update_data.py STATUS）
```

**坑位**：服务器为旧版TLS，Python ssl 必须加：
```python
ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT  # 0x4
```
字段名不要猜——先打印 `records[0]` 看真实字段（曾猜 certificateNo/productVersion 全错，真实为 certificateCode/productVersion 之外另有 productModel）。

### 1.2 IPv6 Ready Logo（ipv6testingcenter.com）

```
https://www.ipv6testingcenter.com/index/index/cert_list.html
参数: vendor_name=<厂商名>（模糊匹配，需多轮尝试不同写法）
```

### 1.3 网专（CAC）与电科院

- 网专：`https://www.cac.gov.cn/cms/pub/interact/wa/wasearch.jsp` **无程序化权限**，以用户截图转录为准。
- 电科院：EPRI（epri.com.cn）报告检索平台，人工查询。

## 2. Excel 生成规则（openpyxl，已验证的完整脚本模式）

参考实现：`scripts/build_excel.py`（已嵌入本包，可直接运行生成13-sheet Excel）。

### 2.1 必守的坑位规则

| 规则 | 原因 |
|---|---|
| `cell.fill = fill` 必须写成 `if fill is not None: cell.fill = fill` | 赋值 None 会产生非法填充对象，`wb.save()` 直接失败 |
| 数字单元格用"居中+不换行"样式 | "数字+自动换行"在 Excel COM 打印渲染出现 `####`（cell.Text 实际正常） |
| 表头一律横向排列，禁止 `text_rotation=90` | 用户明确反感竖排文字；长列名用横向换行+加宽列+加高表头 |
| 合并单元格只给块首行写企业名，块切换时重置游标 | 否则明细提取/写入会串行污染 |
| `NW`（列数常量）加列时必须同步更新 | 曾因加入江南科友未同步导致溢出列无样式 |

### 2.2 对比表结构（13个sheet，用户确认的最终形态）

1. **对比总览**（第一个sheet，用户指定）：企业资质矩阵 ✔/✘/△ + 资质计数对比，通栏10列以上
2. **资质排行榜**（由"国密证书排行榜"改造）：不分四大方向，按各项资质分别排行（网专有哪些、国密有哪些…），各资质取前50，不足50删空行；前十标黄；并列名次算法 `rank = prev_rank if value == prev_value else k + 1`；跨方向按企业全称合并取各维度max；中安云科用官方口径单独构造记录
3. 中安云科（含4项ISO）
4. 10家竞品各一个sheet（三未信安、渔翁、江南天安、数盾、海泰方圆、北京CA、吉大正元、信安世纪、格尔、江南科友）
- 统一口径：**有效证书**；表头该合并就合并，不留无用空表
- 明细列序（源自资质汇总表）：row[1]简称 row[3]资质来源 row[5]编号 row[6]产品类型 row[7]产品类别 row[8]产品名称 row[9]型号 row[10]版本 row[14]机构 row[15]日期 row[16]有效期
- FIPS计数必须过滤占位行（`no in ('','—','None')` 的垃圾行），否则每家虚增1条

### 2.3 排序与编号规则（用户长期标准）

- 「序号」列 = 按排序规则的连续编号 1..N，原始编号另设「名录序号」列保留
- 主排序键 + 并列组内明确次级键（如证书数降序），口径写在说明页
- 对照/对比表用 ✔ / ✘ / △；产品类矩阵用 ✔

## 3. PowerShell / Excel COM 渲染验证（Windows）

- **纯ASCII脚本**：PowerShell 5.1 读无BOM UTF-8 .ps1 会按ANSI解析导致中文乱码；中文路径用 `$env:USERPROFILE` 拼接
- 前置：`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`；先建日志目录再写日志
- 用途：Excel COM 打开→逐sheet读 cell.Text→验证渲染；PyMuPDF(fitz) 可将PDF转PNG（`get_pixmap(matrix=fitz.Matrix(n,n), clip=fitz.Rect(...))`）

## 4. 行业情报库（按主题沉淀，写报告时直接引用）

### 4.1 电子认证新规（合规主线，2026-09至11）
- 文件链：**工信发函〔2026〕181号**《关于做好电子认证业务规则相关工作的通知》（任务布置）→ **工信部〔2026〕378号**（过渡期安排）→ **T/CQAE 11034-2025**（标准本体）
- 10-14 工信部推进会，58家CA参会；过渡期 10-30 到期；逾期按《电子签名法》《电子认证服务管理办法》处理
- 新规三要点：五环节（告知/身份核验/意愿确认/协议签署/数据留存）必须持牌CA直接完成不得委托；证书分级（高等级/基础级）；两条防规避红线
- 落地样例：湖南CA CPS V5.0（四条红线+人脸/双录颗粒度最细）、安徽CA V6.0、上海CA六条承诺、CFCA第六版、沃通CPS V2.0、北京CA终止事件型证书（10-30）、苏州"多因子事件证书"停服、东南大学个人证书两年期管理、广西公共资源"一证四步"
- 11-11 工信部注销2家CA许可证（7月已注销1家）→ "常态化监管"，被注销CA客户=确定性换证需求
- 事件证书停服→存量客户合规立项→单一来源原厂锁定：福建农信118万单一来源给北京数字认证 = **标准模板（预算区间80-150万）**

### 4.2 后量子（PQC）主线
- 时间表：ICCS 84候选算法（2026-09）→ 2027-06一轮评估完成 → 国标预计2027底-2028初 → 央行要求2027底前金融迁移试点；产品窗口期12-18个月
- 竞品动作：三未信安后量子中标269万+华能滇东337.3万；专利铺到"迁移率闭环检测""AI智能体抗量子MPC托管"；格尔双栈NGPKI+单证书双公钥+信通院首家验证；CFCA SVS-PQC签名验签服务器（ML-DSA-44/65/87+ML-KEM-512/768/1024，NIST 5级）=CA系首款PQC硬件
- 技术情报：RFC 9955警告混合签名剥离/降级风险（对冲格尔双公钥路线的现成论据）；ML-DSA签名3.3KB vs ECDSA 64B（~50倍体积膨胀=存量密码机容量重估=升级采购触发器）；FIPS 140-2已于2026-09-21日落；全球公共CA均未签发PQC证书
- 财务印证（2026三季报）：三未信安唯一扭亏（归因芯片+抗量子落地）；格尔抗量子声量最大但Q3由盈转亏——"讲的人没赚到钱，做的人赚到了"

### 4.3 智能体（Agent）身份安全主线
- 30天内微软/Okta/ServiceNow/格尔/芯盾/天融信六家落子；品类从"管人"扩展到"管Agent"
- 合规依据：T/BFIA 070-2026《智能体技术金融应用安全要求》可写进投标书
- 芯盾时代核心论点："授权合法≠行为合法"
- 深信服中标全国海关"基于AI的网络安全智能体"87.66万=AI智能体首次进中央部委采购品目
- 密评联委会《生成式人工智能系统密码应用指引》：五大类风险+三层框架（通用基线+专属防护+增强防护），衔接GB/T 39786——AI场景方案书直接引用此表述

### 4.4 中标形态规律（报价底稿）
- 政务云密码服务已成独立采购品目：格尔崇明卫健286万；宁波政务云二期BJCA全栈15分项报价（4.99万-16万区间）+信安世纪国密负载均衡
- 电力市场=联合体打法：广东电网第四批（南瑞信通+三未联合体/渔翁），智能密码钥匙曾流标（投标人不足=捡漏入口）
- 存量锁定：信安世纪中原银行SSL网关单一来源；江南天安"整机新购+年度维保"滚动锁定
- 人天服务价格战（中国银行2800人天：189万/117.6万/85万，差2.2倍）→ 密码设备因资质壁垒价格坚挺
- 投标教训：绿盟340万项目因投标函/授权书未签字符合性审查出局 → 标书签署双人复核

### 4.5 国际厂商跟踪点
Thales（Luna 8后量子HSM、Mistral IP9100）、Entrust（nShield 5原生PQC固件）、DigiCert（澳洲国家能源PKI=行业级设备PKI标杆；数据泄露事件=核验材料保管警示；Quantum Central）、Keyfactor、Microsoft Project Perception、Okta、Cloudflare（70%浏览器流量混合ML-KEM但源站仅15%）。

## 5. 搜索方法论

- 每期6-12组检索；WorkBuddy WebSearch 带 `freshness` 参数（周报d7、半月m1、快报d5）；其他平台把时间词写进查询串并逐条核对日期。WebSearch被拦截时切换备用多源通道（workflows.md §检索纪律）
- 固定检索组：①密码上市公司（三未/格尔/信安世纪/吉大正元/数字认证）②零信任厂商（深信服/安恒/绿盟/天融信/奇安信）③身份安全（芯盾/竹云/安讯奔/CFCA/北京CA）④数据安全（美创/天空卫士/明朝万达/闪捷）⑤政策标准（国密局/工信部/网信办/密评）⑥国际（Thales/Entrust/DigiCert/Keyfactor + PQC/PKI关键词）⑦特定事件追查（新规落地/三季报/展会）
- 搜索习惯：先用企业简称检索，再用全名核对确认
- 展会情报（安博会/乌镇/世界互联网大会）单独设一组检索词
