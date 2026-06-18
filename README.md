# local_ai

Orchestration and CLI Management Layer for CyberPUF and CyberPUF_LLM Modules.

[Turkce](#turkce-dokumantasyon) | [English](#english-documentation)

---

## Turkce Dokumantasyon

### Projenin Amaci ve Kapsami
Bu proje, CyberPUF (Physical Unclonable Function) tabanli uc yapay zeka (Edge-AI) model agirligi sifreleme sistemi ile optimize edilmis yerel buyuk dil modellerinin (LLM) orkestrasyonunu saglayan ana kontrol katmanidir. local_ai, donanim tabanli siber guvenlik mekanizmalarini (Intel SGX/TEE, TPM 2.0, PQC ve anti-debug korumalari) yerel yapay zeka cikarim (inference) motoru, Dokuman Destekli Arama (RAG) sistemi, sesli/gorsel asistan modulleri ve terminal ajani ile tek bir CLI arayuzunde birlestirir.

---

### Sistem Mimarisi ve Teknik Detaylar

Sistem alti ana bilesenden olusmaktadir:

#### 1. Cikarim (Inference) Motoru ve Bellek Yonetimi
- **OpenVINO ve Optimum Intel:** Hugging Face modellerini Intel donanimlarinda optimize etmek icin Optimum Intel entegrasyonu kullanilir. Modeller FP16 veya INT4 formatlarinda cikarim yapabilir.
- **Dinamik USM Fallback:** Cikarim hedefleri (CPU/GPU) dinamik olarak secilir. GPU uzerinde yetersiz USM (Unified Shared Memory) bellek ayrilimi veya gecersiz bellek tahsisi ("large_allocations" hatasi) durumunda, sistem calisma aninda otomatik olarak cikarimi kesintiye ugratmadan CPU moduna duser (OOM korumasi).
- **Transformers Chat Templates:** Tokenizer katmaninda yerel modellerin chat_template yapilari cozumlenerek cok turlu sohbetler evrensel sekilde formatlanir. Bellek sinirlarina ulasildiginda eski baglamlar dinamik olarak pop edilerek baglam uzunlugu (Context Window) optimize edilir.

#### 2. Siber Guvenlik Katmani (CyberPUF_LLM Entegrasyonu)
- **Donanim Onaylama (Hardware Attestation):** TEE (Trusted Execution Environment) Docker yapilari (Gramine/Intel SGX simülasyonu) ve simüle TPM 2.0 alintilari (quote) araciligiyla calisma ortami butunlugu dogrulanir.
- **Kuantum Sonrasi Kriptografi (PQC - ML-KEM/Kyber):** Model anahtar uretim sureclerinde Rust tabanli mock ML-KEM rutinleri ile kuantum direncli anahtar kapsulleme uygulanir.
- **Anti-Debugging ve Bellek Korumasi:** Linux `ptrace` API'si ve `/proc/self/status` altindaki `TracerPid` alaninin periyodik taranmasi ile dinamik analiz araclarinin (gdb, strace) sisteme baglanmasi engellenir. Izinsiz baglanti durumunda bellek aninda sifirlanir (zeroization).
- **Parcali Sifre Cozme (Layer-by-Layer Paging):** Bellek uzerinden model agirliklarinin dump edilmesini onlemek amaciyla, model katmanlari parcalar halinde diskte saklanir ve yalnizca cikarim aninda ilgili yapay sinir agi katmani sifresi cozülerek bellege yuklenir. Islem bitince bellek temizlenir.

#### 3. Dokuman Destekli Arama (RAG - Retrieval-Augmented Generation)
- **Vektor Veritabani:** LangChain altyapisiyla, yerel `docs/` dizinindeki PDF ve TXT dosyalari `RecursiveCharacterTextSplitter` ile parcalanir (chunk size: 500, overlap: 50).
- **Semantik Arama:** `sentence-transformers/all-MiniLM-L6-v2` modeli yerel embedding vektorlerini uretir ve `FAISS` vektor veritabani indeksine kaydeder. Kullanici sorgulari bu vektor veri tabaninda aratilip en alakali ilk uc parca (k=3) asistan baglamina enjekte edilir.

#### 4. Canli HUD (Heads-Up Dashboard) ve Streamer
- **ANSI Imlec Yonetimi:** Yapay zeka yanit verirken cikarim akisini bozmamak icin terminalde ANSI imlec kaydetme/geri yukleme (`\033[s` ve `\033[u`) kodlari kullanilir.
- **Sistem Monitorizasyonu:** `psutil` kullanilarak anlik CPU, RAM kullanim yuzdeleri ile cikarim hizi (Tokens/Second) ve uretilen toplam token sayisi terminalin en alt satirinda sabit bir HUD uzerinde canli olarak gosterilir.

#### 5. Cevrimdisi Ses ve Gorsel OCR Entegrasyonu
- **Speech-to-Text (STT):** `SpeechRecognition` kütüphanesi ile mikrofon girisi dinlenir, ortam gurultusu (`adjust_for_ambient_noise`) kalibre edilir ve ses verisi Google Web Speech API uzerinden metne cevrilir.
- **Text-to-Speech (TTS):** Model tarafindan uretilen yanitlar, `pyttsx3` cevrimdisi ses motoru kullanilarak sesli geri bildirime donusturulur.
- **Gorsel OCR (Tesseract):** RAM ve GPU yukunu artirmamak adina buyuk Vision-Language modelleri yerine hafif `pytesseract` OCR motoru entegre edilmistir. `/goster` komutu ile goruntulerden metin ve kod bloklari ayiklanarak LLM baglamina eklenir.

#### 6. Terminal Ajani Modu
- `/calistir` komutu ile asistan, isletim sistemi shell komutlarini `subprocess.check_output` uzerinden guvenli bir subshell altinda calistirir. Komut ciktisi veya olusan hata LLM baglamina otomatik olarak beslenerek analiz etmesi saglanir.

---

### Kurulum Adimlari

#### 1. Sistem Gereksinimleri (Ubuntu/WSL)
OCR ve ses modullerinin calisabilmesi icin asagidaki C++ derleme bilesenleri ve kütüphaneler kurulmalidir:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev portaudio19-dev
```

#### 2. Python Bagimliliklarinin Yuklenmesi
Projeyi calistirmak icin `ai_env` adli sanal ortami aktif edip gereksinimleri yukleyin:
```bash
source ai_env/bin/activate
pip install -r requirements.txt
```
*Gereksinimler listesi:* `duckduckgo-search`, `SpeechRecognition`, `pyttsx3`, `pytesseract`, `pyaudio`, `transformers`, `optimum-intel`, `openvino`, `psutil`, `langchain-community`, `faiss-cpu`, `sentence-transformers`, `pillow`.

---

### CLI Komutlari ve Parametreleri

| Komut | Parametre | Aciklama |
|---|---|---|
| `/ayarlar` | Yok | CPU/GPU secimi, donanim onaylama, PQC, anti-debug, layer-paging ve sesli yanit durum toggling islemleri. |
| `/yardim` | Yok | Calisilan ekrana gore dinamik (Baglamsal) aciklama listesi dondurur. |
| `/calistir` | `<sistem_komutu>` | Terminal komutunu isletim sisteminde guvenlik onayiyla calistirip ciktisini modele besler. |
| `/ara` | `<sorgu>` | DuckDuckGo search uzerinden yerel web aramasi yapar ve guncel sonuclari modele iletir. |
| `/goster` | `<resim_yolu> <soru>` | Tesseract ile goruntuyu tarayip metin/kod bloklarini cikartir ve soruyla birlikte modele iletir. |
| `/ses-dinle` | Yok | Mikrofon akisini 5 saniye dinleyip sesi metne cevirir. |
| `/model` | Yok | Mevcut modeli RAM'den temizler ve yeni model secim ekranina doner. |
| `/sistem` | Yok | CPU ve RAM yuzdelik kullanim barini ekrana yazdirir. |
| `/disa-aktar` | `<dosya_adi>` | Mevcut sohbet gecmisini belirtilen Markdown (.md) dosyasina kaydeder. |
| `/kaydet` | `<dosya_adi>` | Sohbet gecmisini JSON formatinda kaydeder. |
| `/yukle` | `<dosya_adi>` | JSON formatinda kaydedilmis sohbeti yukler. |
| `/karakter` | Yok | Modelin sistem rolunu (Asistan, Siber Guvenlikci, Yazilimci, Samimi Dost) degistirir. |

---

## English Documentation

### Project Purpose and Scope
This project serves as the primary orchestration and control plane for managing local large language models (LLMs) integrated with the CyberPUF (Physical Unclonable Function) edge cryptographic architecture. local_ai bridges hardware-level security mechanisms (Intel SGX/TEE enclaves, TPM 2.0, PQC, and anti-debug agents) with a optimized inference execution engine, Retrieval-Augmented Generation (RAG), voice/vision capabilities, and an autonomous terminal execution environment under a unified CLI.

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
