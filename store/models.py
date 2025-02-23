from .managers import UserManager  # استيراد UserManager الجديد

from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from uuid import uuid4
from django.utils.text import slugify


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
    image = models.ImageField(upload_to='categories/', null=True, blank=True)  # إضافة حقل الصورة

    def __str__(self):
        return self.name


class Store(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="stores")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(null=True, blank=True)
    opens_at = models.DateTimeField(null=True, blank=True)
    close_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='stores/', null=True, blank=True)  # إضافة حقل الصورة

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class StoreCategory(models.Model):
    name = models.CharField(max_length=255)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="store_categories")
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='store_categories/', null=True, blank=True)  # إضافة حقل الصورة

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
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    store_category = models.ForeignKey(StoreCategory, on_delete=models.CASCADE, related_name="products", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)  # ✅ إضافة الصورة

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
class Order(models.Model):
    ORDER_STATUS_PENDING = 'P'
    ORDER_STATUS_SHIPPED = 'S'
    ORDER_STATUS_DELIVERED = 'D'
    ORDER_STATUS_ACCEPTED = 'A'
    ORDER_STATUS_CHOICES = [
        (ORDER_STATUS_PENDING, 'Pending'),
        (ORDER_STATUS_SHIPPED, 'Shipped'),
        (ORDER_STATUS_DELIVERED, 'Delivered'),
        (ORDER_STATUS_ACCEPTED, 'Accepted'),
    ]

    placed_at = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=1, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_PENDING)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total_price(self, save=True):
        total = sum(item.quantity * item.unit_price for item in self.items.all())
        if self.total_price != total:  # تجنب الحفظ غير الضروري
            self.total_price = total
            if save:
                self.save(update_fields=['total_price'])

    def __str__(self):
        return f"Order {self.id} - {self.customer.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.unit_price:  # إذا لم يتم تحديد السعر، اجلبه من المنتج
            self.unit_price = self.product.unit_price  

        super().save(*args, **kwargs)  

        # تحديث السعر بعد حفظ العنصر
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
