"""
Script bantu: update DATABASE_URL di file .env dengan password yang benar,
tanpa menampilkan password di layar dan otomatis di-encode agar aman
dipakai dalam URL (menangani karakter spesial seperti @, :, /, dll).

Cara pakai:
    python update_env_password.py
"""

import getpass
from urllib.parse import quote

password = getpass.getpass("Masukkan password postgres (tidak akan terlihat di layar): ")
password_encoded = quote(password, safe="")

with open(".env", encoding="utf-8") as f:
    baris = f.readlines()

with open(".env", "w", encoding="utf-8") as f:
    for b in baris:
        if b.startswith("DATABASE_URL="):
            f.write(f"DATABASE_URL=postgresql://postgres:{password_encoded}@localhost:5432/kaltide\n")
        else:
            f.write(b)

print("Selesai! File .env sudah diupdate.")
