import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsite.settings')
django.setup()
from blog.socials import FacebookPoster

if __name__ == "__main__":
    print("Testing Facebook...")
    FacebookPoster.send(
        message="Hello from Python Code!", 
        link="http://127.0.0.1:8000"
    )