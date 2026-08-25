"""더미 데이터 시드 — 문제 + 유저 + 오늘 solves.
실행:  python seed.py
⚠️ 개발용: 실행 시 기존 users/problems/solves 를 모두 지우고 다시 넣음.
"""
import bcrypt
from datetime import datetime, timedelta, timezone

from core.db import db, ensure_indexes
from core.utils import get_today_date, calc_score

KST = timezone(timedelta(hours=9))


def _hash(pw):
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _hints(texts):
    return [{"order": i + 1, "text": t} for i, t in enumerate(texts)]


def run():
    ensure_indexes()
    db.users.delete_many({})
    db.problems.delete_many({})
    db.solves.delete_many({})

    today = get_today_date()
    base = datetime.strptime(today, "%Y-%m-%d")
    d1 = (base - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (base - timedelta(days=2)).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)

    # ---- 문제 3개 (오늘 + 지난 2일) ----
    problems = [
        {"date": today, "week": 1, "difficulty": "medium",
         "title": "물병을 뜻하는 파이썬 웹 프레임워크",
         "question": "이 경량 파이썬 웹 프레임워크의 이름은?",
         "answer": "flask", "accepted": ["flask", "플라스크"],
         "hints": _hints(["Python 기반입니다.",
                          "웹 애플리케이션 개발에 사용됩니다.",
                          "비교적 가벼운 프레임워크입니다.",
                          "Jinja2를 기본 템플릿 엔진으로 사용합니다.",
                          "이름은 물병을 뜻하는 영어 단어이기도 합니다."]),
         "explanation": "Flask는 파이썬 경량 웹 프레임워크입니다.",
         "created_at": now},
        {"date": d1, "week": 1, "difficulty": "easy",
         "title": "문서 지향 NoSQL 데이터베이스",
         "question": "JSON 유사 문서를 저장하는 대표적 NoSQL DB는?",
         "answer": "mongodb", "accepted": ["mongodb", "몽고db", "몽고디비"],
         "hints": _hints(["NoSQL입니다.", "문서(document) 기반입니다.",
                          "Atlas라는 클라우드 서비스가 있습니다."]),
         "explanation": "MongoDB는 문서 지향 NoSQL 데이터베이스입니다.",
         "created_at": now},
        {"date": d2, "week": 1, "difficulty": "medium",
         "title": "파이썬 기본 템플릿 엔진",
         "question": "Flask가 기본으로 쓰는 템플릿 엔진은?",
         "answer": "jinja2", "accepted": ["jinja2", "jinja", "진자2"],
         "hints": _hints(["Flask와 함께 쓰입니다.", "{{ }} 문법을 사용합니다.",
                          "이름에 숫자가 붙습니다."]),
         "explanation": "Jinja2는 파이썬 템플릿 엔진입니다.",
         "created_at": now},
    ]
    db.problems.insert_many(problems)
    today_pid = db.problems.find_one({"date": today})["_id"]

    # ---- 유저 6명 ----
    users = [{"username": f"jungle{i}", "password": _hash("test1234"),
              "nickname": nick, "created_at": now}
             for i, nick in enumerate(
                 ["jungle1", "python맨", "flask왕", "devkim", "mongo러버", "정글6"], 1)]
    db.users.insert_many(users)
    docs = list(db.users.find())

    # ---- 오늘 solves 5개 (다양한 점수) ----
    # (닉네임, hints_used, duration_sec)
    plays = [(docs[0], 1, 40), (docs[1], 1, 55), (docs[2], 2, 30),
             (docs[3], 2, 120), (docs[4], 3, 90)]
    solves = []
    for i, (u, hints, dur) in enumerate(plays):
        solved_at = base.replace(hour=10, minute=0, tzinfo=timezone.utc) + timedelta(minutes=i)
        solves.append({
            "user_id": u["_id"], "problem_id": today_pid, "date": today,
            "status": "solved", "hints_used": hints, "attempts_used": 1,
            "started_at": solved_at - timedelta(seconds=dur),
            "solved_at": solved_at, "duration_sec": dur,
            "score": calc_score(dur, hints),
        })
    db.solves.insert_many(solves)

    print(f"시드 완료 · 문제 {len(problems)}개 / 유저 {len(users)}명 / "
          f"오늘 풀이 {len(solves)}개 (오늘={today})")


if __name__ == "__main__":
    run()
