# blog/context_processors.py
from .models import Category, Article

def common_context(request):
    """
    Контекстный процессор для передачи часто используемых данных
    (категорий и популярных статей) во все шаблоны.
    """
    # Получаем только slug и name для меню - это быстрее
    categories = Category.objects.values('slug', 'name')
    # Получаем только 10 самых свежих статей для боковой панели
    # Используем select_related для оптимизации запроса к category
    popular_articles = Article.objects.select_related('category').order_by('-created_at')[:10].values('slug', 'title', 'category__name', 'created_at')
    return {
        'categories': categories,
        'popular_articles': popular_articles, # Переименуем, чтобы не путать с пагинатором в views.py
    }
