# Changelog

Semua perubahan penting pada proyek ini didokumentasikan dalam berkas ini.
Format ini mengacu pada panduan [Keep a Changelog](https://keepachangelog.com/id/1.0.0/) dan menggunakan [Semantic Versioning](https://semver.org/lang/id/).

---

## [Unreleased]

### Ditambahkan
- **CRUD Transaksi Barang Keluar**:
  - Halaman riwayat dan formulir tambah barang keluar.
  - Validasi stok saat menambah dan mengubah transaksi agar stok tidak minus.
  - Fitur ubah dan hapus transaksi barang keluar.
  - Tautan menu navigasi "Barang Keluar".
- **Ringkasan Dashboard**:
  - Metrik jumlah jenis barang, jumlah transaksi, dan total stok saat ini.
  - Daftar barang dengan stok 5 unit atau kurang, termasuk penanda stok habis.

### Rencana Pengembangan
- **Pengujian Otomatis (Automated Testing)**:
  - Implementasi pengujian unit dan integrasi (misalnya dengan `pytest` / `unittest`) untuk rute aplikasi, validasi alur transaksi, dan perhitungan stok.

### Diubah
- **CRUD Master Barang**:
  - Menambahkan form tambah barang dan ubah nama barang melalui antarmuka web.
  - Menambahkan aktivasi/nonaktivasi barang. Barang nonaktif tidak muncul pada pilihan transaksi baru, tetapi riwayat transaksi tetap tersimpan.
  - Menambahkan migrasi kolom status yang tetap kompatibel dengan database lama saat menjalankan `flask init-db`.

---

## [0.3.0] - 2026-11-03

### Ditambahkan
- **CRUD Transaksi Barang Masuk** (PR #3 - `feat/barang-masuk`):
  - Halaman riwayat barang masuk (`/masuk`) yang menampilkan nomor urut, tanggal, kode barang, nama barang, jumlah, nomor faktur, dan tombol aksi ubah/hapus.
  - Halaman form tambah barang masuk (`/masuk/tambah`) dengan tanggal default hari ini, dropdown pilihan kode & nama barang, input jumlah valid (> 0), serta nomor faktur (opsional).
  - Fitur ubah data transaksi barang masuk (`/masuk/<id>/ubah`) dilengkapi validasi agar pengubahan jumlah tidak menyebabkan sisa stok barang menjadi negatif.
  - Fitur hapus data transaksi barang masuk (`/masuk/<id>/hapus`) dengan validasi penjagaan sisa stok agar tidak minus.
  - Fungsi utilitas `stok_barang(kode)` pada `db.py` untuk menghitung sisa stok terkini berdasarkan total transaksi masuk dikurangi total keluar.
  - Tautan menu navigasi "Barang Masuk" pada template utama (`templates/base.html`).

---

## [0.2.0] - 2026-10-21

### Ditambahkan
- **Master Barang & Impor Transaksi Excel** (PR #2 - `feat/master-barang`):
  - Skema tabel `barang` (kode, nama) dan `transaksi` (id, tanggal, jenis, kode_barang, jumlah, no_faktur).
  - CLI command `flask import-excel <path>` untuk membaca dan mengimpor riwayat data barang & transaksi langsung dari file Excel (`data/transaksi.xlsx`).
  - Halaman Master Barang (`/barang`) dengan kalkulasi stok otomatis per barang berbasis agregasi data transaksi (`SUM(Masuk) - SUM(Keluar)`).
  - Kolom nomor urut pada tabel tampilan master barang.
  - Menu navigasi "Barang" pada navbar di `templates/base.html`.
  - Pustaka `openpyxl` dan `et_xmlfile` ke dalam `requirements.txt`.
  - Konfigurasi pengabaian berkas `.DS_Store` pada `.gitignore`.

---

## [0.1.0] - 2026-10-21

### Ditambahkan
- **Setup Dasar Flask & Sistem Autentikasi** (PR #1 - `feat/setup-login`):
  - Inisialisasi struktur aplikasi Flask (`app.py`) dan koneksi SQLite dengan penegakan relasi foreign key (`db.py`).
  - Skema tabel `users` (id, username, password_hash).
  - CLI command `flask init-db` untuk inisialisasi tabel basis data dan pembuatan user default (`admin` / `admin123`).
  - Fitur autentikasi pengguna: Halaman login (`/login`), proses logout (`/logout`), dan decorator pengaman rute `@login_required`.
  - Template dasar `base.html` berdesain gelap (*dark theme*) dengan tipografi Google Fonts *Montserrat Alternates*.
  - Template halaman Dashboard (`index.html`) dan Login (`login.html`).

---

## [0.0.1] - 2026-10-21

### Ditambahkan
- **Inisialisasi Repositori Proyek** (Commit `4aec0f1`):
  - Setup dasar `.gitignore` untuk environment Python dan sistem.
  - Setup dependensi dasar awal `requirements.txt` (`Flask`).
