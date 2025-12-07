import os
import django

# Настройка окружения Django, чтобы видеть .env и настройки
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsite.settings')
django.setup()

from blog.socials import TwitterPoster, LinkedInPoster

# def test_twitter():
#     print("\n" + "="*20)
#     print("🐦 ТЕСТ TWITTER")
#     print("="*20)
    
#     # Проверка наличия ключей
#     api_key = os.getenv('TWITTER_API_KEY')
#     if not api_key:
#         print("❌ ОШИБКА: TWITTER_API_KEY не найден в .env")
#         return

#     print("🔑 Ключи найдены. Пробую отправить твит...")
    
#     # Пытаемся отправить
#     success = TwitterPoster.send(
#         title="Test Tweet from CureCurious Debugger",
#         url="http://127.0.0.1:8000/",
#         tags=["test", "debug"]
#     )
    
#     if success:
#         print("✅ УСПЕХ: Твит опубликован!")
#     else:
#         print("❌ ПРОВАЛ: Смотри ошибку выше (обычно 401 Unauthorized или 403 Forbidden).")

def test_linkedin():
    print("\n" + "="*20)
    print("💼 ТЕСТ LINKEDIN")
    print("="*20)
    
    token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    urn = os.getenv('LINKEDIN_URN')
    
    if not token:
        print("❌ ОШИБКА: LINKEDIN_ACCESS_TOKEN не найден")
        return
    if not urn:
        print("❌ ОШИБКА: LINKEDIN_URN не найден")
        return
        
    print(f"👤 Твой URN: {urn}")
    print("🚀 Пробую отправить пост...")
    
    success = LinkedInPoster.send(
        title="Test Post from HealthHub Debugger",
        url="http://127.0.0.1:8000/",
        description="Testing API integration connection."
    )
    
    if success:
        print("✅ УСПЕХ: Пост опубликован в LinkedIn!")
    else:
        print("❌ ПРОВАЛ: Смотри текст ошибки выше.")

if __name__ == "__main__":
    #python test_socials.pytest_twitter()
    test_linkedin()