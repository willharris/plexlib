# -*- coding: utf-8 -*-
import json
import logging
import os
import re
from collections import OrderedDict
from logging.handlers import SMTPHandler, TimedRotatingFileHandler

import requests
from flask import request
from plexapi.server import PlexServer

from plexlib import app

LOGFMT = '[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s][%(process)d/%(threadName)s] %(message)s'


def find_file(name, start='/'):
    """
    Search for a file within a directory tree.

    :param str name: The file or directory to find.
    :param str start: The directory from which to start searching. Default: '/'.
    :return: The full path to the search query, or None if not found.
    :rtype: str
    """
    fullpath = None
    for dirname, subdirs, files in os.walk(start):
        subdirs = map(lambda x: x.decode('utf-8'), subdirs)
        files = map(lambda x: x.decode('utf-8'), files)
        if name in files or name in subdirs:
            fullpath = os.path.join(dirname, name)
            break

    return fullpath


def get_section_for_video_file(file_name):
    """
    Determine the Plex section name for a video file.

    :param str file_name: The name of the file for which to search.
    :return: The name of the Plex section to which the file belongs.
    :rtype: str
    :raises NotFound: if the section name could not be determined.
    """
    if not file_name:
        raise RuntimeError('No filename provided')

    movie_lib = (app.config['PLEXLIB_MOVIES_ROOT'], 'Movies')
    tv_lib = (app.config['PLEXLIB_TVSHOWS_ROOT'], 'TV Shows')
    tv_match = re.search(r's\d+e\d+', file_name, re.I)

    if tv_match:
        search_dirs = [tv_lib, movie_lib]
    else:
        search_dirs = [movie_lib, tv_lib]

    section_name = None

    for search_dir, s_name in search_dirs:
        if not os.path.isdir(search_dir):
            raise RuntimeError('Could not find %s root directory at %s' % (s_name, search_dir))
        fullpath = find_file(file_name, search_dir)
        if fullpath:
            section_name = s_name
            break

    if not section_name:
        raise RuntimeError('Could not find section name for file %s' % file_name)

    return section_name


def setup_flask_logging(logdir):
    class RequestFormatter(logging.Formatter):
        def format(self, record):
            try:
                record.url = request.url
                record.remote_addr = request.remote_addr
            except RuntimeError:
                record.url = '<no request>'
                record.remote_addr = '<no request>'
            return super(RequestFormatter, self).format(record)

    # TODO decide if we really need the request info, as it's often not there
    formatter = RequestFormatter(LOGFMT)

    mail_handler = SMTPHandler(
        mailhost=app.config['MAIL_SERVER'],
        fromaddr=app.config['NOTIFICATION_SENDER'],
        toaddrs=app.config['ADMINS'],
        subject='PlexLib Server Error'
    )
    mail_handler._timeout = 15.0  # ugly hack, but the default of 5s is unacceptable and cannot be configured
    mail_handler.setLevel(logging.ERROR)

    if logdir:
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

        file_handler = TimedRotatingFileHandler(os.path.join(logdir, 'plexlib.log'),
                                                when='d', backupCount=10, encoding='utf-8')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    for handler in app.logger.handlers:
        handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
        handler.setFormatter(formatter)

    if not app.debug:
        app.logger.addHandler(mail_handler)

    plexlogger = logging.getLogger("plexapi")
    for handler in app.logger.handlers:
        plexlogger.addHandler(handler)


_plex_instance = None


def get_plex():
    global _plex_instance
    if not _plex_instance:
        session = requests.Session()
        if app.debug:
            # When we are running in debug mode, disable the (default) gzip encoding so we can better
            # observe the communicate with the Plex server
            session.headers['Accept-Encoding'] = 'default'
        _plex_instance = PlexServer(app.config['PLEX_URL'], app.config['PLEX_TOKEN'], session=session)
    return _plex_instance


def get_section_updated_key(section_name):
    return '%s_updated' % section_name


def dump_env():
    app.logger.debug('Environment: %s', json.dumps(OrderedDict(sorted(os.environ.items()))))


def dump_config():
    strings = map(lambda kv: (kv[0], str(kv[1])), app.config.items())
    app.logger.debug('Config: %s', json.dumps(OrderedDict(sorted(strings))))
