import django_filters
from .models import Product,Store,Category
from django.db import models

import django_filters
from store.models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='lte')
    title = django_filters.CharFilter(field_name="title", lookup_expr='icontains')
    store_name = django_filters.CharFilter(field_name="store__name", lookup_expr='icontains')
    store = django_filters.NumberFilter(field_name="store__id")
    store_category = django_filters.NumberFilter(field_name="store_category__id")

    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    available = django_filters.BooleanFilter(method='filter_available')

    class Meta:
        model = Product
        fields = ['title', 'store_name', 'min_price', 'max_price', 'store', 'store_category', 'has_discount', 'available']

    def filter_has_discount(self, queryset, name, value):
        if value is True:
            return queryset.filter(price_after_discount__lt=django_filters.F('unit_price'))
        elif value is False:
            return queryset.filter(price_after_discount=django_filters.F('unit_price'))
        return queryset

    def filter_available(self, queryset, name, value):
        if isinstance(value, bool):
            return queryset.filter(available=value)
        return queryset




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





