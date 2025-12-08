import os
import requests

# === ВСТАВЬ ДАННЫЕ ===
APP_ID = os.getenv(FACEBOOK_APP_ID)
APP_SECRET = os.getenv(FACEBOOK_APP_SECRET)
SHORT_TOKEN = os.getenv(FACEBOOK_SHORT_TOKEN)
# =====================

def get_permanent_token():
    # 1. Меняем короткий токен пользователя на Длинный (60 дней)
    url_long = "https://graph.facebook.com/v19.0/oauth/access_token"
    params_long = {
        'grant_type': 'fb_exchange_token',
        'client_id': APP_ID,
        'client_secret': APP_SECRET,
        'fb_exchange_token': SHORT_TOKEN
    }
    
    resp = requests.get(url_long, params=params_long)
    if resp.status_code != 200:
        print(f"❌ Ошибка обмена токена: {resp.text}")
        return

    long_user_token = resp.json().get('access_token')
    print("✅ Получен длинный токен пользователя!")

    # 2. Получаем список страниц и их "Вечные" токены
    url_pages = "https://graph.facebook.com/v19.0/me/accounts"
    params_pages = {
        'access_token': long_user_token
    }
    
    resp_pages = requests.get(url_pages, params=params_pages)
    if resp_pages.status_code != 200:
        print(f"❌ Ошибка получения страниц: {resp_pages.text}")
        return

    data = resp_pages.json().get('data', [])
    
    if not data:
        print("⚠️ У тебя нет страниц Facebook! Создай страницу.")
        return

    print("\nТвои страницы и их ВЕЧНЫЕ токены (копируй в .env):")
    print("="*60)
    for page in data:
        print(f"📄 Страница: {page['name']}")
        print(f"🆔 PAGE_ID: {page['id']}")
        print(f"🔑 PAGE_TOKEN: {page['access_token']}")
        print("-" * 60)

if __name__ == "__main__":
    get_permanent_token()