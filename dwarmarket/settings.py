"""
Django settings for dwarmarket project.
"""
from pathlib import Path
from datetime import timedelta
import os
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== [ الأساسيات ] ====================
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # مطلوب بدون قيمة افتراضية
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'web-production-7ceef.up.railway.app',
    'dawarmarket.com',
    'www.dawarmarket.com',
    'localhost',
    '127.0.0.1'
]

CSRF_TRUSTED_ORIGINS = [
    'https://web-production-7ceef.up.railway.app',
    'https://dawarmarket.com',
    'https://www.dawarmarket.com'
]

# ==================== [ التطبيقات ] ====================
INSTALLED_APPS = [
    # الأساسية
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # الطرف الثالث
    'rest_framework',
    'djoser',
    'corsheaders',
    'django_filters',
    
    # Cloudinary
    'cloudinary',
    'cloudinary_storage',
    
    # التطبيقات الداخلية
    'store.apps.StoreConfig',
]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

# ==================== [ Middleware ] ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# ==================== [ القوالب ] ====================
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

# ==================== [ قاعدة البيانات ] ====================
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ==================== [ Cloudinary ] ====================
cloudinary.config(
    cloud_name=os.environ['CLOUDINARY_CLOUD_NAME'],
    api_key=os.environ['CLOUDINARY_API_KEY'],
    api_secret=os.environ['CLOUDINARY_API_SECRET'],
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ['CLOUDINARY_CLOUD_NAME'],
    'API_KEY': os.environ['CLOUDINARY_API_KEY'],
    'API_SECRET': os.environ['CLOUDINARY_API_SECRET'],
    'MEDIA_TAG': 'dawarmarket_media',
    'STATIC_TAG': 'dawarmarket_static',
    'MAGIC_FILE_PATH': 'magic',
    'PREFIX': os.environ.get('CLOUDINARY_PREFIX', 'dawarmarket/prod')
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticCloudinaryStorage'

# ==================== [ الملفات الثابتة ] ====================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==================== [ الأمان ] ====================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ==================== [ CORS ] ====================
CORS_ALLOWED_ORIGINS = [
    "https://dawarmarket.com",
    "https://www.dawarmarket.com",
    "https://web-production-7ceef.up.railway.app"
]
CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# ==================== [ REST Framework ] ====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'COERCE_DECIMAL_TO_STRING': False,
}

# ==================== [ Djoser & JWT ] ====================
DJOSER = {
    'LOGIN_FIELD': 'phone',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'SERIALIZERS': {
        'user_create': 'store.serializers.UserCreateSerializer',
        'current_user': 'store.serializers.UserSerializer',
    }
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'UPDATE_LAST_LOGIN': True,
}

# ==================== [ إعدادات أخرى ] ====================
AUTH_USER_MODEL = 'store.User'
LANGUAGE_CODE = 'ar-eg'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== [ Debug Toolbar ] ====================
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']

# ==================== [ Logging ] ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_errors.log'),
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}