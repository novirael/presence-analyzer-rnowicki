# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import threading
import xml.etree.ElementTree as etree
from json import dumps
from functools import wraps
from datetime import datetime, timedelta

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


def cache(sec):
    """
    Save to cash function result for given period of time.
    """
    def decorator(fun):
        cache_lock = threading.Lock()
        fun.cache = [datetime.now(), {}]

        def wrapper(*args, **kwargs):
            with cache_lock:
                now = datetime.now()
                if now > fun.cache[0]:
                    fun.cache[0] = now + timedelta(seconds=sec)
                    fun.cache[1] = fun(*args, **kwargs)
                return fun.cache[1]
        return wrapper
    return decorator


@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    usage_id = get_details()
    data = {}
    err = []

    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            if user_id in usage_id:
                data.setdefault(user_id, {})[date] = {
                    'start': start,
                    'end': end,
                }
            else:
                err.append(user_id)

        for e in set(err):
            log.debug("User %d presence data exist but details doesn't.", e)

    return data


def get_details():
    """
    Parse XML file and groups it by user_id.

    It creates structure like this:
    details = {
        'user_id': {
            'name': 'User name,
            'avatar': '/example/path/to/image'
        }
    }
    """
    details = {}
    try:
        tree = etree.parse(app.config['DATA_XML'])
        uroot = tree.getroot().find('users')
        for child in uroot:
            user_id_xml = int(child.attrib['id'])
            avatar = child.find('avatar').text
            name = child.find('name').text
            details[user_id_xml] = {'avatar': avatar, 'name': name}

    except IOError:
        log.debug("Cannot open XML file")

    return details


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    Returns interval time of work grouped by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_by_weekday_with_points(items):
    """
    Groups presence entries by weekday.
    Returns interval time of entrance and leave grouped by weekday.
    """
    result = {i: [[], []] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()][0].append(seconds_since_midnight(start))
        result[date.weekday()][1].append(seconds_since_midnight(end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
