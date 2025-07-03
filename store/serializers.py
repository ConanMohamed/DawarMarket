from decimal import Decimal

from djoser.serializers import (
    UserSerializer as BaseUserSerializer,
    UserCreateSerializer as BaseUserCreateSerializer,
)
from django.db import transaction
from django.utils.timezone import localtime
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import (
    Category,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductSize,
    Store,
    StoreCategory,
    User,
)

# -----------------------------------------------------------------------------
# ✅ Helper Serializers
# -----------------------------------------------------------------------------
class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = [
            "id",
            "size_name",
            "size_type",
            "price",
            "price_after_discount",
            "is_available",
        ]


# -----------------------------------------------------------------------------
# ✅ Store‑level Serializers
# -----------------------------------------------------------------------------
class StoreListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "image",
            "opens_at",
            "close_at",
            "max_discount",
            "category",
        ]


class CategorySerializer(serializers.ModelSerializer):
    total_stores = serializers.SerializerMethodField()
    stores = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'total_stores', 'stores', 'image']

    def get_total_stores(self, category):
        return category.stores.count()

    def get_stores(self, category):
        request = self.context.get('request')
        return [
            {
                'id': store.id,
                'name': store.name,
                'store_url': reverse('stores-detail', args=[store.id], request=request),
                'image': store.image.url if store.image else None
            }
            for store in category.stores.all()
        ]


class StoreCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreCategory
        fields = ["id", "name"]


class StoreSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    store_categories = StoreCategorySerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "description",
            "opens_at",
            "close_at",
            "max_discount",
            "category",
            "products_count",
            "image",
            "store_categories",
        ]

    def get_category(self, store: Store):
        return {
            "id": store.category.id,
            "name": store.category.name,
            "image": store.category.image.url if store.category.image else None,
        }

    def get_products_count(self, store: Store):
        return store.products.count()

    def get_image(self, obj):
        if obj.image:
            try:
                return obj.image.url.replace(
                    "/upload/", "/upload/w_600,h_600,c_fit,q_auto:eco,f_auto/"
                )
            except Exception:
                return None
        return None


# -----------------------------------------------------------------------------
# ✅ Product‑level Serializers
# -----------------------------------------------------------------------------
class LightweightProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "title", "description", "sizes", "image", "available"]

    def get_image(self, obj):
        if obj.image:
            try:
                return obj.image.url.replace(
                    "/upload/", "/upload/w_600,h_600,c_fit,q_auto:eco,f_auto/"
                )
            except Exception:
                return None
        return None


class SimpleProductSerializer(serializers.ModelSerializer):
    """Returns basic info + min price among sizes"""

    image = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "min_price", "image"]

    def get_image(self, obj):
        if obj.image:
            try:
                return obj.image.url.replace(
                    "/upload/", "/upload/w_600,h_600,c_fit,q_auto:eco,f_auto/"
                )
            except Exception:
                return None
        return None

    def get_min_price(self, obj):
        first_size = obj.sizes.filter(is_available=True).order_by("price").first()
        if first_size:
            return first_size.price_after_discount or first_size.price
        return None


class ProductSerializer(serializers.ModelSerializer):
    store_category = StoreCategorySerializer()
    image = serializers.SerializerMethodField()
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "store",
            "store_category",
            "sizes",
            "image",
            "available",
        ]

    def get_image(self, obj):
        if obj.image:
            try:
                return obj.image.url.replace(
                    "/upload/", "/upload/w_600,h_600,c_fit,q_auto:eco,f_auto/"
                )
            except Exception:
                return None
        return None


# -----------------------------------------------------------------------------
# ✅ Cart Serializers
# -----------------------------------------------------------------------------
class CartItemSerializer(serializers.ModelSerializer):
    # ⬅️ بيانات المنتج الأساسي
    product_id   = serializers.IntegerField(source='product_size.product.id', read_only=True)
    product_name = serializers.CharField(source='product_size.product.title', read_only=True)
    product_image = serializers.SerializerMethodField()

    # ⬅️ بيانات المقاس
    size_name = serializers.CharField(source='product_size.size_name', read_only=True)
    size_type = serializers.CharField(source='product_size.size_type', read_only=True)

    # ⬅️ الأسعار
    unit_price   = serializers.SerializerMethodField()
    discount_pct = serializers.SerializerMethodField()
    total_price  = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = [
            'id',
            'product_id', 'product_name', 'product_image',
            'size_name', 'size_type',
            'quantity',
            'unit_price', 'discount_pct', 'total_price',
        ]

    # ---------- helpers ----------
    def get_product_image(self, obj):
        img = obj.product_size.product.image
        if img:
            return img.url.replace('/upload/', '/upload/w_150,h_150,c_fit,q_auto,f_auto/')
        return None

    def get_unit_price(self, obj):
        ps = obj.product_size
        return ps.price_after_discount or ps.price

    def get_discount_pct(self, obj):
        ps = obj.product_size
        if ps.price and ps.price_after_discount:
            pct = 100 * (ps.price - ps.price_after_discount) / ps.price
            return round(pct)
        return 0

    def get_total_price(self, obj):
        return obj.quantity * self.get_unit_price(obj)



class CartSerializer(serializers.ModelSerializer):
    id          = serializers.UUIDField(read_only=True)
    items       = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    items_total = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model  = Cart
        fields = [
            'id',
            'items',
            'items_count',
            'items_total',
            'total_price',
        ]

    # ---------- helpers ----------
    def get_items_count(self, cart):
        return cart.items.count()

    def get_items_total(self, cart):
        return sum(item.quantity *
                   (item.product_size.price_after_discount or item.product_size.price)
                   for item in cart.items.all())


    def get_total_price(self, cart):
        return self.get_items_total(cart) 
    
    


class AddCartItemSerializer(serializers.ModelSerializer):
    """Add product_size to cart"""

    id = serializers.IntegerField(read_only=True)
    product_size = serializers.PrimaryKeyRelatedField(
        queryset=ProductSize.objects.filter(is_available=True)
    )

    class Meta:
        model = CartItem
        fields = ["id", "product_size", "quantity"]

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        product_size: ProductSize = self.validated_data["product_size"]
        quantity = self.validated_data["quantity"]

        cart_item, created = CartItem.objects.get_or_create(
            cart_id=cart_id,
            product_size=product_size,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        self.instance = cart_item
        return cart_item


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


# -----------------------------------------------------------------------------
# ✅ Order Serializers
# -----------------------------------------------------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product_name  = serializers.CharField(
        source='product_size.product.title',
        read_only=True
    )
    product_image = serializers.SerializerMethodField()
    total_item_price = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = [
            'id',
            'product_size',
            'product_name',     # ← الجديد
            'product_image',    # ← اختياري
            'quantity',
            'total_item_price',
        ]

    # صورة مصغّرة (اختياري)
    def get_product_image(self, obj):
        img = obj.product_size.product.image
        if img:
            return img.url.replace(
                '/upload/', '/upload/w_150,h_150,c_fit,q_auto,f_auto/'
            )
        return None

    def get_total_item_price(self, obj):
        return float(obj.quantity * obj.unit_price)


class OrderSerializer(serializers.ModelSerializer):
    placed_at = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    customer = serializers.CharField(source="customer.full_name")
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    store_name = serializers.SerializerMethodField()
    store_image = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_status",
            "placed_at",
            "customer",
            "items",
            "total_price",
            "notes",
            "store_name",
            "store_image",
        ]

    def get_placed_at(self, obj):
        return localtime(obj.placed_at).strftime("%Y-%m-%d %H:%M")

   
    def get_store_name(self, order):
        first_item = order.items.first()
        return first_item.product_size.product.store.name if first_item else None

    def get_store_image(self, obj):
        request = self.context.get("request")
        first_item = obj.items.first()
        if first_item and first_item.product_size.product.store.image:
            return request.build_absolute_uri(first_item.product_size.product.store.image.url)
        return None



class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    notes   = serializers.CharField(required=False, allow_blank=True, max_length=2_000)

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart with the given ID was found.')
        if not CartItem.objects.filter(cart_id=cart_id).exists():
            raise serializers.ValidationError('The cart is empty.')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id  = self.validated_data['cart_id']
            notes    = self.validated_data.get('notes', '')
            customer = User.objects.get(id=self.context['user_id'])

            # ➊ إنشاء الطلب
            order = Order.objects.create(customer=customer, notes=notes)

            # ➋ جلب عناصر السلة مع الـ product_size
            cart_items = (
                CartItem.objects
                .filter(cart_id=cart_id)
                .select_related('product_size')
            )

            # ➌ بناء عناصر الطلب
            order_items = [
                OrderItem(
                    order      = order,
                    product_size = item.product_size,
                    quantity   = item.quantity,
                    unit_price = item.product_size.price_after_discount
                                 or item.product_size.price   # السعر المُجمَّد وقت الطلب
                )
                for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)

            # ➍ حساب إجمالي الطلب ثم حذف السلة
            order.calculate_total_price(save=True)
            Cart.objects.filter(pk=cart_id).delete()
            return order




class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_status']


class UserCreateSerializer(BaseUserCreateSerializer):
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'full_name', 'phone', 'password', 'confirm_password', 'address', 'near_mark']

    def validate(self, data):
        if data['password'] != data.pop('confirm_password', None):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        return super().create(validated_data)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'full_name', 'phone', 'address', 'near_mark']