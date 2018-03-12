# -*- coding: utf-8 -*-
import threading
import time

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


def launch_alert_listener(reschedule=True, interval=5.0):
    """
    Checks if an existing AlertListener thread is running, and if not, starts one. Optionally launches a Timer thread
    to call the method again.

    In the case that the Plex Media Server is restarted, any previously running AlertListener threads will
    exit due to the WebSocket connection having been closed.

    :param boolean reschedule: if True, will cause the method to be called again. Default: True
    :param float interval: the interval in seconds after which to call the method again. Default: 5.0
    """
    threads = threading.enumerate()
    # first check if first/main thread is still alive, and abort if not
    if not threads[0].is_alive():
        app.logger.info('Main thread is dead, aborting: %s', threads[0])
        return

    thread_names = [x.__class__.__name__ for x in threads]

    if 'AlertListener' not in thread_names:
        app.logger.debug('Thread names: %s', thread_names)
        plex = get_plex()
        listener = plex.startAlertListener(callback=library_scan_callback)
        app.logger.info('Started listener: %s', listener)

    if reschedule:
        threading.Timer(interval, launch_alert_listener).start()
