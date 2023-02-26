import os

print("config log")
from arcticc import log
from arcticc.config import load_loggers_config

print("log.configure")
log.configure(load_loggers_config(), force=True)


def application(env, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"Hello World"]
