import requests
import secrets
import string
import base64
import webbrowser
import os

# === ВСТАВЬ СВОИ ДАННЫЕ ===
CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'
# ==========================

def get_token():
    # 1. Генерируем ссылку (запрашиваем ВСЕ нужные права)
    state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    scope = 'w_member_social openid profile email'
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        f"&scope={scope}"
    )
    
    print("\n1. Открываю браузер. Войди и нажми 'Allow'...")
    webbrowser.open(auth_url)
    print(f"\nСсылка (если не открылась): {auth_url}\n")
    
    redirect_response = input("2. Вставь ссылку после редиректа сюда: ").strip()
    
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(redirect_response)
        code = parse_qs(parsed.query)['code'][0]
    except:
        print("❌ Ошибка: Код не найден в ссылке.")
        return

    # 2. Получаем Токен
    token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        print(f"❌ Ошибка получения токена: {resp.text}")
        return
        
    data = resp.json()
    access_token = data.get('access_token')
    # Проверяем, какие права реально выдал LinkedIn
    issued_scope = data.get('scope', '') 
    
    print(f"\n🔑 Токен получен!")
    print(f"📋 Выданные права (Scope): {issued_scope}")
    
    if 'w_member_social' not in issued_scope:
        print("⚠️ ВНИМАНИЕ: В токене НЕТ права 'w_member_social'.")
        print("   -> Зайди в LinkedIn Developers -> Products и добавь 'Share on LinkedIn'.")
        return

    # 3. Узнаем правильный URN для этого токена
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Пробуем через /userinfo (самый надежный для новых токенов)
    urn = None
    try:
        r = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)
        if r.status_code == 200:
            sub = r.json().get('sub')
            urn = f"urn:li:person:{sub}"
    except:
        pass
        
    # Если не вышло, пробуем /me
    if not urn:
        try:
            r = requests.get('https://api.linkedin.com/v2/me', headers=headers)
            if r.status_code == 200:
                mid = r.json().get('id')
                urn = f"urn:li:person:{mid}"
        except:
            pass

    if urn:
        print("\n" + "="*40)
        print("✅ УСПЕХ! Скопируй эти строки в .env:")
        print("="*40)
        print(f"LINKEDIN_ACCESS_TOKEN={access_token}")
        print(f"LINKEDIN_URN={urn}")
        print("="*40)
    else:
        print(f"❌ Токен есть, но не удалось узнать ID. Ошибка доступа к профилю.")

if __name__ == "__main__":
    get_token()