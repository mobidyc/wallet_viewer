#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import requests
import ast
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch import ElasticsearchException
from elasticsearch.helpers import bulk

from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

# Internal imports
from config import *
from functions import *

import sys
sys.dont_write_bytecode = True


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
            print 'Unknown pool {0}: {1}'.format(pool['url'], pool['type'])
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
                        if r.status_code is not 200:
                            continue

                        balance = json.loads(r.content)
                    except Exception:
                        print "Generic Exception: {}".format(traceback.format_exc())
                        continue

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


def create_index(es):
    try:
        if not es.indices.exists(index=index_date):
            # Ignore 400 cause by IndexAlreadyExistsException when creating an index
            es.indices.create(index=index_date, body=index_settings, ignore=400)
            # Set the alias
            es.indices.put_alias(index=index_date, name=index_alias)
    except ElasticsearchException as e:
        print 'ES Error: {0}'.format(e.error)
        return False
    except Exception:
        print "Generic Exception: {}".format(traceback.format_exc())
        return False

if __name__ == '__main__':
    es = Elasticsearch( [es_ip], port=es_port, raise_on_error = False)
    while True:
        if DEBUG:
            print "DEBUG: mode activated"

        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        ltime = now.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (now.microsecond / 1000) + "Z"
        index_date = '{name}-{date}'.format(name = index_name, date = today)

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

        # Ingest data
        if array_marketcap:
            for i in array_marketcap:
                i.update({'timestamp': ltime})
            try:
                bulk(es, array_marketcap, index=index_date, doc_type=index_name, raise_on_error = False)
            except ElasticsearchException as e:
                print 'ES Error: {0}'.format(e.error)
            except Exception:
                print "Generic Exception: {}".format(traceback.format_exc())
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
        except ElasticsearchException as e:
            print 'ES Error: {0}'.format(e.error)
        except Exception:
            print "Generic Exception: {}".format(traceback.format_exc())

        print "Wait for {0} seconds".format(ticktime)
        time.sleep(ticktime)


# APIS TO INTEGRATE
# https://github.com/forknote/forknote-pool
# https://github.com/MPOS/php-mpos/wiki/API-Reference
