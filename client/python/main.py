import os

import logging
import time
from threading import Lock
from typing import Any
from kazoo.client import KazooClient

from flask import Flask, request

import cache_coherence

# app core init ///////////////
PARENT_SEARCH_ATTEMPT_COUNT = 5

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
    global values_map, values_map_lock
    with values_map_lock:
        if key in values_map:
            result = values_map[key]
            logging.debug(f"Retrieving {key} from map with value {result}")
            return result
        else:
            return None


def remove_from_map(key) -> bool:
    global values_map, values_map_lock
    with values_map_lock:
        if key in values_map:
            logging.debug(f"Removing {key} from map")
            values_map.pop(key)
            last_changes_map[key] = [True, False]
            return True
        else:
            return False


def store_in_map(key, value):
    global values_map, values_map_lock
    with values_map_lock:
        values_map[key] = value
        last_changes_map[key] = [True, False]


@app.put("/store/")
def store_value():
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
            if not root_flag:
                root_notifier.add_job(cache_coherence.JobType.REMOVE, key)
            return cache_coherence.OK_RESPONSE

    return cache_coherence.NOT_FOUND_VALUE


def search_for_parent(zoo_keeper: KazooClient) -> str:

    for i in range(0, PARENT_SEARCH_ATTEMPT_COUNT):
        path_queue = ["/"]
        logging.debug(f"Starting {i + 1}. attempt of the search for parent")
        while len(path_queue) > 0:
            curr_path = path_queue.pop()

            # begin the search for parent node
            data, stats = zoo_keeper.get(curr_path)
            if stats.children_count > 0:
                children = zoo_keeper.get_children(curr_path)
                if parent_address in children:
                    return f"{curr_path}/{parent_address}"
                for addr in children:
                    # add new paths to queue for future search
                    path_queue.append(f"{curr_path}/{addr}")

        # let's wait for a while. Maybe the parent connects
        time.sleep(5)

    return ""


def register_to_zookeeper(zoo_keeper: KazooClient):
    # Start a Zookeeper session
    zoo_keeper.start()

    if root_flag:
        zoo_keeper.create(f"/{node_address}", ephemeral=True, makepath=True)
    else:
        parent_path = search_for_parent(zoo_keeper)
        if parent_path == "":
            logging.error("Parent node not found inside zookeeper. Aborting!")
            quit()
        zoo_keeper.create(f"{parent_path}/{node_address}", ephemeral=True, makepath=True)


if __name__ == '__main__':

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
    register_to_zookeeper(zk)

    if not root_flag:
        # root doesnt need root notifier
        root_notifier.start()
    # flask run is blocking
    app.run(host=str(node_address))

    if not root_flag:
        # root doesnt need root notifier
        root_notifier.running = False
        root_notifier.join()
    # Close the session
    zk.stop()
