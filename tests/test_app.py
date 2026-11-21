import os
import tempfile
import unittest

from werkzeug.security import generate_password_hash

import db
from app import app


class InventarisTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "test.db")
        app.config.update(TESTING=True, DATABASE=self.database_path)
        with app.app_context():
            conn = db.get_db()
            with open("schema.sql", encoding="utf-8") as schema:
                conn.executescript(schema.read())
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                ("tester", generate_password_hash("secret", method="pbkdf2:sha256")),
            )
            conn.execute("INSERT INTO barang (kode, nama) VALUES ('BRG-1', 'Barang Uji')")
            conn.commit()
        self.client = app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def login(self):
        return self.client.post(
            "/login", data={"username": "tester", "password": "secret"},
            follow_redirects=True,
        )

    def test_login_required_and_valid_login(self):
        response = self.client.get("/barang")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)
        self.assertEqual(self.client.get("/barang").status_code, 200)

    def test_master_barang_create_edit_and_deactivate(self):
        self.login()
        response = self.client.post("/barang/tambah", data={"kode": "BRG-2", "nama": "Barang Kedua"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/barang/BRG-2/ubah", data={"nama": "Nama Baru"})
        self.assertEqual(response.status_code, 302)
        self.client.post("/barang/BRG-2/status")
        with app.app_context():
            barang = db.get_db().execute("SELECT nama, aktif FROM barang WHERE kode = 'BRG-2'").fetchone()
            self.assertEqual(barang["nama"], "Nama Baru")
            self.assertEqual(barang["aktif"], 0)

    def test_transaksi_updates_stock_and_rejects_overdraw(self):
        self.login()
        tanggal = "2026-11-21"
        response = self.client.post("/masuk/tambah", data={
            "tanggal": tanggal, "kode_barang": "BRG-1", "jumlah": "10", "no_faktur": "F-1",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertEqual(db.stok_barang("BRG-1"), 10)

        response = self.client.post("/keluar/tambah", data={
            "tanggal": tanggal, "kode_barang": "BRG-1", "jumlah": "4", "no_faktur": "F-2",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertEqual(db.stok_barang("BRG-1"), 6)

        response = self.client.post("/keluar/tambah", data={
            "tanggal": tanggal, "kode_barang": "BRG-1", "jumlah": "7", "no_faktur": "",
        }, follow_redirects=True)
        self.assertIn("Ditolak: jumlah melebihi stok barang".encode(), response.data)
        with app.app_context():
            self.assertEqual(db.stok_barang("BRG-1"), 6)

    def test_edit_and_delete_incoming_transaction_preserve_nonnegative_stock(self):
        self.login()
        self.client.post("/masuk/tambah", data={
            "tanggal": "2026-11-21", "kode_barang": "BRG-1", "jumlah": "5", "no_faktur": "",
        })
        with app.app_context():
            transaction_id = db.get_db().execute("SELECT id FROM transaksi").fetchone()["id"]

        response = self.client.post(f"/masuk/{transaction_id}/ubah", data={
            "tanggal": "2026-11-21", "jumlah": "2", "no_faktur": "",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertEqual(db.stok_barang("BRG-1"), 2)

        self.client.post("/keluar/tambah", data={
            "tanggal": "2026-11-21", "kode_barang": "BRG-1", "jumlah": "2", "no_faktur": "",
        })
        response = self.client.post(f"/masuk/{transaction_id}/hapus", follow_redirects=True)
        self.assertIn("stok barang akan menjadi minus".encode(), response.data)
        with app.app_context():
            self.assertEqual(db.stok_barang("BRG-1"), 0)
            self.assertIsNotNone(db.get_db().execute("SELECT id FROM transaksi WHERE id = ?", (transaction_id,)).fetchone())


if __name__ == "__main__":
    unittest.main()
