"""[팀원 A 담당] 오늘의 퀴즈 · 지난 문제.

공용 도구: db(core.db) / login_required(core.auth) / get_today_date, calc_score(core.utils)
스키마·복붙 스니펫: docs/DailyDrop-백엔드-설계.md §3 참고
아래는 '돌아가는 스텁' — TODO 부분을 실제 로직으로 채우면 됨.
"""
from datetime import datetime, timezone, timedelta
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

    if solve is None:
        db.solves.insert_one({"user_id": g.user_id, "problem_id": problem["_id"],
                              "date": date, "status": "solving", "hints_used": 0, "attempts_used": 0,
                              "started_at": datetime.now(timezone.utc), "solved_at": None,
                              "duration_sec": 0, "score": 0})

        solve = db.solves.find_one({"user_id": g.user_id, "date": date})

    return render_template("quiz/today.html", date=date, problem=problem, solve=solve)


@quiz_bp.route("/hint", methods=["POST"])
@login_required
def hint():
    date = get_today_date()
    solve = db.solves.find_one({"user_id": g.user_id, "date": date})
    problem = db.problems.find_one({"date": date})

    if solve["hints_used"] < (len(problem["hints"])):
        idx = solve["hints_used"]
        db.solves.update_one({"user_id": g.user_id, "date": date}, {
                             "$inc": {"hints_used": 1}})
        return jsonify({
            "success": True,
            "message": problem["hints"][idx]["text"]
        })

    else:
        return jsonify({
            "success": False,
            "message": "모든 힌트를 소진했습니다"
        })


@quiz_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    KST = timezone(timedelta(hours=9))

    user_answer = request.form.get("answer")
    user_answer = user_answer.strip().lower()
    date = get_today_date()
    problem = db.problems.find_one({"date": date})
    solve = db.solves.find_one({"user_id": g.user_id, "date": date})
    problem_list = [problem["answer"]]
    for i in problem["accepted"]:
        problem_list.append(i.strip())
    release_time = datetime.strptime(problem["date"], "%Y-%m-%d").replace(
        hour=10,
        tzinfo=KST
    )

    isCorrect = 0
    for i in problem_list:
        if i == user_answer:
            isCorrect = 1
            break

    if isCorrect:
        db.solves.update_one({"user_id": g.user_id, "date": date}, {
                             "$set": {"status": "solved"}})
        db.solves.update_one({"user_id": g.user_id, "date": date}, {
                             "$set": {"solved_at": datetime.now(timezone.utc)}})
        solve = db.solves.find_one({"user_id": g.user_id, "date": date})
        solved_at_utc = solve["solved_at"].replace(tzinfo=timezone.utc)
        started_at_utc = solve["started_at"].replace(tzinfo=timezone.utc)
        duration = (solved_at_utc.astimezone(KST) - release_time).total_seconds()
        start_to_solve = (solved_at_utc.astimezone(KST) - started_at_utc.astimezone(KST)).total_seconds()
        db.solves.update_one({"user_id": g.user_id, "date": date}, {
                                     "$set": {"duration_sec": start_to_solve}})
        score = calc_score(duration, solve["hints_used"])
        db.solves.update_one({"user_id": g.user_id, "date": date}, {
                             "$set": {"score": score}})
        return jsonify({
            "isCorrect": True,
            "score": score
        })

    else:
        db.solves.update_one({"user_id": g.user_id, "date": date}, {
                             "$inc": {"attempts_used": 1}})
        if solve["hints_used"] < (len(problem["hints"])):
                db.solves.update_one({"user_id": g.user_id, "date": date}, {
                                     "$inc": {"hints_used": 1}})
                solve = db.solves.find_one({"user_id": g.user_id, "date": date})
                return jsonify({
                            "isCorrect": False,
                            "score": None,
                            "message": problem["hints"][solve["hints_used"]-1]["text"]
                        })
                
        else:
            db.solves.update_one({"user_id": g.user_id, "date": date}, {
                                         "$set": {"status": "failed"}})
            return jsonify({
                "isCorrect": False,
                "isFailed": True,
                "score": None
            })


@quiz_bp.route("/archive")
@login_required
def archive():
    problems = list(db.problems.find(
        {"date": {"$lt": get_today_date()}}).sort("date", -1))
    solved_list = list(db.solves.find({"status": "solved"}))
    failed_list = list(db.solves.find({"status": "failed"}))
    accu_list = []
    for i in problems:
        failed_num = 0
        solved_num = 0
        for x in solved_list:
            if i["date"] == x["date"]:
                solved_num += 1
        for y in failed_list:
            if i["date"] == y["date"]:
                failed_num += 1
        if solved_num + failed_num == 0:
            accu = 0
        else:
            accu = solved_num / (solved_num + failed_num)
        accu_list.append(accu * 100)
    return render_template("quiz/archive.html", problems=problems, accu_list=accu_list)
