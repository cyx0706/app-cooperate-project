
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '=)6*5n6df)y-(ncc(87=vc4e)c3bwms^8imnof&=v4dko56ncr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app_api.middleware.HttpOtherMethodMiddleware',
]

ROOT_URLCONF = 'MyTieba.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = 'MyTieba.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'postbar',
        'USER': 'root',
        'PASSWORD': '0706xxsr',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'CHARSET': 'utf8',
    }
}

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
REDIS_DB = 0


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# APPEND_SLASH = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static1/').replace('\\', '/')
STATICFILES_DIRS = (
       os.path.join(BASE_DIR,'static/').replace('\\','/'),
)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/').replace('\\', '/')
MEDIA_URL = '/media/'

MAX_UPLOAD_SIZE = 3 * 1024 * 1024  # 3MB

# email setting

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = '18539075138@163.com'
EMAIL_HOST_PASSWORD = '0706XXSR'
EMAIL_SUBJECT_PREFIX = u'django'       #为邮件Subject-line前缀,默认是'[django]'
EMAIL_USE_TLS = True                  #与SMTP服务器通信时，是否启动TLS链接(安全链接)。默认是false
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# logger
BASE_LOG_DIR = os.path.join(BASE_DIR, "log")
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console':{
#             'level':'DEBUG',
#             'class':'logging.StreamHandler',
#         },
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切换文件当达到最大大小
#             'filename': os.path.join(BASE_LOG_DIR, 'debug.log').replace('\\', '/'),
#             'formatter': 'standard',
#             'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
#             'encoding': 'UTF-8',
#         },
#         'warning_file': {
#             'level': 'WARNING',
#             'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切换文件当达到最大大小
#             'filename': os.path.join(BASE_LOG_DIR, 'warning.log').replace('\\', '/'),
#             'formatter': 'standard',
#             'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
#             'encoding': 'UTF-8',
#         },
#         'info_file': {
#             'level': 'INFO',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(BASE_LOG_DIR, 'info.log').replace('\\', '/'),
#             'formatter': 'standard',
#             'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
#             'encoding': 'UTF-8',
#         }
#     },
#     'formatters': {
#         'standard': {
#             'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d]'+
#                       '[%(module)s:%(funcName)s] [%(levelname)s]- %(message)s'  #日志格式
#         },
#         # 简单的日志格式
#         'simple': {
#             'format': '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d]%(message)s'
#         },
#         # 定义一个特殊的日志格式
#         'collect': {
#             'format': '%(message)s'
#         }
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file', 'console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'warning': {
#             'handlers': ['warning_file',],
#             'level': 'WARNING',
#             'propagate': True,
#         },
#         'info': {
#             'handlers': ['info_file', ],
#             'level': 'INFO',
#             'propagate': False,
#         }
#     }
# }