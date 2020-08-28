#!/usr/bin/env python3
import requests


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