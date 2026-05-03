# 👖 BLUE JEANS · REVISE ENGINE v2.7

영화 시나리오 각색(Revision) 전용 엔진.
Writer Engine에서 출력한 초고를 입력받아, 수정 지시문과 LOCKED 요소에 따라 실제 수정본을 생성한다.

---

## 🆕 v2.7 — 자동 배치 분할 시스템 (2026-05-03)

### 결함 해결
v2.6에서 71씬 같은 대형 시나리오를 진단할 때 출력 토큰이 max_tokens(32K) 한도를 넘어 결과가 잘리던 문제를 근본적으로 해결.

**v2.6의 문제**
- 71씬 시나리오 → 단일 LLM 호출 → 출력 토큰 초과 → 잘림
- A25~A28 헐리우드 작법 룰 추가 후 진단 분량이 늘어 잘림이 더 심해짐
- 사용자가 직접 배치를 잘라 입력하는 우회 방식 사용 중

**v2.7의 해결**
- '진단 시작' 버튼 한 번만 누르면 엔진이 자동으로 N씬 단위로 분할
- 각 배치를 별도 LLM 호출로 진단 → 결과 자동 병합
- 진행률 progress bar 실시간 표시
- 한 배치 실패 시 최대 3회 자동 재시도

### 신규 기능

#### 1. 다형식 씬 헤더 자동 인식
3가지 시나리오 형식을 자동 인식·분할.
- **S#숫자 형식**: 한국 시나리오 표준 (`S#1.`, `S#1`, `S# 1` 등)
- **EXT./INT. 형식**: 헐리우드 표준 (`EXT. 한남시장 — DAY` 등) — 「테이스티 러브 v3.2」가 사용
- **씬/Scene 형식**: 폴백

#### 2. 자동 배치 분할 미리보기
원본 시나리오 입력 즉시 UI에 자동 안내:
> 📦 **v2.7 자동 배치 분할:** 감지된 씬 수 **71씬** → 진단 시 **6배치**로 자동 분할 처리됩니다.

#### 3. 배치 사이즈 조절 슬라이더
고급 옵션 expander 안에 8~15 범위 슬라이더 제공 (기본 12).
- 헐리우드 작법 + 직업 Pack + 시대 Pack 동시 사용 시 → 10 권장
- 기본 작품 → 12 권장
- 매우 안전하게 → 8

#### 4. 진단 진행률 실시간 표시
```
🔬 배치 1/6 진단 중... (S#1~S#12)
🔬 배치 2/6 진단 중... (S#13~S#24)
...
✅ 자동 배치 진단 완료 — 6배치 → 수정 대상 24개 씬 식별
```

### 검증 결과 — 「테이스티 러브 v3.2」 (71씬, 46,296자)

| 항목 | 결과 |
|------|------|
| 씬 헤더 형식 | EXT./INT. (헐리우드) |
| 감지된 씬 수 | 71씬 ✅ |
| 분할 결과 (batch_size=12) | 6배치 |
| 본문 보존율 | 99.8% |
| 최대 배치 입력 토큰 | ~5,696 토큰 (안전) |
| 토큰 잘림 발생 | **없음** |

### 신규 함수 (main.py)

```python
_detect_scene_count(scenario_text) -> int
    """씬 헤더 패턴 카운트 (3종 형식 지원)"""

_split_scenario_by_scenes(scenario_text, batch_size=12) -> list
    """N씬 단위로 시나리오 분할"""

run_diagnose_with_auto_batch(client, batch_size=12) -> dict
    """자동 배치 분할 진단 + 결과 병합"""

_run_diagnose_single(client, raw_text, pre_results,
                     batch_info=None, retry_count=1) -> dict
    """단일 진단 호출 + 재시도"""
```

### 신규 매개변수 (prompt.py)

```python
build_diagnose_prompt(..., batch_info=None)
    """
    batch_info = {
        "batch_index": 1,
        "total_batches": 6,
        "scene_range": "S#1~S#12",
        "first_scene": 1,
        "last_scene": 12,
        "scene_format": "S#" | "EXT/INT" | "FALLBACK"
    }
    """
```

### 보존된 자산 (변경 없음)

- 5종 작업 모드 (전체 각색 / 이어쓰기 / 부분 수정 / Rewrite Engine 흡수 / 구간 모드)
- DOCX 빌더 (씬번호·대사·대사연속·지문·인서트헤더·인서트본문·인서트라벨)
- AI ESCAPE A1~A28 룰셋 (헐리우드 작법 A25~A28 포함)
- Writer Engine 자산 (`_split_action_paragraph`, `_strip_prop_state_memos`, `_parse_insert_blocks` 등)
- `_validate_and_fix_revised_format` 검증 함수
- `_split_dialog_action_fusion` 대사·지문 융합 분리
- `_normalize_scene_time_marker` DAY/NIGHT 정규화
- LOCKED 우선 원칙
- 디자인 시스템 (navy #191970 / yellow #FFCB05 / Pretendard·Playfair)

---

## 핵심 특징

- **3-Stage 파이프라인**: DIAGNOSE (지시 해석) → REVISE (실제 집필) → VERIFY (검증 보고서)
- **자동 배치 분할** (v2.7 신규): 시나리오 크기와 무관하게 안전 처리
- **듀얼 모델 정책**: Opus 4.6 (집필) / Sonnet 4.6 (분석)
- **LOCKED 우선 원칙**: 지시문과 LOCKED가 충돌하면 LOCKED 우선
- **수정 강도 3단계**: CONSERVATIVE / BALANCED / AGGRESSIVE
- **AI ESCAPE A1~A28 내장**: 헐리우드 작법 4대 원칙 포함
- **Profession Pack**: 19개 직업 카테고리 전문성 블록
- **Period Pack**: 10개 시대대 고증 블록 (조선 전기~민주화기)
- **Historical Film Rules**: 정통/팩션/퓨전 3유형 분기
- **Fact-Based Rules**: 실화 기반 작품 명예훼손·인격권 가이드
- **Rewrite Engine 연동**: CHRIS/SHIHO 진단·처방 JSON 자동 변환
- **2종 DOCX 출력**: 수정본 + 검증 보고서

---

## 입력 → 출력

### 입력
1. **원본 시나리오** — DOCX (한국 표준 S# 또는 헐리우드 EXT./INT. 형식 모두 지원)
2. **수정 지시문** — 자유 텍스트 / 모니터 보고서 / 투자사 피드백 / Rewrite JSON
3. **LOCKED** — 절대 건드리지 말 요소 (자유 텍스트)
4. **주요 캐릭터 직업** (선택)
5. **시대 · 실화 정보** (선택)
6. **장르 + 수정 강도** — 11장르 + 3단계
7. **DIAGNOSE 배치 사이즈** (v2.7 신규, 기본 12)

### 출력
1. **수정본 DOCX** — 한국 시나리오 표준 서식, 수정된 씬 전문 + 변경 노트
2. **검증 보고서 DOCX** — 4축 검증
3. **JSON 전체 백업** (옵션)

---

## 3-Stage 파이프라인

### Stage 1: DIAGNOSE (지시 해석)
- 모델: Sonnet 4.6
- **v2.7: 시나리오를 자동으로 N씬 단위로 분할 → 배치별 진단 → 결과 병합**
- 출력: 수정 대상 씬 목록, 씬별 수정 방향, LOCKED 충돌 지점

### Stage 2: REVISE (실제 집필)
- 모델: Opus 4.6
- 진단 결과의 revision_items를 6씬 단위로 배치 분할 → 배치별 집필
- 출력: 수정된 씬 전문 + 변경 노트

### Stage 3: VERIFY (검증 보고서)
- 모델: Sonnet 4.6
- 4축 검증 (지시 반영 / LOCKED 보존 / AI ESCAPE / 장르 준수도)

---

## Streamlit Cloud 배포 가이드

### 1) GitHub 저장소 (`cinepark-1974/revise-engine`)

기존 v2.6 저장소에서 다음 두 파일만 교체하면 됩니다.

```
revise-engine/
├── main.py                 ← v2.7로 교체
├── prompt.py               ← v2.7로 교체
├── profession_pack.py      (변경 없음)
├── period_pack.py          (변경 없음)
├── writer_modules.py       (변경 없음)
├── requirements.txt        (변경 없음)
├── README.md               ← v2.7로 교체 (선택)
└── .streamlit/
    └── config.toml         (변경 없음)
```

### 2) 푸시 → Streamlit Cloud 자동 재배포

GitHub 푸시 시 Streamlit Cloud가 자동으로 재배포합니다.
재배포 완료 후 사이드바에 **REVISE ENGINE v2.7** 배지가 표시되는지 확인하세요.

### 3) 동작 검증

「테이스티 러브 v3.2」(71씬) 업로드 → 다음 메시지 자동 표시되는지 확인:

> 📦 **v2.7 자동 배치 분할:** 감지된 씬 수 **71씬** → 진단 시 **6배치**로 자동 분할 처리됩니다.

진단 시작 → progress bar로 6배치 순차 진행 → 완료 메시지 표시.

### 4) 로컬 실행

```bash
streamlit run main.py
```

---

## 사용 워크플로 (v2.7 변경점만)

### Before (v2.6)
1. 71씬 시나리오 업로드
2. 진단 시작 → ❌ 토큰 초과 잘림
3. 사용자가 시나리오를 직접 12씬씩 잘라 별도 진단
4. 진단 결과 6개를 사용자가 수동으로 합침
5. → 시간 낭비 + 누락 위험

### After (v2.7)
1. 71씬 시나리오 업로드
2. UI에 즉시 안내: "71씬 → 6배치 자동 분할 예정"
3. 진단 시작 (버튼 1회 클릭)
4. progress bar로 진행 상황 자동 표시
5. → 완료 ✅

---

## 토큰 안전 마진 (v2.7 기준)

| batch_size | 평균 입력 토큰 | 출력 토큰 마진 | 권장 케이스 |
|------------|--------------|--------------|-----------|
| 8          | ~3,800       | 충분         | 가장 안전 |
| 10         | ~4,800       | 매우 안전    | 헐리우드+직업+시대 동시 |
| **12** (기본) | **~5,700** | **안전**    | **일반 작품** |
| 15         | ~7,200       | 보통         | 짧은 작품 |

(테이스티 러브 v3.2 기준 측정값. 시나리오 길이에 따라 달라질 수 있음.)

---

## 파일 구조

```
revise-engine/
├── main.py                 # Streamlit App + 3-Stage 파이프라인 + ★ 자동 배치 분할 (v2.7)
├── prompt.py               # System Prompt + AI ESCAPE + Genre Rules + ★ batch_info (v2.7)
├── profession_pack.py      # 19개 직업 카테고리
├── period_pack.py          # 10개 시대대 고증
├── writer_modules.py       # Fact-Based + Historical + Genre Override/Enforcement
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

---

## 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1.0 | 2026-04-21 | 초기 릴리스 — 3-Stage 파이프라인, AI ESCAPE A1~A20, Profession Pack 19개 |
| v2.2 | 2026-04-25 | 구간 지정 모드 (이어쓰기 + 부분 수정), Period Pack 10개, Historical Rules |
| v2.6 | 2026-04-30 | 헐리우드 작법 4대 원칙 (A25~A28) 추가 |
| **v2.7** | **2026-05-03** | **★ 자동 배치 분할 시스템 — 토큰 잘림 결함 해결, 헐리우드 형식 자동 인식** |

---

## 다음 작업 (v2.7 정상 작동 확인 후)

「테이스티 러브 v3.2」 → 헐리우드 작법 일괄 적용 → v3.3 생성
- 1~25씬: LOCKED (보호 영역)
- 26~71씬: 전체 재집필
- 분량: 71씬 그대로 유지

---

© 2026 BLUE JEANS PICTURES. All rights reserved.
