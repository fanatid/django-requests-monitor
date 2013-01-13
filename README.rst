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

* ``RM_STORAGE``

  Connection string to storage::

  	memcached://<host>:<port>

  Default value: ``memcached://127.0.0.1:11211``

* ``RM_STORAGE_TIMEOUT``

  Storage time in seconds, must be ``Int``, default: ``300``

* ``RM_URL``

  Path to requests monitor page, default: ``/request/``
