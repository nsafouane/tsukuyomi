import time
from tsukuyomi.proto import common_pb2

def _to_pb_timestamp(t: float) -> common_pb2.Timestamp:
    seconds = int(t)
    nanos = int((t - seconds) * 1e9)
    return common_pb2.Timestamp(seconds=seconds, nanos=nanos)


def _from_pb_timestamp(pb_timestamp: common_pb2.Timestamp) -> float:
    return pb_timestamp.seconds + pb_timestamp.nanos / 1e9
