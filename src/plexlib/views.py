# -*- coding: utf-8 -*-
import os
import socket
import time
from collections import OrderedDict

from flask import request, jsonify, render_template, abort

from plexlib import app
from plexlib.tasks import do_update_library, identify_new_media
from plexlib.utilities import get_plex


@app.route('/')
@app.route('/index.html')
def index():
    plex = get_plex()
    sections = [x.title for x in plex.library.sections()]
    context = {
        'hostname': socket.gethostname(),
        'sections': sections,
        'url': app.config['PLEX_URL'],
        'version': plex.version,
    }
    return render_template('index.html', **context)


@app.route('/config/')
def config():
    # Only show the config if the request already knows the secret token
    token = request.args.get('token')
    if not token == app.config['PLEX_TOKEN']:
        abort(404)

    config = OrderedDict(sorted(app.config.items()))
    return render_template('config.html', config=config, env=os.environ)


def library_method(method, **kwargs):
    try:
        kwargs['request_time'] = time.time()
        kwargs['method'] = method.__name__

        task = method.apply_async(kwargs=kwargs)

        kwargs['success'] = True
        kwargs['task_id'] = task.task_id
    except Exception as ex:
        kwargs['success'] = False
        kwargs['error'] = ex.__class__.__name__
        kwargs['message'] = str(ex)
        app.logger.warn(ex)

    app.logger.debug(f'Called library method: {kwargs}')
    return jsonify(kwargs)


@app.route('/update/from_name/', methods=['POST'])
def update_from_name():
    try:
        kwargs = {
            'file_name': request.form['name']
        }
        result = library_method(do_update_library, **kwargs)
    except Exception as ex:
        return jsonify({'success': False, 'error': ex.__class__.__name__, 'message': str(ex)})

    return result


@app.route('/update/<section>/', methods=['GET'])
def update_section(section):
    kwargs = {
        'section_name': section
    }
    return library_method(do_update_library, **kwargs)


@app.route('/new-media/<section>/', methods=['GET'])
def new_media_in_section(section):
    kwargs = {
        'section_name': section
    }
    return library_method(identify_new_media, **kwargs)
