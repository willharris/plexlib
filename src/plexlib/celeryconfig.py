# -*- coding: utf-8 -*-
from celery import Celery
from opbeat.contrib.celery import register_signal
from opbeat.contrib.flask import Opbeat

from plexlib import app, config_class

celery = Celery(app.name, namespace='CELERY')
celery.config_from_object(config_class)

try:
    opbeat = Opbeat(app)
    register_signal(opbeat.client)
except Exception as ex:
    app.logger.exception('Unable to register Opbeat celery hooks', ex)
