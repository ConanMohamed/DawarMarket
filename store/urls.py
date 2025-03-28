from django.urls import path
from rest_framework_nested import routers

from . import views



router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')
router.register('stores', views.StoreViewSet, basename='stores')
router.register('cart', views.CartViewSet, basename='carts')
router.register('orders', views.OrderViewSet, basename='orders')
router.register('categories', views.CategoryViewSet, basename='categories')
router.register('storecategories', views.StoreCategoryViewSet, basename='storecategories')  # ✅ إضافة StoreCategoryViewSet

cart_item_router = routers.NestedSimpleRouter(router, 'cart', lookup='cart')
cart_item_router.register('items', views.CartItemViewSet, basename='cart-items')

urlpatterns = router.urls + cart_item_router.urls



urlpatterns += [
    path('delete-account/', views.delete_account_form, name='delete-account-form'),
]

