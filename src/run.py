# -*- coding: utf-8 -*-
import os

from plexlib import app
from plexlib.listener import library_scan_callback
from plexlib.tasks import initialize_section_recents
from plexlib.utilities import get_plex, setup_logging

setup_logging(os.path.join(os.path.dirname(__file__), os.pardir, 'logs'))

if not app.config['DEBUG'] or 'UWSGI_EMPEROR_FD' in os.environ or os.environ.get('WERKZEUG_RUN_MAIN', False):
    plex = get_plex()
    notifier = plex.startAlertListener(library_scan_callback)
    app.logger.info('Added notifier: %s', notifier)
    initialize_section_recents.delay()


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
