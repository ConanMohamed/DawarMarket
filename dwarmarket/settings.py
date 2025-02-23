from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔒 استخدام متغيرات البيئة للأمان
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-default-secret-key')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# ✅ ضبط ALLOWED_HOSTS لقراءة القيم من البيئة
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'web-production-7ceef.up.railway.app').split(',')

# ✅ إصلاح مشكلة CSRF (403 Forbidden)
CSRF_TRUSTED_ORIGINS = [
    "https://web-production-7ceef.up.railway.app",
]

# ✅ التطبيقات المثبتة
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'rest_framework',
    'djoser',
    'debug_toolbar',
    'store',
    'corsheaders',
]

# ✅ الميدل وير
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # يجب أن يكون أول middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dwarmarket.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dwarmarket.wsgi.application'

# ✅ قاعدة البيانات PostgreSQL
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
}

# ✅ إعدادات الملفات الثابتة والوسائط
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ✅ ضبط WhiteNoise لتقديم الملفات الثابتة
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ تحسين الأمان للملفات الثابتة والكوكيز
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True  # يجبر جميع الطلبات على استخدام HTTPS

# ✅ إعدادات CORS لدعم الاتصال من تطبيق Flutter بشكل آمن
CORS_ALLOWED_ORIGINS = [
    "https://web-production-7ceef.up.railway.app",
    "https://your-flutter-app.com",  # استبدل بهذا رابط التطبيق الفعلي إذا كنت تستخدم واحدًا
]

# ✅ إعدادات REST Framework و JWT
REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

DJOSER = {
    'LOGIN_FIELD': 'phone',
    'SERIALIZERS': {
        'user_create': 'store.serializers.UserCreateSerializer',
        'current_user': 'store.serializers.UserSerializer',
    }
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1)
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'store.User'
