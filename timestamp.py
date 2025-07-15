from micropython import const
import time

TIMESTAMP_FORMAT = const("%d-%02d-%02d %02d:%02d:%02d")

def get_current_timestamp():
    timestamp_elems = time.gmtime()[0:6]
    return TIMESTAMP_FORMAT % timestamp_elems