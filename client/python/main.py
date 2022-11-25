import os

import logging
import socket
import time

from flask import Flask, request, jsonify

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level='INFO')
app = Flask(__name__)
# hack to let the vagrant setup eth1 interface for http server
time.sleep(2)

root_flag = False


@app.put("/store/")
def store_value():
    # todo
    new_value = request.get_data()

    return "Ok"


@app.get('/receive/<>')
def return_desired_value():
    # todo
    new_value = request.get_data()

    return "NotFound"


@app.delete('/remove/')
def remove_value():
    # todo
    new_value = request.get_data()

    return "NotFound"


@app.get('/update/')
def send_cache_update():
    # todo send update on value change

    return ""


def register_to_zookeeper():

    # todo register
    return


if __name__ == '__main__':
    global root_flag
    parent_address = os.environ['PARENT_NODE']
    node_address = os.environ['NODE_ADDRESS']

    logging.info('Welcome to distributed binary tree cache client!')

    if parent_address == "ROOT":
        # this client is root
        root_flag = True
        logging.info('Im ROOT of the tree (' + node_address + ')!')
    else:
        logging.info('Im LEAF of the tree (' + node_address + ')! My parent is ' + parent_address)

    # todo get/check correct address
    app.run(host=str(node_address))
