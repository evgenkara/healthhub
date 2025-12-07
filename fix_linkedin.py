import os
import requests
from dotenv import load_dotenv

# Загружаем текущий токен из .env
load_dotenv()

def find_correct_urn():
    token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    
    if not token:
        print("❌ ОШИБКА: В .env нет LINKEDIN_ACCESS_TOKEN")
        return

    print(f"🔑 Использую токен: {token[:10]}...")
    headers = {'Authorization': f'Bearer {token}'}

    # Способ 1: Через /userinfo (Новый стандарт OpenID)
    print("\n1. Пробую метод OpenID (userinfo)...")
    try:
        resp = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            sub_id = data.get('sub')
            # Для userinfo правильный формат ВСЕГДА urn:li:person
            correct_urn = f"urn:li:person:{sub_id}"
            print(f"✅ НАЙДЕНО! Твой правильный URN: {correct_urn}")
            print("\nСкопируй эту строку в .env:")
            print(f"LINKEDIN_URN={correct_urn}")
            return
        else:
            print(f"   Не сработало: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Способ 2: Через /me (Старый стандарт)
    print("\n2. Пробую метод Legacy (/me)...")
    try:
        resp = requests.get('https://api.linkedin.com/v2/me', headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            mem_id = data.get('id')
            # Для /me правильный формат тоже urn:li:person для ugcPosts
            correct_urn = f"urn:li:person:{mem_id}"
            print(f"✅ НАЙДЕНО! Твой правильный URN: {correct_urn}")
            print("\nСкопируй эту строку в .env:")
            print(f"LINKEDIN_URN={correct_urn}")
            return
        else:
            print(f"   Не сработало: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    print("\n❌ Не удалось узнать URN. Возможно, токен протух или у него нет прав.")
    print("Попробуй запустить get_linkedin_token.py заново.")

if __name__ == "__main__":
    find_correct_urn()