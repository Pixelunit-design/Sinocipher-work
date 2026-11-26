# Sinocipher Work Skills

中安云科工作技能库，收录安全资讯编写、竞品内容监测等可复用的 AI 工作流程，并持续扩充。

## 技能目录

| Skill | 用途 | 版本 | 依赖 |
|---|---|---|---|
| [sinocipher-news-weekly](skills/sinocipher-news-weekly/SKILL.md) | 核验并编写安全资讯周览、速览及续期改稿，聚焦数据安全、密码技术（包括零信任）和 CA | 1.0.0 | 可检索、读取公开网页并交付文件的 AI 助手 |
| [competitor-wechat-monitor](skills/competitor-wechat-monitor/SKILL.md) | 按内置企业名单和内容源整理网安企业公众号及海外内容动态，生成日报、周报或月报 | 1.0.0 | Python 3.8+、openpyxl；第三方本地服务按需使用 |

## 下载与安装

在 [Releases](https://github.com/Pixelunit-design/Sinocipher-work/releases) 选择技能对应的版本，下载名称为 `<skill-name>-v<版本>.zip` 的附件。

每个附件只包含一个 skill 的完整目录。GitHub 自动生成的 `Source code (zip)` 包含整个仓库，使用时需从 `skills/` 内选取需要的目录。

安装后的层级应为：

```text
<你的平台技能目录>/
└── sinocipher-news-weekly/
    ├── SKILL.md
    └── references/
```

不同产品的安装入口与技能目录不同，请按目标产品的实际支持方式安装；本仓库不承诺所有 AI 产品即装即用。详见 [安装说明](docs/installation.md)。

## 使用示例

安全资讯：
> 使用 sinocipher-news-weekly，编写 2026 年 11 月 16 日至 22 日的安全资讯周览，按来源清单核验，并说明参考资讯的采用去向。

竞品监测：
> 使用 competitor-wechat-monitor，依据内置名单整理指定日期区间的网安企业动态，注明来源和日期，生成 HTML 周报；不能覆盖的渠道请说明。

安装 skill 不会自动创建定时任务。运行时仍需可用的检索、网页读取和文件交付能力。

## 维护与版本

源码统一放在 `skills/<skill-name>/`，目录名不带版本号。各 skill 独立版本管理：

- Tag：`sinocipher-news-weekly-v1.0.0`、`competitor-wechat-monitor-v1.0.0`。
- ZIP：`<skill-name>-v<版本>.zip`。
- 版本记录：对应 `SKILL.md` 内的 `metadata.version`。

新增技能及更新流程见 [维护约定](CONTRIBUTING.md)；历史变更见 [CHANGELOG](CHANGELOG.md)。

## 内容与依赖说明

竞品技能内含两份 Excel 企业名单与内容源表，属于随技能一起分发的数据。名单中的渠道、确认状态和数量反映数据版本，不代表运行时已重新核验。

微信公开页面的可读性受平台策略影响；第三方服务是可选能力，接口与部署方式需以其当前文档为准。本次发布整理完成了离线结构与数据加载检查，未验证线上抓取与第三方服务部署。

仓库尚未声明统一开源许可证；如需对外授权复用，维护者应先明确许可范围及随附数据、模板的适用条款。
