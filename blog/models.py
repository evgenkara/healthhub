from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField("SEO описание категории", blank=True) # Полезно для SEO категорий

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_view', kwargs={'slug': self.slug})


class Article(models.Model):
    CONTENT_TYPES = [
        ('ARTICLE', 'Статья для сайта'),
        ('POST', 'Пост для соцсетей'),
    ]
    # Основной контент
    title = models.CharField("Заголовок (H1)", max_length=300)
    slug = models.SlugField(unique=True, blank=True, max_length=300)
    content = models.TextField("Контент статьи")
    
    # Изображения
    featured_image = models.ImageField("Главное изображение", upload_to='articles/%Y/%m/', blank=True, null=True)
    # second_image лучше убрать, если нейросеть будет вставлять картинки прямо в текст (HTML),
    # либо оставить, если жесткий дизайн. Лучшая практика: хранить доп. картинки как вложения 
    # или вставлять в content img src.
    content_type = models.CharField(
        max_length=10, 
        choices=CONTENT_TYPES, 
        default='ARTICLE'
    )
    # Мета-данные и SEO
    meta_title = models.CharField("SEO Title", max_length=300, blank=True, help_text="Если пусто, берется title")
    meta_description = models.TextField("Meta Description", blank=True, help_text="Краткое содержание для поисковиков")
    keywords = models.CharField("Keywords", max_length=255, blank=True)
    
    # Связи и статусы
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True) # Важно для SEO
    published = models.BooleanField("Опубликовано", default=False) # Сначала False, пока скрипт не подтвердит
    # Флаг намерения: "Хочу, чтобы это ушло в телеграм"
    push_to_telegram = models.BooleanField("Отправлять в Telegram?", default=False)
    
    # Флаг статуса: "Уже отправлено" (он у тебя уже есть как posted_to_socials)
    promote_to_socials = models.BooleanField("Промо в соцсети", default=False)
    
    # Статусы (чтобы знать, куда ушло)
    posted_to_telegram = models.BooleanField(default=False)
    posted_to_twitter = models.BooleanField(default=False)
    posted_to_linkedin = models.BooleanField(default=False)
    

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            if self.content_type == 'POST':
                import uuid
                self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
            else:
                self.slug = base_slug
        if not self.meta_title:
            self.meta_title = self.title
        # Авто-генерация meta description из контента, если пусто
        if not self.meta_description and self.content:
            # Берем первые 150 символов, очищая от HTML (нужна доп. функция, но пока так)
            self.meta_description = self.content[:150] + "..."
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})
    
class SocialQueue(models.Model):
    PLATFORMS = [
        ('TG', 'Telegram'),
        ('TW', 'Twitter'),
        ('LI', 'LinkedIn'),
        ('PI', 'Pinterest'),
        ('FB', 'Facebook'), # Добавили
        ('RD', 'Reddit'),   # Добавили
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    platform = models.CharField(max_length=2, choices=PLATFORMS)
    scheduled_time = models.DateTimeField("Время публикации")
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_time']
        verbose_name = "Очередь соцсетей"
        verbose_name_plural = "Очередь соцсетей"
        # Индекс для ускорения поиска последнего поста
        indexes = [
            models.Index(fields=['platform', 'scheduled_time']),
        ]

    def __str__(self):
        return f"{self.platform}: {self.article.title}"