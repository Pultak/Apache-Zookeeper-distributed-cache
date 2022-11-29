import logging
from enum import Enum

import requests
import sys
import os


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level='DEBUG')


USAGE_MESSAGE = """Possible usages:
put <node_id> <key> <value>
get <node_id> <key>
delete <node_id> <key>
exit

Where both <key> and <value> can be any arbitrary string.
And <node_id> is a index of cache node you want to send request to.
"""


class RequestType(Enum):
    PUT = 0
    GET = 1
    DELETE = 2


def setup_url(node_address, key_param, value_param) -> str:
    parameters = f"key={key_param}"
    if value_param is not None:
        parameters += f"&value={value_param}"
    res_address = f"http://{node_address}:5000/store?{parameters}"
    return res_address


def execute_http_request(url, req_type):
    try:
        if req_type == RequestType.GET:
            logging.debug(f"Sending HTTP GET to {url}")
            response = requests.get(url).text
        elif req_type == RequestType.PUT:
            logging.debug(f"Sending HTTP PUT to {url}")
            response = requests.put(url).text
        elif req_type == RequestType.DELETE:
            logging.debug(f"Sending HTTP DELETE to {url}")
            response = requests.delete(url).text
        else:
            logging.error("Unknown request type!")
            return
        logging.info("Node responded: %s" % response)
    except Exception as ex:
        logging.error(f"Request {url} failed due to {ex}")


running = True


client_count = int(os.environ["CLIENT_COUNT"])
address_offset = int(os.environ["ADDRESS_OFFSET"])
base_subnet = os.environ["BASE_SUBNET"]

cache_nodes = []
for i in range(1, client_count):
    cache_nodes.append(base_subnet + str(address_offset + client_count))

logging.info("Welcome to client application for control of the cache nodes!")
logging.info(f"It should be possible to connect to these nodes: {cache_nodes}")
logging.info(USAGE_MESSAGE)

if len(cache_nodes) < 1:
    logging.error("There are no nodes to connect to!")
    quit()

while running:
    line = sys.stdin.readline()
    print("\n")
    tokens = line.split(" ", 2)

    if len(tokens) > 0:
        action = tokens[0]
        try:
            if action == "put" and len(tokens) == 4:
                node_id = int(tokens[1])
                key = tokens[2]
                value = tokens[3]
                execute_http_request(setup_url(cache_nodes[node_id], key, value), RequestType.PUT)
            elif action == "get" and len(tokens) == 3:
                node_id = int(tokens[1])
                key = tokens[2]
                execute_http_request(setup_url(cache_nodes[node_id], key, None), RequestType.GET)
            elif action == "delete" and len(tokens) == 3:
                node_id = int(tokens[1])
                key = tokens[2]
                execute_http_request(setup_url(cache_nodes[node_id], key, None), RequestType.DELETE)
            elif action == "exit":
                running = False
                break
        except Exception as e:
            logging.error(f"Please insert only input valid data! {e}")
    else:
        logging.error(f"Invalid input! {USAGE_MESSAGE}")
