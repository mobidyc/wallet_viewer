#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import traceback

from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

from decimal import *
getcontext().prec = 10


def float_value(val):
    # Force type to be a float
    try:
        return Decimal(val)
    except:
        return 0.0


def get_url_json(url):
    try:
        r = requests.get(url, verify=False)
    except requests.exceptions.RequestException as e:
        print "Get URL error: {0} - {1}".format(url, e)
        return False
    except Exception:
        print "Generic Exception: {}".format(traceback.format_exc())
        return False

    if r.status_code is not 200:
        return False

    try:
        result = json.loads(r.content)
    except ValueError:
        print "Decoding JSON has failed"
        return False

    if isinstance(result, dict):
	     result.update({"apiurl": url})

    return result


# need to handle lists
def getval_from_struct(refer_value, abstract_struct, mydict):
    for key, val in abstract_struct.iteritems():
        if val == refer_value:
            return mydict[key]
        elif isinstance(val, list):
            continue
        else:
            return getval_from_struct(refer_value, val, mydict[key])
    # If not found
    return False


def write_log(dest, txt, mode):
    try:
        with open(dest, mode) as outfile:
            json.dump(txt, outfile, indent=4)
    except Exception:
        print "Generic Exception: {}".format(traceback.format_exc())
