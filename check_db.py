import sqlite3

# افتح قاعدة البيانات
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# اعرض كل المستخدمين
cursor.execute("SELECT id, username, password_hash, public_key, private_key FROM users")
users = cursor.fetchall()

for user in users:
    print("ID:", user[0])
    print("Username:", user[1])
    print("Password Hash:", user[2])
    print("Public Key:", user[3][:50] + "...")  # خلي العرض مختصر
    print("Private Key:", user[4][:50] + "...")
    print("-" * 40)

conn.close()