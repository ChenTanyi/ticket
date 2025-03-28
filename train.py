#!/usr/bin/env python3
import datetime
import os
import re
import time
import json
import yaml
import common
import requests
import logging

H = '''Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en,en-US;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5
Cache-Control: no-cache
Connection: keep-alive
Cookie: {0}
Host: kyfw.12306.cn
If-Modified-Since: 0
Referer: https://kyfw.12306.cn/otn/leftTicket/init
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36
X-Requested-With: XMLHttpRequest'''.format(os.environ.get('TRAIN_COOKIE'), '')

API_COLUMN = [
    '', '按钮', '列车号', '车次', '起始站代码', '到达站代码', '出发站', '到达站', '出发时间', '到达时间', '历时',
    '是否可购买', 'yp_info', '出发日期', 'train_seat_feature', 'location_code',
    'from_station_no', 'to_station_no', 'is_support_code',
    'controlled_train_flag', 'gg_num', '高级软卧', '其他', '软卧', '软座', '特等座', '无座',
    'yb_num', '硬卧', '硬座', '二等座', '一等座', '商务座', '动卧', 'yp_ex', 'seat_type',
    'exchange_train_flag', '候补标记', '候补座位限制'
]

SAMPLE_QUERIES = '''\
- url: https://kyfw.12306.cn/otn/leftTicket/queryR?leftTicketDTO.train_date=2025-04-04&leftTicketDTO.from_station=IOQ&leftTicketDTO.to_station=IZQ&purpose_codes=ADULT
  start_times:
    06:36:
      seats: [二等座]
      unwant_tickets: [无]
'''
QUERIES = yaml.safe_load(os.environ.get('TRAIN_QUERY', SAMPLE_QUERIES))


def send_msg(msg):
    common.send_msg('Train', msg)


def request(sess, url, start_time2tickets):
    try:
        r = sess.get(url)
        r.raise_for_status()
        resp = r.json()
    except Exception as e:
        send_msg(f'Requests Error: {e}')
        return
    try:
        code_to_station = resp['data']['map']
        results = resp['data']['result']
        for result in results:
            trains = result.split('|')
            from_station = code_to_station[trains[6]]
            to_station = code_to_station[trains[7]]
            start_time = trains[8]
            end_time = trains[9]
            msg = f'{from_station}({start_time}) -> {to_station}({end_time})\n'

            tickets = {}
            if '*' in start_time2tickets:
                tickets = start_time2tickets['*']
            elif start_time in start_time2tickets:
                tickets = start_time2tickets[start_time]
            else:
                continue

            need_send = False
            for seat in tickets.get('seats'):
                seat_index = API_COLUMN.index(seat)
                msg += f'{seat}: {trains[seat_index]}\n'
                if trains[seat_index] not in tickets.get('unwant_tickets'):
                    need_send = True

            logging.info(msg)
            if need_send:
                send_msg(msg)
    except Exception as e:
        send_msg(f'Parse Error: {e}')


def main():
    headers = common.get_header(H)
    with requests.session() as sess:
        sess.headers.update(headers)
        now = datetime.datetime.now(datetime.UTC)
        logging.info(now)
        if now.minute < 2:
            send_msg('Alive')
        for query in QUERIES:
            if query['url'] != '':
                request(sess, query['url'], query['start_times'])


if __name__ == '__main__':
    logging.basicConfig(
        format = '%(asctime)s %(levelname)s %(message)s', level = 'INFO')
    main()
