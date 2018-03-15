import os

import envdir
import redis

from flask import Flask
from flask_mail import Mail
from werkzeug.utils import import_string

this_dir = os.path.dirname(__file__)

envs = os.path.abspath(os.path.join(this_dir, os.pardir, os.pardir, 'envs'))
if os.path.isdir(envs):
    envdir.open(envs)

app = Flask(__name__, static_folder='../../web/static')
config_class = import_string('config.%s' % os.environ.get('FLASK_CONFIG', 'DevConfig'))
config_obj = config_class()
app.config.from_object(config_obj)

mail = Mail(app)

redisdb = redis.Redis.from_url(app.config['REDIS_URL'])

from plexlib import views
