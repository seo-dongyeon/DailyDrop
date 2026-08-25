"""회원 인증 (세션 기반). 공용 데코레이터 login_required 제공.

팀원 사용법:
    from core.auth import login_required
    @quiz_bp.route("/"); @login_required
    def view():
        g.user_id  # 로그인한 유저의 ObjectId
"""
import bcrypt
from datetime import datetime, timezone
from functools import wraps
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, g)
from core.db import db

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    """미로그인 시 /login 으로 리다이렉트, 로그인 시 g.user_id 세팅."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        uid = session.get("user_id")
        if not uid:
            return redirect(url_for("auth.login"))
        g.user_id = ObjectId(uid)
        return view(*args, **kwargs)
    return wrapped


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        nickname = request.form.get("nickname") or username
        hashed = bcrypt.hashpw(password.encode("utf-8"),
                               bcrypt.gensalt()).decode("utf-8")
        try:
            db.users.insert_one({
                "username": username,
                "password": hashed,
                "nickname": nickname,
                "created_at": datetime.now(timezone.utc),
            })
        except DuplicateKeyError:
            return render_template("auth/signup.html",
                                   error="이미 존재하는 아이디입니다.")
        return redirect(url_for("auth.login"))
    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.users.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode("utf-8"),
                                   user["password"].encode("utf-8")):
            session["user_id"] = str(user["_id"])
            return redirect(url_for("quiz.today"))
        return render_template("auth/login.html",
                               error="아이디 또는 비밀번호가 틀렸습니다.")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
