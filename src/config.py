import os
import socket


class ConfigurationException(RuntimeError):

    def __init__(self, key, key_type=None):
        self.key_err = key
        self.key_type = key_type

    def __str__(self):
        elems = ['%s must be configured' % self.key_err]
        if self.key_type:
            elems.append('(%s)' % self.key_type)
        return ' '.join(elems)


class BaseConfig(object):

    DEBUG = eval(os.environ.get('FLASK_DEBUG', 'False'))

    try:
        PLEX_URL = os.environ['PLEX_URL']
        PLEX_TOKEN = os.environ['PLEX_TOKEN']
    except KeyError as ex:
        raise ConfigurationException(ex)

    PLEX_VIDEO_FILE_ROOT = os.environ.get('PLEX_VIDEO_FILE_ROOT', '/Volumes/Video')
    
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://plexlib:plexlib@localhost/plexlib')
    # CELERY_RESULT_BACKEND = os.environ.get('CELERY_BROKER_URL', 'amqp://plexlib:plexlib@localhost/plexlib')

    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

    NOTIFICATION_SENDER = os.environ.get('NOTIFICATION_SENDER', 'PlexLib <plexlib@%s>' % socket.getfqdn())
    NOTIFICATION_RECIPIENT = os.environ.get('NOTIFICATION_RECIPIENT', '')

    def __init__(self):
        for key, rawval in os.environ.iteritems():
            if key.startswith('FLASK_'):
                try:
                    val = eval(rawval)
                except:
                    val = rawval

                setattr(self, key[6:], val)

        if not hasattr(self, 'ADMINS'):
            raise ConfigurationException('FLASK_ADMINS')
        elif not isinstance(self.ADMINS, (list, tuple)):
            raise ConfigurationException('FLASK_ADMINS', 'list or tuple')


class DevConfig(BaseConfig):

    DEBUG = eval(os.environ.get('FLASK_DEBUG', 'True'))
    CELERY_ALWAYS_EAGER = eval(os.environ.get('CELERY_ALWAYS_EAGER', 'True'))


class ProdConfig(BaseConfig):

    SECRET_KEY = os.environ.get('SECRET_KEY', 'topitus-secretus!')
