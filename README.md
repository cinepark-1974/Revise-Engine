# 👖 BLUE JEANS · REVISE ENGINE

영화 시나리오 각색(Revision) 전용 엔진.
Writer Engine에서 출력한 초고를 입력받아, 수정 지시문과 LOCKED 요소에 따라 실제 수정본을 생성한다.

---

## 핵심 특징

- **3-Stage 파이프라인**: DIAGNOSE (지시 해석) → REVISE (실제 집필) → VERIFY (검증 보고서)
- **듀얼 모델 정책**: Opus 4.6 (집필) / Sonnet 4.6 (분석) 비용 효율 최적화
- **LOCKED 우선 원칙**: 지시문과 LOCKED가 충돌하면 LOCKED가 우선
- **수정 강도 3단계**: CONSERVATIVE (70%+ 보존) / BALANCED (50% 보존) / AGGRESSIVE (20~30% 유지)
- **Writer Engine v3.5 룰팩 내장**: AI ESCAPE A1~A20, 9장르 Rule Pack, 8장르 Override, 5종 Genre Enforcement
- **Profession Pack**: 19개 직업 카테고리 전문성 블록 (Creator Engine v2.3.9 이식)
- **Period Pack**: 10개 시대대 고증 블록 (Creator Engine v2.4.0 이식) — 조선 전기~민주화기
- **Historical Film Rules**: 정통/팩션/퓨전 3유형 분기
- **Fact-Based Rules**: 실화 기반 작품 명예훼손·인격권 가이드라인
- **Rewrite Engine 연동**: CHRIS/SHIHO 진단·처방 JSON을 자동 변환하여 수정 지시문으로 사용
- **2종 DOCX 출력**: 수정본 + 검증 보고서

---

## 입력 → 출력

### 입력
1. **원본 시나리오** — DOCX 파일 (Writer Engine 출력)
2. **수정 지시문** — 자유 텍스트
   - 본인 지시
   - 모니터 보고서
   - 투자사 피드백
   - **Rewrite Engine의 진단·처방 JSON** — 자동 변환 기능 (CHRIS+SHIHO만, MOON 자동 제외)
3. **LOCKED** — 절대 건드리지 말 요소 (자유 텍스트)
4. **주요 캐릭터 직업** (선택사항) — 예: `유진=쇼핑 호스트, 진호=변호사`
   - 비워두면 원본 DOCX에서 자동 감지
   - 19개 직업 카테고리의 전문 용어·공간 디테일·금지 사항 자동 주입
5. **시대 · 실화 정보** (선택사항)
   - 시대 드롭다운 (현대 / 조선 전기~민주화기 10종)
   - 역사영화 유형 (정통/팩션/퓨전)
   - 실화 기반 체크박스
6. **장르 + 수정 강도** — 11장르 + 3단계

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
- 주입되는 룰팩: AI ESCAPE A1~A20, 장르 Override, 장르 Enforcement, 직업 Pack, Period Pack, 역사영화 유형, 실화 가이드

### Stage 3: VERIFY (검증 보고서)
- 모델: Sonnet 4.6
- 역할: 원본 vs 수정본 비교, 4축 검증
- 출력: 판정(APPROVED / NEEDS_REVISION / REJECTED) + 점수 + 항목별 체크리스트

---

## Streamlit Cloud 배포

1. **GitHub 저장소 생성**: `cinepark-1974/revise-engine`
2. **파일 업로드** (6개 + 1폴더):
   - `main.py`
   - `prompt.py`
   - `profession_pack.py`
   - `period_pack.py`
   - `writer_modules.py`
   - `requirements.txt`
   - `README.md`
   - `.streamlit/config.toml`
3. **Streamlit Cloud 연결**: https://streamlit.io/cloud 에서 저장소 선택
4. **Secrets 등록**: Settings → Secrets 메뉴
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. **배포 완료** — Main file path는 `main.py`

---

## 파일 구조

```
revise-engine/
├── main.py                 # Streamlit App + 3-Stage 파이프라인
├── prompt.py               # System Prompt + AI ESCAPE + Genre Rules + 3-Stage builders + JSON 파서
├── profession_pack.py      # 19개 직업 카테고리 (Creator Engine v2.3.9 이식)
├── period_pack.py          # 10개 시대대 고증 (Creator Engine v2.4.0 이식)
├── writer_modules.py       # Fact-Based + Historical + Genre Override/Enforcement (Writer Engine v3.5 이식)
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml         # 라이트 모드 테마
```

---

## 장르 Rule Pack (11종)

- 드라마 / 느와르 / 스릴러 / 범죄/스릴러 / 액션 / 로맨스 / 로맨틱 코미디 / 호러 / 코미디 / 판타지 / SF

각 장르별로 Core / Must Have / Fails / Fun 4축 정의.
Stage 2 REVISE에서는 추가로 Genre Override (씬 단위 디테일 규칙) + Genre Enforcement (매 씬 강제 체크리스트) 주입.

---

## Profession Pack (19개 직업 카테고리)

법률직 / 의료직 / 금융기업직 / 언론창작직 / 공직정치 / 요식서비스직 / 교육직 / 엔터테인먼트 / 기술IT직 / 예술전통 / 강력수사 / 마약수사 / 지능수사 / 대공정보 / 조직폭력 / 마약밀수 / 화이트칼라범죄 / 건설부동산 / 농림수산자영업

각 카테고리는 8개 필드로 구성: 세부직종 / 하루타임라인 / 전문용어 / 공간디테일 / 직업스트레스 / 금지사항 / 한국맥락 / 연애스타일.

작동: 사용자 명시 입력 우선, 없으면 원본 DOCX에서 자동 감지.

---

## Period Pack (10개 시대)

- 조선 전기 (1392~1592)
- 조선 중기 (1592~1700)
- 조선 후기 (1700~1876)
- 구한말 (1876~1910)
- 일제강점기 전기 (1910~1931)
- 일제강점기 후기 (1931~1945)
- 해방정국 (1945~1950)
- 한국전쟁기 (1950~1953)
- 개발독재기 (1960~1987)
- 민주화기 (1987~1999)

각 시대별로 복식·관직·언어·주거·생활상·주요사건·인물 등 고증 디테일.

역사영화 유형 분기:
- 정통: 사실 충실, 시대 언어 엄격
- 팩션: 사실 + 허구 결합, 균형 잡힌 톤
- 퓨전: 현대 감각 적극 도입, 톤 자유로움

---

## Rewrite Engine 연동 (자동 변환)

Rewrite Engine의 진단·처방 결과를 Revise Engine 수정 지시문으로 자동 변환하는 기능.

### 사용법
1. Rewrite Engine에서 시나리오 분석 완료 후 진단·처방 JSON 다운로드
2. Revise Engine의 수정 지시문 영역에서 "🔗 Rewrite Engine 진단·처방 JSON 불러오기" 펼치기
3. JSON 파일 업로드 또는 텍스트 붙여넣기
4. "📥 변환" 버튼 클릭 → 자동으로 수정 지시문 입력창에 추가됨

### 자동 처리
- CHRIS 분석 추출: 스코어, 종합 분석, 장점·단점·핵심처방, 서사 동력, 장르 준수도, 오프닝 진단
- SHIHO 처방 추출: 시퀀스 워싱, 대사 분석, 각색 제안 (10 Steps), 오프닝/장르 처방
- MOON 리라이팅 자동 제외 — Revise Engine이 자체 방식으로 수정본 생성

### 지원하는 JSON 구조
- `chris_analysis` + `shiho_prescription` 키로 구조화된 export
- Rewrite Engine 내부 flat 구조 (자동 감지)

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
[진단 라인]    Rewrite Engine — 진단·처방 (CHRIS·SHIHO·MOON 보고서)
                                   ↓ (JSON 다운로드)
[수정 라인]    ★ Revise Engine ★ — 실제 수정본 생성
                                   ↓
                               [수정고 완성]
```

Revise Engine은 진단과 집필 사이의 공백을 메우는 엔진.
Rewrite Engine이 "무엇이 문제인지"를 알려준다면, Revise Engine은 "실제로 어떻게 고칠지"를 해낸다.

---

## 버전

**v1.0** (2026-04-21) — 초기 릴리스

- 영화 시나리오 전용 (시리즈·소설은 별도 엔진 예정)
- 3-Stage 파이프라인 + 듀얼 모델 정책
- AI ESCAPE A1~A20 내장
- 11장르 Rule Pack + 8장르 Override + 5종 Genre Enforcement
- Profession Pack 19개 직업 카테고리
- Period Pack 10개 시대 + Historical Film Rules 3유형
- Fact-Based Rules
- Rewrite Engine 진단·처방 JSON 자동 변환 연동
- LOCKED 우선 원칙
- DOCX 입출력 + JSON 백업

---

© 2026 BLUE JEANS PICTURES. All rights reserved.
