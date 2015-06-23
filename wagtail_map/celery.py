"""
Celery config for wagtail_map project.

For more information on this file, see
http://celery.readthedocs.org/en/latest/django/first-steps-with-django.html

Run your celery worker(s) as `celery -A wagtail_map worker --loglevel=info`
"""

from __future__ import absolute_import

import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wagtail_map.settings.dev")

app = Celery("wagtail_map")

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
