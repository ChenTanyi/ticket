#!/usr/bin/env python3
import ctypes
import logging
import os
import re
import requests
import sys


def get_header(s):
    headers = dict()
    for line in s.strip().split('\n'):
        k, v = re.match(r'(.*?): (.*)', line.strip()).groups()
        headers[k] = v
    return headers


def send_msg(title, msg):
    server_key = os.environ.get('FIREBASE_SERVER_KEY')
    if server_key:
        r = notify(server_key, title, msg, timeout = 10)
        r.raise_for_status()
    else:
        notify_desktop(title, msg)


def notify_desktop(title, msg):
    if sys.platform == 'win32':
        ctypes.windll.user32.MessageBoxW(None, msg, title, 0)
    else:
        logging.error(f'unknow platform {sys.platform}')


def notify(key: str, title: str, body: str, **kwargs) -> requests.Response:
    r = requests.post(
        'https://fcm.googleapis.com/fcm/send',
        headers = {'Authorization': 'key={0}'.format(key)},
        json = {
            'notification': {
                'title': title,
                'body': body,
            },
            'data': {
                'message': body,
            },
            "condition": "!('test' in topics)",
        },
        timeout = kwargs.get('timeout'))
    return r