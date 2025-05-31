from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from decimal import Decimal
from django.db import transaction
from django.db.models import Count
from rest_framework.reverse import reverse
from django.utils.timezone import localtime

from .models import Product, Cart, CartItem, Order, OrderItem, Store, Category, User, StoreCategory


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price', 'price_after_discount', 'available']


class StoreCategoryWithProductsSerializer(serializers.ModelSerializer):
    products = SimpleProductSerializer(many=True, read_only=True)

    class Meta:
        model = StoreCategory
        fields = ['id', 'name', 'products']


class StoreSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    store_categories = StoreCategoryWithProductsSerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            'id', 'name', 'description', 'opens_at', 'close_at', 'max_discount',
            'category', 'products_count', 'image', 'store_categories'
        ]

    def get_products_count(self, store: Store):
        return store.products.count()

    def get_image(self, obj):
        if obj.image:
            try:
                url = obj.image.url
                return url.replace('/upload/', '/upload/w_300,q_auto/')
            except:
                return None
        return None


class CategorySerializer(serializers.ModelSerializer):
    total_stores = serializers.SerializerMethodField()
    stores = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'total_stores', 'stores', 'image']

    def get_total_stores(self, category: Category):
        return category.stores.count()

    def get_stores(self, category: Category):
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
        fields = ['id', 'name', 'store', 'image']


class ProductSerializer(serializers.ModelSerializer):
    store_category = StoreCategorySerializer()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'unit_price', 'price_after_discount', 'store', 'store_category', 'image', 'available']

    def get_image(self, obj):
        if obj.image:
            try:
                url = obj.image.url
                return url.replace('/upload/', '/upload/w_300,q_auto/')
            except:
                return None
        return None


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.price_after_discount

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum(item.quantity * item.product.price_after_discount for item in cart.items.all())

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']


class AddCartItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product = self.validated_data['product']
        quantity = self.validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            cart_id=cart_id, product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        self.instance = cart_item
        return cart_item

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_item_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'total_item_price']

    def get_total_item_price(self, obj):
        return float(obj.quantity * obj.product.price_after_discount)


class OrderSerializer(serializers.ModelSerializer):
    placed_at = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    customer = serializers.CharField()
    total_price = serializers.SerializerMethodField()
    store_name = serializers.SerializerMethodField()
    store_image = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_status', 'placed_at', 'customer', 'items', 'total_price', 'store_name', 'store_image']

    def get_placed_at(self, obj):
        return localtime(obj.placed_at).strftime('%Y-%m-%d %H:%M')

    def get_total_price(self, obj):
        return sum(item.quantity * item.product.price_after_discount for item in obj.items.all())

    def get_store_name(self, obj):
        first_item = obj.items.first()
        return first_item.product.store.name if first_item else None

    def get_store_image(self, obj):
        request = self.context.get('request')
        first_item = obj.items.first()
        if first_item and first_item.product.store.image:
            return request.build_absolute_uri(first_item.product.store.image.url)
        return None


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart with the given ID was found.')
        if not CartItem.objects.filter(cart_id=cart_id).exists():
            raise serializers.ValidationError('The cart is empty.')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer = User.objects.get(id=self.context['user_id'])
            order = Order.objects.create(customer=customer)

            cart_items = CartItem.objects.filter(cart_id=cart_id).select_related('product')
            order_items = [
                OrderItem(order=order, product=item.product, quantity=item.quantity, unit_price=item.product.unit_price)
                for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
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
