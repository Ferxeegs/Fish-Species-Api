# Tutorial Fish Species API

API REST berbasis Flask untuk mendeteksi dan mengklasifikasi spesies ikan dari gambar menggunakan model **YOLO** (Ultralytics). API ini mengembalikan bounding box, tingkat kepercayaan (confidence), dan nama spesies ikan yang terdeteksi.

> **Untuk developer yang mengintegrasikan API:** lihat [API_GUIDE.md](./API_GUIDE.md) (structured output, validasi JSON, retry, fallback, debugging).
>
> **Dokumentasi interaktif (Swagger UI):** `/docs` — mirip FastAPI. ReDoc: `/redoc`. OpenAPI: `/openapi.json`.

---

## Daftar Isi

1. [Gambaran Umum](#gambaran-umum)
2. [Arsitektur Proyek](#arsitektur-proyek)
3. [Spesies yang Didukung](#spesies-yang-didukung)
4. [Persyaratan Sistem](#persyaratan-sistem)
5. [Instalasi Lokal](#instalasi-lokal)
6. [Menjalankan Server](#menjalankan-server)
7. [Menggunakan API](#menggunakan-api)
8. [Menjalankan dengan Docker](#menjalankan-dengan-docker)
9. [Penjelasan Kode](#penjelasan-kode)
10. [Kustomisasi](#kustomisasi)
11. [Troubleshooting](#troubleshooting)

---

## Gambaran Umum

Proyek ini menyediakan endpoint berikut:

| Method | Endpoint   | Deskripsi                              |
|--------|------------|----------------------------------------|
| `GET`  | `/health`  | Liveness check (aplikasi berjalan)     |
| `GET`  | `/ready`   | Readiness check (model sudah dimuat)   |
| `POST` | `/predict` | Mengunggah gambar ikan untuk deteksi   |

Alur kerja singkat:

```
Client mengirim gambar (multipart/form-data)
        ↓
Flask menerima file di endpoint /predict
        ↓
Gambar dikonversi ke NumPy array
        ↓
Model YOLO (speciesv4.pt) melakukan inferensi
        ↓
Hasil deteksi difilter berdasarkan confidence threshold
        ↓
Response JSON berisi daftar deteksi
```

---

## Arsitektur Proyek

```
Fish-Species-Api/
├── app.py                 # Application factory Flask
├── wsgi.py                # Entry point Gunicorn (production)
├── gunicorn.conf.py       # Konfigurasi Gunicorn
├── check_model.py         # Skrip verifikasi model
├── requirements.txt       # Dependensi Python
├── Dockerfile             # Konfigurasi container Docker
├── docker-compose.yml     # Orkestrasi container
├── .env.example           # Template environment variables
├── .env                   # Environment lokal (jangan commit)
├── config/
│   └── settings.py        # Konfigurasi terpusat dari .env
├── model/
│   ├── speciesv4.pt       # File bobot model YOLO (wajib ada)
│   └── model_loader.py    # Lazy-load model YOLO
├── routes/
│   └── predict.py         # Logika prediksi
└── utils/
    ├── auth.py            # Autentikasi API key
    ├── validators.py      # Validasi upload gambar
    └── preprocess.py      # Transformasi gambar (legacy)
```

---

## Spesies yang Didukung

Model saat ini dikonfigurasi untuk mendeteksi 5 jenis ikan:

| ID Kelas | Nama Spesies   |
|----------|----------------|
| 0        | Ikan Bawal     |
| 1        | Ikan Gurame    |
| 2        | Ikan Lele      |
| 3        | Ikan Nila      |
| 4        | Ikan Tuna      |

Daftar ini didefinisikan di `routes/predict.py`. Pastikan urutan dan nama kelas sesuai dengan model yang Anda latih.

---

## Persyaratan Sistem

- **Python** 3.10 atau lebih baru
- **pip** (package manager Python)
- File model `model/speciesv4.pt` (harus tersedia sebelum menjalankan API)
- (Opsional) **Docker** untuk deployment berbasis container

### Dependensi Utama

| Paket            | Fungsi                              |
|------------------|-------------------------------------|
| Flask            | Web framework / REST API            |
| PyTorch (CPU)    | Backend deep learning               |
| Ultralytics      | Wrapper YOLO untuk inferensi        |
| Pillow           | Membaca dan memproses gambar        |
| OpenCV           | Dukungan pemrosesan gambar          |
| NumPy            | Representasi array gambar           |

---

## Instalasi Lokal

### 1. Clone repositori

```bash
git clone https://github.com/Ferxeegs/Fish-Species-Api.git
cd Fish-Species-Api
```

### 2. Konfigurasi environment

```bash
cp .env.example .env
```

Edit `.env` dan set minimal `SECRET_KEY` serta `API_KEY` (wajib jika `FLASK_ENV=production`):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Buat virtual environment (disarankan)

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install PyTorch CPU

PyTorch perlu diinstal terlebih dahulu dengan index URL khusus:

```bash
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

### 5. Install dependensi lainnya

```bash
pip install -r requirements.txt
```

### 6. Pastikan file model tersedia

Letakkan file model di:

```
model/speciesv4.pt
```

Verifikasi model dapat dimuat:

```bash
python check_model.py
```

Output yang diharapkan:

```
Model berhasil dimuat: <ultralytics.yolo.engine.model.YOLO object ...>
```

---

## Menjalankan Server

### Production (Gunicorn)

```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

### Development (Flask built-in)

Set `FLASK_ENV=development` dan `FLASK_DEBUG=true` di `.env`, lalu:

```bash
python app.py
```

Server berjalan di `http://localhost:5000`.

---

## Menggunakan API

### Request

| Properti       | Nilai                              |
|----------------|------------------------------------|
| URL            | `http://localhost:5000/predict`    |
| Method         | `POST`                             |
| Header         | `X-API-Key: <API_KEY dari .env>`   |
| Content-Type   | `multipart/form-data`              |
| Field form     | `image` (file gambar)              |

Format gambar yang didukung: JPEG, PNG, WebP (maks. 10 MB default).

### Contoh dengan cURL

```bash
curl -X POST http://localhost:5000/predict \
  -H "X-API-Key: your-api-key-here" \
  -F "image=@/path/ke/gambar_ikan.jpg"
```

### Contoh dengan Python (requests)

```python
import requests

url = "http://localhost:5000/predict"
headers = {"X-API-Key": "your-api-key-here"}
files = {"image": open("gambar_ikan.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

### Contoh dengan JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append("image", fileInput.files[0]);

fetch("http://localhost:5000/predict", {
  method: "POST",
  headers: { "X-API-Key": "your-api-key-here" },
  body: formData,
})
  .then((res) => res.json())
  .then((data) => console.log(data));
```

### Response Sukses (HTTP 200)

```json
{
  "success": true,
  "predictions": [
    {
      "center_x": 320.5,
      "center_y": 240.2,
      "width": 150.0,
      "height": 80.5,
      "confidence": 0.87,
      "class_name": "Ikan Gurame"
    }
  ]
}
```

| Field        | Tipe    | Deskripsi                                              |
|--------------|---------|--------------------------------------------------------|
| `center_x`   | float   | Koordinat X pusat bounding box (piksel)                |
| `center_y`   | float   | Koordinat Y pusat bounding box (piksel)                |
| `width`      | float   | Lebar bounding box (piksel)                            |
| `height`     | float   | Tinggi bounding box (piksel)                           |
| `confidence` | float   | Skor kepercayaan model (0–1)                           |
| `class_name` | string  | Nama spesies ikan                                      |

Jika tidak ada ikan terdeteksi di atas threshold, `predictions` berupa array kosong `[]`.

### Response Error

**Tidak terautentikasi (HTTP 401):**

```json
{
  "success": false,
  "message": "Unauthorized"
}
```

**Tidak ada gambar (HTTP 400):**

```json
{
  "success": false,
  "message": "No image provided"
}
```

**File kosong (HTTP 400):**

```json
{
  "success": false,
  "message": "No selected file"
}
```

**Kesalahan pemrosesan (HTTP 500):**

```json
{
  "success": false,
  "message": "Error processing image"
}
```

**Rate limit (HTTP 429):**

```json
{
  "success": false,
  "message": "Rate limit exceeded. Try again later."
}
```

---

## Menjalankan dengan Docker

Proyek ini memakai **satu `docker-compose.yml`** dengan **profile** `dev` dan `prod`:

| Profile | Service | Environment | Port host | Jaringan |
|---------|---------|-------------|-----------|----------|
| `dev` | `api-dev` | `.env.development` | `127.0.0.1:5000` | default |
| `prod` | `api-prod` | `.env.production` | tidak di-expose | `app-bridge` |

File env:

| File | Dipakai oleh |
|------|--------------|
| `.env.development` | Profile `dev` |
| `.env.production` | Profile `prod` (buat dari `.env.production.example`) |

Tambahkan di `.env` (root) agar default local pakai dev:

```env
COMPOSE_PROFILES=dev
```

### Development (local)

```bash
docker compose --profile dev up -d --build

# atau jika COMPOSE_PROFILES=dev sudah di .env:
docker compose up -d --build
```

Akses:

- API: `http://localhost:5000`
- Swagger UI: `http://localhost:5000/docs`
- API key dev: `dev-api-key` (dari `.env.development`)

```bash
curl http://localhost:5000/ready
curl -X POST http://localhost:5000/predict \
  -H "X-API-Key: dev-api-key" \
  -F "image=@ikan.jpg"
```

### Production (server)

```bash
cp .env.production.example .env.production
# Edit SECRET_KEY & API_KEY di .env.production

docker network create app-bridge 2>/dev/null || true
docker compose --profile prod up -d --build
```

### Perintah umum

```bash
docker compose ps
docker compose logs -f
docker compose down
```

> **Kenapa local tidak jalan sebelumnya?** Config production tidak expose port ke host dan membutuhkan jaringan Docker eksternal `app-bridge` untuk Nginx global. Untuk local, selalu pakai config **dev**.

### Nginx Global Gateway (conf.d)

Pola sama dengan stack lain di server (mis. purchasing-go): gateway Nginx join jaringan Docker `app-bridge` dan proxy ke `container_name`.

File: `nginx/fish-species-api.conf`

```bash
# 1. Pastikan jaringan app-bridge sudah ada
docker network create app-bridge 2>/dev/null || true

# 2. Pastikan container Nginx global sudah join app-bridge
docker network connect app-bridge <nama-container-nginx-global>

# 3. Jalankan stack API (production)
docker compose --profile prod up -d --build

# 4. Salin config ke gateway
sudo cp nginx/fish-species-api.conf /etc/nginx/conf.d/fish-species-api.conf

# 5. Edit server_name (default: fish-species.ferxcode.my.id)
sudo nano /etc/nginx/conf.d/fish-species-api.conf

# 6. Reload Nginx global
sudo nginx -t && sudo systemctl reload nginx
```

| Item | Nilai |
|------|-------|
| Jaringan Docker | `app-bridge` (external) |
| Container name | `fish_species_api` |
| Upstream | `fish_species_api:5000` |
| Upload max | `10M` (sesuai `MAX_UPLOAD_SIZE_MB`) |
| Proxy timeout | `120s` (sesuai `GUNICORN_TIMEOUT`) |

Tes dari luar:

```bash
curl http://fish-species.ferxcode.my.id/ready
curl -X POST http://fish-species.ferxcode.my.id/predict \
  -H "X-API-Key: your-api-key" \
  -F "image=@ikan.jpg"
```

### Build image manual

```bash
docker build -t fish-species-api .
```

### Jalankan container manual

```bash
docker run -p 5000:5000 fish-species-api
```

API dapat diakses di `http://localhost:5000/predict`.

### Catatan Docker

- Image menggunakan `python:3.10-slim` sebagai base.
- Dependensi sistem untuk OpenCV (`libgl1`, `libglib2.0-0`) diinstal otomatis di Dockerfile.
- PyTorch CPU diinstal saat proses build image.
- Pastikan file `model/speciesv4.pt` ikut tersalin ke dalam image (sudah ditangani oleh `COPY . .` di Dockerfile).
- Container menjalankan **Gunicorn** (bukan Flask dev server).
- User non-root, filesystem read-only, dan `no-new-privileges` diaktifkan.
- Health check menggunakan endpoint `/ready`.
- Semua konfigurasi diambil dari file `.env`.

---

## Penjelasan Kode

### `app.py` — Entry Point

- Membuat instance Flask.
- Mendefinisikan route `GET /health` untuk health check (Docker Compose).
- Mendefinisikan route `POST /predict`.
- Memvalidasi keberadaan file gambar dalam request.
- Memanggil `predict_image()` dari `routes/predict.py`.
- Menangani error dan mengembalikan response JSON.

### `model/model_loader.py` — Pemuatan Model

- Memuat model YOLO dari `model/speciesv4.pt` saat modul diimpor.
- Model disimpan dalam mode evaluasi (`model.eval()`).
- Model dimuat **sekali** saat startup, sehingga inferensi berikutnya lebih cepat.

### `routes/predict.py` — Logika Prediksi

1. Membuka gambar dari file upload menggunakan Pillow.
2. Mengonversi ke NumPy array.
3. Menjalankan inferensi YOLO.
4. Mengekstrak bounding box (`xywh`), confidence, dan class ID.
5. Memfilter hasil dengan `score_threshold` default **0.4** (40%).
6. Memetakan class ID ke nama spesies ikan.
7. Mengembalikan list deteksi sebagai JSON-serializable dict.

### `utils/preprocess.py` — Preprocessing (Opsional)

File ini berisi transformasi `torchvision` (resize 224×224, normalisasi ImageNet). **Saat ini tidak digunakan** dalam alur prediksi aktif karena YOLO menangani preprocessing secara internal. File ini dapat dipakai jika Anda beralih ke model klasifikasi non-YOLO di masa depan.

### `check_model.py` — Verifikasi Model

Skrip sederhana untuk memastikan file model valid dan dapat dimuat oleh Ultralytics sebelum menjalankan server.

---

## Kustomisasi

### Mengubah Confidence Threshold

Di `routes/predict.py`, parameter `score_threshold` pada fungsi `predict_image` menentukan batas minimum confidence:

```python
def predict_image(image, score_threshold=0.4):
```

Nilai lebih tinggi → deteksi lebih ketat (lebih sedikit false positive).  
Nilai lebih rendah → deteksi lebih sensitif (lebih banyak hasil, risiko false positive).

### Menambah / Mengubah Kelas Ikan

Edit daftar `class_names` di `routes/predict.py`:

```python
class_names = ["Ikan Bawal", "Ikan Gurame", "Ikan Lele", "Ikan Nila", "Ikan Tuna"]
```

Pastikan urutan sesuai dengan label yang digunakan saat pelatihan model.

### Mengganti Model

1. Letakkan file bobot baru di folder `model/`.
2. Perbarui path di `model/model_loader.py` dan `check_model.py`:

```python
model_path = 'model/nama_model_baru.pt'
```

3. Sesuaikan `class_names` jika kelas berbeda.

### Mengubah Port

Edit baris terakhir di `app.py`:

```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

Jangan lupa memperbarui `EXPOSE` di `Dockerfile` jika menggunakan Docker.

---

## Troubleshooting

### Model tidak ditemukan

```
FileNotFoundError: model/speciesv4.pt
```

**Solusi:** Pastikan file `speciesv4.pt` ada di folder `model/`. File ini mungkin tidak disertakan di repositori Git karena ukurannya besar.

### Error saat install PyTorch

**Solusi:** Instal PyTorch CPU secara terpisah sebelum `requirements.txt`:

```bash
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### OpenCV error di Linux/Docker

```
ImportError: libGL.so.1: cannot open shared object file
```

**Solusi:** Di Docker sudah ditangani oleh Dockerfile. Untuk instalasi lokal di Linux:

```bash
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### Response array kosong `[]`

Kemungkinan penyebab:

- Tidak ada ikan terdeteksi dalam gambar.
- Confidence semua deteksi di bawah threshold (default 0.4).
- Gambar terlalu buram, gelap, atau objek terlalu kecil.

**Solusi:** Coba gambar lain, atau turunkan `score_threshold` sementara untuk debugging.

### NumPy version conflict

`requirements.txt` membatasi `numpy<2.0` untuk kompatibilitas dengan PyTorch 2.1. Jangan upgrade NumPy ke versi 2.x tanpa mengupgrade PyTorch.

---

## Ringkasan Cepat

```bash
# Local (development)
docker compose --profile dev up -d --build
curl http://localhost:5000/ready
curl -X POST http://localhost:5000/predict \
  -H "X-API-Key: dev-api-key" \
  -F "image=@ikan.jpg"

# Production (server)
cp .env.production.example .env.production
docker compose --profile prod up -d --build
```

---

## Referensi

- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyTorch CPU Installation](https://pytorch.org/get-started/locally/)
