#!/usr/bin/env python

import json
import requests


state_file_name = "/tmp/plugin-state-file.json"
url = "http://localhost:10100/rotate"

watch_list = [
    "failure.server.launch.count", "failure.server.launch.rate_1m",
    "failure.server.launch.rate_5m", "failure.server.launch.rate_15m",
    "failure.authentication.identity.count",
    "failure.authentication.identity.rate_1m",
    "failure.authentication.identity.rate_5m",
    "failure.authentication.identity.rate_15m",
]


accumulators = dict()
deltas = dict()
state = None


def recover_state():
    global state
    try:
        state = json.load(file(state_file_name))
    except:
        state = dict()


def initialize_accumulators():
    global accumulators
    for key in watch_list:
                accumulators[key] = 0


def accumulate_event(event):
    """
    Take the latest reading as our definitive measurement for a given stat.
    Since Logstash is not configured to automatically zero measurements, this is
    guaranteed to be the largest known measurement for this log rotation.
    """
    global accumulators
    for key in watch_list:
        accumulators[key] = event.get(key, 0)


def update_state():
    global state, deltas
    for key in accumulators:
        new_value = accumulators[key]
        old_value = state.get(key, 0)
        delta = max(new_value - old_value, 0)
        state[key] = new_value
        deltas[key] = delta

def accumulate(events):
    for event in events:
        try:
            e = json.loads(event)
            accumulate_event(e)
        except:
            pass

def persist_state():
    file(state_file_name, "w").write(json.dumps(state))


def report():
    print "status ok metrics follow."
    for key in deltas:
        print "metric {0} int64 {1}".format(key, deltas[key])


def main():
    recover_state()
    r = requests.post(url)
    log_file_name = r.text
    initialize_accumulators()
    if r.status_code == 200:
        contents = file(log_file_name).readlines()
        accumulate(contents)
    update_state()
    persist_state()
    report()

