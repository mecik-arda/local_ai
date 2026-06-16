import os
import sys

# İndirme çubuklarının logları kirletmemesi için devre dışı bırakıyoruz
# İstenirse terminalde çalıştırılırken silinebilir
# os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from huggingface_hub import snapshot_download

models = [
    "OpenVINO/DeepSeek-R1-Distill-Qwen-7B-nf4-ov",
    "OpenVINO/Mistral-7B-Instruct-v0.3-int4-ov",
    "OpenVINO/Qwen2.5-14B-Instruct-int4-ov",
    "OpenVINO/Qwen2.5-7B-Instruct-int4-ov",
    "OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov",
    "OpenVINO/Phi-3-mini-4k-instruct-int4-ov"
]

print("="*60)
print("GÜVENLİ VE RESMİ OPENVINO MODELLERİ İNDİRİLİYOR")
print("="*60)
print("Bu işlem internet hızınıza bağlı olarak zaman alabilir (Toplam ~25-30 GB).")

for i, model_id in enumerate(models, 1):
    print(f"\n[{i}/{len(models)}] {model_id} indiriliyor...")
    try:
        snapshot_download(repo_id=model_id)
        print(f"Başarılı: {model_id} tamamlandı.")
    except Exception as e:
        print(f"HATA: {model_id} indirilirken sorun oluştu - {e}")

print("\nTüm modellerin indirme kontrolü tamamlandı!")
