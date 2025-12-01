import re
from django import template

register = template.Library()

@register.filter(name='first_sentence')
def first_sentence(html_content):
    if not html_content:
        return ""
    
    # Находим первый <p>...</p>
    match = re.search(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""
    
    text = match.group(1)
    # Убираем все HTML-теги
    text = re.sub(r'<[^>]+>', '', text).strip()
    
    # Берём только первое предложение
    sentences = re.split(r'(?<=[.!?])\s+', text, 1)  # только первое
    if sentences:
        first = sentences[0].strip()
        # Обрезаем до 180 символов
        return first[:180] + ("..." if len(first) > 180 else "")
    return ""
