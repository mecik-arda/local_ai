# Underworld Framework

Orchestration and CLI Management Layer for CyberPUF and CyberPUF_LLM Modules.

[Türkçe](#türkçe-dokümantasyon) | [English](#english-documentation)

---

## Türkçe Dokümantasyon

### Projenin Amacı ve Kapsamı
Bu proje, CyberPUF (Physical Unclonable Function) tabanlı uç yapay zeka (Edge-AI) model ağırlığı şifreleme sistemi ile optimize edilmiş yerel büyük dil modellerinin (LLM) orkestrasyonunu sağlayan ana kontrol katmanıdır. Underworld Framework, donanım tabanlı siber güvenlik mekanizmalarını (Intel SGX/TEE, TPM 2.0, PQC ve anti-debug korumaları) yerel yapay zeka çıkarım (inference) motoru, Doküman Destekli Arama (RAG) sistemi, sesli/görsel asistan modülleri ve terminal ajanı ile tek bir CLI arayüzünde birleştirir.

---

### Sistem Mimarisi ve Teknik Detaylar

Sistem altı ana bileşenden oluşmaktadır:

#### 1. Çıkarım (Inference) Motoru ve Bellek Yönetimi
- **OpenVINO ve Optimum Intel:** Hugging Face modellerini Intel donanımlarında optimize etmek için Optimum Intel entegrasyonu kullanılır. Modeller FP16 veya INT4 formatlarında çıkarım yapabilir.
- **Dinamik USM Fallback:** Çıkarım hedefleri (CPU/GPU) dinamik olarak seçilir. GPU üzerinde yetersiz USM (Unified Shared Memory) bellek ayrılımı veya geçersiz bellek tahsisi ("large_allocations" hatası) durumunda, sistem çalışma anında otomatik olarak çıkarımı kesintiye uğratmadan CPU moduna düşer (OOM koruması).
- **Transformers Chat Templates:** Tokenizer katmanında yerel modellerin chat_template yapıları çözümlenerek çok turlu sohbetler evrensel şekilde formatlanır. Bellek sınırlarına ulaşıldığında eski bağlamlar dinamik olarak pop edilerek bağlam uzunluğu (Context Window) optimize edilir.

#### 2. Siber Güvenlik Katmanı (CyberPUF_LLM Entegrasyonu)
- **Donanım Onaylama (Hardware Attestation):** TEE (Trusted Execution Environment) Docker yapıları (Gramine/Intel SGX simülasyonu) ve simüle TPM 2.0 alıntıları (quote) aracılığıyla çalışma ortamı bütünlüğü doğrulanır.
- **Kuantum Sonrası Kriptografi (PQC - ML-KEM/Kyber):** Model anahtar üretim süreçlerinde Rust tabanlı mock ML-KEM rutinleri ile kuantum dirençli anahtar kapsülleme uygulanır.
- **Anti-Debugging ve Bellek Koruması:** Linux `ptrace` API'si ve `/proc/self/status` altındaki `TracerPid` alanının periyodik taranması ile dinamik analiz araçlarının (gdb, strace) sisteme bağlanması engellenir. İzinsiz bağlantı durumunda bellek anında sıfırlanır (zeroization).
- **Parçalı Şifre Çözme (Layer-by-Layer Paging):** Bellek üzerinden model ağırlıklarının dump edilmesini önlemek amacıyla, model katmanları parçalar halinde diskte saklanır ve yalnızca çıkarım anında ilgili yapay sinir ağı katmanı şifresi çözülerek belleğe yüklenir. İşlem bitince bellek temizlenir.

#### 3. Doküman Destekli Arama (RAG - Retrieval-Augmented Generation)
- **Vektör Veritabanı:** LangChain altyapısıyla, yerel `docs/` dizinindeki PDF ve TXT dosyaları `RecursiveCharacterTextSplitter` ile parçalanır (chunk size: 500, overlap: 50).
- **Semantik Arama:** `sentence-transformers/all-MiniLM-L6-v2` modeli yerel embedding vektörlerini üretir ve `FAISS` vektör veritabanı indeksine kaydeder. Kullanıcı sorguları bu vektör veri tabanında aratılıp en alakalı ilk üç parça (k=3) asistan bağlamına enjekte edilir.

#### 4. Canlı HUD (Heads-Up Dashboard) ve Streamer
- **ANSI İmleç Yönetimi:** Yapay zeka yanıt verirken çıkarım akışını bozmamak için terminalde ANSI imleç kaydetme/geri yükleme (`\033[s` ve `\033[u`) kodları kullanılır.
- **Sistem Monitörizasyonu:** `psutil` kullanılarak anlık CPU, RAM kullanım yüzdeleri ile çıkarım hızı (Tokens/Second) ve üretilen toplam token sayısı terminalin en alt satırında sabit bir HUD üzerinde canlı olarak gösterilir.

#### 5. Çevrimdışı Ses ve Görsel OCR Entegrasyonu
- **Speech-to-Text (STT):** `SpeechRecognition` kütüphanesi ile mikrofon girişi dinlenir, ortam gürültüsü (`adjust_for_ambient_noise`) kalibre edilir ve ses verisi Google Web Speech API üzerinden metne çevrilir.
- **Text-to-Speech (TTS):** Model tarafından üretilen yanıtlar, `pyttsx3` çevrimdışı ses motoru kullanılarak sesli geri bildirime dönüştürülür.
- **Görsel OCR (Tesseract):** RAM ve GPU yükünü artırmamak adına büyük Vision-Language modelleri yerine hafif `pytesseract` OCR motoru entegre edilmiştir. `/goster` komutu ile görüntülerden metin ve kod blokları ayıklanarak LLM bağlamına eklenir.

#### 6. Terminal Ajanı Modu
- `/calistir` komutu ile asistan, işletim sistemi shell komutlarını `subprocess.check_output` üzerinden güvenli bir subshell altında çalıştırır. Komut çıktısı veya oluşan hata LLM bağlamına otomatik olarak beslenerek analiz etmesi sağlanır.

---

### Kurulum Adımları

#### 1. Sistem Gereksinimleri (Ubuntu/WSL)
OCR ve ses modüllerinin çalışabilmesi için aşağıdaki C++ derleme bileşenleri ve kütüphaneler kurulmalıdır:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev portaudio19-dev
```

#### 2. Python Bağımlılıklarının Yüklenmesi
Projeyi çalıştırmak için `ai_env` adlı sanal ortamı aktif edip gereksinimleri yükleyin:
```bash
source ai_env/bin/activate
pip install -r requirements.txt
```
*Gereksinimler listesi:* `duckduckgo-search`, `SpeechRecognition`, `pyttsx3`, `pytesseract`, `pyaudio`, `transformers`, `optimum-intel`, `openvino`, `psutil`, `langchain-community`, `faiss-cpu`, `sentence-transformers`, `pillow`.

---

### CLI Komutları ve Parametreleri

| Komut | Parametre | Açıklama |
|---|---|---|
| `/ayarlar` | Yok | CPU/GPU seçimi, donanım onaylama, PQC, anti-debug, layer-paging ve sesli yanıt durum toggling işlemleri. |
| `/yardim` | Yok | Çalışılan ekrana göre dinamik (Bağlamsal) açıklama listesi döndürür. |
| `/calistir` | `<sistem_komutu>` | Terminal komutunu işletim sisteminde güvenlik onayıyla çalıştırıp çıktısını modele besler. |
| `/ara` | `<sorgu>` | DuckDuckGo search üzerinden yerel web araması yapar ve güncel sonuçları modele iletir. |
| `/goster` | `<resim_yolu> <soru>` | Tesseract ile görüntüyü tarayıp metin/kod bloklarını çıkartır ve soruyla birlikte modele iletir. |
| `/ses-dinle` | Yok | Mikrofon akışını 5 saniye dinleyip sesi metne çevirir. |
| `/model` | Yok | Mevcut modeli RAM'den temizler ve yeni model seçim ekranına döner. |
| `/sistem` | Yok | CPU ve RAM yüzdelik kullanım barını ekrana yazdırır. |
| `/disa-aktar` | `<dosya_adi>` | Mevcut sohbet geçmişini belirtilen Markdown (.md) dosyasına kaydeder. |
| `/kaydet` | `<dosya_adi>` | Sohbet geçmişini JSON formatında kaydeder. |
| `/yukle` | `<dosya_adi>` | JSON formatında kaydedilmiş sohbeti yükler. |
| `/karakter` | Yok | Modelin sistem rolünü (Asistan, Siber Güvenlikçi, Yazılımcı, Samimi Dost) değiştirir. |

---

## English Documentation

### Project Purpose and Scope
This project serves as the primary orchestration and control plane for managing local large language models (LLMs) integrated with the CyberPUF (Physical Unclonable Function) edge cryptographic architecture. Underworld Framework bridges hardware-level security mechanisms (Intel SGX/TEE enclaves, TPM 2.0, PQC, and anti-debug agents) with a optimized inference execution engine, Retrieval-Augmented Generation (RAG), voice/vision capabilities, and an autonomous terminal execution environment under a unified CLI.

---

### System Architecture and Technical Specifications

The system is structured around six core modules:

#### 1. Optimized Inference & Memory Fallback
- **OpenVINO and Optimum Intel:** Models are compiled and executed using Intel OpenVINO via Optimum Intel. FP16 and INT4 execution targets are supported.
- **Dynamic USM Fallback:** Inference targets CPU/GPU dynamically. In case of Unified Shared Memory allocation issues (e.g., GPU Out-Of-Memory or "large_allocations" limits), the engine catches the exception and hot-swaps to CPU without interrupting the user session.
- **Context Management:** Tokenizer inputs are structured dynamically through chat templates. When the maximum context limits are approached, the scheduler pops the oldest memory nodes to avoid memory overflows.

#### 2. Cryptographic Security Layer (CyberPUF_LLM)
- **Hardware Attestation:** Confirms runtime platform integrity via TPM 2.0 mock quotes and Dockerized SGX/TEE sim structures.
- **Post-Quantum Cryptography (PQC):** Intercepts key generation procedures using Rust-based ML-KEM/Kyber mock encapsulation.
- **Anti-Debugging Tracers:** Implements active tracers using the Linux `ptrace` API and scans `/proc/self/status` `TracerPid`. If debug attachment (e.g., GDB, strace) is detected, memory buffers are instantly zeroized and the execution terminates.
- **Layer-by-Layer Paging:** To mitigate cold-boot attacks and full weights dumping, weights are stored encrypted. The system loads, decrypts, and executes only one neural layer at a time in memory, zeroing it out immediately afterward.

#### 3. Document-Supported RAG (Retrieval-Augmented Generation)
- **Vector Indexing:** Processes PDF and TXT assets from the local `docs/` directory using LangChain's `RecursiveCharacterTextSplitter` (chunk size: 500, overlap: 50).
- **Semantic Retrieval:** Generates embeddings using `sentence-transformers/all-MiniLM-L6-v2` locally and updates a `FAISS` vector index. The retriever extracts the top three relevant blocks (k=3) to insert into the system prompt.

#### 4. Live HUD & Stream Rendering
- **ANSI Cursor Management:** Saves and restores cursor positions using ANSI escape codes (`\033[s`, `\033[u`) to render system stats dynamically.
- **Real-Time Telemetry:** Computes metrics (CPU load, RAM percentage, tokens generated per second, total token count) via `psutil` and displays it in a sticky HUD status bar.

#### 5. Speech & Lightweight Vision OCR
- **Speech-to-Text (STT):** Microphone signals are captured via `SpeechRecognition`, calibrated for noise, and converted to strings using Google's Web Speech API.
- **Text-to-Speech (TTS):** Converts output strings to voice feedback offline through `pyttsx3`.
- **Lightweight OCR:** Replaces memory-heavy VLMs with `pytesseract` to extract code and text from screenshots or images, appending them to the LLM's dynamic context.

#### 6. Subprocess Terminal Agent
- Executes shell commands within a subshell sandbox using `subprocess.check_output` after a security confirmation prompt. Stdout/stderr results are fed directly to the LLM for diagnosis.

---

### Setup Instructions

#### 1. System Packages (Ubuntu/WSL)
Install libraries for audio stream capture and OCR:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev portaudio19-dev
```

#### 2. Virtual Environment Configuration
Activate `ai_env` and install the pip requirements:
```bash
source ai_env/bin/activate
pip install -r requirements.txt
```

---

### CLI Command Reference

| Command | Argument | Description |
|---|---|---|
| `/ayarlar` | None | Manage targets (CPU/GPU), TPM, PQC, Anti-debug, paging, and voice feedback configurations. |
| `/yardim` | None | Context-aware help listing, dynamically adjusting to the active screen view. |
| `/calistir` | `<command>` | Run a shell script/command and analyze its stdout/stderr inside the LLM context. |
| `/ara` | `<query>` | Query DuckDuckGo and feed live web summaries to the prompt. |
| `/goster` | `<image_path> <prompt>` | Extract text or code snippets from images using Tesseract OCR. |
| `/ses-dinle` | None | Listen to the microphone for 5 seconds and transcribe it to text. |
| `/model` | None | Unload model weights from RAM and navigate back to the model selector. |
| `/sistem` | None | Output current CPU and RAM loads in the console. |
| `/disa-aktar`| `<file_name>` | Export current chat history to a Markdown report format. |
| `/kaydet` | `<file_name>` | Save current session history as a JSON file. |
| `/yukle` | `<file_name>` | Restore a previous chat session from a JSON file. |
| `/karakter` | None | Change system personality (Assistant, Cyber Security Expert, Developer, Friend). |
