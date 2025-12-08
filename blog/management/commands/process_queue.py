# blog/management/commands/process_queue.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import SocialQueue
from blog.socials import TwitterPoster, LinkedInPoster, PinterestPoster, RedditPoster
import os
import requests

class Command(BaseCommand):
    help = 'Отправляет запланированные посты в соцсети'

    def handle(self, *args, **options):
        now = timezone.now()
        # Берем неотправленные задачи, время которых пришло
        tasks = SocialQueue.objects.filter(scheduled_time__lte=now, is_sent=False)

        self.stdout.write(f"⏳ Найдено задач к отправке: {tasks.count()}")

        domain = os.getenv('SITE_DOMAIN', 'http://127.0.0.1:8000')

        for task in tasks:
            article = task.article
            # Формируем полную ссылку на статью и картинку
            url = f"{domain}/article/{article.slug}/"
            
            image_path = None
            image_url = None
            if article.featured_image:
                image_path = article.featured_image.path
                if domain.startswith('http'):
                    image_url = f"{domain}{article.featured_image.url}"
                else:
                    image_url = f"http://{domain}{article.featured_image.url}"

            success = False
            self.stdout.write(f"🚀 Processing {task.platform}: {article.title[:30]}...")

            try:
                # === 1. TELEGRAM ===
                if task.platform == 'TG':
                    token = os.getenv('TELEGRAM_BOT_TOKEN')
                    chat_id = os.getenv('TELEGRAM_CHANNEL_ID')
                    caption = f"<b>{article.title}</b>\n\n{article.meta_description[:150]}...\n\n👉 {url}"
                    
                    if image_path:
                        with open(image_path, 'rb') as f:
                            resp = requests.post(
                                f"https://api.telegram.org/bot{token}/sendPhoto",
                                data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'},
                                files={'photo': f}
                            )
                    else:
                        resp = requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            data={'chat_id': chat_id, 'text': caption, 'parse_mode': 'HTML'}
                        )
                    success = (resp.status_code == 200)

                # === 2. TWITTER ===
                elif task.platform == 'TW':
                    clean_cat = article.category.slug.replace("-", "")
                    tags = ["health", clean_cat]
                    success = TwitterPoster.send(article.title, url, image_path, tags)

                # === 3. LINKEDIN ===
                elif task.platform == 'LI':
                    success = LinkedInPoster.send(article.title, url, article.meta_description)

                # === 4. PINTEREST ===
                elif task.platform == 'PI':
                    if image_url:
                        success = PinterestPoster.send(
                            article.title, url, 
                            article.meta_description, image_url
                        )
                    else:
                        self.stdout.write(self.style.WARNING("Skipping Pinterest: No image URL"))
                        success = True # Пропускаем, но помечаем как обработанное

                # === 5. REDDIT ===
                elif task.platform == 'RD':
                    # Пытаемся отправить, если ключи настроены
                    if os.getenv('REDDIT_CLIENT_ID'): 
                        success = RedditPoster.send(article.title, url)
                    else:
                        self.stdout.write("Reddit keys missing, skipping...")
                        success = True # Фиктивный успех, чтобы не забивать очередь

                # === 6. FACEBOOK ===
                elif task.platform == 'FB':
                    from blog.socials import FacebookPoster # Убедись в импорте
                    
                    # Подготовка данных
                    caption = f"{article.title}\n\n{article.meta_description[:200]}..."
                    img_path = article.featured_image.path if article.featured_image else None
                    
                    success = FacebookPoster.send(
                        message=caption,
                        image_path=img_path,
                        link=url
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Critical Error: {e}"))

            # Финализация
            if success:
                task.is_sent = True
                task.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Sent to {task.platform}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Failed {task.platform}"))