# -*- coding: utf-8 -*-
"""
Flask app initialization.
"""
import os.path
from flask import Flask


app = Flask(__name__)  # pylint: disable-msg=C0103

app.config['DATA_XML'] = 'runtime/data/users.xml'