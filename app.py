import bcrypt
import jwt
import datetime
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, make_response, g
from dotenv import load_dotenv
from functools import wraps
import os

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
# DB 연결 (접속 문자열은 .env의 MONGO_URI로만 관리 — 코드/깃에 시크릿 금지)
load_dotenv()
uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)
db = client["dailydrop"]


@app.route("/")
def home():
    return "Hello, DailyDrop!"


@app.route("/signup", methods=["GET", "POST"])
def singup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed = bcrypt.hashpw(password.encode(
            "utf-8"), bcrypt.gensalt()).decode("utf-8")
        db.users.insert_one({
            "username": username,
            "password": hashed
        })
        return redirect("/signup")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db.users.find_one({"username": username})

        if user and bcrypt.checkpw(password.encode("utf-8"),
                                   user["password"].encode("utf-8")):
            return "로그인 성공"
        else:
            return "아이디 또는 비밀번호가 틀렸습니다."
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
