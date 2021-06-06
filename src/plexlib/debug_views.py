# -*- coding: utf-8 -*-
import json
import os
from collections import OrderedDict

from flask import render_template, abort, Blueprint
from plexapi.exceptions import NotFound

from plexlib import app, redisdb
from plexlib.utilities import require_token, get_plex, get_section_recents


mod_debug = Blueprint('debug', __name__)


@mod_debug.route('/')
@require_token
def index(token=''):
    plex = get_plex()
    sections = [x.title for x in plex.library.sections()]
    return render_template('debug.html', token=token, sections=sections)


@mod_debug.route('/config/')
@require_token
def config(**kwargs):
    config = OrderedDict(sorted(app.config.items()))
    return render_template('config.html', config=config, env=os.environ)


@mod_debug.route('/dump-recents/<section_name>/')
@require_token
def dump_recents(section_name, **kwargs):
    plex = get_plex()

    try:
        section = plex.library.section(section_name)
        plex_recents = get_section_recents(section)
    except NotFound:
        abort(404)

    try:
        cached_recents = sorted(json.loads(redisdb.get(f'{section_name}_recents')), reverse=True)
    except Exception as ex:
        app.logger.error(ex)
        cached_recents = []

    return render_template('section_recents.html', section_name=section_name, plex_recents=plex_recents,
                           cached_recents=cached_recents)
