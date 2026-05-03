# 👖 BLUE JEANS · REVISE ENGINE v2.9

영화 시나리오 각색 전용 엔진.

---

## 🆕 v2.9 — 비트 보강 확장 모드 (2026-05-03)

### 4번째 작업 모드 신설

기존 3개(전체 각색 / 이어쓰기 / 부분 수정)에 **🎯 비트 보강 확장**이 추가되었습니다.

| 모드 | 용도 |
|------|------|
| 📝 전체 각색 | 시나리오 전체 재집필 |
| ✍️ 이어쓰기 | 손본 부분(이전 버전) 톤 학습 → 다음 부분 재집필 |
| ✂️ 부분 수정 | 지정 범위만 재집필 |
| **🎯 비트 보강 확장** | **약점 비트에 ADD 씬 자동 분배 → 분량 확장 (예: 71→100씬)** |

### 비트 보강 확장 모드 동작

```
[입력]
- 시나리오 1개
- 보호 구간 (LOCKED, 예: S#1~S#25)
- 추가 목표 씬 수 (예: 29)

[Phase 1] 시나리오 전체 → 15-Beat 매핑 (Sonnet, 단일 호출)
[Phase 2] 약점 비트별 +29씬 자동 분배
[Phase 3] 비트 인식 배치 진단 (12씬 단위)
[Phase 4] LOCKED 영역 강제 차단:
  - 보호 구간 내 REWRITE → out_of_scope 이동
  - 보호 구간 내 ADD 위치 → 작업 영역 시작점으로 자동 우회
[Phase 5] 결과 통합 → ADD 29 + REWRITE N
```

### LOCKED 강제 차단 검증

테이스티 러브 시나리오 시뮬레이션:

| 입력 | 결과 |
|------|------|
| REWRITE S#5 (LOCKED 영역) | 🚫 차단 → out_of_scope |
| REWRITE S#15 (LOCKED 영역) | 🚫 차단 → out_of_scope |
| REWRITE S#30 (작업 영역) | ✅ 통과 |
| ADD insert_after S#10 (LOCKED 영역) | ↪️ S#25로 자동 우회 |
| ADD insert_after S#22 (LOCKED 영역) | ↪️ S#25로 자동 우회 |
| ADD insert_after S#35 (작업 영역) | ✅ 통과 |

---

## 🎬 71→100씬 확장 워크플로

### 1) 작업 모드 선택
**🎯 비트 보강 확장** 카드 클릭

### 2) 입력 영역 (자동 표시)
- 🎯 추가할 씬 수: **29**
- 🔒 보호 시작: **S#1**
- 🔒 보호 끝: **S#25**
- 작업 영역: **S#26 ~ S#71** (자동 산출)

### 3) 진단 시작
**🔬 Stage 1: 진단 시작 (DIAGNOSE)** 클릭
- Phase 1~5 자동 진행 (약 6~10분)
- ADD 29씬 + REWRITE N씬 결과 표시
- LOCKED 침범 차단 통계 표시

### 4) 집필 시작
**✍️ Stage 2: 집필 시작 (REVISE)** 클릭
- 4~5씬 단위 배치 분할 자동 처리
- 100씬 통합 DOCX 출력

---

## 라우팅 우선순위 (v2.9)

```
run_diagnose(client)
  ├── ★ Fast Path 0 (v2.9): work_mode=="expansion" + target_added>0
  │     → run_diagnose_beat_expansion (Beat-Aware + LOCKED 차단)
  ├── Fast Path 1: 구간 모드 (이어쓰기/부분수정) → 코드 자동 생성
  ├── Fast Path 2: Rewrite Engine JSON 흡수 → 코드 자동 생성
  └── Fast Path 3: 일반 진단
        ├── target_added > 0 → v2.8 Beat-Aware
        └── target_added == 0 → v2.7 자동 배치
```

---

## 신규 함수 (v2.9)

```python
# main.py
_parse_scene_range_to_int(range_str) -> int
    """'S#25' → 25 변환"""

_filter_target_scenes_against_protected(target_scenes, protected_ranges)
    """LOCKED 영역 침범 항목 차단/우회"""

run_diagnose_beat_expansion(client, batch_size, target_added_scenes)
    """v2.9 비트 보강 확장 진단 (Beat-Aware + LOCKED 강제)"""
```

---

## 보존된 자산 (v2.8 → v2.9 변경 없음)

- 5종 작업 모드 (이제 4종 + Rewrite JSON 흡수)
- DOCX 빌더
- AI ESCAPE A1~A28
- Writer Engine 자산
- v2.7 자동 배치 분할 / v2.8 Beat-Aware Diagnose
- LOCKED 우선 원칙
- 디자인 시스템

---

## Streamlit Cloud 배포

`cinepark-1974/revise-engine` 저장소에서 **`main.py`와 `prompt.py` 두 파일만 교체** → 푸시 → 자동 재배포.

배포 확인:
- 헤더: **REVISE ENGINE v2.9** 노란 배지
- 푸터: Auto Batch Split (초록) + Beat-Aware Diagnose (주황) + **Beat Expansion Mode (분홍)**
- 작업 모드 선택: **4개 카드** (전체/이어쓰기/부분/비트확장)

---

## 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v2.7 | 2026-05-03 | 자동 배치 분할 |
| v2.8 | 2026-05-03 | Beat-Aware Diagnose |
| **v2.9** | **2026-05-03** | **★ 비트 보강 확장 모드 (4번째 작업 모드)** |

---

© 2026 BLUE JEANS PICTURES. All rights reserved.
