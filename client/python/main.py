import ipaddress
import logging
import time
import os

from threading import Lock
from typing import Any

# ZOOKEEPER
from kazoo.client import KazooClient

# REST SERVER
from flask import request
from flask import Flask
from flask_restx import Resource, Api

import root_comm
from tree_node import TreeNode

# app core init ///////////////
PARENT_SEARCH_ATTEMPT_COUNT = 5


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level='DEBUG')
app = Flask(__name__)
api = Api(app)

try:
    tree_root_address = os.environ['PARENT_NODE']
    node_address = os.environ['NODE_ADDRESS']
    ensemble = os.environ['ZOO_SERVERS']
except Exception as e:
    tree_root_address = "ROOT"
    node_address = "localhost"
    ensemble = "None"
    logging.info("Core environment variables not found. Executing in yaml generation mode. Exception " + e.__str__())

root_flag = False
root_node = None

values_map = {}
values_map_lock = Lock()

last_changes_map = {}

root_notifier = root_comm.RootSignalerThread(sleep_time=5, cache_update=20)


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



@app.route("/getParent/")
def get_parent():
    if not root_flag:
        return root_comm.METHOD_NOT_ALLOWED_RESPONSE, 405

    new_address = request.args.get('nodeName')
    try:
        ipaddress.ip_address(new_address)
    except Exception as ex:
        logging.error(f"Invalid get_parent request. Invalid IP address passed! {ex}")
        return root_comm.BAD_REQUEST_RESPONSE, 400
    result = root_node.search_for_childless(new_address)

    if result is None:
        # something failed miserably
        return root_comm.TEAPOT_RESPONSE, 418


    logging.info(f"Assigning parent '{result.address}' to node '{new_address}'")
    result.add_child(new_address)
    return result.address, 200

@api.route("/store/")
class StoringValue(Resource):
    @api.doc(
        params={
            'key': 'Key of the value you want to store to the cache system',
            'value': 'Value you want to store to the cache system'
                },
        responses={
            200: "Success",
            400: "No values/no valid values passed"
        }
    )
    def put(self):
        if root_comm.URL_KEY_PARAMETER not in request.args.keys() \
                and root_comm.URL_VALUE_PARAMETER not in request.args.keys():
            return root_comm.BAD_REQUEST_RESPONSE, 400

        key = request.args.get('key')
        value = request.args.get('value')

        if key is not None and value is not None:
            store_in_map(key, value)
            if not root_flag:
                # you are not root -> inform root of change
                root_notifier.add_job(root_comm.JobType.STORE, (key, value))
            return root_comm.OK_RESPONSE, 200
        else:
            return root_comm.BAD_REQUEST_RESPONSE, 400


@api.route('/receive/')
class RetrievingValue(Resource):

    @api.doc(
        params={
            'key': 'Key of the value you want to get from the cache system'
            },
        responses={
            200: "Success, value returned",
            204: "No value with passed kay found"
        }
    )
    def get(self):
        key = request.args.get('key')

        logging.debug(f"HTTP GET /receive/ called with key {key}")
        if key is not None:
            val = get_from_map(key)
            if val is not None:
                logging.info(f"For key '{key}' returning value '{val}'")
                return val, 200
            elif not root_flag:
                logging.debug(f"The key '{key}' is not stored in this cache. Lets ask our parent")
                parent_response, status_code = root_notifier.get_root_value(key)
                logging.info(f"For key '{key}' parent {root_notifier.parent_address} responded: {status_code}, {parent_response}")
                return parent_response, status_code
        return root_comm.NOT_FOUND_VALUE, 204


@api.route('/remove/')
class RemovingValue(Resource):

    @api.doc(
        params={
            'key': 'Key you want to delete from the cache system'
            },
        responses={
            200: "Success, value deleted",
            204: "No value with passed kay found"
        }
    )
    def delete(self):
        key = request.args.get('key')
        logging.debug(f"HTTP DELETE /remove/ called with key {key}")

        if key is not None:
            removed_flag = remove_from_map(key)

            if not root_flag:
                root_notifier.add_job(root_comm.JobType.REMOVE, key)
            if removed_flag is True:
                return root_comm.OK_RESPONSE, 200

        return root_comm.NOT_FOUND_VALUE, 204


def search_for_parent(zoo_keeper: KazooClient) -> str:
    """
    Function for BFS of the parent address in the ZooKeeper tree structure
    :param zoo_keeper: zookeeper client to get its tree structure
    :return:
    """
    for i in range(0, PARENT_SEARCH_ATTEMPT_COUNT):
        path_queue = ["/"]
        logging.debug(f"Starting {i + 1}. attempt of the search for ZooKeeper parent")
        while len(path_queue) > 0:
            curr_path = path_queue.pop()

            # begin the search for parent node
            data, stats = zoo_keeper.get(curr_path)
            if stats.children_count > 0:
                children = zoo_keeper.get_children(curr_path)
                if root_notifier.parent_address in children:
                    return f"{curr_path}/{root_notifier.parent_address}"
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
        if not zoo_keeper.exists(f"/{node_address}"):
            logging.info("Creating new node inside ZooKeeper tree structure")
            zoo_keeper.create(f"/{node_address}",
                              # ephemeral=True,  # ephemeral -> means this node cant have children
                              makepath=True)
    else:
        parent_path = search_for_parent(zoo_keeper)
        if parent_path == "":
            logging.error("Parent node not found inside zookeeper. Aborting!")
            quit()
        new_full_path = f"{parent_path}/{node_address}"
        if not zoo_keeper.exists(new_full_path):
            logging.info("Creating new node inside ZooKeeper tree structure")
            zoo_keeper.create(new_full_path, makepath=True)


def get_parent_address():

    # 5 attempts to get parent address
    for i in range(0, 5):

        response = root_notifier.ask_tree_root_for_parent(tree_root_address, node_address)
        if response is not None:
            root_notifier.parent_address = response
            break


if __name__ == '__main__':

    logging.info('Welcome to distributed binary tree cache client!')

    if tree_root_address == "ROOT":
        # this client is root
        root_flag = True
        logging.info('Im ROOT of the tree (' + node_address + ')!')
        root_node = TreeNode(node_address, None)
    else:
        get_parent_address()
        logging.info('Im LEAF of the tree (' + node_address + ')! My parent is ' + root_notifier.parent_address)
        if root_notifier.parent_address is None:
            logging.error("My parent is None! Cant continue")
            quit()

    print(f"Client will use these Kazoo servers: {ensemble}.")
    # Create the client instance
    zk = KazooClient(hosts=ensemble)
    if ensemble != "None":
        register_to_zookeeper(zk)

    if not root_flag:
        # root doesnt need root notifier
        root_notifier.start()
    # flask run is blocking
    app.run(host=str(node_address), debug=True)

    if not root_flag:
        # root doesnt need root notifier
        root_notifier.running = False
        root_notifier.join()
    # Close the session
    zk.stop()
