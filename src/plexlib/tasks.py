# -*- coding: utf-8 -*-
import json
from collections import OrderedDict

from celery import Celery
from celery.utils.log import get_task_logger
from flask import render_template
from flask_mail import Message

from plexlib import app, mail, redisdb
from plexlib.utilities import get_section_for_video_file, get_plex, get_section_updated_key

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
celery_logger = get_task_logger(__name__)


@celery.task()
def dump_config():
    cleaned = map(lambda kv: (kv[0], unicode(kv[1])), app.config.iteritems())
    od = OrderedDict(sorted(cleaned))
    celery_logger.info('Flask Config: %s', json.dumps(od))


@celery.task(bind=True)
def do_update_library(self, section_name=None, file_name=None, request_time=0.0):
    celery_logger.info('library update requested: %s / %s / %s', section_name, file_name, request_time)

    if not section_name and file_name:
        section_name = get_section_for_video_file(file_name)

    celery_logger.info('Section name: %s', section_name)

    redis_key = get_section_updated_key(section_name)
    section_updated_time = float(redisdb.get(redis_key) or 0.0)

    if section_updated_time > request_time:
        celery_logger.info('Section was updated after request was sent, cancelling update')
        return

    plex = get_plex()
    section = plex.library.section(section_name)

    if section.refreshing:
        celery_logger.info('Section %s already updating, retrying task', section)
        self.retry()

    celery_logger.info('Updating %s', section)
    section.update()


@celery.task(autoretry_for=(Exception,), default_retry_delay=30)
def initialize_section_recents():
    plex = get_plex()

    for section in plex.library.sections():
        section_recents = set([x.key.replace('/library/metadata/', '') for x in section.recentlyAdded()])
        redisdb.set('%s_recents' % section.title, json.dumps(list(section_recents)))
        celery_logger.info('Stored %d recent items from %s', len(section_recents), section.title)


@celery.task()
def identify_new_media(section_name):
    plex = get_plex()

    section = plex.library.section(section_name)
    section_recents = section.recentlyAdded()

    new_section_recents = set([x.key.replace('/library/metadata/', '') for x in section_recents])
    old_section_recents = redisdb.getset('%s_recents' % section_name, json.dumps(list(new_section_recents)))

    old_section_recents = set(json.loads(old_section_recents))

    diff = [item for item in new_section_recents if item not in old_section_recents]

    diff_items = []
    for item in diff:
        diff_items.extend(filter(lambda x: x.key.endswith(item), section_recents))

    celery_logger.info('New items in %s: %s', section_name, diff_items)

    if app.config['NOTIFICATION_RECIPIENT']:
        if diff_items:
            titles = []
            for item in diff_items:
                if hasattr(item, 'show'):
                    titles.append('%s - %s - %s' % (item.show().title, item.seasonEpisode, item.title))
                elif hasattr(item, 'artist'):
                    titles.append('%s - %s' % (item.artist().title, item.title))
                else:
                    titles.append(item.title)

            with app.app_context():
                msg = Message('New item in your Plex library',
                              sender=app.config['NOTIFICATION_SENDER'],
                              recipients=[app.config['NOTIFICATION_RECIPIENT']])
                msg.body = render_template('email/new_media.txt',
                                           section_name=section_name,
                                           titles=titles)
                mail.send(msg)
    else:
        celery_logger.info('NOTIFICATION_RECIPIENT not configured, no notification sent')