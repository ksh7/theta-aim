import datetime

from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from celery import shared_task


@shared_task(name="sample_task")
def sample_task(a, b):
    import time
    time.sleep(5)
    return a + b
