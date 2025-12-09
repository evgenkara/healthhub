from django.core.management.base import BaseCommand
from blog.models import Article, Category, SocialQueue
from blog.ai.prompts import get_article_system_prompt, get_social_system_prompt, get_image_prompt_generator_prompt
from blog.ai.generators import ask_ollama, generate_image_comfy
from django.utils.text import slugify
from django.conf import settings
import csv
import os
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Запускает дневную норму генерации контента (100 статей + 10 постов)'

    def handle(self, *args, **options):
        self.stdout.write("🚀 ЗАПУСК ФАБРИКИ КОНТЕНТА...")

        # 1. ГЕНЕРАЦИЯ СТАТЕЙ (100 шт)
        self.generate_articles(limit=100)
        
        # 2. ГЕНЕРАЦИЯ ПОСТОВ (10 шт)
        self.generate_social_posts(limit=10)
        
        self.stdout.write(self.style.SUCCESS("✅ Дневной план выполнен!"))

    def generate_articles(self, limit):
        csv_path = os.path.join(settings.BASE_DIR, 'keywords.csv')
        if not os.path.exists(csv_path):
            self.stdout.write("⚠️ Нет файла keywords.csv")
            return

        # Читаем CSV и берем случайные темы или по порядку
        with open(csv_path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        
        # Чтобы не генерировать одно и то же, можно удалять использованные строки
        # или просто брать срез. Для примера берем первые 'limit'
        targets = rows[:limit]

        for i, row in enumerate(targets, 1):
            keyword = row['keyword'].strip()
            category_name = row['category'].strip()
            
            self.stdout.write(f"[{i}/{limit}] Статья: {keyword}")

            # 1. Текст
            html = ask_ollama(f"Write a detailed article about {keyword}", get_article_system_prompt())
            if not html: continue

            # 2. Промпт для картинки
            img_prompt = ask_ollama(keyword, get_image_prompt_generator_prompt())
            
            # 3. Картинка
            img_filename = f"{slugify(keyword)}.png"
            img_path = generate_image_comfy(img_prompt, img_filename)

            # 4. Сохранение
            cat, _ = Category.objects.get_or_create(name=category_name)
            Article.objects.create(
                title=keyword,
                content=html,
                category=cat,
                featured_image=img_path, # Может быть None, если Comfy выключен
                content_type='ARTICLE',
                published=True,
                promote_to_socials=True # Чтобы попала в Round Robin
            )

    def generate_social_posts(self, limit):
        topics = [
            "Morning health motivation", "Why sleep matters", "Hydration tip", 
            "Stress relief breathwork", "Benefit of cold showers", "Intermittent fasting fact",
            "Vitamin D benefits", "Walking daily", "Reducing sugar", "Mindfulness moment"
        ]

        for i in range(limit):
            topic = random.choice(topics)
            self.stdout.write(f"[{i+1}/{limit}] Пост: {topic}")

            # 1. Текст (Твиттер)
            # Генерируем 2 варианта: для Твиттера (короткий) и для других (длиннее)
            tw_text = ask_ollama(f"Write a tweet about {topic}", get_social_system_prompt('TW'))
            
            # 2. Картинка (более абстрактная/яркая для соцсетей)
            img_prompt = ask_ollama(f"{topic}, bright colors, minimal vector art style", get_image_prompt_generator_prompt())
            img_filename = f"post_{slugify(topic)}_{random.randint(100,999)}.png"
            img_path = generate_image_comfy(img_prompt, img_filename)

            # 3. Сохранение
            # Создаем запись Article с типом POST. 
            # Она не появится на сайте, но сигнал schedule_social_posts подхватит её
            article = Article.objects.create(
                title=f"Social Post: {topic}",
                content=tw_text, # Здесь лежит текст твита
                content_type='POST',
                featured_image=img_path,
                published=True,
                promote_to_socials=True
            )