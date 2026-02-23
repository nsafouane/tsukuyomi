"""
TSUKUYOMI gRPC Server - Main Entry Point
=========================================

Manages server lifecycle and configuration for the Tsukuyomi gRPC server.
Implements the GrpcServer wrapper class that orchestrates the servicers.

Author: Tanit (OpenClaw Agent)
Date: 2026-02-04
"""

import asyncio
import logging
import os
from typing import Optional
from concurrent import futures

import grpc
from grpc import aio

# Import generated protobuf classes
from tsukuyomi.transport.proto import fate_engine_service_pb2_grpc
from tsukuyomi.transport.proto import guest_api_pb2_grpc

# Import servicers
from tsukuyomi.transport.grpc.fate_servicer import FateEngineServicer
from tsukuyomi.transport.grpc.guest_servicer import GuestServicer

# Import the Fate Engine and Drama Director
from tsukuyomi.environment.core import FateEngine
from tsukuyomi.narrative.core.director import DramaDirector

logger = logging.getLogger("gRPC.Server")


class GrpcServer:
    """
    gRPC Server wrapper for the Fate Engine.

    Manages server lifecycle and configuration.
    """

    def __init__(
        self,
        fate_engine: FateEngine,
        host: str = "0.0.0.0",
        port: int = 50051,
        max_workers: int = 10,
        drama_director: Optional[DramaDirector] = None,
    ):
        self.engine = fate_engine
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.server: Optional[aio.Server] = None
        self.fate_servicer: Optional[FateEngineServicer] = None
        self.guest_servicer: Optional[GuestServicer] = None

        # FIX: Activate Drama Engine
        self.drama_director = drama_director or DramaDirector(fate_engine)

    async def start(self):
        """Start the gRPC server."""
        self.server = aio.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers),
            options=[
                ("grpc.max_send_message_length", 50 * 1024 * 1024),  # 50MB
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
            ],
        )

        self.fate_servicer = FateEngineServicer(self.engine, self.drama_director)
        fate_engine_service_pb2_grpc.add_FateEngineServiceServicer_to_server(
            self.fate_servicer, self.server
        )

        self.guest_servicer = GuestServicer(self.engine)
        guest_api_pb2_grpc.add_GuestServiceServicer_to_server(
            self.guest_servicer, self.server
        )

        listen_addr = f"{self.host}:{self.port}"

        # Security: Enable TLS if certificates exist
        tls_cert = os.getenv("TLS_CERT_PATH", "certs/server.crt")
        tls_key = os.getenv("TLS_KEY_PATH", "certs/server.key")

        if os.path.exists(tls_cert) and os.path.exists(tls_key):
            with open(tls_cert, 'rb') as f:
                cert_chain = f.read()
            with open(tls_key, 'rb') as f:
                private_key = f.read()

            server_creds = grpc.ssl_server_credentials([(private_key, cert_chain)])
            self.server.add_secure_port(listen_addr, server_creds)
            logger.info(f"gRPC Server started WITH TLS on {listen_addr}")
        else:
            logger.warning(f"TLS certificates not found at {tls_cert}, using insecure port")
            self.server.add_insecure_port(listen_addr)

        await self.server.start()
        logger.info(f"gRPC Server started on {listen_addr}")

    async def stop(self, grace: float = 5.0):
        """Stop the gRPC server gracefully."""
        if self.server:
            await self.server.stop(grace)
            logger.info("gRPC Server stopped")

    async def wait_for_termination(self):
        """Wait for server termination."""
        if self.server:
            await self.server.wait_for_termination()


async def run_server(
    tick_rate: int = 20,
    seed: int = 42,
    host: str = "0.0.0.0",
    port: int = 50051,
    db_path: Optional[str] = "tsukuyomi_history.db",
    scenario_config: Optional[str] = None,
):
    """
    Run the Fate Engine with gRPC server.

    This is the main entry point for running a Tsukuyomi simulation server.
    """
    # Initialize Fate Engine
    engine = FateEngine(
        tick_rate=tick_rate,
        seed=seed,
        db_path=db_path,
        scenario_config=scenario_config,
    )

    # Only register demo actors if the world is empty (new DB)
    if not engine.world_state.actors:
        logger.info("New world: No actors registered.")
    else:
        logger.info(f"Resumed world: {len(engine.world_state.actors)} actors found.")

    # Initialize gRPC server
    grpc_server = GrpcServer(engine, host=host, port=port)
    await grpc_server.start()

    # Run engine and server concurrently
    try:
        await asyncio.gather(engine.run(), grpc_server.wait_for_termination())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        engine.stop()
        await grpc_server.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tsukuyomi gRPC Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=50051, help="Server port")
    parser.add_argument("--tick-rate", type=int, default=20, help="Ticks per second")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for determinism"
    )
    parser.add_argument(
        "--db", default="tsukuyomi_history.db", help="Path to SQLite database"
    )

    args = parser.parse_args()

    asyncio.run(
        run_server(
            tick_rate=args.tick_rate,
            seed=args.seed,
            host=args.host,
            port=args.port,
            db_path=args.db,
        )
    )
