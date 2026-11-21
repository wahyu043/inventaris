import functools
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash
import db

app = Flask(__name__)
app.config["SECRET_KEY"] = "ganti-nanti-untuk-produksi"   # kunci penanda tangan cookie session
db.init_app(app)


@app.context_processor
def inject_db_helpers():
    return {"db": db}


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
    conn = db.get_db()
    ringkasan = conn.execute("""
        SELECT
            COUNT(DISTINCT b.kode) AS total_jenis_barang,
            COUNT(t.id) AS total_transaksi,
            COALESCE(SUM(CASE
                WHEN t.jenis = 'Masuk' THEN t.jumlah
                WHEN t.jenis = 'Keluar' THEN -t.jumlah
                ELSE 0
            END), 0) AS total_stok
        FROM barang b
        LEFT JOIN transaksi t ON t.kode_barang = b.kode
    """).fetchone()
    batas_stok_rendah = 5
    stok_rendah = conn.execute("""
        SELECT b.kode, b.nama,
               COALESCE(SUM(CASE
                   WHEN t.jenis = 'Masuk' THEN t.jumlah
                   WHEN t.jenis = 'Keluar' THEN -t.jumlah
                   ELSE 0
               END), 0) AS stok
        FROM barang b
        LEFT JOIN transaksi t ON t.kode_barang = b.kode
        GROUP BY b.kode, b.nama
        HAVING stok <= ?
        ORDER BY stok, b.nama
    """, (batas_stok_rendah,)).fetchall()
    return render_template("index.html", ringkasan=ringkasan,
                           stok_rendah=stok_rendah,
                           batas_stok_rendah=batas_stok_rendah)

@app.route("/barang")
@login_required
def barang():
    rows = db.get_db().execute("""
        SELECT b.kode, b.nama, b.aktif,
               COALESCE(SUM(CASE WHEN t.jenis = 'Masuk' THEN t.jumlah ELSE -t.jumlah END), 0) AS stok
        FROM barang b
        LEFT JOIN transaksi t ON t.kode_barang = b.kode
        GROUP BY b.kode, b.nama
        ORDER BY b.nama
    """).fetchall()
    return render_template("barang.html", rows=rows)


@app.route("/barang/tambah", methods=["GET", "POST"])
@login_required
def barang_tambah():
    if request.method == "POST":
        kode = request.form.get("kode", "").strip()
        nama = request.form.get("nama", "").strip()
        if not kode or not nama:
            flash("Kode dan nama barang wajib diisi", "error")
        elif db.get_db().execute("SELECT 1 FROM barang WHERE kode = ?", (kode,)).fetchone():
            flash("Kode barang sudah digunakan", "error")
        else:
            conn = db.get_db()
            conn.execute("INSERT INTO barang (kode, nama, aktif) VALUES (?, ?, 1)", (kode, nama))
            conn.commit()
            flash("Barang berhasil ditambahkan", "ok")
            return redirect(url_for("barang"))
    return render_template("barang_form.html", data=None)


@app.route("/barang/<kode>/ubah", methods=["GET", "POST"])
@login_required
def barang_ubah(kode):
    conn = db.get_db()
    data = conn.execute("SELECT kode, nama FROM barang WHERE kode = ?", (kode,)).fetchone()
    if data is None:
        abort(404)
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama barang wajib diisi", "error")
        else:
            conn.execute("UPDATE barang SET nama = ? WHERE kode = ?", (nama, kode))
            conn.commit()
            flash("Nama barang berhasil diubah", "ok")
            return redirect(url_for("barang"))
    return render_template("barang_form.html", data=data)


@app.route("/barang/<kode>/status", methods=["POST"])
@login_required
def barang_status(kode):
    conn = db.get_db()
    data = conn.execute("SELECT aktif FROM barang WHERE kode = ?", (kode,)).fetchone()
    if data is None:
        abort(404)
    status = 0 if data["aktif"] else 1
    conn.execute("UPDATE barang SET aktif = ? WHERE kode = ?", (status, kode))
    conn.commit()
    flash("Barang dinonaktifkan" if not status else "Barang diaktifkan kembali", "ok")
    return redirect(url_for("barang"))

@app.route("/masuk")
@login_required
def masuk_list():
    rows = db.get_db().execute("""
        SELECT t.id, t.tanggal, t.kode_barang, b.nama, t.jumlah, t.no_faktur
        FROM transaksi t
        JOIN barang b ON b.kode = t.kode_barang
        WHERE t.jenis = 'Masuk'
        ORDER BY t.tanggal DESC, t.id DESC
    """).fetchall()
    return render_template("masuk_list.html", rows=rows)

@app.route("/masuk/tambah", methods=["GET", "POST"])
@login_required
def masuk_tambah():
    conn = db.get_db()
    daftar_barang = conn.execute("SELECT kode, nama FROM barang WHERE aktif = 1 ORDER BY nama").fetchall()

    if request.method == "POST":
        tanggal = request.form["tanggal"]
        kode = request.form["kode_barang"]
        no_faktur = request.form["no_faktur"].strip() or None
        try:
            jumlah = int(request.form["jumlah"])
        except ValueError:
            jumlah = 0

        if not tanggal or jumlah <= 0:
            flash("Tanggal wajib diisi dan jumlah harus lebih dari 0", "error")
        else:
            conn.execute(
                "INSERT INTO transaksi (tanggal, jenis, kode_barang, jumlah, no_faktur) "
                "VALUES (?, 'Masuk', ?, ?, ?)",
                (tanggal, kode, jumlah, no_faktur),
            )
            conn.commit()
            flash("Barang masuk berhasil ditambahkan", "ok")
            return redirect(url_for("masuk_list"))   # PRG: redirect setelah POST

    return render_template("masuk_form.html", daftar_barang=daftar_barang,
                           data=None, hari_ini=date.today().isoformat())

def ambil_masuk(id):
    """Ambil 1 transaksi masuk, atau tampilkan 404 kalau tidak ada."""
    row = db.get_db().execute(
        "SELECT t.*, b.nama FROM transaksi t JOIN barang b ON b.kode = t.kode_barang "
        "WHERE t.id = ? AND t.jenis = 'Masuk'", (id,)
    ).fetchone()
    if row is None:
        abort(404)
    return row


@app.route("/masuk/<int:id>/ubah", methods=["GET", "POST"])
@login_required
def masuk_ubah(id):
    data = ambil_masuk(id)

    if request.method == "POST":
        tanggal = request.form["tanggal"]
        no_faktur = request.form["no_faktur"].strip() or None
        try:
            jumlah = int(request.form["jumlah"])
        except ValueError:
            jumlah = 0

        if not tanggal or jumlah <= 0:
            flash("Tanggal wajib diisi dan jumlah harus lebih dari 0", "error")
        elif db.stok_barang(data["kode_barang"]) - data["jumlah"] + jumlah < 0:
            flash("Ditolak: stok barang akan menjadi minus", "error")
        else:
            conn = db.get_db()
            conn.execute(
                "UPDATE transaksi SET tanggal = ?, jumlah = ?, no_faktur = ? WHERE id = ?",
                (tanggal, jumlah, no_faktur, id),
            )
            conn.commit()
            flash("Barang masuk berhasil diubah", "ok")
            return redirect(url_for("masuk_list"))

    return render_template("masuk_form.html", data=data, daftar_barang=[], hari_ini="")


@app.route("/masuk/<int:id>/hapus", methods=["POST"])
@login_required
def masuk_hapus(id):
    data = ambil_masuk(id)
    if db.stok_barang(data["kode_barang"]) - data["jumlah"] < 0:
        flash("Tidak bisa dihapus: stok barang akan menjadi minus", "error")
    else:
        conn = db.get_db()
        conn.execute("DELETE FROM transaksi WHERE id = ?", (id,))
        conn.commit()
        flash("Barang masuk berhasil dihapus", "ok")
    return redirect(url_for("masuk_list"))


@app.route("/keluar")
@login_required
def keluar_list():
    rows = db.get_db().execute("""
        SELECT t.id, t.tanggal, t.kode_barang, b.nama, t.jumlah, t.no_faktur
        FROM transaksi t
        JOIN barang b ON b.kode = t.kode_barang
        WHERE t.jenis = 'Keluar'
        ORDER BY t.tanggal DESC, t.id DESC
    """).fetchall()
    return render_template("keluar_list.html", rows=rows)


def ambil_keluar(id):
    """Ambil 1 transaksi keluar, atau tampilkan 404 kalau tidak ada."""
    row = db.get_db().execute(
        "SELECT t.*, b.nama FROM transaksi t JOIN barang b ON b.kode = t.kode_barang "
        "WHERE t.id = ? AND t.jenis = 'Keluar'", (id,)
    ).fetchone()
    if row is None:
        abort(404)
    return row


@app.route("/keluar/tambah", methods=["GET", "POST"])
@login_required
def keluar_tambah():
    conn = db.get_db()
    daftar_barang = conn.execute("SELECT kode, nama FROM barang WHERE aktif = 1 ORDER BY nama").fetchall()

    if request.method == "POST":
        tanggal = request.form["tanggal"]
        kode = request.form["kode_barang"]
        no_faktur = request.form["no_faktur"].strip() or None
        try:
            jumlah = int(request.form["jumlah"])
        except ValueError:
            jumlah = 0

        barang = conn.execute("SELECT 1 FROM barang WHERE kode = ?", (kode,)).fetchone()
        if not tanggal or jumlah <= 0:
            flash("Tanggal wajib diisi dan jumlah harus lebih dari 0", "error")
        elif not barang:
            flash("Barang tidak ditemukan", "error")
        elif db.stok_barang(kode) < jumlah:
            flash("Ditolak: jumlah melebihi stok barang", "error")
        else:
            conn.execute(
                "INSERT INTO transaksi (tanggal, jenis, kode_barang, jumlah, no_faktur) "
                "VALUES (?, 'Keluar', ?, ?, ?)",
                (tanggal, kode, jumlah, no_faktur),
            )
            conn.commit()
            flash("Barang keluar berhasil ditambahkan", "ok")
            return redirect(url_for("keluar_list"))

    return render_template("keluar_form.html", daftar_barang=daftar_barang,
                           data=None, hari_ini=date.today().isoformat())


@app.route("/keluar/<int:id>/ubah", methods=["GET", "POST"])
@login_required
def keluar_ubah(id):
    data = ambil_keluar(id)

    if request.method == "POST":
        tanggal = request.form["tanggal"]
        no_faktur = request.form["no_faktur"].strip() or None
        try:
            jumlah = int(request.form["jumlah"])
        except ValueError:
            jumlah = 0

        if not tanggal or jumlah <= 0:
            flash("Tanggal wajib diisi dan jumlah harus lebih dari 0", "error")
        elif db.stok_barang(data["kode_barang"]) + data["jumlah"] < jumlah:
            flash("Ditolak: jumlah melebihi stok barang", "error")
        else:
            conn = db.get_db()
            conn.execute(
                "UPDATE transaksi SET tanggal = ?, jumlah = ?, no_faktur = ? WHERE id = ?",
                (tanggal, jumlah, no_faktur, id),
            )
            conn.commit()
            flash("Barang keluar berhasil diubah", "ok")
            return redirect(url_for("keluar_list"))

    return render_template("keluar_form.html", data=data, daftar_barang=[], hari_ini="")


@app.route("/keluar/<int:id>/hapus", methods=["POST"])
@login_required
def keluar_hapus(id):
    ambil_keluar(id)
    conn = db.get_db()
    conn.execute("DELETE FROM transaksi WHERE id = ?", (id,))
    conn.commit()
    flash("Barang keluar berhasil dihapus", "ok")
    return redirect(url_for("keluar_list"))


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
