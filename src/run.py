# -*- coding: utf-8 -*-
import os

from plexlib import app
from plexlib.listener import launch_alert_listener
from plexlib.tasks import initialize_section_recents
from plexlib.utilities import setup_flask_logging, dump_env, dump_config


def run_singleton_actions():
    """
    These actions should only be run once within the whole system, i.e. only on one worker process/thread
    when running in a single-process scenario such as when developing.
    """
    initialize_section_recents.delay()
    launch_alert_listener(5.0)


if os.environ.get('WERKZEUG_RUN_MAIN', False) or 'UWSGI_ORIGINAL_PROC_NAME' in os.environ:
    setup_flask_logging(app.config['PLEXLIB_LOGDIR'])

    if app.debug:
        dump_env()
        dump_config()

    if 'UWSGI_ORIGINAL_PROC_NAME' in os.environ:
        from uwsgidecorators import postfork

        # Actions that launch threads should only run after uwsgi has forked the worker processes, otherwise
        # networking actions can cause a deadlock on macOS due to an unreleased lock from the master process.
        # c.f. https://emptysqua.re/blog/getaddrinfo-deadlock/
        @postfork
        def initialize_uwsgi():
            import uwsgi  # not in PYTHONPATH - only importable when running under uwsgi
            if uwsgi.worker_id() == 1:
                run_singleton_actions()

    if os.environ.get('WERKZEUG_RUN_MAIN', False):
        run_singleton_actions()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config['DEBUG'])
