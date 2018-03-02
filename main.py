#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psutil
import json
import pprint
import socket
import sys
import time
import requests
import ast
import random
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

from config import *
from functions import *


def get_pools_infos(config):
    pools_tested = []
    for pool in config['pools']:
        if pool['type'] == 'mpos':
            poolinfo = get_poolinfo_mpos(pool['url'], pool['api_key'], DEBUG)
            if poolinfo:
                for i in poolinfo:
                    pools_tested.append(i)
        elif pool['type'] == 'yiimp':
            poolinfo = get_poolinfo_yiimp(pool['url'], DEBUG)
            if poolinfo:
                for i in poolinfo:
                    pools_tested.append(i)
        else:
            print '{0}: {1}'.format(pool['url'], pool['type'])
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

                log_file = "temp_apis/{coin}-{wallet}-0.log".format(coin=coin, wallet=wallet)
                url = explorer_url.replace('@WALLET@', wallet)
                if DEBUG:
                    print "DEBUG: Explorer ({0}) currency ({1}) wallet ({2})".format(url, coin, wallet)
                    balance = json.load(open(log_file))
                else:
                    try:
                        r = requests.get(url, verify=False)
                    except:
                        continue

                    if r.status_code is not 200:
                        continue

                    balance = json.loads(r.content)
                    # write output to help next debug
                    write_log(log_file, balance, "w")

                # in case the wallet is not found or real error
                try:
                    if 'error' in balance:
                        continue
                except:
                    pass

                # If abstractstruct is not defined, we should have the value
                if not abstractstruct:
                    myval = balance
                else:
                    myval = getval_from_struct('@WWW@', ast.literal_eval(abstractstruct), balance)

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

def test_es_conx():
    # make sure ES is up and running
    try:
        r = requests.get(es_url, verify=False)
        return r.status_code
    except:
        return 500

def create_index(es):
    if not es.indices.exists(index=index_date):
        # Ignore 400 cause by IndexAlreadyExistsException when creating an index
        es.indices.create(index=index_date, body=index_settings, ignore=400)
        # Set the alias
        es.indices.put_alias(index=index_date, name=index_alias)

if __name__ == '__main__':
    es = Elasticsearch( [es_ip], port=es_port)
    while True:
        if DEBUG:
            print "DEBUG: mode activated"
        """
        else:
            fun = ['Wallets tic... ', 'Wallets tac... ']
            print fun[random.randint(0,1)],
            sys.stdout.flush()
        """

        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        ltime = now.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (now.microsecond / 1000) + "Z"
        index_date = '{name}-{date}'.format(name = index_name, date = today)

        if test_es_conx() is not 200:
            print 'Connection waiting'
            try:
                es = Elasticsearch( [es_ip], port = es_port, request_timeout = 30)
                time.sleep(5)
            except:
                pass
            continue

        create_index(es)

        """
        We do not want to run marketcap every ticks
        """
        array_marketcap = []
        try:
            marketcap_tick += 1
        except NameError:
            marketcap_tick = marketcap_tick_times

        """
        START MARKETCAP
        """
        if marketcap_tick >= marketcap_tick_times:
            print 'Mamamaaaamarketcap!!!!...'
            marketcap_tick = 0
            array_marketcap = getCoinMarket(config['marketcap'])
            for i in array_marketcap:
                i.update({'timestamp': ltime})

        # Ingest data
        if array_marketcap:
            count = 0
            array_limit = []
            for i in array_marketcap:
                count += 1
                array_limit.append(i)
                if count == 250:
                    print   "send bulk {0}... ".format(250)
                    try:
                        bulk(es, array_limit, index=index_date, doc_type=index_name, raise_on_error = False)
                    except:
                        pass
                    array_limit = []
                    count = 0
            try:
                bulk(es, array_limit, index=index_date, doc_type=index_name, raise_on_error = False)
            except:
                pass
        """
        END MARKETCAP
        """

        print "pool infos... "
        array_poolinfo = get_pools_infos(config)
        for i in array_poolinfo:
            i.update({'timestamp': ltime})

        print "wallet infos... "
        array_wallets = get_wallet_infos(config)

        try:
            bulk(es, array_poolinfo, index=index_date, doc_type=index_name, raise_on_error = False)
            bulk(es, array_wallets, index=index_date, doc_type=index_name, raise_on_error = False)
        except:
            pass

        print "Wait for {0} seconds".format(ticktime)
        time.sleep(ticktime)


# APIS TO INTEGRATE
# https://github.com/forknote/forknote-pool
# https://github.com/MPOS/php-mpos/wiki/API-Reference
