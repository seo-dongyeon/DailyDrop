"""[데모 전용] 시연용 날짜 이동 라우트 — ⚠️ 배포 전 삭제!

메인화면 버튼으로 '오늘' 날짜를 앞뒤로 옮겨서
"날짜가 바뀌면 새 문제가 랜덤 출제된다"를 라이브로 보여주기 위한 데모 도구.
demo_bp를 app.py에서 register 안 하면 아무 영향 없음(폴더째 삭제하면 끝).
"""
from flask import Blueprint, redirect, url_for, request
from core.auth import login_required
from core.utils import advance_demo_date, reset_demo_date

demo_bp = Blueprint("demo", __name__)


@demo_bp.route("/demo/shift-day", methods=["POST"])
@login_required
def shift_day():
    """days만큼 데모 날짜 이동 (+1 다음날 / -1 이전날) 후 홈으로."""
    try:
        days = int(request.form.get("days", 1))
    except (TypeError, ValueError):
        days = 1
    advance_demo_date(days)
    return redirect(url_for("quiz.today"))


@demo_bp.route("/demo/reset", methods=["POST"])
@login_required
def reset():
    """데모 날짜 해제 → 실제 시간(오늘)으로 복귀."""
    reset_demo_date()
    return redirect(url_for("quiz.today"))
