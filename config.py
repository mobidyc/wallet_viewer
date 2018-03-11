import json

# Global explorer conf
explorers = json.load(open('explorers.json'))

# User configuration
config = json.load(open('coins.json'))

# use file templates instead on web connections
DEBUG = False

# Index creation settings
index_name = 'cryptomoney'
index_alias = index_name
index_settings = { "settings" : {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "index.codec": "best_compression"
}}

# Seconds between iterations
ticktime = 300

es_ip    = 'localhost'
es_port  = '9200'
es_url   = 'http://{0}:{1}'.format(es_ip, es_port)

temp_folder = "/tmp"

""" some fields tye need to be enforced """
index_mappings = {
    "mappings" : {
        "cryptomoney" : {
            "properties" : {
                "balance" : { "type" : "float" }
            }
        }
    }
}



"""
saved passwd file not to appear in git the file
"es_access_hidden.py" overwrite the above es_* variables
"""
try:
    from es_access_hidden import *
except:
    pass

# Internal: update explorers method with the user specified explorers
for coin in config['coins']:
    if 'explorers' in config['coins'][coin]:
        explorers.update({coin: {"explorers": [{config['coins'][coin]['explorers']}]}})

