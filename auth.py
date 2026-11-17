"""Регистрация, вход по e-mail и гостевой вход (US-01, US-02, US-03)."""
import re
import sqlite3
import functools

from flask import (Blueprint, current_app, flash, g, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("auth", __name__)

NICK_RE = re.compile(r"^[\w\- ]{2,20}$", re.UNICODE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 6

SCHEMA = """
CREATE TABLE IF NOT EXISTS account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nick TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_confirmed INTEGER NOT NULL DEFAULT 0
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().executescript(SCHEMA)


def valid_nick(nick: str) -> bool:
    return bool(NICK_RE.match(nick)) and nick.strip() == nick


@bp.before_app_request
def load_user():
    """g.user = {'nick', 'guest', 'account_id'} или None."""
    nick = session.get("nick")
    g.user = None
    if nick:
        g.user = {"nick": nick, "guest": session.get("guest", False),
                  "account_id": session.get("account_id")}


def login_required(view):
    @functools.wraps(view)
    def wrapped(*a, **kw):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*a, **kw)
    return wrapped


def _start_session(nick, guest, account_id=None):
    session.clear()
    session["nick"] = nick
    session["guest"] = guest
    if account_id is not None:
        session["account_id"] = account_id


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("lobby"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM account WHERE email = ?", (email,)).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            flash("Неверный e-mail или пароль.")
        else:
            _start_session(row["nick"], False, row["id"])
            return redirect(url_for("lobby"))
    return render_template("login.html", tab="email")


@bp.route("/guest", methods=["GET", "POST"])
def guest():
    if g.user:
        return redirect(url_for("lobby"))
    if request.method == "POST":
        nick = request.form.get("nick", "").strip()
        if not valid_nick(nick):
            flash("Имя игрока: 2–20 символов (буквы, цифры, пробел, дефис).")
        else:
            _start_session(nick, True)
            return redirect(url_for("lobby"))
    return render_template("login.html", tab="guest")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("lobby"))
    if request.method == "POST":
        nick = request.form.get("nick", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        repeat = request.form.get("repeat", "")
        error = None
        if not valid_nick(nick):
            error = "Имя игрока: 2–20 символов (буквы, цифры, пробел, дефис)."
        elif not EMAIL_RE.match(email):
            error = "Введите корректный e-mail."
        elif len(password) < MIN_PASSWORD:
            error = f"Пароль должен быть не короче {MIN_PASSWORD} символов."
        elif password != repeat:
            error = "Пароли не совпадают."
        if error is None:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO account (nick, email, password_hash) VALUES (?,?,?)",
                    (nick, email, generate_password_hash(password)))
                db.commit()
            except sqlite3.IntegrityError:
                error = "Аккаунт с таким e-mail уже существует."
            else:
                _start_session(nick, False, cur.lastrowid)
                return redirect(url_for("lobby"))
        flash(error)
    return render_template("register.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
