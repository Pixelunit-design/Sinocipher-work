#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加载竞品名单+内容源对照表，合并输出统一JSON。
数据来源: skill内置 assets/data/ 目录（随skill分发，修改名单直接改这里的xlsx）。
特殊需求可用 --list/--sources 显式指定其他文件。
用法: python load_competitors.py --out competitors.json
"""
import argparse
import json
import sys
from pathlib import Path

import openpyxl

LIST_NAME = "2026重点企业截止8月初更新版.xlsx"
SOURCES_NAME = "2026重点企业微信公众号与内容源汇总_163家_v2.xlsx"

# 数据只读skill内置目录（不依赖任何本地存储路径，兼容所有人电脑习惯）
DATA_DIR = Path(__file__).resolve().parent.parent / "assets" / "data"


def resolve(name, override=None):
    if override:
        p = Path(override)
        if not p.exists():
            sys.exit(f"错误: 指定文件不存在: {p}")
        return p
    p = DATA_DIR / name
    if p.exists():
        print(f"[数据源] {name} <- {p}")
        return p
    sys.exit(f"错误: skill数据目录中找不到 {name}（应为 {DATA_DIR}），请核对文件名或用 --list/--sources 指定")


def load_list(path):
    """读竞品名单: 国家|企业类别|企业|企业全称|主营定位"""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["2026重点企业汇总"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    header = [str(c).strip() if c else "" for c in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    items = []
    for r in rows[1:]:
        if r[idx["企业"]] is None:
            continue
        items.append({
            "country": str(r[idx["国家"]]).strip(),
            "cat": str(r[idx["企业类别"]]).strip(),
            "name": str(r[idx["企业"]]).strip(),
            "full": r[idx.get("企业全称", 3)],
            "position": r[idx["主营定位"]] if "主营定位" in idx and idx["主营定位"] < len(r) else "",
        })
    return items


def load_sources(path):
    """读对照表: 公众号名称|ID|官网博客|X|获取渠道|状态，键为企业名"""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["163家企业内容源汇总"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    header = [str(c).strip() if c else "" for c in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    name_col = idx.get("企业", 2)
    mapping = {}
    for r in rows[1:]:
        if r[name_col] is None:
            continue
        mapping[str(r[name_col]).strip()] = {
            "wx_name": r[idx["微信公众号名称"]] if "微信公众号名称" in idx else "",
            "wx_id": r[idx["微信号(ID)"]] if "微信号(ID)" in idx else "",
            "blog": r[idx["官网/博客"]] if "官网/博客" in idx else "",
            "x_account": r[idx["X(Twitter)"]] if "X(Twitter)" in idx else "",
            "channel": r[idx["内容获取渠道"]] if "内容获取渠道" in idx else "",
            "status": r[idx["状态"]] if "状态" in idx else "",
        }
    return mapping


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default=None, help="竞品名单xlsx路径（不指定则自动寻路）")
    ap.add_argument("--sources", default=None, help="内容源对照表xlsx路径（不指定则自动寻路）")
    ap.add_argument("--out", default="competitors.json", help="输出JSON路径")
    args = ap.parse_args()

    list_path = resolve(LIST_NAME, args.list)
    sources_path = resolve(SOURCES_NAME, args.sources)

    companies = load_list(list_path)
    sources = load_sources(sources_path)
    merged = []
    for c in companies:
        s = sources.get(c["name"], {})
        c.update({k: (s.get(k) or "") for k in
                  ("wx_name", "wx_id", "blog", "x_account", "channel", "status")})
        merged.append(c)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)

    domestic = [c for c in merged if c["country"] == "中国"]
    confirmed = [c for c in domestic if c["status"] == "已确认"]
    print(f"竞品总数: {len(merged)} (国内{len(domestic)} / 国外{len(merged)-len(domestic)})")
    print(f"国内已确认公众号: {len(confirmed)} / {len(domestic)}")
    print(f"输出: {args.out}")
    missing = [c["name"] for c in domestic if not c["wx_name"]]
    if missing:
        print(f"未确认公众号({len(missing)}家): {'、'.join(missing)}", file=sys.stderr)


if __name__ == "__main__":
    main()
