"""
TSUKUYOMI gRPC Client - Phase 4 Implementation
===============================================

Python client for interacting with the Fate Engine gRPC server.

Provides:
- Proposal submission
- World state queries
- Real-time tick streaming

Author: Tanit (OpenClaw Agent)
Date: 2026-02-04
"""

import asyncio
import logging
import uuid
import time
from typing import AsyncIterator, Optional, Dict, Callable

import grpc
from grpc import aio

# Import generated protobuf classes
from tsukuyomi.proto import common_pb2
from tsukuyomi.proto import core_pb2
from tsukuyomi.proto import fate_engine_service_pb2
from tsukuyomi.proto import fate_engine_service_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gRPC.Client")


def _to_pb_timestamp(t: float) -> common_pb2.Timestamp:
    """Convert float timestamp to protobuf Timestamp."""
    seconds = int(t)
    nanos = int((t - seconds) * 1e9)
    return common_pb2.Timestamp(seconds=seconds, nanos=nanos)


class FateEngineClient:
    """
    gRPC Client for the Fate Engine.
    
    Provides a high-level API for:
    - Submitting proposals (actions)
    - Querying world state
    - Streaming tick updates
    """
    
    def __init__(self, server_address: str = "localhost:50051"):
        self.server_address = server_address
        self.channel: Optional[aio.Channel] = None
        self.stub: Optional[fate_engine_service_pb2_grpc.FateEngineServiceStub] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Connect to the Fate Engine server.
        
        Returns True if connection successful.
        """
        try:
            self.channel = aio.insecure_channel(
                self.server_address,
                options=[
                    ('grpc.max_send_message_length', 50 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                ]
            )
            self.stub = fate_engine_service_pb2_grpc.FateEngineServiceStub(self.channel)
            
            # Test connection with a simple call
            await self.get_world_state()
            
            self._connected = True
            logger.info(f"Connected to Fate Engine at {self.server_address}")
            return True
        
        except grpc.RpcError as e:
            logger.error(f"Failed to connect to {self.server_address}: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.channel:
            await self.channel.close()
            self._connected = False
            logger.info("Disconnected from Fate Engine")
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    # -------------------------------------------------------------------------
    # Proposal Submission
    # -------------------------------------------------------------------------
    
    async def submit_proposal(
        self,
        actor_id: str,
        action: str,
        parameters: Dict[str, str],
        proposal_id: Optional[str] = None
    ) -> tuple[bool, str, str]:
        """
        Submit a proposal to the Fate Engine.
        
        Args:
            actor_id: UUID of the actor making the proposal
            action: Action type (MOVE, INTERACT, IDLE, EMOTE)
            parameters: Action-specific parameters
            proposal_id: Optional custom proposal ID
        
        Returns:
            Tuple of (accepted, message, proposal_id)
        """
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        proposal = core_pb2.Proposal(
            proposal_id=proposal_id or str(uuid.uuid4()),
            actor_id=actor_id,
            action=core_pb2.ActionType.Value(action.upper()),
            parameters=parameters,
            timestamp=_to_pb_timestamp(time.time())
        )
        
        try:
            response = await self.stub.SubmitProposal(proposal)
            return response.accepted, response.message, response.proposal_id
        
        except grpc.RpcError as e:
            logger.error(f"SubmitProposal failed: {e}")
            raise
    
    async def move(self, actor_id: str, destination: str) -> tuple[bool, str, str]:
        """
        Submit a MOVE proposal.
        
        Args:
            actor_id: Actor UUID
            destination: Target location name
        
        Returns:
            Tuple of (accepted, message, proposal_id)
        """
        return await self.submit_proposal(
            actor_id=actor_id,
            action="MOVE",
            parameters={"destination": destination}
        )
    
    async def interact(
        self,
        actor_id: str,
        target_id: str,
        interaction_type: str = "generic"
    ) -> tuple[bool, str, str]:
        """
        Submit an INTERACT proposal.
        
        Args:
            actor_id: Actor UUID
            target_id: Target actor/object UUID
            interaction_type: Type of interaction (e.g., "talk", "trade")
        
        Returns:
            Tuple of (accepted, message, proposal_id)
        """
        return await self.submit_proposal(
            actor_id=actor_id,
            action="INTERACT",
            parameters={"target_id": target_id, "type": interaction_type}
        )
    
    async def emote(self, actor_id: str, emote_type: str = "wave") -> tuple[bool, str, str]:
        """
        Submit an EMOTE proposal.
        
        Args:
            actor_id: Actor UUID
            emote_type: Type of emote (e.g., "wave", "laugh", "nod")
        
        Returns:
            Tuple of (accepted, message, proposal_id)
        """
        return await self.submit_proposal(
            actor_id=actor_id,
            action="EMOTE",
            parameters={"type": emote_type}
        )
    
    async def idle(self, actor_id: str, duration: str = "1") -> tuple[bool, str, str]:
        """
        Submit an IDLE proposal.
        
        Args:
            actor_id: Actor UUID
            duration: Idle duration in ticks
        
        Returns:
            Tuple of (accepted, message, proposal_id)
        """
        return await self.submit_proposal(
            actor_id=actor_id,
            action="IDLE",
            parameters={"duration": duration}
        )
    
    # -------------------------------------------------------------------------
    # World State Query
    # -------------------------------------------------------------------------
    
    async def get_world_state(self) -> core_pb2.WorldState:
        """
        Get the current world state.
        
        Returns:
            WorldState protobuf message
        """
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        try:
            request = fate_engine_service_pb2.GetWorldStateRequest()
            response = await self.stub.GetWorldState(request)
            return response
        
        except grpc.RpcError as e:
            logger.error(f"GetWorldState failed: {e}")
            raise
    
    async def get_actors(self) -> Dict[str, core_pb2.Actor]:
        """Get all actors from the world state."""
        world_state = await self.get_world_state()
        return dict(world_state.actors)
    
    async def get_locations(self) -> Dict[str, core_pb2.Location]:
        """Get all locations from the world state."""
        world_state = await self.get_world_state()
        return dict(world_state.locations)
    
    # -------------------------------------------------------------------------
    # Tick Streaming
    # -------------------------------------------------------------------------
    
    async def stream_tick_updates(
        self,
        callback: Optional[Callable[[core_pb2.TickState], None]] = None
    ) -> AsyncIterator[core_pb2.TickState]:
        """
        Stream real-time tick updates from the server.
        
        Args:
            callback: Optional callback function for each tick
        
        Yields:
            TickState protobuf messages
        """
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        try:
            request = fate_engine_service_pb2.StreamTickUpdatesRequest()
            async for tick_state in self.stub.StreamTickUpdates(request):
                if callback:
                    callback(tick_state)
                yield tick_state
        
        except grpc.RpcError as e:
            logger.error(f"StreamTickUpdates failed: {e}")
            raise
    
    async def watch_ticks(
        self,
        num_ticks: int = 10,
        callback: Optional[Callable[[core_pb2.TickState], None]] = None
    ) -> list[core_pb2.TickState]:
        """
        Watch a specific number of ticks.
        
        Args:
            num_ticks: Number of ticks to watch
            callback: Optional callback for each tick
        
        Returns:
            List of TickState messages
        """
        ticks = []
        count = 0
        
        async for tick_state in self.stream_tick_updates(callback):
            ticks.append(tick_state)
            count += 1
            if count >= num_ticks:
                break
        
        return ticks


# ============================================================================
# Demo / Test Runner
# ============================================================================

async def demo_client():
    """Demonstrate the gRPC client functionality."""
    client = FateEngineClient("localhost:50051")
    
    print("Connecting to Fate Engine...")
    connected = await client.connect()
    
    if not connected:
        print("Failed to connect. Make sure the server is running:")
        print("  python -m tsukuyomi.proto.grpc_server")
        return
    
    try:
        # Get initial world state
        print("\n=== World State ===")
        world_state = await client.get_world_state()
        print(f"Tick: {world_state.tick_number}")
        print(f"Actors: {len(world_state.actors)}")
        for actor_id, actor in world_state.actors.items():
            print(f"  - {actor.name}: pos=({actor.position.x}, {actor.position.y})")
        
        print(f"Locations: {len(world_state.locations)}")
        for loc_name, loc in world_state.locations.items():
            print(f"  - {loc_name}: ({loc.position.x}, {loc.position.y})")
        
        # Get actor ID for testing
        if world_state.actors:
            test_actor_id = list(world_state.actors.keys())[0]
            test_actor_name = world_state.actors[test_actor_id].name
            
            # Submit proposals
            print(f"\n=== Submitting Proposals for {test_actor_name} ===")
            
            # Move to tavern
            accepted, msg, pid = await client.move(test_actor_id, "tavern")
            print(f"MOVE to tavern: {msg} (id: {pid[:8]}...)")
            
            # Emote
            accepted, msg, pid = await client.emote(test_actor_id, "wave")
            print(f"EMOTE wave: {msg} (id: {pid[:8]}...)")
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Check updated state
            print("\n=== Updated World State ===")
            world_state = await client.get_world_state()
            actor = world_state.actors.get(test_actor_id)
            if actor:
                print(f"{actor.name}: pos=({actor.position.x}, {actor.position.y}), loc={actor.current_location}")
        
        # Watch ticks
        print("\n=== Watching 5 Ticks ===")
        
        def on_tick(tick_state):
            print(f"Tick {tick_state.tick_number}: {len(tick_state.pending_proposals)} proposals, {len(tick_state.resolutions)} resolutions")
        
        await client.watch_ticks(num_ticks=5, callback=on_tick)
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(demo_client())
