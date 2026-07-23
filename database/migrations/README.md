# Migrasi Database

Folder ini akan berisi file migrasi inkremental (mis. menggunakan Alembic)
setelah `schema.sql` awal stabil dan sudah dipakai di lingkungan development.

Rencana penamaan file migrasi:

```
0001_initial_schema.sql
0002_tambah_kolom_x.sql
...
```

Untuk saat ini (Tahap 1), gunakan langsung `database/schema.sql` untuk
inisialisasi database baru.
