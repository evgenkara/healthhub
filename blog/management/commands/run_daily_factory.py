from django.core.management.base import BaseCommand
from blog.models import Article, Category, SocialQueue
from blog.ai.prompts import get_article_system_prompt, get_social_system_prompt, get_image_prompt_generator_prompt
from blog.ai.generators import ask_ollama, generate_image_comfy
from blog.utils import send_telegram_admin  # <--- Импортируем нашего почтальона
from django.utils.text import slugify
from django.conf import settings
import csv
import os
import random
import time

class Command(BaseCommand):
    help = 'Запускает дневную норму генерации (удаляет строки из CSV + шлет отчет)'

    def handle(self, *args, **options):
        start_time = time.time()
        send_telegram_admin("🏭 <b>Фабрика запущена!</b>\nНачинаю производство контента.")

        # 1. ГЕНЕРАЦИЯ СТАТЕЙ (100 шт)
        articles_created = self.generate_articles(limit=100)
        
        # 2. ГЕНЕРАЦИЯ ПОСТОВ (10 шт)
        posts_created = self.generate_social_posts(limit=10)
        
        duration = round((time.time() - start_time) / 60, 1)
        
        report = (
            f"✅ <b>Смена окончена!</b>\n\n"
            f"⏱ Время: {duration} мин\n"
            f"📝 Статьи: +{articles_created}\n"
            f"📱 Посты: +{posts_created}\n"
            f"💾 База данных обновлена."
        )
        self.stdout.write(self.style.SUCCESS(report))
        send_telegram_admin(report)

    def generate_articles(self, limit):
        csv_path = os.path.join(settings.BASE_DIR, 'keywords.csv')
        if not os.path.exists(csv_path):
            self.stdout.write("⚠️ Нет файла keywords.csv")
            send_telegram_admin("⚠️ <b>Внимание:</b> Файл keywords.csv не найден!")
            return 0

        # --- ЛОГИКА ЧТЕНИЯ И УДАЛЕНИЯ ---
        # 1. Читаем ВСЕ строки
        with open(csv_path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            fieldnames = rows[0].keys() if rows else ['category', 'keyword']
        
        if not rows:
            send_telegram_admin("⚠️ <b>Внимание:</b> CSV файл пуст! Нечего генерировать.")
            return 0

        # 2. Делим на "в работу" и "остаток"
        targets = rows[:limit]       # То, что будем делать сейчас
        remaining = rows[limit:]     # То, что останется на завтра

        # 3. ПЕРЕЗАПИСЫВАЕМ файл сразу (чтобы не было дублей, если скрипт упадет)
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(remaining)
        
        self.stdout.write(f"✂️ Изъято {len(targets)} тем из CSV. Осталось: {len(remaining)}")

        # --- ГЕНЕРАЦИЯ ---
        success_count = 0
        
        for i, row in enumerate(targets, 1):
            keyword = row['keyword'].strip()
            category_name = row['category'].strip()
            
            self.stdout.write(f"[{i}/{len(targets)}] {keyword}")

            # Текст
            html = ask_ollama(f"Write a detailed article about {keyword}", get_article_system_prompt())
            if not html: 
                print("   -> Пропуск (ошибка текста)")
                continue

            # Картинка
            img_prompt = ask_ollama(keyword, get_image_prompt_generator_prompt())
            img_filename = f"{slugify(keyword)}.png"
            img_path = generate_image_comfy(img_prompt, img_filename)

            # Сохранение
            try:
                cat, _ = Category.objects.get_or_create(name=category_name)
                Article.objects.create(
                    title=keyword,
                    content=html,
                    category=cat,
                    featured_image=img_path,
                    content_type='ARTICLE',
                    published=True,
                    promote_to_socials=True
                )
                success_count += 1
            except Exception as e:
                print(f"   -> Ошибка БД: {e}")

        return success_count

    def generate_social_posts(self, limit):
        topics = [
            "Morning health motivation", "Why sleep matters", "Hydration tip", 
            "Stress relief breathwork", "Benefit of cold showers", "Intermittent fasting fact",
            "Vitamin D benefits", "Walking daily", "Reducing sugar", "Mindfulness moment"
        ]
        
        success_count = 0
        for i in range(limit):
            topic = random.choice(topics)
            
            tw_text = ask_ollama(f"Write a tweet about {topic}", get_social_system_prompt('TW'))
            if not tw_text: continue

            img_prompt = ask_ollama(f"{topic}, bright vector art", get_image_prompt_generator_prompt())
            img_filename = f"post_{slugify(topic)}_{random.randint(100,999)}.png"
            img_path = generate_image_comfy(img_prompt, img_filename)

            try:
                Article.objects.create(
                    title=f"Social Post: {topic}",
                    content=tw_text,
                    content_type='POST',
                    featured_image=img_path,
                    published=True,
                    promote_to_socials=True
                )
                success_count += 1
            except:
                pass
                
        return success_count