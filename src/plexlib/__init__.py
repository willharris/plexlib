import os

import redis

from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from werkzeug.utils import import_string

this_dir = os.path.dirname(__file__)

load_dotenv()

app = Flask(__name__, static_folder='../../web/static')
config_class = import_string('config.%s' % os.environ.get('FLASK_CONFIG', 'DevConfig'))
config_obj = config_class()
app.config.from_object(config_obj)

mail = Mail(app)

redisdb = redis.Redis.from_url(app.config['REDIS_URL'], decode_responses=True)

from plexlib import views

from plexlib.debug_views import mod_debug
app.register_blueprint(mod_debug, url_prefix='/debug/')

from plexlib.tools.flask_cache_bust import init_cache_busting
init_cache_busting(app)
