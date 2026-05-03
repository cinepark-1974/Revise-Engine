# 👖 BLUE JEANS · REVISE ENGINE v2.8

영화 시나리오 각색(Revision) 전용 엔진.

---

## 🆕 v2.8 — Beat-Aware Diagnose (2026-05-03)

### 신규 기능: 시나리오 확장 자동화

71씬 → 100씬 같은 **대규모 분량 확장 작업**을 위한 비트 인식 진단 시스템.

#### 핵심 동작

```
[Phase 1] 시나리오 전체 → 15-Beat 매핑 (Sonnet 4.6, 단일 호출)
            ↓
        beat_map JSON 생성
            ↓
[Phase 2] 추가 씬 수(예: +29) → 약점 비트별 자동 분배
            ↓
        distribution = {
          "fun_and_games": +7,
          "bad_guys_close_in": +9,
          "all_is_lost": +4,
          "finale": +9,
          ...
        }
            ↓
[Phase 3] 71씬 → 6배치 자동 분할 (v2.7)
            ↓
[Phase 4] 각 배치별 비트 인식 진단
          - 배치 내 씬이 어느 비트에 속하는지 인식
          - 그 비트가 약점이면 ADD 위치 제안
          - 누락 필수 요소(Cost of Choice 등) 보강
            ↓
        통합 diagnose_result + ADD 29씬 + REWRITE N씬
```

#### 15-Beat 마스터 (Save the Cat)

| 비트 | 권장 분량 | 기능 |
|------|----------|------|
| Opening Image | 0~1% | 작품 첫 인상 |
| Setup | 1~10% | 일상 + 결핍 |
| Theme Stated | 5% | 주제 대사 |
| Catalyst | 10% | Inciting Incident |
| Debate | 10~20% | 망설임 |
| Break into Two | 20~25% | 1막→2막 |
| B Story | 22% | 서브플롯 시작 |
| Fun and Games | 25~50% | **포스터 비트, 가장 두꺼움** |
| Midpoint | 50% | 판 뒤집힘 |
| Bad Guys Close In | 50~75% | 압박 고조 |
| All Is Lost | 75% | 최저점 |
| Dark Night | 75~80% | 정적 |
| Break into Three | 80% | A+B 통합 |
| Finale | 80~99% | 5단계 클라이맥스 |
| Final Image | 99~100% | Opening의 거울 |

#### 약점 비트 자동 진단

각 비트별로 4단계 강도 평가:
- 🟢 **STRONG**: 기능 충실 + 분량 충분
- 🟡 **ADEQUATE**: 기능은 있으나 분량 부족
- 🟠 **WEAK**: 기능 약함 또는 분량 부족
- 🔴 **MISSING**: 비트 자체 없음

#### 누락 필수 요소 자동 검출 (장르별)

로맨틱 코미디:
- Yearning Accumulation (갈망의 축적)
- Emotional Delay (감정의 지연)
- Obstacle to Union (만남의 장벽)
- **Cost of Choice (선택의 대가)** — 보고서가 「테이스티 러브」에서 누락 진단했던 필수 요소
- **Punch Beat (펀치 비트)** — 동일

#### 자동 분배 알고리즘

1. weak_beats의 deficit 합계 산출
2. deficit 큰 비트부터 비례 분배
3. missing_essentials의 CRITICAL 항목은 무조건 +1씬 보장
4. 잔여분은 가장 큰 분배 비트에서 보정

검증 결과 (테이스티 러브 시뮬레이션, 71→100):

| 비트 | 분배 |
|------|------|
| Fun and Games | +7씬 |
| Bad Guys Close In | +9씬 |
| All Is Lost | +4씬 (Punch Beat 보강) |
| Finale | +9씬 (Cost of Choice 보강) |
| **합계** | **+29씬** ✅ |

---

## 🎬 71→100씬 확장 워크플로

### Step 1: 시나리오 입력
- 원본 시나리오 DOCX 업로드 (테이스티 러브 v3.2)
- 자동으로 71씬 감지 (헐리우드 EXT./INT. 형식 인식)

### Step 2: 작업 모드 선택
- 작업 모드: **이어쓰기 (continuation)**
- 보호 영역: S#1~S#25 LOCKED
- 작업 영역: S#26~S#71

### Step 3: v2.8 Beat-Aware Diagnose 활성화
- `🎯 추가할 씬 수` 입력란에 **29** 입력
- 즉시 UI에 "확장 목표: 71씬 → 100씬" 표시

### Step 4: 진단 시작
- Phase 1: 비트 매핑 (약 1~2분)
- 비트별 강도 + 약점 + 누락 요소 자동 표시
- Phase 2: 6배치 비트 인식 진단 (약 5~7분)
- 각 배치마다 ADD 위치 자동 제안

### Step 5: 진단 결과 검토
- ADD 29씬의 비트별 분포 확인
- REWRITE 씬 검토
- 필요 시 일부 ADD 제거/이동

### Step 6: Stage 2 집필 시작
- v2.7 자동 배치 분할 시스템이 ADD 29 + REWRITE N개를 4~5씬 단위로 분할
- Opus 4.6이 배치별 집필
- 통합 DOCX 출력 (총 100씬)

---

## 신규 함수 (v2.8)

### prompt.py
```python
build_beat_mapping_prompt(scenario_text, genre)
    """전체 시나리오 → 15-Beat 매핑 프롬프트"""

distribute_added_scenes_across_beats(beat_map, target_added)
    """약점 비트에 추가 씬 자동 분배"""

build_beat_aware_diagnose_block(beat_map, distribution, target_added)
    """build_diagnose_prompt에 주입할 비트 인식 블록"""

SAVE_THE_CAT_15_BEATS  # 15-Beat 마스터 정의
```

### main.py
```python
_run_pre_diagnose_beat_map(client, scenario_text, genre)
    """Phase 1: 비트 매핑 (단일 Sonnet 호출)"""

run_diagnose_with_beat_aware_batch(client, batch_size, target_added_scenes)
    """Phase 2~4: 비트 인식 배치 진단 + 결과 통합"""
```

### build_diagnose_prompt 신규 매개변수
```python
build_diagnose_prompt(
    ...,
    beat_map: dict = None,           # v2.8 비트 매핑 결과
    beat_distribution: dict = None,  # v2.8 분배 결과
    target_added_scenes: int = 0     # v2.8 목표 추가 씬 수
)
```

---

## 라우팅 우선순위 (v2.8 업데이트)

```
run_diagnose(client)
  ├── Fast Path 1: 구간 모드(이어쓰기/부분수정) → 코드 자동 생성
  ├── Fast Path 2: Rewrite Engine JSON 흡수 → 코드 자동 생성
  └── Fast Path 3: 일반 진단
        ├── target_added_scenes > 0
        │     → run_diagnose_with_beat_aware_batch (v2.8)
        └── target_added_scenes == 0
              → run_diagnose_with_auto_batch (v2.7)
```

---

## 보존된 자산 (v2.7 → v2.8 변경 없음)

- 5종 작업 모드
- DOCX 빌더
- AI ESCAPE A1~A28
- Writer Engine 자산
- v2.7 자동 배치 분할 시스템
- LOCKED 우선 원칙
- 디자인 시스템

---

## Streamlit Cloud 배포

기존 v2.7 저장소에서 **`main.py`와 `prompt.py` 두 파일만 교체**.

```
revise-engine/
├── main.py                 ← v2.8로 교체
├── prompt.py               ← v2.8로 교체
├── profession_pack.py      (변경 없음)
├── period_pack.py          (변경 없음)
├── writer_modules.py       (변경 없음)
├── requirements.txt        (변경 없음)
└── .streamlit/config.toml  (변경 없음)
```

GitHub 푸시 → Streamlit Cloud 자동 재배포.

---

## 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1.0 | 2026-04-21 | 초기 릴리스 |
| v2.2 | 2026-04-25 | 구간 지정 모드, Period Pack |
| v2.6 | 2026-04-30 | 헐리우드 작법 A25~A28 |
| v2.7 | 2026-05-03 | 자동 배치 분할 시스템 |
| **v2.8** | **2026-05-03** | **★ Beat-Aware Diagnose — 시나리오 확장 자동화** |

---

© 2026 BLUE JEANS PICTURES. All rights reserved.
