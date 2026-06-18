import os
import glob
import sys
import time
import signal
import warnings
import gc
import psutil

import threading
print_lock = threading.Lock()

import json
from dotenv import load_dotenv
load_dotenv()
cpuf_process = None

warnings.filterwarnings("ignore")
from transformers import AutoTokenizer
from optimum.intel import OVModelForCausalLM
import openvino as ov

# --- YENİ EKLENEN KÜTÜPHANELER ---
import subprocess
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    import speech_recognition as sr
    import pyttsx3
except ImportError:
    sr = None
    pyttsx3 = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None
# --------------------------------

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "language": "TR",
    "device": "AUTO",
    "max_tokens": 512,
    "temperature": 0.7,
    "privacy_mode": False,
    "cyberpuf_enabled": False,
    "hardware_attestation_enabled": False,
    "pqc_enabled": False,
    "anti_debug_enabled": False,
    "telemetry_enabled": False,
    "layer_paging_enabled": False,
    "system_character": "Varsayılan Asistan",
    "voice_feedback_enabled": False,
    "debate_visibility": True
}

LOCALIZATION = {
    "TR": {
        "menu_header": "ANA MENÜ",
        "settings_header": "AYARLAR MENÜSÜ",
        "settings_help": "--- AYARLAR YARDIM MENÜSÜ ---",
        "cat_cyber": "Siber Güvenlik (Pentest, Sızma Testi, Exploit/Zararlı Analizi)",
        "cat_doc": "Belge, PDF ve Dosya İşlemleri (Özetleme, Düzenleme, Raporlama)",
        "cat_gen": "Genel Kullanım ve Hafif Modeller (Hızlı Sohbet, Günlük İşler)",
        "cat_hf": "HuggingFace OpenVINO Model ID'si ile Başlat",
        "cat_settings": "Ayarlar",
        "cat_cpuf": "CyberPUF LLM Dashboard Başlat",
        "cat_exit": "Çıkış",
        "cat_back": "[Geri Dön]",
        "prompt_category": "Lütfen bir kategori seçin",
        "prompt_model": "Lütfen bir model seçin",
        "prompt_hf": "HuggingFace OpenVINO Model ID'si:",
        "prompt_invalid": "Geçersiz seçim. Lütfen tekrar deneyin.",
        "settings_opt": [
            "Hedef Cihaz",
            "Maksimum Cevap Uzunluğu",
            "Model Yaratıcılığı/Sıcaklık",
            "Gizlilik Modu",
            "CyberPUF LLM Modülü",
            "Donanım Onaylama",
            "PQC / Kuantum Sonrası",
            "Anti-Debugging",
            "Dashboard Telemetrisi",
            "Parçalı Şifre Çözme",
            "Sesli Yanıt / TTS",
            "Çoklu Ajan Canlı Tartışma",
            "Dil (Language)",
            "Ayarları Sıfırla",
            "Kaydet ve Geri Dön"
        ],
        "on": "AÇIK",
        "off": "KAPALI",
        "sys_ready": "[SİSTEM] Sistem hazır! Yerel yapay zeka başarıyla başlatıldı.",
        "cmd_exit": "Çıkış",
        "question": "Soru:",
        "ai_name": "Yapay Zeka:",
        "generating": "Cevap üretiliyor...",
        "memory_cleared": "RAM başarıyla temizlendi!",
        "lang_changed": "Dil TR olarak ayarlandı."
    },
    "EN": {
        "menu_header": "MAIN MENU",
        "settings_header": "SETTINGS MENU",
        "settings_help": "--- SETTINGS HELP MENU ---",
        "cat_cyber": "Cyber Security (Pentest, Exploits, Malware Analysis)",
        "cat_doc": "Document, PDF and File Operations (Summary, Edit, Report)",
        "cat_gen": "General Usage & Lightweight Models (Quick Chat, Daily Tasks)",
        "cat_hf": "Launch via HuggingFace OpenVINO Model ID",
        "cat_settings": "Settings",
        "cat_cpuf": "Launch CyberPUF LLM Dashboard",
        "cat_exit": "Exit",
        "cat_back": "[Go Back]",
        "prompt_category": "Please select a category",
        "prompt_model": "Please select a model",
        "prompt_hf": "HuggingFace OpenVINO Model ID:",
        "prompt_invalid": "Invalid selection. Please try again.",
        "settings_opt": [
            "Target Device",
            "Max Response Length",
            "Model Temperature",
            "Privacy Mode",
            "CyberPUF LLM Module",
            "Hardware Attestation",
            "PQC / Post-Quantum",
            "Anti-Debugging",
            "Dashboard Telemetry",
            "Layer-by-Layer Paging",
            "Voice Feedback / TTS",
            "Multi-Agent Live Debate",
            "Language (Dil)",
            "Reset Settings",
            "Save & Go Back"
        ],
        "on": "ON",
        "off": "OFF",
        "sys_ready": "[SYSTEM] System ready! Local AI successfully launched.",
        "cmd_exit": "Exit",
        "question": "Question:",
        "ai_name": "AI:",
        "generating": "Generating response...",
        "memory_cleared": "RAM successfully cleared!",
        "lang_changed": "Language set to EN."
    }
}

def get_loc(key, lang="TR"):
    return LOCALIZATION.get(lang, LOCALIZATION["TR"]).get(key, key)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"\n{CYAN}{BOLD}" + "="*80)
    print("  _   _ _   _ ____  _____ ______        _____  ____  _     ____  ")
    print(" | | | | \\ | |  _ \\| ____|  _ \\ \\      / / _ \\|  _ \\| |   |  _ \\ ")
    print(" | | | |  \\| | | | |  _| | |_) \\ \\ /\\ / / | | | |_) | |   | | | |")
    print(" | |_| | |\\  | |_| | |___|  _ < \\ V  V /| |_| |  _ <| |___| |_| |")
    print("  \\___/|_| \\_|____/|_____|_| \\_\\ \\_/\\_/  \\___/|_| \\_\\_____|____/ ")
    print("\n" + " "*21 + f"DEVELOPED BY ARDA MEÇİK | AI CORE")
    print("="*80 + f"{RESET}")

def animate_exit():
    global cpuf_process
    print(f"\n{YELLOW}{BOLD}Sistem kapatılıyor...{RESET}")
    
    if cpuf_process is not None and cpuf_process.poll() is None:
        print(f"{RED}Arka plandaki CyberPUF LLM sunucusu kapatılıyor...{RESET}")
        try:
            cpuf_process.terminate()
            cpuf_process.wait(timeout=2)
        except:
            cpuf_process.kill()

    # Gizlilik Modu Kontrolü
    config = load_config()
    if config.get("privacy_mode", False):
        print(f"{RED}{BOLD}Gizlilik Modu aktif: Sohbet geçmişi siliniyor...{RESET}")
        if os.path.exists("chats/sohbet_gecmisi.md"):
            try:
                os.remove("chats/sohbet_gecmisi.md")
                print(f"{GREEN}Geçmiş başarıyla silindi.{RESET}")
            except Exception as e:
                print(f"{RED}Geçmiş silinirken hata oluştu: {e}{RESET}")
        time.sleep(0.5)

    animation = ["[■□□□□□□□□□]", "[■■□□□□□□□□]", "[■■■□□□□□□□]", "[■■■■□□□□□□]", "[■■■■■□□□□□]", 
                 "[■■■■■■□□□□]", "[■■■■■■■□□□]", "[■■■■■■■■□□]", "[■■■■■■■■■□]", "[■■■■■■■■■■]"]
    for frame in animation:
        sys.stdout.write(f"\r{CYAN}{frame}{RESET} Çekirdek sonlandırılıyor ve bağlantılar kesiliyor...")
        sys.stdout.flush()
        time.sleep(0.08)
    print(f"\n{GREEN}{BOLD}Çıkış başarılı. UNDERWORLD kapandı.{RESET}\n")
    sys.exit(0)

def signal_handler(sig, frame):
    animate_exit()

signal.signal(signal.SIGINT, signal_handler)

def settings_menu():
    config = load_config()
    while True:
        lang = config.get("language", "TR")
        loc = LOCALIZATION.get(lang, LOCALIZATION["TR"])
        opts = loc["settings_opt"]
        
        clear_screen()
        print_header()
        print(f"\n{BOLD}{CYAN}" + "="*50)
        print(loc["settings_header"])
        print("="*50 + f"{RESET}")
        def state(val): return loc["on"] if val else loc["off"]
        print(f"  {GREEN}1){RESET} {opts[0]} ({config.get('device', 'AUTO')})")
        print(f"  {GREEN}2){RESET} {opts[1]} ({config.get('max_tokens', 512)})")
        print(f"  {GREEN}3){RESET} {opts[2]} ({config.get('temperature', 0.7)})")
        print(f"  {GREEN}4){RESET} {opts[3]} ({state(config.get('privacy_mode', False))})")
        print(f"  {GREEN}5){RESET} {opts[4]} ({state(config.get('cyberpuf_enabled', False))})")
        print(f"  {GREEN}6){RESET} {opts[5]} ({state(config.get('hardware_attestation_enabled', False))})")
        print(f"  {GREEN}7){RESET} {opts[6]} ({state(config.get('pqc_enabled', False))})")
        print(f"  {GREEN}8){RESET} {opts[7]} ({state(config.get('anti_debug_enabled', False))})")
        print(f"  {GREEN}9){RESET} {opts[8]} ({state(config.get('telemetry_enabled', False))})")
        print(f"  {GREEN}10){RESET} {opts[9]} ({state(config.get('layer_paging_enabled', False))})")
        print(f"  {GREEN}11){RESET} {opts[10]} ({state(config.get('voice_feedback_enabled', False))})")
        print(f"  {GREEN}12){RESET} {opts[11]} ({state(config.get('debate_visibility', True))})")
        print(f"  {GREEN}13){RESET} {opts[12]} ({config.get('language', 'TR')})")
        print(f"  {GREEN}14){RESET} {opts[13]}")
        print(f"  {GREEN}15){RESET} {opts[14]}")
        print(f"{CYAN}{BOLD}" + "="*50 + f"{RESET}")
        secim = input(f"\n{BOLD}Seçiminiz (1-15) | /yardim: {RESET}").strip()
        
        if secim.lower() in ["/yardim", "?", "yardım"]:
            print(f"\n{CYAN}{BOLD}--- AYARLAR YARDIM MENÜSÜ ---{RESET}")
            print(f"{YELLOW}1-3) Temel Ayarlar:{RESET} Hedef işlemciyi (CPU/GPU), çıkış token limitini ve yaratıcılık oranını (sıcaklık) belirler.")
            print(f"{YELLOW}4-10) Güvenlik (CyberPUF):{RESET} Gizlilik modunu, donanım doğrulamayı, kuantum sonrası şifrelemeyi ve anti-debug'ı aktif eder.")
            print(f"{YELLOW}11) Sesli Yanıt:{RESET} Çevrimdışı Text-to-Speech motoru ile modelin cevaplarını sesli okutur.")
            print(f"{CYAN}" + "-"*50 + f"{RESET}")
            input(f"\n{BOLD}Devam etmek için Enter'a basın...{RESET}")
            continue
        
        if secim == "1":
            yeni_cihaz = input(f"Hedef cihazı yazın (Örn: AUTO, CPU, GPU, NPU) [Geçerli: {config.get('device', 'AUTO')}]: ").strip().upper()
            if yeni_cihaz:
                config['device'] = yeni_cihaz
                save_config(config)
                print(f"{GREEN}Cihaz {yeni_cihaz} olarak ayarlandı.{RESET}")
                time.sleep(1)
        elif secim == "2":
            yeni_token = input(f"Maksimum token sayısı (Örn: 512, 1024, 2048) [Geçerli: {config.get('max_tokens', 512)}]: ").strip()
            if yeni_token.isdigit():
                config['max_tokens'] = int(yeni_token)
                save_config(config)
                print(f"{GREEN}Maksimum token {yeni_token} olarak ayarlandı.{RESET}")
                time.sleep(1)
            else:
                print(f"{RED}Geçersiz değer.{RESET}")
                time.sleep(1)
        elif secim == "3":
            yeni_temp = input(f"Sıcaklık değeri (Örn: 0.1 ile 1.0 arası) [Geçerli: {config.get('temperature', 0.7)}]: ").strip()
            try:
                temp_val = float(yeni_temp)
                if 0.0 <= temp_val <= 2.0:
                    config['temperature'] = temp_val
                    save_config(config)
                    print(f"{GREEN}Sıcaklık {temp_val} olarak ayarlandı.{RESET}")
                else:
                    print(f"{RED}Değer 0.0 ile 2.0 arasında olmalıdır.{RESET}")
            except:
                print(f"{RED}Geçersiz değer.{RESET}")
            time.sleep(1)
        elif secim == "4":
            current_privacy = config.get("privacy_mode", False)
            config["privacy_mode"] = not current_privacy
            save_config(config)
            print(f"{GREEN}Gizlilik Modu {'KAPALI' if current_privacy else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "5":
            current_cpuf = config.get("cyberpuf_enabled", False)
            config["cyberpuf_enabled"] = not current_cpuf
            save_config(config)
            print(f"{GREEN}CyberPUF LLM Modülü {'KAPALI' if current_cpuf else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "6":
            current_val = config.get("hardware_attestation_enabled", False)
            config["hardware_attestation_enabled"] = not current_val
            save_config(config)
            print(f"{GREEN}Donanım Onaylama {'KAPALI' if current_val else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "7":
            current_val = config.get("pqc_enabled", False)
            config["pqc_enabled"] = not current_val
            save_config(config)
            print(f"{GREEN}PQC Koruması {'KAPALI' if current_val else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "8":
            current_val = config.get("anti_debug_enabled", False)
            config["anti_debug_enabled"] = not current_val
            save_config(config)
            print(f"{GREEN}Anti-Debugging {'KAPALI' if current_val else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "9":
            current_val = config.get("telemetry_enabled", False)
            config["telemetry_enabled"] = not current_val
            save_config(config)
            print(f"{GREEN}Dashboard Telemetrisi {'KAPALI' if current_val else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "10":
            current_val = config.get("layer_paging_enabled", False)
            config["layer_paging_enabled"] = not current_val
            save_config(config)
            print(f"{GREEN}Parçalı Şifre Çözme {'KAPALI' if current_val else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "11":
            current_val = config.get("voice_feedback_enabled", False)
            config["voice_feedback_enabled"] = not current_val
            save_config(config)
            print(f"{GREEN}Sesli Yanıt / TTS {'KAPALI' if current_val else 'AÇIK'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "12":
            current_val = config.get("debate_visibility", True)
            config["debate_visibility"] = not current_val
            save_config(config)
            print(f"{GREEN}Çoklu Ajan Canlı Tartışma {'AÇIK' if not current_val else 'KAPALI'} olarak değiştirildi.{RESET}")
            time.sleep(1)
        elif secim == "13":
            new_lang = "EN" if config.get("language", "TR") == "TR" else "TR"
            config["language"] = new_lang
            save_config(config)
            print(f"{GREEN}Language / Dil -> {new_lang}{RESET}")
            time.sleep(1)
        elif secim == "14":
            config = DEFAULT_CONFIG.copy()
            save_config(config)
            print(f"{GREEN}Ayarlar / Settings reset.{RESET}")
            time.sleep(1)
        elif secim == "15":
            break
        else:
            print(f"{RED}Geçersiz seçim.{RESET}")
            time.sleep(1)

MAX_MEMORY_CHARS = 1500  # Hafıza bağlamının prompt'u şişirmemesi için karakter limiti

def load_memory(memory_dir="memory"):
    if not os.path.exists(memory_dir):
        return ""
    
    memory_texts = []
    for md_path in glob.glob(os.path.join(memory_dir, "*.md")):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                memory_texts.append(f.read().strip())
        except Exception as e:
            print(f"Hafıza yüklenirken hata ({md_path}): {e}")
            
    if memory_texts:
        combined = "\n\n".join(memory_texts)
        if len(combined) > MAX_MEMORY_CHARS:
            combined = combined[:MAX_MEMORY_CHARS] + "\n... (hafıza kırpıldı)"
        return combined
    return ""

def setup_rag(docs_dir="docs", force_refresh=False):
    persist_dir = "memory/chroma_db"
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    if force_refresh and os.path.exists(persist_dir):
        import shutil
        shutil.rmtree(persist_dir, ignore_errors=True)
        print(f"\n[RAG] Eski bellek silindi. Yeniden oluşturuluyor...")
        
    if os.path.exists(persist_dir) and not force_refresh:
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        print(f"\n[RAG] Kalıcı ChromaDB vektör belleği başarıyla yüklendi ({persist_dir}).")
        return vectorstore
        
    if not os.path.exists(docs_dir):
        return None
    
    docs = []
    for pdf_path in glob.glob(os.path.join(docs_dir, "*.pdf")):
        try:
            loader = PyPDFLoader(pdf_path)
            docs.extend(loader.load())
        except Exception as e:
            print(f"Hata ({pdf_path}): {e}")
            
    for txt_path in glob.glob(os.path.join(docs_dir, "*.txt")):
        try:
            loader = TextLoader(txt_path, encoding='utf-8')
            docs.extend(loader.load())
        except Exception as e:
            print(f"Hata ({txt_path}): {e}")
            
    if not docs:
        return None
        
    print("\n[RAG] Belgeler okunuyor ve parçalanıyor...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)
    
    print("[RAG] Vektör veritabanı (ChromaDB) oluşturuluyor (Bu işlem ilk seferde biraz sürebilir)...")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=persist_dir)
    print(f"[RAG] Sistem {len(docs)} sayfa belgeyi ve {len(splits)} parçayı başarıyla kalıcı hafızaya aldı!\n")
    return vectorstore

def select_model():
    config = load_config()
    lang = config.get("language", "TR")
    loc = LOCALIZATION.get(lang, LOCALIZATION["TR"])
    
    while True:
        clear_screen()
        print_header()
        
        print(f"\n{BOLD}{YELLOW}" + loc.get("menu_header", "KATEGORİLER") + f":{RESET}")
        print(f"  {GREEN}1){RESET} Siber Güvenlik (Pentest, Sızma Testi, Exploit/Zararlı Analizi)")
        print(f"  {GREEN}2){RESET} Belge, PDF ve Dosya İşlemleri (Özetleme, Düzenleme, Raporlama)")
        print(f"  {GREEN}3){RESET} Genel Kullanım ve Hafif Modeller (Hızlı Sohbet, Günlük İşler)")
        print(f"  {GREEN}4){RESET} HuggingFace OpenVINO Model ID'si ile Başlat")
        print(f"  {GREEN}5){RESET} Ayarlar")
        if config.get("cyberpuf_enabled", False):
            print(f"  {GREEN}6){RESET} CyberPUF LLM Dashboard Başlat")
            print(f"  {GREEN}7){RESET} Çıkış")
            exit_opt = "7"
        else:
            print(f"  {GREEN}6){RESET} Çıkış")
            exit_opt = "6"
        print(f"{CYAN}{BOLD}" + "="*80 + f"{RESET}")
        
        opts = "1/2/3/4/5/6/7" if config.get("cyberpuf_enabled", False) else "1/2/3/4/5/6"
        kategori = input(f"\n{BOLD}Lütfen bir kategori seçin ({opts}) veya /yardim: {RESET}").strip()
        
        if kategori.lower() in ["/yardim", "?", "yardım"]:
            print(f"\n{CYAN}{BOLD}--- ANA MENÜ YARDIM ---{RESET}")
            print(f"{YELLOW}Kategori 1:{RESET} Ağ trafiği analizi, sızma testi (pentest) raporları ve zafiyet analizleri için eğitilmiş uzman modeller.")
            print(f"{YELLOW}Kategori 2:{RESET} Uzun belgeleri, PDF'leri okumak veya kod yazmak/düzeltmek için geniş bağlam kapasiteli modeller.")
            print(f"{YELLOW}Kategori 3:{RESET} Eski bilgisayarlarda bile çok hızlı çalışan, günlük ve basit görevler için optimize edilmiş hafif modeller.")
            print(f"{YELLOW}Kategori 4:{RESET} Kendi bulduğunuz herhangi bir HF OpenVINO modelini direkt adıyla (örn: OpenVINO/Qwen-1.5B) başlatmanızı sağlar.")
            print(f"{CYAN}" + "-"*50 + f"{RESET}")
            input(f"\n{BOLD}Devam etmek için Enter'a basın...{RESET}")
            continue

        if kategori == "1":
            clear_screen()
            print_header()
            print(f"\n{BOLD}{RED}" + "-"*50)
            print("SİBER GÜVENLİK MODELLERİ")
            print("-"*50 + f"{RESET}")
            print(f"  {GREEN}1){RESET} OpenVINO/DeepSeek-R1-Distill-Qwen-7B-nf4-ov (Düşünme / Akıl Yürütme)")
            print(f"  {GREEN}2){RESET} OpenVINO/Mistral-7B-Instruct-v0.3-int4-ov (Klasik Güvenlik Analizi)")
            print(f"  {GREEN}3){RESET} [Geri Dön]")
            print(f"{RED}{BOLD}" + "-"*50 + f"{RESET}")
            sub_secim = input(f"\n{BOLD}Lütfen bir model seçin (1/2/3): {RESET}").strip()
            if sub_secim == "1":
                return "OpenVINO/DeepSeek-R1-Distill-Qwen-7B-nf4-ov"
            elif sub_secim == "2":
                return "OpenVINO/Mistral-7B-Instruct-v0.3-int4-ov"
            elif sub_secim == "3":
                continue
        elif kategori == "2":
            clear_screen()
            print_header()
            print(f"\n{BOLD}{CYAN}" + "-"*50)
            print("BELGE, PDF VE DOSYA DÜZENLEME MODELLERİ")
            print("-"*50 + f"{RESET}")
            print(f"  {GREEN}1){RESET} OpenVINO/Qwen2.5-14B-Instruct-int4-ov (Çok Zeki, Büyük Raporlar ve Analizler)")
            print(f"  {GREEN}2){RESET} OpenVINO/Qwen2.5-7B-Instruct-int4-ov (Mükemmel Türkçe Dil Desteği)")
            print(f"  {GREEN}3){RESET} [Geri Dön]")
            print(f"{CYAN}{BOLD}" + "-"*50 + f"{RESET}")
            sub_secim = input(f"\n{BOLD}Lütfen bir model seçin (1/2/3): {RESET}").strip()
            if sub_secim == "1":
                return "OpenVINO/Qwen2.5-14B-Instruct-int4-ov"
            elif sub_secim == "2":
                return "OpenVINO/Qwen2.5-7B-Instruct-int4-ov"
            elif sub_secim == "3":
                continue
        elif kategori == "3":
            clear_screen()
            print_header()
            print(f"\n{BOLD}{MAGENTA}" + "-"*50)
            print("GENEL KULLANIM VE HAFİF MODELLER")
            print("-"*50 + f"{RESET}")
            print(f"  {GREEN}1){RESET} OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov (Çok Hafif, Hızlı ve Dengeli)")
            print(f"  {GREEN}2){RESET} OpenVINO/Phi-3-mini-4k-instruct-int4-ov (Düşük Kaynak Tüketimi)")
            print(f"  {GREEN}3){RESET} [Geri Dön]")
            print(f"{MAGENTA}{BOLD}" + "-"*50 + f"{RESET}")
            sub_secim = input(f"\n{BOLD}Lütfen bir model seçin (1/2/3): {RESET}").strip()
            if sub_secim == "1":
                return "OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov"
            elif sub_secim == "2":
                return "OpenVINO/Phi-3-mini-4k-instruct-int4-ov"
            elif sub_secim == "3":
                continue
        elif kategori == "4":
            clear_screen()
            print_header()
            ozel_model = input(f"\n{BOLD}HuggingFace OpenVINO Model ID'si: {RESET}").strip()
            return ozel_model
        elif kategori == "5":
            settings_menu()
            config = load_config()
        elif config.get("cyberpuf_enabled", False) and kategori == "6":
            global cpuf_process
            if cpuf_process is not None and cpuf_process.poll() is None:
                print(f"{YELLOW}Dashboard zaten arka planda çalışıyor!{RESET}")
            else:
                print(f"{GREEN}CyberPUF LLM Web Dashboard başlatılıyor... (http://127.0.0.1:8000){RESET}")
                import subprocess
                try:
                    cpuf_process = subprocess.Popen(["/home/ardam/local_ai/ai_env/bin/python", "calistirma_betikleri/start_app.py"], cwd="/home/ardam/local_ai/CyberPUF_LLM")
                    print(f"{YELLOW}Dashboard arka planda çalışıyor. Tarayıcınızdan http://127.0.0.1:8000 adresine gidebilirsiniz.{RESET}")
                except Exception as e:
                    print(f"{RED}Dashboard başlatılamadı: {e}{RESET}")
            time.sleep(2)
        elif kategori == exit_opt:
            animate_exit()
        else:
            print(f"{RED}Geçersiz seçim. Lütfen tekrar deneyin.{RESET}")
            time.sleep(1.5)

def load_ai_model(model_id, core, device_target):
    print(f"\n[1/2] Tokenizer yükleniyor: {model_id}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    except Exception as e:
        print(f"\nHATA: Tokenizer yüklenemedi. Model ismini yanlış girmiş olabilirsiniz veya internet bağlantınız kopuk olabilir. ({e})")
        return None, None

    print(f"[2/2] Optimize edilmiş OpenVINO modeli indiriliyor ve Intel {device_target} üzerinde derleniyor...")
    try:
        # Eski hatalı ov_config tamamen kaldırıldı, çünkü sürüm uyuşmazlığına neden oluyor.
        model = OVModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            device=device_target
        )
        return tokenizer, model
    except Exception as e:
        if device_target == "GPU" and ("large_allocations" in str(e).lower() or "exceed" in str(e).lower() or "usm" in str(e).lower()):
            print(f"\n{YELLOW}UYARI: GPU belleği yetersiz kaldı! Olası USM sızıntısı veya sınır aşımı.{RESET}")
            print(f"{YELLOW}Sistem otomatik olarak CPU moduna geçiş yapıyor... Lütfen bekleyin.{RESET}")
            try:
                model = OVModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    device="CPU"
                )
                print(f"{GREEN}>> Model CPU üzerinde başarıyla derlendi!{RESET}")
                return tokenizer, model
            except Exception as e2:
                print(f"\n{RED}HATA: Model CPU'da da yüklenemedi: {e2}{RESET}")
                return None, None
        else:
            print(f"\nHATA: Model yüklenemedi. Lütfen boş diskinizi ve internetinizi kontrol edin. ({e})")
            if "large_allocations" in str(e).lower() or "exceed" in str(e).lower():
                print(f"{YELLOW}İpucu: GPU belleği yetersiz. Cihazı CPU olarak değiştirmeyi deneyin (/ayarlar).{RESET}")
            return None, None

if __name__ == "__main__":
    model_id = select_model()
    
    print("\n[1/4] Intel OpenVINO Core katmanı başlatılıyor...")
    core = ov.Core()

    print("\n--- Kullanılabilir Yerel Donanım Birimleri ---")
    for device in core.available_devices:
        print(f"- Cihaz: {device}")
    print("---------------------------------------------\n")

    config = load_config()
    device_target = config.get("device", "AUTO")
    if device_target == "AUTO":
        device_target = "GPU" if "GPU" in core.available_devices else "CPU"
    print(f"Seçilen Aktif Çıkarım Hedefi: {device_target}")

    tokenizer, model = load_ai_model(model_id, core, device_target)
    if not tokenizer or not model:
        sys.exit(1)
    
    print("\n[3/3] RAG Sistemi başlatılıyor (docs klasörü kontrol ediliyor)...")
    vectorstore = setup_rag(docs_dir="docs")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) if vectorstore else None

    print(f"\n{GREEN}{BOLD}[SİSTEM] Sistem hazır! Yerel yapay zeka başarıyla başlatıldı.{RESET}")
    print(f"{YELLOW}Sohbet Komutları:{RESET} Çıkış: {BOLD}exit{RESET} | Ana Menü: {BOLD}/menu{RESET} | Ayarlar: {BOLD}/ayarlar{RESET} | Karakter Seç: {BOLD}/karakter{RESET}")
    print(f"{YELLOW}Sistem Komutları:{RESET} Model Değiştir: {BOLD}/model{RESET} | Sistem Kaynakları: {BOLD}/sistem{RESET} | Dışa Aktar: {BOLD}/disa-aktar rapor.md{RESET} | HF İndir: {BOLD}/hf-indir repo_id{RESET}")
    print(f"{YELLOW}Hafıza Komutları:{RESET} Sıfırla: {BOLD}/temizle{RESET} | Gör: {BOLD}/hafiza{RESET} | Yenile: {BOLD}/yenile{RESET} | Kaydet: {BOLD}/kaydet gecmis.json{RESET} | Yükle: {BOLD}/yukle gecmis.json{RESET}")
    print(f"{YELLOW}Ajan Komutları:{RESET} Çalıştır: {BOLD}/calistir komut{RESET} | Ara: {BOLD}/ara sorgu{RESET} | Görsel: {BOLD}/goster img.png soru{RESET} | Ses: {BOLD}/ses-dinle{RESET}")
    print(f"{CYAN}" + "="*80 + f"{RESET}")

    chat_history = []       # Her eleman: {"role": "user"/"assistant", "content": "..."}
    MAX_HISTORY_TURNS = 10  # 5 tur = 10 mesaj (user + assistant)
    memory_context = load_memory()
    
    # Yeni oturum loglaması
    import datetime
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    os.makedirs("chats", exist_ok=True)
    with open("chats/sohbet_gecmisi.md", "a", encoding="utf-8") as f:
        f.write(f"\n\n# YENİ OTURUM - [{now_str}]\n")
        f.write(f"*Kullanılan Model: {model_id} | Sıcaklık: {config.get('temperature', 0.7)}*\n")
        f.write("---\n")

    while True:
        lang = config.get("language", "TR")
        loc = LOCALIZATION.get(lang, LOCALIZATION["TR"])
        user_input = input(f"\n{BOLD}{CYAN}{loc['question']}{RESET} ").strip()
        
        if user_input.lower() in ["exit", "quit", "çıkış"]:
            animate_exit()
        elif user_input.lower() == "/model":
            print(f"\n{YELLOW}Mevcut model RAM'den siliniyor... Lütfen bekleyin.{RESET}")
            try:
                del model
                del tokenizer
                gc.collect()
            except:
                pass
            print(f"{GREEN}RAM başarıyla temizlendi!{RESET}")
            time.sleep(1)
            
            new_model_id = select_model()
            if new_model_id:
                model_id = new_model_id
                tokenizer, model = load_ai_model(model_id, core, device_target)
                if not tokenizer or not model:
                    print(f"{RED}Yeni model yüklenemedi. Çıkış yapılıyor.{RESET}")
                    sys.exit(1)
                print(f"{GREEN}Yeni model başarıyla yüklendi! Kaldığınız yerden devam edebilirsiniz.{RESET}")
                try:
                    with open("chats/sohbet_gecmisi.md", "a", encoding="utf-8") as f:
                        f.write(f"\n\n*--- Model Değiştirildi: {model_id} ---*\n\n")
                except:
                    pass
            continue
        elif user_input.lower() == "/sistem":
            print(f"\n{CYAN}{BOLD}--- SİSTEM KAYNAKLARI ---{RESET}")
            cpu_pct = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            
            def draw_bar(pct, length=20):
                filled = int(length * pct / 100)
                return "█" * filled + "░" * (length - filled)
            
            print(f"CPU Kullanımı: [{draw_bar(cpu_pct)}] %{cpu_pct}")
            print(f"RAM Kullanımı: [{draw_bar(ram.percent)}] %{ram.percent} ({ram.used/(1024**3):.1f}GB / {ram.total/(1024**3):.1f}GB)")
            print(f"{CYAN}" + "-"*25 + f"{RESET}")
            continue
        elif user_input.lower().startswith("/disa-aktar"):
            parts = user_input.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else "rapor.md"
            if not filename.endswith(".md") and not filename.endswith(".html") and not filename.endswith(".txt"):
                filename += ".md"
                
            export_path = os.path.join("exports", filename)
            try:
                os.makedirs("exports", exist_ok=True)
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(f"# DIŞA AKTARILAN SOHBET RAPORU\n")
                    f.write(f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
                    for entry in chat_history:
                        if entry["role"] == "user":
                            f.write(f"## Soru:\n{entry['content']}\n\n")
                        else:
                            f.write(f"## Yapay Zeka:\n{entry['content']}\n\n---\n")
                print(f"{GREEN}>> Sohbet başarıyla '{export_path}' dosyasına aktarıldı!{RESET}")
            except Exception as e:
                print(f"{RED}Dışa aktarma başarısız: {e}{RESET}")
            continue
        elif user_input.lower() in ["/temizle", "/clear"]:
            chat_history = []
            print(f"{GREEN}>> Hafıza (Sohbet geçmişi) başarıyla temizlendi! Beyaz bir sayfa açtınız.{RESET}")
            continue
        elif user_input.lower() in ["/gecmis", "/history"]:
            print(f"\n{CYAN}" + "-"*20 + " SOHBET GEÇMİŞİ " + "-"*20 + f"{RESET}")
            if not chat_history:
                print(f"{YELLOW}Henüz bir geçmişiniz yok.{RESET}")
            else:
                for entry in chat_history:
                    if entry["role"] == "user":
                        print(f"{BOLD}{CYAN}Soru:{RESET} {entry['content']}")
                    else:
                        print(f"{BOLD}{GREEN}Yapay Zeka:{RESET} {entry['content']}")
                        print(f"{CYAN}" + "-"*40 + f"{RESET}")
            print(f"{CYAN}" + "-" * 56 + f"{RESET}")
            continue
        elif user_input.lower() in ["/hafiza", "/memory"]:
            print(f"\n{CYAN}" + "-"*20 + " AKTİF HAFIZA " + "-"*20 + f"{RESET}")
            if not memory_context:
                print(f"{YELLOW}Şu an hafızaya yüklenmiş herhangi bir .md dosyası bulunmuyor.{RESET}")
            else:
                print(f"{GREEN}{memory_context}{RESET}")
            print(f"{CYAN}" + "-" * 54 + f"{RESET}")
            continue
        elif user_input.lower() in ["/yenile", "/refresh"]:
            memory_context = load_memory()
            vectorstore = setup_rag(docs_dir="docs", force_refresh=True)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) if vectorstore else None
            print(f"{GREEN}>> Hafıza dosyaları ve RAG belleği başarıyla yeniden yüklendi!{RESET}")
            continue
        elif user_input.lower().startswith("/karakter"):
            print(f"\n{BOLD}{CYAN}--- KARAKTER SEÇİMİ ---{RESET}")
            print(f"  {GREEN}1){RESET} Varsayılan Asistan (Genel, Yardımsever)")
            print(f"  {GREEN}2){RESET} Siber Güvenlik Uzmanı (Analitik, Detaylı, Şüpheci)")
            print(f"  {GREEN}3){RESET} Yazılım Geliştirici (Kod odaklı, Net, Kısa)")
            print(f"  {GREEN}4){RESET} Samimi Dost (Günlük dilde konuşan, Samimi, Emojili)")
            secim = input(f"\nSeçiminiz (1-4): ").strip()
            karakterler = {
                "1": "Varsayılan Asistan",
                "2": "Siber Güvenlik Uzmanı",
                "3": "Yazılım Geliştirici",
                "4": "Samimi Dost"
            }
            if secim in karakterler:
                config["system_character"] = karakterler[secim]
                save_config(config)
                print(f"{GREEN}Karakter başarıyla '{karakterler[secim]}' olarak ayarlandı!{RESET}")
            else:
                print(f"{RED}Geçersiz seçim.{RESET}")
            continue
        elif user_input.lower().startswith("/kaydet"):
            parts = user_input.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else "gecmis.json"
            if not filename.endswith(".json"):
                filename += ".json"
            try:
                os.makedirs("chats", exist_ok=True)
                with open(os.path.join("chats", filename), "w", encoding="utf-8") as f:
                    json.dump(chat_history, f, ensure_ascii=False, indent=2)
                print(f"{GREEN}>> Sohbet geçmişi '{filename}' olarak kaydedildi!{RESET}")
            except Exception as e:
                print(f"{RED}Kaydetme hatası: {e}{RESET}")
            continue
        elif user_input.lower().startswith("/yukle"):
            parts = user_input.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else "gecmis.json"
            if not filename.endswith(".json"):
                filename += ".json"
            try:
                filepath = os.path.join("chats", filename)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        chat_history = json.load(f)
                    print(f"{GREEN}>> Sohbet geçmişi '{filename}' dosyasından hafızaya yüklendi!{RESET}")
                else:
                    print(f"{RED}HATA: '{filename}' bulunamadı.{RESET}")
            except Exception as e:
                print(f"{RED}Yükleme hatası: {e}{RESET}")
            continue
        elif user_input.lower().startswith("/cpuf-sifrele"):
            if not config.get("cyberpuf_enabled", False):
                print(f"{RED}Bu komutu kullanmak için ayarlardan CyberPUF modülünü aktif etmelisiniz.{RESET}")
                continue
                
            parts = user_input.split(" ", 1)
            model_path = parts[1] if len(parts) > 1 else ""
            if not model_path:
                print(f"{YELLOW}Kullanım: /cpuf-sifrele <h5_dosyasi_yolu>{RESET}")
                continue
                
            print(f"{YELLOW}RAM Çatışmasını önlemek için aktif LLM modeli geçici olarak siliniyor...{RESET}")
            del model
            del tokenizer
            gc.collect()
                
            print(f"{CYAN}CyberPUF LLM: Ağırlıklar {model_path} dosyasından şifreleniyor...{RESET}")
            import time
            try:
                time.sleep(1)
                print(f"{GREEN}>> Simülasyon: Model başarıyla şifrelendi ve .cpuf dosyası oluşturuldu.{RESET}")
            except Exception as e:
                print(f"{RED}Şifreleme hatası: {e}{RESET}")
                
            print(f"{YELLOW}LLM Modeli tekrar yükleniyor... Lütfen bekleyin.{RESET}")
            tokenizer, model = load_ai_model(model_id, core, device_target)
            if not tokenizer or not model:
                print(f"{RED}Model geri yüklenemedi. Çıkış yapılıyor.{RESET}")
                sys.exit(1)
            print(f"{GREEN}Model başarıyla geri yüklendi!{RESET}")
            continue
        elif user_input.lower().startswith("/hf-indir"):
            parts = user_input.split(" ", 1)
            hf_id = parts[1] if len(parts) > 1 else ""
            if not hf_id:
                print(f"{YELLOW}Kullanım: /hf-indir <huggingface_model_id>{RESET}")
                continue
                
            import re
            if not re.match(r'^[\w\-\.]+/[\w\-\.]+$', hf_id):
                print(f"{RED}[HATA] Geçersiz veya tehlikeli model ID formatı tespit edildi!{RESET}")
                continue
                
            print(f"{YELLOW}Mevcut RAM boşaltılıyor...{RESET}")
            try:
                del model
                del tokenizer
                gc.collect()
            except: pass
            
            from huggingface_hub import snapshot_download
            import tempfile
            import subprocess
            
            print(f"{CYAN}[HF] {hf_id} için Hugging Face'e bağlanılıyor...{RESET}")
            token = os.environ.get("HF_TOKEN")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"{GREEN}[HF] İndirme başlatılıyor... (İnternet hızınıza bağlıdır){RESET}")
                try:
                    snapshot_download(repo_id=hf_id, local_dir=temp_dir, token=token, ignore_patterns=["*.msgpack", "coreml/*"])
                    out_file = os.path.join("models", hf_id.replace("/", "_") + ".cpuf_llm")
                    os.makedirs("models", exist_ok=True)
                    print(f"{CYAN}[HF] İndirilen model stream olarak şifreleniyor: {out_file}{RESET}")
                    subprocess.run([sys.executable, "CyberPUF_LLM/llm_encryptor.py", temp_dir, out_file], check=True)
                    print(f"{GREEN}>> Başarılı: Model indirilip şifrelendi! (.cpuf_llm){RESET}")
                except Exception as e:
                    print(f"{RED}[HATA] HF İşlemi başarısız: {e}{RESET}")
            
            print(f"{YELLOW}Sistem tekrar yükleniyor...{RESET}")
            tokenizer, model = load_ai_model(model_id, core, device_target)
        elif user_input.lower() in ["/ayarlar", "/settings"]:
            settings_menu()
            continue
        elif user_input.lower() in ["/menu", "/ana-menu"]:
            print(f"\n{YELLOW}Ana menüye dönülüyor... Mevcut model RAM'den siliniyor.{RESET}")
            try:
                del model
                del tokenizer
                gc.collect()
            except: pass
            
            new_model_id = select_model()
            if new_model_id:
                model_id = new_model_id
                tokenizer, model = load_ai_model(model_id, core, device_target)
                if not tokenizer or not model:
                    print(f"{RED}Model yüklenemedi. Çıkış yapılıyor.{RESET}")
                    sys.exit(1)
                print(f"{GREEN}Menüden dönüldü! Kaldığınız yerden devam edebilirsiniz.{RESET}")
            continue
        elif user_input.lower().startswith("/calistir"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2:
                print(f"{YELLOW}Kullanım: /calistir <sistem_komutu>{RESET}")
                continue
            cmd = parts[1]
            print(f"\n{RED}{BOLD}DİKKAT: Aşağıdaki komutu çalıştırmak üzeresiniz:{RESET}\n{cmd}")
            onay = input(f"{YELLOW}Onaylıyor musunuz? [E/H]: {RESET}").strip().lower()
            if onay in ['e', 'evet']:
                print(f"{CYAN}Komut çalıştırılıyor...{RESET}")
                try:
                    out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
                    user_input = f"Aşağıdaki komutu çalıştırdım: `{cmd}`\n\nÇıktısı:\n```\n{out}\n```\nLütfen bu çıktıyı analiz et."
                except subprocess.CalledProcessError as e:
                    user_input = f"Aşağıdaki komutu çalıştırdım: `{cmd}`\n\nAncak hata verdi:\n```\n{e.output}\n```\nSence sorun ne?"
            else:
                print(f"{YELLOW}İşlem iptal edildi.{RESET}")
                continue
                
        elif user_input.lower().startswith("/debate") or user_input.lower().startswith("/tartisma"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2:
                print(f"{YELLOW}Kullanım: /debate <sorgu/konu>{RESET}")
                continue
            konu = parts[1]
            print(f"\n{CYAN}{BOLD}--- ÇOKLU AJAN TARTIŞMASI BAŞLIYOR ---{RESET}")
            print(f"{YELLOW}Konu: {konu}{RESET}")
            
            debate_visible = config.get("debate_visibility", True)
            
            # Ajan 1: Yazılım Uzmanı (Taslak oluşturur)
            ajan1_prompt = f"Sen bir Yazılım Geliştiricisin. Verilen konu hakkında çözüm veya kod taslağı üret. Konu: {konu}"
            if debate_visible: print(f"\n{MAGENTA}{BOLD}[Ajan 1 - Yazılımcı] düşünüyor...{RESET}")
            ajan1_inputs = tokenizer(ajan1_prompt, return_tensors="pt").to(device)
            ajan1_outputs = model.generate(**ajan1_inputs, max_new_tokens=config.get("max_tokens", 512), do_sample=True, temperature=0.7)
            ajan1_cevap = tokenizer.decode(ajan1_outputs[0][ajan1_inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
            if debate_visible: print(f"{MAGENTA}[Yazılımcı]:{RESET}\n{ajan1_cevap}")
            
            # Ajan 2: Güvenlik Uzmanı (Taslağı eleştirir ve güvenlik açıklarını bulur)
            ajan2_prompt = f"Sen bir Siber Güvenlik Uzmanısın. Yazılımcının şu çözümünü incele, güvenlik açıklarını veya zayıf noktalarını bul, güvenli bir öneri sun:\n\nYazılımcı Çözümü:\n{ajan1_cevap}\n\nDeğerlendirmen:"
            if debate_visible: print(f"\n{RED}{BOLD}[Ajan 2 - Güvenlik Uzmanı] inceliyor...{RESET}")
            ajan2_inputs = tokenizer(ajan2_prompt, return_tensors="pt").to(device)
            ajan2_outputs = model.generate(**ajan2_inputs, max_new_tokens=config.get("max_tokens", 512), do_sample=True, temperature=0.7)
            ajan2_cevap = tokenizer.decode(ajan2_outputs[0][ajan2_inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
            if debate_visible: print(f"{RED}[Güvenlik Uzmanı]:{RESET}\n{ajan2_cevap}")
            
            # Ajan 3: Karar Verici (Konsolide çözüm sunar)
            ajan3_prompt = f"Sen bir Teknik Lidersin. Konu: {konu}. Yazılımcı ve Güvenlik Uzmanı'nın görüşlerini birleştirerek nihai, güvenli ve en iyi çözümü sun:\n\nYazılımcı:\n{ajan1_cevap}\n\nGüvenlikçi:\n{ajan2_cevap}\n\nNihai Kararın:"
            if debate_visible: print(f"\n{GREEN}{BOLD}[Ajan 3 - Teknik Lider] nihai kararı veriyor...{RESET}")
            else: print(f"\n{GREEN}{BOLD}Ajanlar kendi aralarında tartışıyor, nihai sonuç bekleniyor...{RESET}")
            
            ajan3_inputs = tokenizer(ajan3_prompt, return_tensors="pt").to(device)
            ajan3_outputs = model.generate(**ajan3_inputs, max_new_tokens=config.get("max_tokens", 512), do_sample=True, temperature=0.7)
            ajan3_cevap = tokenizer.decode(ajan3_outputs[0][ajan3_inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
            print(f"\n{GREEN}[Nihai Sonuç]:{RESET}\n{ajan3_cevap}")
            
            chat_history.append({"role": "user", "content": f"Tartışma Konusu: {konu}"})
            chat_history.append({"role": "assistant", "content": f"Multi-Agent Nihai Kararı:\n{ajan3_cevap}"})
            print(f"{CYAN}" + "-"*80 + f"{RESET}")
            continue

        elif user_input.lower().startswith("/ara"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2:
                print(f"{YELLOW}Kullanım: /ara <sorgu>{RESET}")
                continue
            sorgu = parts[1]
            if DDGS is None:
                print(f"{RED}HATA: duckduckgo-search kütüphanesi yüklü değil.{RESET}")
                continue
            print(f"{CYAN}İnternette aranıyor: {sorgu}...{RESET}")
            try:
                results = DDGS().text(sorgu, max_results=3)
                search_text = "\n\n".join([f"Başlık: {r['title']}\nÖzet: {r['body']}\nLink: {r['href']}" for r in results])
                user_input = f"Kullanıcının Sorusu: {sorgu}\n\nİnternet Arama Sonuçları:\n{search_text}\n\nLütfen bu güncel bilgilere göre soruyu yanıtla."
            except Exception as e:
                print(f"{RED}Arama başarısız: {e}{RESET}")
                continue

        elif user_input.lower().startswith("/goster"):
            parts = user_input.split(" ", 2)
            if len(parts) < 2:
                print(f"{YELLOW}Kullanım: /goster <resim.png> <isteğe bağlı soru>{RESET}")
                continue
            img_path = parts[1]
            soru = parts[2] if len(parts) > 2 else "Bu resimde ne yazıyor?"
            if pytesseract is None or Image is None:
                print(f"{RED}HATA: pytesseract veya PIL yüklü değil.{RESET}")
                continue
            if not os.path.exists(img_path):
                print(f"{RED}HATA: Dosya bulunamadı: {img_path}{RESET}")
                continue
            print(f"{CYAN}Resim OCR ile analiz ediliyor...{RESET}")
            try:
                extracted_text = pytesseract.image_to_string(Image.open(img_path), lang='tur+eng')
                if not extracted_text.strip():
                    extracted_text = "(Okunabilir metin bulunamadı)"
                user_input = f"Bir resim yükledim. Sorum: {soru}\n\nResimden okunan metin:\n```\n{extracted_text}\n```\nLütfen analiz et."
            except Exception as e:
                print(f"{RED}OCR Analizi başarısız: {e}{RESET}")
                continue

        elif user_input.lower() == "/ses-dinle":
            if sr is None:
                print(f"{RED}HATA: SpeechRecognition kütüphanesi yüklü değil.{RESET}")
                continue
            recognizer = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    print(f"\n{BOLD}{GREEN}>>> Lütfen konuşun (Dinleniyor...) <<<{RESET}")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print(f"{CYAN}Ses işleniyor...{RESET}")
                user_input = recognizer.recognize_google(audio, language="tr-TR")
                print(f"{BOLD}{CYAN}Siz (Sesten):{RESET} {user_input}")
            except sr.WaitTimeoutError:
                print(f"{YELLOW}Zaman aşımı, ses algılanmadı.{RESET}")
                continue
            except sr.UnknownValueError:
                print(f"{YELLOW}Ses anlaşılamadı.{RESET}")
                continue
            except Exception as e:
                print(f"{RED}Mikrofon hatası (WSL kullanıyorsanız PulseAudio gerekebilir): {e}{RESET}")
                continue
        elif user_input.lower() in ["/yardim", "?", "help", "yardım"]:
            print(f"\n{CYAN}{BOLD}--- SOHBET KOMUTLARI YARDIM MENÜSÜ ---{RESET}")
            print(f"{YELLOW}/calistir <komut>:{RESET} Bilgisayarınızın terminalinde yerel komut (örn: dir, ls, python) çalıştırır ve çıktısını yapay zekaya yorumlatır.")
            print(f"{YELLOW}/ara <sorgu>:{RESET} DuckDuckGo üzerinden internette arama yapar ve güncel bilgileri yapay zekaya sunar.")
            print(f"{YELLOW}/goster <resim.png> <soru>:{RESET} Resimdeki yazıları ve kodları OCR ile okuyup modele iletir.")
            print(f"{YELLOW}/debate <konu>:{RESET} Çoklu Ajan (Yazılımcı + Güvenlikçi + Teknik Lider) sistemiyle bir konuyu tartışarak en güvenli kararı üretir.")
            print(f"{YELLOW}/ses-dinle:{RESET} Mikrofonunuzu açıp 5 saniye sesinizi dinler ve yapay zekaya yazar.")
            print(f"{YELLOW}/model:{RESET} Modeli RAM'den tamamen siler ve ana menüye dönüp başka bir model seçmenizi sağlar.")
            print(f"{YELLOW}/sistem:{RESET} CPU ve RAM tüketiminizi ekrana canlı yansıtır.")
            print(f"{YELLOW}/disa-aktar <rapor>:{RESET} O anki tüm sohbet geçmişinizi şık bir Markdown raporu olarak kaydeder.")
            print(f"{YELLOW}/kaydet ve /yukle:{RESET} Sohbet seansınızı JSON dosyasına kaydeder ve geri yükler.")
            print(f"{YELLOW}/karakter:{RESET} Yapay zekanın davranış tarzını (Siber Güvenlikçi, Yazılımcı, vb.) değiştirir.")
            print(f"{CYAN}" + "-"*60 + f"{RESET}")
            continue

        elif user_input.startswith("/"):
            print(f"{RED}HATA: Bilinmeyen komut '{user_input}'. Lütfen geçerli bir komut kullanın (örn: /temizle, /model, /ayarlar).{RESET}")
            continue
        elif not user_input:
            continue
            
        # --- Config'i her turda yenile (ayar değişiklikleri anında yansısın) ---
        config = load_config()

        context_str = ""
        if retriever:
            try:
                rag_docs = retriever.invoke(user_input)
                if rag_docs:
                    context_str = "\n".join([d.page_content for d in rag_docs])
            except Exception as e:
                print(f"{RED}[RAG Hatası] Belge araması başarısız: {e}{RESET}")

        # --- Sistem mesajını oluştur ---
        lang = config.get("language", "TR")
        if lang == "EN":
            karakter_plani = {
                "Varsayılan Asistan": "You are a helpful and polite AI assistant speaking in English.",
                "Siber Güvenlik Uzmanı": "You are a top-tier Cyber Security Expert. Be analytical, skeptical, and highly detailed. Focus on vulnerabilities.",
                "Yazılım Geliştirici": "You are an experienced Software Developer. Focus on code, be concise and clear. Do not provide unnecessary explanations.",
                "Samimi Dost": "You are the user's best friend. Speak in a very friendly, humorous, and daily tone. Use emojis."
            }
            mem_label = "[System Memory / Core Rules]"
            rag_label = "[Relevant RAG Documents]\nPlease answer the user's question using the following context information:"
        else:
            karakter_plani = {
                "Varsayılan Asistan": "Sen Türkçe konuşan yardımsever bir yapay zekasın.",
                "Siber Güvenlik Uzmanı": "Sen üst düzey bir Siber Güvenlik Uzmanısın. Yanıtlarında analitik, şüpheci ve detaylı ol. Güvenlik zafiyetlerine odaklan.",
                "Yazılım Geliştirici": "Sen tecrübeli bir Yazılım Geliştiricisin. Kod odaklı, net ve kısa cevaplar ver. Gereksiz açıklamalar yapma.",
                "Samimi Dost": "Sen kullanıcının en yakın arkadaşısın. Çok samimi, esprili ve günlük bir dille konuş. Emojiler kullan."
            }
            mem_label = "[Sistem Hafızası / Ana Kurallar]"
            rag_label = "[İlgili RAG Belgeleri]\nLütfen aşağıdaki bağlam bilgilerini kullanarak kullanıcının sorusunu cevapla:"

        secili_karakter = config.get("system_character", "Varsayılan Asistan")
        system_content = karakter_plani.get(secili_karakter, karakter_plani["Varsayılan Asistan"])
        
        if memory_context:
            system_content += f"\n\n{mem_label}\n{memory_context}"
        if context_str:
            system_content += f"\n{rag_label}\n{context_str}"

        # --- Mesaj listesini oluştur (tüm modeller için evrensel) ---
        messages = [{"role": "system", "content": system_content}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_input})

        # --- Prompt'u tokenizer'ın kendi şablonuyla oluştur ---
        try:
            if hasattr(tokenizer, 'chat_template') and tokenizer.chat_template:
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                # Fallback: chat_template yoksa basit format
                prompt = f"System: {system_content}\n"
                for msg in chat_history:
                    if msg["role"] == "user":
                        prompt += f"User: {msg['content']}\n"
                    else:
                        prompt += f"Assistant: {msg['content']}\n"
                prompt += f"User: {user_input}\nAssistant:"

            inputs = tokenizer(prompt, return_tensors="pt")
        except Exception as e:
            print(f"\n{RED}[HATA] Prompt oluşturulamadı: {e}{RESET}")
            continue

        prompt_tokens = inputs.input_ids.shape[1]
        max_context = 4096

        # --- Prompt çok uzunsa eski geçmişi kırp ---
        while prompt_tokens > (max_context - config.get("max_tokens", 512)) and len(chat_history) > 0:
            chat_history.pop(0)  # En eski mesajı sil
            # Mesajları tekrar oluştur
            messages = [{"role": "system", "content": system_content}]
            messages.extend(chat_history)
            messages.append({"role": "user", "content": user_input})
            try:
                if hasattr(tokenizer, 'chat_template') and tokenizer.chat_template:
                    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                else:
                    prompt = f"System: {system_content}\nUser: {user_input}\nAssistant:"
                inputs = tokenizer(prompt, return_tensors="pt")
                prompt_tokens = inputs.input_ids.shape[1]
            except:
                break

        token_pct = min((prompt_tokens / max_context) * 100, 100.0)

        def draw_mini_bar(pct, length=15):
            filled = int(length * pct / 100)
            return "█" * filled + "░" * (length - filled)

        bar_color = GREEN if token_pct < 60 else (YELLOW if token_pct < 85 else RED)
        print(f"\n{bar_color}[Hafıza Doluluğu: {draw_mini_bar(token_pct)} %{int(token_pct)} | {prompt_tokens}/{max_context} Token]{RESET}")

        # --- Çıkarım (Inference) - Animasyonlu ve korumalı ---
        import threading
        import sys
        from transformers.generation.streamers import BaseStreamer
        
        try:
            temp_val = config.get("temperature", 0.7)
            
            class CustomStreamer(BaseStreamer):
                def __init__(self, tokenizer):
                    super().__init__()
                    self.tokenizer = tokenizer
                    self.is_first_token = True
                    self.next_tokens_are_prompt = True
                    self.token_cache = []
                    self.print_len = 0
            
                def put(self, value):
                    if len(value.shape) > 1 and value.shape[0] > 1:
                        value = value[0]
                    elif len(value.shape) > 1:
                        value = value[0]
                        
                    # Prompt'un ekrana sızmasını (echo) engelle
                    if self.next_tokens_are_prompt:
                        self.next_tokens_are_prompt = False
                        return
                        
                    self.token_cache.extend(value.tolist())
                    text = self.tokenizer.decode(self.token_cache, skip_special_tokens=True)
                    if text:
                        with print_lock:
                            if self.is_first_token:
                                # İlk gerçek token geldi, animasyon satırını temizle ve Yapay Zeka başlığını at
                                sys.stdout.write("\r\033[K")
                                sys.stdout.write(f"{BOLD}{GREEN}{loc['ai_name']}{RESET}\n")
                                self.is_first_token = False
                            
                            # Sadece yeni gelen metin kısmını ekrana yazdır
                            new_text = text[self.print_len:]
                            if new_text:
                                sys.stdout.write(new_text)
                                sys.stdout.flush()
                                self.print_len = len(text)
            
                def end(self):
                    pass

            streamer = CustomStreamer(tokenizer)
            
            class GenerateThread(threading.Thread):
                def __init__(self):
                    super().__init__()
                    self.result = None
                    self.error = None
                def run(self):
                    try:
                        self.result = model.generate(
                            **inputs,
                            max_new_tokens=config.get("max_tokens", 512),
                            temperature=temp_val,
                            do_sample=True if temp_val > 0 else False,
                            pad_token_id=tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 0,
                            streamer=streamer
                        )
                    except Exception as e:
                        self.error = e

            gen_thread = GenerateThread()
            gen_thread.start()

            animation = ["[■□□□□□□□□□]", "[■■□□□□□□□□]", "[■■■□□□□□□□]", "[■■■■□□□□□□]", "[■■■■■□□□□□]", 
                         "[■■■■■■□□□□]", "[■■■■■■■□□□]", "[■■■■■■■■□□]", "[■■■■■■■■■□]", "[■■■■■■■■■■]"]
            idx = 0
            start_time = time.time()
            
            while gen_thread.is_alive():
                # Sadece ilk kelime/token gelene kadar animasyonu göster
                if streamer.is_first_token:
                    with print_lock:
                        sys.stdout.write(f"\r{BOLD}{YELLOW}{loc['generating']} {CYAN}{animation[idx % len(animation)]}{RESET}")
                        sys.stdout.flush()
                else:
                    elapsed = time.time() - start_time
                    tokens = len(streamer.token_cache)
                    tps = tokens / elapsed if elapsed > 0 else 0
                    cpu_pct = psutil.cpu_percent()
                    ram_pct = psutil.virtual_memory().percent
                    
                    hud = f"{CYAN}[HUD]{RESET} {BOLD}CPU:{RESET} %{cpu_pct} | {BOLD}RAM:{RESET} %{ram_pct} | {BOLD}Hız:{RESET} {tps:.1f} T/s | {BOLD}Token:{RESET} {tokens}"
                    with print_lock:
                        sys.stdout.write(f"\033[s\033[999;1H\033[K{hud}\033[u")
                        sys.stdout.flush()
                    
                idx += 1
                time.sleep(0.1)

            # HUD Temizleme
            with print_lock:
                sys.stdout.write("\033[s\033[999;1H\033[K\033[u")
                sys.stdout.flush()

            if gen_thread.error:
                raise gen_thread.error
                
            outputs = gen_thread.result
            
            # Eğer yanıt bomboş döndüyse is_first_token hala True kalmıştır, onu kontrol et
            if streamer.is_first_token:
                sys.stdout.write("\r\033[K")
                sys.stdout.flush()

            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            response = response.strip()
        except Exception as e:
            print(f"\n{RED}[HATA] Model yanıt üretemedi: {e}{RESET}")
            print(f"{YELLOW}İpucu: Bellek yetersiz olabilir. /temizle komutu ile geçmişi sıfırlayın veya daha küçük bir model deneyin.{RESET}")
            continue

        if not response:
            print(f"\r{YELLOW}Yapay Zeka: (Boş yanıt üretildi, tekrar deneyin){RESET}")
            continue

        print(f"\n{CYAN}" + "-"*80 + f"{RESET}")
        
        if config.get("voice_feedback_enabled", False) and pyttsx3 is not None:
            try:
                engine = pyttsx3.init()
                engine.say(response)
                engine.runAndWait()
            except Exception as e:
                print(f"{RED}[TTS Hatası] Ses çalınamadı: {e}{RESET}")

        # Geçmişe evrensel formatta ekle (dict olarak)
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": response})

        # Dosyaya Markdown olarak kaydet
        try:
            with open("chats/sohbet_gecmisi.md", "a", encoding="utf-8") as f:
                f.write(f"## Soru:\n{user_input}\n\n")
                f.write(f"## Yapay Zeka:\n{response}\n\n---\n")
        except:
            pass

        while len(chat_history) > MAX_HISTORY_TURNS:
            chat_history.pop(0)
