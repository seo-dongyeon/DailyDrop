"""공용 경계 로직 테스트 — ★핵심 챌린지(10시 경계, 점수 하한)."""
from datetime import datetime, timezone, timedelta

from core.utils import get_today_date, calc_score

KST = timezone(timedelta(hours=9))


# ---- calc_score (설계문서 §1.5 예시값) ----
def test_score_no_hints():
    assert calc_score(30, 0) == 970          # 30초, 힌트0


def test_score_one_hint():
    assert calc_score(20, 1) == 920          # 20 + 60 = 80


def test_score_three_hints():
    assert calc_score(45, 3) == 775          # 45 + 180 = 225


def test_score_five_hints():
    assert calc_score(300, 5) == 400         # 300 + 300 = 600


def test_score_floors_at_zero():
    assert calc_score(5000, 5) == 0          # 음수 방지


# ---- get_today_date (KST + 10시 경계) ----
def test_before_10am_is_yesterday():
    now = datetime(2026, 8, 25, 9, 0, tzinfo=KST)
    assert get_today_date(now) == "2026-08-24"


def test_at_10am_is_today():
    now = datetime(2026, 8, 25, 10, 0, tzinfo=KST)
    assert get_today_date(now) == "2026-08-25"


def test_after_10am_is_today():
    now = datetime(2026, 8, 25, 15, 30, tzinfo=KST)
    assert get_today_date(now) == "2026-08-25"


def test_utc_input_converted_to_kst():
    # UTC 02:00 == KST 11:00 → 오늘
    assert get_today_date(datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc)) == "2026-08-25"
    # UTC 00:00 == KST 09:00 → 10시 이전 → 어제
    assert get_today_date(datetime(2026, 8, 25, 0, 0, tzinfo=timezone.utc)) == "2026-08-24"
