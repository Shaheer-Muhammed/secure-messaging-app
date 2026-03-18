from flask import Flask, render_template, request
import sqlite3
import bcrypt
from crypto import rsa_utils

app = Flask(__name__)

# --------------------------------
# Database Initialization
# --------------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        public_key TEXT,
        private_key TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        ciphertext TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# --------------------------------
# Home Page
# --------------------------------
@app.route("/")
def home():
    return "Secure Messaging Application is Running!"


# --------------------------------
# User Registration with RSA Keys
# --------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Generate RSA keys
        public_key, private_key = rsa_utils.generate_keys()

        # Store user in database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, public_key, private_key) VALUES (?, ?, ?, ?)",
                (username, hashed_password, public_key, private_key)
            )
            conn.commit()
            message = f"User '{username}' registered successfully with RSA keys!"
            print(message)  # اطبعها في الترمنال
        except sqlite3.IntegrityError:
            message = f"Username '{username}' already exists! Choose another username."
            print(message)
            return message
        finally:
            conn.close()

        return message

    return render_template("register.html")


# --------------------------------
# User Login
# --------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            stored_hash = user[0]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                print(f"User '{username}' logged in successfully!")
                return "Login Successful!"

        print(f"Login failed for user '{username}'")
        return "Invalid username or password"

    return render_template("login.html")


# --------------------------------
# Send Message
# --------------------------------
@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    if request.method == "POST":
        sender_username = request.form.get("sender", "shaheer")  # للتجربة نستخدم shaheer
        receiver_username = request.form["receiver"]
        message = request.form["message"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # جلب public key للمستقبل
        cursor.execute("SELECT id, public_key FROM users WHERE username = ?", (receiver_username,))
        receiver = cursor.fetchone()

        # جلب id المرسل
        cursor.execute("SELECT id FROM users WHERE username = ?", (sender_username,))
        sender = cursor.fetchone()

        if not receiver:
            return f"Receiver '{receiver_username}' not found! Check the username exactly."

        receiver_id, receiver_public_key = receiver
        sender_id = sender[0]

        # تشفير الرسالة باستخدام public key
        print(f"Encrypting message for receiver '{receiver_username}'...")
        encrypted_message = rsa_utils.encrypt_message(receiver_public_key, message)
        print(f"Encrypted message: {encrypted_message[:50]}...")  # جزء صغير للعرض

        # حفظ الرسالة المشفرة في قاعدة البيانات
        cursor.execute(
            "INSERT INTO messages (sender_id, receiver_id, ciphertext) VALUES (?, ?, ?)",
            (sender_id, receiver_id, encrypted_message)
        )

        conn.commit()
        conn.close()

        print(f"Message from '{sender_username}' to '{receiver_username}' saved successfully!")
        return "Message sent and encrypted successfully!"

    return render_template("send_message.html")


# --------------------------------
# View Messages
# --------------------------------
@app.route("/view_messages/<username>")
def view_messages(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # جلب id و private key للمستخدم
    cursor.execute("SELECT id, private_key FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        return f"User '{username}' not found!"
    user_id, private_key = user

    # جلب الرسائل الواردة لهذا المستخدم
    cursor.execute("""
        SELECT m.ciphertext, u.username
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.receiver_id = ?
    """, (user_id,))
    rows = cursor.fetchall()

    messages = []
    for ciphertext, sender_username in rows:
        decrypted = rsa_utils.decrypt_message(private_key, ciphertext)
        messages.append({"sender": sender_username, "content": decrypted})

    conn.close()
    return render_template("view_messages.html", messages=messages)


# --------------------------------
# Run Server
# --------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)