#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import pprint
import sys
from datetime import datetime
from decimal import *
getcontext().prec = 10

from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)


def get_poolinfo_mpos(url, apikey, debug=False):
    """
    Retrieve pool currency informations for MPOS type api
    """
    weburl = '{0}/index.php?page=api&action=getpoolinfo&api_key={1}'.format(url, apikey)
    log_file = "temp_apis/MPOS-poolinfo-apikey.log"
    if debug:
        print "DEBUG: MPOS info url: {0}".format(weburl)
        print "DEBUG: mode log file: {}".format(log_file)
        res = json.load(open(log_file))
    else:
        try:
            r = requests.get(weburl, verify=False)
            if r.status_code is not 200:
                return False
            res = json.loads(r.content)
        except:
            return False

        write_log(log_file, res, "w")

    pool_arr = []
    if res:
        pool = res['getpoolinfo']['data']
        algo = ""
        try:
            algo = pool['algorithm']
        except:
            pass
        poolinfo = {
            'tag': 'poolinfo',
            'url': url,
            'coinname': pool['coinname'],
            'currency': pool['currency'],
            'algorithm': algo,
            'fees': pool['fees'],
            'port': pool['stratumport'],
            'apikey': apikey,
            'pooltype': 'mpos'
        }
        pool_arr.append(poolinfo)
    return pool_arr


def get_poolinfo_yiimp(url, debug=False):
    """
    Retrieve pool currency informations for YIIMP type api

    sometimes algo in currency and status are not in the same case...
    I'll do an ugly lowercase in both to handle that
    """
    status = '{0}/api/status'.format(url)
    log_file = "temp_apis/YIIMP-poolinfo-status.log"
    if debug:
        print "DEBUG: YIIMP status url: {0}".format(status)
        poolstat = json.load(open(log_file))
    else:
        try:
            r = requests.get(status, verify=False)
        except:
            return False

        if r.status_code is not 200:
            return False
        try:
            poolstat = json.loads(r.content)
        except:
            return False

        # Ugly but needed
        poolstat = {k.lower(): v for k, v in poolstat.items()}

        write_log(log_file, poolstat, "w")

    currencies = '{0}/api/currencies'.format(url)
    log_file = "temp_apis/YIIMP-poolinfo-currency.log"
    if debug:
        print "DEBUG: YIIMP currency url: {0}".format(currencies)
        poolcurr = json.load(open(log_file))
    else:
        try:
            r = requests.get(currencies, verify=False)
        except:
            return False

        if r.status_code is not 200:
            return False
        try:
            poolcurr = json.loads(r.content)
        except:
            return False

        # Ugly but needed
        for k, v in poolcurr.items():
            for k2, v2 in v.items():
                if k2 == 'algo':
                    v[k2] = v2.lower()

        write_log(log_file, poolcurr, "w")

    pool_arr = []
    if poolstat and poolcurr:
        for coin in poolcurr:
            algo = poolcurr[coin]['algo']

            poolinfo = {
                'tag': 'poolinfo',
                'url': url,
                'coinname': poolcurr[coin]['name'],
                'currency': coin,
                'algorithm': algo,
                'fees': poolstat[algo]['fees'],
                'port': poolstat[algo]['port'],
                'pooltype': 'yiimp'
            }
            pool_arr.append(poolinfo)
    return pool_arr


def getCoinMarket(info, debug=False):
    name = info["name"]
    api = info["apiurl"]
    url = '{0}/?convert=EUR&limit=0'.format(api)

    log_file = "temp_apis/{0}.log".format(name)
    if debug:
        print "DEBUG: mode log file: {}".format(log_file)
        res = json.load(open(log_file))
    else:
        try:
            r = requests.get(url, verify=False)
        except:
            return False
        if r.status_code is not 200:
            return False

        res = json.loads(r.content)
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
        except:
            print "Unexpected error:", sys.exc_info()[0]
            continue

        coins_array.append(coin_info)
    return coins_array

def float_value(val):
    try:
        return Decimal(val)
    except:
        return 0.0

# need to handle lists
def getval_from_struct(refer_value, abstract_struct, mydict):
    for key, val in abstract_struct.iteritems():
        if val == refer_value:
            return mydict[key]
        elif isinstance(val, list):
            continue
        else:
            return getval_from_struct(refer_value, val, mydict[key])


def write_log(dest, txt, mode):
    with open(dest, mode) as outfile:
        json.dump(txt, outfile, indent=4)
