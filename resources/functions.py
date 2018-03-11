#!/usr/bin/env python
# -*- coding: utf-8 -*-


from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
session = FuturesSession(executor=ThreadPoolExecutor(max_workers=10))

import requests
import json
import traceback
import threading
import queue as Queue

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
        return Decimal(0.0)


def get_url_json(url):
    def bg_cb(sess, resp):
        # parse the json storing the result on the response object
        try:
            resp.data = resp.json()
        except ValueError as e:
            resp.data = e
        except:
            resp.data = "get_url_json bg_cb error"

    future = session.get(url, background_callback=bg_cb)
    try:
        response = future.result()
    except requests.exceptions.RequestException as e:
        print("Error: {0}".format(e))
        return False
    except:
        print("get_url_json error")
        return False

    if response.status_code is not 200:
        return False

    if isinstance(response.data, dict):
        response.data.update({"apiurl": url})

    return response.data


# need to handle lists
def getval_from_struct(refer_value, abstract_struct, mydict):
    for key, val in abstract_struct.items():
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
        print("Generic Exception: {}".format(traceback.format_exc()))


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
        """ result blocks, max 30 seconds """
        q.put(ret, True, 30)

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


def deadline(timeout, *args, **kwargs):
    """is a the decorator name with the timeout parameter in second"""
    def decorate(f):
        """ the decorator creation """
        def handler(signum, frame):
            """ the handler for the timeout """
            raise TimeoutException() #when the signal have been handle raise the exception

        def new_f(*args, **kwargs):
            """ the initiation of the handler,
            the lauch of the function and the end of it"""
            signal.signal(signal.SIGALRM, handler) #link the SIGALRM signal to the handler
            signal.alarm(timeout) #create an alarm of timeout second
            res = f(*args, **kwargs) #lauch the decorate function with this parameter
            signal.alarm(0) #reinitiate the alarm
            return res #return the return value of the fonction

        new_f.__name__ = f.__name__
        return new_f
    return decorate
