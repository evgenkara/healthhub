from django.contrib.sitemaps import Sitemap
from .models import Article

class ArticleSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Article.objects.filter(published=True).order_by('-created_at')

    def location(self, obj):
        return f'/article/{obj.slug}/'
