# -*- coding: utf-8 -*-
import time

from plexlib import redisdb, app
from plexlib.tasks import identify_new_media
from plexlib.utilities import get_section_updated_key


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
