import os
import django
import requests
import time

# ✅ إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dwarmarket.settings')
django.setup()

from store.models import Store  # لازم يكون بعد django.setup()

# ✅ العنوان الأساسي
BASE_URL = "https://dawarmarket.com"

# ✅ روابط ثابتة أولًا
URLS_TO_WARM = [
    "/store/stores/",
    "/store/products/",
    "/store/categories/",
    "/store/orders/",
]

# ✅ أضف روابط ديناميكية لكل متجر
for store_id in Store.objects.values_list("id", flat=True):
    URLS_TO_WARM.append(f"/store/stores/{store_id}/")
    URLS_TO_WARM.append(f"/store/storecategories/?store_id={store_id}")

# ✅ تشغيل الكاش السّاخن
def warm_up():
    for path in URLS_TO_WARM:
        url = f"{BASE_URL}{path}"
        try:
            print(f"🔥 Warming up {url}")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                print(f"✅ {path} cached successfully")
            else:
                print(f"⚠️ {path} failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Error warming {path}: {e}")

        time.sleep(2)  # ⏱️ استراحة بسيطة

if __name__ == "__main__":
    warm_up()
