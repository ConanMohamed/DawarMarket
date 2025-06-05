import os
import django
import requests

# إعداد Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dwarmarket.settings')
django.setup()

BASE_URL = "https://dawarmarket.com"

def get_all_store_ids():
    try:
        print("📦 Fetching store IDs...")
        res = requests.get(f"{BASE_URL}/store/stores/", timeout=10)
        res.raise_for_status()
        stores = res.json()
        return [store["id"] for store in stores]
    except Exception as e:
        print(f"❌ Failed to fetch store IDs: {e}")
        return []

def warm_up():
    print("🔥 Starting warm-up...")
    store_ids = get_all_store_ids()

    urls = [
        "/store/products/",
        "/store/categories/",
        "/store/orders/"
    ]

    for store_id in store_ids:
        urls.append(f"/store/stores/{store_id}/")
        urls.append(f"/store/storecategories/?store_id={store_id}")

    for path in urls:
        url = f"{BASE_URL}{path}"
        try:
            print(f"🌐 Warming: {url}")
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                print(f"✅ Cached: {path}")
            else:
                print(f"⚠️ Failed {path} - status {res.status_code}")
        except Exception as e:
            print(f"❌ Error on {path}: {e}")

if __name__ == "__main__":
    warm_up()
