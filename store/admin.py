from django.contrib import admin, messages
from django.db.models.aggregates import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse, path
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.utils.formats import date_format
from django.forms import BaseInlineFormSet
from django.template.response import TemplateResponse
from django.shortcuts import redirect

from . import models

# ✅ ProductSize Inline
class ProductSizeInline(admin.TabularInline):
    model = models.ProductSize
    extra = 1
    fields = ['size_name', 'size_type','price', 'price_after_discount', 'is_available']
    list_editable = ['price', 'price_after_discount', 'is_available']

# ✅ Product Admin (بدون unit_price و price_after_discount مباشرة)
@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['title']}
    list_display = ['title', 'store', 'available', 'image_preview']
    list_filter = ['store', 'available']
    list_per_page = 10
    list_select_related = ['store']
    search_fields = ['title']
    inlines = [ProductSizeInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />',
                               obj.image.url.replace('/upload/', '/upload/w_100,q_auto,f_auto/'))
        return "No Image"
    image_preview.short_description = "Image"

# ✅ CartItem admin تسجيل فقط
admin.site.register(models.CartItem)

# ✅ StoreCategory Admin
@admin.register(models.StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'image_preview', 'products_count']
    list_select_related = ['store']
    search_fields = ['name', 'store__name']
    list_per_page = 20

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />',
                               obj.image.url.replace('/upload/', '/upload/w_100,q_auto,f_auto/'))
        return "No Image"
    image_preview.short_description = "Image"

    @admin.display(ordering='products_count')
    def products_count(self, store_category):
        url = reverse('admin:store_product_changelist') + '?' + urlencode({'store_category__id': str(store_category.id)})
        return format_html('<a href="{}">{} Products</a>', url, store_category.products_count or 0)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_count=Count('products', distinct=True))

# ✅ Store Admin
@admin.register(models.Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'image_preview', 'products_count']
    list_select_related = ['category']
    search_fields = ['name']
    list_per_page = 20

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />',
                               obj.image.url.replace('/upload/', '/upload/w_100,q_auto,f_auto/'))
        return "No Image"
    image_preview.short_description = "Image"

    @admin.display(ordering='products_count')
    def products_count(self, store):
        url = reverse('admin:store_product_changelist') + '?' + urlencode({'store__id': str(store.id)})
        return format_html('<a href="{}">{} Products</a>', url, store.products_count or 0)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_count=Count('products', distinct=True))

# ✅ Category Admin
@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview', 'stores_count']
    search_fields = ['name']
    list_per_page = 20

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50px" style="border-radius: 5px;" />',
                               obj.image.url.replace('/upload/', '/upload/w_100,q_auto,f_auto/'))
        return "No Image"
    image_preview.short_description = "Image"

    @admin.display(ordering='stores_count')
    def stores_count(self, category):
        url = reverse('admin:store_store_changelist') + '?' + urlencode({'category__id': str(category.id)})
        return format_html('<a href="{}">{} Stores</a>', url, getattr(category, 'stores_count', 0))

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(stores_count=Count('stores'))

# ✅ User Admin
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

# ✅ OrderItem Inline
class OrderItemInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        seen_items = {}
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                product_size = form.cleaned_data['product_size']
                if product_size in seen_items:
                    form.cleaned_data['DELETE'] = True
                else:
                    seen_items[product_size] = form.instance

class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    formset = OrderItemInlineFormset
    extra = 1
    fields = ['product_size', 'quantity', 'price_display', 'total_price_display']
    readonly_fields = ['price_display', 'total_price_display']

    def price_display(self, obj):
        try:
            return f"{obj.unit_price:.2f} EGP"
        except:
            return "-"

    def total_price_display(self, obj):
        try:
            return f"{obj.quantity * obj.unit_price:.2f} EGP"
        except:
            return "-"

# ✅ Order Admin
@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    inlines = [OrderItemInline]
    list_display = ['id', 'formatted_placed_at', 'customer_info', 'order_status', 'total_price_display']
    list_select_related = ['customer']
    search_fields = ['id', 'customer__phone', 'customer__full_name']
    ordering = ['-placed_at']
    list_per_page = 20
    list_filter = ['order_status']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items__product_size')

    @admin.display(description="وقت الطلب")
    def formatted_placed_at(self, obj):
        return date_format(localtime(obj.placed_at), format='DATETIME_FORMAT', use_l10n=True)

    @admin.display(ordering='customer')
    def customer_info(self, order):
        address = order.customer.address or "—"
        landmark = order.customer.near_mark or "—"
        return format_html("<strong>{}</strong><br>📞 {}<br>📍 {}<br>📌 {}",
                           order.customer.full_name, order.customer.phone, address, landmark)

    @admin.display(ordering='total_price', description="Total Price")
    def total_price_display(self, order):
        return format_html("<strong>{:.2f} EGP</strong>", float(order.total_price or 0))

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.calculate_total_price(save=True)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/print/', self.admin_site.admin_view(self.print_order_view), name='print-order'),
            path('check-new-orders/', self.admin_site.admin_view(self.check_new_orders), name="check-new-orders"),
            path('update-order-total/<int:order_id>/', self.admin_site.admin_view(self.update_order_total), name="update-order-total"),
        ]
        return custom_urls + urls

    def check_new_orders(self, request):
        count = models.Order.objects.filter(order_status__iexact="pending").count()
        return JsonResponse({"new_orders": count})

    def update_order_total(self, request, order_id):
        try:
            order = models.Order.objects.get(id=order_id)
            return JsonResponse({"total_price": float(order.total_price)})
        except models.Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)

    def print_order_view(self, request, object_id):
        try:
            order = models.Order.objects.select_related('customer').prefetch_related('items__product_size').get(pk=object_id)
            context = {
                'order': order,
                'title': f'Order #{order.id}',
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, order),
            }
            return TemplateResponse(request, 'admin/store/order_print.html', context)
        except models.Order.DoesNotExist:
            messages.error(request, f"الطلب رقم {object_id} غير موجود")
            return redirect(reverse('admin:store_order_changelist'))

    class Media:
        js = (
            'rest_framework/js/auto-refresh.js',
            'admin/js/order-print-button.js',
            'admin/js/fix-tabs.js',
        )
