# Fish Species API — Panduan Pengguna

Dokumen ini untuk developer yang mengintegrasikan **Fish Species API** ke aplikasi mobile, web, atau backend lainnya.

---

## Daftar Isi

1. [Informasi Dasar](#informasi-dasar)
2. [Structured Output](#structured-output)
3. [JSON Validation](#json-validation)
4. [Normalisasi Hasil](#normalisasi-hasil)
5. [Retry](#retry)
6. [Fallback Response](#fallback-response)
7. [Penyimpanan Respons Mentah untuk Debugging](#penyimpanan-respons-mentah-untuk-debugging)
8. [Contoh Implementasi Lengkap](#contoh-implementasi-lengkap)

---

## Informasi Dasar

| Item | Nilai |
|------|-------|
| Base URL (production) | `https://fish-species.ferxcode.my.id` |
| Dokumentasi interaktif | `https://fish-species.ferxcode.my.id/docs` (Swagger UI) |
| Dokumentasi ReDoc | `https://fish-species.ferxcode.my.id/redoc` |
| OpenAPI spec | `https://fish-species.ferxcode.my.id/openapi.json` |
| Autentikasi | Header `X-API-Key: <API_KEY>` |
| Endpoint utama | `POST /predict` |
| Format upload | `multipart/form-data`, field: `image` |
| Format gambar | JPEG, PNG, WebP |
| Ukuran maks. file | 10 MB |
| Rate limit | 30 request / menit / IP |

### Endpoint pendukung

| Method | Path | Auth | Deskripsi |
|--------|------|------|-----------|
| `GET` | `/health` | Tidak | Cek apakah service hidup |
| `GET` | `/ready` | Tidak | Cek apakah model sudah siap |
| `POST` | `/predict` | **Ya** | Deteksi spesies ikan dari gambar |
| `GET` | `/docs` | Tidak | **Swagger UI** — dokumentasi interaktif |
| `GET` | `/redoc` | Tidak | **ReDoc** — dokumentasi alternatif |
| `GET` | `/openapi.json` | Tidak | Spesifikasi OpenAPI 3.0 |

### Contoh request

```bash
curl -X POST "https://fish-species.ferxcode.my.id/predict" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@/path/to/fish.jpg"
```

### Spesies yang didukung

| ID (internal model) | Nama |
|---------------------|------|
| 0 | Ikan Bawal |
| 1 | Ikan Gurame |
| 2 | Ikan Lele |
| 3 | Ikan Nila |
| 4 | Ikan Tuna |

---

## Structured Output

Semua respons API menggunakan **JSON**. Ada dua bentuk utama: **sukses prediksi** dan **error**.

### Respons sukses (`POST /predict`, HTTP 200)

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

| Field | Tipe | Wajib | Deskripsi |
|-------|------|-------|-----------|
| `success` | boolean | Ya | Selalu `true` jika HTTP 200 |
| `predictions` | array | Ya | Daftar deteksi; bisa kosong `[]` |
| `predictions[].center_x` | number | Ya | Pusat bounding box (sumbu X, piksel) |
| `predictions[].center_y` | number | Ya | Pusat bounding box (sumbu Y, piksel) |
| `predictions[].width` | number | Ya | Lebar bounding box (piksel) |
| `predictions[].height` | number | Ya | Tinggi bounding box (piksel) |
| `predictions[].confidence` | number | Ya | Skor kepercayaan (0.0 – 1.0) |
| `predictions[].class_name` | string | Ya | Nama spesies ikan |

> **Catatan:** `predictions: []` berarti tidak ada ikan terdeteksi di atas threshold (bukan error).

### Respons error (HTTP 4xx / 5xx)

```json
{
  "success": false,
  "message": "Unauthorized"
}
```

| HTTP | `message` (contoh) | Penyebab |
|------|-------------------|----------|
| 400 | `No image provided` | Field `image` tidak dikirim |
| 400 | `File type not allowed` | Ekstensi tidak didukung |
| 400 | `Invalid or corrupted image file` | File bukan gambar valid |
| 401 | `Unauthorized` | `X-API-Key` salah atau tidak ada |
| 413 | `File exceeds maximum size of 10 MB` | File terlalu besar |
| 429 | `Rate limit exceeded. Try again later.` | Terlalu banyak request |
| 500 | `Error processing image` | Kesalahan server saat inferensi |
| 500 | `Internal server error` | Kesalahan server umum |
| 503 | — (endpoint `/ready`) | Model belum siap |

### Health & Ready

```json
// GET /health → 200
{ "status": "ok" }

// GET /ready → 200
{ "status": "ready", "model_loaded": true }

// GET /ready → 503
{ "status": "not_ready", "model_loaded": false }
```

### JSON Schema (referensi validasi)

Simpan sebagai `schemas/predict-success.schema.json` di project client Anda:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["success", "predictions"],
  "additionalProperties": false,
  "properties": {
    "success": { "const": true },
    "predictions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "center_x", "center_y", "width", "height",
          "confidence", "class_name"
        ],
        "additionalProperties": false,
        "properties": {
          "center_x": { "type": "number" },
          "center_y": { "type": "number" },
          "width": { "type": "number", "minimum": 0 },
          "height": { "type": "number", "minimum": 0 },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
          "class_name": { "type": "string", "minLength": 1 }
        }
      }
    }
  }
}
```

Schema error:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["success", "message"],
  "additionalProperties": false,
  "properties": {
    "success": { "const": false },
    "message": { "type": "string", "minLength": 1 }
  }
}
```

---

## JSON Validation

Selalu validasi respons sebelum dipakai di UI atau database. Jangan asumsikan struktur JSON selalu benar (proxy, timeout parsial, dll.).

### TypeScript — tipe & type guard

```typescript
export interface Prediction {
  center_x: number;
  center_y: number;
  width: number;
  height: number;
  confidence: number;
  class_name: string;
}

export interface PredictSuccess {
  success: true;
  predictions: Prediction[];
}

export interface PredictError {
  success: false;
  message: string;
}

export type PredictResponse = PredictSuccess | PredictError;

function isPrediction(value: unknown): value is Prediction {
  if (typeof value !== "object" || value === null) return false;
  const p = value as Record<string, unknown>;
  return (
    typeof p.center_x === "number" &&
    typeof p.center_y === "number" &&
    typeof p.width === "number" &&
    typeof p.height === "number" &&
    typeof p.confidence === "number" &&
    p.confidence >= 0 &&
    p.confidence <= 1 &&
    typeof p.class_name === "string" &&
    p.class_name.length > 0
  );
}

export function parsePredictResponse(
  status: number,
  body: unknown
): PredictResponse {
  if (typeof body !== "object" || body === null) {
    return { success: false, message: "Invalid JSON body" };
  }

  const data = body as Record<string, unknown>;

  if (data.success === true) {
    if (!Array.isArray(data.predictions)) {
      return { success: false, message: "Missing predictions array" };
    }
    if (!data.predictions.every(isPrediction)) {
      return { success: false, message: "Invalid prediction item" };
    }
    return { success: true, predictions: data.predictions };
  }

  if (data.success === false && typeof data.message === "string") {
    return { success: false, message: data.message };
  }

  return {
    success: false,
    message: `Unexpected response (HTTP ${status})`,
  };
}
```

### Python — validasi dengan Pydantic

```python
from typing import Literal, Union
from pydantic import BaseModel, Field, ValidationError


class Prediction(BaseModel):
    center_x: float
    center_y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    class_name: str = Field(min_length=1)


class PredictSuccess(BaseModel):
    success: Literal[True]
    predictions: list[Prediction]


class PredictError(BaseModel):
    success: Literal[False]
    message: str


def parse_predict_response(status_code: int, payload: dict) -> Union[PredictSuccess, PredictError]:
    try:
        if payload.get("success") is True:
            return PredictSuccess.model_validate(payload)
        return PredictError.model_validate(payload)
    except ValidationError as exc:
        return PredictError(success=False, message=f"Invalid response schema: {exc}")
```

---

## Normalisasi Hasil

Respons API mentah berisi **banyak deteksi** (multi-fish) dengan format bounding box `xywh`. Di aplikasi client, biasanya Anda ingin satu objek konsisten.

### Bentuk normalisasi yang disarankan

```typescript
export interface NormalizedFishResult {
  species: string;           // class_name utama
  confidence: number;        // confidence tertinggi (0–1)
  confidence_percent: number; // confidence * 100, dibulatkan
  detected: boolean;         // ada deteksi atau tidak
  total_detections: number;  // jumlah semua box
  all_species: string[];     // daftar unik spesies terdeteksi
  bbox: {                    // box dengan confidence tertinggi
    x: number;
    y: number;
    width: number;
    height: number;
  } | null;
  raw_predictions: Prediction[]; // simpan asli untuk audit
}
```

### Logika normalisasi

1. Urutkan `predictions` berdasarkan `confidence` descending.
2. Ambil item pertama sebagai **hasil utama** (jika ada).
3. Konversi `center_x/center_y/width/height` → sudut kiri-atas jika UI Anda butuh `x, y`:

```
x = center_x - (width / 2)
y = center_y - (height / 2)
```

4. Jika `predictions` kosong → `detected: false`, `species: "Tidak terdeteksi"`.

### Contoh (TypeScript)

```typescript
export function normalizePredictions(
  predictions: Prediction[]
): NormalizedFishResult {
  if (predictions.length === 0) {
    return {
      species: "Tidak terdeteksi",
      confidence: 0,
      confidence_percent: 0,
      detected: false,
      total_detections: 0,
      all_species: [],
      bbox: null,
      raw_predictions: [],
    };
  }

  const sorted = [...predictions].sort((a, b) => b.confidence - a.confidence);
  const best = sorted[0];
  const uniqueSpecies = [...new Set(predictions.map((p) => p.class_name))];

  return {
    species: best.class_name,
    confidence: best.confidence,
    confidence_percent: Math.round(best.confidence * 1000) / 10,
    detected: true,
    total_detections: predictions.length,
    all_species: uniqueSpecies,
    bbox: {
      x: best.center_x - best.width / 2,
      y: best.center_y - best.height / 2,
      width: best.width,
      height: best.height,
    },
    raw_predictions: predictions,
  };
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class NormalizedFishResult:
    species: str
    confidence: float
    confidence_percent: float
    detected: bool
    total_detections: int
    all_species: list[str]
    bbox: dict | None
    raw_predictions: list[dict]


def normalize_predictions(predictions: list[dict]) -> NormalizedFishResult:
    if not predictions:
        return NormalizedFishResult(
            species="Tidak terdeteksi",
            confidence=0.0,
            confidence_percent=0.0,
            detected=False,
            total_detections=0,
            all_species=[],
            bbox=None,
            raw_predictions=[],
        )

    sorted_preds = sorted(predictions, key=lambda p: p["confidence"], reverse=True)
    best = sorted_preds[0]
    unique = list(dict.fromkeys(p["class_name"] for p in predictions))

    return NormalizedFishResult(
        species=best["class_name"],
        confidence=best["confidence"],
        confidence_percent=round(best["confidence"] * 100, 1),
        detected=True,
        total_detections=len(predictions),
        all_species=unique,
        bbox={
            "x": best["center_x"] - best["width"] / 2,
            "y": best["center_y"] - best["height"] / 2,
            "width": best["width"],
            "height": best["height"],
        },
        raw_predictions=predictions,
    )
```

---

## Retry

Gunakan retry **hanya** untuk error yang bersifat sementara. Jangan retry error validasi client.

### Kapan retry

| HTTP | Retry? | Alasan |
|------|--------|--------|
| 200 | — | Sukses |
| 400 | **Tidak** | Request salah (gambar invalid, dll.) |
| 401 | **Tidak** | API key salah — perbaiki konfigurasi |
| 413 | **Tidak** | File terlalu besar — compress/resize dulu |
| 429 | **Ya** | Rate limit — tunggu & coba lagi |
| 500 | **Ya** | Error server sementara |
| 502 / 503 / 504 | **Ya** | Gateway / service belum siap |
| Network timeout | **Ya** | Koneksi terputus |

### Strategi yang disarankan

- **Maks. percobaan:** 3 (total 1 request awal + 2 retry)
- **Backoff:** exponential — 1s → 2s → 4s (+ jitter acak 0–500ms)
- **Timeout per request:** 120 detik (inferensi ML bisa lambat)
- **Jangan retry** jika `success: false` dengan HTTP 400/401/413

### Contoh (Python + `requests`)

```python
import random
import time
import requests

MAX_RETRIES = 3
BASE_DELAY_SEC = 1.0
TIMEOUT_SEC = 120
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def predict_with_retry(image_path: str, api_key: str, base_url: str) -> dict:
    url = f"{base_url.rstrip('/')}/predict"
    headers = {"X-API-Key": api_key}

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(image_path, "rb") as f:
                response = requests.post(
                    url,
                    headers=headers,
                    files={"image": f},
                    timeout=TIMEOUT_SEC,
                )

            payload = response.json()

            if response.status_code == 200:
                return {
                    "ok": True,
                    "status": response.status_code,
                    "body": payload,
                    "attempt": attempt,
                }

            if response.status_code not in RETRYABLE_STATUS:
                return {
                    "ok": False,
                    "status": response.status_code,
                    "body": payload,
                    "attempt": attempt,
                    "retryable": False,
                }

            last_error = payload

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = {"success": False, "message": str(exc)}

        if attempt < MAX_RETRIES:
            delay = BASE_DELAY_SEC * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            time.sleep(delay)

    return {
        "ok": False,
        "status": None,
        "body": last_error,
        "attempt": MAX_RETRIES,
        "retryable": True,
    }
```

### Contoh (JavaScript)

```javascript
const RETRYABLE = new Set([429, 500, 502, 503, 504]);

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function predictWithRetry(file, apiKey, baseUrl, maxRetries = 3) {
  let lastResult = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const form = new FormData();
    form.append("image", file);

    try {
      const res = await fetch(`${baseUrl}/predict`, {
        method: "POST",
        headers: { "X-API-Key": apiKey },
        body: form,
        signal: AbortSignal.timeout(120_000),
      });

      const body = await res.json();
      lastResult = { status: res.status, body, attempt };

      if (res.ok) return { ok: true, ...lastResult };
      if (!RETRYABLE.has(res.status)) {
        return { ok: false, retryable: false, ...lastResult };
      }
    } catch (err) {
      lastResult = {
        status: 0,
        body: { success: false, message: String(err) },
        attempt,
      };
    }

    if (attempt < maxRetries) {
      const delay = 1000 * 2 ** (attempt - 1) + Math.random() * 500;
      await sleep(delay);
    }
  }

  return { ok: false, retryable: true, ...lastResult };
}
```

---

## Fallback Response

Jika API gagal setelah semua retry, kembalikan respons **fallback** yang konsisten agar UI tidak crash.

### Prinsip

1. Jangan tampilkan `message` error mentah dari server ke end-user (bisa berisi detail teknis).
2. Bedakan **error teknis** (log internal) vs **pesan user-friendly**.
3. Struktur fallback harus mirip hasil normal agar komponen UI bisa render tanpa branch khusus.

### Template fallback

```json
{
  "species": "Tidak diketahui",
  "confidence": 0,
  "confidence_percent": 0,
  "detected": false,
  "total_detections": 0,
  "all_species": [],
  "bbox": null,
  "error": {
    "code": "API_UNAVAILABLE",
    "user_message": "Gagal mengenali ikan. Silakan coba lagi.",
    "retryable": true
  }
}
```

### Mapping kode error

| Situasi | `error.code` | `user_message` (contoh) | `retryable` |
|---------|--------------|-------------------------|-------------|
| Tidak ada deteksi (HTTP 200, `[]`) | — | "Tidak ada ikan terdeteksi dalam gambar." | false |
| Rate limit | `RATE_LIMITED` | "Terlalu banyak permintaan. Tunggu sebentar." | true |
| Gambar invalid | `INVALID_IMAGE` | "Format gambar tidak didukung." | false |
| Unauthorized | `UNAUTHORIZED` | "Konfigurasi layanan tidak valid." | false |
| Server error | `API_UNAVAILABLE` | "Layanan sementara tidak tersedia." | true |
| Timeout | `TIMEOUT` | "Koneksi timeout. Periksa jaringan Anda." | true |

### Contoh fungsi gabungan

```typescript
export function toClientResult(
  apiResult: { ok: boolean; status: number; body: PredictResponse },
  normalized?: NormalizedFishResult
) {
  if (apiResult.ok && normalized?.detected) {
    return { ...normalized, error: null };
  }

  if (apiResult.ok && normalized && !normalized.detected) {
    return {
      ...normalized,
      error: {
        code: "NO_DETECTION",
        user_message: "Tidak ada ikan terdeteksi dalam gambar.",
        retryable: false,
      },
    };
  }

  const status = apiResult.status;
  const code =
    status === 429 ? "RATE_LIMITED" :
    status === 401 ? "UNAUTHORIZED" :
    status === 400 ? "INVALID_IMAGE" :
    status === 0  ? "TIMEOUT" :
    "API_UNAVAILABLE";

  return {
    species: "Tidak diketahui",
    confidence: 0,
    confidence_percent: 0,
    detected: false,
    total_detections: 0,
    all_species: [],
    bbox: null,
    raw_predictions: [],
    error: {
      code,
      user_message: "Gagal mengenali ikan. Silakan coba lagi.",
      retryable: ["RATE_LIMITED", "API_UNAVAILABLE", "TIMEOUT"].includes(code),
    },
  };
}
```

---

## Penyimpanan Respons Mentah untuk Debugging

Simpan respons mentah API untuk investigasi bug, audit, dan perbaikan model — **tanpa** mengekspos data sensitif ke user.

### Apa yang disimpan

```json
{
  "id": "req_20260629_abc123",
  "timestamp": "2026-06-29T10:15:30.123Z",
  "request": {
    "endpoint": "/predict",
    "method": "POST",
    "image_filename": "fish.jpg",
    "image_size_bytes": 245760,
    "image_mime": "image/jpeg"
  },
  "response": {
    "http_status": 200,
    "duration_ms": 1842,
    "headers": {
      "content-type": "application/json"
    },
    "body": {
      "success": true,
      "predictions": []
    }
  },
  "client": {
    "app_version": "1.2.0",
    "platform": "android"
  },
  "normalized": {
    "species": "Tidak terdeteksi",
    "detected": false
  }
}
```

### Yang **tidak** boleh disimpan di log production

- Nilai `X-API-Key`
- Isi binary gambar penuh (kecuali di lingkungan debug khusus)
- Data personal pengguna tanpa consent

### Rekomendasi penyimpanan

| Lingkungan | Tempat | Retensi |
|------------|--------|---------|
| Development | File lokal / console | 7 hari |
| Staging | Database / S3 bucket debug | 30 hari |
| Production | Structured log (JSON lines) | 14–30 hari |

### Contoh logger (Python)

```python
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEBUG_LOG_DIR = Path("logs/api_raw")


def save_raw_response(
    *,
    image_filename: str,
    image_size: int,
    http_status: int,
    duration_ms: float,
    response_body: dict,
    normalized: dict,
    platform: str = "unknown",
) -> str:
    DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)

    record_id = f"req_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    record = {
        "id": record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": {
            "endpoint": "/predict",
            "method": "POST",
            "image_filename": image_filename,
            "image_size_bytes": image_size,
        },
        "response": {
            "http_status": http_status,
            "duration_ms": round(duration_ms, 2),
            "body": response_body,
        },
        "client": {"platform": platform},
        "normalized": normalized,
    }

    log_file = DEBUG_LOG_DIR / f"{record_id}.json"
    log_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record_id
```

### Contoh logger (JavaScript / Node)

```javascript
import { writeFile, mkdir } from "fs/promises";
import { randomUUID } from "crypto";

export async function saveRawResponse({
  imageFilename,
  imageSize,
  httpStatus,
  durationMs,
  responseBody,
  normalized,
  platform = "web",
}) {
  const id = `req_${new Date().toISOString().slice(0, 10).replace(/-/g, "")}_${randomUUID().slice(0, 8)}`;
  const record = {
    id,
    timestamp: new Date().toISOString(),
    request: {
      endpoint: "/predict",
      method: "POST",
      image_filename: imageFilename,
      image_size_bytes: imageSize,
    },
    response: {
      http_status: httpStatus,
      duration_ms: Math.round(durationMs),
      body: responseBody,
    },
    client: { platform },
    normalized,
  };

  await mkdir("logs/api_raw", { recursive: true });
  await writeFile(`logs/api_raw/${id}.json`, JSON.stringify(record, null, 2));
  return id;
}
```

> Tambahkan `logs/api_raw/` ke `.gitignore` di project client Anda.

---

## Contoh Implementasi Lengkap

Alur integrasi yang disarankan:

```
1. Pilih & validasi gambar di client
2. POST /predict dengan retry
3. Validasi JSON respons
4. Normalisasi predictions → NormalizedFishResult
5. Jika gagal → fallback response
6. Simpan raw response untuk debugging
7. Tampilkan hasil ke user
```

### Python — pipeline lengkap

```python
import time

from your_app.fish_api import (
    normalize_predictions,
    parse_predict_response,
    predict_with_retry,
    save_raw_response,
    to_fallback,
)


def identify_fish(image_path: str, api_key: str, base_url: str):
    started = time.perf_counter()
    raw = predict_with_retry(image_path, api_key, base_url)
    duration_ms = (time.perf_counter() - started) * 1000

    body = raw.get("body") or {}
    parsed = parse_predict_response(raw.get("status") or 0, body)

    if parsed.success:
        normalized = normalize_predictions(
            [p.model_dump() for p in parsed.predictions]
        )
        result = normalized if normalized.detected else to_fallback("NO_DETECTION")
    else:
        result = to_fallback_from_api(raw.get("status"), parsed.message)

    save_raw_response(
        image_filename=image_path.split("/")[-1],
        image_size=0,  # isi dari os.path.getsize(image_path)
        http_status=raw.get("status") or 0,
        duration_ms=duration_ms,
        response_body=body,
        normalized=result.__dict__ if hasattr(result, "__dict__") else result,
    )

    return result
```

---

## Checklist Integrasi

- [ ] Simpan `API_KEY` di environment variable (bukan hardcode di source)
- [ ] Set timeout request ≥ 120 detik
- [ ] Validasi JSON sebelum akses field
- [ ] Normalisasi multi-detection ke satu hasil utama
- [ ] Implement retry hanya untuk 429 / 5xx / timeout
- [ ] Siapkan fallback response untuk UI
- [ ] Log respons mentah untuk debugging (tanpa API key)
- [ ] Tes dengan gambar: ada ikan, tidak ada ikan, file corrupt, file > 10 MB

---

## Dukungan

- Health: `GET /health`
- Readiness: `GET /ready`
- Base URL production: `https://fish-species.ferxcode.my.id`

Untuk setup server & deployment, lihat [TUTORIAL.md](./TUTORIAL.md).
