# -*- coding: utf-8 -*-
import os

from opbeat.contrib.flask import Opbeat

from plexlib import app
from plexlib.listener import launch_alert_listener
from plexlib.tasks import initialize_section_recents
from plexlib.utilities import setup_flask_logging, dump_env, dump_config

setup_flask_logging(app.config['PLEXLIB_LOGDIR'])

if not app.config['DEBUG'] or 'UWSGI_ORIGINAL_PROC_NAME' in os.environ or os.environ.get('WERKZEUG_RUN_MAIN', False):
    if app.debug:
        dump_env()
        dump_config()

    if 'OPBEAT_APP_ID' in os.environ:
        opbeat = Opbeat(app)

    initialize_section_recents.delay()
    launch_alert_listener(5.0)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config['DEBUG'])
