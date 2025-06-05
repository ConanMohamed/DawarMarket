import os
import django
import requests
import time
from django.conf import settings

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dwarmarket.settings')
django.setup()

BASE_URL = "https://dawarmarket.com"
STATIC_URLS = [
    "/store/stores/",
    "/store/products/",
    "/store/categories/",
    "/store/orders/",
]

DELAY = 2  # تأخير خفيف بين كل طلب

def get_json(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"⚠️ Failed [{res.status_code}] → {url}")
    except Exception as e:
        print(f"❌ Error at {url}: {e}")
    return []

def warm_url(path):
    url = f"{BASE_URL}{path}"
    try:
        print(f"🔥 Warming {url}")
        res = requests.get(url, timeout=10)
        print("✅ Success" if res.status_code == 200 else f"⚠️ Status {res.status_code}")
    except Exception as e:
        print(f"❌ Error warming {url}: {e}")
    time.sleep(DELAY)

def warm_up():
    # روابط عامة
    for path in STATIC_URLS:
        warm_url(path)

    # كل Store
    stores = get_json(f"{BASE_URL}/store/stores/")
    for store in stores:
        store_id = store['id']
        warm_url(f"/store/stores/{store_id}/")
        warm_url(f"/store/storecategories/?store_id={store_id}")

        # كل StoreCategory داخل الـ Store
        categories = get_json(f"{BASE_URL}/store/storecategories/?store_id={store_id}")
        for cat in categories:
            cat_id = cat['id']
            warm_url(f"/store/storecategories/{cat_id}/")

            # المنتجات داخل كل StoreCategory (عن طريق استرجاع كل المنتجات، وتصفية store_category_id)
            products = cat.get('products', [])
            for product in products:
                product_id = product['id']
                warm_url(f"/store/products/{product_id}/")

if __name__ == "__main__":
    warm_up()
