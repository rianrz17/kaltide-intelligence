# Cara Membuat Repo GitHub & Push Kode Ini

Ikuti langkah ini di komputer Anda setelah mengekstrak file zip.

## 1. Buat repo baru di GitHub

Buka https://github.com/new lalu buat repo baru, misalnya:
`kaltide-intelligence` (bisa Private dulu selama masih tahap MVP).
**Jangan** centang "Initialize with README" agar tidak konflik.

## 2. Inisialisasi git secara lokal

```bash
cd kaltide-intelligence
git init
git add .
git commit -m "Initial commit: struktur repo KALTIDE Intelligence (Tahap 1)"
git branch -M main
```

## 3. Hubungkan ke repo GitHub

```bash
git remote add origin https://github.com/<username-atau-organisasi>/kaltide-intelligence.git
git push -u origin main
```

Ganti `<username-atau-organisasi>` dengan akun/organisasi GitHub tim Anda.

## 4. (Opsional) Buat branch develop untuk kerja harian

```bash
git checkout -b develop
git push -u origin develop
```

Disarankan tim bekerja di `develop`, lalu merge ke `main` saat rilis stabil.

## 5. Verifikasi

- README.md tampil otomatis di halaman utama repo.
- Workflow CI di `.github/workflows/backend-ci.yml` akan otomatis berjalan
  setiap ada push/PR ke `main` atau `develop` yang menyentuh folder `backend/`.

---

Jika tim menggunakan GitHub CLI (`gh`), langkah 1-3 bisa dipersingkat:

```bash
gh repo create kaltide-intelligence --private --source=. --remote=origin --push
```
