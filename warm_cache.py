import os
import django
import requests
from django.conf import settings

# ✅ إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dawarmarket.settings')
django.setup()

from store.models import Store, StoreCategory, Product

BASE_URL = "https://dawarmarket.com"

STATIC_URLS = [
    "/store/stores/",
    "/store/products/",
    "/store/categories/",
    "/store/orders/",
]

def build_dynamic_urls():
    dynamic_urls = []
    store_ids = Store.objects.values_list('id', flat=True)

    for store_id in store_ids:
        # روابط المتجر
        dynamic_urls.append(f"/store/stores/{store_id}/")
        dynamic_urls.append(f"/store/storecategories/?store_id={store_id}")

        # روابط المنتجات داخل المتجر (من خلال الأقسام)
        store_category_ids = StoreCategory.objects.filter(store_id=store_id).values_list('id', flat=True)
        product_ids = Product.objects.filter(store_category_id__in=store_category_ids).values_list('id', flat=True)

        for product_id in product_ids:
            dynamic_urls.append(f"/store/products/{product_id}/")

    return dynamic_urls

def warm_up():
    urls_to_warm = STATIC_URLS + build_dynamic_urls()

    for path in urls_to_warm:
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
