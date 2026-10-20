# 1. Base Image: Lingkungan dasar menggunakan Python 3.10 versi slim (Linux Debian minimal)
FROM python:3.10-slim

# 2. Environment Variables: Menghindari pembuatan file bytecode .pyc dan memastikan log tampil langsung
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Direktori kerja di dalam container
WORKDIR /app

# 4. Instalasi pustaka sistem operasi tingkat rendah yang dibutuhkan OpenCV di Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 5. Salin berkas dependensi dan pasang pustaka Python
# Tahap ini dipisah agar Docker dapat memanfaatkan mekanisme caching layer saat build ulang
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Salin seluruh kode sumber microservice ke dalam container
COPY . .

# 7. Dokumentasikan port yang digunakan oleh FastAPI
EXPOSE 8000

# 8. Perintah utama yang dijalankan saat container aktif
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
