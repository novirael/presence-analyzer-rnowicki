# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, render_template

from presence_analyzer.main import app
from presence_analyzer.utils import jsonify, get_data, mean, \
    group_by_weekday, group_by_weekday_with_points

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/static/presence_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': 'User {0}'.format(str(i))}
            for i in data.keys()]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end(user_id):
    """
    Returns mean presence time of begin and end of work.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday_with_points(data[user_id])

    result = [(calendar.day_abbr[weekday], mean(points[0]), mean(points[1]))
              for weekday, points in weekdays.items()]
    return result

@app.route('/chart/meantime')
def meantime():
    return render_template('meantime.html', meantime=True)

@app.route('/chart/presenceweekday')
def presenceweekday():
    return render_template('presenceweekday.html', preweekday=True)

@app.route('/chart/presencestartend')
def presencestartend():
    return render_template('presencestartend.html', prestartend=True)
