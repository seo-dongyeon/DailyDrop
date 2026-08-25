"""[팀원 A 담당] 오늘의 퀴즈 · 지난 문제.

공용 도구: db(core.db) / login_required(core.auth) / get_today_date, calc_score(core.utils)
스키마·복붙 스니펫: docs/DailyDrop-백엔드-설계.md §3 참고
아래는 '돌아가는 스텁' — TODO 부분을 실제 로직으로 채우면 됨.
"""
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, g
from core.db import db
from core.auth import login_required
from core.utils import get_today_date, calc_score

quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.route("/")
@login_required
def today():
    date = get_today_date()
    problem = db.problems.find_one({"date": date})
    solve = db.solves.find_one({"user_id": g.user_id, "date": date})
    # TODO(팀원 A): solve 없으면 status="solving" 문서 생성 (§3 스니펫)
    if solve is None:
        db.solves.insert_one({"user_id": g.user_id, "problem_id": problem["_id"],
        "date": date, "status": "solving", "hints_used": 0, "attempts_used": 0,
        "started_at": datetime.now(timezone.utc), "solved_at": None,
        "duration_sec": 0, "score": 0})
        
        solve = db.solves.find_one({"user_id": g.user_id, "date": date})
    
    # TODO(팀원 A): 잠긴 힌트 노출 금지 → problem.hints[:solve.hints_used] 만 전달
    public_problem = {"id": problem["_id"], "date": date, "week": problem["week"],"title": problem["title"], 
    "question": problem["question"], "difficulty": problem["difficulty"], 
    "hints": problem["hints"][:solve["hints_used"]], "created_at": problem["created_at"]}

    return render_template("quiz/today.html", date=date, problem=problem, solve=solve)


@quiz_bp.route("/hint", methods=["POST"])
@login_required
def hint():
    # TODO(팀원 A): 다음 힌트 1개 공개 + hints_used += 1, 힌트 텍스트 반환
    date = get_today_date()
    solve = db.solves.find_one({"user_id": g.user_id, "date": date})
    problem = db.problems.find_one({"date": date})
    
    if solve["hints_used"] < (len(problem["hints"])-1):
        db.solves.update_one({"user_id": g.user_id, "date": date}, {"$inc": {"hints_used": 1}})
        solve = db.solves.find_one({"user_id": g.user_id, "date": date})
        return jsonify({
            "success": True,
            "message": problem["hints"][solve["hints_used"]]["text"]
            })
    
    else:
        return jsonify({
                    "success": True,
                    "message": "모든 힌트를 소진했습니다"
                    })
            


@quiz_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    # TODO(팀원 A): 정규화 채점 → 정답 시 calc_score(duration, hints_used)로 score 저장
    user_answer = request.form.get("answer")
    user_answer = user_answer.strip().lower()
    date = get_today_date()
    problem = db.problems.find_one({"date": date})
    problem_list = [problem["answer"]]
    for i in problem["accepted"]:
        problem_list.append(i.strip())
    
    isCorrect = 0
    for i in problem_list:
        if i == user_answer:
            isCorrect = 1
            break
    
    if isCorrect:
        db.solves.update_one({"user_id": g.user_id, "date": date}, {"$set": {"status": "solved"}})
        db.solves.update_one({"user_id": g.user_id, "date": date}, {"$set": {"solved_at": datetime.now(timezone.utc)}})
        solve = db.solves.find_one({"user_id": g.user_id, "date": date})
        score = calc_score(solve["solved_at"], solve["hints_used"])
        db.solves.update_one({"user_id": g.user_id, "date": date}, {"$set": {"score": score}})
        return jsonify({
            "isCorrect": True,
            "score": score
        })
    
    else:
        db.solves.update_one({"user_id": g.user_id, "date": date}, {"$inc": {"attempts_used": 1}})
        return jsonify({
                    "isCorrect": False,
                    "score": None
                })


@quiz_bp.route("/archive")
@login_required
def archive():
    # TODO(팀원 A): 지난 문제 목록 + 정답률
    problems = list(db.problems.find({"date": {"$lt": get_today_date()}}).sort("date", -1))
    solved_list = list(db.solves.find({"status": "solved"}))
    failed_list = list(db.solves.find({"status": "failed"}))
    
    return render_template("quiz/archive.html", problems=problems, solved_list=solved_list, failed_list=failed_list)