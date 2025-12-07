from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django import forms
from .models import Article, Category, SocialQueue  # Убедись, что SocialQueue импортирована
import requests
import os
import csv
import json
import random
import uuid
import time
from django.conf import settings
from threading import Thread
from django.utils.text import slugify
from io import BytesIO
from PIL import Image

# === НАСТРОЙКИ ЛОКАЛЬНОЙ НЕЙРОСЕТИ ===
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3:8b" # Или qwen2.5:14b, что у тебя будет стоять
COMFYUI_URL = "http://127.0.0.1:8188/prompt" # Адрес ComfyUI
# ======================================

STOP_FLAG = os.path.join(settings.BASE_DIR, 'STOP_GENERATION')
PROGRESS_FILE = os.path.join(settings.BASE_DIR, 'GENERATION_PROGRESS')

class GenerateForm(forms.Form):
    articles_count = forms.IntegerField(initial=50, label="Сколько СТАТЕЙ генерировать")
    posts_count = forms.IntegerField(initial=10, label="Сколько СОЦ-ПОСТОВ генерировать")

# --- 1. ФУНКЦИИ ГЕНЕРАЦИИ ТЕКСТА (OLLAMA) ---

def ask_ollama(prompt, system_prompt="You are a helpful AI assistant."):
    """Универсальная функция запроса к локальной LLM"""
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    try:
        resp = requests.post(OLLAMA_URL, json=data, timeout=120)
        if resp.status_code == 200:
            return resp.json()['response']
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
    return None

def generate_image_prompt(topic, style="cinematic"):
    """Просит LLM придумать описание картинки для Stable Diffusion"""
    system = "You are an expert prompt engineer for Stable Diffusion XL."
    prompt = f"""
    Ты — профессиональный фотограф и AI-художник. Твоя задача — превращать короткие темы в детальные промпты для Stable Diffusion.

Всегда следуй структуре:
[Subject], [Action/Context], [Art Style], [Lighting], [Color Palette], [Camera details].

Пример:
Input: "Morning coffee"
Output: "Close-up shot of a steaming ceramic cup of coffee on a rustic wooden table, sunrise light streaming through a window, golden hour, cinematic lighting, shallow depth of field, bokeh, 8k resolution, hyperrealistic, cozy atmosphere."

Никогда не пиши "Here is the prompt". Пиши только сам промпт.
    """
    return ask_ollama(prompt, system)

def generate_social_content():
    """Генерирует тему и текст для короткого поста"""
    topics = [
        "Morning motivation for healthy life",
        "Quick tip for better sleep",
        "Why water is important",
        "Mental health minute",
        "Stretching exercise of the day"
    ]
    topic = random.choice(topics)
    
    system = "You are a social media influencer in the health niche."
    prompt = f"""Write a short, engaging social media post (max 280 chars) about: {topic}.
    Include 2-3 emojis and hashtags. Do not use markdown."""
    
    text = ask_ollama(prompt, system)
    return topic, text

# --- 2. ФУНКЦИИ ГЕНЕРАЦИИ КАРТИНОК (COMFYUI) ---

def generate_local_image(positive_prompt, filename):
    """Отправляет запрос в локальный ComfyUI"""
    # Это упрощенный JSON workflow для ComfyUI. 
    # В реальности тебе нужно будет скопировать API Format из своего ComfyUI.
    # Для примера я использую базовую структуру.
    
    # ВАЖНО: Это плейсхолдер! Тебе нужно будет вставить сюда свой Workflow JSON
    # Я покажу как это сделать отдельно.
    print(f"🎨 Генерирую картинку: {positive_prompt[:50]}...")
    
    # Эмуляция ожидания (пока нет реального ComfyUI)
    time.sleep(2) 
    
    # ВМЕСТО ЭТОГО БЛОКА БУДЕТ ЗАПРОС К COMFYUI
    # Пока используем заглушку или старый метод, если ComfyUI не настроен
    return None 

# --- 3. ГЛАВНАЯ ЛОГИКА ---

def worker_generate_content(articles_count, posts_count):
    # 1. ГЕНЕРАЦИЯ СТАТЕЙ (Из CSV)
    csv_path = os.path.join(settings.BASE_DIR, 'keywords.csv')
    if os.path.exists(csv_path) and articles_count > 0:
        with open(csv_path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))[:articles_count]
            for row in rows:
                if os.path.exists(STOP_FLAG): break
                
                keyword = row['keyword']
                
                # A. Генерируем промпт для картинки
                img_prompt = generate_image_prompt(keyword)
                
                # B. Генерируем Текст Статьи
                html = ask_ollama(f"Write a detailed article about {keyword}...", system_prompt="Expert Writer")
                
                # C. Генерируем (или качаем) картинку
                # generate_local_image(img_prompt, f"{slugify(keyword)}.jpg")
                # Пока старая логика для теста:
                # ... (код скачивания картинки) ...

                # D. Сохраняем и отправляем
                cat, _ = Category.objects.get_or_create(name=row['category'])
                
                # Тут вызов твоей функции upload_article_to_remote...
                print(f"✅ Статья '{keyword}' обработана.")

    # 2. ГЕНЕРАЦИЯ СОЦ-ПОСТОВ (Случайные)
    for i in range(posts_count):
        if os.path.exists(STOP_FLAG): break
        
        topic, text = generate_social_content()
        img_prompt = generate_image_prompt(f"{topic}, bright, happy, morning vibe")
        
        print(f"📱 Пост {i+1}: {topic}")
        
        # Загружаем на сервер как Article, но с типом POST
        # upload_article_to_remote(..., content=text, content_type='POST')

def generate_articles_view(request):
    # ... (стандартный view код) ...
    if request.method == 'POST':
        form = GenerateForm(request.POST)
        if form.is_valid():
            a_count = form.cleaned_data['articles_count']
            p_count = form.cleaned_data['posts_count']
            Thread(target=worker_generate_content, args=(a_count, p_count)).start()
            return redirect('/generate/')
    # ...
    return render(request, 'generate_form.html', {'form': form})


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # Добавили content_type и promote_to_socials в таблицу
    list_display = ('title', 'category', 'content_type', 'created_at', 'published', 'promote_to_socials')
    
    # Фильтры справа (очень удобно)
    list_filter = ('published', 'content_type', 'promote_to_socials', 'category', 'created_at')
    
    # Поиск по заголовку
    search_fields = ('title', 'content')
    
    # Автозаполнение слага
    prepopulated_fields = {"slug": ("title",)}
    
    # Поля, которые можно редактировать, не заходя внутрь статьи
    list_editable = ('published', 'promote_to_socials')

@admin.register(SocialQueue)
class SocialQueueAdmin(admin.ModelAdmin):
    list_display = ('platform', 'article', 'scheduled_time', 'is_sent')
    list_filter = ('platform', 'is_sent', 'scheduled_time')
    ordering = ('-scheduled_time',)