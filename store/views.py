from django.shortcuts import get_object_or_404
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.decorators import action

from django.db.models import Prefetch

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .filters import ProductFilter, StoreFilter, CategoryFilter
from .pagination import DefaultPagination
from .models import Product, Store, OrderItem, Cart, CartItem, Order, User, Category, StoreCategory
from .serializers import (
    ProductSerializer, StoreSerializer, CartSerializer, CartItemSerializer, 
    AddCartItemSerializer, OrderSerializer, CreateOrderSerializer, 
    UpdateCartItemSerializer, UpdateOrderSerializer, CategorySerializer, StoreCategorySerializer
)
from .permissions import IsAdminOrReadOnly, IsOrderOwnerOrAdmin


@method_decorator(cache_page(60), name='retrieve')      # ← دقيقة واحدة
@method_decorator(cache_page(60 * 5), name='list')       # ← 5 دقايق
class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination

    search_fields = ['title', 'description', 'store__name']
    ordering_fields = ['unit_price', 'last_update', 'id']

    

    def get_queryset(self):
        return Product.objects.select_related('store', 'store_category').only(
            'id', 'title', 'unit_price', 'price_after_discount', 'available', 'store_id', 'store_category_id', 'image'
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

        # أول مرة → شغل الاستعلام العادي
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 5)  # 5 دقايق
        print(f"⏱ Product list from DB in {time.time() - start:.3f}s")
        return Response(response.data)



    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).exists():
            return Response(
                {'error': 'Product cannot be deleted because it is associated with an order item.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        import time
        from django.core.cache import cache

        start = time.time()
        product_id = kwargs.get('pk')
        cache_key = f"product_detail:{product_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ Product #{product_id} from CACHE in {time.time() - start:.3f}s")
            return Response(cached_data)

        # لو مش متخزّن → استعلام عادي
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 5)  # 5 دقايق
        print(f"⏱ Product #{product_id} from DB in {time.time() - start:.3f}s")
        return Response(response.data)



from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page



from rest_framework.response import Response
from django.core.cache import cache

@method_decorator(cache_page(60), name='retrieve')
@method_decorator(cache_page(60 * 5), name='list')
class StoreViewSet(ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'category__name']
    ordering_fields = ['name', 'created_at']

    from django.db.models import Prefetch

    def get_queryset(self):
        # استرجاع بيانات أخف قدر الإمكان
        return Store.objects.select_related('category').only(
            'id', 'name', 'description', 'opens_at', 'close_at', 'max_discount', 'image', 'category_id'
        ).prefetch_related(
            Prefetch(
                'store_categories',
                queryset=StoreCategory.objects.only('id', 'name', 'store_id').prefetch_related(
                    Prefetch(
                        'products',
                        queryset=Product.objects.only(
                            'id', 'title', 'unit_price', 'price_after_discount', 'image', 'store_category_id'
                        )
                    )
                )
            )
        )





    def get_serializer_context(self):
        return {'request': self.request}

    def list(self, request, *args, **kwargs):
        import time
        start = time.time()

        cache_key = f"store_categories:{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached:
            print(f"✅ Returned store categories from CACHE in {time.time() - start:.3f} sec")
            return Response(cached)

        print("📡 Not in cache, querying DB...")
        queryset = self.filter_queryset(self.get_queryset())

        t1 = time.time()
        serializer = self.get_serializer(queryset, many=True)
        t2 = time.time()

        data = serializer.data
        cache.set(cache_key, data, timeout=300)

        print(f"⏱ QuerySet took {t1 - start:.3f} sec")
        print(f"⏱ Serialization took {t2 - t1:.3f} sec")
        print(f"⏱ Total StoreCategory API time: {time.time() - start:.3f} sec")

        return Response(data)
    
    
    

    
    def retrieve(self, request, *args, **kwargs):
        import time
        from django.core.cache import cache
        from django.db.models import Prefetch

        start = time.time()
        store_id = kwargs.get('pk')
        cache_key = f"store_detail:{store_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ Store #{store_id} from CACHE in {time.time() - start:.3f}s")
            return Response(cached_data)

        # بدل ما نستدعي super().retrieve، نجهّز البيانات يدويًا ونستخدم نفس logic
        try:
            store = Store.objects.select_related('category') \
                .only(
                    'id', 'name', 'description', 'opens_at', 'close_at', 'max_discount', 'image', 'category_id',
                    'category__id', 'category__name', 'category__image'
                ) \
                .prefetch_related(
                    Prefetch(
                        'store_categories',
                        queryset=StoreCategory.objects.only('id', 'name', 'store_id').prefetch_related(
                            Prefetch(
                                'products',
                                queryset=Product.objects.only(
                                    'id', 'title', 'unit_price', 'price_after_discount',
                                    'image', 'store_category_id', 'available'
                                )
                            )
                        )
                    )
                ).get(pk=store_id)

        except Store.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        serializer = StoreSerializer(store, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=300)

        print(f"⏱ Store #{store_id} from DB in {time.time() - start:.3f}s")
        return Response(data)







@method_decorator(cache_page(60), name='retrieve')
@method_decorator(cache_page(60 * 5), name='list')
class StoreCategoryViewSet(ModelViewSet):
    serializer_class = StoreCategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['store_id']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    
    

    
    
    def get_queryset(self):
        store_id = self.request.query_params.get('store_id')
        if store_id:
            return StoreCategory.objects.filter(store_id=store_id).prefetch_related(
                Prefetch(
                    'products',
                    queryset=Product.objects.only(
                        'id', 'title', 'unit_price', 'price_after_discount', 'image', 'store_category_id'
                    )
                )
            )
        return StoreCategory.objects.all().select_related('store')
    
    
    def list(self, request, *args, **kwargs):
        import time
        start = time.time()

        store_id = request.query_params.get('store_id')
        cache_key = f"store_categories:store_id:{store_id}" if store_id else f"store_categories:all"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ StoreCategory list from CACHE in {time.time() - start:.3f}s")
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        print(f"⏱ StoreCategory list from DB in {time.time() - start:.3f}s")
        return response



    


class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product')

    def create(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related('product', 'cart')

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import time

@method_decorator(cache_page(60 * 3), name='list')       # كاش 3 دقايق لقائمة الأوردرات
@method_decorator(cache_page(60), name='retrieve')       # كاش دقيقة واحدة لتفاصيل الأوردر
class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsOrderOwnerOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data, context={'user_id': request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        base_qs = Order.objects.select_related('customer').only(
            'id', 'customer_id', 'order_status', 'placed_at'
        ).prefetch_related(
            'items__product__store',
            'items__product'
        )
        return base_qs if self.request.user.is_staff else base_qs.filter(customer=self.request.user)

    def list(self, request, *args, **kwargs):
        start = time.time()
        response = super().list(request, *args, **kwargs)
        print(f"⏱ Orders LIST took {time.time() - start:.3f} sec")
        return response

    def retrieve(self, request, *args, **kwargs):
        start = time.time()
        response = super().retrieve(request, *args, **kwargs)
        print(f"⏱ Order RETRIEVE took {time.time() - start:.3f} sec")
        return response

    def destroy(self, request, *args, **kwargs):
        order = get_object_or_404(Order, id=kwargs['pk'], customer=request.user)
        if order.order_status != Order.ORDER_STATUS_PENDING:
            return Response({'error': 'You can only delete orders that are pending.'}, status=status.HTTP_403_FORBIDDEN)
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


