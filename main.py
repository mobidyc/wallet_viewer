#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode = True

import json
import time
import ast
from datetime import datetime
from elasticsearch import Elasticsearch
import pprint

# Internal imports
from config import *
from resources.functions import *
from resources.elastic import *
from resources.yiimp import *
from resources.mpos import *
from resources.coinmarket import *


def get_pools_infos(config, debug=False):
    pools_tested = []
    myruns = []

    for pool in config['pools']:
        if pool['type'] == 'mpos':
            poolinfo = get_poolinfo_mpos(pool['url'], pool['api_key'], debug)
            myruns.append(poolinfo)
        elif pool['type'] == 'yiimp':
            poolinfo = get_poolinfo_yiimp(pool['url'], debug)
            myruns.append(poolinfo)
        else:
            print 'Unknown pool {0}: {1}'.format(pool['url'], pool['type'])

    # Wait for all threads to finish and get the data
    for i in range(len(myruns)):
        result = myruns[i].result_queue.get()
        if result:
            for i in result:
                pools_tested.append(i)

    return pools_tested

def get_wallet_infos(config):
    wallet_infos = []
    for coin in config['coins']:
        print "{0}...".format(coin),

        # Try to get the current balance on all wallets
        for wallet in config['coins'][coin]['wallets']:
            if coin in explorers.keys():
                # In the future, handle list of explorers for fail over
                expl = explorers[coin]['explorers'][0]

                explorer_url = expl['url']
                explorer_name = expl['name']
                abstractstruct = expl['method']

                log_file = "{tmp}/{coin}-{wallet}-0.log".format(tmp=temp_folder, coin=coin, wallet=wallet)
                url = explorer_url.replace('@WALLET@', wallet)
                if DEBUG:
                    print "DEBUG: Explorer ({0}) currency ({1}) wallet ({2})".format(url, coin, wallet)
                    balance = json.load(open(log_file))
                else:
                    balance = get_url_json(url)
                    # write output to help next debug
                    write_log(log_file, balance, "w")

                # in case the wallet is not found or real error
                try:
                    if 'error' in balance:
                        continue
                except TypeError:
                    pass
                except Exception:
                    print "Generic Exception: {}".format(traceback.format_exc())
                    continue

                # If abstractstruct is not defined, we should have the value
                if not abstractstruct:
                    myval = balance
                else:
                    myval = getval_from_struct('@WWW@', ast.literal_eval(abstractstruct), balance)
                    myval = float_value(myval)

                esdata = {
                        'tag': 'balance',
                        'explorer_url': explorer_url,
                        'explorer_name': explorer_name,
                        'currency': coin,
                        'wallet': wallet,
                        'balance': myval,
                        'timestamp': ltime
                    }

                wallet_infos.append(esdata)
    return wallet_infos


if __name__ == '__main__':
    es = Elasticsearch( [es_ip], port=es_port, raise_on_error = False)
    while True:
        if DEBUG:
            print "DEBUG: mode activated"

        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        ltime = now.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (now.microsecond / 1000) + "Z"
        index_date = '{name}-{date}'.format(name = index_name, date = today)

        create_index(es, index_date, index_alias, index_settings)

        """
        We do not want to run marketcap every ticks
        """
        array_marketcap = []
        try:
            marketcap_tick += 1
        except NameError:
            marketcap_tick = marketcap_tick_times

        if marketcap_tick >= marketcap_tick_times:
            marketcap_tick = 0
            """
            START MARKETCAP
            """
            print 'Mamamaaaamarketcap!!!!...'
            array_marketcap = getCoinMarket(config['marketcap'])
            if array_marketcap:
                for i in array_marketcap:
                    i.update({'timestamp': ltime})
                # Ingest to ES
                send_bulk(es, array_marketcap, index_date, index_name)
            """
            END MARKETCAP
            """

        print "pool infos... "
        array_poolinfo = get_pools_infos(config, DEBUG)
        for i in array_poolinfo:
            i.update({'timestamp': ltime})

        print "wallet infos... "
        array_wallets = get_wallet_infos(config)

        # Ingest to ES
        send_bulk(es, array_poolinfo, index_date, index_name)
        send_bulk(es, array_wallets, index_date, index_name)

        print "Wait for {0} seconds".format(ticktime)
        time.sleep(ticktime)


# APIS TO INTEGRATE
# https://github.com/forknote/forknote-pool
# https://github.com/MPOS/php-mpos/wiki/API-Reference
