from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "change_this_to_a_secret_key"  # 用於 session 和 flash，正式環境請改成隨機值

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            age INTEGER,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    gender = request.form.get("gender", "").strip()
    age = request.form.get("age", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not email or not password:
        flash("姓名、郵箱和密碼為必填項", "danger")
        return redirect(url_for("index") + "#register")

    try:
        age_int = int(age) if age else None
    except ValueError:
        flash("年齡必須為數字", "danger")
        return redirect(url_for("index") + "#register")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (name, gender, age, email, phone, password)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, gender, age_int, email, phone, password),
        )
        conn.commit()
        flash("賬號創建成功，請使用姓名或郵箱登入", "success")
    except sqlite3.IntegrityError:
        flash("該郵箱已被註冊，請使用其他郵箱或直接登入", "danger")
    finally:
        conn.close()

    return redirect(url_for("index") + "#login")


@app.route("/login", methods=["POST"])
def login():
    account = request.form.get("account", "").strip()  # 姓名或郵箱
    password = request.form.get("password", "").strip()

    if not account or not password:
        flash("請輸入賬號和密碼", "danger")
        return redirect(url_for("index") + "#login")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM users
        WHERE (name = ? OR email = ?) AND password = ?
        """,
        (account, account, password),
    )
    user = cur.fetchone()
    conn.close()

    if user:
        session["user_name"] = user["name"]
        flash(f"歡迎，{user['name']}！登入成功。", "success")
        return redirect(url_for("welcome"))
    else:
        flash("賬號或密碼錯誤", "danger")
        return redirect(url_for("index") + "#login")


@app.route("/welcome", methods=["GET"])
def welcome():
    user_name = session.get("user_name")
    if not user_name:
        return redirect(url_for("index"))
    return render_template("welcome.html", user_name=user_name)


@app.route("/reset_password", methods=["POST"])
def reset_password():
    account = request.form.get("account", "").strip()  # 姓名或郵箱
    new_password = request.form.get("new_password", "").strip()

    if not account or not new_password:
        flash("請輸入賬號和新密碼", "danger")
        return redirect(url_for("index") + "#reset")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET password = ?
        WHERE name = ? OR email = ?
        """,
        (new_password, account, account),
    )
    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated:
        flash("密碼重設成功，請使用新密碼登入", "success")
    else:
        flash("未找到該賬號，請確認姓名或郵箱是否正確", "danger")

    return redirect(url_for("index") + "#login")


if __name__ == "__main__":
    init_db()
    # 0.0.0.0 方便在局域網內用手機訪問；正式環境可根據需要調整
    app.run(host="0.0.0.0", port=5000, debug=True)


