from flask import Blueprint, render_template, g, jsonify
from core.db import db
from core.auth import login_required
from core.utils import get_today_date
from datetime import datetime
import random

ranking_bp = Blueprint("ranking", __name__)

@ranking_bp.route("/ranking")
@login_required
def ranking():
    date = get_today_date()
    # 정렬 우선순위: 점수 > 힌트 사용횟수 > 풀이 완료 시각
    rows = list(db.solves.find({"date": date, "status": "solved"})
                .sort([("score", -1), ("hints_used", 1),("solved_at", 1)]))
    # db에서 rows데이터에 들어있는 정보를 통해 닉네임을 찾고 rows에 다시 닉네임을 주입시키는 로직
    # 순위를 나타낼 때 예외 사항 
    # 1) 점수 동일 2) 힌트 사용횟수 동일 3) 풀이완료시각 동일 조건일 경우 -> 공동 순위 부여
    rank_rows = []
    for idx, row in enumerate(rows, start=1):
        user = db.users.find_one({"_id": row["user_id"]})
        rank_rows.append({
            "rank": idx,
            "nickname": user["nickname"] if user else "알 수 없음",
            "score": row["score"],
            "solved_at": row["solved_at"],
            "hints_used": row["hints_used"],
            "is_me": row["user_id"] == g.user_id
        })

    return render_template("ranking/ranking.html", date=date, rows=rank_rows)

@ranking_bp.route("/ranking/side_panel/_ranking_panel", methods=['GET'])
@login_required
def liveRanking():
    date = get_today_date()
    rows = list(db.solves.find({"date": date, "status": "solved"}).sort([("score", -1), ("hints_user", 1), ("solved_at", 1)]).limit(5))
    rank_rows=[]
    for idx, row in enumerate(rows, start=1):
        user = db.users.find_one({"_id": row["user_id"]})
        rank_rows.append({
            "rank": idx,
            "nickname": user["nickname"] if row["user_id"] else "알 수 없음",
            "score": row["score"],
        })

    ########################################################################################
    # # ❗️테스트용 데이터 - mock_rows
    # users = [
    #     {"rank": 1, "nickname": "테스트1", "score": random.randint(900, 1000)},
    #     {"rank": 2, "nickname": "테스트2", "score": random.randint(900, 1000)},
    #     {"rank": 3, "nickname": "테스트3", "score": random.randint(900, 1000)},
    # ]  
    # # 2. 점수(score) 기준 내림차순 정렬 📉
    # users_sorted = sorted(users, key=lambda x: x["score"], reverse=True)
    
    # # 3. 정렬된 순서대로 rank 부여 및 Top 3 추출 🏆
    # mock_rows = []
    # for idx, user in enumerate(users_sorted[:3]):
    #     mock_rows.append({
    #         "rank": idx + 1,  # 1위, 2위, 3위
    #         "nickname": user["nickname"],
    #         "score": user["score"]
    #     })
    ########################################################################################            
    return jsonify({
        "status": "success",
        "rows": rank_rows
    })


@ranking_bp.route("/history")
@login_required
def history():
    mine = list(db.solves.find({"user_id": g.user_id}).sort("date", -1))
    history = []
    for m in mine:
        problem = db.problems.find_one({"_id": m["problem_id"]})
        history.append({
            "date": m["date"],
            "problem_title": problem["title"] if problem else "문제 없음",
            "status": m["status"],
            "hints_used": m.get("hints_used", 0),
            "duration_sec": m.get("duration_sec", 0),
        })

    total = len(mine)
    avg_hints = round(sum(r.get("hints_used", 0) for r in mine) / total, 1) if total else 0
    avg_solved = round((sum(r.get("status") == "solved" for r in mine) / total)*100, 1) if total else 0

    # max_streak 구현
    # 1) 날짜 최신순으로 정렬 + status="solved"인 데이터만 추출
    dates = []
    for m in mine:
        if(m["status"] == "solved"):
            dates.append(m.get("date"))
    # 2) 연속이면 current_streak+1
    # datetime 객체를 사용하여 두 날짜 사이의 일수 차이를 계산한다. 기준 날짜 - 이전 날짜 수 == 1 => current_streak+1
    current_streak = 1
    max_streak = 0 
    # 연속일은 문제를 푼 날부터 +1 (연속된 횟수로 접근하지 않음.)
    # 리스트 안에 나열되어 있는 앞뒤 날짜 데이터를 뺀 값이 1일 때만 current_streak +1 카운팅
    for idx in range(1, len(dates)):
        conseDays = (datetime.strptime(dates[idx-1], "%Y-%m-%d").date() - datetime.strptime(dates[idx], "%Y-%m-%d").date()).days
        if( conseDays == 1):
            current_streak += 1
        else:
            current_streak = 1   
    
    # 3) current_streak > max_streak => max_streak = current_streak break
        if(current_streak > max_streak):
            max_streak = current_streak
    
    return render_template("ranking/history.html", mine=history, total=total, avg_solved=avg_solved, avg_hints=avg_hints, max_streak=max_streak)

@ranking_bp.route("/ranking/side_panel/_stats_panel", methods=['GET'])
@login_required
def stats():
    date = get_today_date()
    rows = list(db.solves.find({"date": date}))

    total_attempts = len(rows) # 퀴즈가 나온 시점의 총 도전 수
    total_avg_solved = round((sum(r.get("status") == "solved" for r in rows) / total_attempts)*100, 1) if total_attempts else 0
    total_avg_hints = round((sum(r.get("hints_used")== 0 for r in rows)) / total_attempts, 1) if total_attempts else 0

    print(total_avg_solved,total_avg_hints,total_attempts)
    return jsonify({
        "status": "success",
        "attempts": total_attempts,
        "hints": total_avg_hints,
        "solved": total_avg_solved,
    })
