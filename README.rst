=======================
Django Requests Monitor
=======================

The Django Requests Monitor stores debug information about requests and
displayed on single page.


Installation
============

All also as well in `django-debug-toolbar <https://github.com/django-debug-toolbar/django-debug-toolbar>`_
, except:

#. Add ``requests_monitor`` to your ``INSTALLED_APPS`` before
   ``debug_toolbar``::

       INSTALLED_APPS = (
           ...
           'requests_monitor',
           'debug_toolbar',
           ...
       )

#. And replace ``debug_toolbar.middleware.DebugToolbarMiddleware`` to
   ``requests_monitor.middleware.RequestMonitorMiddleware``.


Configuration
=============

Requests Monitor configurated via dictionary ``REQUESTS_MONITOR_CONFIG``:

* ``STORAGE``
    Temponary dara storage, right now supported redis and builtin storage (unstable)

    Redis example::

      redis://127.0.0.1:6379

* ``TIMEOUT``
    Storage time in seconds, must be ``Int``.

* ``PREFIX``
    Path to requests monitor page.

* ``FILTERS``
    List every item is (Class, args, kwargs).
    Args and kwargs will be transferred to Class on since initialization.
    Class must have 2 functions:

      * process_request(request)
      * process_response(request, response)

    If function return False, request will not be saved.

Default configuration::

  REQUESTS_MONITOR_CONFIG = {
      'STORAGE': 'redis://127.0.0.1:6379',
      'TIMEOUT': 300,
      'PREFIX':  '/requests/',
      'FILTERS': (),
  }

Example configuration
=====================

::

  REQUESTS_MONITOR_CONFIG = {
      'STORAGE': 'redis://127.0.0.1:6379',
      'TIMEOUT': 100,
      'PREFIX':  '/requests/',
      'FILTERS': (
          ('requests_monitor.filters.AjaxOnlyFilter'),
          ('requests_monitor.filters.DisallowUrlFilter', (re.compile('^/favicon.ico$'),)),
      ),
  }

