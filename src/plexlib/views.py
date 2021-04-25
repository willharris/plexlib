# -*- coding: utf-8 -*-
import time
from collections import OrderedDict

from flask import request, jsonify, render_template, abort

from plexlib import app
from plexlib.tasks import do_update_library
from plexlib.utilities import get_plex


@app.route('/')
@app.route('/index.html')
def index():
    plex = get_plex()
    sections = [x.title for x in plex.library.sections()]
    return render_template('index.html', sections=sections, url=app.config['PLEX_URL'], version=plex.version)


@app.route('/config/')
def config():
    # Only show the config if the request already knows the secret token
    token = request.args.get('token')
    if not token == app.config['PLEX_TOKEN']:
        abort(404)

    config = OrderedDict(sorted(app.config.iteritems()))
    return render_template('config.html', config=config)


@app.route('/update/from_name/', methods=['POST'])
def update_from_name():
    try:
        file_name = request.form['name'].decode('utf-8')
        task = do_update_library.apply_async(kwargs={'file_name': file_name, 'request_time': time.time()})
    except Exception as ex:
        return jsonify({'success': False, 'error': ex.__class__.__name__, 'message': str(ex)})

    return jsonify({'success': True, 'file_name': file_name, 'task_id': task.task_id})


@app.route('/update/<section>/', methods=['GET'])
def update_section(section):
    try:
        task = do_update_library.apply_async(kwargs={'section_name': section, 'request_time': time.time()})
    except Exception as ex:
        return jsonify({'success': False, 'error': ex.__class__.__name__, 'message': str(ex)})

    return jsonify({'success': True, 'section_name': section, 'task_id': task.task_id})
