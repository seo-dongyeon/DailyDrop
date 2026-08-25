---
tags: [해커톤, DailyDrop, 작업순서, 역할분담]
작성: 2026-08-25
---

# DailyDrop — 팀원별 작업순서 (뼈대 완성 후)

> 백엔드 공용 뼈대(core/ · base.html · 스텁 라우트 · seed)가 올라간 상태에서, **각 팀원이 무엇부터 시작할지** 정리.
> 계약·스키마·복붙 스니펫은 [[DailyDrop 백엔드 설계 (공통 계약)]] §2~3 참고.
> ⚠️ **랭킹은 점수제(score)** — 힌트 수 기준 아님. `score DESC → solved_at ASC`.

---

## 0. 전원 공통 세팅 (제일 먼저, 한 번)

1. [ ] 레포 clone → `main` 최신화 (`git pull`)
2. [ ] 가상환경 + 패키지: `python -m venv venv` → 활성화 → `pip install -r requirements.txt`
3. [ ] **로컬 `.env` 생성** — `.env.example` 복사 후 `MONGO_URI`(백엔드 담당에게 비공개로 받기) + `SECRET_KEY` 채우기
4. [ ] (한 명만) `python seed.py` — 문제/유저/오늘 풀이 더미 데이터 넣기 ⚠️ 실행 시 기존 데이터 삭제되니 팀에 공유 후
5. [ ] `python app.py` → `http://127.0.0.1:5000/signup` 가입 → 로그인 → 뼈대 화면 확인
6. [ ] **자기 브랜치 생성**: `git checkout -b feat/quiz` (A) / `feat/ranking` (B)
7. [ ] 자기 파일만 수정 — A는 `quiz/`·`templates/quiz/`, B는 `ranking/`·`templates/ranking/`

> 시작점: 각 라우트에 `# TODO(팀원 X)` 주석, 각 템플릿에 `{# [팀원 X 작업 영역] #}` 표시가 이미 있음.

---

## 1. 팀원 A — 오늘의 퀴즈 · 지난 문제

파일: `quiz/routes.py`, `templates/quiz/today.html`, `templates/quiz/archive.html`
> seed의 오늘 문제(`flask`)로 바로 테스트 가능.

| 순서 | 작업 | 완료 기준 |
|:--:|---|---|
| **1** | **`GET /` solve 문서 로드/생성** — solve 없으면 `status="solving"` 문서 insert (§3 스니펫). 공개 힌트만(`problem.hints[:solve.hints_used]`) 템플릿에 전달 | 처음 진입 시 solves에 문서 생김, 힌트 0개 노출 |
| **2** | **`today.html` 렌더** — 문제 제목/본문, 공개 힌트 리스트, 정답 입력폼, "다음 힌트"·"제출" 버튼 (Bootstrap) | 화면에 문제+입력폼 보임 |
| **3** | **`POST /hint` (AJAX)** — `hints_used += 1`, 다음 힌트 텍스트 JSON 반환. `today.html`에 jQuery로 버튼→ajax→힌트 추가 | 버튼 클릭마다 힌트 1개씩 열림 (최대 5) |
| **4** | **`POST /submit` 채점** — `answer.strip().lower()` 정규화 + `accepted[]` 비교. 정답 시 `calc_score(duration, hints_used)`로 score 저장, `status="solved"`, `solved_at` (§3 스니펫). ⚠️ 점수는 서버에서만 | 정답 시 solves에 score/solved_at 기록 |
| **5** | **결과 화면** (`result.html` 또는 today 내 분기) — 점수·사용 힌트·소요시간·해설 표시. 오답+힌트 소진 시 `status="failed"`(랭킹 제외) | 정답/실패 결과가 다르게 표시 |
| **6** | **하루 1회/재진입** — 이미 `solved`/`failed`면 진입 시 결과 화면으로 바로 | 새로고침해도 다시 못 풀게 |
| **7** | **`GET /archive` 지난 문제** — `problems.find({date:{$lt:오늘}})` 목록 + 내 결과 | 지난 문제 목록 보임 |

**A가 팀과 맞출 것**: ⑤의 `status="failed"` 규칙(오답+힌트 소진 시 랭킹 제외) → 팀원 B와 합의.

---

## 2. 팀원 B — 랭킹 · 통계 · 내 기록

파일: `ranking/routes.py`, `templates/ranking/ranking.html`, `templates/ranking/history.html`
> seed가 오늘 풀이 5개를 점수 다양하게 넣어둠 → **A의 구현을 기다릴 필요 없이 바로 시작 가능.**

| 순서 | 작업 | 완료 기준 |
|:--:|---|---|
| **1** | **`GET /ranking`** — `solves.find({date, status:"solved"}).sort([("score",-1),("solved_at",1)])`. 각 행에 닉네임 조인(`users.nickname`) | 점수 높은 순으로 표 출력 |
| **2** | **내 순위 강조** — `r.user_id == g.user_id` 행 하이라이트 | 내 행 색 다르게 |
| **3** | **오늘의 통계** — 도전 수, 성공률, 평균 힌트, 평균 소요시간 (`solves` aggregate) | 통계 4종 숫자 표시 |
| **4** | **`GET /history` 내 기록** — `solves.find({user_id:g.user_id}).sort("date",-1)` 표(날짜·문제·결과·점수·힌트·시간) | 내 풀이 히스토리 표 |
| **5** | **개인 통계** — 총 풀이 수, 평균 힌트, 연속 성공(streak, `get_today_date` 재사용해 날짜 연속 판정) | 요약 통계 표시 |
| **6** | **재사용 사이드 패널** — 랭킹+통계를 `templates/ranking/_side_panel.html` partial로 → 메인 화면(팀원 A의 today.html)에서 `{% include %}` | 메인 우측에도 랭킹/통계 표시 |

**B가 팀과 맞출 것**: ⑥ 사이드 패널 partial 이름·전달 변수 → 팀원 A와 합의(메인 화면 우측에 include).

---

## 3. 협업 규칙 (충돌·혼란 방지)

- **자기 폴더만** 수정. `core/`·`app.py`·`base.html`은 백엔드 담당(공용)에게 요청.
- 기능 단위로 **자주 커밋 + PR**. main 직push 금지(토대 이후).
- 작업 전 `git pull origin main` → 최신 뼈대 반영.
- 공용 계약(스키마·함수 시그니처)을 바꿔야 하면 **혼자 바꾸지 말고 팀 합의** 후 계약 문서 수정.

## 4. 팀 합의 남은 체크리스트
- [ ] `status="failed"` 규칙 (힌트 소진+오답 → 랭킹 제외?) — A·B
- [ ] 사이드 패널 partial 인터페이스 — A·B
- [ ] 시드 재실행 타이밍(데이터 초기화 주의) — 전원
- [ ] 점수 튜닝값(`HINT_TIME_PENALTY=60`, `DECAY_PER_SEC=1`) 밸런싱 — 전원
