#!/bin/bash

# Proje dizinine geçiş yap
cd /home/ardam/underw_framework

# Sanal ortamı (ai_env) aktif et
source ai_env/bin/activate

# Uygulamayı başlat
underw start
