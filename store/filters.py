import django_filters
from .models import Product,Store,Category

class ProductFilter(django_filters.FilterSet):
    # فلترة السعر الأدنى
    min_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='gte')
    # فلترة السعر الأعلى
    max_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='lte')
    # البحث في العنوان باستخدام contains (غير حساس لحالة الأحرف)
    title = django_filters.CharFilter(field_name="title", lookup_expr='icontains')
    # البحث باستخدام اسم المتجر
    store_name = django_filters.CharFilter(field_name="store__name", lookup_expr='icontains')
    
    class Meta:
        model = Product
        fields = ['title', 'store_name', 'min_price', 'max_price']




class StoreFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')
    category = django_filters.CharFilter(field_name="category__name", lookup_expr='icontains')
    
    class Meta:
        model = Store
        fields = ['name', 'category']




class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')
    
    class Meta:
        model = Category
        fields = ['name']
