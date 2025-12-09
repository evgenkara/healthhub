# blog/ai/generators.py
import requests
import json
import random
import time
import os
import subprocess
import shutil
from django.conf import settings

# === НАСТРОЙКИ ===
OLLAMA_BASE_URL = "http://127.0.0.1:11434/api"
OLLAMA_GENERATE = f"{OLLAMA_BASE_URL}/generate"

# Твоя модель (проверь ollama list)
TEXT_MODEL = "qwen3:14b-q4_k_m"  

# ComfyUI
COMFY_HOST = "http://127.0.0.1:8188"
COMFY_PROMPT = f"{COMFY_HOST}/prompt"

# Пути
USER_HOME = os.path.expanduser("~") 
COMFY_DIR = os.path.join(USER_HOME, "ComfyUI")
COMFY_OUTPUT_DIR = os.path.join(COMFY_DIR, "output")
# Путь к Python внутри venv ComfyUI (важно для запуска)
COMFY_PYTHON = os.path.join(COMFY_DIR, "venv", "bin", "python")
COMFY_MAIN = os.path.join(COMFY_DIR, "main.py")
# =================

def kill_comfy():
    """Жестко убивает процесс ComfyUI, освобождая 100% VRAM"""
    print("🛑 [System] Убиваю процесс ComfyUI...")
    try:
        # fuser -k 8188/tcp убивает любой процесс, занимающий порт 8188
        os.system("fuser -k 8188/tcp > /dev/null 2>&1")
        time.sleep(5) # Даем время на закрытие
    except Exception as e:
        print(f"⚠️ Ошибка при убийстве процесса: {e}")

def start_comfy():
    """Запускает ComfyUI и ждет, пока он поднимется"""
    # Сначала проверяем, вдруг он уже работает
    try:
        requests.get(COMFY_HOST, timeout=1)
        print("ℹ️ ComfyUI уже запущен.")
        return True
    except:
        pass

    print("🚀 [System] Запускаю ComfyUI с нуля...")
    
    if not os.path.exists(COMFY_PYTHON):
        print(f"❌ ОШИБКА: Не найден Python виртуального окружения: {COMFY_PYTHON}")
        return False

    # Запускаем в отдельном процессе
    # --normalvram балансирует память, --preview-method auto ускоряет
    try:
        subprocess.Popen(
            [COMFY_PYTHON, COMFY_MAIN, "--normalvram"], 
            cwd=COMFY_DIR,
            stdout=subprocess.DEVNULL, # Скрываем лишний мусор в логах
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"❌ Не удалось запустить процесс: {e}")
        return False

    # Ждем, пока сервер ответит (пинг)
    print("⏳ Ожидание загрузки сервера ComfyUI...")
    for _ in range(30): # Ждем до 30 секунд
        try:
            requests.get(COMFY_HOST, timeout=1)
            print("✅ ComfyUI готов к работе!")
            time.sleep(2) # Еще чуть-чуть на инициализацию
            return True
        except:
            time.sleep(1)
    
    print("❌ Тайм-аут: ComfyUI не запустился за 30 секунд.")
    return False

def unload_ollama():
    """Выгружает модель Ollama через API"""
    print(f"🧹 [VRAM] Выгружаю Ollama...")
    try:
        requests.post(OLLAMA_GENERATE, json={
            "model": TEXT_MODEL,
            "keep_alive": 0
        }, timeout=5)
    except:
        pass

# --- ГЛАВНЫЕ ФУНКЦИИ ---

def ask_ollama(prompt, system_prompt):
    # 1. ПЕРЕД ТЕКСТОМ: Убиваем ComfyUI, чтобы освободить ВСЮ память
    kill_comfy()
    time.sleep(1) 

    payload = {
        "model": TEXT_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_ctx": 4096 
        },
        "keep_alive": "5m" 
    }
    try:
        print(f"📝 [Ollama] Пишу текст...")
        resp = requests.post(OLLAMA_GENERATE, json=payload, timeout=1200)
        
        if resp.status_code == 200:
            return resp.json()['response'].strip()
        else:
            print(f"❌ Ошибка API Ollama: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка соединения с Ollama: {e}")
        return None

def generate_image_comfy(prompt_text, output_filename):
    # 1. ПЕРЕД КАРТИНКОЙ: Выгружаем Ollama
    unload_ollama()
    time.sleep(2)

    # 2. ЗАПУСКАЕМ ComfyUI (если он был убит)
    if not start_comfy():
        return None

    # 3. Загружаем Workflow
    workflow_path = os.path.join(settings.BASE_DIR, 'comfy_workflow.json')
    if not os.path.exists(workflow_path):
        print("⚠️ Нет файла comfy_workflow.json!")
        return None

    with open(workflow_path, 'r') as f:
        prompt_data = json.load(f)

    try:
        # Поиск ID узлов
        text_node_id = None
        seed_node_id = None

        for key, value in prompt_data.items():
            if value.get("class_type") == "CLIPTextEncode" and "inputs" in value:
                # Ищем позитивный промпт
                if text_node_id is None: text_node_id = key
            
            if value.get("class_type") in ["KSampler", "SamplerCustom"]:
                seed_node_id = key

        # Дефолтные ID (на случай если автопоиск не сработал)
        if not text_node_id: text_node_id = "6"
        if not seed_node_id: seed_node_id = "3"

        # Подстановка
        if text_node_id in prompt_data:
            prompt_data[text_node_id]["inputs"]["text"] = prompt_text
        
        # Новый сид
        new_seed = random.randint(1, 1000000000000)
        if seed_node_id in prompt_data:
            inputs = prompt_data[seed_node_id]["inputs"]
            if "seed" in inputs: inputs["seed"] = new_seed
            elif "noise_seed" in inputs: inputs["noise_seed"] = new_seed

        # 4. Отправка
        print(f"🎨 [ComfyUI] Генерирую картинку...")
        requests.post(COMFY_PROMPT, json={"prompt": prompt_data})
        
        # 5. Ожидание
        print(f"⏳ Жду результат...")
        start_time = time.time()
        
        while time.time() - start_time < 240: # Ждем до 4 минут (на холодный старт)
            time.sleep(2)
            fresh_files = []
            if os.path.exists(COMFY_OUTPUT_DIR):
                for f in os.listdir(COMFY_OUTPUT_DIR):
                    if f.endswith(('.png', '.jpg', '.jpeg')):
                        full_path = os.path.join(COMFY_OUTPUT_DIR, f)
                        if os.path.getmtime(full_path) > start_time:
                            fresh_files.append(full_path)
            
            if not fresh_files: continue

            newest_file = max(fresh_files, key=os.path.getmtime)
            print(f"✅ Картинка готова: {os.path.basename(newest_file)}")
            
            target_dir = os.path.join(settings.MEDIA_ROOT, 'articles')
            os.makedirs(target_dir, exist_ok=True)
            
            final_path = os.path.join(target_dir, output_filename)
            shutil.move(newest_file, final_path)
            
            # === ФИНАЛЬНЫЙ ШТРИХ: Убиваем ComfyUI после работы ===
            # Это гарантирует, что к следующему циклу память будет чиста для Ollama
            kill_comfy()
            
            return os.path.join('articles', output_filename)
        
        print("❌ Тайм-аут генерации.")
        kill_comfy() # Убиваем даже при ошибке
        return None

    except Exception as e:
        print(f"❌ Ошибка в generate_image_comfy: {e}")
        kill_comfy()
        return None