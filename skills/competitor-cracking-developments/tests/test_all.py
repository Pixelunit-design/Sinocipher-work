#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
competitor-cracking-developments 自动化测试脚本
用法: python tests/test_all.py        （全部通过退出码0；日志写入 tests/test-log-<日期>.txt）
设计: 先把整个技能包复制到系统临时目录（模拟冷启动：不依赖原工作区/本地磁盘历史文件），
      在临时副本上执行全部检查。区分 通过(PASS)/失败(FAIL)/跳过(SKIP)。
"""
import json, os, re, shutil, subprocess, sys, tempfile, datetime, hashlib, importlib.util
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent          # 技能包根目录
LOG_LINES = []
RESULTS = []  # (名称, 状态)

def log(msg=""):
    print(msg)
    LOG_LINES.append(msg)

def record(name, ok, note=""):
    status = "PASS" if ok else "FAIL"
    RESULTS.append((name, status))
    log(f"[{status}] {name}" + (f" — {note}" if note else ""))

def record_skip(name, note):
    RESULTS.append((name, "SKIP"))
    log(f"[SKIP] {name} — {note}")

# ---------- T0 冷启动：复制到临时目录 ----------
tmp_root = Path(tempfile.mkdtemp(prefix="ccd_test_"))
tmp_pkg = tmp_root / "competitor-cracking-developments"
shutil.copytree(PKG, tmp_pkg, ignore=shutil.ignore_patterns("backup", "__pycache__", "*.pyc"))
log(f"冷启动副本: {tmp_root}")

# ---------- T1 硬编码路径检查 ----------
def t1():
    bad = []
    for py in (tmp_pkg / "scripts").glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for pat in (r"C:\\", r"D:\\", r"F:\\", r"[A-Z]:\\\\", r"\.workbuddy", r"中安云科\\WorkBuddy"):
            if re.search(pat, text):
                bad.append(f"{py.name}:{pat}")
    record("T1 脚本无硬编码盘符/原工作区路径", not bad, "; ".join(bad) or "全部使用 Path(__file__) 相对定位")

# ---------- T2 语法检查 ----------
def t2():
    fails = []
    for py in (tmp_pkg / "scripts").glob("*.py"):
        r = subprocess.run([sys.executable, "-m", "py_compile", str(py)], capture_output=True)
        if r.returncode != 0:
            fails.append(py.name)
    record("T2 三个脚本语法检查", not fails, "; ".join(fails) or "update/validate/build_excel 均通过")

# ---------- T3 数据一致性校验（冷启动副本） ----------
def t3():
    r = subprocess.run([sys.executable, str(tmp_pkg / "scripts" / "validate_data.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    record("T3 validate_data.py 校验通过（0错误）", r.returncode == 0, (r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "")

# ---------- T4/T5/T6/T7/T8 Excel生成与口径 ----------
EXPECT_SHEETS = ["对比总览", "资质排行榜", "中安云科", "三未信安", "渔翁信息", "江南天安", "江南科友",
                 "数盾科技", "海泰方圆", "北京CA", "吉大正元", "信安世纪", "格尔软件"]

def t4():
    r = subprocess.run([sys.executable, str(tmp_pkg / "scripts" / "build_excel.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = tmp_pkg / "outputs" / "中安云科vs竞品资质对比表.xlsx"
    record("T4 Excel脚本冷启动直接运行", r.returncode == 0 and out.exists(), str(out) if out.exists() else (r.stderr or "")[-200:])
    return out

def t5_t6_t7_t8():
    out = tmp_pkg / "outputs" / "中安云科vs竞品资质对比表.xlsx"
    if not out.exists():
        record_skip("T5-T8 Excel内容检查", "T4未产出文件")
        return
    try:
        from openpyxl import load_workbook
    except ImportError:
        record_skip("T5-T8 Excel内容检查", "缺少openpyxl")
        return
    wb = load_workbook(out)
    record("T5a Excel重新打开", True, f"{len(wb.sheetnames)}个sheet")
    record("T5b 13个Sheet名称与顺序", wb.sheetnames == EXPECT_SHEETS, " → ".join(wb.sheetnames))
    try:
        wb.save(str(tmp_root / "resave_test.xlsx"))
        record("T5c Excel重新保存", True)
    except Exception as e:
        record("T5c Excel重新保存", False, str(e)[:120])

    ws = wb["对比总览"]
    zayk_valid = None
    for row in ws.iter_rows(min_col=1, max_col=6):
        vals = [c.value for c in row]
        if vals[0] == "中安云科" and isinstance(vals[2], int):
            zayk_valid = vals[2]
            break
    record("T6 对比总览中安云科有效商密=34（用户口径）", zayk_valid == 34, f"实际={zayk_valid}")

    ws = wb["资质排行榜"]
    # 定位"一、有效证书"块与"二、"块之间的数据行
    blocks, current = {}, None
    for row in ws.iter_rows(min_col=1, max_col=1):
        v = row[0].value
        if isinstance(v, str):
            if v.startswith("一、"):
                current = "valid"
                blocks[current] = []
            elif v.startswith("二、") or v.startswith("三、") or v.startswith("四、") or v.startswith("五、") or v.startswith("六、"):
                current = None if not v.startswith("六、") else "total_gm"
                if current:
                    blocks[current] = []
        elif isinstance(v, int) and current:
            blocks[current].append(row[0].row)
    valid_names = [ws.cell(row=r, column=2).value for r in blocks.get("valid", [])]
    VERIFIED = {"中安云科", "三未信安", "渔翁信息", "江南天安", "江南科友", "数盾科技",
                "海泰方圆", "北京CA", "吉大正元", "信安世纪", "格尔软件"}
    record("T7a 有效证书榜仅含已核验11家（无未核验企业混入）",
           set(valid_names) <= VERIFIED and len(valid_names) == 11,
           f"{len(valid_names)}家: {valid_names}")
    zk_rank_row = next((r for r in blocks.get("valid", []) if ws.cell(row=r, column=2).value == "中安云科"), None)
    record("T7b 有效榜中安云科=34",
           zk_rank_row is not None and ws.cell(row=zk_rank_row, column=4).value == 34,
           f"值={ws.cell(row=zk_rank_row, column=4).value if zk_rank_row else '未上榜'}")
    total_names = [ws.cell(row=r, column=2).value for r in blocks.get("total_gm", [])]
    record("T7c 总量榜独立存在（含未核验企业，规模口径）",
           len(total_names) >= 40 and "中安云科" in total_names,
           f"总量榜{len(total_names)}家")
    # T8 缺失数据不视为零：有效榜不得出现152家未核验企业
    record("T8 缺有效数据企业未按零处理（有效榜=11家而非163家）", len(valid_names) == 11)

# ---------- T9 接口异常模拟（不破坏已有数据） ----------
def t9():
    det_fp = tmp_pkg / "data" / "competitor_gm_detail.json"
    zay_fp = tmp_pkg / "data" / "zayk_certs.json"
    before_det = hashlib.md5(det_fp.read_bytes()).hexdigest()
    before_zay = hashlib.md5(zay_fp.read_bytes()).hexdigest()
    upd_path = str(tmp_pkg / "scripts" / "update_data.py")
    wrapper = tmp_root / "patch_api.py"
    wrapper.write_text(
        "import sys, importlib.util\n"
        "spec = importlib.util.spec_from_file_location('update_data', r'" + upd_path + "')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "m.API = 'http://127.0.0.1:1/no_such_api'\n"   # 必然连接失败的假接口
        "sys.argv = ['update_data.py'] + sys.argv[1:]\n"
        "try:\n    m.main()\nexcept SystemExit as e:\n    sys.exit(e.code if isinstance(e.code, int) else 0)\n",
        encoding="utf-8")
    r1 = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    after_det = hashlib.md5(det_fp.read_bytes()).hexdigest()
    after_zay = hashlib.md5(zay_fp.read_bytes()).hexdigest()
    record("T9a 接口异常返回非零退出码", r1.returncode in (1, 2), f"exit={r1.returncode}")
    record("T9b 接口异常不破坏已有数据（明细/中安云科文件未变）",
           before_det == after_det and before_zay == after_zay, "文件哈希一致")

    # 骤降保护与旧数量来源 单元检查
    spec = importlib.util.spec_from_file_location("update_data", tmp_pkg / "scripts" / "update_data.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    zayk = json.loads(zay_fp.read_text(encoding="utf-8"))
    jnkf = json.loads((tmp_pkg / "data" / "jnkf_gm_detail.json").read_text(encoding="utf-8"))
    ok1 = m.old_count_for("中安云科", {}, zayk, []) == len(zayk["gm"])
    ok2 = m.old_count_for("江南科友", {}, {}, jnkf) == len(jnkf)
    ok3 = m.sanity_ok(0, 100) is False
    ok4 = m.sanity_ok(10, 0) is True
    record("T9c 中安云科/科友旧数量来源正确+骤降保护",
           ok1 and ok2 and ok3 and ok4,
           f"zayk={ok1}, jnkf={ok2}, 空列表拒绝={ok3}, 首次放行={ok4}")

    # 中安云科默认排除（静态+动态）
    src = (tmp_pkg / "scripts" / "update_data.py").read_text(encoding="utf-8")
    record("T9d 默认刷新排除中安云科（保护开关）", "targets.pop(\"中安云科\", None)" in src and m.ZAYK_PROTECT is True)

# ---------- T10 江南科友双数据源优先级 ----------
def t10():
    det_fp = tmp_pkg / "data" / "competitor_gm_detail.json"
    det = json.loads(det_fp.read_text(encoding="utf-8"))
    det["江南科友"] = [{"no": "TEST-JNKF-001", "name": "优先级测试产品", "model": "T1", "ver": "V9",
                        "type": "t", "level": "L", "issue": "", "until": "", "status": "有效"}]
    det_fp.write_text(json.dumps(det, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(tmp_pkg / "scripts" / "build_excel.py")], capture_output=True, encoding="utf-8", errors="replace")
    found = False
    if r.returncode == 0:
        from openpyxl import load_workbook
        wb = load_workbook(tmp_pkg / "outputs" / "中安云科vs竞品资质对比表.xlsx")
        ws = wb["江南科友"]
        for row in ws.iter_rows():
            for c in row:
                if c.value == "TEST-JNKF-001":
                    found = True
    record("T10 科友刷新后Excel使用新数据（detail优先于jnkf种子）", found, "TEST-JNKF-001 标记出现在科友sheet")

# ---------- T11 历史报告与事件库追溯 ----------
def t11():
    os.chdir(tmp_pkg)
    idx = json.loads((tmp_pkg / "state" / "report-index.json").read_text(encoding="utf-8"))
    missing = []
    embedded = 0
    for r in idx["reports"]:
        f = tmp_pkg / r["file"]
        if f.exists():
            embedded += 1
        elif "未嵌入" not in json.dumps(r, ensure_ascii=False):
            missing.append(r["report_id"])
    record("T11a 已嵌入历史报告路径全部有效（按文件实际存在计数）", not missing,
           f"{embedded}/{len(idx['reports'])}期文件实际存在, 缺失: {missing or '无'}")
    report_ids = {r["report_id"] for r in idx["reports"]}
    evs = [json.loads(l) for l in (tmp_pkg / "data" / "events.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    orphan = [e["event_id"] for e in evs if e.get("report_id") not in report_ids]
    record("T11b 事件库report_id全部可追溯", not orphan, f"{len(evs)}条事件")
    # 事件库结构化来源字段
    bad_src = [e["event_id"] for e in evs if not isinstance(e.get("source"), dict) or "type" not in e["source"]]
    record("T11c 事件库来源已结构化（type/publisher/url字段）", not bad_src, f"异常: {bad_src or '无'}")
    # 证据等级合法性（evidence-policy L1-L6）
    bad_lv = [e["event_id"] for e in evs if e.get("source", {}).get("evidence_level") not in ("L1","L2","L3","L4","L5","L6")]
    record("T11d 事件库证据等级均为L1-L6合法值", not bad_lv, f"异常: {bad_lv or '无'}")
    # company_id 统一为全称（非空时不得是简称）
    shorts = {"中安云科","三未信安","渔翁信息","江南天安","江南科友","数盾科技","海泰方圆","北京CA","吉大正元","信安世纪","格尔软件"}
    bad_cid = [e["event_id"] for e in evs if e.get("company_id") in shorts]
    record("T11e company_id统一为企业全称（不得用简称）", not bad_cid, f"异常: {bad_cid or '无'}")

# ---------- T12 发布ZIP检查（优先真实发布包，回退自打包） ----------
def t12():
    import zipfile
    release = PKG.parent / "outputs" / "competitor-cracking-developments-v1.0.0.zip"
    zp = release if release.exists() else tmp_root / "zip_test.zip"
    if not release.exists():
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for p in tmp_pkg.rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts:
                    z.write(p, p.relative_to(tmp_root).as_posix())
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        bad = [n for n in names if "\\" in n]
        crc_ok = z.testzip() is None
    record("T12 发布ZIP完整性+正斜杠路径（跨平台解包）", crc_ok and not bad and len(names) > 30,
           f"{zp.name}: {len(names)}文件, CRC={crc_ok}, 反斜杠路径={len(bad)}")

# ---------- T13 依赖声明与requirements.txt合法性 ----------
def t13():
    req = (tmp_pkg / "requirements.txt").read_text(encoding="utf-8").splitlines()
    deps = [l.strip() for l in req if l.strip() and not l.strip().startswith("#")]
    bad = [l for l in deps if l.lower().startswith(("pip ", "python ", "install"))]
    has_openpyxl = any("openpyxl" in l for l in deps)
    record("T13 requirements.txt可被pip解析（无命令前缀，含openpyxl）", not bad and has_openpyxl,
           f"依赖行: {deps}")
    # README必须声明openpyxl依赖
    readme = (tmp_pkg / "README.md").read_text(encoding="utf-8")
    record("T13b README声明openpyxl依赖", "openpyxl" in readme)

# ---------- T14 Excel表内数字与说明文字一致性（防"数字打架"回归） ----------
def t14(xlsx):
    try:
        from openpyxl import load_workbook
    except ImportError:
        record_skip("T14 Excel口径一致性", "缺少openpyxl")
        return
    wb = load_workbook(xlsx)
    ws = wb["对比总览"]
    # 计算权威有效数top1（来自competitor_gm_detail）
    det = json.loads((tmp_pkg / "data" / "competitor_gm_detail.json").read_text(encoding="utf-8"))
    SHORT = {"三未信安科技股份有限":"三未信安","渔翁信息技术股份有限":"渔翁信息","北京江南天安科技有限":"江南天安",
             "广州江南科友科技股份":"江南科友","数盾信息科技股份有限":"数盾科技","北京海泰方圆科技股份":"海泰方圆",
             "北京数字认证股份有限":"北京CA","长春吉大正元信息技术":"吉大正元","北京信安世纪科技股份":"信安世纪","格尔软件股份有限":"格尔软件"}
    eff = {}
    for full, recs in det.items():
        s = SHORT.get(full[:12], full[:6])
        eff[s] = sum(1 for r in recs if r["status"] == "有效")
    top1_name, top1_n = max(eff.items(), key=lambda kv: kv[1])
    texts = [str(c.value) for row in ws.iter_rows() for c in row if isinstance(c.value, str)]
    gap1 = next((t for t in texts if "差距①" in t), "")
    ok = (top1_name in gap1) and (str(top1_n) in gap1)
    record("T14a 差距①文字与表内权威数据一致", ok, f"权威top1={top1_name}{top1_n} | 文本: {gap1[:60]}")
    # 各公司sheet国密标题：状态计数之和 == 总数（防"凭空少1条"回归）
    mism = []
    for name in ("吉大正元", "中安云科", "三未信安", "格尔软件", "北京CA"):
        w = wb[name]
        for row in w.iter_rows(max_row=15, max_col=1):
            v = str(row[0].value or "")
            m = re.search(r"官网共\s*(\d+)\s*条（(.+)）", v)
            if m:
                total = int(m.group(1)); parts = re.findall(r"(\d+)", m.group(2))
                if sum(int(p) for p in parts) != total:
                    mism.append(f"{name}:{m.group(0)[:40]}")
                break
    record("T14b 公司sheet国密标题计数加总==总数", not mism, f"不一致: {mism or '无'}")
    # EPRI跨sheet一致性：北京CA在总览与排行榜同值
    ep_overview = None
    for row in ws.iter_rows(max_col=10):
        if row[0].value == "北京CA":
            ep_overview = row[8].value; break
    rank_ws = wb["资质排行榜"]
    ep_rank = None
    current = None
    # 块序：一、国密有效 二、网专 三、IPv6 四、EPRI 五、FIPS 六、国密总量（单次遍历同步跟踪块）
    for row in rank_ws.iter_rows(min_col=1, max_col=4):
        v = str(row[0].value or "")
        if v.startswith("四、"): current = "epri"
        elif v.startswith(("五、", "六、")): current = None
        if current == "epri" and row[1].value == "北京CA":
            ep_rank = row[3].value
    record("T14c 北京CA EPRI跨Sheet一致（总览=排行榜）", ep_overview == ep_rank,
           f"总览={ep_overview}, 排行榜={ep_rank}")

for t in (t1, t2, t3, t4, t5_t6_t7_t8, t9, t10, t11, t12, t13, lambda: t14(tmp_pkg / "outputs" / "中安云科vs竞品资质对比表.xlsx")):
    try:
        t()
    except Exception as e:
        record(f"{t.__name__} 执行异常", False, repr(e)[:200])

# ---------- 汇总 ----------
log("\n===== 测试汇总 =====")
n_pass = sum(1 for _, s in RESULTS if s == "PASS")
n_fail = sum(1 for _, s in RESULTS if s == "FAIL")
n_skip = sum(1 for _, s in RESULTS if s == "SKIP")
for name, s in RESULTS:
    log(f"  {s}  {name}")
log(f"\n合计: {n_pass} 通过, {n_fail} 失败, {n_skip} 跳过")
log_file = PKG.parent / "outputs" / f"test-log-{datetime.date.today().isoformat()}.txt"  # 写到包外outputs/，避免污染源码目录
log_file.parent.mkdir(parents=True, exist_ok=True)
log_file.write_text("\n".join(LOG_LINES), encoding="utf-8")
log(f"日志已写入: {log_file}")
sys.exit(1 if n_fail else 0)
