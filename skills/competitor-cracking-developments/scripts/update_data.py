#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
competitor-cracking-developments 数据更新脚本 v1.2
数据源: scctc.org.cn 商用密码认证证书官方接口
用法:
    python update_data.py              # 刷新全部10家竞品（不含中安云科）
    python update_data.py 三未信安     # 只刷新指定竞品
    python update_data.py 中安云科     # 显式刷新中安云科（会覆盖用户确认口径，慎用）
退出码:
    0 = 全部成功且校验通过
    1 = 部分企业刷新失败/被骤降保护拒绝（已成功者已落盘）
    2 = 刷新后数据校验失败（validate_data.py 报错）
安全机制（v1.2）:
    1. 中安云科默认排除——其资质以用户确认口径为准；旧数量从 zayk_certs.json 读取（骤降保护有效）
    2. 江南科友旧数量从 jnkf_gm_detail.json 读取；刷新成功同时写入 competitor_gm_detail.json
       （build_excel 优先读该文件）与 jnkf_gm_detail.json（保持双文件一致）
    3. 接口响应结构校验：缺少 data/records 字段视为失败，不落盘
    4. 数量骤降校验：新数量 < 旧数量70% 时拒绝写入（旧数量按各企业正确数据源统计）
    5. 未知状态码映射为"待确认"并显式告警，不静默
    6. 写入前自动备份旧文件到 data/backup/<日期>/，原子写入（临时文件+替换）
    7. 快照日期按企业记录（refreshed_at / snapshot_date）；仅全量刷新成功时才更新
       data/README.md 顶部全局快照日期，部分刷新不改全局日期
    8. 刷新完成后自动运行 validate_data.py 完整校验
范围限制（如实声明）: 本脚本只刷新商用密码证书。IPv6/网专/FIPS/EPRI/ISO 等其他
    数据源无公开接口或需人工查询，不在自动刷新范围，详见 data/README.md。
"""
import json, ssl, sys, time, datetime, shutil, os, subprocess
import urllib.request, urllib.parse
from pathlib import Path

API = "https://www.scctc.org.cn/ucenter/api/certificate/pageList"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ZAYK_PROTECT = True  # 中安云科保护开关

# 简称 -> 官网登记全称（2026-09 核对；企业改名时先改这里）
COMPANIES = {
    "三未信安": "三未信安科技股份有限公司",
    "渔翁信息": "渔翁信息技术股份有限公司",
    "江南天安": "北京江南天安科技有限公司",
    "数盾科技": "数盾信息科技股份有限公司",
    "海泰方圆": "北京海泰方圆科技股份有限公司",
    "北京CA": "北京数字认证股份有限公司",
    "吉大正元": "长春吉大正元信息技术股份有限公司",
    "信安世纪": "北京信安世纪科技股份有限公司",
    "格尔软件": "格尔软件股份有限公司",
    "江南科友": "广州江南科友科技股份有限公司",
    "中安云科": "中安云科科技发展（山东）有限公司",
}
STATUS = {"0": "有效", "1": "注销", "4": "过期", "3": "待确认"}
KNOWN_STATUS = set(STATUS.values())

def new_ctx():
    ctx = ssl.create_default_context()
    ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT  # scctc 旧版TLS
    return ctx

def fetch(full_name):
    """拉取某企业全部证书；接口异常抛错而不是返回空列表"""
    recs, page = [], 1
    while True:
        params = urllib.parse.urlencode({
            "certificateCategory": "1", "assignorName": full_name,
            "current": page, "size": 50})
        req = urllib.request.Request(f"{API}?{params}",
            headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, context=new_ctx(), timeout=30) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"接口请求失败: {e}") from e
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict) or "records" not in data:
            raise RuntimeError(f"接口响应结构异常（缺少 data.records），full={full_name} page={page}")
        rows = data["records"]
        if not rows:
            if page == 1:
                return []  # 第1页为空=该企业确无证书
            break
        for x in rows:
            raw = str(x.get("certificateStatus"))
            st = STATUS.get(raw)
            if st is None:
                print(f"  [告警] 未知状态码 {raw}（证书 {x.get('certificateCode')}），已标注'待确认'")
                st = "待确认"
            recs.append({"no": x.get("certificateCode", ""),
                         "name": x.get("productName", ""),
                         "model": x.get("productModel", ""),
                         "ver": x.get("productVersion", ""),
                         "type": x.get("productType", ""),
                         "level": x.get("productSecurityLevel", ""),
                         "issue": x.get("issueDate", ""),
                         "until": x.get("effectiveDate", ""),
                         "status": st})
        if len(rows) < 50:
            break
        page += 1
        time.sleep(0.5)
    return recs

def atomic_write(path: Path, text: str):
    """临时文件+替换的原子写入"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def backup(path: Path, today: str):
    if path.exists():
        bdir = DATA / "backup" / today
        bdir.mkdir(parents=True, exist_ok=True)
        dst = bdir / path.name
        if not dst.exists():  # 同日多次运行只留首份备份
            shutil.copy2(path, dst)

def old_count_for(short, detail, zayk, jnkf):
    """按企业读取正确的旧数据数量（骤降保护基准）：
    中安云科→zayk_certs.json；江南科友→jnkf_gm_detail.json 或 detail；
    其余→competitor_gm_detail.json"""
    if short == "中安云科":
        return len(zayk.get("gm", []))
    if short == "江南科友":
        return len(detail.get(short, [])) or len(jnkf)
    return len(detail.get(short, []))

def sanity_ok(new_n, old_n):
    """数量骤降保护：新数量低于旧的70%时视为异常（旧数据为空时放行）"""
    return (not old_n) or new_n >= old_n * 0.7

# 常用别名 → 标准简称（防止传"数字认证"等日常简称时静默退出）
ALIASES = {
    "数字认证": "北京CA",
    "BJCA": "北京CA",
    "三未": "三未信安",
    "科友": "江南科友",
    "江南科友科技": "江南科友",
}

def update_readme_date(today: str):
    """全量刷新成功后更新 data/README.md 的"最近全量刷新日"行（按数据源分列的新格式）"""
    fp = DATA / "README.md"
    if not fp.exists():
        print("[提示] data/README.md 不存在，跳过日期更新")
        return
    text = fp.read_text(encoding="utf-8")
    for prefix in ("**最近全量刷新日", "**快照日期：", "**最新快照：", "**部分刷新快照："):
        if prefix in text:
            head, rest = text.split(prefix, 1)
            _, tail = rest.split("**", 1)
            text = head + prefix + "：" + today + "**" + tail
            atomic_write(fp, text)
            return
    # 新格式README无该行：追加到"数据日期说明"块内
    marker = "- **最近完整校验**"
    if marker in text:
        text = text.replace(marker, f"- **最近全量刷新日**：{today}（由 update_data.py 自动写入）\n" + marker, 1)
    else:
        text += f"\n- **最近全量刷新日**：{today}（由 update_data.py 自动写入）\n"
    atomic_write(fp, text)
    print("[提示] data/README.md 已追加'最近全量刷新日'行")

def main():
    only = set(sys.argv[1:])
    # 别名解析
    resolved = {ALIASES.get(a, a) for a in only}
    unknown = resolved - set(COMPANIES)
    if unknown:
        print(f"[错误] 无法识别的企业简称: {', '.join(sorted(unknown))}。可用简称: {', '.join(COMPANIES)}（别名: 数字认证→北京CA 等）")
        sys.exit(3)
    today = datetime.date.today().isoformat()
    explicit_zayk = "中安云科" in resolved
    targets = {k: v for k, v in COMPANIES.items() if not resolved or k in resolved}
    if ZAYK_PROTECT and not explicit_zayk:
        targets.pop("中安云科", None)  # 默认排除中安云科（用户确认口径保护）
    if not targets:
        print("[提示] 无可刷新目标（若仅指定'中安云科'，其受保护开关默认拒绝；如需刷新请修改 ZAYK_PROTECT）")
        sys.exit(3)

    fp = DATA / "competitor_gm.json"
    gm_summary = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    detail_fp = DATA / "competitor_gm_detail.json"
    detail = json.loads(detail_fp.read_text(encoding="utf-8")) if detail_fp.exists() else {}
    jnkf_fp = DATA / "jnkf_gm_detail.json"
    jnkf = json.loads(jnkf_fp.read_text(encoding="utf-8")) if jnkf_fp.exists() else []
    zfp = DATA / "zayk_certs.json"
    zayk = json.loads(zfp.read_text(encoding="utf-8")) if zfp.exists() else {}

    changed, failed = [], []
    for short, full in targets.items():
        try:
            recs = fetch(full)
        except RuntimeError as e:
            print(f"[跳过] {short}: {e}")
            failed.append(short)
            continue
        status = {}
        for r in recs:
            status[r["status"]] = status.get(r["status"], 0) + 1
        old_n = old_count_for(short, detail, zayk, jnkf)
        if not sanity_ok(len(recs), old_n):
            print(f"[拒绝写入] {short}: 新{len(recs)}条 < 旧{old_n}条的70%，疑似接口异常，旧数据已保留")
            failed.append(short)
            continue
        print(f"[OK] {short}: {len(recs)}条 {status}" + (f"（旧{old_n}条）" if old_n else ""))
        if not changed:
            for p in {detail_fp, fp, zfp, jnkf_fp}:
                backup(p, today)  # 每次运行只备一次旧数据
        if short == "中安云科":
            zayk.setdefault("gm", [])
            zayk["gm"] = recs
            zayk["_gm_refreshed_at"] = today
        else:
            gm_summary[full] = {"total": len(recs), "status": status,
                                "assignors": {full: len(recs)},
                                "snapshot_date": today, "refreshed_at": today}
            detail[short] = recs
            if short == "江南科友":
                jnkf = recs  # 双文件保持一致
        changed.append(short)
        time.sleep(0.5)

    # ---- 落盘（仅当有成功刷新；全量成功才更新全局日期）----
    full_run = (not only) and len(changed) == len(targets) and len(targets) > 0
    if changed:
        if zayk.get("_gm_refreshed_at") == today:
            atomic_write(zfp, json.dumps(zayk, ensure_ascii=False, indent=1))
        atomic_write(fp, json.dumps(gm_summary, ensure_ascii=False, indent=1))
        atomic_write(detail_fp, json.dumps(detail, ensure_ascii=False, indent=1))
        atomic_write(jnkf_fp, json.dumps(jnkf, ensure_ascii=False, indent=1))
        if full_run:
            update_readme_date(today)
        else:
            print("[提示] 部分刷新：全局快照日期未改动（各企业以 snapshot_date/refreshed_at 记录）。")
        print(f"\n已刷新: {', '.join(changed)}"
              + (f"；失败/跳过: {', '.join(failed)}" if failed else ""))
        print(f"备份目录: data/backup/{today}")
        print("注意: 本脚本只更新商密证书；IPv6/网专/FIPS 等未自动更新。")
    else:
        print("无任何企业刷新成功，数据未变更。" + (f" 失败: {', '.join(failed)}" if failed else ""))

    # ---- 刷新后自动校验 ----
    print("\n--- 自动运行数据校验 ---")
    vr = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_data.py")])
    if vr.returncode != 0:
        print("[校验失败] 刷新后的数据未通过一致性校验，请检查上方 [ERROR] 项。")
        sys.exit(2)
    if failed:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
