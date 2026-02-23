"""
Tsukuyomi Protocol Buffer Definitions
======================================

Auto-generated protobuf Python classes for gRPC communication.

This module contains all the protobuf message definitions and service stubs
used by the Tsukuyomi transport layer.

Generated from .proto files in the proto directory.
"""

# Import protobuf message definitions
from tsukuyomi.transport.proto import common_pb2
from tsukuyomi.transport.proto import core_pb2
from tsukuyomi.transport.proto import perception_pb2
from tsukuyomi.transport.proto import fate_engine_service_pb2
from tsukuyomi.transport.proto import guest_api_pb2

# Import gRPC stubs (lazy import to avoid circular dependency)
try:
    from tsukuyomi.transport.proto import common_pb2_grpc
    from tsukuyomi.transport.proto import core_pb2_grpc
    from tsukuyomi.transport.proto import perception_pb2_grpc
    from tsukuyomi.transport.proto import fate_engine_service_pb2_grpc
    from tsukuyomi.transport.proto import guest_api_pb2_grpc
    _grpc_available = True
except ImportError:
    _grpc_available = False

__all__ = [
    "common_pb2",
    "core_pb2",
    "perception_pb2",
    "fate_engine_service_pb2",
    "guest_api_pb2",
]
