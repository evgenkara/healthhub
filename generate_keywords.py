import csv
import random

# === ТОЛЬКО 12 КАТЕГОРИЙ, как в вашем проекте ===
CATEGORIES = [
    "Nutrition & Diet", "Vitamins & Supplements", "Weight Loss & Fat Burning",
    "Fitness & Exercise", "Mental Health & Stress", "Sleep & Recovery",
    "Women's Health", "Men's Health", "Anti-Aging & Longevity",
    "Immune System", "Heart Health", "Brain Health"
]

# Словари для разных позиций в фразе
PREFIXES = [
    "best", "top", "ultimate", "complete", "essential", "practical", 
    "science-backed", "proven", "effective", "natural", "simple", "easy",
    "quick", "safe", "powerful", "advanced", "comprehensive", "expert"
]

MAIN_TOPICS = {
    "Nutrition & Diet": [
        "keto diet", "intermittent fasting", "plant-based diet", "mediterranean diet", 
        "low carb diet", "high protein diet", "anti-inflammatory diet", "gut healing diet",
        "blood sugar balance", "healthy meal prep"
    ],
    "Vitamins & Supplements": [
        "vitamin d3", "magnesium glycinate", "omega 3 fatty acids", "collagen peptides", 
        "ashwagandha extract", "turmeric curcumin", "probiotic strains", "vitamin b12",
        "zinc picolinate", "vitamin c liposomal"
    ],
    "Weight Loss & Fat Burning": [
        "belly fat reduction", "metabolic rate boost", "insulin sensitivity", 
        "appetite suppression", "fat burning foods", "weight loss plateau", 
        "hormonal weight gain", "stress eating", "body recomposition"
    ],
    "Fitness & Exercise": [
        "hiit workouts", "strength training", "mobility exercises", "yoga for flexibility",
        "functional fitness", "home workout routine", "recovery techniques", 
        "exercise for beginners", "core strengthening"
    ],
    "Mental Health & Stress": [
        "anxiety reduction", "stress management", "mindfulness practices", 
        "meditation techniques", "cortisol regulation", "burnout prevention", 
        "emotional resilience", "nervous system regulation"
    ],
    "Sleep & Recovery": [
        "sleep quality improvement", "insomnia solutions", "deep sleep techniques", 
        "circadian rhythm optimization", "sleep hygiene practices", "waking up refreshed"
    ],
    "Women's Health": [
        "hormone balance", "pcos management", "menopause transition", "thyroid health",
        "fertility optimization", "postpartum recovery", "estrogen dominance"
    ],
    "Men's Health": [
        "testosterone optimization", "prostate health", "erectile function", 
        "male fertility", "andropause management", "muscle mass preservation"
    ],
    "Anti-Aging & Longevity": [
        "cellular rejuvenation", "telomere protection", "longevity diet", 
        "biological age reversal", "skin aging prevention", "collagen production"
    ],
    "Immune System": [
        "immune support", "immune modulation", "inflammation reduction", 
        "autoimmune management", "gut immune connection", "antiviral nutrition"
    ],
    "Heart Health": [
        "blood pressure management", "cholesterol optimization", "heart disease prevention", 
        "circulation improvement", "arterial health", "omega 3 benefits"
    ],
    "Brain Health": [
        "cognitive enhancement", "memory improvement", "brain fog solutions", 
        "neuroplasticity training", "dementia prevention", "focus and concentration"
    ]
}

MODIFIERS = [
    "benefits", "side effects", "dosage guide", "for beginners", 
    "at home", "naturally", "without medication", "science proven", 
    "practical tips", "daily routine", "meal plan", "supplement stack", 
    "lifestyle changes", "dietary adjustments", "exercise protocol", 
    "success stories", "common mistakes", "myths debunked", 
    "long term results", "safety considerations"
]

# Демографические модификаторы (для дополнительного разнообразия)
DEMOGRAPHICS = ["over 30", "over 40", "over 50", "over 60", "women", "men", "athletes", "busy professionals"]

def generate_phrase(category):
    """Генерирует осмысленную фразу для заданной категории"""
    topic = random.choice(MAIN_TOPICS[category])
    
    # Случайно выбираем структуру фразы
    structure = random.choice([
        lambda t: f"best {t}",
        lambda t: f"how to improve {t}",
        lambda t: f"{t} for {random.choice(['better health', 'optimal results', 'longevity', 'vitality', 'energy', 'wellbeing'])}",
        lambda t: f"{t}: {random.choice(MODIFIERS)}",
        lambda t: f"{random.choice(PREFIXES)} {t} {random.choice(MODIFIERS)}",
        lambda t: f"complete guide to {t}",
        lambda t: f"{t} without {random.choice(['side effects', 'medication', 'expensive treatments', 'dieting', 'surgery'])}",
        lambda t: f"{t} for {random.choice(DEMOGRAPHICS)}",
        lambda t: f"science behind {t}",
        lambda t: f"{t} results"
    ])
    
    phrase = structure(topic)
    
    # Иногда добавляем демографический модификатор
    if random.random() < 0.15:
        phrase += f" for {random.choice(DEMOGRAPHICS)}"
    
    # Иногда добавляем дополнительный модификатор
    if random.random() < 0.1:
        phrase += f" with {random.choice(['natural remedies', 'lifestyle changes', 'dietary adjustments', 'exercise routine', 'stress management'])}"
    
    return phrase.lower()

# === Генерация 15000 уникальных ключевых слов ===
keywords = set()
target = 15000
attempts = 0
max_attempts = 50000

while len(keywords) < target and attempts < max_attempts:
    category = random.choice(CATEGORIES)
    phrase = generate_phrase(category)
    keywords.add((category, phrase))
    attempts += 1
    
    if len(keywords) % 1000 == 0 and len(keywords) > 0:
        print(f"Сгенерировано: {len(keywords)}/{target}")

# Дополняем, если не хватает
if len(keywords) < target:
    print("Дополнительная генерация...")
    remaining = target - len(keywords)
    all_topics = [item for sublist in MAIN_TOPICS.values() for item in sublist]
    simple_combinations = []
    for prefix in PREFIXES:
        for topic in random.sample(all_topics, min(100, len(all_topics))):
            for modifier in random.sample(MODIFIERS, 3):
                simple_combinations.append(f"{prefix} {topic} {modifier}")
    random.shuffle(simple_combinations)
    for i in range(min(remaining, len(simple_combinations))):
        category = random.choice(CATEGORIES)
        keywords.add((category, simple_combinations[i].lower()))

# === Сохранение ===
with open('keywords-15000.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['category', 'keyword'])
    writer.writerows(keywords)

print(f"\nГОТОВО! {len(keywords)} уникальных ключевых слов сохранено в файл keywords-15000.csv")