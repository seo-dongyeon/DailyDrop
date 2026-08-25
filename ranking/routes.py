"""[팀원 B 담당] 랭킹 · 통계 · 내 기록.

공용 도구: db(core.db) / login_required(core.auth) / get_today_date(core.utils)
스키마·복붙 스니펫: docs/DailyDrop-백엔드-설계.md §3 참고
랭킹 정렬 = score DESC → solved_at ASC (점수제 확정).
아래는 '돌아가는 스텁' — TODO 부분을 실제 로직으로 채우면 됨.
"""
from flask import Blueprint, render_template, g
from core.db import db
from core.auth import login_required
from core.utils import get_today_date

ranking_bp = Blueprint("ranking", __name__)


@ranking_bp.route("/ranking")
@login_required
def ranking():
    date = get_today_date()
    # TODO(팀원 B): 닉네임 조인 + 내 순위 강조
    rows = list(db.solves.find({"date": date, "status": "solved"})
                .sort([("score", -1), ("solved_at", 1)]))
    return render_template("ranking/ranking.html", date=date, rows=rows)


@ranking_bp.route("/history")
@login_required
def history():
    # TODO(팀원 B): 내 풀이 히스토리 + 통계(총 풀이·평균 힌트·streak)
    mine = list(db.solves.find({"user_id": g.user_id}).sort("date", -1))
    return render_template("ranking/history.html", mine=mine)
