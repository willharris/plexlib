import os
import socket
from datetime import timedelta

from kombu import Queue, Exchange
from kombu.common import Broadcast


def process_environment(target, prefix, keyfunc=lambda x, y: x[len(y):]):
    for key, rawval in os.environ.items():
        if key.startswith(prefix):
            try:
                val = eval(rawval)
            except:
                val = rawval

            setattr(target, keyfunc(key, prefix), val)


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

    PLEXLIB_LOGDIR = os.environ.get('PLEXLIB_LOGDIR', os.path.join(os.path.dirname(__file__), os.pardir, 'logs'))
    PLEXLIB_MOVIES_ROOT = os.environ.get('PLEXLIB_MOVIES_ROOT', '/Volumes/Video/Movies')
    PLEXLIB_TVSHOWS_ROOT = os.environ.get('PLEXLIB_TVSHOWS_ROOT', '/Volumes/Video/TV')
    PLEXLIB_VIDEO_EXTS = set(eval(os.environ.get('PLEXLIB_VIDEO_EXTS', "{'mp4', 'mkv', 'm4v', 'avi'}")))

    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

    NOTIFICATION_SENDER = os.environ.get('NOTIFICATION_SENDER', 'PlexLib <plexlib@%s>' % socket.getfqdn())
    NOTIFICATION_RECIPIENT = os.environ.get('NOTIFICATION_RECIPIENT', '')

    def __init__(self, *args, **kwargs):
        process_environment(self, 'FLASK_')

        if not hasattr(self, 'ADMINS'):
            raise ConfigurationException('FLASK_ADMINS')
        elif not isinstance(self.ADMINS, (list, tuple)):
            raise ConfigurationException('FLASK_ADMINS', 'list or tuple')

        super(BaseConfig, self).__init__(*args, **kwargs)


class CeleryConfigMixin(object):
    task_default_queue = 'default'
    task_default_exchange = 'default'
    task_default_routing_key = 'default'

    task_queues = (
        Queue('default', Exchange('default'), routing_key='default'),
        Broadcast('broadcast', routing_key='broadcast'),
    )

    broker_url = os.environ.get('CELERY_BROKER_URL', 'amqp://plexlib:plexlib@localhost/plexlib')
    broker_transport_options = {'max_retries': 2}
    result_backend = os.environ.get('CELERY_RESULT_BACKEND', '')

    beat_schedule = {
        'check-volumes': {
            'task': 'plexlib.tasks.check_video_volumes',
            'schedule': timedelta(minutes=30),
            'options': {'queue': 'broadcast'}
        }
    }

    def __init__(self, *args, **kwargs):
        process_environment(self, 'CELERY_', lambda x, y: x[7:].lower())

        super(CeleryConfigMixin, self).__init__(*args, **kwargs)


class DevConfig(BaseConfig, CeleryConfigMixin):

    DEBUG = eval(os.environ.get('FLASK_DEBUG', 'True'))
    task_always_eager = eval(os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'True'))


class ProdConfig(BaseConfig, CeleryConfigMixin):

    SECRET_KEY = os.environ.get('SECRET_KEY', 'topitus-secretus!')
