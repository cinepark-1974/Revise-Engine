# 👖 BLUE JEANS · REVISE ENGINE

영화 시나리오 각색(Revision) 전용 엔진.
Writer Engine에서 출력한 초고를 입력받아, 수정 지시문과 LOCKED 요소에 따라 실제 수정본을 생성한다.

---

## 핵심 특징

- **3-Stage 파이프라인**: DIAGNOSE (지시 해석) → REVISE (실제 집필) → VERIFY (검증 보고서)
- **듀얼 모델 정책**: Opus 4.6 (집필) / Sonnet 4.6 (분석) 비용 효율 최적화
- **LOCKED 우선 원칙**: 지시문과 LOCKED가 충돌하면 LOCKED가 우선
- **수정 강도 3단계**: CONSERVATIVE (70%+ 보존) / BALANCED (50% 보존) / AGGRESSIVE (20~30% 유지)
- **Writer Engine v3.5 룰팩 내장**: AI SCREENPLAY ESCAPE A1~A20, 9장르 Rule Pack
- **2종 DOCX 출력**: 수정본 + 검증 보고서
- **Profession Pack 연동**: 19개 직업 카테고리 전문성 블록 (Creator Engine v2.3.9 이식) — 명시 입력 + 원본 자동 감지

---

## 입력 → 출력

### 입력
1. **원본 시나리오** — DOCX 파일 (Writer Engine 출력)
2. **수정 지시문** — 자유 텍스트
   - 본인 지시
   - 모니터 보고서
   - 투자사 피드백
   - Rewrite Engine의 CHRIS/SHIHO 진단·처방 내용
3. **LOCKED** — 절대 건드리지 말 요소 (자유 텍스트)
4. **주요 캐릭터 직업** (선택사항) — 예: `유진=쇼핑 호스트, 진호=변호사`
   - 비워두면 원본 DOCX에서 자동 감지
   - Profession Pack 19개 카테고리의 전문 용어·공간 디테일·금지 사항 자동 주입
5. **옵션** — 장르 선택 (11종) + 수정 강도 (3단계)

### 출력
1. **수정본 DOCX** — 한국 시나리오 표준 서식, 수정된 씬 전문 + 변경 노트
2. **검증 보고서 DOCX** — 4축 검증 (지시 반영 / LOCKED 보존 / AI ESCAPE / 장르 준수도)
3. **JSON 전체 백업** (옵션) — 3-Stage 결과 전체

---

## 3-Stage 파이프라인

### Stage 1: DIAGNOSE (지시 해석)
- 모델: Sonnet 4.6
- 역할: 원본 + 지시문 + LOCKED를 분석하여 수정 플랜 JSON 생성
- 출력: 수정 대상 씬 목록, 씬별 수정 방향, LOCKED 충돌 지점

### Stage 2: REVISE (실제 집필)
- 모델: Opus 4.6
- 역할: Stage 1 플랜에 따라 실제 씬 재집필
- 출력: 수정된 씬 전문 (한국 시나리오 서식) + 변경 노트

### Stage 3: VERIFY (검증 보고서)
- 모델: Sonnet 4.6
- 역할: 원본 vs 수정본 비교, 4축 검증
- 출력: 판정(APPROVED / NEEDS_REVISION / REJECTED) + 점수 + 항목별 체크리스트

---

## 로컬 실행

```bash
streamlit run main.py
```

> `.streamlit/secrets.toml` 에 `ANTHROPIC_API_KEY = "sk-ant-..."` 를 먼저 설정해야 합니다.

---

## Streamlit Cloud 배포

1. **GitHub 저장소 생성**: `cinepark-1974/revise-engine`
2. **파일 업로드**:
   - `main.py`
   - `prompt.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`
3. **Streamlit Cloud 연결**: https://streamlit.io/cloud 에서 저장소 선택
4. **Secrets 등록**:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. **배포 완료** — Main file path는 `main.py`

---

## 파일 구조

```
revise-engine/
├── main.py                 # Streamlit App + 3-Stage 파이프라인
├── prompt.py               # System Prompt + AI ESCAPE + Genre Rules + 3-Stage builders
├── profession_pack.py      # 19개 직업 카테고리 전문성 블록 (Creator Engine v2.3.9 이식)
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml         # 라이트 모드 테마
```

---

## Profession Pack (19개 직업 카테고리)

Creator Engine v2.3.9의 profession_pack.py를 그대로 이식. 각 카테고리는 8개 필드로 구성:

**카테고리 목록:**
- 법률직 / 의료직 / 금융기업직 / 언론창작직 / 공직정치 / 요식서비스직
- 교육직 / 엔터테인먼트 / 기술IT직 / 예술전통
- 강력수사 / 마약수사 / 지능수사 / 대공정보
- 조직폭력 / 마약밀수 / 화이트칼라범죄
- 건설부동산 / 농림수산자영업

**각 카테고리의 8개 필드:**
1. **subtypes** — 세부 직종 (3~6개)
2. **daily_timeline** — 하루 타임라인 (아침→밤)
3. **jargon** — 전문 용어 사전 (15~20개, 한/영 병기)
4. **space_detail** — 공간 디테일 (소품·냄새·소리)
5. **stress** — 직업적 스트레스 & 내적 갈등
6. **forbidden** — 작가가 흔히 범하는 오류 (금지 목록)
7. **korea_context** — 한국 고유 맥락 (계급·호칭·조직문화)
8. **romance_style** — 연애/관계 스타일 경향성

**작동 방식:**
- 사용자 명시 입력 (`유진=쇼핑 호스트, 진호=변호사`) → 해당 직업 블록 주입
- 명시 입력이 없으면 원본 DOCX 본문에서 자동 감지
- Stage 1 DIAGNOSE: 직업별 금지 사항 위반 진단
- Stage 2 REVISE: 집필 시 공간·용어·디테일 반영
- 감지 실패해도 에러 없이 통과 (기본 집필로 진행)

---

## 장르 Rule Pack (11종)

- 드라마 / 느와르 / 스릴러 / 범죄/스릴러 / 액션 / 로맨스 / 로맨틱 코미디 / 호러 / 코미디 / 판타지 / SF

각 장르별로:
- **Core**: 핵심 정체성
- **Must Have**: 필수 요소 4항목
- **Fails**: 실패 패턴 4항목
- **Fun**: 장르적 재미

---

## AI SCREENPLAY ESCAPE (A1~A20)

Writer Engine v3.5에서 이식한 20가지 AI 특유의 실수 패턴.
수정본에 이 패턴이 나타나면 즉시 다시 쓰도록 강제.

- A1~A10: 감정 설명 지문 / 대칭 대사 / 침묵 부재 등 기본 20가지 패턴
- A11~A13: 물리적 논리 비약 / 관찰자 없는 숫자 / 인과의 구멍
- A14~A16: 캐릭터 재소개 / 반복 루프 / 정보 반복 전달
- A17~A20: 메타데이터 누출 / 대사 포맷 오염 / 장르 톤 붕괴 / 소설체 지문

Stage 3 VERIFY에서 각 패턴 위반 여부를 자동 점검.

---

## 블루진 엔진 생태계 내 위치

```
[기획 라인]    Creator Engine
[집필 라인]    Writer Engine → [영화 초고]
                                   ↓
[진단 라인]    Rewrite Engine — 진단·처방 (리포트 생성)
                                   ↓
[수정 라인]    ★ Revise Engine ★ — 실제 수정본 생성
                                   ↓
                               [수정고 완성]
```

**Revise Engine은 진단과 집필 사이의 공백을 메우는 엔진.**
Rewrite Engine이 "무엇이 문제인지"를 알려준다면, Revise Engine은 "실제로 어떻게 고칠지"를 해낸다.

---

## 버전

**v1.0** (2026-04-21) — 초기 릴리스

- 영화 시나리오 전용 (시리즈·소설은 별도 엔진 예정)
- 3-Stage 파이프라인 + 듀얼 모델 정책
- AI ESCAPE A1~A20 내장
- 9장르 Rule Pack 내장
- LOCKED 우선 원칙
- DOCX 입출력 + JSON 백업

---

© 2026 BLUE JEANS PICTURES. All rights reserved.
