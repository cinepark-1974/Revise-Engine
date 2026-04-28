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
    split_into_batches,
    merge_batch_results,
    # v2.0 신규
    build_tone_dna_extraction_prompt,
    build_diff_analysis_prompt,
    build_distribution_diagnostic_prompt,
    absorb_rewrite_engine_metadata,
    # v2.1 신규
    build_genre_dna_extraction_prompt,
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
    "revise_batches": None,     # 배치 분할 결과 (list)
    "batch_results": {},        # {batch_index: revise_result, ...}
    "current_batch": 0,         # 현재 처리 중인 배치 (1부터)
    "batch_size": 6,            # 한 배치당 씬 개수
    "revise_result": None,      # Stage 2 통합 결과
    "verify_result": None,      # Stage 3 JSON 결과
    # v2.0 — 톤 레퍼런스 + Diff 학습 + Rewrite 메타
    "tone_ref_text": "",        # 톤 레퍼런스 DOCX의 전문
    "tone_ref_filename": "",
    "diff_orig_text": "",       # Diff 모드 — 원본 (이전 버전)
    "diff_orig_filename": "",
    "diff_refined_text": "",    # Diff 모드 — 손본본 (최신 버전)
    "diff_refined_filename": "",
    "rewrite_json_text": "",    # Rewrite Engine JSON 원문 (변환 + 흡수)
    "tone_dna": None,           # 추출된 톤 DNA (DIAGNOSE 자동 실행)
    "diff_analysis": None,      # Diff 학습 결과
    "distribution_diagnostic": None,  # 분포 진단
    "rewrite_metadata": None,   # Rewrite 메타 흡수
    # v2.1 — 장르 DNA (참고작 1~3편에서 추출)
    "genre_ref_texts": [],      # [참고작1 텍스트, 참고작2, ...] 최대 3편
    "genre_ref_filenames": [],  # 파일명 리스트
    "genre_dna": None,          # 추출된 장르 DNA
    # v2.1 — Diff 모드: Before로 원본을 자동 사용할지 옵션
    "diff_use_main_as_before": True,
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


def call_claude(client, prompt_text: str, model: str, max_tokens: int = 32000, retries: int = 2):
    """Claude API 스트리밍 호출 + max_tokens 잘림 시 자동 증량 재시도.

    모델별 한도:
    - Sonnet 4.6: 최대 64,000 토큰
    - Opus 4.6:   최대 32,000 토큰
    """
    # 모델별 상한
    if "opus" in model.lower():
        absolute_cap = 32000
    else:  # sonnet, haiku 등
        absolute_cap = 64000

    current_tokens = min(max_tokens, absolute_cap)

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
                if attempt < retries and current_tokens < absolute_cap:
                    next_tokens = min(int(current_tokens * 1.5), absolute_cap)
                    if next_tokens == current_tokens:
                        # 이미 한도에 도달
                        st.warning(f"⚠️ 모델 한도({absolute_cap} 토큰)에서 응답이 잘렸습니다. "
                                   "결과가 불완전할 수 있습니다. 시나리오를 더 짧게 분할하거나 "
                                   "지시문을 간소화하는 것을 권장합니다.")
                        return collected
                    st.info(f"🔄 응답이 {current_tokens:,} 토큰에서 잘렸습니다. "
                            f"{next_tokens:,} 토큰으로 재시도합니다... ({attempt+2}/{1+retries})")
                    current_tokens = next_tokens
                    continue
                else:
                    st.warning(f"⚠️ {retries}회 재시도 후에도 {current_tokens:,} 토큰에서 잘렸습니다. "
                               "결과가 불완전할 수 있습니다.")
            return collected
        except Exception as e:
            st.error(f"❌ API 오류: {type(e).__name__} — {e}")
            return None
    return None


def parse_json(raw: str):
    """JSON 파싱 (마크다운 코드블록 제거 + 양끝 트리밍 + 잘린 JSON 복구 시도)."""
    if not raw:
        return None
    txt = raw.strip()
    # 코드블록 제거
    txt = re.sub(r'^```(?:json)?\s*\n', '', txt)
    txt = re.sub(r'\n```\s*$', '', txt)
    # 첫 { 부터 시작
    s = txt.find('{')
    if s == -1:
        return None

    # 1. 정상 파싱 시도 — 마지막 } 까지
    e = txt.rfind('}')
    if e > s:
        try:
            return json.loads(txt[s:e+1])
        except json.JSONDecodeError:
            pass  # 복구 시도로 진행

    # 2. 잘린 JSON 복구 시도 — 괄호 균형 맞추기
    candidate = txt[s:]
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape_next = False
    last_valid_pos = -1

    for i, ch in enumerate(candidate):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            open_braces += 1
        elif ch == '}':
            open_braces -= 1
            if open_braces == 0 and open_brackets == 0:
                last_valid_pos = i
        elif ch == '[':
            open_brackets += 1
        elif ch == ']':
            open_brackets -= 1

    # 마지막 유효 위치까지로 시도
    if last_valid_pos > 0:
        try:
            return json.loads(candidate[:last_valid_pos+1])
        except json.JSONDecodeError:
            pass

    # 3. 잘린 끝부분 강제 닫기 시도
    truncated = candidate.rstrip().rstrip(',')
    # 마지막에 미완성 문자열이 있으면 닫기
    if truncated.count('"') % 2 == 1:
        truncated += '"'
    # 열린 배열/객체 닫기
    truncated += ']' * max(0, open_brackets) + '}' * max(0, open_braces)

    try:
        result = json.loads(truncated)
        st.warning("⚠️ 응답이 잘렸지만 부분 복구를 시도했습니다. 결과 일부가 누락될 수 있습니다.")
        return result
    except json.JSONDecodeError as err:
        st.error(f"❌ JSON 파싱 실패: {err}")
        st.caption("응답 끝부분 (디버깅용):")
        st.code(candidate[-500:], language="json")
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


def create_revised_docx(revise_result: dict, title: str = "", genre: str = "",
                        original_text: str = "",
                        fact_based: bool = False,
                        historical: bool = False,
                        historical_type: str = "") -> bytes:
    """Stage 2 결과를 한국 시나리오 표준 서식의 DOCX로 변환.

    Writer Engine과 동일한 서식 사용:
    - 함초롬바탕 10pt 기본
    - 씬번호 / 대사 / 대사연속 / 지문 4가지 Word 스타일
    - A4, 20mm 여백
    - 캐릭터명\t\t대사 형식 자동 감지
    - 메타데이터 자동 차단
    """
    from docx import Document as DocxDocument
    from docx.shared import Pt, RGBColor, Mm, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.ns import qn
    from io import BytesIO

    doc = DocxDocument()

    # ── 페이지 설정 (A4, 20mm 마진) ──
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)
    section.left_margin = Mm(20)
    section.right_margin = Mm(20)

    # ── 기본 스타일: 함초롬바탕 10pt ──
    style_normal = doc.styles["Normal"]
    style_normal.font.name = "함초롬바탕"
    style_normal.font.size = Pt(10)
    style_normal.paragraph_format.space_after = Pt(2)
    style_normal.paragraph_format.space_before = Pt(0)
    rpr = style_normal.element.rPr
    if rpr is None:
        rpr = style_normal.element.makeelement(qn('w:rPr'), {})
        style_normal.element.append(rpr)
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rfonts)
    rfonts.set(qn('w:eastAsia'), '함초롬바탕')

    def _set_eastasia_font(rpr_elem, font_name='함초롬바탕'):
        rf = rpr_elem.find(qn('w:rFonts'))
        if rf is None:
            rf = rpr_elem.makeelement(qn('w:rFonts'), {})
            rpr_elem.append(rf)
        rf.set(qn('w:eastAsia'), font_name)

    # ── 커스텀 스타일: 씬번호 / 대사 / 대사연속 / 지문 ──
    style_scene = doc.styles.add_style('씬번호', WD_STYLE_TYPE.PARAGRAPH)
    style_scene.base_style = doc.styles['Normal']
    style_scene.font.name = '함초롬바탕'
    style_scene.font.size = Pt(11)
    style_scene.font.bold = True
    style_scene.paragraph_format.space_before = Pt(24)
    style_scene.paragraph_format.space_after = Pt(6)
    style_scene.paragraph_format.line_spacing = 1.5
    _set_eastasia_font(style_scene.element.get_or_add_rPr())

    style_dialogue = doc.styles.add_style('대사', WD_STYLE_TYPE.PARAGRAPH)
    style_dialogue.base_style = doc.styles['Normal']
    style_dialogue.font.name = '함초롬바탕'
    style_dialogue.font.size = Pt(10)
    style_dialogue.font.bold = True
    style_dialogue.paragraph_format.left_indent = Cm(1.25)
    style_dialogue.paragraph_format.space_before = Pt(8)
    style_dialogue.paragraph_format.space_after = Pt(2)
    style_dialogue.paragraph_format.line_spacing = 1.5
    _set_eastasia_font(style_dialogue.element.get_or_add_rPr())

    style_dialogue_cont = doc.styles.add_style('대사연속', WD_STYLE_TYPE.PARAGRAPH)
    style_dialogue_cont.base_style = style_dialogue
    style_dialogue_cont.paragraph_format.space_before = Pt(0)
    style_dialogue_cont.paragraph_format.space_after = Pt(0)

    style_action = doc.styles.add_style('지문', WD_STYLE_TYPE.PARAGRAPH)
    style_action.base_style = doc.styles['Normal']
    style_action.font.name = '함초롬바탕'
    style_action.font.size = Pt(10)
    style_action.font.bold = False
    style_action.paragraph_format.space_before = Pt(2)
    style_action.paragraph_format.space_after = Pt(2)
    _set_eastasia_font(style_action.element.get_or_add_rPr())

    # ── 헬퍼 ──
    def add_text(text, bold=False, size=None, color=None, align=None):
        p = doc.add_paragraph()
        if align:
            p.alignment = align
        r = p.add_run(text)
        r.font.name = "함초롬바탕"
        _set_eastasia_font(r._element.get_or_add_rPr())
        if bold:
            r.bold = True
        if size:
            r.font.size = size
        if color:
            r.font.color.rgb = color
        return p

    def add_scene_heading(text):
        p = doc.add_paragraph(style='씬번호')
        r = p.add_run(text)
        r.font.name = "함초롬바탕"
        _set_eastasia_font(r._element.get_or_add_rPr())
        return p

    def add_dialogue(char_name, parenthetical, line, continuation=False):
        if continuation:
            p = doc.add_paragraph(style='대사연속')
            paren = f"({parenthetical}) " if parenthetical else ""
            full = f"\t\t{paren}{line}"
        else:
            p = doc.add_paragraph(style='대사')
            paren = f"({parenthetical}) " if parenthetical else ""
            full = f"{char_name}\t\t{paren}{line}"
        r = p.add_run(full)
        r.font.name = "함초롬바탕"
        _set_eastasia_font(r._element.get_or_add_rPr())
        return p

    def add_action(text):
        p = doc.add_paragraph(style='지문')
        r = p.add_run(text)
        r.font.name = "함초롬바탕"
        _set_eastasia_font(r._element.get_or_add_rPr())
        return p

    # ── 커버 페이지 ──
    for _ in range(6):
        doc.add_paragraph("")
    add_text("시나리오 (수정본)", size=Pt(11), align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph("")
    proj_title = title or f"<{genre}>"
    add_text(proj_title, bold=True, size=Pt(24), align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph("")
    doc.add_paragraph("")
    add_text("기획/제작 | 블루진픽처스", size=Pt(10),
             align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x8E, 0x8E, 0x99))
    rr = revise_result.get("revision_result", {})
    scenes = rr.get("revised_scenes", [])
    add_text(f"Revise Engine v2.1  ·  {len(scenes)}개 씬 수정",
             size=Pt(9), align=WD_ALIGN_PARAGRAPH.CENTER,
             color=RGBColor(0x8E, 0x8E, 0x99))
    doc.add_page_break()

    # ── 면책 자막 (실화/팩션·퓨전) ──
    _need_disclaimer = fact_based or (
        historical and ("팩션" in (historical_type or "") or "퓨전" in (historical_type or ""))
    )
    if _need_disclaimer:
        for _ in range(10):
            doc.add_paragraph("")
        add_text("본 작품에 등장하는 인물, 단체, 지명, 상호, 사건은",
                 size=Pt(11), align=WD_ALIGN_PARAGRAPH.CENTER)
        add_text("모두 허구이며, 실존하는 것과 관련이 있더라도",
                 size=Pt(11), align=WD_ALIGN_PARAGRAPH.CENTER)
        add_text("극적 구성을 위해 각색되었습니다.",
                 size=Pt(11), align=WD_ALIGN_PARAGRAPH.CENTER)
        doc.add_page_break()

    # ─────────────────────────────────────────────────────────
    # 본문 파싱: 원본 + 수정본을 통합한 "최종 시나리오" 생성
    # ─────────────────────────────────────────────────────────
    # 1) 원본 시나리오를 씬 단위로 분할
    # 2) 수정 대상 씬은 revised_content로 교체
    # 3) ADD 타입은 insert_position에 따라 삽입
    # 4) DELETE 타입은 제거
    #
    # 결과: 시나리오 처음부터 끝까지 자연스럽게 흐르는 통합본
    # ─────────────────────────────────────────────────────────

    import re as _re

    # 씬 헤딩 패턴 (Writer Engine과 동일)
    heading_re = _re.compile(r'^S?#?\d*\.?\s*(INT\.|EXT\.|INT\./EXT\.)\s*(.+)', _re.IGNORECASE)


    def _merge_header_content(header: str, content: str) -> str:
        """헤더와 본문이 중복되지 않도록 합친다.
        본문 첫 줄에 이미 헤더 핵심부(S#번호 또는 INT./EXT.)가 있으면 헤더 생략."""
        if not content.strip():
            return header
        first_line = content.strip().split('\n')[0].strip()
        # S#번호 추출
        import re as _re_inner
        h_num = _re_inner.search(r'S#\d+', header or "")
        c_num = _re_inner.search(r'S#\d+', first_line)
        if h_num and c_num and h_num.group() == c_num.group():
            return content  # 본문이 이미 헤더 포함
        # INT./EXT. 매칭
        if _re_inner.match(r'^(INT\.|EXT\.)', first_line, _re_inner.IGNORECASE):
            # 첫 줄이 씬 헤더 형태 → 본문 그대로
            return content
        return f"{header}\n{content}"

    def split_into_scenes(text: str):
        """원본 텍스트를 [(scene_id, scene_body), ...] 리스트로 분할."""
        if not text:
            return []
        lines = text.split('\n')
        scenes_list = []
        current_id = ""
        current_body = []

        for line in lines:
            stripped = line.strip()
            # S#숫자 또는 INT./EXT. 패턴이 씬 헤딩
            if heading_re.match(stripped) or _re.match(r'^S#\d+', stripped):
                # 이전 씬 저장
                if current_id or current_body:
                    scenes_list.append((current_id, '\n'.join(current_body)))
                # 새 씬 시작
                current_id = stripped
                current_body = [line]
            else:
                current_body.append(line)

        # 마지막 씬
        if current_id or current_body:
            scenes_list.append((current_id, '\n'.join(current_body)))

        return scenes_list

    def extract_scene_number(scene_id_str: str) -> str:
        """씬 식별자에서 'S#숫자' 패턴만 추출 (매칭용)."""
        m = _re.search(r'S#(\d+)', scene_id_str)
        return f"S#{m.group(1)}" if m else scene_id_str.strip()[:20]

    # 수정본 씬을 scene_number로 인덱싱
    revised_by_id = {}     # {"S#1": revised_content}
    deleted_ids = set()    # {"S#5", ...}
    add_after = {}         # {"S#42": [{header, content}, ...]}  ADD 타입

    for sc in scenes:
        sid = sc.get("scene_id", "")
        s_type = sc.get("type", "REWRITE")
        s_header = sc.get("scene_header", sid)
        s_content = sc.get("revised_content", "")
        s_num = extract_scene_number(sid)

        if s_type == "DELETE":
            deleted_ids.add(s_num)
        elif s_type == "ADD":
            insert_after = sc.get("insert_position", "") or sid
            insert_num = extract_scene_number(insert_after)
            if insert_num not in add_after:
                add_after[insert_num] = []
            # ADD 씬은 헤더가 본문에 없을 수 있으니 합쳐서
            full_text = _merge_header_content(s_header, s_content)
            add_after[insert_num].append(full_text)
        else:
            # REWRITE / MERGE / SPLIT: 단순 교체
            full_text = _merge_header_content(s_header, s_content)
            revised_by_id[s_num] = full_text

    # 원본을 씬 단위로 분할 후 통합 시나리오 구성
    final_scenes = []
    if original_text:
        original_scenes = split_into_scenes(original_text)
        for orig_id, orig_body in original_scenes:
            orig_num = extract_scene_number(orig_id)
            if orig_num in deleted_ids:
                continue  # 삭제
            if orig_num in revised_by_id:
                final_scenes.append(revised_by_id[orig_num])  # 교체
            else:
                final_scenes.append(orig_body)  # 원본 유지
            # ADD 처리
            if orig_num in add_after:
                for added in add_after[orig_num]:
                    final_scenes.append(added)
    else:
        # 원본이 없으면 수정본만 출력 (배치 부분만)
        for sc in scenes:
            s_type = sc.get("type", "REWRITE")
            if s_type == "DELETE":
                continue
            s_header = sc.get("scene_header", "")
            s_content = sc.get("revised_content", "")
            full_text = _merge_header_content(s_header, s_content)
            final_scenes.append(full_text)

    full_text = '\n\n'.join(final_scenes)

    # ─────────────────────────────────────────────────────────
    # 본문 라인 단위 파싱 (Writer Engine 동일 로직)
    # ─────────────────────────────────────────────────────────
    char_re = _re.compile(
        r'^\s{2,}([가-힣a-zA-Z\s]{1,15}?)\s*'
        r'(?:\((V\.O\.|O\.S\.|CONT\'D|cont\'d|v\.o\.|o\.s\.)\))?\s*$',
        _re.IGNORECASE
    )
    inline_dialogue_re = _re.compile(
        r'^([가-힣a-zA-Z\s]{1,15}?)\s*'
        r'(?:\((V\.O\.|O\.S\.|CONT\'D|cont\'d|v\.o\.|o\.s\.)\))?\s*'
        r'\t{1,}\s*(?:\(([^)]*)\)\s*)?(.+)',
        _re.IGNORECASE
    )
    paren_re = _re.compile(r'^\s{2,}\((.+?)\)\s*$')

    # 문자열 그대로의 \n이 들어온 경우(JSON 이스케이프 잔존) 안전 처리
    full_text = full_text.replace('\\n', '\n').replace('\\t', '\t')
    lines = full_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # 마크다운 강조 기호 제거 (** ** 등)
        if stripped.startswith('**') and stripped.endswith('**'):
            stripped = stripped[2:-2].strip()
            line = stripped

        # 메타 라인 차단 (간단 버전 — 메타 마커가 들어오면 스킵)
        if stripped.startswith('▸') or stripped.startswith('━━━'):
            i += 1
            continue
        if '내부 메모' in stripped or 'WRITER_NOTES' in stripped:
            i += 1
            continue

        # 씬 헤딩
        m = heading_re.match(stripped)
        if m or _re.match(r'^S#\d+', stripped):
            add_scene_heading(stripped)
            i += 1
            continue

        # 인라인 대사
        im = inline_dialogue_re.match(stripped)
        if im:
            char_name = im.group(1).strip()
            vo_marker = im.group(2) or ""
            inline_paren = im.group(3) or ""
            inline_text = im.group(4).strip()
            if vo_marker:
                char_name = f"{char_name} ({vo_marker})"
            add_dialogue(char_name, inline_paren, inline_text)
            i += 1
            continue

        # 들여쓰기 캐릭터명 + 대사
        cm = char_re.match(line)
        if cm:
            char_name = cm.group(1).strip()
            vo_marker = cm.group(2) or ""
            if vo_marker:
                char_name = f"{char_name} ({vo_marker})"
            parenthetical = ""
            dialogue_lines = []
            i += 1
            if i < len(lines):
                pm = paren_re.match(lines[i])
                if pm:
                    parenthetical = pm.group(1)
                    i += 1
            while i < len(lines):
                dl = lines[i]
                ds = dl.strip()
                if not ds:
                    break
                if heading_re.match(ds) or _re.match(r'^S#\d+', ds):
                    break
                if char_re.match(dl):
                    break
                if inline_dialogue_re.match(ds):
                    break
                dialogue_lines.append(ds)
                i += 1
            if dialogue_lines:
                merged = " ".join(dialogue_lines)
                add_dialogue(char_name, parenthetical, merged)
            continue

        # 그 외: 지문
        add_action(stripped)
        i += 1

    # ── 바이트 반환 ──
    buf = BytesIO()
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
def run_v2_pre_analyses(client) -> dict:
    """v2.0/v2.1 자동 분석을 실행하고 결과를 세션에 저장.

    실행 항목:
    1. 톤 DNA 추출 (tone_ref_text 있을 때)
    2. Diff 학습 (After 있고 Before는 자동/수동 선택)
    3. 분포 진단 (항상 실행)
    4. Rewrite 메타 흡수 (rewrite_json_text 있을 때)
    5. 장르 DNA 추출 (genre_ref_texts 있을 때) [v2.1]

    Returns:
        {tone_dna, diff_analysis, distribution_diagnostic, rewrite_metadata, genre_dna}
    """
    results = {
        "tone_dna": None,
        "diff_analysis": None,
        "distribution_diagnostic": None,
        "rewrite_metadata": None,
        "genre_dna": None,
    }

    # 1. 톤 DNA 추출
    if st.session_state.tone_ref_text and st.session_state.tone_ref_text.strip():
        with st.spinner("📐 톤 DNA 자동 추출 중... (Sonnet 4.6)"):
            prompt_text = build_tone_dna_extraction_prompt(st.session_state.tone_ref_text)
            raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=8000)
            if raw:
                tone_dna = parse_json(raw)
                if tone_dna:
                    results["tone_dna"] = tone_dna
                    st.session_state.tone_dna = tone_dna
                    summary = tone_dna.get("tone_dna", {}).get("summary", "톤 추출 완료")
                    st.success(f"✅ 톤 DNA 추출 완료: {summary[:120]}")

    # 2. Diff 학습 (Before는 옵션에 따라 main 시나리오 또는 별도 업로드)
    diff_before = ""
    diff_after = st.session_state.diff_refined_text.strip() if st.session_state.diff_refined_text else ""
    if diff_after:
        if st.session_state.diff_use_main_as_before:
            diff_before = st.session_state.raw_text.strip() if st.session_state.raw_text else ""
        else:
            diff_before = st.session_state.diff_orig_text.strip() if st.session_state.diff_orig_text else ""

    if diff_before and diff_after:
        with st.spinner("🔬 작가 편집 패턴 학습 중... (Sonnet 4.6)"):
            prompt_text = build_diff_analysis_prompt(diff_before, diff_after)
            raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=8000)
            if raw:
                diff = parse_json(raw)
                if diff:
                    results["diff_analysis"] = diff
                    st.session_state.diff_analysis = diff
                    summary = diff.get("diff_analysis", {}).get("summary", "편집 패턴 학습 완료")
                    st.success(f"✅ Diff 학습 완료: {summary[:120]}")

    # 3. 분포 진단 (항상 실행)
    with st.spinner("📊 장르 메트릭 + 캐릭터 분포 진단 중... (Sonnet 4.6)"):
        prompt_text = build_distribution_diagnostic_prompt(
            st.session_state.raw_text,
            st.session_state.genre
        )
        raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=8000)
        if raw:
            dist = parse_json(raw)
            if dist:
                results["distribution_diagnostic"] = dist
                st.session_state.distribution_diagnostic = dist
                summary = dist.get("distribution_diagnostic", {}).get("summary", "분포 진단 완료")
                upgrades = dist.get("distribution_diagnostic", {}).get("auto_priority_upgrades", [])
                st.success(f"✅ 분포 진단 완료: {summary[:100]}  (자동 격상 {len(upgrades)}개)")

    # 4. Rewrite 메타 흡수
    if st.session_state.rewrite_json_text and st.session_state.rewrite_json_text.strip():
        meta = absorb_rewrite_engine_metadata(st.session_state.rewrite_json_text)
        if meta and any([
            meta.get("preserve_notes_by_seq"),
            meta.get("weak_zone_scenes"),
            meta.get("auto_priority_high"),
        ]):
            results["rewrite_metadata"] = meta
            st.session_state.rewrite_metadata = meta
            preserve_count = len(meta.get("preserve_notes_by_seq", {}))
            weak_count = len(meta.get("weak_zone_scenes", []))
            st.success(f"✅ Rewrite 메타 흡수: preserve_notes {preserve_count}개, weak_zones {weak_count}개")

    # 5. 장르 DNA 추출 (v2.1)
    if st.session_state.genre_ref_texts and any(t.strip() for t in st.session_state.genre_ref_texts):
        ref_count = len(st.session_state.genre_ref_texts)
        with st.spinner(f"🎬 장르 DNA 추출 중... 참고작 {ref_count}편 분석 (Sonnet 4.6)"):
            prompt_text = build_genre_dna_extraction_prompt(
                st.session_state.genre_ref_texts,
                st.session_state.genre
            )
            raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=8000)
            if raw:
                gd = parse_json(raw)
                if gd:
                    results["genre_dna"] = gd
                    st.session_state.genre_dna = gd
                    summary = gd.get("genre_dna", {}).get("summary", "장르 DNA 추출 완료")
                    st.success(f"✅ 장르 DNA 추출 완료: {summary[:120]}")

    return results


def run_diagnose(client):
    """Stage 1: Sonnet으로 지시 해석 + 수정 플랜 생성. v2.0/v2.1 자동 분석 사전 실행."""

    # v2.0/v2.1 — 사전 분석 자동 실행 (이미 캐시된 결과 있으면 재사용)
    pre_results = {
        "tone_dna": st.session_state.tone_dna,
        "diff_analysis": st.session_state.diff_analysis,
        "distribution_diagnostic": st.session_state.distribution_diagnostic,
        "rewrite_metadata": st.session_state.rewrite_metadata,
        "genre_dna": st.session_state.genre_dna,
    }
    # 어느 것도 없으면 사전 분석 실행
    if not any(pre_results.values()):
        pre_results = run_v2_pre_analyses(client)

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
        tone_dna=pre_results.get("tone_dna"),
        diff_analysis=pre_results.get("diff_analysis"),
        distribution_diagnostic=pre_results.get("distribution_diagnostic"),
        rewrite_metadata=pre_results.get("rewrite_metadata"),
        genre_dna=pre_results.get("genre_dna"),
    )
    raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=32000)
    if not raw:
        return None
    return parse_json(raw)


def run_revise_batch(client, batch_index: int, batch_scenes: list, total_batches: int):
    """Stage 2: Opus로 특정 배치만 집필.

    Args:
        client: Anthropic 클라이언트
        batch_index: 배치 번호 (1부터)
        batch_scenes: 이번 배치에서 처리할 씬 리스트
        total_batches: 전체 배치 수
    """
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
        batch_scenes=batch_scenes,
        batch_index=batch_index,
        total_batches=total_batches,
        tone_dna=st.session_state.tone_dna,
        diff_analysis=st.session_state.diff_analysis,
        genre_dna=st.session_state.genre_dna,
    )
    raw = call_claude(client, prompt_text, model=MODEL_WRITE, max_tokens=32000)
    if not raw:
        return None
    return parse_json(raw)


def run_revise(client):
    """Stage 2: 전체 배치 처리 (구버전 호환 — 사용하지 않는 것을 권장)."""
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
    raw = call_claude(client, prompt_text, model=MODEL_WRITE, max_tokens=32000)
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
    raw = call_claude(client, prompt_text, model=MODEL_ANALYZE, max_tokens=32000)
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

    # ── 피드백 자료 (v2.1: 선택사항으로 격하) ──
    st.markdown('<div class="rev-card-title">2. 피드백 자료 <span style="font-weight:400; color:#8E8E99; font-size:0.85rem;">(선택사항)</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">모니터 보고서·투자사 피드백·본인 메모·Rewrite Engine 진단 등 수정 방향에 도움되는 자료를 자유롭게 입력하세요. '
                '비워두어도 자동 진단이 작동합니다.</div>',
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
                    # v2.0 — 원문도 별도 저장 (메타 흡수용)
                    st.session_state.rewrite_json_text = json_source
                    st.session_state.rewrite_metadata = None  # 캐시 무효화

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
                        st.success(f"✅ 변환 완료! 지시문에 추가되었습니다 ({len(converted):,}자). v2.0 진단 시 preserve_notes·weak_zones도 자동 흡수됩니다.")
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

    # ── v2.1 신규 — 작가 톤 학습 + 장르 DNA ──
    st.markdown('<div class="rev-card-title">6. 작가 톤 학습 + 장르 DNA <span style="font-weight:400; color:#8E8E99; font-size:0.85rem;">(선택사항 · 강력 추천)</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="rev-caption">손본 시나리오로 작가 톤을 학습시키거나, 같은 장르 명작으로 장르 DNA를 추출해 강제 적용합니다. 모두 자동 분석됩니다.</div>',
                unsafe_allow_html=True)

    tab_tone, tab_diff, tab_genre = st.tabs([
        "📐 톤 레퍼런스 (작가 톤 1편)",
        "🔬 Diff 학습 (Before vs After)",
        "🎬 장르 DNA (참고작 1~3편)"
    ])

    # 탭 1: 톤 레퍼런스 (작가 손본 1편)
    with tab_tone:
        st.caption("작가가 직접 손본 시나리오 1개를 업로드하면, 작가 고유의 톤 DNA를 자동 추출해 모든 새 각색에 강제 주입합니다.")
        ref_file = st.file_uploader(
            "작가가 손본 시나리오 DOCX",
            type=["docx"],
            key="tone_ref_uploader",
            help="예: v2_3 같은 작가가 직접 다듬은 버전"
        )
        if ref_file:
            try:
                from docx import Document as _Doc
                _doc = _Doc(ref_file)
                _text = "\n".join(p.text for p in _doc.paragraphs if p.text.strip())
                st.session_state.tone_ref_text = _text
                st.session_state.tone_ref_filename = ref_file.name
                st.success(f"✅ 톤 레퍼런스 로드: {ref_file.name} ({len(_text):,}자)")
                if st.session_state.tone_dna:
                    st.info("✓ 톤 DNA가 이미 추출되어 있습니다.")
                else:
                    st.caption("→ 진단(Stage 1) 시 톤 DNA 자동 추출.")
            except Exception as e:
                st.error(f"파일 읽기 실패: {e}")
        elif st.session_state.tone_ref_filename:
            st.info(f"📎 등록됨: {st.session_state.tone_ref_filename} ({len(st.session_state.tone_ref_text):,}자)")
            if st.button("🗑️ 톤 레퍼런스 제거", key="btn_clear_tone_ref"):
                st.session_state.tone_ref_text = ""
                st.session_state.tone_ref_filename = ""
                st.session_state.tone_dna = None
                st.rerun()

    # 탭 2: Diff 학습 (Before + After)
    with tab_diff:
        st.caption("이전 버전(Before) vs 작가 손본 최신(After) 두 개를 비교해 편집 패턴(삭제·압축·통합 기준)을 자동 학습합니다.")

        use_main = st.checkbox(
            "✅ Before로 1번 원본 시나리오를 자동 사용 (권장)",
            value=st.session_state.diff_use_main_as_before,
            key="diff_use_main_chk",
            help="대부분의 경우 1번 원본을 Before로 쓰는 것이 자연스럽습니다."
        )
        st.session_state.diff_use_main_as_before = use_main

        ref2_file = st.file_uploader(
            "손본 최신 버전 DOCX (After)",
            type=["docx"],
            key="diff_refined_uploader",
            help="예: v2_3"
        )
        if ref2_file:
            try:
                from docx import Document as _Doc
                _doc = _Doc(ref2_file)
                _text = "\n".join(p.text for p in _doc.paragraphs if p.text.strip())
                st.session_state.diff_refined_text = _text
                st.session_state.diff_refined_filename = ref2_file.name
                st.success(f"✅ After 등록: {ref2_file.name} ({len(_text):,}자)")
            except Exception as e:
                st.error(f"파일 읽기 실패: {e}")
        elif st.session_state.diff_refined_filename:
            st.info(f"📎 After: {st.session_state.diff_refined_filename}")

        if not use_main:
            st.markdown("**고급 옵션 — Before 별도 업로드:**")
            orig_file = st.file_uploader(
                "Before DOCX (별도 지정)",
                type=["docx"],
                key="diff_orig_uploader",
            )
            if orig_file:
                try:
                    from docx import Document as _Doc
                    _doc = _Doc(orig_file)
                    _text = "\n".join(p.text for p in _doc.paragraphs if p.text.strip())
                    st.session_state.diff_orig_text = _text
                    st.session_state.diff_orig_filename = orig_file.name
                    st.success(f"✅ Before: {orig_file.name}")
                except Exception as e:
                    st.error(f"파일 읽기 실패: {e}")

        if st.session_state.diff_refined_text:
            if st.session_state.diff_analysis:
                st.success("✓ Diff 분석 완료. 진단 시 자동 적용됩니다.")
            else:
                st.caption("→ 진단(Stage 1) 시 자동으로 편집 패턴 학습.")
            if st.button("🗑️ Diff 자료 제거", key="btn_clear_diff"):
                st.session_state.diff_refined_text = ""
                st.session_state.diff_refined_filename = ""
                st.session_state.diff_orig_text = ""
                st.session_state.diff_orig_filename = ""
                st.session_state.diff_analysis = None
                st.rerun()

    # 탭 3: 장르 DNA (참고작 1~3편)
    with tab_genre:
        st.caption("같은 장르 명작 시나리오 1~3편을 업로드하면 장르의 본질(코믹 폭발·정보 비대칭·일상 균열 등)을 정량 메트릭으로 추출해 집필 시 강제 룰로 적용합니다.")

        # ─────────────────────────────────────────
        # STEP 1. 참고작 업로드 (메인 동선)
        # ─────────────────────────────────────────
        st.markdown('<div style="background:#FFF8DD; padding:8px 12px; border-radius:6px; '
                    'border-left:3px solid #FFCB05; margin:8px 0; font-size:0.88rem;">'
                    '<b>① 처음 사용</b> — 같은 장르 명작 1~3편 업로드 → 진단 시 장르 DNA 자동 추출'
                    '</div>', unsafe_allow_html=True)

        genre_files = st.file_uploader(
            "참고작 시나리오 DOCX (1~3편 · 같은 장르)",
            type=["docx"],
            key="genre_ref_uploader",
            accept_multiple_files=True,
            help="예: 로코 → 「조별과제」+「프로듀스 101」 / 느와르 → 「달콤한 인생」+「올드보이」"
        )
        if genre_files:
            try:
                from docx import Document as _Doc
                texts = []
                names = []
                for gf in genre_files[:3]:
                    _doc = _Doc(gf)
                    _text = "\n".join(p.text for p in _doc.paragraphs if p.text.strip())
                    texts.append(_text)
                    names.append(gf.name)
                st.session_state.genre_ref_texts = texts
                st.session_state.genre_ref_filenames = names
                st.success(f"✅ 참고작 {len(texts)}편 로드: {', '.join(names)}")
                if st.session_state.genre_dna:
                    st.info("✓ 장르 DNA 추출 완료. 진단 시 자동 적용됩니다.")
                else:
                    st.caption("→ 진단(Stage 1) 시 장르 DNA 자동 추출됩니다.")
            except Exception as e:
                st.error(f"파일 읽기 실패: {e}")
        elif st.session_state.genre_ref_filenames:
            st.info(f"📎 등록된 참고작: {', '.join(st.session_state.genre_ref_filenames)}")

        # ─────────────────────────────────────────
        # STEP 2. 추출된 DNA 다운로드 (라이브러리 보관)
        # ─────────────────────────────────────────
        if st.session_state.genre_dna:
            st.markdown('<div style="background:#EAF3DE; padding:8px 12px; border-radius:6px; '
                        'border-left:3px solid #2EC484; margin:14px 0 8px; font-size:0.88rem;">'
                        '<b>② 추출 완료 — 다음 작품에서 재사용하려면 JSON으로 보관하세요</b>'
                        '</div>', unsafe_allow_html=True)
            import json as _json
            dna_json = _json.dumps(st.session_state.genre_dna, ensure_ascii=False, indent=2)
            cdl1, cdl2 = st.columns([3, 1])
            with cdl1:
                st.download_button(
                    "💾 장르 DNA JSON 다운로드 (라이브러리 보관)",
                    data=dna_json.encode("utf-8"),
                    file_name=f"genre_dna_{st.session_state.genre.replace(' ','_')}.json",
                    mime="application/json",
                    key="dl_genre_dna",
                    help="다음 프로젝트에서 재사용하려면 이 파일을 보관하세요",
                    use_container_width=True,
                )
            with cdl2:
                if st.button("🗑️ 제거", key="btn_clear_genre_dna", use_container_width=True):
                    st.session_state.genre_ref_texts = []
                    st.session_state.genre_ref_filenames = []
                    st.session_state.genre_dna = None
                    st.rerun()

        # ─────────────────────────────────────────
        # STEP 3. 라이브러리 — 이전에 보관한 JSON 재사용 (반복 사용자)
        # ─────────────────────────────────────────
        st.markdown("---")
        with st.expander("📚 장르 DNA 라이브러리 — 이전에 추출해둔 JSON 불러오기"):
            st.caption("같은 장르로 작업한 적이 있다면, 이전에 다운로드해둔 JSON을 업로드해서 "
                       "참고작 다시 안 올리고 바로 적용할 수 있습니다.")
            dna_json_file = st.file_uploader(
                "장르 DNA JSON 업로드",
                type=["json"],
                key="genre_dna_json_uploader"
            )
            if dna_json_file:
                try:
                    import json as _json
                    raw = dna_json_file.read().decode("utf-8")
                    loaded = _json.loads(raw)
                    st.session_state.genre_dna = loaded
                    summary = loaded.get("genre_dna", {}).get("summary", "장르 DNA 로드됨")
                    st.success(f"✅ 라이브러리에서 로드: {summary[:120]}")
                except Exception as e:
                    st.error(f"JSON 로드 실패: {e}")

    # ── 실행 버튼 ──
    st.markdown("---")

    # v2.1: 입력 검증 — 시나리오 + (피드백 자료 / 손본본 / Rewrite JSON / 장르 DNA 중 1개 이상)
    has_scenario = bool(st.session_state.raw_text)
    aux_inputs = [
        bool(st.session_state.instruction.strip()),
        bool(st.session_state.diff_refined_text),
        bool(st.session_state.rewrite_json_text.strip()),
        bool(st.session_state.genre_dna or st.session_state.genre_ref_texts),
        bool(st.session_state.tone_ref_text),
    ]
    has_aux = any(aux_inputs)
    ready = has_scenario  # 시나리오만 있으면 자동 진단 모드로 진행 가능

    if not has_scenario:
        st.warning("⚠️ 1번 원본 시나리오 DOCX 업로드는 필수입니다.")
    elif not has_aux:
        st.info("ℹ️ 피드백·손본본·Rewrite JSON·장르 DNA 등 보조 자료가 없습니다. 시나리오 자체를 자동 진단해 약점을 찾습니다.")
    else:
        # 어떤 자료가 등록되어 있는지 한눈에
        active = []
        if st.session_state.instruction.strip(): active.append("📝 피드백")
        if st.session_state.diff_refined_text: active.append("🔬 Diff")
        if st.session_state.rewrite_json_text.strip(): active.append("🔗 Rewrite JSON")
        if st.session_state.tone_ref_text: active.append("📐 톤 레퍼런스")
        if st.session_state.genre_dna or st.session_state.genre_ref_texts: active.append("🎬 장르 DNA")
        st.caption(f"등록된 자료: {' · '.join(active)}")

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
            # 배치 분할 실행 (DIAGNOSE 결과 기반)
            batches = split_into_batches(
                st.session_state.diagnose_result,
                batch_size=st.session_state.batch_size
            )
            if not batches:
                st.error("수정 대상 씬이 없습니다. 진단 결과를 확인해주세요.")
            else:
                st.session_state.revise_batches = batches
                st.session_state.batch_results = {}
                st.session_state.current_batch = 0
                st.session_state.step = 2
                st.success(f"✅ {len(batches)}개 배치로 분할되었습니다. 배치별로 집필을 진행합니다.")
                st.rerun()
    with c2:
        if st.button("◀ 입력으로 돌아가기", use_container_width=True):
            st.session_state.step = 0
            st.session_state.diagnose_result = None
            st.rerun()


def _priority_badge(priority: str) -> str:
    """우선순위 배지 HTML."""
    colors = {
        "HIGH":   ("#E14444", "#FFFFFF"),
        "MEDIUM": ("#FFCB05", "#191970"),
        "LOW":    ("#8E8E99", "#FFFFFF"),
    }
    bg, fg = colors.get(priority, ("#8E8E99", "#FFFFFF"))
    return f'<span style="display:inline-block; padding:2px 8px; background:{bg}; color:{fg}; border-radius:4px; font-size:0.72rem; font-weight:800; font-family:Paperlogy,sans-serif;">{priority}</span>'


def _type_badge(t: str) -> str:
    """작업 종류 배지 HTML."""
    icons = {
        "REWRITE": "✏️",
        "ADD":     "➕",
        "DELETE":  "🗑️",
        "MERGE":   "🔗",
        "SPLIT":   "✂️",
    }
    icon = icons.get(t, "📝")
    return f'<span style="display:inline-block; padding:2px 8px; background:#EEEEF6; color:#191970; border-radius:4px; font-size:0.72rem; font-weight:700; margin-left:4px;">{icon} {t}</span>'


def show_step_2_revise():
    """Step 2: 배치 단위 순차 집필 UI."""
    batches = st.session_state.revise_batches or []
    batch_results = st.session_state.batch_results or {}

    if not batches:
        st.error("배치 정보가 없습니다. 진단 단계로 돌아가주세요.")
        if st.button("◀ 진단으로 돌아가기"):
            st.session_state.step = 1
            st.rerun()
        return

    total_batches = len(batches)
    completed_count = sum(1 for i in range(1, total_batches + 1) if i in batch_results)

    # 전체 씬 개수 / 완료 씬 개수
    total_scenes = sum(len(b["scenes"]) for b in batches)
    completed_scenes = sum(
        len(batch_results[i].get("revision_result", {}).get("revised_scenes", []))
        for i in range(1, total_batches + 1)
        if i in batch_results
    )

    # ── 헤더 ──
    st.markdown('<div class="rev-card-title">✍️ Stage 2: 배치 단위 집필 (REVISE)</div>',
                unsafe_allow_html=True)

    # 진행률 바
    progress = completed_count / total_batches if total_batches else 0
    st.progress(progress, text=f"배치 {completed_count} / {total_batches} 완료  ({completed_scenes} / {total_scenes} 씬)")

    # 배치 전략 안내
    plan = st.session_state.diagnose_result.get("revision_plan", {})
    strategy = plan.get("batch_strategy", "")
    if strategy:
        st.info(f"📋 **배치 전략:** {strategy}")

    st.markdown("---")

    # ── 배치 카드 목록 ──
    for batch in batches:
        bidx = batch["batch_index"]
        scenes = batch["scenes"]
        is_done = bidx in batch_results
        is_current = (bidx == completed_count + 1) and not is_done

        # 카드 헤더
        if is_done:
            status_icon = "✅"
            status_color = "#2EC484"
            status_text = "완료"
        elif is_current:
            status_icon = "▶️"
            status_color = "#FFCB05"
            status_text = "다음 배치"
        else:
            status_icon = "⏸️"
            status_color = "#8E8E99"
            status_text = "대기"

        with st.container():
            st.markdown(
                f'<div style="background:#FFFFFF; border:2px solid {status_color}; '
                f'border-radius:10px; padding:16px; margin-bottom:12px;">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                f'<div style="font-family:Paperlogy,sans-serif; font-weight:800; font-size:1.05rem; color:#191970;">'
                f'{status_icon} 배치 {bidx} / {total_batches}'
                f'</div>'
                f'<div style="color:{status_color}; font-weight:700; font-size:0.85rem;">{status_text}</div>'
                f'</div>'
                f'<div style="color:#8E8E99; font-size:0.85rem; margin-bottom:8px;">'
                f'{batch["priority_summary"]}  ·  {batch["type_summary"]}  ·  씬 {len(scenes)}개'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # 씬 목록 (작은 expander)
            with st.expander(f"씬 목록 ({len(scenes)}개)", expanded=is_current and not is_done):
                for sc in scenes:
                    sid = sc.get("scene_id", "")
                    pri = sc.get("priority", "MEDIUM")
                    typ = sc.get("type", "REWRITE")
                    pos = sc.get("scene_position", "")
                    func = sc.get("original_function", "")

                    st.markdown(
                        f'{_priority_badge(pri)} {_type_badge(typ)} '
                        f'<b>{sid}</b>  '
                        f'<span style="color:#8E8E99; font-size:0.85rem;">— {pos}</span>',
                        unsafe_allow_html=True
                    )
                    if func:
                        st.caption(f"플롯상 기능: {func}")

                    # 수정 항목 요약
                    items = sc.get("revision_items", [])
                    for it in items[:3]:  # 최대 3개만 표시
                        st.markdown(f"  └ *{it.get('issue','')}* → {it.get('proposed_direction','')}")
                    st.markdown("")

            # 배치 액션 버튼
            bc1, bc2, bc3 = st.columns([2, 1, 1])
            with bc1:
                if is_done:
                    # 완료된 배치 — 결과 미리보기 + 재집필
                    btn_label = f"🔄 배치 {bidx} 재집필"
                    if st.button(btn_label, key=f"rewrite_batch_{bidx}", use_container_width=True):
                        client = get_client()
                        if client:
                            with st.spinner(f"✍️ 배치 {bidx} 재집필 중... (Opus 4.6)"):
                                result = run_revise_batch(client, bidx, scenes, total_batches)
                                if result:
                                    st.session_state.batch_results[bidx] = result
                                    st.success(f"✅ 배치 {bidx} 재집필 완료")
                                    st.rerun()
                                else:
                                    st.error(f"배치 {bidx} 재집필 실패")
                elif is_current:
                    # 다음 차례 배치 — 집필 시작
                    btn_label = f"▶️ 배치 {bidx} 집필 시작"
                    if st.button(btn_label, key=f"run_batch_{bidx}", type="primary", use_container_width=True):
                        client = get_client()
                        if client:
                            with st.spinner(f"✍️ 배치 {bidx} 집필 중... ({len(scenes)}개 씬, Opus 4.6, 1~3분 소요)"):
                                result = run_revise_batch(client, bidx, scenes, total_batches)
                                if result:
                                    st.session_state.batch_results[bidx] = result
                                    st.success(f"✅ 배치 {bidx} 완료")
                                    st.rerun()
                                else:
                                    st.error(f"배치 {bidx} 집필 실패. 다시 시도해주세요.")
                else:
                    # 대기 중 (이전 배치 미완료)
                    st.button(f"⏸️ 배치 {bidx} 대기 중", disabled=True, use_container_width=True,
                              key=f"wait_batch_{bidx}")

            with bc2:
                if is_done:
                    # 결과 미리보기 토글
                    if st.button("👁️ 결과 보기", key=f"preview_batch_{bidx}", use_container_width=True):
                        st.session_state[f"show_preview_{bidx}"] = not st.session_state.get(f"show_preview_{bidx}", False)
                        st.rerun()

            with bc3:
                if is_done:
                    if st.button("🗑️ 결과 삭제", key=f"delete_batch_{bidx}", use_container_width=True):
                        del st.session_state.batch_results[bidx]
                        # 이후 배치 결과도 삭제 (순차 의존성)
                        for later_idx in range(bidx + 1, total_batches + 1):
                            st.session_state.batch_results.pop(later_idx, None)
                        st.rerun()

            # 결과 미리보기 영역
            if is_done and st.session_state.get(f"show_preview_{bidx}", False):
                br = batch_results[bidx]
                rr = br.get("revision_result", {})
                with st.container():
                    st.markdown(
                        f'<div style="background:#F7F7F5; border-left:4px solid #2EC484; '
                        f'padding:12px 16px; border-radius:0 8px 8px 0; margin-top:8px; margin-bottom:8px;">'
                        f'<b style="color:#191970;">배치 {bidx} 결과 요약</b><br/>'
                        f'<span style="color:#1A1A2E;">{rr.get("summary","(요약 없음)")}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    revised_scenes = rr.get("revised_scenes", [])
                    for sc in revised_scenes:
                        header = sc.get("scene_header", "")
                        pri = sc.get("priority", "MEDIUM")
                        typ = sc.get("type", "REWRITE")
                        with st.expander(f"{header}  [{pri} · {typ}]"):
                            col_o, col_r = st.columns([1, 1])
                            with col_o:
                                st.markdown("**📄 원본 발췌**")
                                excerpt = sc.get("original_excerpt", "")
                                st.text(excerpt if excerpt else "(원본 없음 — 신규 추가/삭제)")
                            with col_r:
                                st.markdown("**✏️ 수정본**")
                                content = sc.get("revised_content", "")
                                st.text(content if content else "(삭제됨)")

                            notes = sc.get("revision_notes", {})
                            if notes:
                                st.markdown("---")
                                st.markdown(f"**변경:** {notes.get('what_changed','')}")
                                st.markdown(f"**보존:** {notes.get('what_preserved','')}")

    st.markdown("---")

    # ── 모든 배치 완료 시 다음 단계 ──
    all_done = (completed_count == total_batches)

    if all_done:
        st.success(f"🎉 모든 배치 완료! 총 {completed_scenes}개 씬이 수정되었습니다.")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        if st.button("✅ Stage 3: 검증 시작 (VERIFY)",
                     disabled=not all_done, use_container_width=True, type="primary"):
            # 모든 배치 결과 통합
            all_results = [batch_results[i] for i in range(1, total_batches + 1) if i in batch_results]
            merged = merge_batch_results(all_results)
            st.session_state.revise_result = merged

            client = get_client()
            if client:
                with st.spinner("✅ 통합 수정본 검증 중... (Sonnet 4.6)"):
                    result = run_verify(client)
                    if result:
                        st.session_state.verify_result = result
                        st.session_state.step = 3
                        st.rerun()
                    else:
                        st.error("검증 실패. 다시 시도해주세요.")
    with c2:
        # 모두 한 번에 (남은 배치 자동 순차 실행)
        remaining = total_batches - completed_count
        if remaining > 0:
            if st.button(f"⏩ 남은 {remaining}개 자동 진행", use_container_width=True):
                client = get_client()
                if client:
                    progress_bar = st.progress(0, text="배치 자동 실행 중...")
                    for i, batch in enumerate(batches):
                        bidx = batch["batch_index"]
                        if bidx in batch_results:
                            continue
                        progress_bar.progress(
                            (completed_count + (i - completed_count + 1)) / total_batches,
                            text=f"배치 {bidx} 집필 중... ({len(batch['scenes'])}개 씬)"
                        )
                        result = run_revise_batch(client, bidx, batch["scenes"], total_batches)
                        if result:
                            st.session_state.batch_results[bidx] = result
                        else:
                            st.error(f"배치 {bidx}에서 실패. 중단합니다.")
                            break
                    progress_bar.empty()
                    st.rerun()
    with c3:
        if st.button("◀ 진단으로", use_container_width=True):
            st.session_state.step = 1
            st.session_state.revise_batches = None
            st.session_state.batch_results = {}
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
            is_historical = (st.session_state.period_key != "(현대)")
            docx_bytes = create_revised_docx(
                st.session_state.revise_result,
                title=title,
                genre=genre,
                original_text=st.session_state.raw_text,
                fact_based=st.session_state.fact_based,
                historical=is_historical,
                historical_type=st.session_state.historical_type if is_historical else "",
            )
            st.download_button(
                "📄 수정본 (DOCX)",
                data=docx_bytes,
                file_name=get_report_filename(title, "revised"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_revised",
                help="원본 + 수정된 씬을 통합한 최종 시나리오 (한국 표준 서식)",
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
                "engine": "BLUE JEANS REVISE ENGINE v2.1",
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
    'BLUE JEANS PICTURES · REVISE ENGINE v2.1  ·  '
    'Powered by Claude Opus 4.6 + Sonnet 4.6'
    '</div>',
    unsafe_allow_html=True,
)
