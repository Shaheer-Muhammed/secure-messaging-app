from flask import Flask, render_template, request, redirect, session
import sqlite3
from crypto import rsa_utils

app = Flask(__name__)
app.secret_key = "secretkey"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        public_key, private_key = rsa_utils.generate_keys()

        db = get_db()

        db.execute(
            "INSERT INTO users (username,password,public_key,private_key) VALUES (?,?,?,?)",
            (username, password, public_key, private_key)
        )

        db.commit()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["username"] = username
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    db = get_db()

    users = db.execute(
        "SELECT username FROM users WHERE username != ?",
        (session["username"],)
    ).fetchall()

    return render_template("dashboard.html", users=users)


@app.route("/send", methods=["POST"])
def send_message():

    sender = session["username"]
    receiver = request.form["receiver"]
    message = request.form["message"]

    db = get_db()

    receiver_data = db.execute(
        "SELECT public_key FROM users WHERE username=?",
        (receiver,)
    ).fetchone()

    if receiver_data is None:
        return "User not found"

    receiver_public_key = receiver_data["public_key"]

    encrypted_message = rsa_utils.encrypt_message(
        receiver_public_key,
        message
    )

    db.execute(
        "INSERT INTO messages (sender,receiver,message) VALUES (?,?,?)",
        (sender, receiver, encrypted_message)
    )

    db.commit()

    return redirect("/messages")


@app.route("/messages")
def messages():

    if "username" not in session:
        return redirect("/login")

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username=?",
        (session["username"],)
    ).fetchone()

    messages = db.execute(
        "SELECT * FROM messages WHERE receiver=?",
        (session["username"],)
    ).fetchall()

    decrypted_messages = []

    for msg in messages:

        decrypted = rsa_utils.decrypt_message(
            user["private_key"],
            msg["message"]
        )

        decrypted_messages.append({
            "sender": msg["sender"],
            "message": decrypted
        })

    return render_template(
        "messages.html",
        messages=decrypted_messages
    )


if __name__ == "__main__":
    app.run(debug=True)