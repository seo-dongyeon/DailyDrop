"""[내 담당] 앱 팩토리 — 블루프린트 등록만. 실제 로직은 core/ · quiz/ · ranking/."""
import os
from flask import Flask
from dotenv import load_dotenv

from core.db import ensure_indexes
from core.auth import auth_bp
from quiz.routes import quiz_bp
from ranking.routes import ranking_bp
from demo.routes import demo_bp        # [데모 전용] 배포 전 제거

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

    app.register_blueprint(auth_bp)      # /signup /login /logout
    app.register_blueprint(quiz_bp)      # / /hint /submit /archive  (팀원 A)
    app.register_blueprint(ranking_bp)   # /ranking /history          (팀원 B)
    app.register_blueprint(demo_bp)      # [데모 전용] /demo/*  ⚠️ 배포 전 제거

    # 모든 템플릿에서 current_user(로그인 유저) 사용 가능 → base.html nav·유저메뉴
    @app.context_processor
    def inject_current_user():
        from flask import session
        from bson import ObjectId
        from core.db import db
        uid = session.get("user_id")
        if not uid:
            return {"current_user": None}
        try:
            return {"current_user": db.users.find_one({"_id": ObjectId(uid)})}
        except Exception:
            return {"current_user": None}

    try:
        ensure_indexes()
    except Exception as e:               # DB 미연결이어도 앱은 뜨게
        print(f"[warn] 인덱스 생성 건너뜀: {e}")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
