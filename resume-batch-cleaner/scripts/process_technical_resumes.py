#!/usr/bin/env python3
"""Analyze, score, rename, and package technical resumes without touching sources.

The script deliberately separates deterministic extraction from human review. It
never deletes or moves an input file. Ambiguous education, role, name, or text
extraction is routed to review instead of being silently accepted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".jpeg", ".png"}
SKIP_DIRS = {"_resume_batch_cleaner_report", "check", "output", "tmp", "temp"}

JUNIOR_COLLEGE_PATTERNS = [
    r"(?<!本)专科(?!专病)", r"(?<![十大])大专(?!利)", r"高职(?!级)", r"高等职业",
    r"大学专科", r"专科学历",
    r"associate\s+degree", r"junior\s+college", r"higher\s+vocational",
]
UPGRADE_PATTERNS = [
    r"专升本", r"专接本", r"专插本", r"专转本", r"高起本",
    r"associate\s+to\s+bachelor", r"junior\s+college\s+to\s+bachelor",
    r"college\s+to\s+bachelor",
]
AMBIGUOUS_EDUCATION_PATTERNS = [
    r"成人本科", r"成人教育", r"自考本科", r"函授本科", r"网络教育本科",
    r"开放大学本科", r"学历提升",
]

TECH_EXCLUDE = [
    r"法务", r"律师", r"营销", r"市场", r"销售", r"运营", r"财务", r"投研",
    r"投资", r"商务", r"(?:^|\W)BD(?:\W|$)", r"产品", r"产品经理", r"产品负责人", r"产品运营",
    r"项目经理", r"交付经理", r"解决方案", r"客户体验", r"关系维护", r"设计师",
    r"策划", r"选品", r"人力", r"招聘", r"HR", r"CMO", r"Marketing",
]
TECH_INCLUDE = [
    r"工程师", r"研发", r"开发", r"算法", r"研究员", r"架构", r"技术负责人",
    r"全栈", r"前端", r"后端", r"服务端", r"客户端", r"测试开发", r"测试工程",
    r"SRE", r"DevOps", r"运维", r"信息安全", r"网络安全", r"数据开发",
    r"数据工程", r"BSP", r"Linux", r"驱动", r"嵌入式", r"SoC", r"芯片",
    r"机器人", r"仿真", r"推理框架", r"量化实现", r"Machine Learning",
    r"LLM应用", r"模型训练", r"后训练", r"模型对齐", r"材料工程", r"结构工程",
]

ROLE_SCARCITY = [
    (20, [r"具身", r"机器人算法", r"推理框架", r"大模型后训练", r"多模态对齐"]),
    (19, [r"Agent系统", r"Agent开发", r"LLM应用", r"模型训练", r"推荐算法"]),
    (18, [r"BSP", r"Linux驱动", r"SoC", r"芯片", r"嵌入式", r"信息安全"]),
    (17, [r"架构", r"SRE", r"DevOps", r"数据工程", r"数据开发"]),
    (15, [r"全栈", r"后端", r"服务端", r"Golang", r"Java", r"Python"]),
    (13, [r"测试开发", r"前端", r"结构工程", r"材料工程"]),
    (10, [r"工程师", r"研发", r"开发"]),
]

SCHOOL_TIER_10 = {
    "清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学", "中国科学技术大学",
    "南京大学", "哈尔滨工业大学", "西安交通大学", "中国科学院大学",
    "Massachusetts Institute of Technology", "Stanford University", "Harvard University",
    "University of Cambridge", "University of Oxford", "Carnegie Mellon University",
}
SCHOOL_TIER_9 = {
    "北京航空航天大学", "北京理工大学", "中国人民大学", "同济大学", "武汉大学",
    "华中科技大学", "东南大学", "中山大学", "南开大学", "天津大学", "北京师范大学",
    "华东师范大学", "厦门大学", "国防科技大学", "电子科技大学", "西北工业大学",
    "大连理工大学", "华南理工大学", "四川大学", "重庆大学", "山东大学", "中南大学",
}
SCHOOL_TIER_8 = {
    "北京邮电大学", "西安电子科技大学", "北京交通大学", "北京科技大学", "南京航空航天大学",
    "南京理工大学", "哈尔滨工程大学", "华东理工大学", "北京工业大学", "武汉理工大学",
    "暨南大学", "苏州大学", "上海大学", "河海大学", "合肥工业大学", "中国农业大学",
    "中央财经大学", "对外经济贸易大学", "上海财经大学", "中国政法大学",
}

PLATFORM_TIER_10 = [
    "字节跳动", "腾讯", "阿里巴巴", "华为", "百度", "Google", "Microsoft", "Amazon",
    "Meta", "Apple", "NVIDIA", "OpenAI", "DeepMind",
]
PLATFORM_TIER_9 = [
    "美团", "京东", "小米", "滴滴", "快手", "蚂蚁", "大疆", "网易", "拼多多",
    "商汤", "旷视", "科大讯飞", "携程", "去哪儿", "理想汽车", "蔚来", "小鹏",
    "比亚迪", "中兴", "OPPO", "vivo", "Shopee", "TikTok",
]
PLATFORM_TIER_8 = [
    "新浪", "搜狐", "B站", "哔哩哔哩", "知乎", "小红书", "得物", "携程", "360",
    "联想", "海康威视", "顺丰", "贝壳", "同程", "哈啰", "Boss直聘", "货拉拉",
]

DOMAIN_PATTERNS = {
    "llm_agent": [r"LLM", r"大模型", r"Agent", r"RAG", r"LangChain", r"LangGraph"],
    "ml_algo": [r"机器学习", r"深度学习", r"算法", r"推荐", r"NLP", r"CV", r"多模态"],
    "backend": [r"Java", r"Golang", r"Go\b", r"Python", r"后端", r"服务端", r"Spring"],
    "frontend": [r"前端", r"React", r"Vue", r"TypeScript", r"WebGL"],
    "data": [r"数据仓库", r"数据湖", r"Flink", r"Spark", r"Kafka", r"ETL", r"数据开发"],
    "infra": [r"Kubernetes", r"K8s", r"Docker", r"SRE", r"DevOps", r"云原生", r"分布式"],
    "database": [r"MySQL", r"PostgreSQL", r"Redis", r"ElasticSearch", r"数据库"],
    "security": [r"安全", r"风控", r"漏洞", r"加密", r"零信任"],
    "embedded": [r"嵌入式", r"BSP", r"Linux驱动", r"SoC", r"MCU", r"RTOS"],
    "robotics": [r"机器人", r"具身", r"仿真", r"SLAM", r"ROS", r"运动控制"],
    "testing": [r"测试开发", r"自动化测试", r"性能测试", r"质量平台"],
    "hardware": [r"硬件", r"电路", r"PCB", r"结构设计", r"材料工程"],
}

TECH_BODY_TITLES = [
    r"软件工程师", r"研发工程师", r"开发工程师", r"算法工程师", r"测试开发工程师",
    r"测试工程师", r"前端工程师", r"后端工程师", r"服务端工程师", r"数据工程师",
    r"数据开发", r"机器学习工程师", r"Machine Learning Engineer", r"Software Engineer",
    r"Research Engineer", r"SRE", r"DevOps", r"架构师", r"技术负责人", r"程序员",
    r"嵌入式", r"驱动工程师", r"BSP", r"结构工程师", r"材料工程师", r"研发负责人",
]
NONTECH_BODY_TITLES = [
    r"产品经理", r"产品负责人", r"运营经理", r"内容运营", r"用户运营", r"市场经理",
    r"营销", r"销售", r"财务", r"审计", r"法务", r"律师", r"投资经理", r"投研",
    r"战略分析", r"咨询顾问", r"客户经理", r"商务拓展", r"(?:^|\W)BD(?:\W|$)",
    r"项目经理", r"交付经理", r"设计师", r"人力资源", r"招聘",
]
TECH_STACK_SIGNALS = [
    r"Java", r"Python", r"Golang", r"\bGo\b", r"C\+\+", r"Rust", r"JavaScript",
    r"TypeScript", r"React", r"Vue", r"Spring", r"Django", r"FastAPI", r"PyTorch",
    r"TensorFlow", r"LangChain", r"LangGraph", r"RAG", r"Linux", r"Kubernetes", r"K8s",
    r"Docker", r"MySQL", r"PostgreSQL", r"Redis", r"Kafka", r"Flink", r"Spark",
    r"RPC", r"微服务", r"分布式", r"数据库", r"数据仓库", r"云原生", r"GitHub",
    r"SolidWorks", r"AutoCAD", r"CATIA", r"CAE", r"有限元", r"材料分析", r"结构设计",
    r"ROS", r"SLAM", r"MCU", r"RTOS", r"PCB", r"芯片", r"嵌入式", r"仿真",
]

COMMON_SURNAMES = set(
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯管卢莫房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉龚程嵇邢裴陆荣翁荀羊惠甄曲封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍桑桂濮牛寿通边扈燕冀浦尚农温别庄晏柴瞿阎充慕连茹习艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷辛阚那简饶空曾沙养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公"
)
COMMON_SURNAMES.update({"帅", "敖", "佟", "朴", "党", "区"})
COMPOUND_SURNAMES = {
    "欧阳", "太史", "端木", "上官", "司马", "东方", "独孤", "南宫", "万俟", "闻人",
    "夏侯", "诸葛", "尉迟", "公羊", "赫连", "澹台", "皇甫", "宗政", "濮阳", "公冶",
    "申屠", "公孙", "慕容", "仲孙", "钟离", "长孙", "宇文", "司徒", "鲜于", "司空",
}


@dataclass
class Candidate:
    source_path: str
    source_batch: str
    extension: str
    file_size: int
    sha256: str
    filename_role: str = ""
    filename_alias: str = ""
    stated_work_years: int | None = None
    extraction_status: str = ""
    text_chars: int = 0
    name: str = ""
    name_source: str = ""
    name_confidence: str = ""
    expected_location: str = "未提及"
    location_evidence: str = ""
    education_excerpt: str = ""
    schools: list[str] = field(default_factory=list)
    junior_college_evidence: str = ""
    upgrade_evidence: str = ""
    private_bachelor_evidence: str = ""
    education_review_reason: str = ""
    role_decision: str = "review"
    role_reason: str = ""
    education_decision: str = "review"
    final_decision: str = "review"
    duplicate_of: str = ""
    school_score: int = 0
    platform_score: int = 0
    career_stage_score: int = 0
    scarcity_score: int = 0
    depth_score: int = 0
    breadth_score: int = 0
    project_score: int = 0
    stability_score: int = 0
    total_score: int = 0
    score_notes: str = ""
    score_override_reason: str = ""
    text: str = ""


def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\x00", "")
    return re.sub(r"[ \t]+", " ", value)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_pdf(path: Path) -> str:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_docx(path: Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not (name.startswith("word/") and name.endswith(".xml")):
                continue
            try:
                root = ElementTree.fromstring(archive.read(name))
            except ElementTree.ParseError:
                continue
            paragraph_parts: list[str] = []
            for node in root.iter():
                tag = node.tag.rsplit("}", 1)[-1]
                if tag in {"t", "tab"} and node.text:
                    paragraph_parts.append(node.text)
                elif tag in {"p", "br", "tr"} and paragraph_parts:
                    parts.append("".join(paragraph_parts))
                    paragraph_parts = []
            if paragraph_parts:
                parts.append("".join(paragraph_parts))
    return "\n".join(parts)


def extract_doc_with_word(path: Path) -> str:
    """Use an isolated PowerShell/Word COM process only for legacy .doc files."""
    escaped = str(path).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; $w=New-Object -ComObject Word.Application; "
        "$w.Visible=$false; try { $d=$w.Documents.Open('" + escaped +
        "',$false,$true); $t=$d.Content.Text; $d.Close($false); [Console]::OutputEncoding="
        "[System.Text.Encoding]::UTF8; Write-Output $t } finally { $w.Quit() }"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        timeout=35,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace")[:300])
    return completed.stdout.decode("utf-8", errors="replace")


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            text = extract_pdf(path)
        elif suffix == ".docx":
            text = extract_docx(path)
        elif suffix == ".doc":
            text = extract_doc_with_word(path)
        elif suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
        elif suffix in {".jpg", ".jpeg", ".png"}:
            return "", "image requires visual/OCR review"
        else:
            return "", f"unsupported suffix: {suffix}"
    except Exception as exc:
        return "", f"extract failed: {exc}"
    text = norm_text(text).strip()
    if len(text) < 80:
        return text, f"insufficient extracted text: {len(text)} chars"
    return text, "ok"


def parse_filename(path: Path) -> tuple[str, str, int | None]:
    stem = re.sub(r" \(\d+\)$", "", path.stem)
    match = re.match(r"^(.*)-(.+)-工作(\d+)年-【脉脉招聘】$", stem, flags=re.I)
    if match:
        return match.group(1).strip(), match.group(2).strip(), int(match.group(3))
    match = re.match(r"^(.+)-在线简历$", stem, flags=re.I)
    if match:
        return "在线简历", match.group(1).strip(), None
    match = re.match(r"^(.*)-(.+)【脉脉招聘】$", stem, flags=re.I)
    if match:
        return match.group(1).strip(), match.group(2).strip(), None
    return "", stem, None


def plausible_chinese_name(token: str) -> bool:
    token = token.strip().replace(" ", "")
    if not re.fullmatch(r"[\u4e00-\u9fff·]{2,5}", token):
        return False
    return token[:2] in COMPOUND_SURNAMES or token[0] in COMMON_SURNAMES


def first_line_name(text: str, alias: str) -> tuple[str, str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    head = "\n".join(lines[:25])
    labelled = re.search(
        r"(?:姓\s*名|Name)\s*[:：]?\s*([A-Za-z][A-Za-z .·'-]{1,35}|[\u4e00-\u9fff·]{2,5})",
        head,
        re.I,
    )
    if labelled:
        return labelled.group(1).strip(), "resume label", "high"
    for first in lines[:8]:
        first = re.sub(r"^[\s\d.·•📄]+", "", first).strip()
        separated = re.match(
            r"^([\u4e00-\u9fff·]{2,5}|[A-Za-z][A-Za-z .·'-]{1,35})(?:\s{1,}|\||｜|,|，)",
            first,
        )
        if separated:
            token = separated.group(1).strip()
            if plausible_chinese_name(token) or re.fullmatch(r"[A-Za-z][A-Za-z .·'-]{1,35}", token):
                return token, "resume first line", "high"
    alias_clean = alias.strip()
    if lines:
        first = re.sub(r"^[\s\d.·•📄]+", "", lines[0]).strip()
        compact = first.replace(" ", "")
        titled = re.match(
            r"^([\u4e00-\u9fff·]{2,5})(?=技术专家|工程师|架构师|研发|开发|求职|男|女|电话|手机|邮箱|简历)",
            compact,
        )
        if titled and plausible_chinese_name(titled.group(1)):
            return titled.group(1), "resume first-line title boundary", "high"
        if len(compact) >= 3 and compact[:2] in COMPOUND_SURNAMES:
            return compact[:4], "resume first-line surname heuristic", "medium"
        if len(compact) >= 3 and compact[0] in COMMON_SURNAMES and re.match(r"^[\u4e00-\u9fff]{3}", compact):
            return compact[:3], "resume first-line surname heuristic", "medium"
        if len(compact) >= 2 and compact[0] in COMMON_SURNAMES and re.match(r"^[\u4e00-\u9fff]{2}", compact):
            return compact[:2], "resume first-line surname heuristic", "low"
    if alias_clean and len(alias_clean) <= 30:
        alias_match = re.search(re.escape(alias_clean), head, re.I)
        if alias_match and alias_match.start() < 100:
            return alias_clean, "resume header matches filename alias", "high"
    return alias_clean or "姓名未识别", "filename fallback", "low"


def clean_location(raw: str) -> str:
    raw = re.split(r"(?:期望|求职|薪资|行业|职能|岗位|状态|到岗|工作经验|\n)", raw)[0]
    raw = re.sub(r"[|｜;；/\\]+", "、", raw)
    raw = re.sub(r"\s+", "", raw).strip("：:，,。.;；、")
    raw = re.sub(r"[<>:\"/\\|?*]", "", raw)
    return raw[:30] if 1 < len(raw) <= 30 else "未提及"


def extract_location(text: str) -> tuple[str, str]:
    patterns = [
        r"(?:期望工作城市|期望城市|期望工作地点|期望地点|意向城市|意向地点)\s*[:：]?\s*([^\n]{2,50})",
        r"求职意向[^\n]{0,80}?(?:城市|地点)\s*[:：]?\s*([^\n]{2,50})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            location = clean_location(match.group(1))
            if location != "未提及":
                return location, match.group(0)[:100]
    return "未提及", ""


def education_excerpt(text: str) -> str:
    headers = list(re.finditer(r"(?:教育背景|教育经历|学历背景|Education)", text, re.I))
    pieces: list[str] = []
    for header in headers[:3]:
        tail = text[header.start(): header.start() + 6000]
        stop = re.search(
            r"\n(?:工作经历|职业经历|项目经验|专业技能|技能专长|核心优势|自我评价|Work Experience|Projects)\b",
            tail[20:], re.I,
        )
        pieces.append(tail[: (stop.start() + 20 if stop else 3500)])
    if pieces:
        return "\n".join(pieces)[:8000]
    lines = text.splitlines()
    hits: list[str] = []
    for index, line in enumerate(lines):
        if re.search(r"大学|学院|本科|硕士|博士|学士|专科|大专|高职", line, re.I):
            hits.extend(lines[max(0, index - 1): min(len(lines), index + 2)])
    return "\n".join(dict.fromkeys(hits))[:6000]


def evidence_for(patterns: Iterable[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 80)
            return re.sub(r"\s+", " ", text[start:end]).strip()
    return ""


def load_institutions(path: Path | None) -> list[dict[str, str]]:
    if not path:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def find_schools(section: str, institutions: list[dict[str, str]]) -> list[str]:
    compact = re.sub(r"\s+", "", section)
    found = [
        row["school_name"]
        for row in institutions
        if row.get("school_name") and re.sub(r"\s+", "", row["school_name"]) in compact
    ]
    return sorted(set(found), key=lambda value: section.find(value))


def classify_education(candidate: Candidate, institutions: list[dict[str, str]]) -> None:
    section = candidate.education_excerpt
    compact_section = re.sub(r"\s+", "", section)
    candidate.junior_college_evidence = evidence_for(JUNIOR_COLLEGE_PATTERNS, section)
    candidate.upgrade_evidence = evidence_for(UPGRADE_PATTERNS, section)
    if candidate.junior_college_evidence or candidate.upgrade_evidence:
        candidate.education_decision = "exclude"
        return

    row_by_name = {row.get("school_name", ""): row for row in institutions}
    private_hits: list[str] = []
    junior_school_hits: list[str] = []
    for school in candidate.schools:
        row = row_by_name.get(school, {})
        level = row.get("level", "")
        private = row.get("private", "").lower() in {"1", "true", "yes", "民办"}
        compact_school = re.sub(r"\s+", "", school)
        school_pos = compact_section.find(compact_school)
        window = compact_section[max(0, school_pos - 100): school_pos + len(compact_school) + 180]
        if "专科" in level:
            junior_school_hits.append(f"{school}（教育部名单办学层次：{level}）")
        if private:
            if re.search(r"本科|学士|Bachelor", window, re.I):
                private_hits.append(f"{school}（教育部名单备注：民办；本科教育窗口：{window[:160]}）")
            else:
                candidate.education_review_reason = f"教育经历含民办本科院校名称但学段不够明确：{school}"
    if junior_school_hits:
        candidate.junior_college_evidence = "；".join(junior_school_hits)
        candidate.education_decision = "exclude"
        return
    if private_hits:
        candidate.private_bachelor_evidence = "；".join(private_hits)
        candidate.education_decision = "exclude"
        return

    ambiguous = evidence_for(AMBIGUOUS_EDUCATION_PATTERNS, section)
    if ambiguous:
        candidate.education_review_reason = f"非全日制/继续教育信号待核：{ambiguous}"
        candidate.education_decision = "review"
        return
    if candidate.education_review_reason:
        candidate.education_decision = "review"
        return
    if not candidate.schools:
        candidate.education_review_reason = "教育院校未能映射到教育部普通高校名单，需核验海外/历史校名及办学性质"
        candidate.education_decision = "review"
        return
    if not section or len(section) < 30:
        candidate.education_review_reason = "未可靠提取教育经历"
        candidate.education_decision = "review"
        return
    candidate.education_decision = "pass"


def classify_role(candidate: Candidate) -> None:
    # The source filename is the requisition/job bucket and therefore takes
    # precedence over incidental words in the resume body. For example, a
    # backend engineer may mention working with product or operations teams.
    role = candidate.filename_role.strip()
    body = candidate.text[:30000]
    header = candidate.text[:1200]
    tech_title_hits = sum(len(re.findall(pattern, body, re.I)) for pattern in TECH_BODY_TITLES)
    nontech_title_hits = sum(len(re.findall(pattern, body, re.I)) for pattern in NONTECH_BODY_TITLES)
    stack_hits = sum(1 for pattern in TECH_STACK_SIGNALS if re.search(pattern, body, re.I))
    header_nontech = evidence_for(NONTECH_BODY_TITLES, header)
    actual_technical = (
        tech_title_hits >= 2
        or (tech_title_hits >= 1 and stack_hits >= 3)
        or stack_hits >= 8
    )
    actual_nontechnical = (
        (header_nontech and tech_title_hits == 0 and stack_hits < 6)
        or (nontech_title_hits >= 2 and tech_title_hits == 0 and stack_hits < 5)
    )
    if role and role != "在线简历":
        excluded = evidence_for(TECH_EXCLUDE, role)
        explicit_hands_on = evidence_for(
            [
                r"工程师", r"研发", r"开发", r"算法", r"研究员", r"架构师?", r"技术负责人",
                r"全栈", r"前端", r"后端", r"服务端", r"客户端", r"SRE", r"DevOps",
                r"BSP", r"Linux驱动", r"嵌入式", r"SoC", r"芯片", r"量化实现",
                r"Machine Learning Engineer", r"模型训练", r"后训练",
            ],
            role,
        )
        if excluded and not explicit_hands_on:
            candidate.role_decision = "exclude"
            candidate.role_reason = f"岗位标题含非技术信号：{excluded}"
        elif explicit_hands_on and actual_nontechnical:
            candidate.role_decision = "exclude"
            candidate.role_reason = (
                "技术职位目录中混入非技术履历："
                f"技术任职命中{tech_title_hits}、技术栈命中{stack_hits}、非技术任职命中{nontech_title_hits}；"
                f"抬头证据：{header_nontech}"
            )
        elif explicit_hands_on and (
            actual_technical or (stack_hits >= 4 and nontech_title_hits <= 1)
        ):
            candidate.role_decision = "keep"
            candidate.role_reason = (
                f"岗位标题含技术实操信号：{explicit_hands_on}；"
                f"正文技术任职命中{tech_title_hits}、技术栈命中{stack_hits}"
            )
        elif explicit_hands_on:
            candidate.role_decision = "review"
            candidate.role_reason = (
                f"岗位标题像技术岗，但正文技术证据不足：技术任职命中{tech_title_hits}、"
                f"技术栈命中{stack_hits}、非技术任职命中{nontech_title_hits}"
            )
        else:
            candidate.role_decision = "review"
            candidate.role_reason = "岗位标题的技术属性不明确"
        return

    excluded = evidence_for(TECH_EXCLUDE, header)
    included = evidence_for(TECH_INCLUDE, header)
    if actual_nontechnical or excluded:
        candidate.role_decision = "exclude"
        candidate.role_reason = f"简历抬头/正文含非技术岗信号：{header_nontech or excluded}"
    elif actual_technical and included:
        candidate.role_decision = "keep"
        candidate.role_reason = (
            f"简历抬头含技术岗信号：{included}；"
            f"正文技术任职命中{tech_title_hits}、技术栈命中{stack_hits}"
        )
    else:
        candidate.role_decision = "review"
        candidate.role_reason = "岗位信息不足或技术属性不明确"


def score_school(section: str, schools: list[str]) -> int:
    combined = section + "\n" + "\n".join(schools)
    if any(name.lower() in combined.lower() for name in SCHOOL_TIER_10):
        return 10
    if any(name in combined for name in SCHOOL_TIER_9):
        return 9
    if any(name in combined for name in SCHOOL_TIER_8):
        return 8
    if re.search(r"985|世界排名.{0,8}(?:前?50|Top\s*50)", combined, re.I):
        return 9
    if re.search(r"211|双一流|世界排名.{0,8}(?:前?100|Top\s*100)", combined, re.I):
        return 8
    if schools:
        return 5
    if re.search(r"University|大学|学院", combined, re.I):
        return 5
    return 3


def score_platform(text: str) -> int:
    if any(name.lower() in text.lower() for name in PLATFORM_TIER_10):
        return 10
    if any(name.lower() in text.lower() for name in PLATFORM_TIER_9):
        return 9
    if any(name.lower() in text.lower() for name in PLATFORM_TIER_8):
        return 8
    company_lines = len(re.findall(r"\d{4}[./年-].{0,80}(?:公司|集团|科技|网络|智能|研究院)", text))
    return 6 if company_lines >= 2 else 4


def score_career(years: int | None) -> int:
    if years is None:
        return 2
    if 3 <= years <= 9:
        return 5
    if years in {2, 10, 11, 12}:
        return 4
    if years in {1, 13, 14, 15}:
        return 2
    if 16 <= years <= 20:
        return 1
    return 0


def score_scarcity(role: str, text: str) -> int:
    haystack = f"{role}\n{text[:2500]}"
    for score, patterns in ROLE_SCARCITY:
        if any(re.search(pattern, haystack, re.I) for pattern in patterns):
            return score
    return 8


def score_depth(text: str, years: int | None) -> int:
    years_value = years or 0
    score = 5 + min(7, int(years_value * 0.65))
    if re.search(r"负责人|技术专家|架构师|Tech Lead|Principal|首席|核心开发", text, re.I):
        score += 2
    if re.search(r"架构设计|底层原理|性能优化|高并发|高可用|分布式|编译器|推理框架", text, re.I):
        score += 2
    if re.search(r"从\s*0\s*[到→-]\s*1|主导|独立负责|owner|ownership", text, re.I):
        score += 2
    if re.search(r"专利|论文|顶会|开源|GitHub", text, re.I):
        score += 1
    return min(20, score)


def score_breadth(text: str) -> tuple[int, list[str]]:
    domains = [name for name, patterns in DOMAIN_PATTERNS.items() if any(re.search(p, text, re.I) for p in patterns)]
    return min(10, 2 + len(domains)), domains


def score_projects(text: str) -> int:
    score = 5
    metrics = re.findall(r"(?:\d+(?:\.\d+)?\s*(?:%|万|亿|k|w|QPS|TPS)|提升|降低|节省|增长|支撑)", text, re.I)
    score += min(7, len(metrics))
    if re.search(r"主导|负责人|owner|牵头|从\s*0\s*[到→-]\s*1", text, re.I):
        score += 3
    if re.search(r"核心系统|平台化|高并发|高可用|大规模|亿级|千万级|多机房|全球化", text, re.I):
        score += 3
    if re.search(r"落地|上线|商业化|生产环境|业务结果", text, re.I):
        score += 2
    return min(20, score)


def score_stability(text: str, years: int | None, extraction_ok: bool) -> int:
    if not extraction_ok:
        return 1
    spans = len(re.findall(r"(?:19|20)\d{2}[./年-]\d{1,2}.{0,8}(?:至今|(?:19|20)\d{2})", text))
    if years and years >= 4 and spans <= 3:
        return 5
    if years and spans > max(4, years // 2 + 1):
        return 2
    return 4 if years and years >= 2 else 3


def apply_scores(candidate: Candidate) -> None:
    candidate.school_score = score_school(candidate.education_excerpt, candidate.schools)
    candidate.platform_score = score_platform(candidate.text)
    candidate.career_stage_score = score_career(candidate.stated_work_years)
    candidate.scarcity_score = score_scarcity(candidate.filename_role, candidate.text)
    candidate.depth_score = score_depth(candidate.text, candidate.stated_work_years)
    candidate.breadth_score, domains = score_breadth(candidate.text)
    candidate.project_score = score_projects(candidate.text)
    candidate.stability_score = score_stability(
        candidate.text, candidate.stated_work_years, candidate.extraction_status == "ok"
    )
    candidate.total_score = sum(
        [
            candidate.school_score, candidate.platform_score, candidate.career_stage_score,
            candidate.scarcity_score, candidate.depth_score, candidate.breadth_score,
            candidate.project_score, candidate.stability_score,
        ]
    )
    candidate.score_notes = f"技术域：{','.join(domains) if domains else '未明确'}"


def iter_input_files(roots: list[Path]) -> Iterable[tuple[Path, str]]:
    for root in roots:
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"input directory not found: {root}")
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            relative_parts = {part.lower() for part in path.relative_to(root).parts[:-1]}
            if relative_parts.intersection(SKIP_DIRS):
                continue
            yield path, root.name


def load_overrides(path: Path | None) -> dict[str, dict[str, object]]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): dict(value) for key, value in data.items()}


def apply_override(candidate: Candidate, overrides: dict[str, dict[str, object]]) -> None:
    override = overrides.get(candidate.source_path) or overrides.get(candidate.sha256)
    if not override:
        return
    allowed = {
        "name", "name_confidence", "expected_location", "role_decision", "role_reason",
        "education_decision", "education_review_reason", "final_decision", "school_score",
        "platform_score", "career_stage_score", "scarcity_score", "depth_score",
        "breadth_score", "project_score", "stability_score", "score_override_reason",
    }
    for key, value in override.items():
        if key in allowed:
            setattr(candidate, key, value)
    candidate.total_score = sum(
        [
            candidate.school_score, candidate.platform_score, candidate.career_stage_score,
            candidate.scarcity_score, candidate.depth_score, candidate.breadth_score,
            candidate.project_score, candidate.stability_score,
        ]
    )


def decide(candidate: Candidate) -> None:
    if candidate.duplicate_of:
        candidate.final_decision = "duplicate"
    elif candidate.role_decision == "exclude" or candidate.education_decision == "exclude":
        candidate.final_decision = "exclude"
    elif candidate.extraction_status != "ok":
        candidate.final_decision = "review"
    elif candidate.role_decision == "keep" and candidate.education_decision == "pass":
        candidate.final_decision = "keep"
    else:
        candidate.final_decision = "review"


def mark_semantic_duplicates(candidates: list[Candidate]) -> None:
    """Mark repeated resumes by strong contact identifiers, preferring usable copies."""
    identifier_groups: dict[str, list[Candidate]] = {}
    for candidate in candidates:
        identifiers = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", candidate.text))
        identifiers.update(
            re.sub(r"\D", "", value)
            for value in re.findall(r"(?<!\d)(?:\+?86[- ]?)?1[3-9](?:[- ]?\d){9}(?!\d)", candidate.text)
        )
        for identifier in {value.lower() for value in identifiers if len(value) >= 8}:
            identifier_groups.setdefault(identifier, []).append(candidate)
    handled: set[int] = set()
    priority = {"keep": 3, "review": 2, "exclude": 1, "duplicate": 0}
    for group in identifier_groups.values():
        unique = list({id(candidate): candidate for candidate in group}.values())
        if len(unique) < 2:
            continue
        owner = max(
            unique,
            key=lambda item: (priority.get(item.final_decision, 0), item.text_chars, item.file_size),
        )
        for candidate in unique:
            if candidate is owner or id(candidate) in handled:
                continue
            candidate.duplicate_of = owner.source_path
            candidate.final_decision = "duplicate"
            handled.add(id(candidate))


def safe_component(value: str, fallback: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "", value).strip(" .")
    return value[:55] or fallback


def write_csv(path: Path, candidates: list[Candidate]) -> None:
    fields = [name for name in Candidate.__dataclass_fields__ if name not in {"text", "education_excerpt"}]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in candidates:
            row = asdict(candidate)
            row.pop("text", None)
            row.pop("education_excerpt", None)
            row["schools"] = "；".join(candidate.schools)
            writer.writerow({key: row.get(key, "") for key in fields})


def write_jsonl(path: Path, candidates: list[Candidate]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(asdict(candidate), ensure_ascii=False) + "\n")


def package_kept(output_dir: Path, candidates: list[Candidate]) -> tuple[Path, int]:
    kept = [candidate for candidate in candidates if candidate.final_decision == "keep"]
    kept.sort(
        key=lambda item: (
            -item.total_score,
            -(item.scarcity_score + item.depth_score),
            -item.project_score,
            -item.platform_score,
            -item.school_score,
            item.name,
        )
    )
    resume_dir = output_dir / "保留简历"
    resume_dir.mkdir(parents=True, exist_ok=True)
    width = max(3, len(str(len(kept))))
    manifest_rows: list[dict[str, object]] = []
    for index, candidate in enumerate(kept, start=1):
        source = Path(candidate.source_path)
        filename = (
            f"{index:0{width}d}-"
            f"{safe_component(candidate.name, '姓名未识别')}-"
            f"{safe_component(candidate.expected_location, '未提及')}"
            f"{source.suffix.lower()}"
        )
        target = resume_dir / filename
        shutil.copy2(source, target)
        manifest_rows.append(
            {
                "rank": index,
                "output_filename": filename,
                "name": candidate.name,
                "expected_location": candidate.expected_location,
                "total_score": candidate.total_score,
                "source_path": candidate.source_path,
                "sha256": candidate.sha256,
            }
        )
    manifest = output_dir / "package-manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]) if manifest_rows else ["rank"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    zip_path = output_dir / "技术岗候选人-筛选评分排序.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(resume_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output_dir))
        archive.write(manifest, manifest.name)
    return zip_path, len(kept)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, help="Input resume directory; repeatable")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--institution-csv", help="CSV with school_name, level, private columns")
    parser.add_argument("--overrides", help="Optional JSON mapping source path or sha256 to reviewed fields")
    parser.add_argument("--package", action="store_true", help="Copy final keep files and create zip")
    args = parser.parse_args()

    roots = [Path(value).expanduser().resolve() for value in args.input]
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    institutions = load_institutions(Path(args.institution_csv).resolve() if args.institution_csv else None)
    overrides = load_overrides(Path(args.overrides).resolve() if args.overrides else None)

    candidates: list[Candidate] = []
    hash_owner: dict[str, Candidate] = {}
    for path, batch in iter_input_files(roots):
        role, alias, years = parse_filename(path)
        digest = sha256_file(path)
        text, status = extract_text(path)
        candidate = Candidate(
            source_path=str(path), source_batch=batch, extension=path.suffix.lower(),
            file_size=path.stat().st_size, sha256=digest, filename_role=role,
            filename_alias=alias, stated_work_years=years, extraction_status=status,
            text_chars=len(text), text=text,
        )
        candidate.name, candidate.name_source, candidate.name_confidence = first_line_name(text, alias)
        candidate.expected_location, candidate.location_evidence = extract_location(text)
        candidate.education_excerpt = education_excerpt(text)
        candidate.schools = find_schools(candidate.education_excerpt, institutions)
        if digest in hash_owner:
            candidate.duplicate_of = hash_owner[digest].source_path
        else:
            hash_owner[digest] = candidate
        classify_role(candidate)
        classify_education(candidate, institutions)
        apply_scores(candidate)
        decide(candidate)
        apply_override(candidate, overrides)
        candidates.append(candidate)

    mark_semantic_duplicates(candidates)

    candidates.sort(key=lambda item: (item.source_batch, item.source_path))
    write_jsonl(output_dir / "analysis-full.jsonl", candidates)
    write_csv(output_dir / "analysis-summary.csv", candidates)
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.final_decision] = counts.get(candidate.final_decision, 0) + 1
    summary = {
        "inputs": [str(root) for root in roots],
        "total": len(candidates),
        "counts": counts,
        "institution_rows": len(institutions),
    }
    (output_dir / "analysis-run.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    if args.package:
        zip_path, kept = package_kept(output_dir, candidates)
        print(json.dumps({"package": str(zip_path), "kept": kept}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
