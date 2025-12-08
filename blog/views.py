
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Article, Category

def get_per_page(request):
    # Мобильные — 10, десктоп — 20
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad']
    if any(keyword in user_agent for keyword in mobile_keywords):
        return 10
    return 20

def home(request):
    articles_list = Article.objects.filter(published=True).order_by('-created_at')
    categories = Category.objects.all()
    
    paginator = Paginator(articles_list, get_per_page(request))
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    
    return render(request, 'home.html', {
        'articles': articles,
        'categories': categories
    })

def category_view(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    articles_list = Article.objects.filter(category=cat, published=True).order_by('-created_at')
    categories = Category.objects.all()
    
    paginator = Paginator(articles_list, get_per_page(request))
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    
    return render(request, 'category.html', {
        'articles': articles,
        'category': cat,
        'categories': categories
    })

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    categories = Category.objects.all()
    articles = Article.objects.filter(published=True).order_by('-created_at')[:10]
    return render(request, 'article_detail.html', {
        'article': article,
        'categories': categories,
        'articles': articles
    })

def search(request):
    query = request.GET.get('q', '').strip()
    categories = Category.objects.all()
    articles_list = Article.objects.filter(published=True)

    if query:
        # Создаем объект запроса
        search_query = SearchQuery(query)
        
        # Определяем, где искать. 
        # weight='A' - самый важный (Заголовок)
        # weight='B' - менее важный (Контент)
        search_vector = SearchVector('title', weight='A') + \
                        SearchVector('content', weight='B')
        
        # 1. Аннотируем (добавляем вычисляемое поле) 'rank' - релевантность
        # 2. Фильтруем (rank__gte=0.1) отсекает мусорные совпадения
        # 3. Сортируем по релевантности (сначала самые точные), потом по дате
        articles_list = articles_list.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', '-created_at')

    else:
        # Если запроса нет, показываем пустой список или последние
        articles_list = Article.objects.none()

    paginator = Paginator(articles_list, get_per_page(request))
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    return render(request, 'search.html', {
        'articles': articles,
        'categories': categories,
        'query': query,
        'count': articles_list.count()
    })

def live_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Для живого поиска (подсказок) обычно ищут только по заголовкам,
    # чтобы было быстро и релевантно.
    # Используем SearchVector только по title
    search_vector = SearchVector('title')
    search_query = SearchQuery(query)
    
    articles = Article.objects.annotate(
        search=search_vector,
        rank=SearchRank(search_vector, search_query)
    ).filter(search=search_query).order_by('-rank')[:7]

    results = [
        {'title': a.title, 'url': f"/article/{a.slug}/"}
        for a in articles
    ]
    return JsonResponse({'results': results})