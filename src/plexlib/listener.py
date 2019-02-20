# -*- coding: utf-8 -*-
import threading
import time

from plexapi.alert import AlertListener

from plexlib import redisdb, app
from plexlib.tasks import identify_new_media
from plexlib.utilities import get_section_updated_key, get_plex


def library_scan_callback(data):
    """
    Callback listener to process library scan notifications.

    :param data:
    """
    if data[u'type'] == u'status':
        notifications = data.get(u'StatusNotification', [])
        for n in notifications:
            name = n.get(u'notificationName')
            if name == u'LIBRARY_UPDATE':
                title = n.get(u'title', '')
                # u'title': u'Scanning the "TV Shows" section'
                if title.startswith(u'Scanning'):
                    section = title[14:-9]
                    redisdb.lpush('scans', section)
                    app.logger.info('Detected beginning of scan: %s', section)

                    redis_key = get_section_updated_key(section)
                    redisdb.set(redis_key, time.time())
                elif title.endswith(u'complete'):
                    # Multiple scans may be triggered by the system automatically before the final
                    # "complete" signal is sent. We therefore process all sections previously pushed,
                    # assuming they were part of the same scan run (implicit assumption: Plex does not
                    # scan multiple sections in parallel).
                    section = redisdb.rpop('scans')
                    while section:
                        app.logger.info('Detected end of scan: %s', section)

                        identify_new_media.delay(section)

                        section = redisdb.rpop('scans')
                else:
                    app.logger.warn('Unhandled update notification: %s', title)
            else:
                app.logger.warn('Unhandled status notification: %s', name)


def check_alert_listener(event, timeout):
    """
    Checks if an existing AlertListener thread is running, and if not, starts one.

    In the case that the Plex Media Server is restarted, any previously running AlertListener threads will
    exit due to the WebSocket connection having been closed.

    :param threading.Event event: a threading event
    :param int timeout: the time to wait between checks for the listener
    """
    while event and not event.wait(timeout):
        threads = threading.enumerate()
        thread_names = [x.__class__.__name__ for x in threads]

        if 'AlertListener' not in thread_names:
            app.logger.debug("Didn't find AlertListener in thread names: %s", thread_names)
            launch_alert_listener(0)


def launch_alert_listener(interval=0):
    """
    Launch a `plexapi.AlertListener` thread to receive updates directly from the Plex Media Server.

    :param float interval: the interval in seconds after which the system should check that the `AlertListener` is
        still alive. Set to 0 to disable rechecking. Default: 0
    """
    try:
        plex = get_plex()
        listener = AlertListener(server=plex, callback=library_scan_callback)
        listener.setName('AlertListener')
        listener.start()
        app.logger.info('Started listener: %s', listener)
    except Exception as ex:
        app.logger.warn('Exception while trying to start listener: %s', ex)

    if interval > 0:
        event = threading.Event()
        thread = threading.Thread(target=check_alert_listener, args=(event, interval))
        thread.setName('AlertListenerWatcher')
        thread.setDaemon(True)
        thread.start()
