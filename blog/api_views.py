# blog/api_views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Article
from .serializers import ArticleSerializer

class ArticleCreateAPIView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    # Только авторизованный пользователь с токеном может постить
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # Парсеры нужны для обработки загрузки картинок (multipart/form-data)
    parser_classes = [MultiPartParser, FormParser]