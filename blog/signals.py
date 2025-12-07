# blog/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Article, SocialQueue
import random


@receiver(post_save, sender=Article)
def schedule_social_posts(sender, instance, created, **kwargs):
    if instance.content_type == 'POST':
    # Добавляем в очередь Telegram и Twitter (для коротких постов это лучшие сети)
        SocialQueue.objects.create(article=instance, platform='TG', scheduled_time=now + timedelta(hours=random.randint(1, 12)))
        SocialQueue.objects.create(article=instance, platform='TW', scheduled_time=now + timedelta(hours=random.randint(1, 12)))
        # Планируем только если статья опубликована, с галочкой промо и это СОЗДАНИЕ (created=True)
    if instance.published and instance.promote_to_socials and created:
        
        # 1. Список платформ в порядке очереди
        # Важно: Порядок жесткий, чтобы распределение было равномерным
        platforms_order = ['TG', 'TW', 'LI', 'FB', 'RD', 'PI']
        
        # 2. Определяем целевую платформу для ЭТОЙ статьи
        # Используем ID статьи. Article ID 1 -> TG, ID 2 -> TW и т.д.
        target_index = instance.id % len(platforms_order)
        platform_code = platforms_order[target_index]

        # === ПРОВЕРКА ОГРАНИЧЕНИЙ ===
        # Pinterest требует картинку. Если её нет, перекидываем в Twitter (текстовая)
        if platform_code == 'PI' and not instance.featured_image:
            print(f"⚠️ Статья {instance.id} должна была уйти в Pinterest, но нет картинки. Меняем на Twitter.")
            platform_code = 'TW'

        # 3. Рассчитываем время публикации
        # Находим ПОСЛЕДНИЙ запланированный пост именно для ЭТОЙ платформы
        last_post = SocialQueue.objects.filter(platform=platform_code).order_by('-scheduled_time').first()
        
        if last_post:
            # Если очередь есть, ставим через 1.5 часа (90 минут) после последнего
            start_time = last_post.scheduled_time + timedelta(minutes=90)
        else:
            # Если очередь пуста, ставим на "сейчас" + 10 минут
            start_time = timezone.now() + timedelta(minutes=10)
            
        # Если время получилось в прошлом (бывает при сбоях), двигаем вперед
        if start_time < timezone.now():
            start_time = timezone.now() + timedelta(minutes=10)

        # 4. Создаем запись в очереди
        SocialQueue.objects.create(
            article=instance,
            platform=platform_code,
            scheduled_time=start_time
        )
        
        print(f"📅 Статья '{instance.title}' запланирована в {platform_code} на {start_time.strftime('%H:%M')}")