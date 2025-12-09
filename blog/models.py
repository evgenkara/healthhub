from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import uuid

class Category(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField("SEO описание категории", blank=True)

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
        return reverse('category', kwargs={'slug': self.slug})


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
    
    # Тип контента (Новое поле)
    content_type = models.CharField(
        "Тип контента",
        max_length=10, 
        choices=CONTENT_TYPES, 
        default='ARTICLE'
    )

    # Мета-данные и SEO
    meta_title = models.CharField("SEO Title", max_length=300, blank=True)
    meta_description = models.TextField("Meta Description", blank=True)
    keywords = models.CharField("Keywords", max_length=255, blank=True)
    
    # Связи и статусы
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    published = models.BooleanField("Опубликовано", default=False)
    
    # Социальные сети
    promote_to_socials = models.BooleanField("Промо в соцсети", default=False)
    
    # Статусы отправки (чтобы не дублировать)
    posted_to_telegram = models.BooleanField(default=False)
    posted_to_twitter = models.BooleanField(default=False)
    posted_to_linkedin = models.BooleanField(default=False)
    posted_to_pinterest = models.BooleanField(default=False)
    posted_to_reddit = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]

    def save(self, *args, **kwargs):
        # Генерируем slug, если его нет
        if not self.slug:
            base_slug = slugify(self.title)
            
            # Если это пост для соцсетей, добавляем уникальный хвост,
            # чтобы посты "Доброе утро" не конфликтовали
            if self.content_type == 'POST':
                unique_suffix = str(uuid.uuid4())[:8]
                self.slug = f"{base_slug}-{unique_suffix}"
            else:
                self.slug = base_slug

        # SEO поля
        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description and self.content:
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
        ('FB', 'Facebook'),
        ('RD', 'Reddit'),
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
        indexes = [
            models.Index(fields=['platform', 'scheduled_time']),
        ]

    def __str__(self):
        return f"{self.platform}: {self.article.title}"