"""공용 함수 (공용). 팀원은 `from core.utils import get_today_date, calc_score`."""
import os
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

# 점수 튜닝값 (밸런싱하며 조정) — 설계문서 §1.5
BASE_SCORE = 1000
HINT_TIME_PENALTY = 60    # 힌트 1개 = 실질경과 +60초
DECAY_PER_SEC = 1         # 1초당 1점 감점 → 실질 1000초에 0점 도달


def get_today_date(now=None):
    """DailyDrop '오늘' 날짜 문자열(YYYY-MM-DD, KST 기준).

    매일 오전 10시(KST)에 새 문제로 전환 → 10시 이전이면 '어제'로 계산.
    (서버 TZ가 UTC여도 항상 KST로 변환 → off-by-one 방지)
    데모용: 환경변수 DEBUG_TODAY 가 있으면 그 값을 그대로 반환.
    """
    debug = os.environ.get("DEBUG_TODAY")
    if debug:
        return debug
    if now is None:
        now = datetime.now(KST)
    else:
        now = now.astimezone(KST)
    if now.hour < 10:
        now = now - timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def calc_score(duration_sec, hints_used):
    """정답 확정 시 서버가 산출하는 점수(0~1000). ⚠️ 반드시 서버에서만 호출.

    실질경과초 = duration_sec + hints_used * HINT_TIME_PENALTY
    score      = max(0, round(1000 - 실질경과초 * DECAY_PER_SEC))
    """
    effective = duration_sec + hints_used * HINT_TIME_PENALTY
    return max(0, round(BASE_SCORE - effective * DECAY_PER_SEC))
