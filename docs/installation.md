# 安装说明

## 安装完整目录

从 Releases 下载所需 skill 的独立 ZIP，解压后把完整的 skill 目录放入目标产品支持的技能位置，或使用该产品提供的导入入口。只复制 `SKILL.md` 会丢失参考资料、模板或数据。

原竞品包约定 WorkBuddy 路径为 `~/.workbuddy/skills/`；请核对所用版本的实际目录。本次未进行 WorkBuddy 安装实测。其他宿主的目录与刷新方式以其文档为准。

正确层级：`<技能目录>/competitor-wechat-monitor/SKILL.md`。

错误层级：`<技能目录>/competitor-wechat-monitor/competitor-wechat-monitor/SKILL.md`。

## 竞品脚本依赖与检查

在已安装 Python 的终端运行：

```powershell
python -m pip install openpyxl
python -X utf8 skills/competitor-wechat-monitor/scripts/load_competitors.py --out competitors.json
```

上述第二条命令从仓库根目录执行；单独安装时按实际路径调整。

脚本从 skill 内的 `assets/data/` 读取两份 Excel，支持用 `--list` 和 `--sources` 指定替代文件。它只验证能否加载数据，不验证公众号真实性或实时可访问性。

批量文章参数为 `--file`：

```powershell
python -X utf8 skills/competitor-wechat-monitor/scripts/fetch_mp_article.py --file urls.txt --out articles.json
```

第三方 wechat-download-api 为可选服务。本次未部署或验证该服务；不能据此承诺完整覆盖所有公众号。未部署时可使用技能描述的检索与公开网页路径。

## 升级

升级前备份自行修改的名单。新版 ZIP 可能覆盖 `assets/data/`，应比较并合并自己的改动后再运行加载检查。
