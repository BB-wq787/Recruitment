from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
import sys
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "change_this_to_a_secret_key"  # 用於 session 和 flash，正式環境請改成隨機值

def get_db_connection():
    # 检查是否有PostgreSQL连接字符串
    database_url = os.environ.get('DATABASE_URL')

    if database_url and database_url.startswith('postgres://'):
        # Railway提供的PostgreSQL URL
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            # 转换PostgreSQL URL格式
            url = urlparse(database_url)
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                user=url.username,
                password=url.password,
                database=url.path[1:],  # 去掉开头的/
                cursor_factory=RealDictCursor
            )
            return conn
        except ImportError:
            print("Warning: psycopg2 not installed, falling back to SQLite")
            database_url = None

    # 默认使用SQLite（本地开发或Railway未配置PostgreSQL时）
    DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 检查是否为PostgreSQL
    is_postgres = hasattr(conn, 'get_dsn_parameters')

    if is_postgres:
        # PostgreSQL表创建
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                password TEXT NOT NULL,
                stamps TEXT DEFAULT ''
            )
            """
        )
    else:
        # SQLite表创建
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                password TEXT NOT NULL,
                stamps TEXT DEFAULT ''
            )
            """
        )

    # 数据库迁移逻辑（仅SQLite支持）
    if not is_postgres:
        # Migrate existing table to remove 'gender' and 'age' columns if present.
        # SQLite doesn't support DROP COLUMN; create a new table and copy relevant data.
        cur.execute("PRAGMA table_info(users)")
        existing_columns = [r["name"] for r in cur.fetchall()]
        desired_columns = {"id", "name", "email", "phone", "password", "stamps"}
        # If there are extra columns (like gender/age) present in the actual table (e.g., from older schema),
        # copy only the desired columns into a fresh table.
        if set(existing_columns) != desired_columns:
            try:
                # Build select list for copy, using literals/defaults when a column is missing.
                select_cols = []
                for col in ["id", "name", "email", "phone", "password", "stamps"]:
                    if col in existing_columns:
                        select_cols.append(col)
                    else:
                        # Provide a sensible default for missing columns
                        if col == "id":
                            select_cols.append("NULL")
                        elif col == "stamps":
                            select_cols.append("'' AS stamps")
                        else:
                            select_cols.append("''")

                cur.execute("CREATE TABLE IF NOT EXISTS users_new (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE, phone TEXT, password TEXT NOT NULL, stamps TEXT DEFAULT '')")
                cur.execute(
                    "INSERT INTO users_new (id, name, email, phone, password, stamps) SELECT " + ", ".join(select_cols) + " FROM users"
                )
                cur.execute("DROP TABLE users")
                cur.execute("ALTER TABLE users_new RENAME TO users")
            except Exception:
                # Fall back: if migration fails, ignore and keep the existing table as-is.
                conn.rollback()
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()

    # 验证必填字段
    if not name or not email or not password:
        flash("Name, email, and password are required.", "danger")
        return redirect(url_for("index"))

    # 验证密码长度
    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 检查用户名是否已存在
        cur.execute("SELECT id FROM users WHERE name = ?", (name,))
        if cur.fetchone():
            flash("This username is already taken. Please choose a different username.", "danger")
            return redirect(url_for("index"))

        cur.execute(
            """
            INSERT INTO users (name, email, phone, password)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, phone, password),
        )
        conn.commit()
        flash("Account created. You can now sign in using your name or email.", "success")
    except sqlite3.IntegrityError:
        flash("This email is already registered. Please sign in or use another email.", "danger")
    finally:
        conn.close()

    return redirect(url_for("index") + "#login")


@app.route("/login", methods=["POST"])
def login():
    account = request.form.get("account", "").strip()  # 姓名或郵箱
    password = request.form.get("password", "").strip()

    if not account or not password:
        flash("Please enter account and password.", "danger")
        return redirect(url_for("index") + "?no_splash=1")

    conn = get_db_connection()
    cur = conn.cursor()
    # 先檢查賬號是否存在
    cur.execute(
        """
        SELECT * FROM users
        WHERE name = ? OR email = ?
        """,
        (account, account),
    )
    user = cur.fetchone()
    
    if not user:
        conn.close()
        flash("Account not found. Please check your account name or email.", "danger")
        return redirect(url_for("index") + "?no_splash=1")
    
    # 賬號存在，檢查密碼
    if user["password"] != password:
        conn.close()
        flash("Incorrect password. Please try again.", "danger")
        return redirect(url_for("index") + "?no_splash=1")
    
    # 登錄成功
    session["user_name"] = user["name"]
    flash(f"Welcome, {user['name']}! Signed in successfully.", "success")
    conn.close()
    return redirect(url_for("welcome"))


@app.route("/welcome", methods=["GET"])
def welcome():
    user_name = session.get("user_name")
    if not user_name:
        return redirect(url_for("index"))
    return render_template("welcome.html", user_name=user_name)


@app.route("/activity", methods=["GET"])
def activity():
    user_name = session.get("user_name")
    if not user_name:
        return redirect(url_for("index"))
    return render_template("activity.html", user_name=user_name)


@app.route("/apply", methods=["GET"])
def apply():
    user_name = session.get("user_name")
    if not user_name:
        return redirect(url_for("index"))
    return render_template("apply.html", user_name=user_name)


@app.route("/estamp", methods=["GET"])
def estamp():
    user_name = session.get("user_name")
    if not user_name:
        return redirect(url_for("index"))
    
    # 获取用户已收集的stamps
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT stamps FROM users WHERE name = ?", (user_name,))
    user = cur.fetchone()
    stamps_str = ""
    if user:
        try:
            stamps_str = user["stamps"] if user["stamps"] else ""
        except (KeyError, IndexError):
            stamps_str = ""
    conn.close()
    
    # 解析stamps字符串为列表
    collected_stamps = [int(s) for s in stamps_str.split(",") if s.strip()] if stamps_str else []
    
    return render_template("estamp.html", user_name=user_name, collected_stamps=collected_stamps)


@app.route("/estamp/save", methods=["POST"])
def save_stamps():
    user_name = session.get("user_name")
    if not user_name:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        data = request.get_json()
        stamps = data.get("stamps", [])
        stamps_str = ",".join(map(str, sorted(stamps)))  # 排序确保顺序一致
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET stamps = ? WHERE name = ?", (stamps_str, user_name))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("index") + "?no_splash=1")


@app.route("/reset_password", methods=["POST"])
def reset_password():
    account = request.form.get("account", "").strip()  # 姓名或郵箱
    new_password = request.form.get("new_password", "").strip()

    if not account or not new_password:
        flash("Please enter account and new password.", "danger")
        return redirect(url_for("index"))

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
        flash("Password has been reset. Please sign in with your new password.", "success")
    else:
        flash("Account not found. Please check the name or email.", "danger")

    return redirect(url_for("index"))


@app.route("/admin/users")
def admin_users():
    # 检查是否为管理员（这里简单检查session中的用户名）
    # 你可以修改这个逻辑来实现更安全的管理员验证
    if not session.get("user_name") or session.get("user_name") not in ["admin", "cc"]:  # 替换为你的管理员用户名
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("welcome"))

    conn = get_db_connection()
    cur = conn.cursor()

    # 获取所有用户数据
    if hasattr(conn, 'get_dsn_parameters'):  # PostgreSQL
        cur.execute("SELECT id, name, email, phone, stamps FROM users ORDER BY id")
    else:  # SQLite
        cur.execute("SELECT id, name, email, phone, stamps FROM users ORDER BY id")

    users = cur.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users)


# Railway会自动调用这个应用实例
if __name__ == "__main__":
    init_db()
    # 本地开发时使用
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_ENV") == "development")