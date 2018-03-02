# wallet_viewer
will connect to appropriated explorers/pools to grab infos and collect them into Elasticsearch

## Configuration

### Global config: config.py
With DEBUG=False each output to a web api will be logged in temp_apis/ folder
With DEBUG=True the files will be used instead of web request

Change the Elasticsearch index settings if needed
```
index_settings = { "settings" : { "number_of_shards": 1, "number_of_replicas": 0, "index.codec": "best_compression" } }
```

You can also change the index name, and alias.

change you Elasticsearch access if needed
```
es_ip    = 'user:passwd@127.0.0.1'
es_port  = '9200'
```

### Wallet config: coins.json
take the template as an example

There is 3 specific blocks:
* "coins"
* "pools"
* "marketcap"


"coins"
insert your wallet (it is the public key, not the private one)
all the pools will be tested the the currency if they do support that currency

"pools"
the complex part of this configuration file.
this program does not auto detect (yet) the api format of your pool, you have to search for it.
only YIIMP and MPOS apis are supported right now.
it can help to provide an url and an output example if you need another type of pools.

"marketcap"
do not modify this block, interna only.

### Explorer config: explorers.json
It's more internal stuff but also fully incomplete
if you want to use another explorer to check your wallet, you can do it in coins.json

the "method" key is the structure to access the desired value, it should be easy to add another explorers.
Do not hesitate raising an issue or doing a pull request to improve this list.
