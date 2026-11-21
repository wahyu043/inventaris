# Inventaris

Aplikasi web sederhana untuk mencatat persediaan barang. Aplikasi menyediakan master barang, transaksi barang masuk dan keluar, serta ringkasan stok pada dashboard.

## Tentang proyek

Proyek ini berawal dari proses pengembangan yang eksploratif dan dibantu AI, pendekatan yang sering disebut *vibe coding*. Implementasi kemudian dirapikan secara bertahap dengan struktur Flask, validasi transaksi, migrasi skema, dan pengujian otomatis. README ini mendokumentasikan cara kerja dan kondisi proyek sebagaimana adanya.

## Fitur

- Login untuk membatasi akses ke halaman inventaris.
- Dashboard dengan jumlah jenis barang, jumlah transaksi, total stok, dan daftar stok rendah (5 unit atau kurang).
- Master barang: tambah barang, ubah nama, dan aktifkan atau nonaktifkan barang.
- Transaksi barang masuk dan keluar: tambah, ubah, hapus, serta lihat riwayat.
- Validasi agar transaksi keluar dan perubahan transaksi tidak membuat stok menjadi negatif.
- Barang nonaktif tidak dapat dipakai untuk transaksi baru.
- Impor data transaksi dan master barang dari berkas Excel.
- Pengujian otomatis untuk autentikasi, master barang, dashboard, transaksi, dan validasi stok.

## Teknologi

- Python dan Flask
- SQLite
- Jinja2 untuk template HTML
- openpyxl untuk impor Excel
- `unittest` untuk pengujian

## Menjalankan secara lokal

Pastikan Python 3 sudah terpasang. Dari direktori proyek, buat dan aktifkan virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Di Windows PowerShell, aktifkan environment dengan `.venv\Scripts\Activate.ps1`.

Siapkan database dan akun awal, kemudian jalankan server:

```bash
flask init-db
flask run
```

Buka alamat yang ditampilkan Flask, biasanya <http://127.0.0.1:5000>.

Kredensial awal:

- Username: `admin`
- Password: `admin123`

Akun awal tersebut ditujukan untuk penggunaan lokal. Ganti kredensial dan `SECRET_KEY` sebelum aplikasi dipakai di lingkungan publik atau produksi. Nilai `SECRET_KEY` saat ini masih berupa nilai bawaan di `app.py`.

`flask init-db` membuat tabel yang belum tersedia dan akun admin awal. Perintah ini juga menambahkan kolom status barang pada database lama. Database SQLite disimpan sebagai `database.db` di direktori kerja.

## Impor data Excel

Setelah inisialisasi database, impor berkas Excel dengan perintah:

```bash
flask import-excel data/transaksi.xlsx
```

Perintah impor membaca lembar aktif, menganggap tiga baris pertama sebagai judul dan header, lalu memproses data mulai baris keempat. Impor dibatalkan jika tabel transaksi sudah berisi data.

## Menjalankan pengujian

Dengan virtual environment aktif:

```bash
python -m unittest discover -s tests -v
```

Pengujian menggunakan database sementara dan tidak mengubah `database.db` lokal.

## Struktur data

- `users`: akun pengguna dan hash kata sandi.
- `barang`: kode, nama, dan status aktif barang.
- `transaksi`: tanggal, jenis (Masuk/Keluar), kode barang, jumlah, dan nomor faktur opsional.

Stok dihitung dari jumlah transaksi masuk dikurangi transaksi keluar; nilai stok tidak disimpan sebagai angka terpisah.
