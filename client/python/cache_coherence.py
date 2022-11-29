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

BAD_REQUEST_RESPONSE = "400"
OK_RESPONSE = "200"

NOT_FOUND_VALUE = "None"


class JobType(Enum):
    STORE = 0
    REMOVE = 1
    GET = 2


class CacheCoherenceThread(threading.Thread):
    def __init__(self, parent_address, sleep_time, cache_update):
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
        logging.info("Cache Coherence Thread started!")
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
            res_address = f"http://{self.parent_address}:5000/receive?{parameters}"
            logging.debug("Sending HTTP GET to %s " % res_address)
            x = requests.put(res_address).text
            logging.debug("Root node responded: %s" % x)
            return x
        except Exception as e:
            logging.error(f"Retrieving of key '{key}' from the root node {self.parent_address} failed due to {e}")
        return

    def set_root_value(self, package: Any):
        key, value = package

        try:
            parameters = f"{URL_KEY_PARAMETER}={key}&{URL_VALUE_PARAMETER}={value}"
            res_address = f"http://{self.parent_address}:5000/store?{parameters}"
            logging.debug("Sending HTTP PUT to %s " % res_address)
            x = requests.put(res_address).text
            logging.debug("Root node responded: %s" % x)
            self.handle_root_response(x)
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

    def remove_root_value(self, key):
        try:
            parameters = f"{URL_KEY_PARAMETER}={key}"
            res_address = f"http://{self.parent_address}:5000/store?{parameters}"
            logging.debug("Sending HTTP DELETE to %s " % res_address)
            x = requests.delete(res_address).text
            logging.debug("Root node responded: %s" % x)
            self.handle_root_response(x)
        except Exception as e:
            logging.error(
                f"Storing of key '{key}' to the root node {self.parent_address} failed due to {e}")

        return
