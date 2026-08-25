---
tags: [해커톤, DailyDrop, 백엔드, 공통계약, 설계도]
작성: 2026-08-25
담당: 회원 · DB · 배포 (백엔드)
---

# DailyDrop — 백엔드 공통 설계도 (팀 계약서)

> **목적**: 3인 팀이 혼란·머지충돌 없이 각자 기능을 구현하도록, 백엔드 담당이 깔아주는 공용 기반과 계약을 한 문서에 정리.
> **역할**: 나(회원·DB·배포) / 팀원 A(오늘의 퀴즈·지난 문제) / 팀원 B(랭킹 통계·내 기록)
> **스택**: Flask · Jinja2 SSR + 부분 AJAX · MongoDB(Atlas) · AWS · 세션 인증

## 확정된 핵심 결정
- **랭킹은 점수제(score)** — 1000점 시작, 시간 경과로 감점 + 힌트 사용 시 추가 감점. `solves.score`에 서버가 산출·저장. 정렬 `score DESC → solved_at ASC`.
- **인증은 세션** — JWT는 비교 검토 후 규모에 안 맞아 세션 선택. `session["user_id"]` 사용.
- **날짜 함수는 `get_today_date()` 로 통일** (KST, 오전 10시 이전이면 어제).
- **접근 방식 A(얇은 공용 기반)** — 나는 plumbing + 계약서만. 팀원은 자기 라우트 + DB 쿼리를 직접 작성. 치팅 민감한 채점은 복붙 스니펫으로 보완.

---

## 1. 폴더 구조 & 소유권 (충돌 방지)

Blueprint로 파일을 나눠 **파일 소유권 = 역할**로 만든다 → 각자 자기 파일만 수정 → 머지충돌 최소화.

```
dailydrop/
├─ app.py                  # [나] app 생성 + blueprint 등록만 (짧게)
├─ core/
│  ├─ db.py               # [나] MongoClient 연결 + 인덱스 생성
│  ├─ auth.py             # [나] /signup /login /logout + login_required + g.user_id
│  └─ utils.py            # [나] get_today_date() (KST 10시 로직) + calc_score()
├─ quiz/
│  └─ routes.py           # [팀원A] / (오늘의퀴즈) /hint /submit /archive
├─ ranking/
│  └─ routes.py           # [팀원B] /ranking /history
├─ templates/
│  ├─ base.html           # [나] 공통 셸(상단바·좌측 nav) — 모두 extends
│  ├─ auth/   login.html signup.html               # [나]
│  ├─ quiz/   today.html result.html archive.html  # [팀원A]
│  └─ ranking/ ranking.html history.html           # [팀원B]
├─ static/                # [공용] css/js (팀원별 하위폴더 권장)
├─ seed.py                # [나] 문제 + 더미 유저/기록 시드
├─ .env / .env.example / .gitignore / requirements.txt   # [나]
└─ README.md              # [나] 이 계약서의 요약본
```

**원칙**
- 팀원 A는 `quiz/`·`templates/quiz/`만, 팀원 B는 `ranking/`·`templates/ranking/`만 수정. `core/`는 나만.
- 모든 화면은 `base.html`을 `extends` → 네비게이션·로그인상태 일관.
- 팀원이 알아야 할 import는 3줄뿐:
  ```python
  from core.db import db
  from core.auth import login_required
  from core.utils import get_today_date, calc_score
  ```

---

## 2. 공용 계약서 (스키마 + 함수)

### 2-1. 컬렉션 (최종)

```text
users
  { _id, username(unique), password(bcrypt), nickname, created_at }

problems                       # 하루 1개 활성
  { _id, date(unique,"2026-08-25"), week, title, question,
    answer, accepted[], difficulty, hints[{order,text}], explanation, created_at }

solves                         # 퀴즈=쓰기 / 랭킹=읽기 (핵심 공유)
  { _id, user_id, problem_id, date,
    status("solving"|"solved"|"failed"),
    hints_used(int), attempts_used(int),
    started_at, solved_at, duration_sec, score(int 0~1000) }
```

> 설계문서의 `guesses[]`(매 시도 로그)는 해커톤 범위에선 제외. `attempts_used` 숫자로 충분.

**인덱스 (내가 `db.py`에서 생성)**
- `users.username` **unique**
- `problems.date` **unique**
- `solves (user_id, date)` **unique** — 하루 1회 보장 + 재진입 상태복원
- `solves (date, score DESC, solved_at ASC)` — 랭킹 조회 최적화

### 2-2. 내가 제공하는 4개 (팀원은 이것만)

```python
db                                      # pymongo handle: db.users / db.problems / db.solves

@login_required                         # 미로그인 시 /login 리다이렉트, g.user_id(ObjectId) 세팅

get_today_date() -> str                 # KST 오늘. 오전 10시 이전이면 어제. 예: "2026-08-25"

calc_score(duration_sec: int, hints_used: int) -> int
    # 실질경과초 = duration_sec + hints_used * HINT_TIME_PENALTY(60)
    # score      = max(0, round(1000 - 실질경과초 * DECAY_PER_SEC(1)))
```

### 2-3. 세션 규약
- 로그인 성공 → `session["user_id"] = str(user["_id"])`
- `@login_required` 가 매 요청에서 `g.user_id = ObjectId(session["user_id"])` 세팅
- 팀원은 `session`을 직접 안 만짐. 보호 라우트에 `@login_required` 붙이고 `g.user_id`만 사용.
- 닉네임 표시: `db.users.find_one({"_id": g.user_id})["nickname"]`

---

## 3. 팀원별 인터페이스 (복붙 스니펫)

### 팀원 A — 퀴즈 (`quiz/routes.py`, `templates/quiz/`)

| 라우트 | 하는 일 |
|---|---|
| `GET /` | 오늘 문제 + 내 풀이상태 렌더 (이미 풀었으면 결과로) |
| `POST /hint` (AJAX) | 다음 힌트 1개 공개 + `hints_used +1` |
| `POST /submit` | **서버 채점** → 정답 시 `calc_score`로 score 저장 |
| `GET /archive` | 지난 문제 목록 + 내 결과 |

```python
# GET /  오늘의 퀴즈
date = get_today_date()
prob = db.problems.find_one({"date": date})
solve = db.solves.find_one({"user_id": g.user_id, "date": date})
if not solve:
    db.solves.insert_one({"user_id": g.user_id, "problem_id": prob["_id"],
        "date": date, "status": "solving", "hints_used": 0, "attempts_used": 0,
        "started_at": datetime.utcnow(), "solved_at": None,
        "duration_sec": 0, "score": 0})
# ⚠️ 잠긴 힌트 노출 금지 → 템플릿엔 prob["hints"][:solve["hints_used"]] 만 전달

# POST /hint  다음 힌트 열기 (AJAX)
solve = db.solves.find_one({"user_id": g.user_id, "date": date})
n = solve["hints_used"]
if n < len(prob["hints"]):
    db.solves.update_one({"_id": solve["_id"]}, {"$inc": {"hints_used": 1}})
    return jsonify(prob["hints"][n])          # {order, text}

# POST /submit  채점 (⚠️ 점수는 반드시 서버에서)
guess = request.form["answer"].strip().lower()
ok = (guess == prob["answer"]) or (guess in prob["accepted"])
if ok:
    now = datetime.utcnow()
    dur = int((now - solve["started_at"]).total_seconds())
    db.solves.update_one({"_id": solve["_id"]}, {"$set": {
        "status": "solved", "solved_at": now,
        "duration_sec": dur, "score": calc_score(dur, solve["hints_used"])}})
else:
    db.solves.update_one({"_id": solve["_id"]}, {"$inc": {"attempts_used": 1}})
    # 힌트 소진 + 오답이면 status="failed" (팀 합의 규칙)
```

### 팀원 B — 랭킹/통계/기록 (`ranking/routes.py`, `templates/ranking/`)

| 라우트 | 하는 일 |
|---|---|
| `GET /ranking` | 오늘 정답자 `score↓ → solved_at↑` 정렬, 내 행 강조 |
| `GET /history` | 내 풀이 히스토리 + 개인 통계(총 풀이·평균 힌트·streak) |

```python
# GET /ranking
date = get_today_date()
rows = list(db.solves.find({"date": date, "status": "solved"})
              .sort([("score", -1), ("solved_at", 1)]))
# 닉네임: user_id → db.users.find_one({"_id": r["user_id"]})["nickname"]
# 내 순위 강조: r["user_id"] == g.user_id 인 행

# GET /history  내 기록 + 통계
mine = list(db.solves.find({"user_id": g.user_id}).sort("date", -1))
# 통계 집계: 총 풀이수 len(mine) / 평균 hints_used / 평균 duration_sec / streak
```

**팀 합의 필요 1건**: 힌트 5개 다 쓰고도 오답이면 `status="failed"`(랭킹 제외)로 확정할지 — 팀원 A와만 맞추면 됨.

---

## 4. 시드 데이터 & 데모 스위치

**`seed.py` 가 넣을 것**
- 문제 3~5개 — `date`를 오늘 + 지난 며칠로 (아카이브 화면 채움)
- 더미 유저 5~6명 (nickname 포함)
- 더미 solves — 오늘 날짜에 score 다양하게 (랭킹/통계 화면 채움)

**데모 스위치 (10시 경계 우회)**
- `get_today_date()`에 디버그 override — 환경변수 `DEBUG_TODAY="2026-08-25"` 있으면 그 날짜 반환, 없으면 실제 KST 로직. `debug=True`일 때만 동작하게 가드.

---

## 5. 내 작업 순서 (가장 빠른 언블록 시퀀스)

**원칙: 팀원이 기다리는 시간을 0으로.** "돌아가는 뼈대 + 계약서"를 제일 먼저 GitHub에.

| 순서 | 작업 | 끝나면 팀원이 할 수 있는 것 |
|:--:|---|---|
| 1 | 레포 뼈대 + push — `app.py`(팩토리), 빈 blueprint 스텁, `base.html`, `requirements.txt`, `.env.example`, README | 클론 → 실행 → 자기 라우트/템플릿 바로 시작 |
| 2 | `core/db.py`(연결+인덱스) + `core/utils.py`(`get_today_date`,`calc_score`) | 실제 컬렉션 쿼리 + 채점 함수 사용 |
| 3 | `seed.py` 실행 → 문제·더미 기록 | 랭킹/통계/아카이브 데이터 채워서 개발 |
| 4 | `core/auth.py` 세션 재작성 + auth 템플릿 | `@login_required` + `g.user_id` 사용 |
| 5 | (막판) AWS EC2 배포 | 전체 시연 |

> 1~3을 먼저 몰아서 끝내면 팀원 둘은 시드 기준으로 UI/쿼리를 바로 짜고, 나는 그 사이 4(세션)를 마무리. 로그인 완성 전엔 임시로 시드 유저 `_id`로 테스트 가능.

---

## 참고: 현재 코드 상태
- 실제 `app.py`는 아직 `home`/`signup`/`login`(bcrypt)만 있고 `jwt`는 import만, 세션 미구현 상태 → 위 구조로 재편성 필요.
- 관련 문서: DailyDrop DB 스키마, DailyDrop 설계문서, DailyDrop 작업일지(회원·DB·배포)
