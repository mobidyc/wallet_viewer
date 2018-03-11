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


def get_pools_infos(config, timestamp, debug=False):
    pools_tested = []
    myruns = []

    for pool in config['pools']:
        if pool['type'] == 'mpos':
            poolinfo = get_poolinfo_mpos(pool['url'], pool['api_key'], timestamp, debug)
            myruns.append(poolinfo)
        elif pool['type'] == 'yiimp':
            poolinfo = get_poolinfo_yiimp(pool['url'], timestamp, debug)
            myruns.append(poolinfo)
        else:
            print 'Unknown pool {0}: {1}'.format(pool['url'], pool['type'])

    # Wait for all threads to finish and get the data
    for i in range(len(myruns)):
        result = myruns[i].result_queue.get(True, 30)
        if result:
            for i in result:
                pools_tested.append(i)

    return pools_tested

def get_wallet_infos(config, timestamp):
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
                    if balance:
                        myval = getval_from_struct('@WWW@', ast.literal_eval(abstractstruct), balance)
                        myval = float_value(myval)
                    else:
                        myval = 0

                esdata = {
                        'tag': 'balance',
                        'explorer_url': explorer_url,
                        'explorer_name': explorer_name,
                        'currency': coin,
                        'wallet': wallet,
                        'balance': myval,
                        'timestamp': timestamp
                    }

                wallet_infos.append(esdata)
    return wallet_infos


def get_wallet_value(marketdict, wallets_dict, timestamp):
    total_bal = {}
    # sum up all the wallets with same currency
    for wallet in wallets_dict:
        print wallet
        currency = wallet['currency']
        balance = wallet['balance']
        if currency in total_bal:
            amount = total_bal['currency']['balance']
            add_amount = amount + balance
            total_bal[currency].update({'balance': add_amount})
        else:
            total_bal.update({currency: { 'balance': balance, 'timestamp': timestamp }})

    # multiply amount with price
    for currency in total_bal:
        for val in range(len(marketdict)):
            if marketdict[val]['currency'] == currency:
                if 'price_eur' in marketdict[val]:
                    value_eur = float_value(total_bal[currency]['balance']) * float_value(marketdict[val]['price_eur'])
                    value_eur = round(value_eur, 4)
                    total_bal[currency].update({'value_eur': value_eur, 'price_eur': marketdict[val]['price_eur']})
                if 'price_btc' in marketdict[val]:
                    value_btc = float_value(total_bal[currency]['balance']) * float_value(marketdict[val]['price_btc'])
                    value_btc = round(value_btc, 4)
                    total_bal[currency].update({'value_btc': value_btc, 'price_btc': marketdict[val]['price_btc']})
                if 'price_usd' in marketdict[val]:
                    value_usd = float_value(total_bal[currency]['balance']) * float_value(marketdict[val]['price_usd'])
                    value_usd = round(value_usd, 4)
                    total_bal[currency].update({'value_usd': value_usd, 'price_usd': marketdict[val]['price_usd']})
                break

    return total_bal


if __name__ == '__main__':
    es = Elasticsearch( [es_ip], port=es_port, raise_on_error = False)
    while True:
        if DEBUG:
            print "DEBUG: mode activated"

        """ VARIABLES INITIATED EACH LOOP """
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        ts = now.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (now.microsecond / 1000) + "Z"
        index_date = '{name}-{date}'.format(name = index_name, date = today)
        array_marketcap = []

        create_index(es, index_date, index_alias, index_settings, index_mappings)

        print 'Mamamaaaamarketcap!!!!...'
        array_marketcap = getCoinMarket(config['marketcap'], ts)
        if array_marketcap:
            # Ingest to ES
            send_bulk(es, array_marketcap, index_date, index_name)

        print "pool infos... "
        array_poolinfo = get_pools_infos(config, ts, DEBUG)

        print "wallet infos... "
        array_wallets = get_wallet_infos(config, ts)

        print "Internal computation"
        total_balances = get_wallet_value(array_marketcap, array_wallets, ts)

        # Ingest to ES
        send_bulk(es, array_poolinfo, index_date, index_name)
        send_bulk(es, array_wallets, index_date, index_name)
        send_bulk(es, total_balances, index_date, index_name)

        print "Wait for {0} seconds".format(ticktime)
        time.sleep(ticktime)


# APIS TO INTEGRATE
# https://github.com/forknote/forknote-pool
# https://github.com/MPOS/php-mpos/wiki/API-Reference
