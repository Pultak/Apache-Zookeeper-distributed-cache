import logging
from enum import Enum

import requests
import sys
import os


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level='DEBUG')


USAGE_MESSAGE = """Possible usages:
put <key> <value>
get <key>
delete <key>
exit
"""


class RequestType(Enum):
    PUT = 0
    GET = 1
    DELETE = 2


def setup_url(node_address, key_param, value_param):
    parameters = f"key={key_param}&value={value_param}"
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
    except Exception as e:
        logging.error(f"Request {url} failed due to {e}")


running = True


cache_nodes = os.environ['CACHE_NODES']

logging.info("Welcome to client application for control of the cache nodes!")
logging.info(f"It should be possible to connect to these nodes: {cache_nodes}")
logging.info(USAGE_MESSAGE)

# todo
quit()

while running:
    line = sys.stdin.readline()
    tokens = line.split(" ", 2)

    if len(tokens) > 0:
        action = tokens[0]

        if action == "put" and len(tokens) == 3:
            key = tokens[1]
            value = tokens[2]

        elif action == "get" and len(tokens) == 2:
            key = tokens[1]
        elif action == "delete" and len(tokens) == 2:
            key = tokens[1]
        elif action == "exit":
            running = False
            break

    logging.error(f"Invalid input! {USAGE_MESSAGE}")



