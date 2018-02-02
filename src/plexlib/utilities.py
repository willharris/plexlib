# -*- coding: utf-8 -*-
import logging
import os
import re
from logging.handlers import SMTPHandler, TimedRotatingFileHandler

from flask import request
from plexapi.server import PlexServer

from plexlib import app


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


def get_section_for_video_file(root, file_name):
    """
    Determine the Plex section name for a video file.

    :param str root: The path to the base directory for Plex video files.
    :param str file_name: The name of the file for which to search.
    :return: The name of the Plex section to which the file belongs.
    :rtype: str
    :raises NotFound: if the section name could not be determined.
    """
    if not file_name:
        raise RuntimeError('No filename provided')

    movie_lib = (os.path.join(root, 'Movies'), 'Movies')
    tv_lib = (os.path.join(root, 'TV'), 'TV Shows')
    tv_match = re.search(r's\d+e\d+', file_name, re.I)

    if tv_match:
        search_dirs = [tv_lib, movie_lib]
    else:
        search_dirs = [movie_lib, tv_lib]

    section_name = None

    for search_dir, s_name in search_dirs:
        fullpath = find_file(file_name, search_dir)
        if fullpath:
            section_name = s_name
            break

    if not section_name:
        raise RuntimeError('Could not find section name for file %s' % file_name)

    return section_name


def setup_logging(logdir):
    class RequestFormatter(logging.Formatter):
        def format(self, record):
            try:
                record.url = request.url
                record.remote_addr = request.remote_addr
            except RuntimeError:
                record.url = '<no request>'
                record.remote_addr = '<no request>'
            return super(RequestFormatter, self).format(record)

    formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )

    mail_handler = SMTPHandler(
        mailhost=app.config['MAIL_SERVER'],
        fromaddr=app.config['NOTIFICATION_SENDER'],
        toaddrs=app.config['ADMINS'],
        subject='PlexLib Server Error'
    )
    mail_handler._timeout = 15.0  # ugly hack, but the default of 5s is unacceptable and cannot be configured
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(formatter)

    if not os.path.isdir(logdir):
        os.makedirs(logdir)

    file_handler = TimedRotatingFileHandler(os.path.join(logdir, 'plexlib.log'),
                                            when='d', backupCount=10, encoding='utf-8')
    file_handler.setFormatter(formatter)

    if not app.debug:
        app.logger.addHandler(mail_handler)
        file_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)
    else:
        file_handler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)

    app.logger.addHandler(file_handler)


_plex_instance = None


def get_plex():
    global _plex_instance
    if not _plex_instance:
        _plex_instance = PlexServer(app.config['PLEX_URL'], app.config['PLEX_TOKEN'])
    return _plex_instance


def get_section_updated_key(section_name):
    return '%s_updated' % section_name
