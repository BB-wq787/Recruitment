from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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
    # Create the canonical (new) users table without gender/age
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

    if not name or not email or not password:
        flash("Name, email, and password are required.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()
    # Prevent duplicate user name or email
    cur.execute(
        "SELECT name, email FROM users WHERE name = ? OR email = ?",
        (name, email),
    )
    existing = cur.fetchone()
    if existing:
        # check which field conflicts
        existing_name = existing["name"] if "name" in existing.keys() else None
        existing_email = existing["email"] if "email" in existing.keys() else None
        if existing_name == name:
            flash("This user name is already taken. Please choose a different name.", "danger")
        elif existing_email == email:
            flash("This email is already registered. Please sign in or use another email.", "danger")
        else:
            flash("Account already exists. Please sign in.", "danger")
        conn.close()
        return redirect(url_for("index"))

    try:
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
        # Fallback: unique constraint violated (email), inform user
        flash("This email is already registered. Please sign in or use another email.", "danger")
    finally:
        conn.close()

    # Redirect back to index but skip the splash on redirect (only show splash on initial open)
    return redirect(url_for("index") + "?no_splash=1#login")


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

    # After resetting password, go back to index but skip the splash
    return redirect(url_for("index") + "?no_splash=1")


if __name__ == "__main__":
    init_db()
    # 0.0.0.0 方便在局域網內用手機訪問；正式環境可根據需要調整
    app.run(host="0.0.0.0", port=5000, debug=True)