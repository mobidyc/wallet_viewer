#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
from resources.functions import *
from config import *


def _get_mpos_info(url, apikey, debug=False):
    # {"getpoolinfo":{"version":"1.0.0","runtime":4.1921138763428,"data":{"currency":"YTN","coinname":"Yenten","cointarget":"120","coindiffchangetarget":1,"algorithm":"yescrypt","stratumport":"3333","payout_system":"prop","confirmations":100,"min_ap_threshold":1,"max_ap_threshold":250,"reward_type":"block","reward":50,"txfee":0.1,"txfee_manual":0.1,"txfee_auto":0.05,"fees":0.45}}}

    weburl = '{0}/index.php?page=api&action=getpoolinfo&api_key={1}'.format(url, apikey)
    log_file = "{0}/MPOS-poolinfo-apikey.log".format(temp_folder)

    if debug:
        print("DEBUG: MPOS info url: {0}".format(weburl))
        res = json.load(open(log_file))
    else:
        res = get_url_json(weburl)
        write_log(log_file, res, "w")

    return res


@threaded
def get_poolinfo_mpos(url, apikey, timestamp, debug=False):
    poolinfo = _get_mpos_info(url, apikey)

    pool_arr = []
    if poolinfo:
        pool = poolinfo['getpoolinfo']['data']
        algo = ""
        if 'algorithm' in pool.keys():
            algo = pool['algorithm']

        try:
            poolinfo = {
                'tag': 'poolinfo',
                'timestamp': timestamp,
                'url': url,
                'coinname': pool['coinname'],
                'currency': pool['currency'],
                'algorithm': algo,
                'apikey': apikey,
                'pooltype': 'mpos'
            }
            poolinfo.update({'fees': float_value(pool['fees'],)})
            poolinfo.update({'port': pool['stratumport']})

            pool_arr.append(poolinfo)
        except Exception:
            print("Generic Exception mpos: {0} - url: {1}".format(traceback.format_exc()), url)
            return False
        except:
            print("get_poolinfo_mpos error")
            return False

    return pool_arr


def get_mpos_difficulty():
    """
    /index.php?page=api&api_key=$API&action=getdifficulty
    {"getdifficulty":{"version":"1.0.0","runtime":3.0710697174072,"data":0.0858135}}
    """
    pass

def get_mpos_userwokrs():
    """
    /index.php?page=api&api_key=$API&action=getuserworkers
    {"getuserworkers":{"version":"1.0.0","runtime":27.462959289551,"data":[{"id":8862,"username":"mobidyc.argon","password":"da_test","monitor":0,"count_all":33,"shares":4.5143239796162,"hashrate":0.49,"difficulty":0.14},{"id":9056,"username":"mobidyc.magnesium","password":"da_test","monitor":0,"count_all":0,"shares":0,"hashrate":0,"difficulty":0},{"id":9805,"username":"mobidyc.magnet","password":"da_test","monitor":0,"count_all":40,"shares":2.2378358244896,"hashrate":0.24,"difficulty":0.06},{"id":9969,"username":"mobidyc.player","password":"da_test","monitor":0,"count_all":0,"shares":0,"hashrate":0,"difficulty":0}]}}
    """
    pass

def _get_mpos_balance():
    """
    /index.php?page=api&api_key=$API&action=getuserbalance
    {"getuserbalance":{"version":"1.0.0","runtime":8.577823638916,"data":{"confirmed":"4.727564720000000000000000000000","unconfirmed":"1.762532840000000000000000000000","orphaned":"0.000000000000000000000000000000"}}}
    """
    pass

def get_mpos_userstatus():
    """
    /index.php?page=api&api_key=$API&action=getuserstatus
    {"getuserstatus":{"version":"1.0.0","runtime":87.05997467041,"data":{"username":"mobidyc","shares":{"valid":2.3750030845404,"invalid":0},"hashrate":0.8543311702474,"sharerate":0.013036059116324}}}
    """
    pass
