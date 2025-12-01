
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django import forms
from .models import Article, Category
import ollama
import requests
import os
import csv
from django.conf import settings
from threading import Thread

STOP_FLAG = os.path.join(settings.BASE_DIR, 'STOP_GENERATION')
PROGRESS_FILE = os.path.join(settings.BASE_DIR, 'GENERATION_PROGRESS')

class GenerateForm(forms.Form):
    count = forms.IntegerField(min_value=1, max_value=5000, initial=100, label="Сколько статей сгенерировать из keywords.csv")

def generate_single_article(keyword, category):
    try:
        client = ollama.Client()
        prompt = f"""Write a detailed 2400–3400 word article titled exactly: "{keyword}"
Include: engaging intro, 10–14 sections, real PubMed links, practical tips, FAQ (8–10 questions), conclusion.
Output ONLY clean HTML."""
        response = client.generate(model='qwen2.5:14b-instruct-q6_k', prompt=prompt, options={'temperature': 0.72})
        html = response['response']
        # ← УДАЛЯЕМ <h1> ВСЁ-ТАКИ, ЕСЛИ ОН ЕСТЬ
        html = html.replace(f"<h1>{keyword}</h1>", "").strip()
        html = html.replace(f"<h1>{keyword.lower()}</h1>", "").strip()
        html = html.replace(f"<h1>{keyword.upper()}</h1>", "").strip()
        article = Article.objects.create(title=keyword, content=html, category=category)

        # Pexels картинки
        
        try:
            query = keyword.replace(" ", "+") + "+health+wellness+fitness"
            url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape"
            headers = {"Authorization": "jMcdR4BWcfCQu6zOTxDc1VhRYT7nJ4m6L5j2bu0T3DoQZ8BqRlERAuD3"}
            data = requests.get(url, headers=headers, timeout=15).json()
                
            if data.get("photos"):
                img_url = data["photos"][0]["src"]["large2x"]
            else:
                img_url = f"https://source.unsplash.com/featured/1200x800/?{keyword},health"
                
            img_data = requests.get(img_url, timeout=20).content
            relative_path = os.path.join('articles', f"{article.slug}.jpg")
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(img_data)
            article.featured_image = relative_path
            
        except Exception as e:
            print(f"Ошибка с фото: {e}")
        article.save()
    except Exception as e:
        print(f"ОШИБКА генерации '{keyword}': {e}")

def background_generate_from_csv(count):
    csv_path = os.path.join(settings.BASE_DIR, 'keywords.csv')
    if not os.path.exists(csv_path):
        return

    # Сразу создаём файл прогресса — Django увидит генерацию
    with open(PROGRESS_FILE, 'w') as pf:
        pf.write(f"0/{count}")

    with open(csv_path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))[:count]
        done = 0

        for row in rows:
            if os.path.exists(STOP_FLAG):
                print("Генерация остановлена")
                break

            category = Category.objects.get_or_create(name=row['category'].strip())[0]
            generate_single_article(row['keyword'].strip(), category)
            done += 1

            # Обновляем прогресс
            with open(PROGRESS_FILE, 'w') as pf:
                pf.write(f"{done}/{count}")

        # Уборка
        for f in [STOP_FLAG, PROGRESS_FILE]:
            if os.path.exists(f):
                os.remove(f)

def generate_articles_view(request):
    generating = os.path.exists(PROGRESS_FILE)
    progress = "0/0"
    if generating:
        try:
            with open(PROGRESS_FILE) as f:
                progress = f.read().strip()
        except:
            progress = "0/0"

    csv_exists = os.path.exists(os.path.join(settings.BASE_DIR, 'keywords.csv'))
    csv_count = 0
    if csv_exists:
        with open(os.path.join(settings.BASE_DIR, 'keywords.csv')) as f:
            csv_count = len(f.readlines()) - 1

    if request.method == 'POST':
        if 'stop' in request.POST:
            open(STOP_FLAG, 'w').close()
            messages.success(request, "Генерация остановлена!")
            return redirect('/generate/')

        form = GenerateForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            Thread(target=background_generate_from_csv, args=(count,)).start()
            messages.success(request, f"Запущено генерация {count} статей")
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

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    search_fields = ('title',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
