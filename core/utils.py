"""공용 함수 (공용). 팀원은 `from core.utils import get_today_date, calc_score`."""
import os
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

# 점수 튜닝값 (밸런싱하며 조정) — 설계문서 §1.5
BASE_SCORE = 1000
HINT_TIME_PENALTY = 180    # 힌트 1개 = 실질경과 180초
SECONDS_PER_POINT  = 60         # 60초(1분) 마다 1점 감점

# ===== [데모 전용] 시연용 날짜 오버라이드 (⚠️ 배포 전 제거!) =====
_DEMO_DATE = None   # 값이 있으면 그 날짜로 강제 (버튼으로 조작)


def advance_demo_date(days=1):
    """데모: 강제 날짜를 days만큼 이동 (+1 다음날 / -1 이전날)."""
    global _DEMO_DATE
    base = _DEMO_DATE or get_today_date()
    d = datetime.strptime(base, "%Y-%m-%d") + timedelta(days=days)
    _DEMO_DATE = d.strftime("%Y-%m-%d")
    return _DEMO_DATE


def reset_demo_date():
    """데모: 강제 날짜 해제 → 실제 시간으로 복귀."""
    global _DEMO_DATE
    _DEMO_DATE = None
# ================================================================


def get_today_date(now=None):
    """DailyDrop '오늘' 날짜 문자열(YYYY-MM-DD, KST 기준).

    매일 오전 10시(KST)에 새 문제로 전환 → 10시 이전이면 '어제'로 계산.
    (서버 TZ가 UTC여도 항상 KST로 변환 → off-by-one 방지)
    데모용: 환경변수 DEBUG_TODAY 가 있으면 그 값을 그대로 반환.
    """
    if _DEMO_DATE:                    # [데모] 강제 날짜가 있으면 우선
        return _DEMO_DATE
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

    실질경과초 = duration_sec + hints_used // HINT_TIME_PENALTY
    score      = max(0, round(1000 - 실질경과초 // SECONDS_PER_POINT ))
    """
    effective = duration_sec + hints_used * HINT_TIME_PENALTY
    return max(0, round(BASE_SCORE - effective // SECONDS_PER_POINT ))
