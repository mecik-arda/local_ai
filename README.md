# local_ai

CyberPUF and LLM Model Local Management System.
This project serves as the main CLI and orchestration layer for managing CyberPUF and CyberPUF_LLM modules.

[Türkçe](#türkçe-dokümantasyon) | [English](#english-documentation)

---

## Türkçe Dokümantasyon

### 🌟 Sürüm v5.0.0-Platinum (Gelişmiş Özellikler Güncellemesi)
Bu sürümle birlikte projeye 5 devasa yerel yetenek, dinamik bir bağlamsal yardım sistemi ve kararlılık iyileştirmeleri eklenmiştir.

#### 1. Terminal Ajanı Modu (`/calistir`) 💻
- Terminal veya shell komutlarını yerel yapay zeka üzerinden güvenle çalıştırın.
- **Siber Güvenlik Çemberi:** Komutlar çalıştırılmadan önce `[E/H]` onayı istenir.
- Çıktılar otomatik yakalanıp asistanın RAG bağlamına eklenerek analiz edilir.

#### 2. Zero-API Yerel Web Arama (`/ara`) 🌍
- DuckDuckGo entegrasyonu sayesinde herhangi bir ücretli API anahtarına gerek kalmadan anlık internet aramaları gerçekleştirilir.
- Çekilen web sonuçları LLM'e özetletilir, böylece yapay zekanın güncel bilgiye erişimi sağlanır.

#### 3. Sesli Asistan ve Çevrimdışı TTS (`/ses-dinle` & `/ayarlar`) 🎙️
- `/ses-dinle` komutu ile mikrofondan Türkçe ses kaydı alınıp yazıya dönüştürülür.
- Ayarlar menüsüne eklenen **(11) Sesli Yanıt / TTS** seçeneği ile yapay zekanın yanıtları çevrimdışı ses motoru (`pyttsx3`) aracılığıyla anında seslendirilir.

#### 4. Canlı HUD (Heads-Up Dashboard) 📊
- Yapay zeka çıktı üretirken terminalin en alt satırında gerçek zamanlı kaynak takibi yapar.
- Eşzamanlı olarak `%CPU | %RAM | Hız (Token/Saniye) | Toplam Token` bilgilerini, metin akışını bozmadan (ANSI kaçış kodlarıyla) gösterir.

#### 5. Görsel Analiz - OCR Destekli Vision (`/goster`) 👁️
- RAM darboğazlarını ve GPU USM sızıntılarını önlemek adına ağır Vision modelleri yerine çok hafif bir OCR motoru (`Tesseract`) kullanılmıştır.
- Belirtilen resimdeki/kod ekran görüntüsündeki metinleri okuyup yapay zekanın analiz etmesini sağlar.

#### 6. Bağlamsal Yardım Sistemi (`/yardim`) ℹ️
- Yardım çıktısı bulunduğunuz yere göre dinamik olarak değişir:
  - **Ana Menüde:** Model kategorileri ve özel model yükleme ipuçları.
  - **Ayarlar Menüsünde:** CyberPUF güvenlik katmanları ve donanım yapılandırma parametreleri.
  - **Sohbet Oturumunda:** `/calistir`, `/ara`, `/goster`, `/ses-dinle` gibi sohbet komutlarının detayları.

---

### 🔑 Ana Güvenlik Özellikleri (CyberPUF Entegrasyonu)
1. **Donanım Doğrulaması (TPM 2.0 & TEE Enklavı):** TEE Docker enklavları ve simüle TPM 2.0 imzaları ile ana bilgisayar bütünlüğünü kontrol eder.
2. **Kuantum Sonrası Kriptografi (PQC ML-KEM/Kyber):** Hibrit kuantum dirençli anahtar kapsülleme (ML-KEM) uygular.
3. **Anti-Debugging ve Koruyucu Watchdog:** `ptrace` ve `TracerPid` taraması ile tersine mühendislik girişimlerini algılar ve kendini kapatıp hafızayı sıfırlar.
4. **Layer-by-Layer Paging:** Modelin tamamının bellekten çekilmesini engellemek için ağırlıkları parçalı şifreler ve sadece aktif nöral katmanı çalışma anında çözer.
5. **WebSocket Canlı Telemetrisi:** Güvenlik olaylarını ve durum loglarını Web Dashboard'a aktarır.

---

### 🛠️ Kurulum (Installation)

#### 1. Sistem Bağımlılıkları (Ubuntu/WSL)
Ses girişi ve OCR işlemleri için gerekli sistem kütüphanelerini yükleyin:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev portaudio19-dev
```

*Not (Ses Desteği):* WSL üzerinden mikrofon kullanıyorsanız, Windows ile WSL arasında ses aktarımı için Windows tarafında `PulseAudio` veya `WSLg` yapılandırması gerekebilir.

#### 2. Python Ortamı ve Bağımlılıklar
Öncelikle projenin Python sanal ortamını (`ai_env`) aktif edin veya bağımlılıkları yükleyin:
```bash
# Sanal ortamı aktif etme
source ai_env/bin/activate

# Gerekli ek kütüphaneleri yükleme
pip install -r requirements.txt
```
*(Gerekirse eksik paketleri manuel yükleyin: `pip install duckduckgo-search SpeechRecognition pyttsx3 pytesseract pyaudio`)*

---

### 🚀 Kullanım Kılavuzu

#### CLI Yöneticisini Başlatma:
```bash
python3 local_ai.py
```

#### Menüler ve Sohbet Komutları:
- **Çıkış:** `exit` veya `quit`
- **Ayarlar Menüsü:** `/ayarlar` (Donanım/Güvenlik modüllerini açıp kapama, TTS aktivasyonu)
- **Model Değiştirme:** `/model`
- **Sistem Kaynakları:** `/sistem`
- **Sohbeti Rapor Olarak Aktarma:** `/disa-aktar rapor.md`
- **Sohbeti Kaydetme/Yükleme:** `/kaydet gecmis.json` | `/yukle gecmis.json`
- **Karakter Değiştirme:** `/karakter` (Asistan, Siber Güvenlikçi, Yazılımcı, Samimi Dost)

---

## English Documentation

### 🌟 Version v5.0.0-Platinum (Advanced Features Update)
This release introduces 5 major offline capabilities, a dynamic contextual help system, and performance improvements to the local AI execution interface.

#### 1. Terminal Agent Mode (`/calistir`) 💻
- Run terminal or shell commands safely through the local AI assistant.
- **CyberPUF Security Shield:** Always prompts for `[Y/N]` approval before executing commands.
- Automatically captures the stdout/stderr and injects it into the LLM context for analysis.

#### 2. Zero-API Local Web Search (`/ara`) 🌍
- Integrates `duckduckgo-search` to perform instant web searches without any paid API keys.
- Web search summaries are parsed and fed directly to the LLM to ground the assistant with current information.

#### 3. Voice Assistant & Offline TTS (`/ses-dinle` & `/ayarlar`) 🎙️
- Capture voice input via `/ses-dinle` using Python's `SpeechRecognition` module.
- Toggle **(11) Sesli Yanıt / TTS** in the Settings menu to enable offline text-to-speech output powered by `pyttsx3`.

#### 4. Live HUD (Heads-Up Dashboard) 📊
- While the LLM is streaming answers, a dedicated HUD displays active resource stats on the very last line of the console.
- Shows `%CPU | %RAM | Speed (Tokens/Second) | Total Tokens` dynamically using ANSI escapes.

#### 5. Image & Screen Analysis - OCR Vision (`/goster`) 👁️
- Leverages `pytesseract` to read code screenshots or document images without loading heavy vision-language models.
- Simply call `/goster image.png "optional prompt"` to extract text and analyze it.

#### 6. Contextual Help System (`/yardim`) ℹ️
- Dynamically outputs help text based on the active screen:
  - **Main Menu:** Tips on model categories and custom HF OpenVINO model loads.
  - **Settings Menu:** Description of CyberPUF security features and device configurations.
  - **Chat Session:** List and usage examples of slash commands like `/calistir`, `/ara`, `/goster`, `/ses-dinle`.

---

### 🔑 Key Security Architecture (CyberPUF Enclave)
1. **Hardware Attestation (TPM 2.0 & TEE):** Evaluates host integrity through simulated TPM 2.0 quotes and TEE Docker enclaves.
2. **Post-Quantum Cryptography (PQC ML-KEM/Kyber):** Quantum-resistant hybrid key encapsulation protects model decryption keys.
3. **Anti-Debugging Tracers:** Hooks `ptrace` and scans `TracerPid` to block dynamic analysis. Triggers automatic zeroization if a debugger is attached.
4. **Layer-by-Layer Paging:** Prevents full weights extraction by cryptographically slicing weights, keeping only the active neural layer plaintext in memory.
5. **WebSocket Telemetry:** Pushes real-time alerts and state logs to the secure Web Dashboard.

---

### 🛠️ Requirements & Setup

#### 1. System Packages (Ubuntu/WSL)
Install the required development headers and binaries for audio and OCR functionality:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev portaudio19-dev
```

*Note (WSL Audio):* Using voice recognition under WSL might require setting up a `PulseAudio` client bridge to Windows.

#### 2. Virtual Environment Setup
Ensure you activate your virtual environment (`ai_env`) before installing Python packages:
```bash
source ai_env/bin/activate
pip install -r requirements.txt
```

---

### 🚀 Usage Guide

#### Start the CLI Orchestration:
```bash
python3 local_ai.py
```

#### Slash Commands & Toggles:
- **Quit CLI:** `exit` or `quit`
- **Configure Features:** `/ayarlar` (Toggle TPM, PQC, Anti-Debug, and TTS options)
- **Swap Models:** `/model` (Unloads current weights from memory and goes back to main menu)
- **Check Resource Load:** `/sistem`
- **Export Markdown Report:** `/disa-aktar report.md`
- **Save/Load Session:** `/kaydet history.json` | `/yukle history.json`
- **Set Character Profile:** `/karakter` (Assistant, Cyber Security Expert, Software Developer, Close Friend)
