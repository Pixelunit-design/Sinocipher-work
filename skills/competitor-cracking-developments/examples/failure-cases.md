# 历史错误与修正案例（examples/failure-cases.md）

> 每条格式：错误 → 根因 → 修正 → 预防。

## E1. sheetagent MCP 打不开本地 Excel
- 错误：`workbook is not open`，反复重试无效。
- 修正：回退 openpyxl 直读（`load_workbook` 两个目标文件均正常解析）。
- 预防：本地xlsx一律 openpyxl；MCP工具失败1次即切换，不重试。

## E2. scctc 旧版TLS连接失败
- 错误：首次请求报TLS握手错误。
- 修正：`ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT`（0x4）。
- 预防：接口脚本模板内置此行。

## E3. scctc 字段名猜错
- 错误：按直觉用 certificateNo/productVersion 等，解析出空值。
- 修正：打印 `records[0]` 全字段，确认真实字段 certificateCode/productModel/productType/productSecurityLevel 等。
- 预防：**任何API先打印首条记录再写解析逻辑**。

## E4. 明细表提取串行污染（行数偏少）
- 错误：合并单元格结构下公司块切换时 `cur_short` 未重置，证书归属串行。
- 修正：`cur_short = c1 if any(t in c1 for t in targets) else ''`，跨sheet按 `(src,no,name,model)` 去重。
- 预防：处理"块状合并"结构时，块切换必须显式重置游标。

## E5. `wb.save()` 失败（非法fill对象）
- 错误：`cell.fill = None` 清样式产生非法填充对象，保存崩溃。
- 修正：`if fill is not None: cell.fill = fill`；已用独立脚本复现验证。
- 预防：openpyxl 禁止给样式属性直接赋 None。

## E6. 并行 Edit 同一文件丢改动
- 错误：多个 Edit 并行调用同一文件，部分改动静默丢失（companies列表、标题等未生效）。
- 修正：改为串行逐个 Edit 重做。
- 预防：**同一文件的多次编辑必须串行**。

## E7. NameError：summary_all 未加载
- 错误：改造排行榜函数时误删加载语句，运行报 NameError。
- 修正：在依赖数据加载位置补回。
- 预防：重构脚本时先梳理数据依赖链再动刀；改完立即跑通。

## E8. FIPS计数虚高（每家凭空+1）
- 错误：汇总表"FIPS认证：—"占位行被当记录。
- 修正：`fips_real()` 过滤 `no in ('','—','None')`。
- 预防：计数类统计必须过滤占位/表头/空行。

## E9. PowerShell 中文乱码 + 日志目录不存在
- 错误：无BOM UTF-8 .ps1 被 PowerShell 5.1 按 ANSI 解析，中文全乱；render 目录不存在致日志写入失败。
- 修正：纯ASCII脚本 + `$env:USERPROFILE` 拼中文路径 + 先建目录。
- 预防：Windows COM 验证脚本一律纯ASCII。

## E10. Excel 渲染显示 `####`
- 排查：Excel 2007 COM 打印引擎对"数字+自动换行"的渲染bug，`cell.Text` 实际正常，非文件问题。
- 处置：数字单元格改"居中+不换行"（CENTER_NW）规避。
- 预防：数字单元格永远不与 wrap_text 混用。

## E11. ipv6_products.json 保存失败
- 错误：脚本漏 `import json`，NameError。
- 处置：数据已从 stdout 完整获取，未修复文件但结果无损。
- 预防：长脚本顶部集中管理 import；落盘失败时先确认 stdout 是否已含完整数据。

## E12. 总览矩阵溢出列无样式
- 错误：加入江南科友后 `NW=11` 未同步为12，产品表ISO列溢出。
- 修正：NW 改12，ISO列跨 K:L 合并。
- 预防：列数常量与合并范围引用同一常量，不硬编码。

## E13. 引用过期路径
- 错误：`F:\桌面\市场营销内容\` 不可访问。
- 排查：确认用户已迁移至 `D:\市场营销内容\`。
- 预防：访问用户文件前先 `ls` 确认路径存在；路径变更记入 context.md。
