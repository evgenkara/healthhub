from django.core.management.base import BaseCommand
from blog.models import Article, SocialQueue
from blog.utils import send_telegram_admin
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Отправляет статистику за последние 24 часа'

    def handle(self, *args, **options):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        # 1. Статьи за сутки
        new_articles = Article.objects.filter(
            created_at__gte=last_24h, 
            content_type='ARTICLE'
        ).count()

        # 2. Посты за сутки
        new_posts = Article.objects.filter(
            created_at__gte=last_24h, 
            content_type='POST'
        ).count()

        # 3. Соцсети (Очередь)
        queue_pending = SocialQueue.objects.filter(is_sent=False).count()
        queue_sent_24h = SocialQueue.objects.filter(
            is_sent=True, 
            scheduled_time__gte=last_24h
        ).count()

        # 4. Всего на сайте
        total_articles = Article.objects.filter(content_type='ARTICLE').count()

        msg = (
            f"📊 <b>Ежедневный отчет CureCurious</b>\n"
            f"<i>{now.strftime('%d.%m.%Y')}</i>\n\n"
            f"<b>Производство:</b>\n"
            f"✅ Новых статей: {new_articles}\n"
            f"✅ Новых постов: {new_posts}\n\n"
            f"<b>Дистрибуция (Соцсети):</b>\n"
            f"🚀 Отправлено: {queue_sent_24h}\n"
            f"⏳ В очереди: {queue_pending}\n\n"
            f"<b>Всего в базе:</b> {total_articles} статей."
        )

        send_telegram_admin(msg)
        self.stdout.write("Отчет отправлен.")