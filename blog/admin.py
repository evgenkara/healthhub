from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django import forms
from .models import Article, Category, SocialQueue
import os
import csv
from django.conf import settings
from threading import Thread
from django.utils.text import slugify

# === ВАЖНО: ИМПОРТИРУЕМ ЛОГИКУ ИЗ ВАШЕГО МОДУЛЯ ===
# Убедитесь, что файлы blog/ai/generators.py и blog/ai/prompts.py существуют
from blog.ai.generators import ask_ollama, generate_image_comfy
from blog.ai.prompts import get_article_system_prompt, get_image_prompt_generator_prompt, get_social_system_prompt

STOP_FLAG = os.path.join(settings.BASE_DIR, 'STOP_GENERATION')
PROGRESS_FILE = os.path.join(settings.BASE_DIR, 'GENERATION_PROGRESS')

class GenerateForm(forms.Form):
    articles_count = forms.IntegerField(
        min_value=0, max_value=100, initial=1, 
        label="Статьи (из CSV)",
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent'})
    )
    posts_count = forms.IntegerField(
        min_value=0, max_value=20, initial=0, 
        label="Соц-посты (случайные темы)",
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent'})
    )

# --- ГЛАВНАЯ ЛОГИКА ---

def worker_generate_content(articles_count, posts_count):
    # 1. ГЕНЕРАЦИЯ СТАТЕЙ (Из CSV)
    csv_path = os.path.join(settings.BASE_DIR, 'keywords.csv')
    
    # Создаем папку для картинок
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'articles'), exist_ok=True)

    if os.path.exists(csv_path) and articles_count > 0:
        with open(csv_path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            # Берем первые N записей
            targets = rows[:articles_count] 
            
            for row in targets:
                if os.path.exists(STOP_FLAG): break
                
                keyword = row['keyword'].strip()
                category_name = row['category'].strip()
                
                print(f"⚙️ [Статья] Работаю над: {keyword}")

                # A. Генерация промпта для картинки
                try:
                    img_prompt_text = ask_ollama(keyword, get_image_prompt_generator_prompt())
                except:
                    img_prompt_text = f"Professional photo of {keyword}, high quality, 4k"

                # B. Генерация Текста Статьи
                html = ask_ollama(f"Write a detailed article about {keyword}. Output HTML.", get_article_system_prompt())
                
                if not html:
                    print(f"❌ Ошибка генерации текста для {keyword}")
                    continue

                # C. Генерация Картинки (ComfyUI)
                # Вызываем ПРАВИЛЬНУЮ функцию из generators.py
                img_filename = f"{slugify(keyword)}.png"
                img_path_rel = generate_image_comfy(img_prompt_text, img_filename)

                # D. Сохранение в БД
                try:
                    category, _ = Category.objects.get_or_create(name=category_name)
                    
                    article, created = Article.objects.update_or_create(
                        title=keyword,
                        defaults={
                            'content': html,
                            'category': category,
                            'content_type': 'ARTICLE',
                            'published': True,
                            'featured_image': img_path_rel # Путь к картинке (или None)
                        }
                    )
                    print(f"✅ Статья '{keyword}' успешно сохранена!")
                except Exception as e:
                    print(f"❌ Ошибка сохранения в БД: {e}")

    # 2. ГЕНЕРАЦИЯ СОЦ-ПОСТОВ
    import random
    topics = ["Healthy Morning", "Better Sleep", "Hydration", "Mindfulness", "Walking Benefits"]
    
    for i in range(posts_count):
        if os.path.exists(STOP_FLAG): break
        
        topic = random.choice(topics)
        print(f"📱 [Пост] Генерирую: {topic}")
        
        try:
            # Текст поста
            post_content = ask_ollama(f"Write a short post about {topic}", get_social_system_prompt('TG'))
            
            # Картинка поста
            img_prompt = ask_ollama(f"{topic}, minimal vector art", get_image_prompt_generator_prompt())
            img_filename = f"post_{slugify(topic)}_{random.randint(100,999)}.png"
            img_path = generate_image_comfy(img_prompt, img_filename)
            
            # Сохраняем
            Article.objects.create(
                title=f"Post: {topic}",
                content=post_content,
                content_type='POST',
                featured_image=img_path,
                published=True,
                promote_to_socials=True # Чтобы попало в расписание
            )
            print(f"✅ Пост '{topic}' сохранен.")
        except Exception as e:
            print(f"❌ Ошибка генерации поста: {e}")

def generate_articles_view(request):
    # Логика View
    generating = os.path.exists(PROGRESS_FILE)
    progress = "0/0"
    
    csv_path = os.path.join(settings.BASE_DIR, 'keywords.csv')
    csv_exists = os.path.exists(csv_path)
    csv_count = 0
    if csv_exists:
        with open(csv_path, encoding='utf-8') as f:
            csv_count = sum(1 for line in f) - 1

    if request.method == 'POST':
        if 'stop' in request.POST:
            open(STOP_FLAG, 'w').close()
            messages.success(request, "Остановка...")
            return redirect('/generate/')

        form = GenerateForm(request.POST)
        if form.is_valid():
            a_count = form.cleaned_data['articles_count']
            p_count = form.cleaned_data['posts_count']
            
            # Запускаем в отдельном потоке
            Thread(target=worker_generate_content, args=(a_count, p_count)).start()
            
            messages.success(request, f"Запущено: {a_count} статей, {p_count} постов.")
            return redirect('/generate/')
    else:
        form = GenerateForm()

    return render(request, 'generate_form.html', {
        'form': form,
        'csv_exists': csv_exists,
        'csv_count': csv_count,
        'progress': progress,
        'generating': generating
    })

# --- РЕГИСТРАЦИЯ В АДМИНКЕ ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'content_type', 'created_at', 'published', 'promote_to_socials')
    list_filter = ('published', 'content_type', 'promote_to_socials', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ('published', 'promote_to_socials')

@admin.register(SocialQueue)
class SocialQueueAdmin(admin.ModelAdmin):
    list_display = ('platform', 'article', 'scheduled_time', 'is_sent')
    list_filter = ('platform', 'is_sent', 'scheduled_time')
    ordering = ('-scheduled_time',)