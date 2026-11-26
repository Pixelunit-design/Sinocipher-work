# -*- coding: utf-8 -*-
"""中安云科 vs 竞品 资质对比表生成脚本 v3（包内相对路径 + 有效证书口径排行榜）

依赖：openpyxl（pip install openpyxl）
输入：本技能包 data/ 目录下的 JSON 快照
输出：本技能包 outputs/中安云科vs竞品资质对比表.xlsx
"""
import json, math
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
OUT = ROOT / 'outputs' / '中安云科vs竞品资质对比表.xlsx'
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(DATA / 'zayk_certs.json', encoding='utf-8') as f:
    zayk = json.load(f)
with open(DATA / 'competitor_gm_detail.json', encoding='utf-8') as f:
    gm = json.load(f)
with open(DATA / 'competitor_other_detail.json', encoding='utf-8') as f:
    other = json.load(f)
# 江南科友数据优先级：competitor_gm_detail.json（刷新脚本会写入此文件）优先，
# jnkf_gm_detail.json 仅为历史种子，避免旧数据覆盖已刷新数据（消除双数据源冲突）
if '江南科友' in gm:
    jnkf_src = 'competitor_gm_detail.json（已含，可能经脚本刷新）'
else:
    with open(DATA / 'jnkf_gm_detail.json', encoding='utf-8') as f:
        gm['江南科友'] = json.load(f)
    jnkf_src = 'jnkf_gm_detail.json（历史种子，未刷新）'
with open(DATA / 'summary_all.json', encoding='utf-8') as f:
    summary_all = json.load(f)
with open(DATA / 'competitor_gm.json', encoding='utf-8') as f:
    gm_summary = json.load(f)  # 权威有效数/快照日期源（data/README.md 口径链第2层）

# 逐企业快照描述（动态生成，禁止硬编码日期）
SNAP_TXT_ITEMS = []
for _full, _rec in gm_summary.items():
    eff = _rec.get('status', {}).get('有效')
    if eff is not None and _rec.get('refreshed_at'):
        SNAP_TXT_ITEMS.append(f"{_full[:6]}…{_rec['refreshed_at']}刷新(有效{eff}/总量{_rec['total']})")
REFRESH_NOTE = ('；已刷新差异：' + '、'.join(SNAP_TXT_ITEMS)) if SNAP_TXT_ITEMS else ''
# EPRI权威口径=用户汇总表(summary_all, L4)；competitor_other_detail明细缺北京CA记录
_EPR = {x['short']: x['epri'] for x in summary_all}
_EPR_ALIAS = {'北京CA': '数字认证'}

# ---------- 样式 ----------
THIN = Side(style='thin', color='BFBFBF')
MED = Side(style='medium', color='8496B0')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HDR_FILL = PatternFill('solid', fgColor='1F4E79')       # 深蓝 列头
GRP_FILL = PatternFill('solid', fgColor='2E75B6')       # 中蓝 分组头
SEC_FILL = PatternFill('solid', fgColor='D9E2F3')       # 浅蓝 区块标题
ANCHOR_FILL = PatternFill('solid', fgColor='FFF2CC')    # 浅黄 中安云科列/行
ZEBRA = PatternFill('solid', fgColor='F5F8FC')          # 斑马纹
TITLE_FONT = Font(name='微软雅黑', size=16, bold=True, color='1F4E79')
SUB_FONT = Font(name='微软雅黑', size=9, italic=True, color='7F7F7F')
HDR_FONT = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
GRP_FONT = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
SEC_FONT = Font(name='微软雅黑', size=12, bold=True, color='1F4E79')
BODY_FONT = Font(name='微软雅黑', size=10, color='262626')
NOTE_FONT = Font(name='微软雅黑', size=9, italic=True, color='595959')
GREEN = PatternFill('solid', fgColor='C6EFCE')
ORANGE = PatternFill('solid', fgColor='FFEB9C')
RED = PatternFill('solid', fgColor='FFC7CE')
GRAY = PatternFill('solid', fgColor='F2F2F2')
WRAP = Alignment(wrap_text=True, vertical='center')
LEFT = Alignment(horizontal='left', vertical='center', wrap_text=True)
CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
CENTER_NW = Alignment(horizontal='center', vertical='center')  # 数字列不换行，避免 ####

def disp_units(s):
    return sum(2 if ord(ch) > 127 else 1 for ch in str(s))

def est_h(vals, widths, min_h=20):
    """按列宽估算折行所需行高（vals 从第1列开始）"""
    lines = 1
    for v, w in zip(vals, widths):
        if v is None: continue
        cap = max(4, int(w) - 2)
        lines = max(lines, math.ceil(disp_units(v) / cap))
    return max(min_h, 14 * lines + 5)

def fill_row(ws, r, c1, c2, fill=None, font=None, border=True):
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=r, column=c)
        if fill: cell.fill = fill
        if font: cell.font = font
        if border: cell.border = BORDER
        cell.alignment = CENTER

def merge_cell(ws, r, c1, c2, text, fill=None, font=None, align=LEFT):
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=r, column=c)
        if fill is not None: cell.fill = fill
        cell.border = BORDER
    ws.cell(row=r, column=c1, value=text)
    if font: ws.cell(row=r, column=c1).font = font
    ws.cell(row=r, column=c1).alignment = align
    if c2 > c1: ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)

def spacer(ws, r, h=10):
    ws.row_dimensions[r].height = h
    return r + 1

def style_header(ws, row, ncols, fill=None, font=None):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = fill or HDR_FILL
        cell.font = font or HDR_FONT
        cell.border = BORDER
        cell.alignment = CENTER
    ws.row_dimensions[row].height = 26

def write_table(ws, start_row, headers, rows, status_col=None, widths=None, zebra=True, row_h=None, with_header=True, spans=None):
    """通用明细表：分组色带的列头 + 可选斑马纹 + 自动行高。
    spans: 逻辑列 → 物理列区间列表，如 [(1,1),(2,2),(3,5)]，使表格占满整个网格宽度。"""
    if spans is None:
        spans = [(j, j) for j in range(1, len(headers) + 1)]
    ncols = spans[-1][1]
    caps = [max(4, sum(widths[c1-1:c2]) - 2) if widths else 20 for (c1, c2) in spans]
    if with_header:
        style_header(ws, start_row, ncols)
        for j, (c1, c2) in enumerate(spans):
            ws.cell(row=start_row, column=c1, value=headers[j])
            if c2 > c1:
                ws.merge_cells(start_row=start_row, start_column=c1, end_row=start_row, end_column=c2)
        start_row += 1
    r = start_row
    for k, row_data in enumerate(rows):
        zeb = ZEBRA if (zebra and k % 2 == 1) else None
        lines = 1
        for v, cap in zip(row_data, caps):
            if isinstance(v, str):
                lines = max(lines, math.ceil(disp_units(v) / cap))
        for j, (c1, c2) in enumerate(spans):
            v = row_data[j]
            is_status = (status_col == j + 1)
            fill = None
            if is_status:
                s = str(v)
                if s == '有效': fill = GREEN
                elif s == '过期': fill = ORANGE
                elif s == '注销': fill = RED
            elif zeb:
                fill = zeb
            for c in range(c1, c2 + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = BORDER
                if fill: cell.fill = fill
            cell = ws.cell(row=r, column=c1, value=v)
            cell.font = BODY_FONT
            cell.alignment = CENTER_NW if isinstance(v, (int, float)) else LEFT
            if c2 > c1:
                ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
        if row_h:
            ws.row_dimensions[r].height = row_h
        else:
            ws.row_dimensions[r].height = est_h(row_data, caps)
        r += 1
    return r

def section(ws, row, text, ncols):
    merge_cell(ws, row, 1, ncols, text, fill=SEC_FILL, font=SEC_FONT, align=LEFT)
    ws.row_dimensions[row].height = 30
    return row + 1

# ---------- 企业资质数据（联网检索 2026-09-07） ----------
corp = {
 '中安云科': [
  ('资本市场状态','—','未上市','画册/工商信息'),
  ('国家高新技术企业','国家级','—','2026画册'),
  ('山东省/市级专精特新企业','省级/市级','—','2026画册'),
  ('山东省/市级瞪羚企业','省级/市级','—','2026画册'),
  ('CMMI 5级','国际/能力成熟度','—','2026画册'),
  ('ISO9001质量管理体系认证','国际','—','2026画册'),
  ('ISO27001信息安全管理体系认证','国际','—','2026画册'),
  ('五星级售后服务认证','国家级','—','2026画册'),
  ('信息安全服务资质','行业','—','2026画册'),
  ('ISO22301业务连续性管理体系认证','国际','—','用户提供证书（2026-09-07）'),
  ('ISO20000-1信息技术服务管理体系认证','国际','—','用户提供证书（2026-09-07）'),
  ('ISO45001职业健康安全管理体系（GB/T 45001-2020/ISO 45001:2018）','国际','注册号03424S20329R1S · 2024-06-25~2027-07-21（初次颁证2021-07-23）· 北京航协认证中心','用户提供证书'),
  ('ISO14001环境管理体系（GB/T 24001-2016/ISO 14001:2015）','国际','注册号03424E30366R1S · 2024-06-25~2027-07-21（初次颁证2021-07-23）· 北京航协认证中心','用户提供证书'),
 ],
 '三未信安': [
  ('资本市场状态','A股科创板','688489（2022年12月上市）','交易所公开信息'),
  ('国家高新技术企业','国家级','GR202511004593（2025-12~2028-12）','全国高企认定管理办公室'),
  ('国家级专精特新重点"小巨人"企业','国家级','2022年入选','工信部'),
  ('北京市"专精特新"中小企业','省级','2023-12~2026-12','北京市经信局'),
  ('CMMI-DEV ML5级','国际','2022年通过','公司官网'),
  ('ISO9001质量管理体系','国际','2011年通过','公司官网'),
  ('ISO27001信息安全管理体系','国际','2015年通过','公司官网'),
  ('ITSS信息技术服务标准等多项体系认证','行业','—','公司官网'),
  ('国家密码科技进步奖5次','奖项','最近2024年2项','公司官网'),
  ('2024/2025信创500强','榜单','2025年第474名','DBC德本咨询'),
  ('并购：江南天安、江南科友、世纪先承','资本运作','2023-2024年','公司官网'),
 ],
 '渔翁信息': [
  ('资本市场状态','未上市','科创板IPO于2024年6月撤回终止','上交所公告'),
  ('⚠ 欺诈发行行政处罚','监管处罚','2026年7月江西证监局对公司及实控人合计罚款超1000万元（公司400万）','江西证监局'),
  ('国家级专精特新重点"小巨人"企业','国家级','2022年入选（2021年首次入选小巨人）','工信部'),
  ('国家高新技术企业','国家级','GR202337009490（2023-12~2026-12）','全国高企认定管理办公室'),
  ('国家知识产权示范企业','国家级','2023-11~2026-11','国家知识产权局'),
  ('山东省"专精特新"中小企业','省级','2025-06~2028-06','山东省工信厅'),
  ('山东省瞪羚企业','省级','2021年获评','威海市政府'),
  ('ISO9001/ISO27001/ISO20000体系认证','国际','—','公司官网'),
  ('ITSS、信息系统安全集成二级、安全运维三级','行业','—','公司官网'),
  ('国家密码科学技术奖4次','奖项','—','公司官网'),
  ('国家信创工委会密码应用组组长单位','行业地位','—','公司官网'),
 ],
 '江南天安': [
  ('资本市场状态','未上市','2024年被三未信安并购，成为其子公司','三未信安官网'),
  ('国家高新技术企业','国家级','GR202311002466（2023-10~2026-10）','全国高企认定管理办公室'),
  ('国家级专精特新"小巨人"企业','国家级','2025-10~2028-10（第二次认定）','工信部'),
  ('北京市企业技术中心','省级','2024年度','北京市经信局'),
  ('ISO9001/ISO27001/ISO20000体系认证','国际','—','信创产业网'),
  ('CMMI-Dev','国际','—','信创产业网'),
  ('安全服务资质（集成/应急/风险评估/等保建设）','行业','—','信创产业网'),
  ('2023/2024北京民营企业中小100强','榜单','2024年第52名','北京市工商联'),
 ],
 '江南科友': [
  ('资本市场状态','未上市','三未信安控股86.28%（2023-06收购66.93%，2024-06增至86.28%）','三未信安公告/企查'),
  ('国家高新技术企业','国家级','广东认定','百度百科'),
  ('广东省专精特新企业','省级','—','百度百科'),
  ('广州市科技小巨人企业','市级','—','百度百科'),
  ('软件企业认定','行业','—','百度百科'),
  ('广东省商用密码应用工程技术研究中心','省级','—','百度百科'),
  ('信息安全集成资质','行业','—','百度百科'),
  ('国家科技部创新基金首批支持企业','国家级','1991年成立，1998年全面进入商用密码领域','百度百科'),
  ('广东软件风云榜"新锐企业"（2024）','榜单','2024年税务信用评级A级','广东软件行业协会'),
 ],
 '数盾科技': [
  ('资本市场状态','未上市','2023年1月获中能智慧战略投资（此前C轮1亿元）','亿欧数据'),
  ('国家高新技术企业','国家级','GR202411009042（2024-12~2027-12）','全国高企认定管理办公室'),
  ('国家级专精特新重点"小巨人"企业','国家级','2024年入选（2021年首次）','工信部'),
  ('北京市"专精特新"中小企业','省级','2024-02~2027-02','北京市经信局'),
  ('北京市企业技术中心','省级','2023年认定','北京市经信局'),
  ('ISO9001/ISO27001体系认证','国际','—','人民政协网'),
  ('CMMI3级、CCRC认证、CS认证','行业','—','人民政协网'),
  ('信息安全服务资质（集成/运维/风险评估）','行业','—','人民政协网'),
  ('北京市科学技术奖一等奖（2022）','奖项','云安全关键技术与应用','北京市科委'),
 ],
 '海泰方圆': [
  ('资本市场状态','未上市','—','工商信息'),
  ('国家高新技术企业','国家级','GR202311001881（2023-10~2026-10）','全国高企认定管理办公室'),
  ('国家级专精特新重点"小巨人"企业','国家级','2022年入选','工信部'),
  ('国家知识产权示范企业','国家级','2023-11~2026-11','国家知识产权局'),
  ('工信部首批商用密码硬科技潜力企业','国家级','2024年','工信部'),
  ('北京市"专精特新"中小企业','省级','2023-12~2026-12','北京市经信局'),
  ('CMMI5级','国际','—','公司官网'),
  ('ISO9001/ISO27001/ISO20000体系认证','国际','—','公司官网'),
  ('信息安全服务资质（集成/开发/运维）','行业','—','公司官网'),
  ('电子文件真实性认定与保障技术北京市工程实验室','省级','—','公司官网'),
  ('密码科技进步奖一、二、三等奖及北京市科技奖','奖项','—','公司官网'),
 ],
 '北京CA': [
  ('资本市场状态','A股创业板','300579（2016年12月上市，"中国电子认证第一股"）','深交所'),
  ('资本市场备注','国企背景','北京国资公司实际控制，2025年9月控股股东变更为北京数据集团','公司公告'),
  ('国家高新技术企业','国家级','GR202311000370（2023-10~2026-10）','全国高企认定管理办公室'),
  ('国务院国资委科改示范企业','国家级','2020年起连续入选','国务院国资委'),
  ('国家科学技术进步奖二等奖','国家级','2018年（参与4个项目）','科技部'),
  ('北京市企业技术中心','省级','2023年认定','北京市经信局'),
  ('ISO27001信息安全管理体系','国际','—','认证平台'),
  ('CS信息系统建设和服务能力评估','行业','—','认证平台'),
  ('首批电子认证服务资质机构、北京商密协会会长单位','行业地位','—','公司官网'),
  ('2025信创500强第54名','榜单','2024年第117名','DBC德本咨询'),
 ],
 '吉大正元': [
  ('资本市场状态','A股深主板','003029（2020年12月上市）','深交所'),
  ('国家高新技术企业','国家级','GR202322000661（2023-10~2026-10）','全国高企认定管理办公室'),
  ('国家级专精特新"小巨人"企业','国家级','2020-11~2023-11','工信部'),
  ('吉林省"专精特新"中小企业','省级','2025-11~2028-11','吉林省工信厅'),
  ('涉密信息系统集成甲级（软件开发）','国家级','子公司长春吉大正元信息安全持有','国家保密局'),
  ('涉密信息系统集成乙级（运行维护）','国家级','同上','国家保密局'),
  ('信息系统安全集成二级服务资质','行业','—','CCRC'),
  ('ISO9001/ISO20000/ISO27001体系认证','国际','—','公司官网'),
  ('国家科技进步二等奖、密码科学技术进步一等奖等多项奖项','奖项','—','公司官网'),
  ('国家规划布局内重点软件企业','国家级','—','公司官网'),
 ],
 '信安世纪': [
  ('资本市场状态','A股科创板','688201（2021年4月上市）','上交所'),
  ('国家高新技术企业','国家级','GR202311002171（2023-10~2026-10）','全国高企认定管理办公室'),
  ('国家级专精特新"小巨人"企业','国家级','2021-07~2024-07','工信部'),
  ('北京市专精特新"小巨人"/中小企业','省级','2020-2023','北京市经信局'),
  ('CMMI5级','国际','—','公司官网'),
  ('ISO9001/ISO27001/ISO20000/ISO45001体系认证','国际','—','公司官网'),
  ('高新技术企业创新能力AAAAA','行业','—','公司官网'),
  ('省部级科技进步三等奖','奖项','2015年','公司官网'),
  ('2025北京专精特新企业100强第88名、2025信创500强第341名','榜单','—','北京企联/DBC'),
 ],
 '格尔软件': [
  ('资本市场状态','A股沪主板','603232（2017年4月上市）','上交所'),
  ('国家高新技术企业','国家级','GR202431000480（2024-12~2027-12）','全国高企认定管理办公室'),
  ('国家级专精特新"小巨人"企业','国家级','2024-09~2027-09','工信部'),
  ('上海市"专精特新"中小企业','省级','2023-03~2026-03','上海市经信委'),
  ('国家科学技术进步奖二等奖2次','国家级','最近2025年度再次获奖','科技部'),
  ('CMMI5级','国际','—','公司官网'),
  ('ISO9001/ISO27001/ISO20000体系认证','国际','—','公司官网'),
  ('CCRC信息安全服务资质、CS认证','行业','—','公司官网'),
  ('商用密码产品生产定点单位、国家火炬计划重点高新技术企业','国家级','—','公司官网'),
  ('2025信创500强第181名','榜单','—','DBC德本咨询'),
 ],
}

# ---------- 企业资质对比矩阵（维度 × 10家公司；顺序与 companies 一致） ----------
MATRIX_DIMS = [
 ('资本市场','未上市','科创板 688489','未上市(IPO撤回)','未上市(被并购)','未上市(三未控股)','未上市','未上市','创业板 300579','深主板 003029','科创板 688201','沪主板 603232'),
 ('国家高新技术企业','✓','✓','✓','✓','✓','✓','✓','✓','✓','✓','✓'),
 ('专精特新·最高级别','省/市级','重点小巨人','重点小巨人','小巨人','省级(广东)','重点小巨人','重点小巨人','—','小巨人','小巨人','小巨人'),
 ('瞪羚企业','✓ 省/市级','—','✓ 省级','—','—','—','—','—','—','—','—'),
 ('CMMI 成熟度','5级','5级','—','Dev','—','3级','5级','—','—','5级','5级'),
 ('ISO 9001','✓','✓','✓','✓','—','✓','✓','未检索到','✓','✓','✓'),
 ('ISO 27001','✓','✓','✓','✓','—','✓','✓','✓','✓','✓','✓'),
 ('其他体系扩展','✓20000/22301/14001/45001','—','✓20000','✓20000','—','—','✓20000','—','✓20000','✓20000/45001','✓20000'),
 ('涉密信息系统集成资质','—','—','—','—','—','—','—','—','✓甲级+乙级','—','—'),
 ('企业技术中心/工程实验室','—','—','—','✓市技术中心','✓省工程研究中心','✓市技术中心','✓市工程实验室','✓市技术中心','—','—','—'),
 ('国家知识产权示范企业','—','—','✓','—','—','—','✓','—','—','—','—'),
 ('信息安全服务资质/CCRC/CS','✓','✓ITSS','✓集成二级','✓','✓信息安全集成','✓CCRC/CS','✓','CS评估','✓集成二级','创新能力AAAAA','✓CCRC/CS'),
 ('省部级以上科技奖项','—','✓密码科5次','✓密码科4次','—','—','✓市科技一等奖','✓密码/市科技奖','✓国家科进二等奖','✓国家科进二等奖','✓省部级三等奖','✓国家科进二等奖×2'),
 ('特色标签/行业地位','五星级售后服务','信创500强#474','信创工委会密码组长','北京民企百强#52','广州市科技小巨人','—','工信部商密潜力企业','科改示范·商密协会长','国家规划重点软件','专精特新百强#88','火炬重点·商密定点'),
 ('⚠ 风险/并购事项','—','—','⚠欺诈发行被罚','⚠2024被并购','⚠三未控股(非独立)','—','—','—','—','—','—'),
]

# ---------- 中安云科网专19条：读取 data/zayk_certs.json cac 字段（用户2026-09-07截图转录，已迁入数据层） ----------
zayk_wz = zayk['cac']  # [{cat,name,model,ver,org,no,valid}, ...]

companies = ['中安云科','三未信安','渔翁信息','江南天安','江南科友','数盾科技','海泰方圆','北京CA','吉大正元','信安世纪','格尔软件']
full_names = {'中安云科':'中安云科科技发展（山东）有限公司','三未信安':'三未信安科技股份有限公司','渔翁信息':'渔翁信息技术股份有限公司（渔翁云科技为同一主体，已合并）','江南天安':'北京江南天安科技有限公司','江南科友':'广州江南科友科技股份有限公司（三未信安控股86.28%）','数盾科技':'数盾信息科技股份有限公司','海泰方圆':'北京海泰方圆科技股份有限公司','北京CA':'北京数字认证股份有限公司','吉大正元':'长春吉大正元信息技术股份有限公司','信安世纪':'北京信安世纪科技股份有限公司','格尔软件':'格尔软件股份有限公司'}

def stats(recs):
    from collections import Counter
    return Counter(r['status'] for r in recs)

wb = Workbook()

# ============ Sheet 1: 对比总览 ============
ws = wb.active
ws.title = '对比总览'
ws.sheet_view.showGridLines = False

NW = 12  # 总列数 A..L（与企业资质矩阵 1+11 家对齐）
# 列宽：A/B 文本较宽；C~J 数字/公司列；K:L 合并为国际认证说明列
OW = [18, 18, 10, 10, 10, 10, 10, 10, 10, 10, 24, 24]
for i, w in enumerate(OW, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# --- 标题 ---
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NW)
ws.cell(row=1, column=1, value='中安云科 vs 10家竞品 资质对比总览').font = TITLE_FONT
ws.row_dimensions[1].height = 34
r = spacer(ws, 2, 4)

# ========== 一、产品资质对比（分组表头） ==========
grp_rows = [('公司基本信息', 1, 2), ('商用密码认证（国密证书 · 官网口径）', 3, 6),
            ('其他产品认证（网专 / IPv6 / 电科院EPRI / FIPS）', 7, 10), ('国际密码模块认证', 11, 12)]
for text, c1, c2 in grp_rows:
    merge_cell(ws, r, c1, c2, text, fill=GRP_FILL, font=GRP_FONT, align=CENTER)
ws.row_dimensions[r].height = 24
r += 1

headers = ['公司', '资本市场', '有效', '过期', '注销', '总量', '网专', 'IPv6', 'EPRI', 'FIPS', 'ISO/IEC 19790']
for j, h in enumerate(headers, 1):
    ws.cell(row=r, column=j, value=h)
style_header(ws, r, NW)
ws.merge_cells(start_row=r, start_column=11, end_row=r, end_column=12)  # ISO 列跨 K:L
ws.row_dimensions[r].height = 24
r += 1

gm_stats = {}
gm_stats['中安云科'] = stats(zayk['gm'])
for c in companies[1:]:
    gm_stats[c] = stats(gm[c])

def fips_real(rr):
    """过滤汇总表中'FIPS认证：—'占位垃圾行"""
    return rr['no'] not in ('-', '—', '') and rr['name'] not in ('-', '—', '')

wz_cnt, ip_cnt, ep_cnt, fp_cnt = {}, {}, {}, {}
for c in companies:
    wz_cnt[c] = ip_cnt[c] = ep_cnt[c] = fp_cnt[c] = 0
wz_cnt['中安云科'] = len(zayk_wz)
ip_cnt['中安云科'] = len(zayk.get('ipv6', []))
for c in companies[1:]:
    for rr in other.get(c, []):
        if rr['src'] == '网专产品认证/检测': wz_cnt[c] += 1
        elif rr['src'] == 'IPv6 Ready Logo认证': ip_cnt[c] += 1
        elif rr['src'] == '电科院EPRI检测报告': ep_cnt[c] += 1
        elif rr['src'] == 'FIPS认证' and fips_real(rr): fp_cnt[c] += 1
# EPRI 权威口径对齐：以用户汇总表（summary_all，L4）为准——明细文件缺北京CA记录，防止跨Sheet打架
for c in companies:
    _k = _EPR_ALIAS.get(c, c)
    if _k in _EPR and _EPR[_k] > ep_cnt[c]:
        ep_cnt[c] = _EPR[_k]

market = {'中安云科':'未上市','三未信安':'科创板 688489','渔翁信息':'未上市','江南天安':'未上市（被并购）','江南科友':'未上市（三未控股）','数盾科技':'未上市','海泰方圆':'未上市','北京CA':'创业板 300579','吉大正元':'深主板 003029','信安世纪':'科创板 688201','格尔软件':'沪主板 603232'}
recs_total = {'中安云科': zayk['gm']}
for c in companies[1:]:
    recs_total[c] = gm[c]

product_first = r
for k, c in enumerate(companies):
    s = gm_stats[c]
    total = len(recs_total[c])
    iso19790 = '全球首批（2023-10，1项）' if c == '中安云科' else ('第二批（2024-07）' if c == '三未信安' else '—')
    vals = [c, market[c], s.get('有效',0), s.get('过期',0), s.get('注销',0), total,
            wz_cnt[c], ip_cnt[c], ep_cnt[c], fp_cnt[c]]
    for j, v in enumerate(vals, 1):
        cell = ws.cell(row=r, column=j, value=v)
        cell.font = BODY_FONT; cell.border = BORDER
        cell.alignment = LEFT if j in (1,2) else CENTER_NW
        if k % 2 == 1: cell.fill = ZEBRA
        if c == '中安云科':
            cell.fill = ANCHOR_FILL
            cell.font = Font(name='微软雅黑', size=10, bold=True, color='7F6000')
    # ISO 列跨 K:L 合并
    for cc in (11, 12):
        cell = ws.cell(row=r, column=cc)
        cell.border = BORDER
        cell.alignment = LEFT
        if k % 2 == 1: cell.fill = ZEBRA
        if c == '中安云科':
            cell.fill = ANCHOR_FILL
    ws.cell(row=r, column=11, value=iso19790)
    if c == '中安云科':
        ws.cell(row=r, column=11).font = Font(name='微软雅黑', size=10, bold=True, color='7F6000')
    else:
        ws.cell(row=r, column=11).font = BODY_FONT
    ws.merge_cells(start_row=r, start_column=11, end_row=r, end_column=12)
    ws.row_dimensions[r].height = 22
    r += 1
r = spacer(ws, r, 6)
# 产品表脚注
merge_cell(ws, r, 1, NW, '注：渔翁信息与"渔翁云"为同一主体（官网口径已合并）；江南天安、江南科友均为三未信安控股子公司；吉大正元另有1条"其他"状态记录未计入有效/过期/注销。', font=NOTE_FONT)
ws.row_dimensions[r].height = 18
r = spacer(ws, r, 12)

# ========== 二、企业资质对比矩阵 ==========
r = section(ws, r, '二、企业资质对比（公司级 · 2026-09-07联网检索）', NW)
hdr_row = r
ws.cell(row=r, column=1, value='资质维度')
for j, cn in enumerate(companies, 2):
    ws.cell(row=r, column=j, value=cn)
style_header(ws, r, NW)
ws.row_dimensions[r].height = 26
# 中安云科列(第2列)高亮表头
ws.cell(row=r, column=2).fill = ANCHOR_FILL
ws.cell(row=r, column=2).font = Font(name='微软雅黑', size=10, bold=True, color='7F6000')
r += 1

MZ = OW  # 供行高估算用（12列与矩阵一一对应）
for k, dim in enumerate(MATRIX_DIMS):
    label = dim[0]
    risk = label.startswith('⚠')
    for j, v in enumerate(dim, 1):
        cell = ws.cell(row=r, column=j, value=v)
        cell.border = BORDER
        cell.alignment = LEFT if j == 1 else CENTER
        if j == 1:
            cell.font = Font(name='微软雅黑', size=10, bold=True, color='C00000' if risk else '1F4E79')
            cell.fill = SEC_FILL if not risk else PatternFill('solid', fgColor='FBE4E4')
        else:
            if j == 2:
                cell.fill = ANCHOR_FILL
                cell.font = Font(name='微软雅黑', size=10, bold=True, color='7F6000')
            else:
                if risk:
                    cell.font = Font(name='微软雅黑', size=10, color='C00000')
                    if str(v) != '—': cell.fill = PatternFill('solid', fgColor='FBE4E4')
                elif str(v) == '—' or '未检索' in str(v):
                    cell.font = Font(name='微软雅黑', size=10, color='A6A6A6')
                else:
                    cell.font = BODY_FONT
                    if k % 2 == 1: cell.fill = ZEBRA
    ws.row_dimensions[r].height = est_h(dim, MZ, min_h=22)
    r += 1

legend = [
 '注①：✓=已具备；—=未检索到该项资质（不代表一定没有，最终以官方平台及资质证书原件为准）。',
 '注②："重点小巨人"=工信部国家级专精特新"重点"小巨人；"小巨人"=国家级专精特新"小巨人"；级别认定年份与证书编号见各公司sheet。',
 '注③：江南天安、江南科友均为三未信安控股子公司（"三未系"）；渔翁信息2026-07因科创板欺诈发行被江西证监局处罚；11家（含中安云科）均为国家级高新技术企业。',
]
for t in legend:
    merge_cell(ws, r, 1, NW, t, font=NOTE_FONT)
    ws.row_dimensions[r].height = 16
    r += 1
r = spacer(ws, r, 12)

# ========== 三、中安云科视角速览 ==========
r = section(ws, r, '三、中安云科关键差距与优势速览（供对外口径参考）', NW)
# —— 差距数字全部由数据动态生成，禁止硬编码 ——
eff_all = sorted(companies, key=lambda c: -gm_stats[c].get('有效', 0))
zk_eff = gm_stats['中安云科'].get('有效', 0)
zk_eff_rank = eff_all.index('中安云科') + 1
_t3 = [(c, gm_stats[c].get('有效', 0)) for c in eff_all if c != '中安云科'][:3]
_t3txt = '、'.join(f'{c}{v}' for c, v in _t3)
_zk_total = gm_stats['中安云科']['有效'] + gm_stats['中安云科'].get('过期', 0) + gm_stats['中安云科'].get('注销', 0) + sum(v for k, v in gm_stats['中安云科'].items() if k not in ('有效', '过期', '注销'))
ep_sorted = sorted((c for c in companies[1:] if ep_cnt[c] > 0), key=lambda c: -ep_cnt[c])
_ep3txt = '、'.join(f'{c}{ep_cnt[c]}' for c in ep_sorted[:3]) or '竞品中暂无已核验EPRI记录'
ip_sorted = sorted((c for c in companies[1:] if ip_cnt[c] > 0), key=lambda c: -ip_cnt[c])
_ip3txt = '、'.join(f'{c}{ip_cnt[c]}' for c in ip_sorted[:3])
insights = [
 (f'【差距① 国密证书存量】', f'有效{zk_eff}条居11家第{zk_eff_rank}位（首位{_t3txt}）；含过期/注销共{_zk_total}条，对外建议统一以"有效{zk_eff}条"口径。', 'C00000'),
 ('【差距② 电科院EPRI】', f'中安云科0条，而{_ep3txt}已有——面向电力行业投标的资质叙事最明显缺口。', 'C00000'),
 ('【差距③ IPv6 Ready】', f'中安{ip_cnt["中安云科"]}条，{_ip3txt}领先；IPv6列装要求趋严背景下建议重点补强。', 'C00000'),
 ('【差距④ 国家级资质】', '竞品10家中8家获国家级专精特新（重点）小巨人、5家已上市；三未系（三未信安+江南天安+江南科友）已形成"芯片-整机-金融密码"集团军；中安现为省市级专精特新+瞪羚，申请国家级小巨人是缩短差距的关键动作。', 'C00000'),
 ('【优势① 国际认证】', 'ISO/IEC 19790密码模块认证全球首批（2023-10）——11家中仅三未信安为第二批，其余9家均无，可直接用于密评高端市场叙事。', '006100'),
 ('【优势② 体系认证齐全】', 'ISO管理体系证书全：9001/14001/20000/22301/27001/45001六项全覆盖（多数竞品仅2-3项）+五星级售后服务认证+CMMI5；11家均为国家级高新技术企业，此项无差异。', '006100'),
]
for tag, body, color in insights:
    merge_cell(ws, r, 1, NW, tag + body, align=LEFT)
    ws.cell(row=r, column=1).font = Font(name='微软雅黑', size=10, color=color)
    ws.row_dimensions[r].height = est_h([tag + body], [sum(OW)], min_h=24)
    r += 1
r = spacer(ws, r, 12)

# ========== 四、数据口径说明 ==========
r = section(ws, r, '四、数据口径与来源说明', NW)
notes = [
 f'1. 商密认证（国密）：商用密码认证业务网 scctc.org.cn 实时查询，基准快照2026-09-07{REFRESH_NOTE}（权威口径链见 data/README.md：competitor_gm.json 逐企业 refreshed_at 为准）；"有效/过期/注销"为官网状态字段，对比以"有效"列为准。',
 '2. 网专/IPv6/电科院EPRI/FIPS：竞品来自《2026重点企业资质认证汇总表》（2026年7月检索口径）；中安云科网专19条、IPv6 6条为2026-09-07官网检索核对（电科院确认无）。',
 '3. 企业资质（公司级）为2026-09-07联网检索（公司官网/认证平台/交易所公告/工信部等），"未检索到"不代表企业一定没有，引用前建议以证书原件复核；中安云科ISO体系证书以用户提供的证书原件为准。',
 '4. 渔翁信息与渔翁云为同一主体，已合并按"渔翁信息技术股份有限公司"统计（官网国密证书共123条）；江南科友官网国密证书103条（有效44/过期41/注销18）。',
 '5. 各公司明细sheet按"企业资质→国密认证→网专→IPv6→电科院EPRI→国际认证"六类展开，证书逐条列出并按状态标色（绿=有效/黄=过期/红=注销）。',
 f'6. 【资质排行榜】口径（2026-11-26定稿）：国密榜区分两榜——【有效证书榜】仅收录已逐条核验的11家（明细状态统计，基准快照2026-09-07{REFRESH_NOTE}；其余152家有效数未核验，不进榜、不作零）；【历史总量榜】为总数口径（2026-07汇总表+中安云科2026-09实查92条）。网专/IPv6/EPRI/FIPS为汇总表2026-07检索记录数口径（EPRI以用户汇总表为权威）。渔翁信息与渔翁云为同一主体已合并；同一企业跨方向重复行已按全称去重、各维度取最大值；各维度榜单取前50名，不足50家的按实际列全。',
]
for t in notes:
    merge_cell(ws, r, 1, NW, t, font=NOTE_FONT)
    ws.row_dimensions[r].height = est_h([t], [sum(OW)], min_h=16)
    r += 1

ws.freeze_panes = 'B2'

# ============ 各公司 Sheet ============
CW = [8, 26, 40, 20, 10, 10, 24, 11, 11, 9]  # A~J 列宽
CW_LAST = [cw + 10 for cw in CW]  # 备用

def write_merged_table(ws, start_row, segs, headers, rows):
    """三段式合并宽表：segs=[(c1,c2,标题)]，rows 每行值长度=len(segs)"""
    for (c1, c2, htext) in segs:
        merge_cell(ws, start_row, c1, c2, htext, fill=HDR_FILL, font=HDR_FONT, align=CENTER)
    ws.row_dimensions[start_row].height = 26
    r = start_row + 1
    for k, vals in enumerate(rows):
        risk = str(vals[0]).startswith('⚠')
        caps = [sum(CW[c1-1:c2]) - 2 for (c1, c2, _) in segs]
        lines = 1
        for v, cap in zip(vals, caps):
            lines = max(lines, math.ceil(disp_units(v) / max(4, cap)))
        for idx, (c1, c2, _) in enumerate(segs):
            if risk:
                fill = PatternFill('solid', fgColor='FBE4E4')
            else:
                fill = ZEBRA if (k % 2 == 1) else None
            font = Font(name='微软雅黑', size=10, bold=(risk and idx == 0), color=('C00000' if risk else '262626'))
            merge_cell(ws, r, c1, c2, vals[idx], fill=fill, font=font, align=LEFT)
        ws.row_dimensions[r].height = max(22, 14 * lines + 8)
        r += 1
    return r

def build_company_sheet(name):
    ws = wb.create_sheet(name[:31])
    ws.sheet_view.showGridLines = False
    for i, w in enumerate(CW, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=10)
    ws.cell(row=1, column=1, value=f'{name}（{full_names[name]}）· 资质明细').font = TITLE_FONT
    ws.row_dimensions[1].height = 32
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=10)
    ws.cell(row=2, column=1, value='信息层级：企业资质 → 商用密码认证（国密）→ 网专检测 → IPv6 Ready → 电科院EPRI → 国际认证；状态标色：绿=有效 / 黄=过期 / 红=注销。').font = SUB_FONT
    ws.row_dimensions[2].height = 16
    r = spacer(ws, 3, 6)

    # 一、企业资质（合并宽表）
    r = section(ws, r, '一、企业资质（公司级 · 2026-09-07联网检索）', 10)
    segs = [(1, 2, '资质名称 / 级别'), (3, 7, '证书编号 / 有效期 / 说明'), (8, 10, '数据来源')]
    rows = []
    for (nm, lv, dt, src) in corp[name]:
        nm_lv = f'{nm}（{lv}）' if lv not in ('', '—') else nm
        rows.append((nm_lv, dt, src))
    end = write_merged_table(ws, r, segs, ['资质名称 / 级别', '证书编号 / 有效期 / 说明', '数据来源'], rows)
    r = end + 1

    # 二、商用密码认证（表头仅一次，按状态分组色带）
    recs = zayk['gm'] if name == '中安云科' else gm[name]
    s = stats(recs)
    total = len(recs)
    # 非标准状态（如"待确认"）通用计入，保证 有效+过期+注销+其他 == 总数
    nonstd = {k: v for k, v in s.items() if k not in ('有效', '过期', '注销')}
    extra = '、' + '、'.join(f'{k} {v}' for k, v in nonstd.items()) if nonstd else ''
    merge_cell(ws, r, 1, 10, f'二、商用密码产品认证（国密）—— 官网共 {total} 条（有效 {s.get("有效",0)} / 过期 {s.get("过期",0)} / 注销 {s.get("注销",0)}{extra}）', fill=SEC_FILL, font=SEC_FONT, align=LEFT)
    ws.row_dimensions[r].height = 28
    r += 1

    GM_HEADERS = ['序号', '证书编号', '产品名称', '型号', '版本', '安全等级', '产品类型', '发证日期', '有效期至', '状态']
    for j, h in enumerate(GM_HEADERS, 1):
        ws.cell(row=r, column=j, value=h)
    style_header(ws, r, 10)
    r += 1

    order = {'有效': 0, '过期': 1, '注销': 2, '其他': 3}
    sorted_recs = sorted(recs, key=lambda x: (order.get(x['status'], 9), x['issue'] or ''))
    from itertools import groupby
    group_fill = {'有效': GREEN, '过期': ORANGE, '注销': RED, '其他': GRAY}
    group_fontc = {'有效': '006100', '过期': '9C6500', '注销': '9C0006', '其他': '595959'}
    label_txt = {'有效': '▶ 有效', '过期': '▶ 已过期', '注销': '▶ 已注销', '其他': '▶ 其他状态'}
    for st, grp in groupby(sorted_recs, key=lambda x: x['status']):
        glist = list(grp)
        merge_cell(ws, r, 1, 10, f'{label_txt.get(st, st)} —— {len(glist)} 条', fill=group_fill.get(st, GRAY),
                   font=Font(name='微软雅黑', size=10, bold=True, color=group_fontc.get(st, '262626')), align=LEFT)
        ws.row_dimensions[r].height = 22
        r += 1
        body = [[i + 1, x['no'], x['name'], x['model'], x['ver'], x['level'], x['type'], x['issue'], x['until'], x['status']]
                for i, x in enumerate(glist)]
        r = write_table(ws, r, GM_HEADERS, body, status_col=10, widths=CW, with_header=False)
    r += 1

    # 三、网专（列跨度占满10列）
    WZ_SPANS = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 7), (8, 9), (10, 10)]
    r = section(ws, r, f'三、网络安全专用产品检测（网专）—— 共 {wz_cnt[name]} 条', 10)
    if name == '中安云科':
        body = [[i + 1, x['no'], x['cat'], x['name'], (x['model'] + ' ' + x['ver']).strip(), x['org'], x['valid']]
                for i, x in enumerate(zayk_wz)]
    else:
        body = [[i + 1, x['no'], x['cat'], x['name'], (x['model'] + ' ' + x['ver']).strip(), x['org'], x['valid']]
                for i, x in enumerate([q for q in other.get(name, []) if q['src'] == '网专产品认证/检测'])]
    r = write_table(ws, r, ['序号', '编号', '产品类别', '产品名称', '型号/版本', '检测机构', '有效期'], body, widths=CW, spans=WZ_SPANS)
    r += 1

    # 四、IPv6（列跨度占满10列）
    IP_SPANS = [(1, 1), (2, 2), (3, 5), (6, 6), (7, 9), (10, 10)]
    r = section(ws, r, f'四、IPv6 Ready Logo 认证 —— 共 {ip_cnt[name]} 条', 10)
    if name == '中安云科':
        body = [[i + 1, x['logo_id'], x['product_name'], x['product_version'], x['test_spec'], x['applied_ts']]
                for i, x in enumerate(zayk.get('ipv6', []))]
    else:
        body = [[i + 1, x['no'], x['name'], x['ver'], x['date'], x['valid']]
                for i, x in enumerate([q for q in other.get(name, []) if q['src'] == 'IPv6 Ready Logo认证'])]
    r = write_table(ws, r, ['序号', 'Logo ID', '产品名称/型号', '版本', '测试规范/日期', '有效期'], body, widths=CW, spans=IP_SPANS)
    r += 1

    # 五、EPRI（0条时压成单行说明，不生成空表）
    hint = '（中安云科经官方检索无电科院检测记录）' if name == '中安云科' else ''
    ep_recs = [] if name == '中安云科' else [q for q in other.get(name, []) if q['src'] == '电科院EPRI检测报告']
    if ep_recs:
        r = section(ws, r, f'五、电科院（EPRI）检测报告 —— 共 {len(ep_recs)} 条', 10)
        body = [[i + 1, x['no'], x['name'], x['model'], x['date'], x['valid']]
                for i, x in enumerate(ep_recs)]
        r = write_table(ws, r, ['序号', '报告编号', '产品名称', '型号', '测试日期', '有效期'], body, widths=CW,
                        spans=[(1, 1), (2, 2), (3, 5), (6, 7), (8, 9), (10, 10)])
        r += 1
    elif ep_cnt[name] > 0:
        # 汇总表口径有条数但明细文件缺逐条记录——如实标注，不得展示为0
        merge_cell(ws, r, 1, 10, f'五、电科院（EPRI）检测报告 —— 共 {ep_cnt[name]} 条（来源：《2026重点企业资质认证汇总表》2026-07检索口径；逐条明细待补充，本表不拆分展示）',
                   fill=GRAY, font=BODY_FONT, align=LEFT)
        ws.row_dimensions[r].height = 22
        r += 2
    else:
        merge_cell(ws, r, 1, 10, f'五、电科院（EPRI）检测报告 —— 无记录 {hint}'.strip(), fill=GRAY, font=BODY_FONT, align=LEFT)
        ws.row_dimensions[r].height = 22
        r += 2

    # 六、国际认证（合并宽表；0条时压成单行说明）
    segs = [(1, 3, '认证体系'), (4, 7, '产品 / 范围'), (8, 10, '证书编号 / 说明 / 来源')]
    rows = []
    if name == '中安云科':
        rows.append(('ISO/IEC 19790 密码模块安全要求', 'PCI-E高性能国密密码卡', '全球首批（2023-10，与华为、纽创信安等同批）· 2026画册'))
    else:
        for x in [q for q in other.get(name, []) if q['src'] == 'FIPS认证' and fips_real(q)]:
            rows.append(('FIPS 140（美国联邦信息处理标准）', x['name'] + ' ' + x['model'], f"{x['no']} · {x['date']}"))
        if name == '三未信安':
            rows.append(('ISO/IEC 19790 密码模块安全要求', '密码产品', '第二批获证（2024-07）· 公开信息'))
    if not rows:
        merge_cell(ws, r, 1, 10, '六、国际认证（ISO/IEC 19790 / FIPS 140 等）—— 无记录', fill=GRAY, font=BODY_FONT, align=LEFT)
        ws.row_dimensions[r].height = 22
    else:
        r = section(ws, r, '六、国际认证（ISO/IEC 19790 / FIPS 140 等）', 10)
        r = write_merged_table(ws, r, segs, ['认证体系', '产品/范围', '说明/来源'], rows)

    ws.freeze_panes = 'A3'
    return ws

# ============ 资质排行榜 Sheet（区分统计口径，不区分方向） ============
def build_rank_sheet():
    ws = wb.create_sheet('资质排行榜')
    ws.sheet_view.showGridLines = False
    RW = [8, 22, 46, 15]
    for i, w in enumerate(RW, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    NW2 = 4
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NW2)
    ws.cell(row=1, column=1, value='企业资质排行榜（区分统计口径 · 不区分方向）').font = TITLE_FONT
    ws.row_dimensions[1].height = 32
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NW2)
    ws.cell(row=2, column=1, value=(
        '口径声明：①国密【有效证书】榜仅收录已逐条核验的11家（10家竞品官网明细 + 中安云科用户确认口径），'
        f'基准快照2026-09-07官方实查{REFRESH_NOTE}；其余152家重点企业有效数未核验，不参与该榜、绝不按零处理。'
        '②网专/IPv6/EPRI/FIPS为《2026重点企业资质认证汇总表》2026-07检索记录数口径（该类认证无状态概念）。'
        '③国密【历史总量】榜为总数口径（含有效/过期/注销），快照2026-07汇总表 + 中安云科2026-09实查，仅供历史规模参考，不代表有效能力。'
        '渔翁信息与渔翁云为同一主体已合并；同一企业跨方向重复行已按全称去重、各维度取最大值；前十名标黄、浅黄行=中安云科。江南科友数据源：' + jnkf_src)).font = SUB_FONT
    ws.row_dimensions[2].height = 76

    def norm(x):
        nm = x['short']
        if '渔翁' in nm: return '渔翁信息'
        if '数字认证' in nm: return '北京CA'  # 与对比总览简称统一
        return nm

    # ---------- A. 国密有效证书排行榜（仅已核验11家，缺数据企业不进榜、不作零） ----------
    valid_rows = [{'short': '中安云科', 'full': full_names['中安云科'],
                   'v': sum(1 for r_ in zayk['gm'] if r_['status'] == '有效'),
                   't': len(zayk['gm'])}]
    for c in companies[1:]:
        recs = gm[c]
        valid_rows.append({'short': c, 'full': full_names[c],
                           'v': sum(1 for r_ in recs if r_['status'] == '有效'),
                           't': len(recs)})
    valid_rows.sort(key=lambda e: -e['v'])

    # ---------- B/C. 汇总表口径（163家总量，各维度取跨方向最大值） ----------
    merged = {}
    for x in summary_all:
        key = (x['full'] or '').strip() or norm(x)
        if key not in merged:
            merged[key] = {'short': norm(x), 'full': key, 'gm': 0, 'wz': 0, 'ipv6': 0, 'epri': 0, 'fips': 0}
        e = merged[key]
        e['short'] = norm(x)
        for dim in ('gm', 'wz', 'ipv6', 'epri', 'fips'):
            e[dim] = max(e[dim], x[dim])
    total_rows = list(merged.values())
    total_rows.append({'short': '中安云科', 'full': full_names['中安云科'], 'gm': len(zayk['gm']),
                       'wz': len(zayk_wz), 'ipv6': len(zayk.get('ipv6', [])), 'epri': 0, 'fips': 0})

    def render_block(r, title, rows, dim_key, unit, top_n=50, zayk_zero_confirmed=False):
        lst = sorted(rows, key=lambda e: -e[dim_key])
        lst = [e for e in lst if e[dim_key] > 0]
        top = lst[:top_n]
        n_on = len(lst)
        zayk_in = next((e for e in top if e['short'] == '中安云科'), None)  # 修复：检查top而非lst，防止静默消失
        cap_txt = f'前{top_n}名（全榜共{n_on}家）' if n_on > top_n else f'全榜共{n_on}家'
        r = section(ws, r, f'{title}  {cap_txt}', NW2)
        for j, h in enumerate(['排名', '企业简称', '企业全称', f'数量（{unit}）'], 1):
            ws.cell(row=r, column=j, value=h)
        style_header(ws, r, NW2)
        r += 1
        prev_v, prev_rank = None, 0
        for k, e in enumerate(top):
            rank = prev_rank if e[dim_key] == prev_v else k + 1
            prev_v, prev_rank = e[dim_key], rank
            is_zayk = e['short'] == '中安云科'
            top10 = k < 10
            for j, v in enumerate([rank, e['short'], e['full'], e[dim_key]], 1):
                cell = ws.cell(row=r, column=j, value=v)
                cell.border = BORDER
                cell.font = BODY_FONT
                cell.alignment = LEFT if j == 3 else CENTER_NW
                if top10:
                    cell.fill = PatternFill('solid', fgColor='FFE699')
                    cell.font = Font(name='微软雅黑', size=10, bold=True, color='7F6000')
                elif is_zayk:
                    cell.fill = ANCHOR_FILL
                    cell.font = Font(name='微软雅黑', size=10, bold=True, color='7F6000')
                elif k % 2 == 1:
                    cell.fill = ZEBRA
            ws.row_dimensions[r].height = 20
            r += 1
        # 中安云科说明行
        if not zayk_in:
            zk_pos = next((i + 1 for i, e in enumerate(lst) if e['short'] == '中安云科'), None)
            if zk_pos:
                zk_v = next(e[dim_key] for e in lst if e['short'] == '中安云科')
                msg = f'…  中安云科以{zk_v}{unit}位列全榜第 {zk_pos} 名，未进入前{top_n}'
                merge_cell(ws, r, 1, NW2, msg, fill=ANCHOR_FILL,
                           font=Font(name='微软雅黑', size=10, bold=True, color='7F6000'), align=LEFT)
            elif zayk_zero_confirmed:
                msg = '注：中安云科该项经用户确认无记录（0条），未列入本榜'
                merge_cell(ws, r, 1, NW2, msg, fill=ANCHOR_FILL,
                           font=Font(name='微软雅黑', size=10, bold=True, color='7F6000'), align=LEFT)
            else:
                msg = '注：中安云科该项无已核验记录（未核验≠0），未列入本榜'
                merge_cell(ws, r, 1, NW2, msg, fill=GRAY,
                           font=Font(name='微软雅黑', size=10, color='595959'), align=LEFT)
            ws.row_dimensions[r].height = 22
            r += 1
        return r

    CN = ['一', '二', '三', '四', '五', '六']
    r = spacer(ws, 3, 6)
    r = render_block(r, f'{CN[0]}、商用密码认证（国密）有效证书 · 已核验11家（基准快照2026-09-07{REFRESH_NOTE}）',
                     valid_rows, 'v', '条', top_n=50)
    r = spacer(ws, r, 12)
    for di, (dim, label, unit) in enumerate(
            [('wz', f'{CN[1]}、网络安全专用产品检测（网专）· 汇总表2026-07记录数口径', '项'),
             ('ipv6', f'{CN[2]}、IPv6 Ready Logo 认证 · 记录数口径', '项'),
             ('epri', f'{CN[3]}、电科院（EPRI）检测报告 · 记录数口径', '份'),
             ('fips', f'{CN[4]}、FIPS 认证 · 记录数口径', '项')]):
        r = render_block(r, label, total_rows, dim, unit, top_n=50,
                         zayk_zero_confirmed=(dim == 'epri'))  # EPRI经用户确认0条
        r = spacer(ws, r, 12)
    r = render_block(r, f'{CN[5]}、商用密码认证（国密）历史证书总量（含有效/过期/注销 · 总数口径仅供规模参考）',
                     total_rows, 'gm', '条', top_n=50)
    ws.freeze_panes = 'A3'
    return ws

for c in companies:
    build_company_sheet(c)

build_rank_sheet()
wb.move_sheet('资质排行榜', offset=-(len(wb.sheetnames) - 2))

wb.save(OUT)
print('saved:', OUT)
print('sheets:', wb.sheetnames)
