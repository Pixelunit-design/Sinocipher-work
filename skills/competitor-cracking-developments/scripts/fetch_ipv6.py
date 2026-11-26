#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPv6 Ready Logo 证书抓取脚本（流程C：IPv6单项对标的数据工具）
接口实测（2026-11-26）：https://www.ipv6testingcenter.com/index/index/cert_list.html
直接返回 JSON：{"total": 907, "rows": [{logo_id, vendor_name, product_name, product_version, applied_ts, test_spec, ...}, ...]}
分页参数 page（每页10条），厂商过滤参数 vendor_name（模糊匹配，含中英文混排"公司全称 / English Name"）。
用法：
    python scripts/fetch_ipv6.py                 # 抓取已知竞品名单
    python scripts/fetch_ipv6.py 三未信安 渔翁    # 只抓指定关键词
输出：data/ipv6_ready.json（快照式覆盖，meta 记录抓取日期）
依赖：Python 标准库。接口异常/解析为空时拒绝写入并报错退出（与 update_data.py 同一保护哲学）。
"""
import json
import ssl
import sys
import datetime
from pathlib import Path
from urllib import request, parse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "ipv6_ready.json"
API = "https://www.ipv6testingcenter.com/index/index/cert_list.html"
# 已知竞品关键词（vendor_name为模糊匹配；官方登记多为全称，故用短关键词）
KNOWN = ["三未信安", "渔翁", "江南天安", "数盾", "海泰方圆", "数字认证",
         "吉大正元", "信安世纪", "格尔", "江南科友"]

CTX = ssl.create_default_context()

def fetch_page(page=1, keyword=""):
    """请求一页证书；返回 (rows, total)。接口异常抛 RuntimeError。"""
    body = parse.urlencode({"page": page, "vendor_name": keyword}).encode("utf-8")
    req = request.Request(API, data=body, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with request.urlopen(req, context=CTX, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        raise RuntimeError(f"IPv6接口请求失败: {e}")
    if not isinstance(payload, dict) or "rows" not in payload:
        raise RuntimeError("IPv6接口返回结构异常（可能改版）")
    return payload.get("rows", []), payload.get("total", 0)

def fetch_by_keyword(keyword):
    rows_all, page = [], 1
    while True:
        rows, total = fetch_page(page, keyword)
        if not rows:
            break
        rows_all.extend(rows)
        if page * 10 >= total or page >= 100:  # 每页10条；100页保护
            break
        page += 1
    return rows_all, total

def atomic_write(fp, text):
    tmp = Path(str(fp) + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(fp)

def main():
    keywords = [a for a in sys.argv[1:] if a] or KNOWN
    certs, failed = [], []
    for kw in keywords:
        try:
            rows, total = fetch_by_keyword(kw)
            certs.extend({"keyword": kw, **r} for r in rows)
            print(f"[OK] {kw}: {len(rows)}条（total={total}）")
        except RuntimeError as e:
            print(f"[失败] {kw}: {e}")
            failed.append(kw)
    # 保护：全部失败或零结果时拒绝写入，防止清空已有快照
    if not certs:
        print("[错误] 无任何有效结果——接口可能改版或网络异常，已拒绝写入数据文件")
        sys.exit(2)
    out = {"meta": {"fetched_at": datetime.date.today().isoformat(),
                    "source": API, "keywords": keywords,
                    "failed": failed,
                    "note": "vendor_name模糊匹配抓取；快照式覆盖；接口每页10条"},
           "certs": certs}
    atomic_write(OUT, json.dumps(out, ensure_ascii=False, indent=1))
    print(f"完成：{len(certs)}条证书 → {OUT}（失败关键词: {failed or '无'}）")
    sys.exit(0)

if __name__ == "__main__":
    main()
