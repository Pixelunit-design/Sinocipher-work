#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
competitor-cracking-developments 数据一致性校验脚本 v3
用法: python validate_data.py    （全部通过退出码0；有错误退出码1）
检查项:
  1. 6个数据JSON可解析
  2. events.jsonl 逐行合法JSON且event_id唯一、report_id可追溯
  3. 状态码在已知集合内（有效/注销/过期/待确认）——明细与汇总双侧检查
  4. competitor_gm.json 汇总自检：status计数之和==total
  5. competitor_gm.json 有效数 与 明细文件逐条统计 交叉核对（允许快照时间差，超出阈值警告）
  6. 企业覆盖：明细9家+科友独立文件+汇总8家以上的覆盖关系核对（渔翁/科友须在汇总中有计数或有来源标注）
  7. 证书编号重复检查（同企业内编号不得重复）
  8. 明细记录必填字段（no/name/status）
  9. refreshed_at 时间戳完整性（缺失警告，不阻断）
 10. config/companies.json 企业数=163 且与 summary_all 全称一致
 11. 中安云科有效数与用户确认口径34核对（不一致为警告，快照漂移需人工确认）
"""
import json, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
errors, warns = [], []

def check(cond, msg):
    if not cond:
        errors.append(msg)

def warn(cond, msg):
    if not cond:
        warns.append(msg)

# 1. JSON可解析
j = {}
for name in ["zayk_certs.json", "competitor_gm.json", "competitor_gm_detail.json",
             "jnkf_gm_detail.json", "competitor_other_detail.json", "summary_all.json"]:
    try:
        j[name] = json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{name} 解析失败: {e}")

if len(j) == 6:
    z = j["zayk_certs.json"]
    detail = j["competitor_gm_detail.json"]
    summary = j["competitor_gm.json"]
    jnkf = j["jnkf_gm_detail.json"]

    # 3. 状态码合法性（明细侧）
    KNOWN = {"有效", "注销", "过期", "待确认"}
    bad_status = []
    def scan(recs, where):
        for r in recs:
            if r.get("status") not in KNOWN:
                bad_status.append((where, r.get("no"), r.get("status")))
            for f in ("no", "name", "status"):
                if f not in r:
                    errors.append(f"{where} 记录缺必填字段 {f}: {r.get('no', '?')}")
    scan(z.get("gm", []), "zayk gm")
    for short, recs in detail.items():
        scan(recs, f"gm_detail/{short}")
    scan(jnkf, "jnkf")
    # 3b. 汇总侧状态键合法性
    for full, rec in summary.items():
        for st in rec.get("status", {}):
            if st not in KNOWN and st not in ("snapshot_date",):
                bad_status.append((f"competitor_gm/{full}", "-", st))
    if bad_status:
        errors.append(f"未知状态码: {bad_status[:5]}（共{len(bad_status)}条）")

    # 4. 汇总自检：status计数之和 == total
    for full, rec in summary.items():
        s = sum(v for k, v in rec.get("status", {}).items() if k != "snapshot_date")
        if s != rec.get("total"):
            errors.append(f"competitor_gm[{full}]: status计数和{s} != total{rec.get('total')}")

    # 5. 有效数交叉核对（汇总 vs 明细逐条统计）
    short2full = {"三未信安": "三未信安科技股份有限公司", "渔翁信息": "渔翁信息技术股份有限公司",
                  "江南天安": "北京江南天安科技有限公司", "数盾科技": "数盾信息科技股份有限公司",
                  "海泰方圆": "北京海泰方圆科技股份有限公司", "北京CA": "北京数字认证股份有限公司",
                  "吉大正元": "长春吉大正元信息技术股份有限公司", "信安世纪": "北京信安世纪科技股份有限公司",
                  "格尔软件": "格尔软件股份有限公司", "江南科友": "广州江南科友科技股份有限公司"}
    for short, full in short2full.items():
        if short in detail and full in summary:
            dn_valid = sum(1 for r in detail[short] if r.get("status") == "有效")
            sn_valid = summary[full].get("status", {}).get("有效", 0)
            if dn_valid != sn_valid:
                base = max(sn_valid, 1)
                diff = abs(dn_valid - sn_valid) / base
                if diff <= 0.05:
                    warns.append(f"{short}: 有效数 明细{dn_valid} vs 汇总{sn_valid} 差异≤5%（快照时间差，请在data/README标注）")
                else:
                    errors.append(f"{short}: 有效数 明细{dn_valid} vs 汇总{sn_valid} 差异>5%，必须核对")
            # 总量
            dn, sn = len(detail[short]), summary[full].get("total", 0)
            if abs(dn - sn) > max(5, sn * 0.05):
                warns.append(f"{short}: 明细{dn}条 vs 计数{sn}条 差异>5%（可能为不同时间快照）")

    # 6. 企业覆盖关系
    n_detail = len(detail)
    check(n_detail >= 9, f"competitor_gm_detail.json 企业数={n_detail} 应≥9")
    check(len(jnkf) > 0, "jnkf_gm_detail.json 为空")
    # 汇总应覆盖明细中的企业（科友可在明细或独立文件中）
    for short, full in short2full.items():
        has_detail = short in detail or (short == "江南科友" and len(jnkf) > 0)
        if has_detail and full not in summary:
            warns.append(f"{short} 有明细但汇总 competitor_gm.json 无计数条目（有效榜需汇总或明细二选一）")
    # 9. refreshed_at 时间戳完整性
    for full, rec in summary.items():
        if "snapshot_date" not in rec:
            warns.append(f"competitor_gm[{full}] 缺 snapshot_date 字段")

    # 7. 证书编号重复检查（同企业内）
    dup = []
    def dupcheck(recs, where):
        nos = [r.get("no") for r in recs if r.get("no")]
        for no, c in Counter(nos).items():
            if c > 1:
                dup.append(f"{where}:{no}×{c}")
    for short, recs in detail.items():
        dupcheck(recs, f"gm_detail/{short}")
    dupcheck(z.get("gm", []), "zayk")
    dupcheck(jnkf, "jnkf")
    if dup:
        warns.append(f"证书编号重复: {dup[:5]}（共{len(dup)}组，跨产品线同号可能是正常现象，请人工确认）")

    # 5b. config/companies.json 一致性
    cfg = json.loads((ROOT / "config" / "companies.json").read_text(encoding="utf-8"))
    fulls_cfg = {c["full"] for c in cfg["companies"]}
    fulls_sum = {x["full"] for x in j["summary_all.json"]}
    check(len(fulls_cfg) == 163, f"companies.json 企业数={len(fulls_cfg)} 应为163")
    check(fulls_cfg == fulls_sum, "companies.json 与 summary_all 全称集合不一致")

    # 2+6b. events.jsonl
    eids = set()
    report_ids = {r["report_id"] for r in json.loads((ROOT / "state" / "report-index.json").read_text(encoding="utf-8"))["reports"]}
    n_ev = 0
    for i, line in enumerate((DATA / "events.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            n_ev += 1
            check(ev["event_id"] not in eids, f"events.jsonl 第{i}行 event_id 重复: {ev['event_id']}")
            eids.add(ev["event_id"])
            warn(ev.get("report_id") in report_ids, f"events.jsonl 第{i}行 report_id={ev.get('report_id')} 不在 report-index")
            for f in ("event_id", "company", "event_type", "event_date", "title", "report_id", "verification_status"):
                warn(f in ev, f"events.jsonl 第{i}行缺字段 {f}")
        except Exception as e:
            errors.append(f"events.jsonl 第{i}行 非法JSON: {e}")
    print(f"events.jsonl: {n_ev} 条事件")

    # 7b. state 完整性
    st = json.loads((ROOT / "state" / "research-state.json").read_text(encoding="utf-8"))
    for f in ("last_report_id", "covered_until", "dedup_rule", "report_index_file"):
        warn(f in st, f"research-state.json 缺字段 {f}")

    # 11. 中安云科口径
    zayk_valid = sum(1 for r in z.get("gm", []) if r["status"] == "有效")
    if zayk_valid != 34:
        warns.append(f"中安云科商密有效={zayk_valid}，与用户确认口径34不一致（接口快照漂移）——Excel/报告引用前须人工确认")

print(f"明细企业: {len(detail)}家(+) 科友{len(jnkf)}条  汇总企业: {len(summary)}家")
print(f"中安云科商密有效: {sum(1 for r in z.get('gm', []) if r['status'] == '有效')}（用户口径34）")
print(f"\n结果: {len(errors)} 错误, {len(warns)} 警告")
for e in errors: print("[ERROR]", e)
for w in warns: print("[WARN]", w)
sys.exit(1 if errors else 0)
