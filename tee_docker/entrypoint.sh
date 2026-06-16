#!/bin/bash
echo "[TEE] Güvenli Alan (Enclave) başlatılıyor..."
echo "[TEE] Donanım korumaları (Intel SGX / AMD SEV) simüle ediliyor..."

# local_ai uygulamasını başlat
python3 /app/local_ai.py
