from rest_framework.pagination import PageNumberPagination



class DefaultPagination(PageNumberPagination):
    page_size = 10  # عدد العناصر في كل صفحة
