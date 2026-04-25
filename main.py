# =================================================================
# 👖 BLUE JEANS REVISE ENGINE
# main.py — Streamlit App (3-Stage Pipeline)
# =================================================================
# © 2026 BLUE JEANS PICTURES. All rights reserved.
#
# v1.0 (2026-04-21)
# Pipeline: DIAGNOSE → REVISE → VERIFY
# Models: Opus 4.6 (집필) / Sonnet 4.6 (분석)
# =================================================================

import os
import re
import json
import io
from datetime import datetime

import streamlit as st
import anthropic
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from prompt import (
    SYSTEM_PROMPT,
    GENRE_RULES,
    INTENSITY_RULES,
    build_diagnose_prompt,
    build_revise_prompt,
    build_verify_prompt,
    get_report_filename,
    get_period_keys_for_ui,
    get_period_labels_for_ui,
    parse_rewrite_engine_json,
)

# =================================================================
# [0] 모델 설정 & 페이지 설정
# =================================================================
MODEL_WRITE   = "claude-opus-4-6"      # Stage 2: 실제 집필
MODEL_ANALYZE = "claude-sonnet-4-6"    # Stage 1 & 3: 분석

st.set_page_config(
    page_title="BLUE JEANS · Revise Engine",
    page_icon="👖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =================================================================
# [1] 디자인 시스템 (Writer/Rewrite Engine과 동일 톤)
# =================================================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@latest/Paperlogy.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap');

:root {
    --navy: #191970; --y: #FFCB05; --bg: #F7F7F5;
    --card: #FFFFFF; --card-border: #E2E2E0; --t: #1A1A2E;
    --g: #2EC484; --r: #E14444; --dim: #8E8E99; --light-bg: #EEEEF6;
    --serif: 'Paperlogy', 'Noto Serif KR', 'Georgia', serif;
    --display: 'Playfair Display', 'Paperlogy', 'Georgia', serif;
    --body: 'Pretendard', -apple-system, sans-serif;
    --heading: 'Paperlogy', 'Pretendard', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--body); color: var(--t); -webkit-font-smoothing: antialiased;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"], [data-testid="stHeader"],
[data-testid="stBottom"] {
    background-color: var(--bg) !important; color: var(--t) !important;
}
.stMarkdown, .stText, .stCode { color: var(--t) !important; }
h1, h2, h3, h4, h5, h6 { color: var(--navy) !important; font-family: var(--heading) !important; }
p, span, label, div, li { color: inherit; }
section[data-testid="stSidebar"] { display: none; }

.stTextInput input, .stTextArea textarea,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background-color: var(--card) !important; color: var(--t) !important;
    border: 1.5px solid var(--card-border) !important; border-radius: 8px !important;
    font-family: var(--body) !important; font-size: 0.92rem !important;
    padding: 0.65rem 0.85rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 2px rgba(25,25,112,0.08) !important;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: var(--card) !important; color: var(--t) !important;
    border: 1.5px solid var(--card-border) !important; border-radius: 8px !important;
}

.stButton > button {
    background-color: var(--navy) !important; color: #FFFFFF !important;
    border: none !important; border-radius: 8px !important;
    font-family: var(--heading) !important; font-weight: 700 !important;
    padding: 0.7rem 1.4rem !important; letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background-color: var(--y) !important; color: var(--navy) !important;
    transform: translateY(-1px);
}

[data-testid="stDownloadButton"] button {
    background-color: var(--y) !important; color: var(--navy) !important;
    border: none !important; border-radius: 8px !important;
    font-family: var(--heading) !important; font-weight: 800 !important;
    padding: 0.75rem 1.4rem !important;
}
[data-testid="stDownloadButton"] button:hover {
    background-color: var(--navy) !important; color: var(--y) !important;
}

[data-testid="stFileUploader"] {
    background-color: var(--card) !important;
    border: 2px dashed var(--card-border) !important;
    border-radius: 10px !important; padding: 1rem !important;
}

.rev-hero {
    text-align: center;
    padding: 52px 0 28px;
    border-bottom: 1px solid var(--card-border);
    margin-bottom: 40px;
}
.rev-hero .brand {
    font-size: 0.85rem; font-weight: 700;
    color: var(--navy); letter-spacing: 0.15em;
    font-family: var(--heading);
}
.rev-hero .title {
    font-size: 2.6rem; font-weight: 900; color: var(--navy);
    font-family: var(--display); letter-spacing: -0.02em;
    position: relative; display: inline-block;
    line-height: 1; margin: 14px 0 0 0;
}
.rev-hero .title::after {
    content: ''; position: absolute; bottom: 2px; left: 0;
    width: 100%; height: 4px; background: var(--y); border-radius: 2px;
}
.rev-hero .tag {
    font-size: 0.7rem; color: var(--dim);
    letter-spacing: 0.15em;
    margin-top: 0.6rem;
}

.rev-stepbar {
    display: flex; justify-content: space-between;
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 12px; padding: 16px 24px; margin-bottom: 32px;
}
.rev-step {
    flex: 1; text-align: center;
    font-family: var(--heading); font-weight: 700;
    color: var(--dim); font-size: 0.88rem;
    position: relative;
}
.rev-step.active { color: var(--navy); }
.rev-step.done { color: var(--g); }
.rev-step .num {
    display: inline-block; width: 28px; height: 28px;
    line-height: 28px; border-radius: 50%;
    background: var(--light-bg); color: var(--dim);
    font-weight: 900; margin-right: 8px;
}
.rev-step.active .num { background: var(--navy); color: var(--y); }
.rev-step.done .num { background: var(--g); color: #FFFFFF; }

.rev-card {
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 12px; padding: 24px; margin-bottom: 20px;
}
.rev-card-title {
    font-family: var(--heading); font-weight: 800;
    color: var(--navy); font-size: 1.15rem;
    margin-bottom: 12px; letter-spacing: -0.01em;
}
.rev-caption {
    color: var(--dim); font-size: 0.85rem;
    margin-top: 4px; margin-bottom: 16px;
}

.rev-badge {
    display: inline-block; padding: 4px 10px;
    background: var(--light-bg); color: var(--navy);
    border-radius: 6px; font-size: 0.78rem; font-weight: 700;
    font-family: var(--heading); margin-right: 6px;
}
.rev-badge.y { background: var(--y); color: var(--navy); }
.rev-badge.g { background: var(--g); color: #FFFFFF; }
.rev-badge.r { background: var(--r); color: #FFFFFF; }

.rev-verdict {
    display: inline-block; padding: 10px 20px;
    border-radius: 8px; font-family: var(--heading);
    font-weight: 900; font-size: 1rem; letter-spacing: 0.05em;
}
.rev-verdict.approved { background: var(--g); color: #FFFFFF; }
.rev-verdict.needs    { background: var(--y); color: var(--navy); }
.rev-verdict.rejected { background: var(--r); color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# [2] 세션 상태 초기화
# =================================================================
INIT_STATE = {
    "step": 0,                  # 0:입력 / 1:DIAGNOSE / 2:REVISE / 3:VERIFY / 4:완료
    "title": "",
    "raw_text": "",             # 원본 시나리오 (DOCX에서 추출)
    "raw_filename": "",
    "instruction": "",          # 수정 지시문
    "locked": "",               # LOCKED 요소
    "profession_input": "",     # 주요 캐릭터 직업 (선택사항)
    "period_key": "(현대)",     # 시대 (사극·시대극)
    "historical_type": "정통",  # 역사영화 유형 (정통/팩션/퓨전)
    "fact_based": False,        # 실화 기반 작품 여부
    "genre": "드라마",
    "intensity": "BALANCED",
    "diagnose_result": None,    # Stage 1 JSON 결과
    "revise_result": None,      # Stage 2 JSON 결과
    "verify_result": None,      # Stage 3 JSON 결과
}

for k, v in INIT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_workflow():
    """전체 워크플로우 리셋."""
    for k, v in INIT_STATE.items():
        st.session_state[k] = v


# =================================================================
# [3] API 클라이언트 & 호출
# =================================================================
def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
    if not api_key:
        st.error("❌ ANTHROPIC_API_KEY가 secrets에 없습니다. "
                 ".streamlit/secrets.toml 또는 환경변수에 추가해주세요.")
        return None
    return anthropic.Anthropic(api_key=api_key)


def call_claude(client, prompt_text: str, model: str, max_tokens: int = 8000, retries: int = 2):
    """Claude API 스트리밍 호출 + max_tokens 잘림 시 자동 증량 재시도."""
    current_tokens = max_tokens
    for attempt in range(1 + retries):
        try:
            collected = ""
            stop_reason = None
            with client.messages.stream(
                model=model,
                max_tokens=current_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt_text}],
            ) as stream:
                for text in stream.text_stream:
                    collected += text
                final_msg = stream.get_final_message()
                stop_reason = final_msg.stop_reason

            if stop_reason == "max_tokens":
                if attempt < retries:
                    next_tokens = min(int(current_tokens * 1.5), 32000)
                    st.info(f"🔄 응답이 {current_tokens} 토큰에서 잘렸습니다. "
                            f"{next_tokens} 토큰으로 재시도합니다... ({attempt+2}/{1+retries})")
                    current_tokens = next_tokens
                    continue
                else:
                    st.warning(f"⚠️ {retries}회 재시도 후에도 {current_tokens} 토큰에서 잘렸습니다. "
                               "결과가 불완전할 수 있습니다.")
            return collected
        except Exception as e:
            st.error(f"❌ API 오류: {type(e).__name__} — {e}")
            return None
    return None


def parse_json(raw: str):
    """JSON 파싱 (마크다운 코드블록 제거 + 양끝 트리밍)."""
    if not raw:
        return None
    txt = raw.strip()
    # 코드블록 제거
    txt = re.sub(r'^```(?:json)?\s*\n', '', txt)
    txt = re.sub(r'\n```\s*$', '', txt)
    # 첫 { 부터 마지막 } 까지만
    s = txt.find('{')
    e = txt.rfind('}')
    if s == -1 or e == -1 or e < s:
        return None
    try:
        return json.loads(txt[s:e+1])
    except json.JSONDecodeError as err:
        st.error(f"❌ JSON 파싱 실패: {err}")
        st.code(txt[:500], language="json")
        return None


# =================================================================
# [4] DOCX 입력: 원본 시나리오 파싱
# =================================================================
def extract_docx_text(uploaded_file) -> str:
    """업로드된 DOCX에서 본문 텍스트를 추출."""
    try:
        doc = Document(uploaded_file)
        paragraphs = []
        for p in doc.paragraphs:
            t = p.text.strip()
            if t:
                paragraphs.append(t)
        # 표 안의 텍스트도 수집 (씬 헤더·대사 표로 정리된 경우 대비)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        t = p.text.strip()
                        if t:
                            paragraphs.append(t)
        return "\n".join(paragraphs)
    except Exception as e:
        st.error(f"DOCX 추출 실패: {e}")
        return ""


# =================================================================
# [5] DOCX 출력: 수정본 & 검증 보고서
# =================================================================
def _set_font(run, font_name="맑은 고딕", size_pt=10.5, bold=False, color=None):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), font_name)


def create_revised_docx(revise_result: dict, title: str = "", genre: str = "") -> bytes:
    """Stage 2 결과를 한국 시나리오 표준 서식의 DOCX로 변환."""
    doc = Document()

    # 페이지 설정 (A4, 여백 2.5cm)
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ── 표지 ──
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("BLUE JEANS PICTURES")
    _set_font(r, size_pt=9, bold=True, color=(255, 203, 5))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("REVISE ENGINE")
    _set_font(r, size_pt=11, bold=True, color=(25, 25, 112))

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title if title else "수정본")
    _set_font(r, size_pt=22, bold=True, color=(25, 25, 112))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("수정본 (Revised Scenes)")
    _set_font(r, size_pt=12, bold=False, color=(142, 142, 153))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_txt = f"장르: {genre}    생성일: {datetime.now().strftime('%Y-%m-%d')}"
    r = p.add_run(meta_txt)
    _set_font(r, size_pt=9, color=(142, 142, 153))

    doc.add_page_break()

    # ── 요약 ──
    rr = revise_result.get("revision_result", {})
    summary = rr.get("summary", "")
    if summary:
        p = doc.add_paragraph()
        r = p.add_run("■ 수정 요약")
        _set_font(r, size_pt=13, bold=True, color=(25, 25, 112))

        p = doc.add_paragraph()
        r = p.add_run(summary)
        _set_font(r, size_pt=10.5)
        doc.add_paragraph()

    cross = rr.get("cross_scene_impact", "")
    if cross:
        p = doc.add_paragraph()
        r = p.add_run("■ 플롯 흐름에 미치는 영향")
        _set_font(r, size_pt=13, bold=True, color=(25, 25, 112))

        p = doc.add_paragraph()
        r = p.add_run(cross)
        _set_font(r, size_pt=10.5)
        doc.add_paragraph()

    unchanged = rr.get("unchanged_scenes_note", "")
    if unchanged:
        p = doc.add_paragraph()
        r = p.add_run("■ 수정 대상 외 씬 안내")
        _set_font(r, size_pt=13, bold=True, color=(25, 25, 112))

        p = doc.add_paragraph()
        r = p.add_run(unchanged)
        _set_font(r, size_pt=10.5)

    doc.add_page_break()

    # ── 수정된 씬 본문 ──
    p = doc.add_paragraph()
    r = p.add_run("■ 수정된 씬")
    _set_font(r, size_pt=15, bold=True, color=(25, 25, 112))
    doc.add_paragraph()

    scenes = rr.get("revised_scenes", [])
    for idx, scene in enumerate(scenes, 1):
        header = scene.get("scene_header", f"Scene {idx}")
        content = scene.get("revised_content", "")
        notes = scene.get("revision_notes", {})

        # 씬 헤더
        p = doc.add_paragraph()
        r = p.add_run(header)
        _set_font(r, size_pt=12, bold=True, color=(25, 25, 112))

        # 씬 본문 (줄 단위로 나누어 입력)
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                doc.add_paragraph()
                continue
            p = doc.add_paragraph()
            # 대사 들여쓰기 감지 (인물명만 있는 줄, 대사 줄)
            if len(line) <= 12 and not re.search(r'[.,!?]', line) and not line.startswith(('S#', 'INT.', 'EXT.', 'CUT')):
                # 인물명 가능성 — 중앙 들여쓰기
                p.paragraph_format.left_indent = Cm(3.5)
                r = p.add_run(line)
                _set_font(r, size_pt=10.5, bold=True)
            elif line.startswith(('S#', 'INT.', 'EXT.', 'CUT')):
                # 씬 헤더·전환
                r = p.add_run(line)
                _set_font(r, size_pt=11, bold=True, color=(25, 25, 112))
            else:
                r = p.add_run(line)
                _set_font(r, size_pt=10.5)

        # 수정 노트 (작은 글씨로)
        doc.add_paragraph()
        what_changed = notes.get("what_changed", "")
        if what_changed:
            p = doc.add_paragraph()
            r = p.add_run(f"  ▸ 변경: {what_changed}")
            _set_font(r, size_pt=9, color=(142, 142, 153))

        what_preserved = notes.get("what_preserved", "")
        if what_preserved:
            p = doc.add_paragraph()
            r = p.add_run(f"  ▸ 보존: {what_preserved}")
            _set_font(r, size_pt=9, color=(142, 142, 153))

        if idx < len(scenes):
            doc.add_paragraph()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run("━━━━━━━━━━━━━━━━━━━━━━━━")
            _set_font(r, size_pt=10, color=(226, 226, 224))
            doc.add_paragraph()

    # ── 바이트 반환 ──
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_verify_docx(verify_result: dict, title: str = "") -> bytes:
    """Stage 3 검증 보고서 DOCX."""
    doc = Document()

    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ── 표지 ──
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("BLUE JEANS PICTURES · REVISE ENGINE")
    _set_font(r, size_pt=9, bold=True, color=(255, 203, 5))

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title if title else "검증 보고서")
    _set_font(r, size_pt=20, bold=True, color=(25, 25, 112))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Verification Report")
    _set_font(r, size_pt=11, color=(142, 142, 153))

    doc.add_paragraph()

    vr = verify_result.get("verify_report", {})

    # ── 종합 판정 ──
    verdict = vr.get("overall_verdict", "")
    score = vr.get("overall_score", "")
    reason = vr.get("verdict_reason", "")

    verdict_color = (46, 196, 132) if verdict == "APPROVED" else \
                    (255, 203, 5) if verdict == "NEEDS_REVISION" else \
                    (225, 68, 68)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"[ {verdict} ]")
    _set_font(r, size_pt=16, bold=True, color=verdict_color)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"종합 점수: {score} / 10.0")
    _set_font(r, size_pt=13, bold=True, color=(25, 25, 112))

    if reason:
        doc.add_paragraph()
        p = doc.add_paragraph()
        r = p.add_run(reason)
        _set_font(r, size_pt=10.5)

    doc.add_paragraph()

    # ── 4축 검증 ──
    def section_score(title_text, key):
        block = vr.get(key, {})
        sc = block.get("score", "")
        p = doc.add_paragraph()
        r = p.add_run(f"■ {title_text}  —  {sc}/10")
        _set_font(r, size_pt=13, bold=True, color=(25, 25, 112))
        return block

    # 1. 지시사항 반영도
    block = section_score("1. 지시사항 반영도 (Instruction Compliance)", "instruction_compliance")
    for item in block.get("items", []):
        status = item.get("status", "")
        inst = item.get("instruction_item", "")
        ev = item.get("evidence", "")
        mark = "✓" if status == "Y" else ("△" if status == "Partial" else "✗")
        p = doc.add_paragraph()
        r = p.add_run(f"  {mark} [{status}] {inst}")
        color = (46, 196, 132) if status == "Y" else (255, 140, 0) if status == "Partial" else (225, 68, 68)
        _set_font(r, size_pt=10, bold=True, color=color)
        if ev:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            r = p.add_run(f"    → {ev}")
            _set_font(r, size_pt=9.5, color=(80, 80, 90))

    doc.add_paragraph()

    # 2. LOCKED 보존도
    block = section_score("2. LOCKED 보존도 (Locked Preservation)", "locked_preservation")
    for item in block.get("items", []):
        status = item.get("status", "")
        locked_item = item.get("locked_item", "")
        ev = item.get("evidence", "")
        mark = "✓" if status == "Preserved" else ("—" if status == "N/A" else "✗")
        p = doc.add_paragraph()
        r = p.add_run(f"  {mark} [{status}] {locked_item}")
        color = (46, 196, 132) if status == "Preserved" else (142, 142, 153) if status == "N/A" else (225, 68, 68)
        _set_font(r, size_pt=10, bold=True, color=color)
        if ev:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            r = p.add_run(f"    → {ev}")
            _set_font(r, size_pt=9.5, color=(80, 80, 90))

    doc.add_paragraph()

    # 3. AI ESCAPE
    block = section_score("3. AI SCREENPLAY ESCAPE 준수도", "ai_escape_check")
    clean = block.get("clean_patterns", "")
    if clean:
        p = doc.add_paragraph()
        r = p.add_run(f"  ✓ 위반 없는 패턴: {clean} / 20")
        _set_font(r, size_pt=10, color=(46, 196, 132))
    violations = block.get("violations", [])
    if violations:
        for v in violations:
            pid = v.get("pattern_id", "")
            pname = v.get("pattern_name", "")
            scene = v.get("scene_id", "")
            quote = v.get("quote", "")
            sev = v.get("severity", "")
            sev_color = (225, 68, 68) if sev == "High" else (255, 140, 0) if sev == "Medium" else (142, 142, 153)
            p = doc.add_paragraph()
            r = p.add_run(f"  ✗ [{pid}] {pname} — {scene} ({sev})")
            _set_font(r, size_pt=10, bold=True, color=sev_color)
            if quote:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.8)
                r = p.add_run(f'    → "{quote}"')
                _set_font(r, size_pt=9.5, color=(80, 80, 90))
    else:
        p = doc.add_paragraph()
        r = p.add_run("  위반 사항 없음.")
        _set_font(r, size_pt=10, color=(46, 196, 132))

    doc.add_paragraph()

    # 4. 장르 준수도
    block = section_score("4. 장르 RULE PACK 준수도", "genre_compliance")
    p = doc.add_paragraph()
    r = p.add_run("  [Must Have]")
    _set_font(r, size_pt=10.5, bold=True, color=(25, 25, 112))
    for item in block.get("must_have_check", []):
        st_val = item.get("status", "")
        it = item.get("item", "")
        nt = item.get("note", "")
        mark = "✓" if st_val == "Met" else ("△" if st_val == "Partial" else "✗")
        color = (46, 196, 132) if st_val == "Met" else (255, 140, 0) if st_val == "Partial" else (225, 68, 68)
        p = doc.add_paragraph()
        r = p.add_run(f"    {mark} [{st_val}] {it}  —  {nt}")
        _set_font(r, size_pt=9.5, color=color)

    p = doc.add_paragraph()
    r = p.add_run("  [Fails to Avoid]")
    _set_font(r, size_pt=10.5, bold=True, color=(25, 25, 112))
    for item in block.get("fails_check", []):
        st_val = item.get("status", "")
        it = item.get("item", "")
        nt = item.get("note", "")
        mark = "✓" if st_val == "Avoided" else ("△" if st_val == "Improved" else "✗")
        color = (46, 196, 132) if st_val == "Avoided" else (255, 140, 0) if st_val == "Improved" else (225, 68, 68)
        p = doc.add_paragraph()
        r = p.add_run(f"    {mark} [{st_val}] {it}  —  {nt}")
        _set_font(r, size_pt=9.5, color=color)

    doc.add_paragraph()

    # ── 주요 변화 ──
    highlights = vr.get("side_by_side_highlights", [])
    if highlights:
        p = doc.add_paragraph()
        r = p.add_run("■ 핵심 변화 요약")
        _set_font(r, size_pt=13, bold=True, color=(25, 25, 112))
        for h in highlights:
            sid = h.get("scene_id", "")
            kc = h.get("key_change", "")
            imp = h.get("improvement_note", "")
            p = doc.add_paragraph()
            r = p.add_run(f"  • {sid}: {kc}")
            _set_font(r, size_pt=10, bold=True)
            if imp:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.8)
                r = p.add_run(f"    {imp}")
                _set_font(r, size_pt=9.5, color=(80, 80, 90))

    # ── 재수정 권고 ──
    recs = vr.get("recommendations", [])
    if recs:
        doc.add_paragraph()
        p = doc.add_paragraph()
        r = p.add_run("■ 재수정 권고")
        _set_font(r, size_pt=13, bold=True, color=(225, 68, 68))
        for rec in recs:
            p = doc.add_paragraph()
            r = p.add_run(f"  • {rec}")
            _set_font(r, size_pt=10)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =================================================================
# [6] Stage 실행 함수
# =================================================================
def run_diagnose(client):
    """Stage 1: Sonnet으로 지시 해석 + 수정 플랜 생성."""
    prompt_text = build_diagnose_prompt(
        raw_text=st.session_state.raw_text,
        instruction=st.session_state.instruction,
        locked=st.session_state.locked,
        genre=st.session_state.genre,
        intensity=st.session_state.intensity,
        profession_input=st.session_state.profession_input,
        period_key=st.session_state.period_key,
        historical_type=st.session_state.historical_type,
        fact_based=st.session_state.fact_based,
    )
    raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=8000)
    if not raw:
        return None
    return parse_json(raw)


def run_revise(client):
    """Stage 2: Opus로 실제 집필."""
    prompt_text = build_revise_prompt(
        raw_text=st.session_state.raw_text,
        diagnose_result=st.session_state.diagnose_result,
        genre=st.session_state.genre,
        intensity=st.session_state.intensity,
        locked=st.session_state.locked,
        profession_input=st.session_state.profession_input,
        period_key=st.session_state.period_key,
        historical_type=st.session_state.historical_type,
        fact_based=st.session_state.fact_based,
    )
    raw = call_claude(client, prompt_text, model=MODEL_WRITE, max_tokens=16000)
    if not raw:
        return None
    return parse_json(raw)


def run_verify(client):
    """Stage 3: Sonnet으로 검증 보고서 생성."""
    prompt_text = build_verify_prompt(
        raw_text=st.session_state.raw_text,
        revise_result=st.session_state.revise_result,
        instruction=st.session_state.instruction,
        locked=st.session_state.locked,
        genre=st.session_state.genre,
    )
    raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=8000)
    if not raw:
        return None
    return parse_json(raw)


# =================================================================
# [7] UI 컴포넌트
# =================================================================
def render_hero():
    st.markdown("""
    <div class="rev-hero">
        <div class="brand">B L U E &nbsp; J E A N S &nbsp; P I C T U R E S</div>
        <div class="title">REVISE ENGINE</div>
        <div class="tag">D I A G N O S E &nbsp; · &nbsp; R E V I S E &nbsp; · &nbsp; V E R I F Y</div>
    </div>
    """, unsafe_allow_html=True)


def render_stepbar():
    step = st.session_state.step
    steps = [
        (0, "입력"),
        (1, "진단"),
        (2, "집필"),
        (3, "검증"),
        (4, "완료"),
    ]
    html = '<div class="rev-stepbar">'
    for num, name in steps:
        cls = "rev-step"
        if num < step:
            cls += " done"
        elif num == step:
            cls += " active"
        html += f'<div class="{cls}"><span class="num">{num+1}</span>{name}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# =================================================================
# [8] Step 화면들
# =================================================================
def show_step_0_input():
    """Step 0: 원본 업로드 + 지시문 + LOCKED + 옵션 입력."""
    st.markdown('<div class="rev-card-title">1. 원본 시나리오 업로드 (DOCX)</div>', unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">Writer Engine에서 출력한 DOCX 파일을 업로드하세요.</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "DOCX 파일 선택",
        type=["docx"],
        key="docx_uploader",
        label_visibility="collapsed"
    )

    if uploaded:
        text = extract_docx_text(uploaded)
        if text:
            st.session_state.raw_text = text
            st.session_state.raw_filename = uploaded.name
            # 제목은 파일명에서 추출
            st.session_state.title = re.sub(r'\.docx$', '', uploaded.name)
            st.success(f"✅ 업로드 완료: {uploaded.name}  ({len(text):,}자)")
            with st.expander("📄 추출된 본문 미리보기 (앞 1,000자)"):
                st.text(text[:1000] + ("..." if len(text) > 1000 else ""))
        else:
            st.error("❌ 본문 추출 실패")

    st.markdown("---")

    # ── 제목 ──
    st.session_state.title = st.text_input(
        "프로젝트 제목",
        value=st.session_state.title,
        placeholder="예: 쿠킹클래스 러브 스토리",
    )

    # ── 장르 + 강도 ──
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.genre = st.selectbox(
            "장르",
            options=list(GENRE_RULES.keys()),
            index=list(GENRE_RULES.keys()).index(st.session_state.genre)
                if st.session_state.genre in GENRE_RULES else 0,
        )
    with c2:
        intensity_options = list(INTENSITY_RULES.keys())
        intensity_labels = {
            "CONSERVATIVE": "CONSERVATIVE (원본 70%+ 보존)",
            "BALANCED":     "BALANCED (원본 50% 보존)",
            "AGGRESSIVE":   "AGGRESSIVE (원본 20~30% 유지)",
        }
        selected_label = st.selectbox(
            "수정 강도 (Intensity)",
            options=[intensity_labels[k] for k in intensity_options],
            index=intensity_options.index(st.session_state.intensity),
        )
        for k, lbl in intensity_labels.items():
            if lbl == selected_label:
                st.session_state.intensity = k
                break
        st.caption(f"→ {INTENSITY_RULES[st.session_state.intensity]['description']}")

    st.markdown("---")

    # ── 수정 지시문 ──
    st.markdown('<div class="rev-card-title">2. 수정 지시문</div>', unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">본인 지시, 모니터 보고서, 투자사 피드백, Rewrite Engine의 CHRIS/SHIHO 분석 내용을 자유롭게 입력하세요.</div>',
                unsafe_allow_html=True)

    # Rewrite Engine JSON 자동 변환 expander
    with st.expander("🔗 Rewrite Engine 진단·처방 JSON 불러오기 (자동 변환)"):
        st.caption("Rewrite Engine에서 다운로드한 진단·처방 JSON을 업로드하거나 텍스트로 붙여넣으면, "
                   "CHRIS 분석 + SHIHO 처방이 자동으로 수정 지시문으로 변환됩니다. "
                   "(MOON 리라이팅은 자동 제외됩니다.)")

        rj_col1, rj_col2 = st.columns([1, 1])
        with rj_col1:
            uploaded_json = st.file_uploader(
                "JSON 파일 업로드",
                type=["json"],
                key="rewrite_json_uploader",
            )
        with rj_col2:
            pasted_json = st.text_area(
                "또는 JSON 직접 붙여넣기",
                height=120,
                key="rewrite_json_pasted",
                placeholder='{\n  "scores": {...},\n  "pros_cons": {...},\n  ...\n}',
            )

        if st.button("📥 Rewrite Engine JSON → 수정 지시문 변환", key="btn_convert_rewrite_json"):
            json_source = None
            if uploaded_json is not None:
                try:
                    json_source = uploaded_json.read().decode("utf-8")
                except Exception as e:
                    st.error(f"파일 읽기 실패: {e}")
            elif pasted_json.strip():
                json_source = pasted_json.strip()

            if json_source:
                try:
                    converted = parse_rewrite_engine_json(json_source)
                    if converted:
                        # 기존 지시문이 있으면 추가, 없으면 대체
                        if st.session_state.instruction.strip():
                            st.session_state.instruction = (
                                st.session_state.instruction.rstrip() +
                                "\n\n--- Rewrite Engine 진단·처방 결과 ---\n\n" +
                                converted
                            )
                        else:
                            st.session_state.instruction = converted
                        st.success(f"✅ 변환 완료! 지시문 입력창에 자동 추가되었습니다 ({len(converted):,}자)")
                        st.rerun()
                    else:
                        st.warning("⚠️ JSON에서 변환 가능한 진단·처방 내용을 찾지 못했습니다.")
                except Exception as e:
                    st.error(f"변환 실패: {e}")
            else:
                st.warning("⚠️ JSON 파일을 업로드하거나 텍스트로 붙여넣어 주세요.")

    st.session_state.instruction = st.text_area(
        "지시문",
        value=st.session_state.instruction,
        height=240,
        placeholder="예:\n• 3막에서 주인공이 특정 남주를 선택하는 결말이 뻔함. 자기 발견 엔딩으로 재집필.\n"
                    "• 유진의 대사가 너무 설명적임. 행동으로 보여주도록.\n"
                    "• S#35 카페 씬의 시작을 '도착 과정' 대신 '이미 진행 중인 상황'으로 변경.\n\n"
                    "또는 Rewrite Engine의 진단·처방 내용을 그대로 붙여넣기도 가능합니다.",
        label_visibility="collapsed",
    )

    # ── LOCKED ──
    st.markdown('<div class="rev-card-title">3. LOCKED — 절대 건드리지 말 요소</div>', unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">수정에서 제외할 요소를 자유롭게 적어주세요. LOCKED는 지시문보다 우선합니다.</div>',
                unsafe_allow_html=True)
    st.session_state.locked = st.text_area(
        "LOCKED",
        value=st.session_state.locked,
        height=120,
        placeholder="예:\n• 주인공의 직업(쇼핑 호스트) 유지\n"
                    "• 엔딩에서 주인공이 혼자 남는 구도 유지\n"
                    "• S#50의 반전은 건드리지 말 것\n"
                    "• 세웅 캐릭터의 대사는 그대로 유지",
        label_visibility="collapsed",
    )

    # ── 직업 전문성 (선택사항) ──
    st.markdown('<div class="rev-card-title">4. 주요 캐릭터 직업 <span style="font-weight:400; color:#8E8E99; font-size:0.85rem;">(선택사항)</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">입력 시 해당 직업의 전문 용어·공간 디테일·금지 사항이 수정본 집필에 반영됩니다. '
                '비워두면 원본에서 자동 감지합니다.</div>', unsafe_allow_html=True)
    st.session_state.profession_input = st.text_area(
        "직업",
        value=st.session_state.profession_input,
        height=80,
        placeholder="예: 유진=쇼핑 호스트, 진호=변호사, 세웅=셰프\n"
                    "또는 단순히: 변호사, 셰프, 쇼핑 호스트",
        label_visibility="collapsed",
    )

    # ── 시대 / 역사영화 / 실화 (선택사항) ──
    st.markdown('<div class="rev-card-title">5. 시대 · 실화 정보 <span style="font-weight:400; color:#8E8E99; font-size:0.85rem;">(사극·시대극·실화영화 작업 시)</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">현대 배경이면 그대로 두세요. 사극·시대극이면 시대를 선택하고, 실화 기반이면 체크하세요.</div>',
                unsafe_allow_html=True)

    period_keys = get_period_keys_for_ui()
    period_labels = get_period_labels_for_ui()

    cp1, cp2 = st.columns([1, 1])
    with cp1:
        # 시대 드롭다운
        try:
            current_idx = period_keys.index(st.session_state.period_key)
        except ValueError:
            current_idx = 0
        selected_period = st.selectbox(
            "시대 배경",
            options=period_keys,
            index=current_idx,
            format_func=lambda k: period_labels.get(k, k),
        )
        st.session_state.period_key = selected_period

    with cp2:
        # 역사영화 유형 (사극일 때만 활성화)
        is_historical = (st.session_state.period_key != "(현대)")
        ht_options = ["정통", "팩션", "퓨전"]
        try:
            ht_idx = ht_options.index(st.session_state.historical_type)
        except ValueError:
            ht_idx = 0
        selected_ht = st.radio(
            "역사영화 유형",
            options=ht_options,
            index=ht_idx,
            horizontal=True,
            disabled=not is_historical,
            help="정통: 사실 충실 / 팩션: 사실+허구 결합 / 퓨전: 현대 감각 적극 도입",
        )
        st.session_state.historical_type = selected_ht
        if not is_historical:
            st.caption("→ 시대 선택 시 활성화됩니다")

    # 실화 기반 체크박스
    st.session_state.fact_based = st.checkbox(
        "🎬 이 작품은 실화 또는 역사적 사건을 기반으로 합니다 (명예훼손·인격권 가이드 적용)",
        value=st.session_state.fact_based,
        help="실명 사용·특정 가능 디테일·실존 공인 악역화 등의 리스크를 자동 점검합니다",
    )

    # ── 실행 버튼 ──
    st.markdown("---")
    ready = bool(st.session_state.raw_text and st.session_state.instruction.strip())

    if not ready:
        st.warning("⚠️ 원본 DOCX 업로드 + 수정 지시문이 모두 있어야 시작할 수 있습니다.")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🔬 Stage 1: 진단 시작 (DIAGNOSE)",
                     disabled=not ready, use_container_width=True):
            client = get_client()
            if client:
                with st.spinner("🔬 수정 지시를 분석하고 수정 플랜을 생성 중... (Sonnet 4.6)"):
                    result = run_diagnose(client)
                    if result:
                        st.session_state.diagnose_result = result
                        st.session_state.step = 1
                        st.rerun()
                    else:
                        st.error("진단 실패. 다시 시도해주세요.")
    with c2:
        if st.button("🔄 초기화", use_container_width=True):
            reset_workflow()
            st.rerun()


def show_step_1_diagnose():
    """Step 1: DIAGNOSE 결과 확인 + REVISE 실행."""
    dr = st.session_state.diagnose_result.get("revision_plan", {})

    st.markdown('<div class="rev-card-title">🔬 Stage 1: 진단 결과 (Revision Plan)</div>',
                unsafe_allow_html=True)

    # 요약
    summary = dr.get("summary", "")
    if summary:
        st.markdown('<div class="rev-card"><b style="color:#191970;">전체 수정 방향</b></div>',
                    unsafe_allow_html=True)
        st.write(summary)

    # 예상 씬 수
    cnt = dr.get("estimated_scene_count", "")
    conf = dr.get("confidence", "")
    if cnt or conf:
        st.markdown(f'<span class="rev-badge">수정 대상 씬: {cnt}</span>'
                    f'<span class="rev-badge y">진단 신뢰도: {conf}/10</span>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # LOCKED 요약
    locked_summary = dr.get("locked_summary", "")
    if locked_summary:
        with st.expander("🔒 LOCKED로 인식된 요소"):
            st.write(locked_summary)

    # 충돌
    conflicts = dr.get("conflicts", [])
    if conflicts:
        st.markdown('<div class="rev-card-title" style="color:#E14444;">⚠️ 지시문 vs LOCKED 충돌</div>',
                    unsafe_allow_html=True)
        for c in conflicts:
            st.warning(f"• **지시:** {c.get('instruction_item','')}\n\n"
                       f"**충돌:** {c.get('locked_conflict','')}\n\n"
                       f"**해결:** {c.get('resolution','')}")

    # 수정 대상 씬 목록
    scenes = dr.get("target_scenes", [])
    if scenes:
        st.markdown(f'<div class="rev-card-title">📋 수정 대상 씬 ({len(scenes)}개)</div>',
                    unsafe_allow_html=True)
        for idx, sc in enumerate(scenes, 1):
            with st.expander(f"Scene {idx}: {sc.get('scene_id', '')}  —  {sc.get('scene_position', '')}"):
                st.markdown(f"**플롯상 기능:** {sc.get('original_function','')}")
                st.markdown(f"**보존 요소:** {sc.get('preservation_notes','')}")
                items = sc.get("revision_items", [])
                for i, it in enumerate(items, 1):
                    src = it.get("source", "")
                    badge = "📝" if src == "user_instruction" else "🔍"
                    st.markdown(f"{badge} **[{i}] {it.get('target_element','')}**")
                    st.markdown(f"- 이슈: {it.get('issue','')}")
                    st.markdown(f"- 방향: {it.get('proposed_direction','')}")

    # Out of Scope
    oos = dr.get("out_of_scope", [])
    if oos:
        with st.expander("⏩ 처리 불가 항목 (Out of Scope)"):
            for item in oos:
                st.markdown(f"- {item}")

    st.markdown("---")

    # 실행 버튼
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✍️ Stage 2: 집필 시작 (REVISE)", use_container_width=True):
            client = get_client()
            if client:
                with st.spinner(f"✍️ {len(scenes)}개 씬 재집필 중... (Opus 4.6 · 2~5분 소요)"):
                    result = run_revise(client)
                    if result:
                        st.session_state.revise_result = result
                        st.session_state.step = 2
                        st.rerun()
                    else:
                        st.error("집필 실패. 다시 시도해주세요.")
    with c2:
        if st.button("◀ 입력으로 돌아가기", use_container_width=True):
            st.session_state.step = 0
            st.session_state.diagnose_result = None
            st.rerun()


def show_step_2_revise():
    """Step 2: REVISE 결과 확인 + VERIFY 실행."""
    rr = st.session_state.revise_result.get("revision_result", {})

    st.markdown('<div class="rev-card-title">✍️ Stage 2: 집필 결과 (Revised Scenes)</div>',
                unsafe_allow_html=True)

    # 요약
    summary = rr.get("summary", "")
    if summary:
        st.markdown('<div class="rev-card"><b style="color:#191970;">수정 요약</b></div>',
                    unsafe_allow_html=True)
        st.write(summary)

    # 수정된 씬
    scenes = rr.get("revised_scenes", [])
    if scenes:
        st.markdown(f'<div class="rev-card-title">📝 수정된 씬 ({len(scenes)}개)</div>',
                    unsafe_allow_html=True)
        for idx, sc in enumerate(scenes, 1):
            header = sc.get("scene_header", f"Scene {idx}")
            with st.expander(f"Scene {idx}: {header}"):
                # Side-by-Side (원본 발췌 vs 수정본)
                col_o, col_r = st.columns([1, 1])
                with col_o:
                    st.markdown("**📄 원본 발췌**")
                    st.text(sc.get("original_excerpt", ""))
                with col_r:
                    st.markdown("**✏️ 수정본**")
                    st.text(sc.get("revised_content", ""))

                # 변경 노트
                notes = sc.get("revision_notes", {})
                if notes:
                    st.markdown("---")
                    st.markdown(f"**변경 내용:** {notes.get('what_changed','')}")
                    st.markdown(f"**보존 요소:** {notes.get('what_preserved','')}")
                    st.markdown(f"**보존 비율:** {notes.get('intensity_check','')}  |  "
                                f"**LOCKED 체크:** {notes.get('locked_check','')}")

    # Cross-scene impact
    cross = rr.get("cross_scene_impact", "")
    if cross:
        with st.expander("🔄 플롯 흐름에 미치는 영향"):
            st.write(cross)

    # Unchanged note
    un = rr.get("unchanged_scenes_note", "")
    if un:
        with st.expander("📎 수정 대상 외 씬 안내"):
            st.write(un)

    st.markdown("---")

    # 실행 버튼
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✅ Stage 3: 검증 시작 (VERIFY)", use_container_width=True):
            client = get_client()
            if client:
                with st.spinner("✅ 수정본 검증 중... (Sonnet 4.6)"):
                    result = run_verify(client)
                    if result:
                        st.session_state.verify_result = result
                        st.session_state.step = 3
                        st.rerun()
                    else:
                        st.error("검증 실패. 다시 시도해주세요.")
    with c2:
        if st.button("◀ 진단으로 돌아가기", use_container_width=True):
            st.session_state.step = 1
            st.session_state.revise_result = None
            st.rerun()


def show_step_3_verify():
    """Step 3: VERIFY 결과 확인 + 완료 이동."""
    vr = st.session_state.verify_result.get("verify_report", {})

    verdict = vr.get("overall_verdict", "")
    score = vr.get("overall_score", "")
    reason = vr.get("verdict_reason", "")

    verdict_class = "approved" if verdict == "APPROVED" else \
                    "needs" if verdict == "NEEDS_REVISION" else "rejected"

    st.markdown('<div class="rev-card-title">✅ Stage 3: 검증 결과</div>',
                unsafe_allow_html=True)

    # 판정
    st.markdown(f'<div style="text-align:center; padding: 20px 0;">'
                f'<span class="rev-verdict {verdict_class}">{verdict}</span>'
                f'<div style="font-size:1.4rem; font-weight:900; color:#191970; margin-top:12px;">'
                f'{score} / 10.0</div></div>', unsafe_allow_html=True)

    if reason:
        st.info(reason)

    st.markdown("---")

    # 4축 점수
    def _show_section(title_text, key, icon):
        block = vr.get(key, {})
        sc = block.get("score", "")
        st.markdown(f'<div class="rev-card-title">{icon} {title_text}  —  {sc}/10</div>',
                    unsafe_allow_html=True)
        return block

    # 1. 지시사항 반영
    block = _show_section("1. 지시사항 반영도", "instruction_compliance", "📝")
    for item in block.get("items", []):
        status = item.get("status", "")
        inst = item.get("instruction_item", "")
        ev = item.get("evidence", "")
        if status == "Y":
            st.success(f"✓ [Y] {inst}\n\n→ {ev}")
        elif status == "Partial":
            st.warning(f"△ [Partial] {inst}\n\n→ {ev}")
        else:
            st.error(f"✗ [N] {inst}\n\n→ {ev}")

    # 2. LOCKED 보존
    block = _show_section("2. LOCKED 보존도", "locked_preservation", "🔒")
    for item in block.get("items", []):
        status = item.get("status", "")
        li = item.get("locked_item", "")
        ev = item.get("evidence", "")
        if status == "Preserved":
            st.success(f"✓ [Preserved] {li}\n\n→ {ev}")
        elif status == "N/A":
            st.caption(f"— [N/A] {li}")
        else:
            st.error(f"✗ [Violated] {li}\n\n→ {ev}")

    # 3. AI ESCAPE
    block = _show_section("3. AI SCREENPLAY ESCAPE", "ai_escape_check", "🤖")
    clean = block.get("clean_patterns", "")
    if clean:
        st.success(f"✓ 위반 없는 패턴: {clean} / 20")
    violations = block.get("violations", [])
    for v in violations:
        pid = v.get("pattern_id", "")
        pname = v.get("pattern_name", "")
        scene = v.get("scene_id", "")
        quote = v.get("quote", "")
        sev = v.get("severity", "")
        emoji = "🔴" if sev == "High" else "🟠" if sev == "Medium" else "🟡"
        st.markdown(f"{emoji} **[{pid}] {pname}** — {scene} ({sev})")
        if quote:
            st.caption(f'→ "{quote}"')

    # 4. 장르 준수도
    block = _show_section("4. 장르 RULE PACK 준수도", "genre_compliance", "🎬")
    st.markdown("**Must Have**")
    for item in block.get("must_have_check", []):
        stt = item.get("status", "")
        emoji = "✓" if stt == "Met" else "△" if stt == "Partial" else "✗"
        st.markdown(f"{emoji} [{stt}] {item.get('item','')}  —  *{item.get('note','')}*")
    st.markdown("**Fails to Avoid**")
    for item in block.get("fails_check", []):
        stt = item.get("status", "")
        emoji = "✓" if stt == "Avoided" else "△" if stt == "Improved" else "✗"
        st.markdown(f"{emoji} [{stt}] {item.get('item','')}  —  *{item.get('note','')}*")

    # 하이라이트
    highlights = vr.get("side_by_side_highlights", [])
    if highlights:
        st.markdown("---")
        st.markdown('<div class="rev-card-title">🌟 핵심 변화 요약</div>', unsafe_allow_html=True)
        for h in highlights:
            st.markdown(f"• **{h.get('scene_id','')}**: {h.get('key_change','')}")
            st.caption(h.get("improvement_note", ""))

    # 재수정 권고
    recs = vr.get("recommendations", [])
    if recs:
        st.markdown("---")
        st.markdown('<div class="rev-card-title" style="color:#E14444;">🔁 재수정 권고</div>',
                    unsafe_allow_html=True)
        for r in recs:
            st.markdown(f"• {r}")

    st.markdown("---")

    # 완료로 이동
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🎉 완료 페이지로 (다운로드)", use_container_width=True):
            st.session_state.step = 4
            st.rerun()
    with c2:
        if st.button("◀ 집필 결과로 돌아가기", use_container_width=True):
            st.session_state.step = 2
            st.session_state.verify_result = None
            st.rerun()


def show_step_4_complete():
    """Step 4: 다운로드 + 초기화."""
    st.markdown('<div style="text-align:center; padding: 30px 0;">'
                '<span style="font-size: 2.4rem; font-weight: 950; color: #2EC484;">'
                '🎉 각색 완료!</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="rev-card-title">📥 다운로드</div>', unsafe_allow_html=True)

    title = st.session_state.title or "수정본"
    genre = st.session_state.genre

    c1, c2 = st.columns(2)

    # 수정본 DOCX
    with c1:
        try:
            docx_bytes = create_revised_docx(
                st.session_state.revise_result,
                title=title,
                genre=genre,
            )
            st.download_button(
                "📄 수정본 (DOCX)",
                data=docx_bytes,
                file_name=get_report_filename(title, "revised"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_revised",
                help="Revise Engine이 생성한 수정된 씬들 + 요약",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"수정본 DOCX 생성 오류: {e}")

    # 검증 보고서 DOCX
    with c2:
        try:
            verify_bytes = create_verify_docx(
                st.session_state.verify_result,
                title=title,
            )
            st.download_button(
                "✅ 검증 보고서 (DOCX)",
                data=verify_bytes,
                file_name=get_report_filename(title, "verify"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_verify",
                help="지시사항 반영 + LOCKED 보존 + AI ESCAPE + 장르 준수도 검증",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"검증 보고서 DOCX 생성 오류: {e}")

    # JSON 백업 다운로드
    st.markdown("---")
    with st.expander("🗃️ 원본 JSON 백업 다운로드 (고급)"):
        full_state = {
            "meta": {
                "title": title,
                "genre": genre,
                "intensity": st.session_state.intensity,
                "generated_at": datetime.now().isoformat(),
                "engine": "BLUE JEANS REVISE ENGINE v1.0",
            },
            "input": {
                "instruction": st.session_state.instruction,
                "locked": st.session_state.locked,
            },
            "diagnose": st.session_state.diagnose_result,
            "revise":   st.session_state.revise_result,
            "verify":   st.session_state.verify_result,
        }
        json_bytes = json.dumps(full_state, ensure_ascii=False, indent=2).encode("utf-8")
        safe_title = re.sub(r'[/*?:"<>|]', '_', title)
        date_str = datetime.now().strftime("%Y%m%d")
        st.download_button(
            "📋 전체 JSON 다운로드",
            data=json_bytes,
            file_name=f"{safe_title}_revise_full_{date_str}.json",
            mime="application/json",
            key="dl_json_full",
            use_container_width=True,
        )

    st.markdown("---")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🔄 새 시나리오 각색 시작", use_container_width=True):
            reset_workflow()
            st.rerun()
    with c2:
        if st.button("◀ 검증 결과로 돌아가기", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


# =================================================================
# [9] 메인 라우터
# =================================================================
render_hero()
render_stepbar()

step = st.session_state.step
if step == 0:
    show_step_0_input()
elif step == 1:
    show_step_1_diagnose()
elif step == 2:
    show_step_2_revise()
elif step == 3:
    show_step_3_verify()
elif step == 4:
    show_step_4_complete()

# ── 푸터 ──
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#8E8E99; font-size:0.75rem; padding:20px 0;">'
    'BLUE JEANS PICTURES · REVISE ENGINE v1.0  ·  '
    'Powered by Claude Opus 4.6 + Sonnet 4.6'
    '</div>',
    unsafe_allow_html=True,
)
