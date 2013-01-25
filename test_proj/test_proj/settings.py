# Django settings for test_proj project.
import os, re

PROJ_PATH = os.path.join(os.path.dirname(__file__), '..')


DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJ_PATH, 'testdb.sqlite'),
    }
}

SITE_ID = 1

STATIC_URL = '/static/'

SECRET_KEY = '0nyn%%917p#7w4*5e0&amp;a4z*-@z7*d_k442q$%vtij52#5*sarg'

ROOT_URLCONF = 'test_proj.urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.join(PROJ_PATH, 'templates'),
)

MIDDLEWARE_CLASSES = (
    'requests_monitor.middleware.RequestMonitorMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'requests_monitor',
    'debug_toolbar',
)

INTERNAL_IPS = ('127.0.0.1',)

REQUESTS_MONITOR_CONFIG = {
    #'STORAGE': 'redis://127.0.0.1:6379',
    'TIMEOUT': 300,
    'PREFIX':  '/requests/',
    'FILTERS': (
        #('requests_monitor.filters.AjaxOnlyFilter'),
        ('requests_monitor.filters.DisallowUrlFilter', (re.compile('^/favicon.ico$'),)),
    ),
}
