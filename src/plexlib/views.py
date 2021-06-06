# -*- coding: utf-8 -*-
import socket
import time

from flask import request, jsonify, render_template

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


@app.route('/update/<section_name>/', methods=['GET'])
def update_section(section_name):
    kwargs = {
        'section_name': section_name
    }
    return library_method(do_update_library, **kwargs)


@app.route('/new-media/<section_name>/', methods=['GET'])
def new_media_in_section(section_name):
    kwargs = {
        'section_name': section_name
    }
    return library_method(identify_new_media, **kwargs)
