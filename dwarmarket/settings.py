from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔒 استخدام متغيرات البيئة للأمان
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-default-secret-key')
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ['true', '1']


# ✅ ضبط ALLOWED_HOSTS
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'web-production-7ceef.up.railway.app,127.0.0.1').split(',')

# ✅ إصلاح CSRF
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
    'store',
    'corsheaders',
]

# ✅ تفعيل debug_toolbar فقط في التطوير
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

# ✅ الميدل وير
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ✅ إضافة debug_toolbar في `MIDDLEWARE` فقط عند `DEBUG=True`
if DEBUG:
    MIDDLEWARE.insert(3, 'debug_toolbar.middleware.DebugToolbarMiddleware')

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
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

# ✅ إعدادات الملفات الثابتة والوسائط
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🔹 إنشاء مجلد staticfiles إذا لم يكن موجودًا
if not os.path.exists(STATIC_ROOT):
    os.makedirs(STATIC_ROOT)

# ✅ ضبط WhiteNoise بشكل صحيح
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ تحسين الأمان ومنع إعادة التوجيه الغير منتهية
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # تعطيل إعادة التوجيه التلقائي إلى HTTPS مؤقتًا

# ✅ تحسين إعدادات الأمان
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin"

# ✅ دعم CORS للسماح بالاتصال من تطبيقات أخرى
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "https://web-production-7ceef.up.railway.app").split(",")

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

# ✅ ضبط الـ Logging لرؤية الأخطاء على Railway
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_error.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# ✅ تفعيل Debug Toolbar فقط في التطوير
if DEBUG:
    INTERNAL_IPS = ["127.0.0.1"]
