# Gramine tabanlı TEE (Trusted Execution Environment) Konteyner Simülasyonu
# Bu imaj, local_ai ve CyberPUF_LLM çekirdek kodunu Intel SGX / AMD SEV benzeri güvenli alanda çalıştırmak için hazırlanmıştır.

FROM ubuntu:22.04

# Temel bağımlılıklar
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip \
    fuse sudo \
    && rm -rf /var/lib/apt/lists/*

# Gramine ve SGX SDK (Simüle)
# Gerçek ortamda gramine-sgx vb. paketler kurulmalıdır.
RUN echo "TEE Environment initialized (Mock SGX Support)"

# Çalışma dizini
WORKDIR /app

# Proje dosyalarını kopyala
COPY ./underw_framework.py /app/
COPY ./CyberPUF_LLM /app/CyberPUF_LLM
COPY ./config.json /app/

# Bağımlılıkları kur
RUN pip3 install -r /app/CyberPUF_LLM/requirements.txt
RUN pip3 install fusepy psutil huggingface_hub

# FUSE ve tmpfs kullanımı için Entrypoint
COPY ./tee_docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# FUSE çalıştırmak için `--privileged` veya `cap_add: SYS_ADMIN` gerektirir.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
