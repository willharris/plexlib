# -*- coding: utf-8 -*-
from celery import Celery
from opbeat.contrib.celery import register_signal
from opbeat.contrib.flask import Opbeat

from plexlib import app

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

try:
    opbeat = Opbeat(app)
    register_signal(opbeat.client)
except Exception as ex:
    app.logger.exception('Unable to register Opbeat celery hooks', ex)
