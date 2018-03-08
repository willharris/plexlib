# -*- coding: utf-8 -*-
import json
import os
from collections import OrderedDict

from opbeat.contrib.flask import Opbeat

from plexlib import app
from plexlib.listener import library_scan_callback
from plexlib.tasks import initialize_section_recents
from plexlib.utilities import get_plex, setup_logging

setup_logging(os.path.join(os.path.dirname(__file__), os.pardir, 'logs'))

if app.debug:
    app.logger.debug('Environment: %s', json.dumps(OrderedDict(sorted(os.environ.iteritems()))))

    strings = map(lambda kv: (kv[0], unicode(kv[1])), app.config.iteritems())
    app.logger.debug('Config: %s', json.dumps(OrderedDict(sorted(strings))))

if not app.config['DEBUG'] or 'UWSGI_ORIGINAL_PROC_NAME' in os.environ or os.environ.get('WERKZEUG_RUN_MAIN', False):
    if 'OPBEAT_APP_ID' in os.environ:
        opbeat = Opbeat(app)

    plex = get_plex()
    notifier = plex.startAlertListener(library_scan_callback)
    app.logger.info('Added notifier: %s', notifier)
    initialize_section_recents.delay()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config['DEBUG'])
