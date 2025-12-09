
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from blog.views import home, category_view, article_detail, search, live_search
from blog.admin import generate_articles_view
from blog.sitemaps import ArticleSitemap
from blog.api_views import ArticleCreateAPIView # Импортируем наш view
from blog.feeds import LatestArticlesFeed # Импортируем

sitemaps = {'articles': ArticleSitemap}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('generate/', generate_articles_view, name='generate_articles'),
    path('search/', search, name='search'),
    path('live-search/', live_search, name='live_search'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    # ← ВСЁ РАБОТАЕТ! Правильные статические страницы
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('disclaimer/', TemplateView.as_view(template_name='disclaimer.html'), name='disclaimer'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),

    # Главная и статьи
    path('', home, name='home'),
    path('category/<slug:slug>/', category_view, name='category'),
    path('article/<slug:slug>/', article_detail, name='article_detail'),
    path('api/articles/create/', ArticleCreateAPIView.as_view(), name='api-article-create'),
    path('feed/', LatestArticlesFeed(), name='article_feed'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('ads.txt', TemplateView.as_view(template_name="ads.txt", content_type="text/plain")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
