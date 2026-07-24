"""
Skrip aktivasi KlienBMKG di endpoint ForecastEngine.
=====================================================
Jalankan dari root repo (~/Downloads/kaltide-intelligence):

    python aktifkan_klien_bmkg.py

Yang dilakukan skrip ini, untuk masing-masing dari 4 file target:
  1. Menambahkan `from app.services.klien_bmkg import KlienBMKG`
     tepat di bawah baris import ForecastEngine (kalau belum ada).
  2. Mengubah `ForecastEngine()` -> `ForecastEngine(klien_bmkg=KlienBMKG())`
     HANYA pada baris instantiate (bukan di tempat lain).

Skrip ini TIDAK menyentuh tide.py (sengaja, karena tide.py tidak
memanggil prakiraan_cuaca() sama sekali -- lihat hasil grep sebelumnya).

Aman dijalankan berkali-kali (idempotent): kalau sudah diubah,
dijalankan lagi tidak akan mengubah apa-apa lagi.
"""

import re
from pathlib import Path

# Path relatif dari root repo ke masing-masing file target
FILE_TARGET = [
    Path("backend/app/api/forecast.py"),
    Path("backend/app/api/flood.py"),
    Path("backend/app/api/impact.py"),
    Path("backend/app/api/warning.py"),
]

IMPORT_KLIEN_BMKG = "from app.services.klien_bmkg import KlienBMKG"

# Pola baris import ForecastEngine, contoh:
#   from app.engines.forecast_engine import ForecastEngine
POLA_IMPORT_ENGINE = re.compile(
    r"^(from\s+[\w.]+\s+import\s+ForecastEngine)\s*$", re.MULTILINE
)

# Pola instantiate, menangkap nama variabel di kiri (engine / forecast_engine / dst)
# Contoh yang harus cocok:
#   engine = ForecastEngine()
#   forecast_engine = ForecastEngine()
POLA_INSTANTIATE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<var>\w+)\s*=\s*ForecastEngine\(\)\s*$", re.MULTILINE
)


def proses_file(path: Path) -> None:
    if not path.exists():
        print(f"[LEWATI] {path} tidak ditemukan -- cek path relatif dari root repo.")
        return

    teks_asli = path.read_text(encoding="utf-8")
    teks = teks_asli

    # 1) Tambah import KlienBMKG kalau belum ada
    if IMPORT_KLIEN_BMKG not in teks:
        cocok = POLA_IMPORT_ENGINE.search(teks)
        if cocok:
            teks = teks[: cocok.end()] + "\n" + IMPORT_KLIEN_BMKG + teks[cocok.end():]
        else:
            print(f"[PERINGATAN] {path}: baris 'import ForecastEngine' tidak ditemukan, "
                  f"import KlienBMKG TIDAK ditambahkan otomatis -- tambahkan manual.")

    # 2) Ubah instantiate ForecastEngine() -> ForecastEngine(klien_bmkg=KlienBMKG())
    def ganti_instantiate(m: re.Match) -> str:
        return f"{m.group('indent')}{m.group('var')} = ForecastEngine(klien_bmkg=KlienBMKG())"

    teks_baru, jumlah = POLA_INSTANTIATE.subn(ganti_instantiate, teks)

    if jumlah == 0:
        print(f"[PERINGATAN] {path}: baris 'X = ForecastEngine()' tidak ditemukan -- "
              f"cek manual, mungkin sudah diubah atau formatnya beda.")
    else:
        teks = teks_baru
        print(f"[OK] {path}: {jumlah} baris instantiate diubah.")

    if teks != teks_asli:
        path.write_text(teks, encoding="utf-8")
    else:
        print(f"[TANPA PERUBAHAN] {path}")


def main() -> None:
    print("Mengaktifkan KlienBMKG di endpoint ForecastEngine...\n")
    for path in FILE_TARGET:
        proses_file(path)
    print("\nSelesai. Jalankan `git diff` untuk review perubahan sebelum commit.")


if __name__ == "__main__":
    main()
