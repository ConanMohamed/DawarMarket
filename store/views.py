from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import (
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .filters import CategoryFilter, ProductFilter, StoreFilter
from .models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    ProductSize,
    Store,
    StoreCategory,
    User,
)
from .pagination import DefaultPagination
from .permissions import IsAdminOrReadOnly, IsOrderOwnerOrAdmin
from .serializers import (
    AddCartItemSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    CreateOrderSerializer,
    OrderSerializer,
    ProductSerializer,
    StoreCategorySerializer,
    StoreSerializer,
    UpdateCartItemSerializer,
    UpdateOrderSerializer,
)

# -----------------------------------------------------------------------------
# ✅ ProductViewSet
# -----------------------------------------------------------------------------

@method_decorator(cache_page(60), name="retrieve")  # دقيقة واحدة
@method_decorator(cache_page(60 * 5), name="list")  # 5 دقائق
class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination

    search_fields = ["title", "description", "store__name"]
    ordering_fields = ["id", "title"]

    def get_queryset(self):
        """Return lightweight product list and prefetch sizes."""
        return (
            Product.objects.select_related("store", "store_category")
            .only("id", "title", "available", "store_id", "store_category_id", "image")
            .prefetch_related("sizes")
        )

    def list(self, request, *args, **kwargs):
        import time
        from django.core.cache import cache

        start = time.time()
        cache_key = f"product_list:{request.get_full_path()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ Product list from CACHE in {time.time() - start:.3f}s")
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 5)
        print(f"⏱ Product list from DB in {time.time() - start:.3f}s")
        return Response(response.data)

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, *args, **kwargs):
        # لا يمكن حذف منتج إذا كان مرتبطًا بعنصر طلب
        if OrderItem.objects.filter(product_size__product_id=kwargs["pk"]).exists():
            return Response(
                {
                    "error": "Product cannot be deleted because it is associated with an order item.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


# -----------------------------------------------------------------------------
# ✅ StoreViewSet
# -----------------------------------------------------------------------------

@method_decorator(cache_page(60), name="retrieve")
@method_decorator(cache_page(60 * 5), name="list")
class StoreViewSet(ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category"]
    search_fields = ["name", "category__name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return (
            Store.objects.select_related("category")
            .only(
                "id",
                "name",
                "description",
                "opens_at",
                "close_at",
                "max_discount",
                "image",
                "category_id",
            )
            .prefetch_related(
                Prefetch(
                    "store_categories",
                    queryset=StoreCategory.objects.only("id", "name", "store_id").prefetch_related(
                        Prefetch(
                            "products",
                            queryset=Product.objects.only(
                                "id", "title", "available", "image", "store_category_id"
                            ).prefetch_related("sizes")
                        )
                    ),
                )
            )
        )

    def get_serializer_context(self):
        return {"request": self.request}

    # Override list + retrieve with manual caching (كما كان في الكود الأصلي)

    def list(self, request, *args, **kwargs):
        import time
        from django.core.cache import cache

        start = time.time()
        cache_key = f"stores:{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached:
            print(f"✅ Store list from CACHE in {time.time() - start:.3f}s")
            return Response(cached)

        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        cache.set(cache_key, serializer.data, timeout=300)
        print(f"⏱ Store list from DB in {time.time() - start:.3f}s")
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        import time
        from django.core.cache import cache

        start = time.time()
        store_id = kwargs.get("pk")
        cache_key = f"store_detail:{store_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ Store #{store_id} from CACHE in {time.time() - start:.3f}s")
            return Response(cached_data)

        try:
            store = self.get_queryset().get(pk=store_id)
        except Store.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        serializer = self.get_serializer(store)
        cache.set(cache_key, serializer.data, timeout=300)
        print(f"⏱ Store #{store_id} from DB in {time.time() - start:.3f}s")
        return Response(serializer.data)


# -----------------------------------------------------------------------------
# ✅ StoreCategoryViewSet
# -----------------------------------------------------------------------------

@method_decorator(cache_page(60), name="retrieve")
@method_decorator(cache_page(60 * 5), name="list")
class StoreCategoryViewSet(ModelViewSet):
    serializer_class = StoreCategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["store_id"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        store_id = self.request.query_params.get("store_id")
        base_qs = StoreCategory.objects
        if store_id:
            base_qs = base_qs.filter(store_id=store_id)
        return base_qs.prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.only("id", "title", "available", "image", "store_category_id").prefetch_related(
                    "sizes"
                ),
            )
        )

    def list(self, request, *args, **kwargs):
        import time
        from django.core.cache import cache

        start = time.time()
        store_id = request.query_params.get("store_id")
        cache_key = f"store_categories:{store_id or 'all'}"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ StoreCategory list from CACHE in {time.time() - start:.3f}s")
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        print(f"⏱ StoreCategory list from DB in {time.time() - start:.3f}s")
        return response


# -----------------------------------------------------------------------------
# ✅ Cart & CartItem viewsets
# -----------------------------------------------------------------------------

class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related(
            "items__product_size__product"
        )

    def create(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}

    def get_queryset(self):
        return (
            CartItem.objects.filter(cart__user=self.request.user)
            .select_related("product_size__product", "cart")
        )


# -----------------------------------------------------------------------------
# ✅ OrderViewSet
# -----------------------------------------------------------------------------



from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import time

@method_decorator(cache_page(60 * 3), name="list")       # كاش 3 دقايق لقائمة الأوردرات
@method_decorator(cache_page(60), name="retrieve")       # كاش دقيقة واحدة لتفاصيل الأوردر
class OrderViewSet(ModelViewSet):
    
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [IsOrderOwnerOrAdmin]

    # --------- Create ----------
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={"user_id": request.user.id},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        out_serializer = OrderSerializer(order, context={"request": request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    # --------- Serializer Choice ----------
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        if self.request.method == "PATCH":
            return UpdateOrderSerializer
        return OrderSerializer

    # --------- Queryset ----------
    def get_queryset(self):
        qs = (
            Order.objects.select_related("customer")
            .only("id", "customer_id", "order_status", "placed_at", "total_price")
            .prefetch_related(
                "items__product_size__product__store",  # المتجر
                "items__product_size__product",         # المنتج
            )
        )
        return qs if self.request.user.is_staff else qs.filter(customer=self.request.user)

    # --------- List ----------
    def list(self, request, *args, **kwargs):
        import time

        start = time.time()
        response = super().list(request, *args, **kwargs)
        print(f"⏱ Orders LIST took {time.time() - start:.3f} sec")
        return response

    # --------- Retrieve ----------
    def retrieve(self, request, *args, **kwargs):
        import time

        start = time.time()
        response = super().retrieve(request, *args, **kwargs)
        print(f"⏱ Order RETRIEVE took {time.time() - start:.3f} sec")
        return response

    # --------- Destroy ----------
    def destroy(self, request, *args, **kwargs):
        order = get_object_or_404(Order, id=kwargs["pk"], customer=request.user)
        if order.order_status != Order.ORDER_STATUS_PENDING:
            return Response(
                {"error": "You can only delete orders that are pending."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


@method_decorator(cache_page(60), name='retrieve')
@method_decorator(cache_page(60 * 5), name='list')
class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        return Category.objects.prefetch_related('stores__category')


from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

def delete_account_form(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user:
            user.delete()
            return render(request, 'delete_success.html')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'delete_account_form.html')


