"""MongoDB 연결 + 인덱스 (공용). 팀원은 `from core.db import db` 만 하면 됨."""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

_uri = os.environ.get("MONGO_URI")
client = MongoClient(_uri)
db = client["dailydrop"]          # db.users / db.problems / db.solves


def ensure_indexes():
    """앱 시작 시 1회 호출 — 계약서(설계도)에 정의된 인덱스 보장."""
    db.users.create_index("username", unique=True)
    db.problems.create_index("date", unique=True)
    # 하루 1회 보장 + 재진입 상태복원
    db.solves.create_index([("user_id", ASCENDING), ("date", ASCENDING)],
                           unique=True)
    # 랭킹 조회 최적화: score DESC → solved_at ASC
    db.solves.create_index([("date", ASCENDING),
                            ("score", DESCENDING),
                            ("solved_at", ASCENDING)])
