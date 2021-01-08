#!/usr/bin/env python3
import os
import re
import json
import time
import yaml
import common
import hashlib
import logging
import requests
from datetime import datetime

H = '''\
accept: application/json
accept-encoding: gzip, deflate, br
accept-language: en,en-US;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5
cache-control: no-cache
content-length: 809
content-type: application/json;charset=UTF-8
cookie: {0}
origin: https://flights.ctrip.com
scope: d
sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
sec-ch-ua-mobile: ?0
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'''.format(os.environ['CTRIP_COOKIE'])

QUERIES = yaml.safe_load(open('query.yml'))
BATCH_SEARCH_URL = 'https://flights.ctrip.com/international/search/api/search/batchSearch'


def send_msg(msg):
    common.send_msg('Ctrip', msg)


def sign_param(params: dict):
    value = (
        params['transactionID'] +
        params['flightSegments'][0]['departureCityCode'] +
        params['flightSegments'][0]['arrivalCityCode'] +
        params['flightSegments'][0]['departureDate'])
    return hashlib.md5(value.encode()).hexdigest()


def request(
        sess: requests.Session,
        url: str,
        params,
        expected: int,
        accept_ranges: list,
):
    try:
        if isinstance(params, str):
            params = json.loads(params)
    except:
        pass

    try:
        r = sess.post(
            BATCH_SEARCH_URL,
            json = params,
            headers = {
                'referer': url,
                'sign': sign_param(params),
                'transactionid': params['transactionID'],
            },
        )
        r.raise_for_status()
    except Exception as e:
        msg = f'Request Error: {e}'
        logging.error(msg)
        send_msg(msg)
        return

    for i, accept_range in enumerate(accept_ranges):
        start_time, end_time = accept_range.split('-')
        start_time = datetime.strptime(
            start_time, '%H:%M') if start_time else datetime(
                year = 1900, month = 1, day = 1, hour = 0, minute = 0)
        end_time = datetime.strptime(
            start_time, '%H:%M') if end_time else datetime(
                year = 1900, month = 1, day = 1, hour = 23, minute = 59)
        accept_ranges[i] = (start_time, end_time)

    try:
        for ticket in r.json()['data']['flightItineraryList']:
            try:
                filght_id = ticket['itineraryId']
                price = min(
                    ticket['priceList'], key = lambda x: x['adultPrice'])['adultPrice']
                dep_time = ticket['flightSegments'][0]['flightList'][0][
                    'departureDateTime']
                departure_time = datetime.strptime(dep_time,
                                                   '%Y-%m-%d %H:%M:%S')
                departure_time = departure_time.replace(year = 1900, month = 1, day = 1)

                for time_range in accept_ranges:
                    if time_range[0] <= departure_time <= time_range[1]:
                        break
                else:
                    logging.info(
                        f'Skip flight {filght_id}, departure time: {dep_time}')
                    continue

                msg = f'Flight: {filght_id}({departure_time.strftime("%H:%M")}), {price} CNY'
                logging.info(msg)
                if price <= expected:
                    send_msg(msg)

            except Exception as e:
                msg = f'Parse Error: {e}'
                logging.error(msg)
                send_msg(msg)
    except Exception as e:
        msg = 'Can not get flight list'
        logging.error(f'{msg} {r.content}')
        send_msg(f'{msg}, error: {e}')


def do_query(query, headers):
    with requests.session() as sess:
        sess.headers.update(headers)
        request(
            sess,
            query['url'],
            query['params'],
            query.get('expected') or 10000,
            query.get('ranges') or ['-'],
        )


def main():
    headers = common.get_header(H)
    now = datetime.utcnow()
    logging.info(now)
    if now.minute < 2:
        send_msg('Alive')
    for query in QUERIES:
        if query['url'] != '':
            logging.info(f"querying: {query.get('tag')} ...")
            do_query(query, headers)
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        format = '%(asctime)s %(levelname)s %(message)s', level = 'INFO')
    main()
