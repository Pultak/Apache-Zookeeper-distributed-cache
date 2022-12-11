import threading
import logging
import time
from typing import Any

import requests

from threading import Lock

from enum import Enum

# constants //////////////////////////////
URL_KEY_PARAMETER = "key"
URL_VALUE_PARAMETER = "value"

BAD_REQUEST_RESPONSE = 400
METHOD_NOT_ALLOWED_RESPONSE = 405
TEAPOT_RESPONSE = 418
OK_RESPONSE = 200

NOT_FOUND_VALUE = "None"


class JobType(Enum):
    STORE = 0
    REMOVE = 1
    GET = 2


class RootSignalerThread(threading.Thread):
    def __init__(self, sleep_time, cache_update, parent_address = None):
        threading.Thread.__init__(self)
        self.running = True

        self.parent_address = parent_address
        self.queue_lock = Lock()
        self.job_queue = []
        self.running = True
        self.sleep_time = sleep_time
        self.cache_update = cache_update

        self.job_switch = {
            JobType.STORE: self.set_root_value,
            JobType.REMOVE: self.remove_root_value
        }

    # helper function to execute the threads
    def run(self):
        logging.info("Root Coherence Thread started!")
        while self.running:

            job = None
            with self.queue_lock:
                if len(self.job_queue) > 0:
                    job = self.job_queue[0]
                    self.job_queue.pop(0)
            if job is not None:
                job_type, job_value = job
                logging.debug(f"Calling job: {job_type}|{job_value}")
                self.job_switch[job_type](job_value)
            else:
                time.sleep(self.sleep_time)

    def add_job(self, job_type, job):
        self.job_queue.append((job_type, job))

    def get_root_value(self, key: Any):
        try:
            parameters = f"{URL_KEY_PARAMETER}={key}"
            res_address = f"http://{self.parent_address}:5000/receive/?{parameters}"
            logging.debug("Sending HTTP GET to %s " % res_address)
            x = requests.get(res_address)
            logging.debug("Root node responded: %s" % x.text)
            return x.text.strip().replace("\"", ""), x.status_code
        except Exception as e:
            logging.error(f"Retrieving of key '{key}' from the root node {self.parent_address} failed due to {e}")
        return

    def set_root_value(self, package: Any):
        key, value = package

        try:
            parameters = f"{URL_KEY_PARAMETER}={key}&{URL_VALUE_PARAMETER}={value}"
            res_address = f"http://{self.parent_address}:5000/store/?{parameters}"
            logging.debug("Sending HTTP PUT to %s " % res_address)
            x = requests.put(res_address).text
            logging.debug("Root node responded: %s" % x)
            self.handle_root_response(int(x))
        except Exception as e:
            logging.error(f"Storing of key '{key}' with value '{value}' to the root node {self.parent_address} failed due to {e}")

    @staticmethod
    def handle_root_response(response):
        if response == OK_RESPONSE:
            return
        elif response == BAD_REQUEST_RESPONSE:
            logging.error(
                f"Internal client error! Root responded with {BAD_REQUEST_RESPONSE} but sent values should be valid!")
            return
        else:
            logging.error("Unknown response from root (%s)!" % response)


    @staticmethod
    def ask_tree_root_for_parent(root_address, node_address):
        try:
            parameters = f"nodeName={node_address}"
            res_address = f"http://{root_address}:5000/getParent/?{parameters}"
            logging.debug("Sending HTTP GET to %s " % res_address)
            x = requests.get(res_address).text
            logging.debug("Root node responded: %s" % x)

            if x == METHOD_NOT_ALLOWED_RESPONSE:
                logging.debug("Root does not consider himself as root and cant assign us parent")
            elif x == TEAPOT_RESPONSE:
                logging.debug("HE is a TEAPOT?")
            else:
                return x
            return None
        except Exception as e:
            logging.error(
                f"Getting parent address from tree root '{root_address}' failed due to {e}")


    def remove_root_value(self, key):
        try:
            parameters = f"{URL_KEY_PARAMETER}={key}"
            res_address = f"http://{self.parent_address}:5000/remove/?{parameters}"
            logging.debug("Sending HTTP DELETE to %s " % res_address)
            x = requests.delete(res_address).text
            logging.debug("Root node responded: %s" % x)
            self.handle_root_response(int(x))
        except Exception as e:
            logging.error(
                f"Storing of key '{key}' to the root node {self.parent_address} failed due to {e}")

        return
