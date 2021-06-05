# -*- coding: utf-8 -*-
import json
import os
from collections import OrderedDict
from logging import Formatter

from celery.signals import worker_ready
from celery.utils.log import get_task_logger
from flask import render_template
from flask_mail import Message
from natsort import natsorted

from plexlib import app, mail, redisdb
from plexlib.celeryconfig import celery
from plexlib.utilities import get_section_for_video_file, get_plex, get_section_updated_key, LOGFMT

if eval(os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False')):
    celery_logger = app.logger
    for handler in celery_logger.handlers:
        handler.setFormatter(Formatter(LOGFMT))
else:
    celery_logger = get_task_logger(__name__)


@worker_ready.connect
def worker_ready(**kwargs):
    celery_logger.info('Worker connected, checking for video volume availability')
    check_video_volumes()


@celery.task()
def dump_config():
    cleaned = map(lambda kv: (kv[0], str(kv[1])), app.config.items())
    od = OrderedDict(sorted(cleaned))
    celery_logger.info('Flask Config: %s', json.dumps(od))


@celery.task(bind=True)
def do_update_library(self, section_name=None, file_name=None, request_time=0.0, **kwargs):
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
def initialize_section_recents(**kwargs):
    plex = get_plex()

    celery_logger.info('Reading recent items from the Plex libraries...')
    for section in plex.library.sections():
        section_recents = set([x.key.replace('/library/metadata/', '') for x in section.recentlyAdded()])
        redisdb.set('%s_recents' % section.title, json.dumps(list(section_recents)))
        celery_logger.info('Stored %d recent items from %s', len(section_recents), section.title)


@celery.task()
def identify_new_media(section_name, **kwargs):
    plex = get_plex()

    section = plex.library.section(section_name)
    section_recents = section.recentlyAdded()

    new_section_recents = set([x.key.replace('/library/metadata/', '') for x in section_recents])
    old_section_recents = redisdb.getset('%s_recents' % section_name, json.dumps(list(new_section_recents)))

    old_section_recents = set(json.loads(old_section_recents))

    diff = new_section_recents.difference(old_section_recents)

    # Based on the item keys, we fill a new list with the actual Plex items
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
                    titles.append('%s (%s)' % (item.title, item.year))

            with app.app_context():
                msg = Message('New media in your Plex library',
                              sender=app.config['NOTIFICATION_SENDER'],
                              recipients=[app.config['NOTIFICATION_RECIPIENT']])
                msg.body = render_template('email/new_media.txt',
                                           section_name=section_name,
                                           titles=natsorted(titles))
                mail.send(msg)
    else:
        celery_logger.info('NOTIFICATION_RECIPIENT not configured, no notification sent')


@celery.task()
def check_video_volumes(**kwargs):
    """
    Looks for a video file inside the configured video volumes. Files are considered to be video files if
    they have one of the extensions configured with the PLEXLIB_VIDEO_EXTS setting.

    :raises RuntimeError: if no video could be found
    """
    video_exts = app.config['PLEXLIB_VIDEO_EXTS']
    for root in ['PLEXLIB_MOVIES_ROOT', 'PLEXLIB_TVSHOWS_ROOT']:
        root_dir = app.config[root]
        if not os.path.isdir(root_dir):
            raise RuntimeError('%s at %s is not a directory' % (root, root_dir))

        has_videos = False
        for dirname, _, files in os.walk(root_dir):
            # get a set of all file extensions in this directory
            file_exts = set(map(lambda x: x[-3:].lower(), files))
            intrsct = video_exts.intersection(file_exts)
            if intrsct:
                celery_logger.debug('Found movie types {%s} at %s', ', '.join(intrsct), dirname)
                has_videos = True
                break

        if not has_videos:
            raise RuntimeError('Did not find any files under %s ending in {%s}' % (root_dir, ', '.join(video_exts)))
