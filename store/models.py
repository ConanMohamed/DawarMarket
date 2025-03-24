from .managers import UserManager  # استيراد UserManager الجديد

from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from uuid import uuid4
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


# User Model (المستخدم)
class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True, default='oo')
    near_mark = models.CharField(max_length=250, blank=True, null=True)

    USERNAME_FIELD = 'phone'  # تسجيل الدخول برقم الهاتف
    REQUIRED_FIELDS = ['email', 'full_name']

    username = None  # حذف username نهائيًا

    objects = UserManager()  # استخدام الـ UserManager الجديد
    
    def __str__(self):
        return self.full_name


# Category Model (تصنيف المنتجات)
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = CloudinaryField('image', null=True, blank=True)

    def __str__(self):
        return self.name


class Store(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="stores")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(null=True, blank=True)
    opens_at = models.TimeField(null=True, blank=True)
    close_at = models.TimeField(null=True, blank=True)
    image = CloudinaryField('image', null=True, blank=True)
    max_discount = models.DecimalField(max_digits=3,decimal_places=1,blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class StoreCategory(models.Model):
    name = models.CharField(max_length=255)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="store_categories")
    created_at = models.DateTimeField(auto_now_add=True)
    image = CloudinaryField('image', null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.store.name}"

    class Meta:
        unique_together = [['name', 'store']]


# Product Model (منتج مرتبط بمحل معين)
class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(1)])
    price_after_discount = models.DecimalField(max_digits=6, decimal_places=2)
    last_update = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    store_category = models.ForeignKey(StoreCategory, on_delete=models.CASCADE, related_name="products", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = CloudinaryField('image', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.store.name}"

    class Meta:
        ordering = ['title']


# Cart Model (عربة التسوق لكل مستخدم)
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")  # ⬅️ تعديل لجعل كل مستخدم يمتلك عربة واحدة فقط

    def __str__(self):
        return f"Cart of {self.user.full_name}"


# CartItem Model (منتجات داخل كارت التسوق)
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [['cart', 'product']]


# Order Model (الطلب مرتبط بالمحل)
from django.db import models
from django.conf import settings
from decimal import Decimal

class Order(models.Model):
    ORDER_STATUS_PENDING = 'pending'
    ORDER_STATUS_SHIPPED = 'Shipped'
    ORDER_STATUS_DELIVERED = 'delivered'
    ORDER_STATUS_ACCEPTED = 'accepted'
    ORDER_STATUS_CANCELED = 'canceled'

    ORDER_STATUS_CHOICES = [
        (ORDER_STATUS_PENDING, 'Pending'),
        (ORDER_STATUS_SHIPPED, 'Shipped'),
        (ORDER_STATUS_DELIVERED, 'Delivered'),
        (ORDER_STATUS_ACCEPTED, 'Accepted'),
        (ORDER_STATUS_CANCELED, 'Canceled')
    ]

    placed_at = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=12, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_PENDING)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total_price(self, save=True):
        """حساب `total_price` بناءً على `price_after_discount` بدلاً من `unit_price`"""
        total = sum(item.quantity * item.product.price_after_discount for item in self.items.all())  # ✅ استخدام price_after_discount

        if self.total_price != total:  # ✅ تجنب الحفظ إذا لم تتغير القيمة
            self.total_price = total
            if save:
                super().save(update_fields=['total_price'])  # ✅ تحديث `total_price` فقط بدون استدعاء `save()` كامل



    def __str__(self):
        return f"Order {self.id} - {self.customer.full_name}"
        
    class Meta:
      ordering = ['-placed_at']




class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, editable=False)  # لا يمكن تعديله يدويًا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.unit_price:  # تأكد من استخدام السعر بعد الخصم
            self.unit_price = self.product.price_after_discount  
        
        super().save(*args, **kwargs)

        # تحديث السعر بعد الحفظ
        if self.order:
            self.order.calculate_total_price()


    def delete(self, *args, **kwargs):
        order = self.order  # احفظ الطلب قبل الحذف
        super().delete(*args, **kwargs)
        
        # تحديث السعر بعد الحذف
        if order:
            order.calculate_total_price()

    def __str__(self):
        return f"OrderItem {self.product.title} ({self.quantity})"

