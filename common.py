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
        k, v = re.match(r'(.*?): (.*)', line).groups()
        headers[k.strip()] = v.strip()
    return headers


def is_remote_msg():
    return os.environ.get('FIREBASE_SERVER_KEY') is not None


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
    elif sys.platform == 'darwin':
        msg = re.sub(r'[^\w ]', '', msg)
        os.system(f'osascript -e \'display notification "{msg}" with title "{title}"\'')
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