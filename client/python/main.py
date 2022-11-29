import os

import logging
import socket
import time
from threading import Lock
from typing import Any
from kazoo.client import KazooClient

from flask import Flask, request, jsonify

import cache_coherence

# app core init ///////////////

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level='DEBUG')
app = Flask(__name__)

parent_address = os.environ['PARENT_NODE']
node_address = os.environ['NODE_ADDRESS']
ensemble = os.environ['ZOO_SERVERS']

root_flag = False

values_map = {}
values_map_lock = Lock()

last_changes_map = {}

root_notifier = cache_coherence.CacheCoherenceThread(parent_address, sleep_time=5, cache_update=20)


def get_from_map(key) -> Any:
    with values_map_lock:
        if key in values_map:
            result = values_map[key]
            logging.debug(f"Retrieving {key} from map with value {result}")
            return result
        else:
            return None


def remove_from_map(key) -> bool:
    with values_map_lock:
        if key in values_map:
            logging.debug(f"Removing {key} from map")
            values_map.pop(key)
            last_changes_map[key] = [True, False]
            return True
        else:
            return False


def store_in_map(key, value):
    with values_map_lock:
        values_map[key] = value
        last_changes_map[key] = [True, False]


@app.put("/store/")
def store_value():
    global values_map
    if cache_coherence.URL_KEY_PARAMETER not in request.args.keys()\
            and cache_coherence.URL_VALUE_PARAMETER not in request.args.keys():
        return cache_coherence.BAD_REQUEST_RESPONSE

    key = request.args.get('key')
    value = request.args.get('value')

    if key is not None and value is not None:
        store_in_map(key, value)
        if not root_flag:
            # you are not root -> inform root of change
            root_notifier.add_job(cache_coherence.JobType.STORE, (key, value))
        return cache_coherence.OK_RESPONSE
    else:
        return cache_coherence.BAD_REQUEST_RESPONSE


@app.get('/receive/')
def return_desired_value():
    key = request.args.get('key')

    logging.debug(f"HTTP GET /receive/ called with key {key}")
    if key is not None:
        val = get_from_map(key)
        if val is not None:
            return str(val)
        elif not root_flag:
            return root_notifier.get_root_value(key)
    return cache_coherence.NOT_FOUND_VALUE


@app.delete('/remove/')
def remove_value():

    key = request.args.get('key')
    logging.debug(f"HTTP DELETE /remove/ called with key {key}")

    if key is not None:
        removed_flag = remove_from_map(key)

        if removed_flag is True:
            root_notifier.add_job(cache_coherence.JobType.REMOVE, key)
            return cache_coherence.OK_RESPONSE

    return cache_coherence.NOT_FOUND_VALUE


def register_to_zookeeper(zoo_keeper):
    # Start a Zookeeper session
    zoo_keeper.start()

    # Create an ephemeral node with the same name as the hostname.
    # If the '/ds/clients' context doesn't exist yet, it will be also created
    zoo_keeper.create(f"/ds/clients/{socket.gethostname()}", ephemeral=True, makepath=True)
    return


if __name__ == '__main__':
    global root_flag

    logging.info('Welcome to distributed binary tree cache client!')

    if parent_address == "ROOT":
        # this client is root
        root_flag = True
        logging.info('Im ROOT of the tree (' + node_address + ')!')
    else:
        logging.info('Im LEAF of the tree (' + node_address + ')! My parent is ' + parent_address)

    print(f"Client will use these Kazoo servers: {ensemble}.")
    # Create the client instance
    zk = KazooClient(hosts=ensemble)

    # todo get/check correct address
    app.run(host=str(node_address))

    # Close the session
    zk.stop()
