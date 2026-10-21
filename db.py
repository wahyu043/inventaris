import sqlite3
import click
from flask import g
from werkzeug.security import generate_password_hash


def get_db():
    # g = objek penyimpanan sementara selama 1 request
    if "db" not in g:
        g.db = sqlite3.connect("database.db")
        g.db.row_factory = sqlite3.Row   # hasil query bisa diakses pakai nama kolom
    return g.db


def close_db(e=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@click.command("init-db")
def init_db_command():
    """Buat tabel + user admin awal."""
    conn = get_db()
    with open("schema.sql") as f:
        conn.executescript(f.read())
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
        ("admin", generate_password_hash("admin123", method="pbkdf2:sha256")),
    )
    conn.commit()
    click.echo("Database siap. Login: admin / admin123")


def init_app(app):
    app.teardown_appcontext(close_db)   # tutup koneksi otomatis tiap request selesai
    app.cli.add_command(init_db_command)