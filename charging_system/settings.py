import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-your-secret-key-here'  # 生产环境需更换

DEBUG = True

ALLOWED_HOSTS = []

LOGGING = {
    'version': 1,  # 日志配置版本（固定为1）
    'disable_existing_loggers': False,  # 不禁用已存在的日志器
    'formatters': {  # 日志格式
        'verbose': {  # 详细格式
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',  # 使用 `{}` 作为格式符
        },
        'simple': {  # 简单格式
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {  # 日志处理器
        'console': {  # 输出到控制台
            'level': 'DEBUG',  # 处理 DEBUG 及以上级别
            'class': 'logging.StreamHandler',  # 控制台输出类
            'formatter': 'verbose',  # 使用 verbose 格式
        },
    },
    'loggers': {  # 日志器
        'django': {  # Django 自带日志器（捕获框架内部日志）
            'handlers': ['console'],  # 使用 console 处理器
            'level': 'INFO',  # 记录 INFO 及以上级别
            'propagate': True,  # 是否向上级日志器传递
        },
        'myapp': {  # 自定义应用日志器（替换为你的 app 名称）
            'handlers': ['console'],
            'level': 'DEBUG',  # 开发环境建议用 DEBUG
            'propagate': False,  # 不向上传递（避免重复记录）
        },
    },
}
# 应用配置
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',

    # 第三方应用
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_yasg',

    # 自定义应用
    'charging',
    'payments',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = ()
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)
CORS_ALLOW_HEADERS = (
    'Token',
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)

ROOT_URLCONF = 'charging_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [Path(BASE_DIR) / 'templates'],
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

WSGI_APPLICATION = 'charging_system.wsgi.application'

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# 自定义用户模型
AUTH_USER_MODEL = 'charging.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# DRF 配置
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# 支付网关配置（示例）
PAYMENT_GATEWAY_URL = 'https://mock-payment-gateway.com/pay'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
