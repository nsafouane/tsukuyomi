"""
TSUKUYOMI gRPC Server - Phase 4 Implementation
===============================================

Implements the FateEngineService gRPC server exposing:
- SubmitProposal: Submit action proposals to the Fate Engine
- GetWorldState: Query current world state
- StreamTickUpdates: Real-time tick state streaming

Author: Tanit (OpenClaw Agent)
Date: 2026-02-04
"""

import asyncio
import logging
import uuid
from typing import AsyncIterator, Optional
from concurrent import futures

import grpc
from grpc import aio

# Import generated protobuf classes
from tsukuyomi.proto import common_pb2
from tsukuyomi.proto import core_pb2
from tsukuyomi.proto import fate_engine_service_pb2
from tsukuyomi.proto import fate_engine_service_pb2_grpc

# Import the Fate Engine
from tsukuyomi.proto.fate_engine import FateEngine, _to_pb_timestamp

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gRPC.Server")


class FateEngineServicer(fate_engine_service_pb2_grpc.FateEngineServiceServicer):
    """
    gRPC Service implementation for the Fate Engine.
    
    Provides external access to:
    - Submit proposals from remote agents
    - Query world state
    - Stream real-time tick updates
    """
    
    def __init__(self, fate_engine: FateEngine):
        self.engine = fate_engine
        self._tick_subscribers: list[asyncio.Queue] = []
        self._subscriber_lock = asyncio.Lock()
        
        # Register post-resolution hook for broadcasting tick updates
        self.engine.post_resolution_hooks.append(self._broadcast_tick_update)
        
        logger.info("FateEngineServicer initialized")
    
    async def _broadcast_tick_update(self, tick: int, resolutions: list):
        """Broadcast tick state to all subscribers."""
        tick_state = self.engine.get_tick_state(tick)
        if not tick_state:
            return
        
        async with self._subscriber_lock:
            dead_queues = []
            for queue in self._tick_subscribers:
                try:
                    queue.put_nowait(tick_state)
                except asyncio.QueueFull:
                    # Queue is full, subscriber is too slow
                    logger.warning("Subscriber queue full, dropping tick update")
                except Exception as e:
                    logger.error(f"Error broadcasting to subscriber: {e}")
                    dead_queues.append(queue)
            
            # Clean up dead queues
            for q in dead_queues:
                self._tick_subscribers.remove(q)
    
    async def SubmitProposal(
        self,
        request: core_pb2.Proposal,
        context: grpc.aio.ServicerContext
    ) -> fate_engine_service_pb2.SubmitProposalResponse:
        logger.debug(f"Received proposal: {request.proposal_id} from {request.actor_id}")
        """
        Handle SubmitProposal RPC.
        
        Validates and queues the proposal for the next tick window.
        """
        try:
            # Validate proposal
            if not request.actor_id:
                return fate_engine_service_pb2.SubmitProposalResponse(
                    accepted=False,
                    message="actor_id is required",
                    proposal_id=""
                )
            
            if request.action == core_pb2.ActionType.ACTION_TYPE_UNSPECIFIED:
                return fate_engine_service_pb2.SubmitProposalResponse(
                    accepted=False,
                    message="action type is required",
                    proposal_id=""
                )
            
            # Generate proposal ID if not provided
            proposal_id = request.proposal_id or str(uuid.uuid4())
            
            # Create a new proposal with the generated ID
            proposal = core_pb2.Proposal()
            proposal.CopyFrom(request)
            proposal.proposal_id = proposal_id
            
            # Submit to fate engine
            accepted = await self.engine.submit_proposal(proposal)
            
            logger.info(f"Proposal {proposal_id} from {request.actor_id}: {'accepted' if accepted else 'queued'}")
            
            return fate_engine_service_pb2.SubmitProposalResponse(
                accepted=accepted,
                message="Proposal accepted" if accepted else "Proposal queued for next tick",
                proposal_id=proposal_id
            )
        
        except Exception as e:
            logger.error(f"Error submitting proposal: {e}", exc_info=True)
            return fate_engine_service_pb2.SubmitProposalResponse(
                accepted=False,
                message=f"Internal error: {str(e)}",
                proposal_id=""
            )
    
    async def GetWorldState(
        self,
        request: fate_engine_service_pb2.GetWorldStateRequest,
        context: grpc.aio.ServicerContext
    ) -> core_pb2.WorldState:
        """
        Handle GetWorldState RPC.
        
        Returns the current snapshot of the world state.
        """
        try:
            world_state = self.engine._get_world_snapshot()
            
            # Add current tick number and timestamp
            world_state.tick_number = self.engine.current_tick
            world_state.timestamp.CopyFrom(_to_pb_timestamp(asyncio.get_event_loop().time()))
            
            logger.debug(f"GetWorldState: tick={self.engine.current_tick}, actors={len(world_state.actors)}")
            
            return world_state
        
        except Exception as e:
            logger.error(f"Error getting world state: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return core_pb2.WorldState()
    
    async def StreamTickUpdates(
        self,
        request: fate_engine_service_pb2.StreamTickUpdatesRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[core_pb2.TickState]:
        """
        Handle StreamTickUpdates RPC.
        
        Streams real-time tick state updates to the client.
        """
        # Create a queue for this subscriber
        queue: asyncio.Queue[core_pb2.TickState] = asyncio.Queue(maxsize=100)
        
        async with self._subscriber_lock:
            self._tick_subscribers.append(queue)
        
        logger.info(f"New tick stream subscriber connected (total: {len(self._tick_subscribers)})")
        
        try:
            while True:
                # Check if client disconnected
                if context.cancelled():
                    break
                
                try:
                    # Wait for next tick update with timeout
                    tick_state = await asyncio.wait_for(queue.get(), timeout=5.0)
                    yield tick_state
                except asyncio.TimeoutError:
                    # Send heartbeat (empty tick state) to keep connection alive
                    continue
        
        except asyncio.CancelledError:
            logger.info("Tick stream subscriber cancelled")
        
        finally:
            async with self._subscriber_lock:
                if queue in self._tick_subscribers:
                    self._tick_subscribers.remove(queue)
            logger.info(f"Tick stream subscriber disconnected (remaining: {len(self._tick_subscribers)})")

    async def RegisterActor(
        self,
        request: fate_engine_service_pb2.RegisterActorRequest,
        context: grpc.aio.ServicerContext
    ) -> fate_engine_service_pb2.RegisterActorResponse:
        """Handle RegisterActor RPC."""
        try:
            self.engine.register_actor(
                request.actor_id,
                request.name,
                (request.x, request.y)
            )
            return fate_engine_service_pb2.RegisterActorResponse(
                success=True,
                message=f"Actor {request.name} registered"
            )
        except Exception as e:
            logger.error(f"Error registering actor: {e}")
            return fate_engine_service_pb2.RegisterActorResponse(
                success=False,
                message=str(e)
            )


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
        max_workers: int = 10
    ):
        self.engine = fate_engine
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.server: Optional[aio.Server] = None
        self.servicer: Optional[FateEngineServicer] = None
    
    async def start(self):
        """Start the gRPC server."""
        self.server = aio.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers),
            options=[
                ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
            ]
        )
        
        self.servicer = FateEngineServicer(self.engine)
        fate_engine_service_pb2_grpc.add_FateEngineServiceServicer_to_server(
            self.servicer, self.server
        )
        
        listen_addr = f"{self.host}:{self.port}"
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
    db_path: Optional[str] = "tsukuyomi_history.db"
):
    """
    Run the Fate Engine with gRPC server.
    
    This is the main entry point for running a Tsukuyomi simulation server.
    """
    # Initialize Fate Engine
    engine = FateEngine(tick_rate=tick_rate, seed=seed, db_path=db_path)
    
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
        await asyncio.gather(
            engine.run(),
            grpc_server.wait_for_termination()
        )
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
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism")
    parser.add_argument("--db", default="tsukuyomi_history.db", help="Path to SQLite database")
    
    args = parser.parse_args()
    
    asyncio.run(run_server(
        tick_rate=args.tick_rate,
        seed=args.seed,
        host=args.host,
        port=args.port,
        db_path=args.db
    ))
