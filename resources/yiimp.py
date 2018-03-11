#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
from resources.functions import *
from config import *


@threaded
def get_poolinfo_yiimp(url, timestamp, debug=False):
    """
    Retrieve pool currency informations for YIIMP type api
    """
    poolstat = _get_yiimp_status(url, debug)
    poolcurr = _get_yiimp_currencies(url, debug)

    pool_arr = []
    if poolstat and poolcurr:
        # Ugly but needed: lowercase the keys
        poolstat = {k.lower() if isinstance(k, str) else k: v.lower() if isinstance(v, str) else v for k,v in poolstat.items()}
        try:
            apiurl = poolcurr['apiurl']
            del poolcurr['apiurl']
        except Exception:
            apiurl = url
            pass

        for coin in poolcurr:
            try:
                algo     = poolcurr[coin]['algo'].lower()
                coinname = poolcurr[coin]['name']
                poolinfo = {
                    'tag': 'poolinfo',
                    'timestamp': timestamp,
                    'url': apiurl,
                    'coinname': coinname,
                    'currency': coin,
                    'algorithm': algo,
                    'pooltype': 'yiimp'
                }
                poolinfo.update({'fees': float_value(poolstat[algo]['fees'])})
                poolinfo.update({'port': poolstat[algo]['port']})

                pool_arr.append(poolinfo)
            except Exception:
                print("Generic Exception: {}".format(traceback.format_exc()))
                continue
            except:
                print("get_poolinfo_yiimp error")
                continue
    return pool_arr


def _get_yiimp_walletex(url, wallet, debug=False):
    # {"currency": "RVN", "unsold": 1.520398350026384, "balance": 1.24986000, "unpaid": 2.77025835, "paid24h": 7.25007630, "total": 10.02033465, "miners": [{"version": "ccminer\/2.2.5", "password": "c=RVN", "ID": "", "algo": "x16r", "difficulty": 6, "subscribe": 1, "accepted": 1718008.909, "rejected": 0}]}

    wallet_url = '{0}/api/walletEx?address={1}'.format(url, wallet)
    log_file = "{0}/YIIMP-poolinfo-wallet.log".format(temp_folder)

    if debug:
        print("DEBUG: YIIMP wallet url: {0}".format(currencies_url))
        wallet = json.load(open(log_file))
    else:
        # Ask the API
        wallet = get_url_json(wallet_url)

        # if needed to debug
        write_log(log_file, wallet, "w")

    return wallet


def _get_yiimp_currencies(url, debug=False):
    # {"KREDS":{"algo":"lyra2v2","port":4533,"name":"Kreds","height":19266,"workers":17,"shares":606,"hashrate":2626458401,"estimate":"0.00000","24h_blocks":37,"24h_btc":0,"lastblock":19259,"timesincelast":1473}}

    currencies_url = '{0}/api/currencies'.format(url)
    log_file = "{0}/YIIMP-poolinfo-currency.log".format(temp_folder)

    if debug:
        print("DEBUG: YIIMP currency url: {0}".format(currencies_url))
        poolcurr = json.load(open(log_file))
    else:
        # Ask the API
        poolcurr = get_url_json(currencies_url)

        # if needed to debug
        write_log(log_file, poolcurr, "w")

    return poolcurr


def _get_yiimp_status(url, debug=False):
    # {"lyra2v2":{"name":"lyra2v2","port":4533,"coins":1,"fees":0,"hashrate":2741907122,"workers":17,"estimate_current":"0.00000000","estimate_last24h":"0.00000000","actual_last24h":"0.00000","hashrate_last24h":2171269381.9896}}

    status_url = '{0}/api/status'.format(url)
    log_file = "{0}/YIIMP-poolinfo-status.log".format(temp_folder)

    if debug:
        print("DEBUG: YIIMP status url: {0}".format(status_url))
        poolstat = json.load(open(log_file))
    else:
        # Ask the API
        poolstat = get_url_json(status_url)

        # if needed to debug
        write_log(log_file, poolstat, "w")

    return poolstat

