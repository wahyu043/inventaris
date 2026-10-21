import functools
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import db

app = Flask(__name__)
app.config["SECRET_KEY"] = "ganti-nanti-untuk-produksi"   # kunci penanda tangan cookie session
db.init_app(app)


def login_required(view):
    """Decorator: halaman hanya bisa dibuka kalau sudah login."""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)   # tanda ? = cegah SQL injection
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        flash("Username atau password salah")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))