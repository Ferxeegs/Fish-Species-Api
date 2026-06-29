"""OpenAPI 3.0 specification builder for Fish Species API."""

from config.settings import settings


def build_openapi_spec(server_url: str = "") -> dict:
    base = server_url.rstrip("/") if server_url else ""
    allowed_ext = ", ".join(sorted(settings.allowed_extensions))
    species_list = ", ".join(settings.class_names)

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Fish Species API",
            "description": (
                "REST API untuk mendeteksi dan mengklasifikasi spesies ikan "
                "dari gambar menggunakan model YOLO.\n\n"
                "### Autentikasi\n"
                "Endpoint `POST /predict` memerlukan header `X-API-Key`.\n"
                "Klik tombol **Authorize** di atas, masukkan API key Anda, "
                "lalu gunakan **Try it out** untuk menguji endpoint.\n\n"
                f"### Spesies yang didukung\n{species_list}\n\n"
                f"### Upload\n"
                f"- Format: {allowed_ext}\n"
                f"- Ukuran maks.: {settings.max_upload_size_mb} MB\n"
                f"- Rate limit: {settings.rate_limit}"
            ),
            "version": "1.0.0",
            "contact": {
                "name": "Fish Species API",
                "url": base or "https://fish-species.ferxcode.my.id",
            },
        },
        "servers": [{"url": base or "/"}],
        "tags": [
            {"name": "Health", "description": "Monitoring & readiness probes"},
            {"name": "Prediction", "description": "Deteksi spesies ikan dari gambar"},
        ],
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Liveness check",
                    "description": "Memastikan proses aplikasi berjalan.",
                    "operationId": "healthCheck",
                    "responses": {
                        "200": {
                            "description": "Service is alive",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/ready": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Readiness check",
                    "description": "Memastikan model YOLO sudah dimuat dan siap menerima inferensi.",
                    "operationId": "readinessCheck",
                    "responses": {
                        "200": {
                            "description": "Model is ready",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ReadyResponse"}
                                }
                            },
                        },
                        "503": {
                            "description": "Model not loaded yet",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/NotReadyResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/predict": {
                "post": {
                    "tags": ["Prediction"],
                    "summary": "Deteksi spesies ikan",
                    "description": (
                        "Mengunggah gambar ikan dan mendapatkan daftar deteksi "
                        "dengan bounding box, confidence, dan nama spesies."
                    ),
                    "operationId": "predictFishSpecies",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["image"],
                                    "properties": {
                                        "image": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": (
                                                f"File gambar ({allowed_ext}), "
                                                f"maks. {settings.max_upload_size_mb} MB"
                                            ),
                                        }
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Prediksi berhasil (bisa kosong jika tidak ada deteksi)",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/PredictSuccess"},
                                    "examples": {
                                        "with_detection": {
                                            "summary": "Satu ikan terdeteksi",
                                            "value": {
                                                "success": True,
                                                "predictions": [
                                                    {
                                                        "center_x": 320.5,
                                                        "center_y": 240.2,
                                                        "width": 150.0,
                                                        "height": 80.5,
                                                        "confidence": 0.87,
                                                        "class_name": "Ikan Gurame",
                                                    }
                                                ],
                                            },
                                        },
                                        "no_detection": {
                                            "summary": "Tidak ada deteksi",
                                            "value": {
                                                "success": True,
                                                "predictions": [],
                                            },
                                        },
                                    },
                                }
                            },
                        },
                        "400": {
                            "description": "Request tidak valid",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "examples": {
                                        "no_image": {
                                            "value": {
                                                "success": False,
                                                "message": "No image provided",
                                            }
                                        },
                                        "invalid_file": {
                                            "value": {
                                                "success": False,
                                                "message": "Invalid or corrupted image file",
                                            }
                                        },
                                    },
                                }
                            },
                        },
                        "401": {
                            "description": "API key tidak valid atau tidak dikirim",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "success": False,
                                        "message": "Unauthorized",
                                    },
                                }
                            },
                        },
                        "413": {
                            "description": "File terlalu besar",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "success": False,
                                        "message": (
                                            f"File exceeds maximum size of "
                                            f"{settings.max_upload_size_mb} MB"
                                        ),
                                    },
                                }
                            },
                        },
                        "429": {
                            "description": "Rate limit terlampaui",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "success": False,
                                        "message": "Rate limit exceeded. Try again later.",
                                    },
                                }
                            },
                        },
                        "500": {
                            "description": "Kesalahan server saat inferensi",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "success": False,
                                        "message": "Error processing image",
                                    },
                                }
                            },
                        },
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key yang diberikan oleh administrator.",
                }
            },
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "required": ["status"],
                    "properties": {
                        "status": {"type": "string", "example": "ok"},
                    },
                },
                "ReadyResponse": {
                    "type": "object",
                    "required": ["status", "model_loaded"],
                    "properties": {
                        "status": {"type": "string", "example": "ready"},
                        "model_loaded": {"type": "boolean", "example": True},
                    },
                },
                "NotReadyResponse": {
                    "type": "object",
                    "required": ["status", "model_loaded"],
                    "properties": {
                        "status": {"type": "string", "example": "not_ready"},
                        "model_loaded": {"type": "boolean", "example": False},
                    },
                },
                "Prediction": {
                    "type": "object",
                    "required": [
                        "center_x",
                        "center_y",
                        "width",
                        "height",
                        "confidence",
                        "class_name",
                    ],
                    "properties": {
                        "center_x": {
                            "type": "number",
                            "format": "float",
                            "description": "Koordinat X pusat bounding box (piksel)",
                            "example": 320.5,
                        },
                        "center_y": {
                            "type": "number",
                            "format": "float",
                            "description": "Koordinat Y pusat bounding box (piksel)",
                            "example": 240.2,
                        },
                        "width": {
                            "type": "number",
                            "format": "float",
                            "description": "Lebar bounding box (piksel)",
                            "example": 150.0,
                        },
                        "height": {
                            "type": "number",
                            "format": "float",
                            "description": "Tinggi bounding box (piksel)",
                            "example": 80.5,
                        },
                        "confidence": {
                            "type": "number",
                            "format": "float",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Skor kepercayaan model",
                            "example": 0.87,
                        },
                        "class_name": {
                            "type": "string",
                            "enum": settings.class_names,
                            "example": "Ikan Gurame",
                        },
                    },
                },
                "PredictSuccess": {
                    "type": "object",
                    "required": ["success", "predictions"],
                    "properties": {
                        "success": {"type": "boolean", "enum": [True]},
                        "predictions": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Prediction"},
                        },
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "required": ["success", "message"],
                    "properties": {
                        "success": {"type": "boolean", "enum": [False]},
                        "message": {"type": "string"},
                    },
                },
            },
        },
    }
