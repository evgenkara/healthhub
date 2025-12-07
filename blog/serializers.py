# blog/serializers.py

from rest_framework import serializers
from .models import Article, Category

class ArticleSerializer(serializers.ModelSerializer):
    # Мы принимаем название категории текстом, а не ID
    category_name = serializers.CharField(write_only=True, required=False)
    # Поле category будет использоваться только для отображения (read_only)
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'featured_image', 
            'category', 'category_name', 'published', 
            'meta_title', 'meta_description', 'keywords', 'promote_to_socials'
        ]

    def create(self, validated_data):
        # Извлекаем имя категории из данных
        category_name = validated_data.pop('category_name', 'Uncategorized')
        
        # Получаем или создаем категорию (Best Practice для автоблогов)
        category, created = Category.objects.get_or_create(name=category_name)
        
        # Создаем статью, привязав к ней категорию
        article = Article.objects.create(category=category, **validated_data)
        return article