# -*- coding: utf-8 -*-
from celery import Celery

from plexlib import app, config_obj

celery = Celery(app.name, namespace='CELERY')
celery.config_from_object(config_obj)
