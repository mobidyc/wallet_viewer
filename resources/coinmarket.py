#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
from datetime import datetime
from resources.functions import *
from config import *


def getCoinMarket(info, timestamp, debug=False):
    name = info["name"]
    api = info["apiurl"]
    url = '{0}/?convert=EUR&limit=0'.format(api)

    log_file = "{0}/{1}.log".format(temp_folder, name)
    if debug:
        print "DEBUG: mode log file: {}".format(log_file)
        res = json.load(open(log_file))
    else:
        res = get_url_json(url)
        write_log(log_file, res, "w")

    coins_array = []
    for coin in res:
        try:
            ts = int(coin['last_updated'])
            ts = datetime.fromtimestamp(ts).strftime('%Y/%m/%d %H:%M:%S')
        except:
            ts = 0

        try:
            coin_info = {
                'tag': 'marketcap',
                'timestamp': timestamp,
                'coinname': coin['name'],
                'currency': coin['symbol'],
                'rank': float_value(coin['rank']),
                'price_usd': float_value(coin['price_usd']),
                'price_btc': float_value(coin['price_btc']),
                '24h_volume_usd': float_value(coin['24h_volume_usd']),
                'market_cap_usd': float_value(coin['market_cap_usd']),
                'available_supply': float_value(coin['available_supply']),
                'total_supply': float_value(coin['total_supply']),
                'max_supply': float_value(coin['max_supply']),
                'percent_change_1h': float_value(coin['percent_change_1h']),
                'percent_change_24h': float_value(coin['percent_change_24h']),
                'percent_change_7d': float_value(coin['percent_change_7d']),
                'last_updated': ts,
                'price_eur': float_value(coin['price_eur']),
                '24h_volume_eur': float_value(coin['24h_volume_eur']),
                'market_cap_eur': float_value(coin['market_cap_eur'])
            }
        except Exception:
            print "Generic Exception: {}".format(traceback.format_exc())
            continue

        coins_array.append(coin_info)
    return coins_array
