from .managers import UserManager
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from uuid import uuid4
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from decimal import Decimal


# ✅ User Model (المستخدم)
class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True, default='oo')
    near_mark = models.CharField(max_length=250, blank=True, null=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['email', 'full_name']

    username = None
    objects = UserManager()

    def __str__(self):
        return self.full_name


# ✅ Category Model
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = CloudinaryField('image', null=True, blank=True)

    def __str__(self):
        return self.name


# ✅ Store Model
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
    max_discount = models.DecimalField(
        max_digits=3, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True
    )

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


# ✅ Product Model
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
    available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.store.name}"

    class Meta:
        ordering = ['title']


# ✅ Cart Model
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"Cart of {self.user.full_name}"


# ✅ CartItem Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [['cart', 'product']]


# ✅ Order Model
class Order(models.Model):
    ORDER_STATUS_PENDING = 'Pending'
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
    notes = models.TextField(blank=True, null=True)


    def calculate_total_price(self, save=True):
        total = sum(item.quantity * item.unit_price for item in self.items.all())  # ✅ استخدم السعر المجمّد
        if self.total_price != total:
            self.total_price = total
            if save:
                super().save(update_fields=['total_price'])


    def __str__(self):
        return f"Order {self.id} - {self.customer.full_name}"

    class Meta:
        ordering = ['-placed_at']


# ✅ OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

   
            
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.unit_price = self.product.price_after_discount
        super().save(*args, **kwargs)
        if self.order:
            self.order.calculate_total_price()


    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.calculate_total_price()

    def __str__(self):
        return f"OrderItem {self.product.title} ({self.quantity})"
