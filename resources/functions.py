#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import traceback
from elasticsearch import ElasticsearchException
import threading
import Queue

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


def create_index(es, index, index_alias, settings={}):
    try:
        if not es.indices.exists(index=index):
            # Ignore 400 cause by IndexAlreadyExistsException when creating an index
            es.indices.create(index=index, body=settings, ignore=400)
            es.indices.put_alias(index=index, name=index_alias)
    except ElasticsearchException as e:
        print 'ES Error: {0}'.format(e.error)
        return False
    except Exception:
        print "Generic Exception: {}".format(traceback.format_exc())
        return False


def threaded(f, daemon=False):
    """
    Decorator to auto thread calls
    Get the result with decorated_func.result_queue.get()
    """
    def wrapped_f(q, *args, **kwargs):
        """
        this function calls the decorated function and puts the result in a queue
        """
        ret = f(*args, **kwargs)
        q.put(ret)

    def wrap(*args, **kwargs):
        """
        this is the function returned from the decorator. It fires off
        wrapped_f in a new thread and returns the thread object with
        the result queue attached
        """

        q = Queue.Queue()

        t = threading.Thread(target=wrapped_f, args=(q,)+args, kwargs=kwargs)
        t.daemon = daemon
        t.start()
        t.result_queue = q
        return t

    return wrap
