from django.contrib.syndication.views import Feed
from django.urls import reverse
from .models import Article

class LatestArticlesFeed(Feed):
    title = "HealthHub Articles"
    link = "/"
    description = "Latest updates on health, wellness, and longevity."

    def items(self):
        # Возвращаем последние 20 опубликованных статей
        return Article.objects.filter(published=True).order_by('-created_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        # Используем meta_description или обрезаем контент
        return item.meta_description or item.content[:200]

    def item_link(self, item):
        return reverse('article_detail', args=[item.slug])

    def item_enclosure_url(self, item):
        # Если есть картинка, добавляем её в RSS (полезно для Pinterest/Flipboard)
        if item.featured_image:
            return item.featured_image.url
        return None
    
    def item_enclosure_length(self, item):
        # Обязательное поле, если используем enclosure, ставим примерно
        if item.featured_image:
            return str(item.featured_image.size)
        return "0"
        
    def item_enclosure_mime_type(self, item):
        return "image/jpeg"