"""
👖 BLUE JEANS Revise Engine — Market Revise Pack
────────────────────────────────────────────────────────────
VERSION: v1.0.0
BUILD DATE: 2026-10-25
근거 자료: Idea Engine Market Lens Pack v1.1 (market_lens_pack.py, VN 자료 기준일 2026-10-23)

Revise Engine 전용 "원고 단위 시장 규칙" 모듈.
market_lens_pack.py(시장 분석 원본)는 고치지 않고 그대로 두고,
각색 단계에 필요한 두 가지만 여기서 관리한다.

  1. redlines  — 렌즈에 근거가 있는 규제·기피 항목.
                 각색 프롬프트의 [시장 레드라인] 블록과 규제 재검사에 쓴다.
                 근거 등급을 함께 단다 (VN은 렌즈 출처가 있어 VERIFIED,
                 ID·JP는 렌즈에 출처 표기가 없어 INFERENCE).
  2. checklist — 고증 확인 항목. 사실을 단정하지 않고 "확인할 것"만 적는다.
                 판정은 모두 VERIFICATION_REQUIRED.
                 ★ 프롬프트에 넣지 않는다 (확인되지 않은 고증을 모델이 지어낼 위험).
                 각색 완료 후 리포트에만 출력한다.

checklist의 씬 탐지는 키워드 기반 후보 탐지다. 해당 씬을 찾아 붙이기만 하고
판정은 하지 않는다. 탐지되지 않았다고 문제가 없다는 뜻이 아니다.
────────────────────────────────────────────────────────────
"""

import re

try:
    from market_lens_pack import MARKET_LABELS as _LENS_LABELS
except ImportError:  # 공유 모듈이 없을 때도 Revise가 멈추지 않도록
    _LENS_LABELS = {
        "KR": ("한국", "🇰🇷"),
        "JP": ("일본", "🇯🇵"),
        "ID": ("인도네시아", "🇮🇩"),
        "VN": ("베트남", "🇻🇳"),
    }

MARKET_REVISE_PACK_VERSION = "v1.0.0"

MARKET_CODES = ["KR", "JP", "ID", "VN"]

GRADE_VERIFIED = "VERIFIED"
GRADE_INFERENCE = "INFERENCE"
GRADE_CREATIVE = "CREATIVE_JUDGMENT"
GRADE_VERIFY_REQ = "VERIFICATION_REQUIRED"
VALID_GRADES = {GRADE_VERIFIED, GRADE_INFERENCE, GRADE_CREATIVE, GRADE_VERIFY_REQ}


# ═══════════════════════════════════════════════════════════════
# 키워드 탐지 도우미
# ═══════════════════════════════════════════════════════════════

# 베트남어 전용 문자 (기본 라틴 밖의 글자). 성조 부호가 붙은 글자는
# Latin Extended Additional 블록(U+1EA0~U+1EF9)과 일부 Latin-1/Extended-A에 있다.
VN_SPECIAL_CHARS = (
    "ăâđêôơưĂÂĐÊÔƠƯ"
    "àáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ"
    "ÀÁẢÃẠẰẮẲẴẶẦẤẨẪẬÈÉẺẼẸỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌỒỐỔỖỘỜỚỞỠỢÙÚỦŨỤỪỨỬỮỰỲÝỶỸỴ"
)
_VN_CHAR_RE = re.compile("[" + re.escape(VN_SPECIAL_CHARS) + "̀-̣̃̉]")
_KANA_RE = re.compile(r"[぀-ヿㇰ-ㇿ]")
_LATIN_WORD_RE = re.compile(r"\b[A-Za-z][a-z]{2,}\b")
_YEAR_RE = re.compile(r"(?<!\d)(1[6-9]\d\d|20[0-4]\d)(?!\d)")


def has_vietnamese_chars(text: str) -> bool:
    """베트남어 성조·특수 문자가 하나라도 있으면 True."""
    return bool(text) and bool(_VN_CHAR_RE.search(text))


def has_kana(text: str) -> bool:
    """히라가나·가타카나가 하나라도 있으면 True."""
    return bool(text) and bool(_KANA_RE.search(text))


def _kw(*words):
    return {"type": "keywords", "words": list(words)}


# ═══════════════════════════════════════════════════════════════
# 시장별 원고 규칙
# ═══════════════════════════════════════════════════════════════

MARKET_REVISE_RULES = {

    # ── 베트남 ────────────────────────────────────────────────
    # 근거: VN Market Lens [법률·심의·규제] (자료 기준일 2026-10-23)
    "VN": {
        "redlines": [
            {
                "id": "VN-R1",
                "rule": "영화법 05/2022/QH15 제9조 금지 항목 — 국가 통합 훼손, 역사 왜곡, "
                        "종교 모욕·불법 종교활동 선전, 사생활 공개, 아동 권리 침해, 성차별",
                "basis": "V·S5",
                "grade": GRADE_VERIFIED,
            },
            {
                "id": "VN-R2",
                "rule": "등급 기준 05/2023/TT-BVHTTDL T16 — 자해·자살은 간접적으로, 약하게, 짧게. "
                        "공포는 강도가 높아도 짧게",
                "basis": "V·S6",
                "grade": GRADE_VERIFIED,
            },
            {
                "id": "VN-R3",
                "rule": "등급 기준 05/2023/TT-BVHTTDL T18 — 강한 폭력은 허용하되 과도한 수준 미만. "
                        "노골적 성행위는 원칙적으로 불가하며, 서사상 필요하고 짧은 경우만 예외",
                "basis": "V·S6",
                "grade": GRADE_VERIFIED,
            },
            {
                "id": "VN-R4",
                "rule": "등급 C(상영 불가) — 제9조 위반, 또는 어느 기준이든 과도한 수준",
                "basis": "V·S6",
                "grade": GRADE_VERIFIED,
            },
            {
                "id": "VN-R5",
                "rule": "영화국장 공문(2026-06) — 과도한 폭력·유혈·미신 요소에 대한 신중 권고 "
                        "(새 규정이 아닌 권고)",
                "basis": "V·S7",
                "grade": GRADE_VERIFIED,
            },
        ],
        "checklist": [
            {"item": "인물 호칭 — 가족·연령·지위에 따른 호칭이 장면마다 일관되는가",
             "detect": _kw("언니", "오빠", "누나", "형님", "할머니", "할아버지", "어머니", "아버지",
                           "엄마", "아빠", "아저씨", "아주머니", "이모", "고모", "삼촌", "선생",
                           "아가씨", "부인", "마님", "어르신",
                           " anh ", " chị ", " em ", " ông ", " bà ", " cô ", " chú ", " bác ",
                           " má ", " mẹ ", " ba ")},
            {"item": "지역 언어 — 북·중·남부 방언 설정이 인물 출신지와 맞는가",
             "detect": _kw("하노이", "호찌민", "호치민", "사이공", "후에", "다낭", "북부", "중부", "남부",
                           "방언", "사투리", "말투", "억양", "Hà Nội", "Sài Gòn", "Huế")},
            {"item": "지명·공간 — 실제 지명을 쓴 경우 위치·시대가 맞는가",
             "detect": _kw("하노이", "호찌민", "호치민", "사이공", "후에", "다낭", "호이안", "메콩",
                           "하이퐁", "나트랑", "냐짱", "달랏", "껀터", "하롱", "쩌런", "촐론",
                           "Hà Nội", "Sài Gòn", "Huế", "Đà Nẵng", "Hội An", "Chợ Lớn")},
            {"item": "의례·신앙 — 장례, 초혼, 제례, 민속 신앙 묘사의 고증",
             "detect": _kw("장례", "초혼", "제사", "제례", "제단", "위패", "사당", "향을", "향 ",
                           "지전", "절을", "무당", "주문", "부적", "의식", "영정", "곡소리", "상복",
                           "사원", "법당", "혼백")},
            {"item": "현대사·역사 연도 — 실존 인물·사건이 등장하면 연도와 직위가 맞는가",
             "detect": {"type": "year_or_keywords",
                        "words": ["식민", "프랑스", "전쟁", "독립", "학살", "총독", "혁명"]}},
            {"item": "베트남어 표기 — 인명·지명의 성조 부호(예: Nguyệt, Dũng, Tiểu Linh)가 "
                     "원고 전체에서 같은 표기로 유지되는가",
             "detect": {"type": "vietnamese_chars"}},
        ],
    },

    # ── 인도네시아 ─────────────────────────────────────────────
    # 근거: ID Market Lens [문화 제약]. 렌즈에 출처 표기가 없으므로 INFERENCE.
    "ID": {
        "redlines": [
            {"id": "ID-R1", "rule": "LSF(영화검열위원회) 통과 필수",
             "basis": "ID 렌즈 [문화 제약]", "grade": GRADE_INFERENCE},
            {"id": "ID-R2", "rule": "이슬람을 직설적으로 비판하는 묘사 회피 (우호적·중립적 묘사는 가능)",
             "basis": "ID 렌즈 [문화 제약]", "grade": GRADE_INFERENCE},
            {"id": "ID-R3", "rule": "노골적 성표현, LGBT 노출, 음주·도박 미화 회피",
             "basis": "ID 렌즈 [문화 제약]", "grade": GRADE_INFERENCE},
        ],
        "checklist": [
            {"item": "자바 케자웬 신앙·VOC 역사 묘사의 고증",
             "detect": _kw("케자웬", "kejawen", "Kejawen", "VOC", "네덜란드", "바타비아", "Batavia",
                           "두쿤", "dukun", "Dukun", "주술", "의식", "제물", "식민")},
            {"item": "자바 / 자카르타 / 외도서 지역 설정의 언어·관습 일관성",
             "detect": _kw("자바", "자카르타", "Jakarta", "수마트라", "발리", "술라웨시", "칼리만탄",
                           "보르네오", "족자", "족자카르타", "반둥", "수라바야", "타라칸", "Tarakan")},
            {"item": "인니어 인명·지명 표기 일관성",
             "detect": {"type": "latin_words"}},
        ],
    },

    # ── 일본 ──────────────────────────────────────────────────
    # 근거: JP Market Lens [기피 사항]. 렌즈에 출처 표기가 없으므로 INFERENCE.
    "JP": {
        "redlines": [
            {"id": "JP-R1", "rule": "한국식 사회파의 직설적 비판 메시지",
             "basis": "JP 렌즈 [기피 사항]", "grade": GRADE_INFERENCE},
            {"id": "JP-R2", "rule": "자극적 폭력, 슬래셔, 노골적 성표현",
             "basis": "JP 렌즈 [기피 사항]", "grade": GRADE_INFERENCE},
            {"id": "JP-R3", "rule": "정치 직설, 특히 한일 관계를 직접 겨냥하는 묘사",
             "basis": "JP 렌즈 [기피 사항]", "grade": GRADE_INFERENCE},
        ],
        "checklist": [
            {"item": "경어 체계와 인물 관계의 일관성",
             "detect": _kw("상,", "상.", "상!", "상?", "사마", "센세", "선배", "센빠이", "센파이",
                           "군,", "짱", "님,", "さん", "様", "先生", "先輩", "くん", "ちゃん")},
            {"item": "일본어 인명·지명 표기 일관성",
             "detect": {"type": "kana_or_keywords",
                        "words": ["도쿄", "오사카", "교토", "후쿠오카", "삿포로", "나고야", "요코하마",
                                  "고베", "센다이", "히로시마"]}},
        ],
    },

    # ── 한국 ──────────────────────────────────────────────────
    # 렌즈: "정치 검열 거의 없음, 표현 수위 폭넓음" → redlines 없음.
    # 기존 Revise 동작 그대로. 시장 검증 섹션에는 Rewrite regulation_flags만 표시.
    "KR": {
        "redlines": [],
        "checklist": [],
    },
}


# ═══════════════════════════════════════════════════════════════
# 조회 함수
# ═══════════════════════════════════════════════════════════════

def normalize_market_code(code) -> str:
    """'vn', '베트남', 'VN ' 같은 입력을 'VN'으로 정리. 모르면 빈 문자열."""
    if not code:
        return ""
    c = str(code).strip()
    up = c.upper()
    if up in MARKET_CODES:
        return up
    for k, (label, _flag) in _LENS_LABELS.items():
        if c == label:
            return k
    return ""


def get_market_label(code: str, with_flag: bool = False) -> str:
    """시장 코드 → '베트남' (with_flag면 '🇻🇳 베트남'). 없으면 '없음'."""
    code = normalize_market_code(code)
    if not code:
        return "없음"
    label, flag = _LENS_LABELS.get(code, (code, ""))
    return f"{flag} {label}".strip() if with_flag else label


def get_redlines(code: str) -> list:
    code = normalize_market_code(code)
    return [dict(r) for r in MARKET_REVISE_RULES.get(code, {}).get("redlines", [])]


def get_checklist_items(code: str) -> list:
    code = normalize_market_code(code)
    return [dict(c) for c in MARKET_REVISE_RULES.get(code, {}).get("checklist", [])]


def market_has_rules(code: str) -> bool:
    code = normalize_market_code(code)
    rules = MARKET_REVISE_RULES.get(code, {})
    return bool(rules.get("redlines") or rules.get("checklist"))


# ═══════════════════════════════════════════════════════════════
# 고증 체크리스트 — 씬 번호만 찾아 붙인다 (판정 없음)
# ═══════════════════════════════════════════════════════════════

def _scene_sort_key(k: str):
    m = re.search(r"(\d+)(?:-(\d+))?", k or "")
    if not m:
        return (10 ** 6, 0, k)
    return (int(m.group(1)), int(m.group(2) or 0), k)


def _detect_in_text(detect: dict, text: str) -> bool:
    if not text or not isinstance(detect, dict):
        return False
    t = detect.get("type")
    padded = f" {text} "
    if t == "keywords":
        return any(w in padded for w in detect.get("words", []))
    if t == "vietnamese_chars":
        return has_vietnamese_chars(text)
    if t == "kana_or_keywords":
        return has_kana(text) or any(w in text for w in detect.get("words", []))
    if t == "year_or_keywords":
        return bool(_YEAR_RE.search(text)) or any(w in text for w in detect.get("words", []))
    if t == "latin_words":
        # 씬 헤더의 INT./EXT./DAY/NIGHT 같은 시나리오 표기는 제외하고 본다
        stripped = re.sub(r"\b(INT|EXT|DAY|NIGHT|CUT|TO|INSERT|CONT|V\.O|O\.S)\b\.?", " ", text,
                          flags=re.IGNORECASE)
        return bool(_LATIN_WORD_RE.search(stripped))
    return False


def build_localization_checklist(code: str, scene_text_map: dict) -> list:
    """각색본 기준 고증 체크리스트.

    Args:
        code: 시장 코드 (VN/ID/JP/KR)
        scene_text_map: {"S#3": "씬 전문", ...} — 각색 완료본 기준

    Returns:
        [{"item": "...", "scenes": ["S#3", ...], "grade": "VERIFICATION_REQUIRED",
          "detection_note": "..."}]
        KR이거나 규칙이 없으면 빈 리스트.
    """
    items = get_checklist_items(code)
    if not items:
        return []
    scene_text_map = scene_text_map or {}
    out = []
    for it in items:
        hits = [k for k, txt in scene_text_map.items() if _detect_in_text(it.get("detect"), txt)]
        hits = sorted(set(hits), key=_scene_sort_key)
        out.append({
            "item": it.get("item", ""),
            "scenes": hits,
            "grade": GRADE_VERIFY_REQ,
            "detection_note": (
                "키워드 기반 후보 씬입니다. 판정은 하지 않았습니다."
                if hits else
                "자동 탐지된 씬이 없습니다. 원고 전체에서 확인이 필요합니다."
            ),
        })
    return out


def format_redlines_for_prompt(code: str) -> list:
    """프롬프트용 레드라인 문자열 리스트. 근거 표기 포함."""
    lines = []
    for r in get_redlines(code):
        lines.append(f"- [{r['id']}] {r['rule']} (근거: {r['basis']} · {r['grade']})")
    return lines
