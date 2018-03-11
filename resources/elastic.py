#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticsearch import ElasticsearchException
from elasticsearch.helpers import bulk
import traceback


def create_index(es, index, index_alias, settings={}, mappings={}):
    try:
        if not es.indices.exists(index=index):
            # Ignore 400 cause by IndexAlreadyExistsException when creating an index
            es.indices.create(index=index, body=settings, ignore=400)
            es.indices.create(index=index, body=mappings, ignore=400)
            es.indices.put_alias(index=index, name=index_alias)
    except ElasticsearchException as e:
        print('ES Error: {0}'.format(e.error))
        return False
    except Exception:
        print("Generic Exception: {}".format(traceback.format_exc()))
        return False


def send_bulk(es, body, index, doctype, err=False):
    try:
        bulk(es, body, index=index, doc_type=doctype, raise_on_error=err)
    except ElasticsearchException as e:
        print('ES Error: {0}'.format(e.error))
    except Exception:
        print("Generic Exception: {}".format(traceback.format_exc()))
