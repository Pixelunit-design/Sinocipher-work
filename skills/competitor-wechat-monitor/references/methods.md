# 内容获取方法手册

## 第一节 微信 User-Agent 公开页面获取（需按实际结果判断）

### 原理
请求 mp.weixin.qq.com 公开文章时，可尝试使用含 `MicroMessenger` 的微信内置浏览器 User-Agent。能否返回正文取决于实际页面和访问策略；本次发布整理未重新验证线上可用性。返回验证页或缺少正文时停止该路径，改用可取得的公开转载或用户提供材料。

### 用法
脚本：`scripts/fetch_mp_article.py`（多篇请求之间内置1.5—2.5秒随机延迟）。

curl 模板：
```bash
curl -sL -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x16082222) NetType/WIFI Language/zh_CN" "https://mp.weixin.qq.com/s/xxxx"
```

Python urllib/requests 均可，用 `python -X utf8` 运行避免中文乱码。

### 使用注意事项（红线，必须遵守）
1. 多篇请求之间保留脚本内置的1.5—2.5秒随机延迟，严禁高频连续请求，防止IP被限制；
2. 微信随时可能调整策略，返回验证页/无 `js_content` 即视为失效——如实告知用户，改用搜狗微信搜索（weixin.sogou.com）/行业媒体转载兜底；
3. 抓取内容仅用于内部存档/竞品分析参考，**不得搬运发布**（版权合规）；
4. 仅抓公开文章页面，不尝试登录态、不逆向API。

### 高效聚合情报源
- **TOP7·厂商资讯聚合** 公众号：每日汇总各厂商公众号动态，周报优先用它。
- 搜狗微信搜索 weixin.sogou.com（搜文章标题/公众号名）。
- FreeBuf / 安全客 / 嘶吼 / 安全牛 / cn-sec 转载监测。
- 巨潮资讯网（上市公司公告，中标/业绩类）。

## 第二节 wechat-download-api 本地服务（全量拉取，可选）

以下第三方服务的接口、认证、限频、有效期与部署说明沿用原包记录，本次未验证；使用前按上游当前文档确认。

仓库：https://github.com/tmwgsicp/wechat-download-api （AGPL 3.0，Docker镜像 `tmwgsicp/wechat-download-api`）

### 前提
- 需要一个微信公众号（订阅号即可），部署后访问 `http://localhost:5000/login.html` 用管理员微信扫码登录。
- 凭证约4天过期，服务自带Webhook过期提醒；每6小时自检登录态。
- 低频自用可不配代理池（内置限频：全局10次/分、单IP 5次/分、文章间隔3秒）；高频/多号拉取建议按README配SOCKS5代理池。

### 部署
- Windows：`start.bat` 一键脚本，或 `docker run -d -p 5000:5000 -v $(pwd)/data:/app/data tmwgsicp/wechat-download-api`。
- 数据存 SQLite（data/rss.db），零配置。

### 常用API（HTTP调用无需Token；仅MCP接入需Bearer Token）
| 接口 | 说明 |
|------|------|
| `GET /api/admin/status` | 检测服务在线/登录态（skill用它判断降级路径） |
| `GET /api/public/searchbiz?query=公众号名` | 搜索公众号，拿 FakeID |
| `GET /api/public/articles?fakeid=&begin=&count=` | 拉取某公众号文章列表（分页） |
| `POST /api/article`（参数 `url`） | 解析单篇正文（标题/作者/正文/图片） |
| `GET /api/rss/{fakeid}?limit=20` | 该公众号RSS源（可接阅读器） |
| `GET /api/export/account/{fakeid}.xlsx` | 整号导出（存档用） |

### 与skill的集成逻辑
1. 先探测 `/api/admin/status`：在线且已登录 → 对163家竞品逐个用 FakeID 拉文章列表（首次需 searchbiz 建立"企业名→FakeID"映射，映射结果建议存到数据层目录，避免重复搜索）。
2. 服务不在线/未登录/过期 → 降级到搜索聚合+UA伪装法。
3. 登录过期时提醒用户重新扫码（localhost 即可完成）。

## 第三节 国外企业（68家）内容获取

无公众号，按对照表中已配好的渠道：
- **官网博客**：多数自带RSS，优先订阅（如 Palo Alto Unit42、CrowdStrike、Zscaler、Fortinet Blogs）。
- **X(Twitter)**：建私有List一次性收编全部账号，每日刷时间线。
- **Google Alerts**：按企业名设关键词提醒，结果进邮箱。
- **行业媒体**：The Hacker News、BleepingComputer、SecurityWeek。

## 第四节 合规边界（全程适用）

- 抓取内容仅用于**内部存档/竞品分析参考**，不得搬运发布、不得对外输出原文。
- 只抓公开页面，不逆向API、不模拟登录第三方账号。
- 报告中引用时写明来源公众号/媒体与日期。
