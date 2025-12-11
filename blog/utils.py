# blog/utils.py
import requests
import os
from django.conf import settings

def send_telegram_admin(message):
    """Отправляет сообщение админу в Телеграм"""
    token = os.getenv('MONITOR_BOT_TOKEN')
    chat_id = os.getenv('MONITOR_ADMIN_ID')
    
    if not token or not chat_id:
        print("⚠️ Не настроен MONITOR_BOT_TOKEN или MONITOR_ADMIN_ID")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"❌ Ошибка отправки в TG: {e}")