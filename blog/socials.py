import tweepy
import requests
import os
import praw
import base64

class TwitterPoster:
    @staticmethod
    def send(title, url, image_path, tags=None): # Добавили image_path
        try:
            # 1. Аутентификация для V1 (Загрузка медиа)
            auth = tweepy.OAuth1UserHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET'),
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_SECRET')
            )
            api = tweepy.API(auth)

            # 2. Аутентификация для V2 (Публикация)
            client = tweepy.Client(
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_SECRET')
            )
            
            # 3. Загружаем картинку
            media_id = None
            if image_path and os.path.exists(image_path):
                media = api.media_upload(filename=image_path)
                media_id = media.media_id

            # 4. Формируем текст
            clean_tags = " ".join([f"#{tag}" for tag in tags]) if tags else "#health"
            text = f"{title}\n\n{clean_tags}\n{url}"
            if len(text) > 280:
                text = f"{title[:200]}...\n\n{url}"

            # 5. Публикуем (с картинкой или без)
            if media_id:
                response = client.create_tweet(text=text, media_ids=[media_id])
            else:
                response = client.create_tweet(text=text)
                
            print(f"🐦 Twitter Post ID: {response.data['id']}")
            return True
        except Exception as e:
            print(f"❌ Twitter Error: {e}")
            return False

class LinkedInPoster:
    @staticmethod
    def send(title, url, description):
        token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        author_urn = os.getenv('LINKEDIN_URN') 
        
        if not token or not author_urn:
            print("⚠️ LinkedIn credentials missing")
            return False

        # === ИСПОЛЬЗУЕМ НОВЫЙ URL API ===
        api_url = "https://api.linkedin.com/rest/posts"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': '202511'  # Обязательно для нового API
        }
        
        # === НОВАЯ СТРУКТУРА JSON ===
        post_data = {
            "author": author_urn,
            "commentary": f"{title}\n\n{description[:200]}...\n\nRead more: {url}",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "article": {
                    "source": url,
                    "title": title,
                    # Можно добавить "thumbnail": "urn:li:image:..." если загружать картинки
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

        try:
            response = requests.post(api_url, headers=headers, json=post_data)
            
            # API LinkedIn возвращает 201 Created при успехе
            if response.status_code == 201:
                print("💼 LinkedIn Posted Successfully (New API)")
                return True
            else:
                print(f"❌ LinkedIn Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ LinkedIn Connection Error: {e}")
            return False

class RedditPoster:
    @staticmethod
    def send(title, url):
        try:
            reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT'),
                username=os.getenv('REDDIT_USERNAME'),
                password=os.getenv('REDDIT_PASSWORD')
            )
            
            if reddit.read_only:
                print("❌ Reddit is read-only. Check credentials.")
                return False

            # Постим в свой профиль
            my_profile = f"u_{os.getenv('REDDIT_USERNAME')}"
            
            submission = reddit.subreddit(my_profile).submit(
                title=title,
                url=url
            )
            
            print(f"👽 Reddit Posted: {submission.shortlink}")
            return True

        except Exception as e:
            print(f"❌ Reddit Error: {e}")
            return False

class PinterestPoster:
    @staticmethod
    def _get_access_token():
        app_id = os.getenv('PINTEREST_APP_ID')
        app_secret = os.getenv('PINTEREST_APP_SECRET')
        refresh_token = os.getenv('PINTEREST_REFRESH_TOKEN')
        
        if not all([app_id, app_secret, refresh_token]):
            return None

        auth_str = f"{app_id}:{app_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        url = 'https://api.pinterest.com/v5/oauth/token'
        headers = {
            'Authorization': f'Basic {b64_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope': 'boards:read,boards:write,pins:read,pins:write'
        }
        
        try:
            resp = requests.post(url, headers=headers, data=data)
            if resp.status_code == 200:
                return resp.json().get('access_token')
            else:
                print(f"Pinterest Token Refresh Failed: {resp.text}")
                return None
        except Exception as e:
            print(f"Pinterest Connection Error: {e}")
            return None

    @staticmethod
    def send(title, url, description, image_url):
        access_token = PinterestPoster._get_access_token()
        if not access_token:
            return False
            
        board_id = os.getenv('PINTEREST_BOARD_ID')
        if not board_id:
            print("❌ Pinterest: No Board ID specified")
            return False

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        api_url = "https://api.pinterest.com/v5/pins"
        
        payload = {
            "title": title,
            "description": description[:500],
            "link": url,
            "board_id": board_id,
            "media_source": {
                "source_type": "image_url",
                "url": image_url 
            }
        }

        try:
            resp = requests.post(api_url, headers=headers, json=payload)
            if resp.status_code == 201:
                print(f"📌 Pinterest Posted: {resp.json()['id']}")
                return True
            else:
                print(f"❌ Pinterest Error: {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Pinterest Request Error: {e}")
            return False
        
class FacebookPoster:
    @staticmethod
    def send(message, image_path=None, link=None):
        page_id = os.getenv('FACEBOOK_PAGE_ID')
        token = os.getenv('FACEBOOK_PAGE_TOKEN')
        
        if not page_id or not token:
            print("❌ Facebook credentials missing")
            return False

        # Формируем текст поста
        full_message = f"{message}\n\n👉 Read more: {link}" if link else message

        try:
            if image_path and os.path.exists(image_path):
                # 1. Постим КАРТИНКУ + Текст
                url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                payload = {
                    'message': full_message,
                    'access_token': token
                }
                # Отправляем файл бинарно
                with open(image_path, 'rb') as img:
                    files = {'source': img}
                    resp = requests.post(url, data=payload, files=files)
            else:
                # 2. Постим только ТЕКСТ + Ссылку (Feed)
                url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
                payload = {
                    'message': full_message,
                    'link': link,
                    'access_token': token
                }
                resp = requests.post(url, data=payload)

            if resp.status_code == 200:
                print(f"📘 FB Posted: ID {resp.json().get('id')}")
                return True
            else:
                print(f"❌ FB Error: {resp.text}")
                return False
                
        except Exception as e:
            print(f"❌ FB Connection Error: {e}")
            return False