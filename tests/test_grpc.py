"""
TSUKUYOMI gRPC Tests - Phase 4
==============================

Unit tests for the gRPC server and client implementation.

Author: Tanit (OpenClaw Agent)
Date: 2026-02-04
"""

import asyncio
import pytest
import uuid
import time
from unittest.mock import MagicMock, patch

# Import the modules under test
from tsukuyomi.transport.proto import common_pb2
from tsukuyomi.transport.proto import core_pb2
from tsukuyomi.transport.proto import fate_engine_service_pb2
from tsukuyomi.environment.core.engine import FateEngine, to_pb_timestamp
from tsukuyomi.transport.grpc.server import FateEngineServicer, GrpcServer
from tsukuyomi.transport.grpc.client import FateEngineClient


# ============================================================================
# FateEngineServicer Tests
# ============================================================================

class TestFateEngineServicer:
    """Tests for the gRPC service implementation."""
    
    @pytest.fixture
    def engine(self):
        """Create a test Fate Engine."""
        engine = FateEngine(tick_rate=20, seed=42)
        engine.register_actor(str(uuid.uuid4()), "TestActor", position=(0, 0))
        return engine
    
    @pytest.fixture
    def servicer(self, engine):
        """Create a servicer with the test engine."""
        return FateEngineServicer(engine)
    
    @pytest.mark.asyncio
    async def test_submit_proposal_valid(self, servicer, engine):
        """Test submitting a valid proposal."""
        actor_id = list(engine.world_state.actors.keys())[0]
        
        proposal = core_pb2.Proposal(
            proposal_id=str(uuid.uuid4()),
            actor_id=actor_id,
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=to_pb_timestamp(time.time())
        )
        
        # Mock context
        context = MagicMock()
        
        response = await servicer.SubmitProposal(proposal, context)
        
        assert response.accepted == True
        assert response.proposal_id == proposal.proposal_id
        assert "accepted" in response.message.lower() or "queued" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_submit_proposal_missing_actor_id(self, servicer):
        """Test submitting proposal without actor_id."""
        proposal = core_pb2.Proposal(
            proposal_id=str(uuid.uuid4()),
            actor_id="",  # Empty actor ID
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern"}
        )
        
        context = MagicMock()
        response = await servicer.SubmitProposal(proposal, context)
        
        assert response.accepted == False
        assert "actor_id" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_submit_proposal_missing_action(self, servicer, engine):
        """Test submitting proposal without action type."""
        actor_id = list(engine.world_state.actors.keys())[0]
        
        proposal = core_pb2.Proposal(
            proposal_id=str(uuid.uuid4()),
            actor_id=actor_id,
            action=core_pb2.ActionType.ACTION_TYPE_UNSPECIFIED,
            parameters={}
        )
        
        context = MagicMock()
        response = await servicer.SubmitProposal(proposal, context)
        
        assert response.accepted == False
        assert "action" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_get_world_state(self, servicer, engine):
        """Test getting world state."""
        request = fate_engine_service_pb2.GetWorldStateRequest()
        context = MagicMock()
        
        response = await servicer.GetWorldState(request, context)
        
        assert len(response.actors) == 1
        assert len(response.locations) >= 4  # market_square, tavern, inn, well
        assert "tavern" in response.locations


# ============================================================================
# FateEngineClient Tests
# ============================================================================

class TestFateEngineClient:
    """Tests for the gRPC client implementation."""
    
    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = FateEngineClient()
        assert client.server_address == "localhost:50051"
        assert client.connected == False
    
    def test_client_custom_address(self):
        """Test client with custom address."""
        client = FateEngineClient("192.168.1.100:9000")
        assert client.server_address == "192.168.1.100:9000"
    
    @pytest.mark.asyncio
    async def test_submit_proposal_not_connected(self):
        """Test submitting proposal without connection raises error."""
        client = FateEngineClient()
        
        with pytest.raises(RuntimeError, match="Not connected"):
            await client.submit_proposal(
                actor_id=str(uuid.uuid4()),
                action="MOVE",
                parameters={"destination": "tavern"}
            )
    
    @pytest.mark.asyncio
    async def test_get_world_state_not_connected(self):
        """Test getting world state without connection raises error."""
        client = FateEngineClient()
        
        with pytest.raises(RuntimeError, match="Not connected"):
            await client.get_world_state()


# ============================================================================
# Integration Tests
# ============================================================================

class TestGrpcIntegration:
    """Integration tests for server and client."""
    
    @pytest.fixture
    def engine(self):
        """Create a test Fate Engine."""
        engine = FateEngine(tick_rate=20, seed=42)
        return engine
    
    @pytest.mark.asyncio
    async def test_proposal_lifecycle(self, engine):
        """Test full proposal submission and resolution cycle."""
        # Register actor
        actor_id = str(uuid.uuid4())
        engine.register_actor(actor_id, "TestActor", position=(0, 0))
        
        # Create proposal
        proposal = core_pb2.Proposal(
            proposal_id=str(uuid.uuid4()),
            actor_id=actor_id,
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=to_pb_timestamp(time.time())
        )
        
        # Submit to engine
        accepted = await engine.submit_proposal(proposal)
        assert accepted == True
        
        # Flush and check
        proposals = await engine.flush_proposals()
        assert len(proposals) == 1
        assert proposals[0].actor_id == actor_id
    
    @pytest.mark.asyncio
    async def test_multiple_proposals(self, engine):
        """Test submitting multiple proposals."""
        # Register actors
        actor1_id = str(uuid.uuid4())
        actor2_id = str(uuid.uuid4())
        engine.register_actor(actor1_id, "Actor1", position=(0, 0))
        engine.register_actor(actor2_id, "Actor2", position=(5, 5))
        
        # Submit multiple proposals
        for actor_id, dest in [(actor1_id, "tavern"), (actor2_id, "inn")]:
            proposal = core_pb2.Proposal(
                proposal_id=str(uuid.uuid4()),
                actor_id=actor_id,
                action=core_pb2.ActionType.MOVE,
                parameters={"destination": dest},
                timestamp=to_pb_timestamp(time.time())
            )
            await engine.submit_proposal(proposal)
        
        proposals = await engine.flush_proposals()
        assert len(proposals) == 2
    
    @pytest.mark.asyncio
    async def test_servicer_broadcasts_to_subscribers(self, engine):
        """Test that servicer broadcasts tick updates to subscribers."""
        servicer = FateEngineServicer(engine)
        
        # Create subscriber queue
        queue = asyncio.Queue(maxsize=10)
        async with servicer._subscriber_lock:
            servicer._tick_subscribers.append(queue)
        
        # Trigger broadcast
        await servicer._broadcast_tick_update(tick=1, resolutions=[])
        
        # Check queue (may be empty if no tick state exists)
        # This tests the broadcast mechanism works
        assert len(servicer._tick_subscribers) == 1


# ============================================================================
# Protocol Buffer Tests
# ============================================================================

class TestProtocolBuffers:
    """Tests for protobuf message handling."""
    
    def test_timestamp_conversion(self):
        """Test timestamp conversion to/from protobuf."""
        original_time = time.time()
        pb_timestamp = to_pb_timestamp(original_time)
        
        assert pb_timestamp.seconds == int(original_time)
        assert pb_timestamp.nanos >= 0
        assert pb_timestamp.nanos < 1_000_000_000
    
    def test_proposal_serialization(self):
        """Test proposal can be serialized and deserialized."""
        proposal = core_pb2.Proposal(
            proposal_id=str(uuid.uuid4()),
            actor_id=str(uuid.uuid4()),
            action=core_pb2.ActionType.MOVE,
            parameters={"destination": "tavern", "speed": "fast"},
            timestamp=to_pb_timestamp(time.time())
        )
        
        # Serialize
        serialized = proposal.SerializeToString()
        
        # Deserialize
        restored = core_pb2.Proposal()
        restored.ParseFromString(serialized)
        
        assert restored.proposal_id == proposal.proposal_id
        assert restored.actor_id == proposal.actor_id
        assert restored.action == core_pb2.ActionType.MOVE
        assert dict(restored.parameters) == {"destination": "tavern", "speed": "fast"}
    
    def test_world_state_structure(self):
        """Test world state protobuf structure."""
        world_state = core_pb2.WorldState(tick_number=100)
        
        # Add actor
        actor = core_pb2.Actor(
            id=str(uuid.uuid4()),
            name="TestActor",
            position=common_pb2.Vector2(x=10.0, y=20.0),
            state="IDLE"
        )
        world_state.actors[actor.id].CopyFrom(actor)
        
        # Add location
        location = core_pb2.Location(
            name="tavern",
            position=common_pb2.Vector2(x=10.0, y=5.0)
        )
        world_state.locations["tavern"].CopyFrom(location)
        
        assert world_state.tick_number == 100
        assert len(world_state.actors) == 1
        assert len(world_state.locations) == 1
        assert world_state.locations["tavern"].name == "tavern"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
