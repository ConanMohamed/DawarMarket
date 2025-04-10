import django_filters
from .models import Product,Store,Category
from django.db import models

class ProductFilter(django_filters.FilterSet):
    available = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields = ['available']

    def filter_available(self, queryset, name, value):
        return queryset.filter(available=value)




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





