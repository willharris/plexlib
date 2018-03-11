# -*- coding: utf-8 -*-
import json
import os
from collections import OrderedDict

from opbeat.contrib.flask import Opbeat

from plexlib import app
from plexlib.listener import launch_alert_listener
from plexlib.tasks import initialize_section_recents
from plexlib.utilities import setup_logging

setup_logging(app.config['PLEXLIB_LOGDIR'])

if not app.config['DEBUG'] or 'UWSGI_ORIGINAL_PROC_NAME' in os.environ or os.environ.get('WERKZEUG_RUN_MAIN', False):
    if app.debug:
        app.logger.debug('Environment: %s', json.dumps(OrderedDict(sorted(os.environ.iteritems()))))

        strings = map(lambda kv: (kv[0], unicode(kv[1])), app.config.iteritems())
        app.logger.debug('Config: %s', json.dumps(OrderedDict(sorted(strings))))

    if 'OPBEAT_APP_ID' in os.environ:
        opbeat = Opbeat(app)

    initialize_section_recents.delay()
    launch_alert_listener()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config['DEBUG'])
