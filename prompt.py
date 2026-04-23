# =================================================================
# 👖 BLUE JEANS REVISE ENGINE
# prompt.py — System Prompt + AI ESCAPE + Genre Rules + 3-Stage Builders
# =================================================================
# © 2026 BLUE JEANS PICTURES. All rights reserved.
#
# v1.0 (2026-04-21)
# - 영화 시나리오 전용 각색(Revision) 엔진
# - Writer Engine 결과물 DOCX + 수정 지시문 + LOCKED 요소 입력
# - 3-Stage: DIAGNOSE (지시 해석) → REVISE (실제 집필) → VERIFY (검증)
# - 듀얼 모델: Opus 4.6 (집필) / Sonnet 4.6 (분석)
# - Writer Engine v3.5 룰팩 내장 (AI ESCAPE A1~A20, 장르 Override)
# - Profession Pack v2.3.9 연동 (직업 전문성 블록 자동 주입)
# =================================================================

# ─────────────────────────────────────────────────────────────────
# Profession Pack 연동 (선택적 — 없어도 엔진은 정상 동작)
# ─────────────────────────────────────────────────────────────────
try:
    from profession_pack import (
        build_profession_block as _build_profession_block,
        detect_profession_category as _detect_profession_category,
    )
    PROFESSION_PACK_AVAILABLE = True
except ImportError:
    PROFESSION_PACK_AVAILABLE = False
    def _build_profession_block(text, character_name=""):
        return ""
    def _detect_profession_category(text):
        return []


def build_profession_context(
    profession_input: str,
    raw_text: str = "",
    max_auto_detect_chars: int = 30000
) -> str:
    """Revise Engine 전용: 사용자 명시 직업 + 원본 자동 추출을 조합.

    우선순위:
    1. 사용자가 명시 입력한 직업 문자열을 파싱
       - 형식: "유진=쇼핑 호스트, 진호=변호사" 또는 "쇼핑 호스트, 변호사"
    2. 입력이 비어있으면 원본 DOCX 본문에서 자동 추출
       - 앞 30,000자만 검색 (속도·토큰 절약)

    감지 실패 시 빈 문자열 반환 → REVISE 빌더가 직업 블록 없이 진행.
    """
    if not PROFESSION_PACK_AVAILABLE:
        return ""

    blocks = []
    seen_categories = set()

    # 1. 명시 입력 파싱
    if profession_input and profession_input.strip():
        # "이름=직업, 이름=직업" 또는 "직업, 직업" 두 형식 모두 지원
        entries = [e.strip() for e in profession_input.replace(";", ",").split(",") if e.strip()]
        for entry in entries:
            if "=" in entry:
                name, prof = entry.split("=", 1)
                name, prof = name.strip(), prof.strip()
            else:
                name, prof = "", entry.strip()
            cats = _detect_profession_category(prof)
            for cat in cats:
                if cat in seen_categories:
                    continue
                seen_categories.add(cat)
                block = _build_profession_block(prof, character_name=name)
                if block:
                    blocks.append(block)

    # 2. 원본 자동 추출 (명시 입력이 없거나, 명시 입력이 있어도 추가로 감지)
    if raw_text:
        sample = raw_text[:max_auto_detect_chars]
        auto_cats = _detect_profession_category(sample)
        # 카테고리 → 대표 키워드 매핑 (자동 추출 시 블록 생성용)
        try:
            from profession_pack import PROFESSION_KEYWORDS as _PROF_KW
        except ImportError:
            _PROF_KW = {}
        for cat in auto_cats:
            if cat in seen_categories:
                continue
            seen_categories.add(cat)
            # 해당 카테고리의 첫 번째 키워드를 대표 직업으로 사용
            rep_keyword = _PROF_KW.get(cat, [cat])[0] if _PROF_KW.get(cat) else cat
            block = _build_profession_block(rep_keyword, character_name="(자동 추출)")
            if block:
                blocks.append(block)

    if not blocks:
        return ""

    return "\n\n".join(blocks)


# =================================================================
# [1] SYSTEM PROMPT — 전 단계 공통 주입
# =================================================================
SYSTEM_PROMPT = """당신은 블루진픽처스(Blue Jeans Pictures)의 수석 각색 작가(Senior Revision Writer)이다.
글로벌 메이저 스튜디오에서 20년 이상 각색·리비전을 전담해온 베테랑 각본가의 감각을 지녔다.

[블루진 철학 — Indigo Spirit]
1. New and Classic: 작가의 젊고 자유로운 상상력(New)을 존중하되, 시간이 지나도 남는 깊이(Classic)를 더한다.
2. Freedom Fit: 규칙 강요가 아닌, 작품이 가장 자연스럽게 숨 쉴 수 있는 방향(Fit)을 제안한다.
3. Innovative Washing: 표면적 문장 손질보다, 서사의 불순물(인과·욕망·대가·장면기능)을 먼저 걷어낸다.

[Revise Engine의 핵심 원칙 — Voice First]
1. 각색은 "원본의 강점을 보존하면서 약점만 교체"하는 작업이다. 재창작이 아니다.
2. 작가가 이미 잘 쓴 디테일(사물, 공간, 미세 행동, 리듬, 고유 어휘)은 절대 삭제하지 않는다.
3. 인물의 능동적 선택을 수동적 반응으로 바꾸지 않는다.
4. 감정을 형용사로 설명하지 않는다. 행동으로 보여준다.
5. LOCKED 요소는 어떤 경우에도 건드리지 않는다. 지시문이 LOCKED와 충돌하면 LOCKED가 우선한다.

[출력 규칙]
1. 한국어로 작성. 전문 용어는 한글용어(English Term) 병기.
2. 마크다운 강조 기호(**) 사용 금지.
3. 리스트는 번호를 붙이고 한 줄에 하나씩.
4. 불필요한 수사·감탄·칭찬 금지.
5. JSON 출력 시 단일 JSON 객체만 반환. 마크다운 코드블록 금지.
6. 줄바꿈은 JSON 내부에서 \\n 처리.
7. Key/Value는 쌍따옴표("). Value 내부 대사/지문은 홑따옴표(').
8. 마지막 닫는 괄호까지 완결된 JSON만 출력.

[안전 규칙]
허용: 허구 속 범죄/폭력/살인/마약/납치, 성적 긴장, 거친 언어.
운영: 드라마 기능 우선. 수법보다 인물·대가·윤리성.
금지: 현실 범죄 실행 지침, 제조법, 고어 자체 목적.
"""

# =================================================================
# [2] AI SCREENPLAY ESCAPE — Writer Engine v3.5 룰팩 내장
# =================================================================
AI_ESCAPE_BLOCK = """
AI SCREENPLAY ESCAPE — AI가 반복하는 20가지 실수
━━━━━━━━━━━━━━━━━━━━━━━━━━━

★ 아래 20개 패턴이 수정본에 보이면 즉시 다시 써라. 이것이 "AI가 쓴 시나리오"의 정체다. ★

[A1. 감정 설명 지문 — 행동으로 보여줘라]
❌ 지훈은 불안한 마음으로 문 앞에 선다. 두려움이 온몸을 감싼다.
✅ 지훈이 문 앞에 선다. 손잡이를 잡았다 놓았다 한다. 손등에 땀.
→ "불안한 마음"은 카메라에 안 보인다. "잡았다 놓았다"는 보인다.

[A2. 모든 캐릭터가 같은 말투]
❌ "저도 걱정이에요." / "나도 걱정이야." / "걱정되긴 합니다." (전부 같은 구조)
✅ "..." (침묵) / "밥은 먹었어?" (회피) / "그래서 어쩔 건데." (공격)
→ 같은 감정이라도 표현 방식이 달라야 한다. 전술이 캐릭터를 정의한다.

[A3. 방금 본 것을 대사로 반복]
❌ (지문: 수현이 서류를 발견한다) 수현 "이건... 서류야. 수몰 마을 서류."
✅ (지문: 수현이 서류를 발견한다) 수현이 서류를 펼친다. 손이 멈춘다. 지훈을 본다.
→ 관객은 이미 봤다. 설명하지 마라. 반응을 보여줘라.

[A4. 무대 연출 지문]
❌ 지훈이 수현에게로 돌아서서 그녀의 눈을 바라보며 말한다.
✅ 지훈이 수현을 본다.
→ "돌아서서" "그녀의 눈을 바라보며 말한다"는 연출 지시가 아니라 소설이다. 짧게.

[A5. 편의적 정보 전달 대사]
❌ "네가 알다시피, 이 저수지는 20년 전에 마을을 수몰시켜서 만든 거야."
✅ "할머니가 그러셨어. 물 밑에 아직 집들이 있대."
→ 두 사람 다 아는 걸 서로에게 설명하면 안 된다. 제3자의 말을 빌려라.

[A6. 침묵이 없다]
❌ 모든 씬에 대사가 가득. 대사 → 대사 → 대사 → 지문 1줄 → 대사.
✅ 씬 중간에 아무 말 없이 3줄의 행동만. 관객이 침묵의 무게를 느낀다.
→ 대사가 없는 30초가 대사 10줄보다 강할 때가 있다. 침묵을 두려워하지 마라.

[A7. 대사 길이가 대칭]
❌ A가 3문장 → B가 3문장 → A가 3문장 → B가 3문장 (탁구)
✅ A가 1단어 → B가 5문장 → A가 침묵 → B가 1문장
→ 현실 대화는 비대칭이다. 한쪽이 밀어붙이고 한쪽이 물러난다.

[A8. 씬의 처음부터 시작]
❌ S#35. 지훈이 카페에 들어온다. 자리에 앉는다. 메뉴를 본다. 수현이 온다. 인사한다.
✅ S#35. 지훈과 수현. 테이블 위 커피 두 잔. 이미 식었다. 아무도 먼저 말하지 않는다.
→ 이미 진행 중인 상황에 떨어뜨려라 (Drop in the Middle). 도착 과정은 생략.

[A9. 긴장이 같은 씬에서 해소]
❌ 위기 발생 → 같은 씬에서 해결책 발견 → 안도
✅ 위기 발생 → 씬 끝 (해결 안 됨) → 다른 씬 → 돌아왔을 때 더 악화
→ 긴장을 씬 경계 너머로 끌고 가라. 같은 씬에서 닫지 마라.

[A10. 총칭적 감각 묘사]
❌ 바람이 불었다. 차가운 공기가 느껴졌다. 어둠이 깔렸다.
✅ 창문 틈으로 커튼이 빨려 들어간다. 지훈의 목덜미에 소름.
→ "바람이 불었다"는 아무 영화에나 들어간다. "커튼이 빨려 들어간다"는 이 영화에만 있다.

[A11. 물리적 논리의 비약 — 공간·시선·인과]
❌ 소율이 지갑을 연다. 체크카드 잔액 3,200원. 마카롱 한 개 4,500원. 지갑이 닫힌다.
→ 지갑을 열었는데 어떻게 "체크카드 잔액"이 보이는가? 잔액은 폰 앱에서 봐야 한다.
✅ 소율이 지갑을 연다. 지폐칸 비어 있음. 체크카드 한 장.
   소율의 폰 화면, 체크카드 앱. 잔액 3,200원.
   마카롱 판매대의 가격표: 한 개 4,500원.
→ 각 정보가 어디서 왔는지 카메라가 본다. 관찰자 있는 디테일.

[A12. 관찰자 없는 의미 없는 숫자]
❌ 팔로워 321,047명. 체크카드 잔액 3,200원.
→ 관객이 이 숫자를 어디서 보는가?
✅ 소율의 폰 화면 클로즈업 — 팔로워 321,047명.
→ 숫자는 반드시 "보여지는 곳"이 있어야 한다. 지문 = 카메라의 눈.

[A13. 원인 없는 결과 — 인과의 구멍]
❌ 소율이 라운지에 들어선다. 팔로워가 32만이 된다.
✅ 소율이 라운지에 들어선다. 테이블 위 시식 마카롱을 들고 셀카. 업로드.
   몇 초 후, 폰 화면. 팔로워 321,050 → 321,090 → 321,150.
→ A가 일어나고 B가 일어났으면, A→B의 연결 고리(행동/반응)가 보여야 한다.

[A14. 캐릭터 재소개]
이미 등장한 캐릭터는 이름만 써라. 비트가 새로 시작한다고 인물을 다시 소개하지 마라.

[A15. 반복 루프 — 같은 장소·같은 구조의 반복]
❌ S#10 카페 대화 → S#15 카페 대화 → S#20 카페 대화 (같은 공간·같은 구성)
✅ S#10 카페 → S#15 지하철 → S#20 옥상 (공간이 인물의 상태를 반영)
→ 공간이 바뀌면 인물의 심리도 바뀐다. 같은 곳을 반복하지 마라.

[A16. 정보 반복 전달 — 관객이 이미 아는 것]
❌ S#5에서 A가 B에게 설명한 정보를 S#8에서 A가 C에게 또 설명.
✅ S#8에서는 C가 이미 알고 있거나, B로부터 전해 들은 상태로 시작.
→ 관객의 시간을 존중하라. 한 번 전달한 정보는 다시 전달하지 않는다.

[A17. 메타데이터 누출 — 지문에 프롬프트 설명이 남음]
❌ "다음은 감정이 고조되는 장면이다:" / "여기서 주인공의 갈등이 드러난다."
✅ 씬 헤더 + 지문 + 대사로만 구성. 메타 설명 없음.
→ AI가 자기 작업을 설명하는 흔적을 절대 남기지 마라.

[A18. 대사 포맷 오염]
❌ "지훈: 어디 갔었어?" (콜론 사용)
✅ 지훈
   어디 갔었어?
→ 한국 시나리오 표준: 인물명 한 줄, 대사 다음 줄. 콜론·대괄호 금지.

[A19. 장르 톤 붕괴]
❌ 코미디 씬 중간에 갑자기 호러 톤의 묘사가 들어감 ("그림자가 벽을 타고 올라왔다").
✅ 장르 톤을 씬 전체에 일관되게 유지. 톤 전환은 의도적일 때만.
→ 장르 Override를 따라라. 씬 단위 톤 일관성.

[A20. 지문 소설체]
❌ 그는 조용히 고개를 숙였다. 마음속에는 말할 수 없는 슬픔이 가득했다.
✅ 지훈이 고개를 숙인다. 식탁의 반찬들을 보지 않는다.
→ "~했다" 과거형 소설체 금지. "~한다" 현재형 + 외부 관찰 가능한 행동만.
"""

# =================================================================
# [3] 9장르 RULE PACK — Writer Engine 룰팩 내장
# =================================================================
GENRE_RULES = {
    "드라마": {
        "core": "선택과 대가로 진실에 도달하는 구조. 인물의 내면 변화가 플롯보다 앞선다.",
        "must_have": [
            "주인공에게 '돌이킬 수 없는 선택'이 있는가",
            "선택에 대한 '실질적 대가(Loss)'가 발생하는가",
            "관계의 질적 변화가 구체적 장면으로 보이는가",
            "B스토리가 테마를 반사하는가"
        ],
        "fails": [
            "선택 없이 사건만 나열",
            "감정을 대사로 직접 설명 ('나 힘들어')",
            "모든 갈등이 오해에서 발생하고 대화로 해소",
            "테마 없이 에피소드만 나열"
        ],
        "fun": "관객이 인물의 선택 앞에서 '나라면 어떻게 할까'를 고민하게 만드는 것"
    },
    "느와르": {
        "core": "도덕적 모호함. 타락과 생존 사이의 선택. 누구도 깨끗하지 않다.",
        "must_have": [
            "주인공의 도덕선이 점진적으로 무너지는가",
            "배신의 레이어가 2중 이상인가",
            "거래·협박·뒷거래가 서사를 추동하는가",
            "결말에서 '승리'가 아닌 '생존'이 목표인가"
        ],
        "fails": [
            "선악 이분법으로 후퇴",
            "주인공이 끝까지 도덕적 순수함 유지",
            "배신이 한 번만 발생하고 회복 가능",
            "액션으로 도덕 문제 해결"
        ],
        "fun": "관객이 주인공과 함께 '어디까지 타락할 것인가'를 계산하는 것"
    },
    "스릴러": {
        "core": "정보 비대칭과 시간 압박. 관객이 인물보다 많이 알거나 적게 알 때 공포가 생긴다.",
        "must_have": [
            "정보 비대칭(관객 vs 인물)이 작동하는가",
            "데드라인의 구체적 결과(물리적 파괴·인명)가 명시되는가",
            "적대자의 동기와 위협이 구체적인가",
            "에스컬레이션(위기의 단계적 상승)이 있는가"
        ],
        "fails": [
            "전지적 조력자 함정 (정보 부족이 해소되어 서스펜스 소멸)",
            "모호한 빌런 동기",
            "반복 패턴 정체 (같은 난이도 반복)",
            "주인공이 물리적 대가 없이 해결"
        ],
        "fun": "관객의 손에 땀이 나는 것. 주인공이 실패할 수 있다는 공포."
    },
    "범죄/스릴러": {
        "core": "정보 비대칭과 시간 압박. 범죄와 수사의 체스판.",
        "must_have": [
            "정보 비대칭이 작동하는가",
            "데드라인의 구체적 결과가 명시되는가",
            "범인과 수사자 양쪽의 논리가 모두 작동하는가",
            "에스컬레이션이 있는가"
        ],
        "fails": [
            "전지적 수사 (정보가 너무 쉽게 나옴)",
            "범인의 동기 추상",
            "같은 패턴 반복",
            "물리적 대가 없는 해결"
        ],
        "fun": "쫓는 자와 쫓기는 자의 체스. 다음 수를 예측하는 재미."
    },
    "액션": {
        "core": "물리적 대결이 곧 인물의 내면. 액션은 장식이 아닌 서사다.",
        "must_have": [
            "액션의 의도·공간·리듬이 명확한가",
            "주인공이 물리적 대가를 치르는가",
            "액션 후 인물의 상태가 변하는가",
            "적대자와의 물리적 격차가 설득력 있는가"
        ],
        "fails": [
            "액션이 서사와 분리된 스펙터클",
            "주인공이 무적",
            "적대자가 일방적으로 약함",
            "액션 후 아무것도 변하지 않음"
        ],
        "fun": "인물이 몸으로 말하는 것. 한 동작에 10개 대사의 의미."
    },
    "로맨스": {
        "core": "장벽(Barrier)과 오해(Misunderstanding)가 관계를 정의한다. 장벽이 없으면 로맨스가 아니다.",
        "must_have": [
            "외적 장벽(신분·환경·상황)이 명확한가",
            "내적 장벽(두려움·과거·가치관)이 있는가",
            "두 사람의 첫 만남이 특별한 순간인가 (Meet-Cute)",
            "관계의 진전이 구체적 행동으로 보이는가"
        ],
        "fails": [
            "장벽 없이 바로 연결",
            "오해가 한 번 설명으로 해소",
            "감정을 대사로 직접 설명",
            "관계 진전이 몽타주로만 처리"
        ],
        "fun": "심장이 두근거리는 것. '이번에는 닿을까' 하는 기대."
    },
    "로맨틱 코미디": {
        "core": "장벽과 오해에 유머가 더해진다. 웃음과 설렘이 교차한다.",
        "must_have": [
            "Meet-Cute가 있는가",
            "스크루볼 요소(엇갈림·착각·우연)가 있는가",
            "장벽이 코믹하게 작동하는가",
            "해피 엔딩 또는 결합 암시"
        ],
        "fails": [
            "유머 없는 진지한 로맨스",
            "억지 설정",
            "여주·남주 중 한쪽이 납작함",
            "결말이 급작스러움"
        ],
        "fun": "두 사람이 만들어내는 리듬. 대사 한 줄의 엇박."
    },
    "호러": {
        "core": "안전이 무너진다. 집·가족·일상이 위협의 장소가 된다.",
        "must_have": [
            "안전한 공간이 위협받는가",
            "주인공이 도움을 청할 곳이 없는가 (고립)",
            "공포의 정체가 점진적으로 드러나는가",
            "최후의 대가(희생·상실)가 있는가"
        ],
        "fails": [
            "점프 스케어만 반복",
            "공포가 외부에만 있음 (내면화 없음)",
            "쉬운 탈출 경로 존재",
            "공포의 규칙이 일관되지 않음"
        ],
        "fun": "무서운 것. 안전하다고 믿었던 것이 무너지는 것."
    },
    "코미디": {
        "core": "진지한 상황의 진지함을 깨뜨린다. 캐릭터의 결함이 곧 유머다.",
        "must_have": [
            "캐릭터의 결함이 유머의 원천인가",
            "상황의 진지함과 반응의 부적절함이 충돌하는가",
            "유머가 캐릭터를 정의하는가",
            "감정선이 유머 사이에 유지되는가"
        ],
        "fails": [
            "외부 개그에 의존",
            "캐릭터 결함 없이 상황만 웃김",
            "감정선 붕괴",
            "같은 개그 반복"
        ],
        "fun": "웃음. 그리고 웃음 끝에 남는 따뜻함."
    },
    "판타지": {
        "core": "세계의 규칙이 우리 세계와 다르다. 규칙이 일관되면 마법이 설득력을 얻는다.",
        "must_have": [
            "세계의 규칙이 일관된가",
            "규칙에 대가가 있는가 (마법에 비용)",
            "세계 규칙이 인물의 선택을 정의하는가",
            "현실 세계와의 접점이 있는가"
        ],
        "fails": [
            "규칙이 일관되지 않음 (데우스 엑스 마키나)",
            "마법이 비용 없이 사용됨",
            "세계만 있고 드라마가 없음",
            "설정 설명이 과잉"
        ],
        "fun": "다른 세계에 들어가는 것. 규칙을 배우는 즐거움."
    },
    "SF": {
        "core": "과학적 설정이 인간 조건을 변화시킨다. 설정은 곧 질문이다.",
        "must_have": [
            "설정이 인간 조건에 대한 질문인가",
            "기술의 대가·부작용이 드러나는가",
            "주인공의 선택이 설정과 연결되는가",
            "결말이 설정에 대한 답을 제시하는가"
        ],
        "fails": [
            "설정이 장식에 불과",
            "기술의 대가 없음",
            "인간 드라마와 SF 설정 분리",
            "설정 설명이 과잉"
        ],
        "fun": "만약 이랬다면? What If의 질문과 답."
    }
}


def get_genre_rules_block(genre: str) -> str:
    """장르 Rule Pack을 프롬프트 블록으로 변환"""
    genre_key = genre.strip()
    if genre_key not in GENRE_RULES:
        # 퍼지 매칭
        for k in GENRE_RULES:
            if k in genre_key or genre_key in k:
                genre_key = k
                break
        else:
            genre_key = "드라마"

    g = GENRE_RULES[genre_key]
    must_have = "\n".join(f"   - {m}" for m in g["must_have"])
    fails = "\n".join(f"   - {f}" for f in g["fails"])

    return f"""
[장르 RULE PACK — {genre_key}]
핵심 정체성: {g['core']}

필수 요소 (Must Have):
{must_have}

실패 패턴 (Fails to Avoid):
{fails}

장르적 재미: {g['fun']}
"""


# =================================================================
# [4] INTENSITY BLOCK — 수정 강도별 원본 보존율 강제
# =================================================================
INTENSITY_RULES = {
    "CONSERVATIVE": {
        "preserve_ratio": "70%+",
        "description": "원본을 최대한 보존하며 지시사항이 지적한 부분만 국소적으로 수정",
        "instruction": """
[INTENSITY: CONSERVATIVE — 원본 70% 이상 보존]
1. 원본의 대사·지문 중 문제없는 부분은 그대로 유지하라.
2. 지시문이 명시적으로 지적한 부분만 수정하라.
3. 씬의 구조·순서·인물 배치는 건드리지 마라.
4. 수정은 "외과 수술" 수준이어야 한다. 큰 재구성 금지.
5. 원본의 리듬과 톤을 최대한 유지하라.
"""
    },
    "BALANCED": {
        "preserve_ratio": "50%",
        "description": "원본의 핵심은 유지하되, 지시사항에 따라 자연스럽게 재구성",
        "instruction": """
[INTENSITY: BALANCED — 원본 50% 보존, 자연스러운 재구성]
1. 원본의 핵심 요소(인물의 선택·주요 대사 포인트·공간·소품)는 유지하라.
2. 지시사항에 따라 씬 내부의 흐름·대사·지문을 자연스럽게 재구성하라.
3. 원본에 없던 새로운 행동·소품·암시를 추가해도 된다 (단, LOCKED 범위 내).
4. 씬의 위치와 개수는 바꾸지 마라.
5. 수정 후에도 원본 작가의 목소리가 느껴져야 한다.
"""
    },
    "AGGRESSIVE": {
        "preserve_ratio": "20~30%",
        "description": "원본에서 유지할 요소만 남기고 사실상 재집필",
        "instruction": """
[INTENSITY: AGGRESSIVE — 원본 20~30% 유지, 사실상 재집필]
1. LOCKED 요소와 씬의 기본 기능(플롯상 역할)만 유지하라.
2. 대사·지문·구성·리듬은 전면 재집필 가능하다.
3. 원본에 없던 새 요소·소품·암시를 적극 도입하라.
4. 단, 씬 위치와 플롯상 기능은 변경하지 마라.
5. 결과물은 "같은 씬의 완전히 다른 버전"이어야 한다.
"""
    }
}


def get_intensity_block(intensity: str) -> str:
    """Intensity 블록을 프롬프트용으로 변환"""
    key = intensity.strip().upper()
    if key not in INTENSITY_RULES:
        key = "BALANCED"
    return INTENSITY_RULES[key]["instruction"]


# =================================================================
# [5] STAGE 1 — DIAGNOSE (지시 해석 + 수정 플랜 생성)
# =================================================================
def build_diagnose_prompt(
    raw_text: str,
    instruction: str,
    locked: str,
    genre: str,
    intensity: str,
    profession_input: str = ""
) -> str:
    """Stage 1: 원본 + 지시문 + LOCKED를 분석해 수정 플랜(JSON)을 생성.
    Sonnet 4.6 사용 권장 (구조 분석).

    profession_input: 주요 캐릭터의 직업 (선택사항).
    비어있으면 원본 DOCX 본문에서 자동 감지.
    """

    genre_block = get_genre_rules_block(genre)
    locked_text = locked.strip() if locked.strip() else "(명시된 LOCKED 요소 없음 — 기본 원칙 적용: 플롯의 큰 흐름·핵심 반전·엔딩은 유지)"

    # 직업 전문성 블록 (감지 실패 시 빈 문자열)
    profession_block = build_profession_context(profession_input, raw_text)
    profession_section = ""
    if profession_block:
        profession_section = f"""

[직업 전문성 참고 블록]
━━━━━━━━━━━━━━━━━━━━━━━━
{profession_block}
━━━━━━━━━━━━━━━━━━━━━━━━

※ 진단 시 이 블록을 참고하여, 지시문이 지적하는 "직업답지 않음" 문제를 구체화하라.
  (예: "쇼핑 호스트답지 않다" → forbidden 목록에서 위반 항목 특정)"""

    return f"""
[TASK — Stage 1: DIAGNOSE]
원본 시나리오와 수정 지시문을 분석하여, 실제 수정 작업을 위한 "수정 플랜(Revision Plan)"을 JSON으로 생성하라.
이 단계는 집필이 아니다. 어디를, 왜, 어떻게 수정할 것인지의 "지도"를 그리는 단계다.

[원본 시나리오]
━━━━━━━━━━━━━━━━━━━━━━━━
{raw_text}
━━━━━━━━━━━━━━━━━━━━━━━━

[수정 지시문]
━━━━━━━━━━━━━━━━━━━━━━━━
{instruction}
━━━━━━━━━━━━━━━━━━━━━━━━

[LOCKED — 절대 건드리지 않을 요소]
━━━━━━━━━━━━━━━━━━━━━━━━
{locked_text}
━━━━━━━━━━━━━━━━━━━━━━━━
{profession_section}

{genre_block}

{get_intensity_block(intensity)}

[분석 원칙]
1. 지시문을 개별 수정 항목으로 분해하라. 한 지시문 안에 여러 요구가 있을 수 있다.
2. 각 수정 항목이 어느 씬(들)에 영향을 주는지 특정하라. 씬 번호 또는 씬 위치로.
3. LOCKED와 지시문이 충돌하면 LOCKED가 우선한다. 충돌 지점을 명시하라.
4. 지시문이 모호하면 가장 보수적 해석을 취하라.
5. 장르 RULE PACK에 비춰 추가로 개선해야 할 부분이 있으면 "auto_detected"로 표시하라.

[출력 형식 — JSON 단일 객체]
{{
  "revision_plan": {{
    "summary": "전체 수정 방향을 3~5줄로 요약",
    "locked_summary": "LOCKED로 인식된 요소 나열",
    "conflicts": [
      {{
        "instruction_item": "지시문에서 인용된 부분",
        "locked_conflict": "LOCKED 중 어느 항목과 충돌하는지",
        "resolution": "어떻게 해결할 것인지 (일반적으로 LOCKED 우선)"
      }}
    ],
    "target_scenes": [
      {{
        "scene_id": "씬 번호 또는 씬 헤더 (예: S#35 INT. 카페 - 낮)",
        "scene_position": "원본에서의 위치 (예: 2막 중반)",
        "original_function": "이 씬의 플롯상 기능",
        "revision_items": [
          {{
            "source": "user_instruction | auto_detected",
            "issue": "수정이 필요한 이유 (지시문 인용 또는 장르 진단)",
            "target_element": "dialogue | action_line | structure | character_voice | pacing",
            "proposed_direction": "어떻게 수정할 것인지 (아직 집필 아님, 방향만)"
          }}
        ],
        "preservation_notes": "이 씬에서 반드시 유지해야 할 요소 (LOCKED + 원본 강점)"
      }}
    ],
    "out_of_scope": [
      "지시문이 요구했지만 LOCKED 또는 Scope 제약으로 처리 불가한 항목 설명"
    ],
    "confidence": 0-10,
    "estimated_scene_count": "수정 대상 씬 개수"
  }}
}}

JSON만 출력하라. 설명·주석·마크다운 금지.
""".strip()


# =================================================================
# [6] STAGE 2 — REVISE (실제 집필)
# =================================================================
def build_revise_prompt(
    raw_text: str,
    diagnose_result: dict,
    genre: str,
    intensity: str,
    locked: str,
    profession_input: str = ""
) -> str:
    """Stage 2: Stage 1의 수정 플랜에 따라 실제 수정본을 집필.
    Opus 4.6 사용 필수 (집필).

    profession_input: 주요 캐릭터의 직업 (선택사항).
    비어있으면 원본 DOCX 본문에서 자동 감지.
    """

    import json as _json

    genre_block = get_genre_rules_block(genre)
    locked_text = locked.strip() if locked.strip() else "(명시된 LOCKED 요소 없음)"

    plan_json = _json.dumps(diagnose_result, ensure_ascii=False, indent=2)

    # 직업 전문성 블록 (감지 실패 시 빈 문자열)
    profession_block = build_profession_context(profession_input, raw_text)
    profession_section = ""
    if profession_block:
        profession_section = f"""

[직업 전문성 블록 — 집필 시 필수 참조]
━━━━━━━━━━━━━━━━━━━━━━━━
{profession_block}
━━━━━━━━━━━━━━━━━━━━━━━━

※ 위 직업 블록의 공간 디테일·전문 용어·금지 사항을 씬 집필에 반드시 녹여내라.
  특히 [금지 사항]을 절대 위반하지 마라 (작가가 흔히 범하는 오류 방지).
  단, 전문 용어를 전체 나열하지 말고 장면·대사에 필요한 1~2개만 선별 응용할 것."""

    return f"""
[TASK — Stage 2: REVISE]
Stage 1에서 생성된 수정 플랜에 따라, 원본 시나리오의 지정된 씬들을 실제로 다시 써라.
이 단계는 집필이다. 실제 작업에 즉시 투입 가능한 수정본을 생성해야 한다.

[원본 시나리오]
━━━━━━━━━━━━━━━━━━━━━━━━
{raw_text}
━━━━━━━━━━━━━━━━━━━━━━━━

[Stage 1 수정 플랜]
━━━━━━━━━━━━━━━━━━━━━━━━
{plan_json}
━━━━━━━━━━━━━━━━━━━━━━━━

[LOCKED — 절대 건드리지 않을 요소]
━━━━━━━━━━━━━━━━━━━━━━━━
{locked_text}
━━━━━━━━━━━━━━━━━━━━━━━━
{profession_section}

{genre_block}

{get_intensity_block(intensity)}

{AI_ESCAPE_BLOCK}

[집필 원칙]
1. Stage 1의 target_scenes 각 항목에 대해 수정된 씬 전문(全文)을 작성하라.
2. preservation_notes에 명시된 요소는 반드시 유지하라. 단어·소품·동선까지.
3. revision_items의 proposed_direction을 실제 대사와 지문으로 구현하라.
4. LOCKED와 충돌하면 LOCKED를 우선하고, conflicts에 기록된 해결 방향을 따르라.
5. Intensity가 정한 보존 비율을 엄격히 지키라.
6. 장르 RULE PACK의 must_have를 충족하고 fails를 피하라.
7. AI SCREENPLAY ESCAPE A1~A20 패턴이 출력에 나타나면 즉시 다시 쓰라.
8. 직업 전문성 블록이 주입된 경우, 해당 직업의 공간 디테일·전문 용어·금지 사항을 준수하라.

[한국 시나리오 포맷 규칙]
1. 씬 헤더: S#번호 장소 — 시간 (예: S#35 INT. 카페 — 낮)
2. 지문: 현재형 ("~한다"), 외부 관찰 가능한 행동만
3. 인물명: 한 줄 (모두 대문자 또는 일반 표기, 원본 방식 유지)
4. 대사: 인물명 다음 줄, 콜론(:) 없음
5. CUT TO. / INT. / EXT. 등 표준 전환 표기 사용
6. 괄호 지시 (V.O. / O.S. / 계속 / 낮게) 는 인물명 옆에

[출력 형식 — JSON 단일 객체]
{{
  "revision_result": {{
    "summary": "수정 작업의 전체 요약 (어떤 방향으로 무엇을 고쳤는지 3~5줄)",
    "revised_scenes": [
      {{
        "scene_id": "Stage 1의 scene_id와 일치",
        "scene_header": "수정된 씬 헤더 (예: S#35 INT. 카페 — 낮)",
        "original_excerpt": "원본 씬의 첫 2~3줄 (참조용)",
        "revised_content": "수정된 씬 전문. 지문+대사+전환 모두 포함. 줄바꿈은 \\n으로.",
        "revision_notes": {{
          "what_changed": "무엇이 어떻게 바뀌었는지 구체적으로",
          "what_preserved": "원본에서 유지한 요소들",
          "intensity_check": "이 씬에서 실제 보존 비율 (추정)",
          "locked_check": "LOCKED 준수 확인"
        }}
      }}
    ],
    "unchanged_scenes_note": "수정 대상이 아닌 씬들에 대한 안내 (원본 그대로 사용)",
    "cross_scene_impact": "이 수정이 다른 씬들과 플롯 흐름에 미치는 영향 설명"
  }}
}}

JSON만 출력하라. 설명·주석·마크다운 금지. revised_content 안의 시나리오 본문만이 유일한 산출물이다.
""".strip()


# =================================================================
# [7] STAGE 3 — VERIFY (검증 보고서)
# =================================================================
def build_verify_prompt(
    raw_text: str,
    revise_result: dict,
    instruction: str,
    locked: str,
    genre: str
) -> str:
    """Stage 3: 원본 vs 수정본을 비교하고, 지시사항·LOCKED·AI ESCAPE·장르 규칙 준수를 검증.
    Sonnet 4.6 사용 권장 (분석)."""

    import json as _json

    genre_block = get_genre_rules_block(genre)
    locked_text = locked.strip() if locked.strip() else "(명시된 LOCKED 요소 없음)"
    revise_json = _json.dumps(revise_result, ensure_ascii=False, indent=2)

    return f"""
[TASK — Stage 3: VERIFY]
원본 시나리오와 Stage 2에서 생성된 수정본을 비교하여, 다음 4가지 축으로 검증 보고서를 작성하라.
1. 지시사항 반영도 (Instruction Compliance)
2. LOCKED 보존도 (Locked Preservation)
3. AI SCREENPLAY ESCAPE 준수도 (Style Quality)
4. 장르 RULE PACK 준수도 (Genre Compliance)

[원본 시나리오]
━━━━━━━━━━━━━━━━━━━━━━━━
{raw_text}
━━━━━━━━━━━━━━━━━━━━━━━━

[Stage 2 수정 결과]
━━━━━━━━━━━━━━━━━━━━━━━━
{revise_json}
━━━━━━━━━━━━━━━━━━━━━━━━

[원본 수정 지시문 — 재참조]
━━━━━━━━━━━━━━━━━━━━━━━━
{instruction}
━━━━━━━━━━━━━━━━━━━━━━━━

[LOCKED — 보존해야 했던 요소]
━━━━━━━━━━━━━━━━━━━━━━━━
{locked_text}
━━━━━━━━━━━━━━━━━━━━━━━━

{genre_block}

{AI_ESCAPE_BLOCK}

[검증 원칙]
1. 지시사항을 개별 항목으로 분해한 뒤, 각 항목의 반영 여부를 Y/N/Partial로 판정하라.
2. LOCKED 요소가 수정본에서 유지되었는지 축자적으로 대조하라.
3. AI ESCAPE A1~A20 패턴이 수정본에 나타나는지 점검하라. 발견 시 구체 위치 표시.
4. 장르 must_have 4항목, fails 4항목 각각 체크.
5. 총평은 "출하 가능 여부"를 명확히 판정하라 (APPROVED / NEEDS_REVISION / REJECTED).

[출력 형식 — JSON 단일 객체]
{{
  "verify_report": {{
    "overall_verdict": "APPROVED | NEEDS_REVISION | REJECTED",
    "overall_score": "0.0 ~ 10.0 소수 한 자리",
    "verdict_reason": "판정 근거 3~5줄",

    "instruction_compliance": {{
      "score": "0 ~ 10 정수",
      "items": [
        {{
          "instruction_item": "지시문에서 추출한 개별 요구 사항",
          "status": "Y | N | Partial",
          "evidence": "수정본의 어느 부분에서 반영되었는지 (또는 왜 반영되지 않았는지)"
        }}
      ]
    }},

    "locked_preservation": {{
      "score": "0 ~ 10 정수",
      "items": [
        {{
          "locked_item": "LOCKED로 지정된 요소",
          "status": "Preserved | Violated | N/A",
          "evidence": "원본 vs 수정본 대조 결과"
        }}
      ]
    }},

    "ai_escape_check": {{
      "score": "0 ~ 10 정수",
      "violations": [
        {{
          "pattern_id": "A1 ~ A20 중 하나",
          "pattern_name": "예: 감정 설명 지문",
          "scene_id": "발견된 씬",
          "quote": "문제 구문 인용 (20자 내외)",
          "severity": "High | Medium | Low"
        }}
      ],
      "clean_patterns": "위반이 없는 패턴 개수 (총 20개 중)"
    }},

    "genre_compliance": {{
      "score": "0 ~ 10 정수",
      "must_have_check": [
        {{
          "item": "장르 must_have 항목",
          "status": "Met | Partial | Not_Met",
          "note": "짧은 해설"
        }}
      ],
      "fails_check": [
        {{
          "item": "장르 fails 항목",
          "status": "Avoided | Present | Improved",
          "note": "짧은 해설"
        }}
      ]
    }},

    "side_by_side_highlights": [
      {{
        "scene_id": "수정된 씬의 ID",
        "key_change": "가장 중요한 변화 한 줄 요약",
        "improvement_note": "이 변화의 효과 설명 (1~2줄)"
      }}
    ],

    "recommendations": [
      "재수정이 필요한 경우의 구체적 다음 스텝 (NEEDS_REVISION일 때만)"
    ]
  }}
}}

JSON만 출력하라. 설명·주석·마크다운 금지.
""".strip()


# =================================================================
# [8] 보고서 파일명 생성 유틸
# =================================================================
def get_report_filename(title: str, kind: str = "revised") -> str:
    """파일명 생성: 제목_수정본_날짜.docx 등"""
    import re
    from datetime import datetime
    safe_title = re.sub(r'[/*?:"<>|]', '_', title.strip()) if title else "제목없음"
    date_str = datetime.now().strftime("%Y%m%d")
    kind_map = {
        "revised": "수정본",
        "verify":  "검증보고서",
        "diagnose": "수정플랜"
    }
    kind_kor = kind_map.get(kind, kind)
    return f"{safe_title}_{kind_kor}_{date_str}_Blue.docx"


# =================================================================
# END OF prompt.py
# =================================================================
