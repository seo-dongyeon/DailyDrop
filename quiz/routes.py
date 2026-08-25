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
    # TODO(팀원 A): 잠긴 힌트 노출 금지 → problem.hints[:solve.hints_used] 만 전달
    return render_template("quiz/today.html",
                           date=date, problem=problem, solve=solve)


@quiz_bp.route("/hint", methods=["POST"])
@login_required
def hint():
    # TODO(팀원 A): 다음 힌트 1개 공개 + hints_used += 1, 힌트 텍스트 반환
    return jsonify({"todo": "hint endpoint"})


@quiz_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    # TODO(팀원 A): 정규화 채점 → 정답 시 calc_score(duration, hints_used)로 score 저장
    return jsonify({"todo": "submit endpoint"})


@quiz_bp.route("/archive")
@login_required
def archive():
    # TODO(팀원 A): 지난 문제 목록 + 내 결과
    problems = list(db.problems.find({"date": {"$lt": get_today_date()}})
                    .sort("date", -1))
    return render_template("quiz/archive.html", problems=problems)
