"""
Tsukuyomi Proto Package

gRPC service definitions and client/server implementations for
the Fate Engine. Provides:
- FateEngineClient: Python gRPC client for agent connections
- FateEngineService: Server implementation
- Protocol buffer definitions for world state, proposals, and tick updates

Security:
- TLS encryption when certificates are available
- Session token authentication for actor operations
- Secure fallback handling with explicit allow_insecure flag
"""

# Import generated protobuf modules to make them available as tsukuyomi.proto.*
from . import common_pb2
from . import core_pb2
from . import perception_pb2
from . import fate_engine_service_pb2
from . import fate_engine_service_pb2_grpc

__all__ = [
    'common_pb2',
    'core_pb2',
    'perception_pb2',
    'fate_engine_service_pb2',
    'fate_engine_service_pb2_grpc',
]