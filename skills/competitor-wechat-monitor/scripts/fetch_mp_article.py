#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UA伪装法抓取微信公众号文章正文。
尝试使用含 MicroMessenger 的 User-Agent 获取公开文章HTML；是否可用取决于页面与访问策略，不保证成功。
用法:
  python fetch_mp_article.py <文章URL> [更多URL...]
  python fetch_mp_article.py --file urls.txt --out articles.json
注意: 每次请求间隔1-2秒随机延迟（内置），严禁高频连续请求。
"""
import argparse
import json
import random
import re
import time
import urllib.request

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
      "MicroMessenger/8.0.34(0x16082222) NetType/WIFI Language/zh_CN")


def strip_tags(html):
    t = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", t).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    title = (re.search(r'property="og:title" content="(.*?)"', html)
             or re.search(r'<h1[^>]*id="activity-name"[^>]*>(.*?)</h1>', html, re.S))
    author = re.search(r'property="og:article:author" content="(.*?)"', html)
    account = re.search(r'id="js_name"[^>]*>(.*?)</a>', html, re.S) or \
              re.search(r'var nickname = htmlDecode\("(.*?)"\)', html)
    m = re.search(r"var createTime = '(.*?)'", html) or \
        re.search(r"publish_time = '(.*?)'", html) or \
        re.search(r'em id="publish_time[^>]*>(.*?)</em>', html, re.S)
    body = re.search(r'id="js_content"(.*?)<(script|/div>\s*<script)', html, re.S)
    blocked = ("验证" in html and "环境异常" in html) or "slider_captcha" in html.lower()
    return {
        "url": url,
        "title": strip_tags(title.group(1)) if title else "",
        "account": strip_tags(account.group(1)) if account else (author.group(1) if author else ""),
        "publish_time": strip_tags(m.group(1)) if m else "",
        "content": strip_tags(body.group(1)) if body else "",
        "blocked": blocked,
        "ok": bool(body) and not blocked,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*", help="文章URL（多个以空格分隔）")
    ap.add_argument("--file", help="从文本文件读取URL（每行一个）")
    ap.add_argument("--out", help="结果输出JSON路径（默认仅打印摘要）")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            urls += [ln.strip() for ln in f if ln.strip().startswith("http")]

    results = []
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(random.uniform(1.5, 2.5))  # 防限流红线，勿删
        try:
            r = fetch(url)
        except Exception as e:
            r = {"url": url, "ok": False, "error": str(e)}
        results.append(r)
        flag = "OK" if r.get("ok") else "FAIL"
        print(f"[{flag}] {r.get('title', '')[:40]} | {r.get('account', '')} | {r.get('publish_time', '')}")
        if r.get("error"):
            print(f"      错误: {r['error']}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
        print(f"已保存 {len(results)} 篇到 {args.out}")


if __name__ == "__main__":
    main()
