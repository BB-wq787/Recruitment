import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 清空用户'cc'的stamps记录
cur.execute("UPDATE users SET stamps = ? WHERE name = ?", ("", "cc"))
conn.commit()

# 验证修改结果
cur.execute("SELECT name, stamps FROM users WHERE name = ?", ("cc",))
user = cur.fetchone()
if user:
    print(f"用户 {user[0]} 的stamps已清空: \"{user[1]}\"")
else:
    print("用户 cc 不存在")

conn.close()








