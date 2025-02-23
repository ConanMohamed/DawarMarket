from django.contrib import admin, messages
from django.db.models.aggregates import Count
from django.db.models.query import QuerySet
from django.utils.html import format_html, urlencode
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from decimal import Decimal
from . import models

# Register CartItem model
admin.site.register(models.CartItem)

# Inventory Filter
class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [
            ('<10', 'Low')
        ]

    def queryset(self, request, queryset: QuerySet):
        if self.value() == '<10':
            return queryset.filter(inventory__lt=10)








# ✅ StoreCategory Admin - عرض الصورة
@admin.register(models.StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'image_preview', 'products_count']
    list_select_related = ['store']
    search_fields = ['name', 'store__name']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"

    @admin.display(ordering='products_count')
    def products_count(self, store_category):
        url = (
            reverse('admin:store_product_changelist')
            + '?'
            + urlencode({'store_category__id': str(store_category.id)})
        )
        return format_html('<a href="{}">{} Products</a>', url, store_category.products_count or 0)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count('products', distinct=True)
        )


# ✅ Store Admin - عرض الصورة
@admin.register(models.Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'image_preview', 'products_count']
    list_select_related = ['category']
    search_fields = ['name']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"

    @admin.display(ordering='products_count')
    def products_count(self, store):
        url = (
            reverse('admin:store_product_changelist')
            + '?'
            + urlencode({'store__id': str(store.id)})
        )
        return format_html('<a href="{}">{} Products</a>', url, store.products_count or 0)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count('products', distinct=True)
        )


# ✅ Category Admin - عرض الصورة
@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview', 'stores_count']
    search_fields = ['name']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"

    @admin.display(ordering='stores_count')
    def stores_count(self, category):
        url = (
            reverse('admin:store_store_changelist')
            + '?'
            + urlencode({'category__id': str(category.id)})
        )
        return format_html('<a href="{}">{} Stores</a>', url, getattr(category, 'stores_count', 0))

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            stores_count=Count('stores')
        )


# ✅ Product Admin - عرض الصورة
@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['title']}
    actions = ['clear_inventory']
    list_display = ['title', 'unit_price', 'inventory_status', 'store', 'image_preview']
    list_editable = ['unit_price']
    list_filter = ['store', 'last_update']
    list_per_page = 10
    list_select_related = ['store']
    search_fields = ['title']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"

    def inventory_status(self, product):
        return 'Low' if product.inventory < 10 else 'OK'

    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        if updated_count > 0:
            self.message_user(
                request,
                f'{updated_count} products were successfully updated.',
                messages.SUCCESS
            )
        else:
            self.message_user(request, 'No products updated.', messages.WARNING)


# User Admin
@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'full_name', 'phone', 'email', 'is_staff', 'is_active')
    search_fields = ('full_name', 'phone', 'email')
    ordering = ('full_name',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email', 'address', 'near_mark')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'full_name', 'email', 'address', 'near_mark', 'is_staff', 'is_active'),
        }),
    )

# Order Item Inline
class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price']
    readonly_fields = ['unit_price']

# Order Admin
@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    inlines = [OrderItemInline]
    list_display = ['id', 'placed_at', 'customer_info', 'total_price_display']
    list_select_related = ['customer']
    search_fields = ['id', 'customer__phone', 'customer__full_name']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_total_price()

    @admin.display(ordering='customer')
    def customer_info(self, order):
        address = order.customer.address if order.customer.address else "—"
        landmark = order.customer.near_mark if order.customer.near_mark else "—"
        return format_html(
            "<strong>{}</strong><br>📞 {}<br>📍 {}<br>📌 {}",
            order.customer.full_name,
            order.customer.phone,
            address,
            landmark
        )

    @admin.display(ordering='total_price', description="Total Price")
    def total_price_display(self, order):
        total = float(order.total_price or 0)
        return format_html("<strong>{} EGP</strong>", "{:.2f}".format(total))



