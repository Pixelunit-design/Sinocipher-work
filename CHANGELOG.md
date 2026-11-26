# 更新记录

## 首次发布候选 · 2026-11-26

以下记录对应本地准备内容，实际发布后补充 Release 链接。

### sinocipher-news-weekly 1.0.0

- 收录安全资讯周览、速览与续期改稿工作流及全部参考资料。
- 在 `metadata.version` 记录版本；规范文本换行。

### competitor-wechat-monitor 1.0.0

- 收录竞品内容监测流程、HTML 模板、两个 Python 脚本及两份 Excel 数据。
- 将顶层 `version` 移到 `metadata.version`，移除非标准的 `agent_created`。
- 修正脚本说明中的 `--file` 参数、请求间隔描述及过度确定的获取效果表述。
- 按当前平台交付文件，避免绑定 `present_files` 和固定工作区根目录；说明正确安装层级。
- 第三方服务说明保留为原包参考，明确接口和部署未在本次验证。

### competitor-cracking-developments 1.0.0

- 收录竞品动态调研（按动态属性分章）、资质对比 Excel、单项资质对标与台账回填四类工作流及全部参考资料。
- 数据自包含：商密/网专/IPv6/FIPS/EPRI 快照 JSON、163 家企业名单、54 条历史事件库及 8 期历史报告全文（跨期去重依据）；数据口径与缺失清单集中在 `data/README.md`。
- 商密数据经 scctc 官方接口 2026-11-26 全量刷新；IPv6 明细经官方接口实测抓取入库（`data/ipv6_ready.json`）。
- 附数据刷新、一致性校验、Excel 生成（需 openpyxl）与 IPv6 抓取（仅标准库）四个脚本及自动化测试。
- 版本记录在 SKILL.md 的 `metadata.version`。

前两者尚未在远端发布；首次版本号沿用原 ZIP 的 1.0.0。若原包已经对外正式发布，请为本次改动递增版本并同步所有版本引用。
