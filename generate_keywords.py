# generate_keywords_ultra_fast.py
import csv
import random

# 12 категорий
categories = [
    "Nutrition & Diet", "Vitamins & Supplements", "Weight Loss & Fat Burning",
    "Fitness & Exercise", "Mental Health & Stress", "Sleep & Recovery",
    "Women's Health", "Men's Health", "Anti-Aging & Longevity",
    "Immune System", "Heart Health", "Brain Health"
]

# База слов — просто мешаем и получаем миллионы комбинаций
words1 = ["best", "top", "how to", "natural", "ultimate", "2026", "easy", "fast", "simple", "effective"]
words2 = ["magnesium", "vitamin d", "omega 3", "collagen", "ashwagandha", "turmeric", "probiotics", "keto", "intermittent fasting", "gut health", "testosterone", "cortisol", "sleep", "anxiety", "weight loss", "belly fat", "immune boost", "brain fog", "hormone balance", "anti aging"]
words3 = ["benefits", "foods", "supplements", "dosage", "for beginners", "at home", "naturally", "meal plan", "remedies", "tips", "guide", "routine", "exercises", "for women", "for men", "over 40", "over 50", "side effects", "results"]

# Генерируем 15 000 уникальных ключей
keywords = set()
while len(keywords) < 15000:
    cat = random.choice(categories)
    key = f"{random.choice(words1)} {random.choice(words2)} {random.choice(words3)}"
    if random.random() < 0.3:
        key += " 2025"
    if random.random() < 0.2:
        key += " naturally"
    keywords.add((cat, key.lower()))

# Сохраняем
with open('keywords-15000-fast.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['category', 'keyword'])
    for cat, kw in keywords:
        writer.writerow([cat, kw])

print("ГОТОВО! 15 000 ключей → keywords-15000-fast.csv")