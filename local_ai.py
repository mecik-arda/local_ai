import os
import glob
import sys
import time
import signal
import warnings
import gc
import psutil

import json
from dotenv import load_dotenv
load_dotenv()
cpuf_process = None

warnings.filterwarnings("ignore")
from transformers import AutoTokenizer
from optimum.intel import OVModelForCausalLM
import openvino as ov

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

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
    "device": "AUTO",
    "max_tokens": 512,
    "temperature": 0.7,
    "privacy_mode": False,
    "cyberpuf_enabled": False
}

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
        clear_screen()
        print_header()
        print(f"\n{BOLD}{CYAN}" + "="*50)
        print("AYARLAR MENÜSÜ")
        print("="*50 + f"{RESET}")
        print(f"  {GREEN}1){RESET} Hedef Cihaz (Şu anki: {config.get('device', 'AUTO')})")
        print(f"  {GREEN}2){RESET} Maksimum Cevap Uzunluğu (Şu anki: {config.get('max_tokens', 512)} token)")
        print(f"  {GREEN}3){RESET} Model Yaratıcılığı/Sıcaklık (Şu anki: {config.get('temperature', 0.7)})")
        print(f"  {GREEN}4){RESET} Gizlilik Modu (Şu anki: {'AÇIK' if config.get('privacy_mode', False) else 'KAPALI'})")
        print(f"  {GREEN}5){RESET} CyberPUF LLM Modülü (Şu anki: {'AÇIK' if config.get('cyberpuf_enabled', False) else 'KAPALI'})")
        print(f"  {GREEN}6){RESET} Ayarları Sıfırla")
        print(f"  {GREEN}7){RESET} Kaydet ve Geri Dön")
        print(f"{CYAN}{BOLD}" + "="*50 + f"{RESET}")
        
        secim = input(f"\n{BOLD}Seçiminiz (1/2/3/4/5/6/7): {RESET}").strip()
        
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
            config = DEFAULT_CONFIG.copy()
            save_config(config)
            print(f"{GREEN}Ayarlar varsayılana sıfırlandı.{RESET}")
            time.sleep(1)
        elif secim == "7":
            break
        else:
            print(f"{RED}Geçersiz seçim.{RESET}")
            time.sleep(1)

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
        return "\n\n".join(memory_texts)
    return ""

def setup_rag(docs_dir="docs"):
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
    
    print("[RAG] Vektör veritabanı oluşturuluyor (Bu işlem ilk seferde biraz sürebilir)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    print(f"[RAG] Sistem {len(docs)} sayfa belgeyi ve {len(splits)} parçayı başarıyla hafızaya aldı!\n")
    return vectorstore

def select_model():
    config = load_config()
    while True:
        clear_screen()
        print_header()
        
        print(f"\n{BOLD}{YELLOW}KATEGORİLER:{RESET}")
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
        kategori = input(f"\n{BOLD}Lütfen bir kategori seçin ({opts}): {RESET}").strip()
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
        model = OVModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            device=device_target
        )
        return tokenizer, model
    except Exception as e:
        print(f"\nHATA: Model yüklenemedi. Lütfen boş diskinizi ve internetinizi kontrol edin. ({e})")
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
    print(f"{YELLOW}Sohbet Komutları:{RESET} Çıkış: {BOLD}exit{RESET} | Anlık Hafıza Sıfırla: {BOLD}/temizle{RESET} | Terminal Geçmişi: {BOLD}/gecmis{RESET}")
    print(f"{YELLOW}Sistem Komutları:{RESET} Model Değiştir: {BOLD}/model{RESET} | Sistem Kaynakları: {BOLD}/sistem{RESET} | Dışa Aktar: {BOLD}/disa-aktar rapor.md{RESET} | HF İndir: {BOLD}/hf-indir repo_id{RESET}")
    print(f"{YELLOW}Hafıza Komutları:{RESET} Hafızayı Gör: {BOLD}/hafiza{RESET} | Hafızayı Yenile: {BOLD}/yenile{RESET}")
    print(f"{CYAN}" + "="*80 + f"{RESET}")

    chat_history = []
    MAX_HISTORY_TURNS = 5
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
        user_input = input(f"\n{BOLD}{CYAN}Soru:{RESET} ").strip()
        
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
                        entry_clean = entry.replace("<|user|>\n", "## Soru:\n").replace("<|end|>\n<|assistant|>\n", "\n\n## Yapay Zeka:\n").replace("<|end|>\n", "\n\n---\n")
                        f.write(entry_clean)
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
                print("".join(chat_history))
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
            print(f"{GREEN}>> Hafıza dosyaları başarıyla yeniden yüklendi!{RESET}")
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
            continue
        elif not user_input:
            continue
            
        context_str = ""
        if retriever:
            docs = retriever.invoke(user_input)
            if docs:
                context_str = "\n".join([d.page_content for d in docs])
                
        system_prompt = "<|system|>\nSen Türkçe konuşan yardımsever bir yapay zekasın."
        if memory_context:
            system_prompt += f"\n\n[Sistem Hafızası / Ana Kurallar]\n{memory_context}\n"
        if context_str:
            system_prompt += f"\n[İlgili RAG Belgeleri]\nLütfen aşağıdaki bağlam bilgilerini kullanarak kullanıcının sorusunu cevapla:\n{context_str}"
        system_prompt += "<|end|>\n"
        
        history_str = "".join(chat_history)
        current_turn = f"<|user|>\n{user_input}<|end|>\n<|assistant|>\n"
        
        prompt = system_prompt + history_str + current_turn
        
        inputs = tokenizer(prompt, return_tensors="pt")
        
        prompt_tokens = inputs.input_ids.shape[1]
        max_context = 4096
        token_pct = min((prompt_tokens / max_context) * 100, 100.0)
        
        def draw_mini_bar(pct, length=15):
            filled = int(length * pct / 100)
            return "█" * filled + "░" * (length - filled)
        
        bar_color = GREEN if token_pct < 60 else (YELLOW if token_pct < 85 else RED)
        print(f"\n{bar_color}[Hafıza Doluluğu: {draw_mini_bar(token_pct)} %{int(token_pct)} | {prompt_tokens}/{max_context} Token]{RESET}")
        
        print(f"{BOLD}{YELLOW}Cevap üretiliyor...{RESET}", end="", flush=True)
        
        temp_val = config.get("temperature", 0.7)
        outputs = model.generate(
            **inputs,
            max_new_tokens=config.get("max_tokens", 512),
            temperature=temp_val,
            do_sample=True if temp_val > 0 else False,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        response = response.strip()
        print(f"\r{BOLD}{GREEN}Yapay Zeka:{RESET}\n{response}")
        print(f"{CYAN}" + "-"*80 + f"{RESET}")
        
        chat_history.append(f"<|user|>\n{user_input}<|end|>\n<|assistant|>\n{response}<|end|>\n")
        
        # Dosyaya Markdown olarak kaydet
        try:
            with open("chats/sohbet_gecmisi.md", "a", encoding="utf-8") as f:
                f.write(f"## Soru:\n{user_input}\n\n")
                f.write(f"## Yapay Zeka:\n{response}\n\n---\n")
        except:
            pass

        if len(chat_history) > MAX_HISTORY_TURNS:
            chat_history.pop(0)
