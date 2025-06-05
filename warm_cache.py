import os
import django
import requests
import time
from django.conf import settings

# ✅ إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dawarmarket.settings')
django.setup()

BASE_URL = "https://dawarmarket.com"

# ✅ Endpoints المهمة
URLS_TO_WARM = [
    "/store/stores/",
    "/store/stores/1/",
    "/store/products/",
    "/store/categories/",
    "/store/storecategories/?store_id=1",
    "/store/orders/",
]

def wait_for_server():
    health_url = f"{BASE_URL}/store/categories/"
    for i in range(10):  # يحاول 10 مرات
        try:
            print(f"⏳ Checking if server is ready ({i+1}/10)...")
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        time.sleep(5)
    print("❌ Server did not become ready in time.")
    return False

def warm_up():
    if not wait_for_server():
        return

    for path in URLS_TO_WARM:
        url = f"{BASE_URL}{path}"
        try:
            print(f"🔥 Warming up {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {path} cached successfully")
            else:
                print(f"⚠️ {path} failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Error warming {path}: {e}")

if __name__ == "__main__":
    warm_up()
