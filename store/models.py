from uuid import uuid4
from decimal import Decimal

from cloudinary.models import CloudinaryField
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify

from .managers import UserManager

# -----------------------------------------------------------------------------
# ✅ User Model (المستخدم)
# -----------------------------------------------------------------------------
class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True)
    near_mark = models.CharField(max_length=250, blank=True, null=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["email", "full_name"]

    username = None
    objects = UserManager()

    def __str__(self):
        return self.full_name


# -----------------------------------------------------------------------------
# ✅ Category Model
# -----------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = CloudinaryField("image", null=True, blank=True)

    def __str__(self):
        return self.name


# -----------------------------------------------------------------------------
# ✅ Store Model
# -----------------------------------------------------------------------------
class Store(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="stores")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(null=True, blank=True)
    opens_at = models.TimeField(null=True, blank=True)
    close_at = models.TimeField(null=True, blank=True)
    image = CloudinaryField("image", null=True, blank=True)
    max_discount = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class StoreCategory(models.Model):
    name = models.CharField(max_length=255)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="store_categories")
    created_at = models.DateTimeField(auto_now_add=True)
    image = CloudinaryField("image", null=True, blank=True)

    class Meta:
        unique_together = [["name", "store"]]

    def __str__(self):
        return f"{self.name} - {self.store.name}"


# -----------------------------------------------------------------------------
# ✅ Product & ProductSize Models
# -----------------------------------------------------------------------------
SIZE_TYPE_CHOICES = [
    ("piece", "عدد قطع / برجر"),
    ("diameter", "قطر بيتزا (سم)"),
    ("default", "افتراضي"),
]


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    store_category = models.ForeignKey(
        StoreCategory,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = CloudinaryField("image", null=True, blank=True)
    available = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

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


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size_name = models.CharField(max_length=50)  # e.g. "Single", "Double", "Small"
    size_type = models.CharField(max_length=20, choices=SIZE_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_after_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["product", "size_name"]]
        ordering = ["product","size_name"]

    def __str__(self):
        return f"{self.product.title} - {self.size_name}"


# -----------------------------------------------------------------------------
# ✅ Cart & CartItem Models
# -----------------------------------------------------------------------------
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.full_name}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [["cart", "product_size"]]

    @property
    def unit_price(self):
        return self.product_size.price_after_discount or self.product_size.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_size} x {self.quantity}"


# -----------------------------------------------------------------------------
# ✅ Order & OrderItem Models
# -----------------------------------------------------------------------------
class Order(models.Model):
    ORDER_STATUS_PENDING = "Pending"
    ORDER_STATUS_SHIPPED = "Shipped"
    ORDER_STATUS_DELIVERED = "Delivered"
    ORDER_STATUS_ACCEPTED = "Accepted"
    ORDER_STATUS_CANCELED = "Canceled"

    ORDER_STATUS_CHOICES = [
        (ORDER_STATUS_PENDING, "Pending"),
        (ORDER_STATUS_SHIPPED, "Shipped"),
        (ORDER_STATUS_DELIVERED, "Delivered"),
        (ORDER_STATUS_ACCEPTED, "Accepted"),
        (ORDER_STATUS_CANCELED, "Canceled"),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    placed_at = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=12, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-placed_at"]

    def calculate_total_price(self, save=True):
        total = sum(item.quantity * item.unit_price for item in self.items.all())
        if self.total_price != total:
            self.total_price = total
            if save:
                super().save(update_fields=["total_price"])

    def __str__(self):
        return f"Order {self.id} - {self.customer.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_size = models.ForeignKey(ProductSize, on_delete=models.PROTECT, related_name="orderitems")
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.unit_price = self.product_size.price_after_discount or self.product_size.price
        super().save(*args, **kwargs)
        if self.order:
            self.order.calculate_total_price()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.calculate_total_price()

    def __str__(self):
        return f"{self.product_size} (x{self.quantity})"
