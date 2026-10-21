CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS barang (
    kode TEXT PRIMARY KEY,
    nama TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT NOT NULL,
    jenis TEXT NOT NULL CHECK (jenis IN ('Masuk', 'Keluar')),
    kode_barang TEXT NOT NULL REFERENCES barang(kode),
    jumlah INTEGER NOT NULL CHECK (jumlah > 0),
    no_faktur TEXT
);