# -*- coding: utf-8 -*-
import time
from flask import request, jsonify

from plexlib import app
from plexlib.tasks import do_update_library


@app.route('/update/from_name/', methods=['POST'])
def update_from_name():
    try:
        file_name = request.form['name'].decode('utf-8')
        task = do_update_library.apply_async(kwargs={'file_name': file_name, 'request_time': time.time()})
    except Exception as ex:
        return jsonify({'success': False, 'error': ex.__class__.__name__, 'message': ex.message})

    return jsonify({'success': True, 'file_name': file_name, 'task_id': task.task_id})


@app.route('/update/<section>/', methods=['GET'])
def update_section(section):
    try:
        task = do_update_library.apply_async(kwargs={'section_name': section, 'request_time': time.time()})
    except Exception as ex:
        return jsonify({'success': False, 'error': ex.__class__.__name__, 'message': ex.message})

    return jsonify({'success': True, 'section_name': section, 'task_id': task.task_id})
