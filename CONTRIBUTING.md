# 维护约定

## 新增 skill

1. 在 `skills/` 下创建小写字母、数字和连字符组成的目录，名称不带版本。
2. 添加 `SKILL.md`，YAML 至少含 `name`、`description`，且 `name` 与目录名相同。
3. 将版本放入 `metadata.version` 字符串；脚本、参考资料、模板及必要数据分别放入 `scripts/`、`references/`、`assets/`。
4. 更新根 README 技能目录和 CHANGELOG。
5. 检查相对引用、依赖和数据加载，再创建独立 tag 与 Release。

```yaml
---
name: example-skill
description: 说明这个技能做什么，以及何时使用。
metadata:
  version: "1.0.0"
---
```

## 更新 skill

以 `main` 保存当前稳定内容；常规修改新建分支，如 `update/competitor-wechat-monitor-1.0.1`，提交后通过 Pull Request 合并。

- 修正说明或缺陷：递增补丁号，如 1.0.0 → 1.0.1。
- 新增兼容能力或新增名单覆盖：递增次版本，如 1.0.0 → 1.1.0。
- 改变输入、数据格式或不兼容行为：递增主版本，如 1.0.0 → 2.0.0。

数据更新也属于发布变更，应记录名单的增删范围和实际数量。只修改一个 skill 时，只升级它的版本。

合并后同步检查 `metadata.version`、README、CHANGELOG、tag、附件名。发布包从目标 tag 对应的源码生成。已发布的版本不覆盖，修复时递增版本重新发布。

## 发布约定

每个 skill 单独创建 Release：

| 项目 | 示例 |
|---|---|
| Tag | `competitor-wechat-monitor-v1.0.1` |
| Title | `competitor-wechat-monitor v1.0.1 · 说明修订` |
| 附件 | `competitor-wechat-monitor-v1.0.1.zip` |

tag 指向整个仓库的提交；tag 名说明此次发布哪个 skill。首次两个 skill 可以从同一提交创建两个 tag。

附件解压后直接出现 `<skill-name>/SKILL.md`。不把版本 ZIP、运行报告、Cookie、凭证或抓取缓存放入源码目录。

本仓库采用独立版本，首页应按技能列版本，不用一个统一 `v1.0.0` 代表全部技能。下载链接指向具体 tag，避免使用只代表全仓库一个版本的 `releases/latest` 充当每个技能的最新版。
