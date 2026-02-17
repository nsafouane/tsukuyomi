"""
Test SaveWorld/LoadWorld gRPC Methods for Phase 3.

Tests:
- SaveWorld method functionality
- LoadWorld method functionality
- Data integrity after save/load
- Performance benchmarks
- Error handling

NOTE: These tests require proto definitions (SaveWorldRequest, LoadWorldRequest, etc.)
that are not currently generated. They are skipped until the proto files are updated.
"""

import pytest

# Skip all tests - proto definitions not implemented yet
pytestmark = pytest.mark.skip(reason="Proto definitions (SaveWorldRequest, LoadWorldRequest) not implemented")

import asyncio
import grpc
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List
import time
import tempfile
import os


# Mock proto imports (in real implementation, these would be actual proto imports)
from tsukuyomi.proto import core_pb2, fate_engine_service_pb2, fate_engine_service_pb2_grpc


class MockFateEngineService(fate_engine_service_pb2_grpc.FateEngineServiceServicer):
    """Mock Fate Engine Service for testing SaveWorld/LoadWorld."""

    def __init__(self):
        self.world_states = {}
        self.save_count = 0
        self.load_count = 0

    async def SaveWorld(self, request, context):
        """Save the current world state."""
        self.save_count += 1
        save_id = request.save_id or f"save_{self.save_count}"

        # Serialize world state
        world_state_data = core_pb2.WorldState()
        world_state_data.CopyFrom(request.world_state)

        self.world_states[save_id] = {
            'world_state': world_state_data,
            'timestamp': request.timestamp,
            'metadata': request.metadata,
        }

        response = fate_engine_service_pb2.SaveWorldResponse()
        response.success = True
        response.save_id = save_id
        response.message = f"World saved successfully as {save_id}"
        response.size_bytes = len(world_state_data.SerializeToString())

        return response

    async def LoadWorld(self, request, context):
        """Load a previously saved world state."""
        self.load_count += 1

        save_id = request.save_id
        if save_id not in self.world_states:
            response = fate_engine_service_pb2.LoadWorldResponse()
            response.success = False
            response.message = f"Save not found: {save_id}"
            return response

        saved_data = self.world_states[save_id]

        response = fate_engine_service_pb2.LoadWorldResponse()
        response.success = True
        response.world_state.CopyFrom(saved_data['world_state'])
        response.message = f"World loaded successfully from {save_id}"
        response.metadata.update(saved_data['metadata'])

        return response

    async def ListSaves(self, request, context):
        """List all saved world states."""
        response = fate_engine_service_pb2.ListSavesResponse()

        for save_id, data in self.world_states.items():
            save_info = fate_engine_service_pb2.SaveInfo()
            save_info.save_id = save_id
            save_info.timestamp.CopyFrom(data['timestamp'])
            save_info.metadata.update(data['metadata'])
            response.saves.append(save_info)

        response.success = True
        return response

    async def DeleteSave(self, request, context):
        """Delete a saved world state."""
        save_id = request.save_id

        if save_id not in self.world_states:
            response = fate_engine_service_pb2.DeleteSaveResponse()
            response.success = False
            response.message = f"Save not found: {save_id}"
            return response

        del self.world_states[save_id]

        response = fate_engine_service_pb2.DeleteSaveResponse()
        response.success = True
        response.message = f"Save deleted: {save_id}"
        return response


@pytest.fixture
def mock_service():
    """Create a mock Fate Engine Service."""
    return MockFateEngineService()


@pytest.fixture
async def grpc_server(mock_service):
    """Create a gRPC server for testing."""
    server = grpc.aio.server()
    fate_engine_service_pb2_grpc.add_FateEngineServiceServicer_to_server(
        mock_service, server
    )
    server.add_insecure_port('[::]:50051')

    await server.start()
    yield server
    await server.stop(grace=1)


@pytest.fixture
async def grpc_client():
    """Create a gRPC client for testing."""
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = fate_engine_service_pb2_grpc.FateEngineServiceStub(channel)
        yield stub


@pytest.mark.asyncio
async def test_save_world_basic(grpc_client):
    """Test basic SaveWorld functionality."""
    # Create a world state to save
    world_state = core_pb2.WorldState()
    world_state.tick_number = 100
    world_state.timestamp.GetCurrentTime()

    # Add an actor
    actor = core_pb2.Actor()
    actor.id = "actor_1"
    actor.name = "Alice"
    actor.position.x = 10.0
    actor.position.y = 20.0
    actor.state = "IDLE"
    world_state.actors["actor_1"].CopyFrom(actor)

    # Create save request
    request = fate_engine_service_pb2.SaveWorldRequest()
    request.save_id = "test_save_1"
    request.world_state.CopyFrom(world_state)
    request.timestamp.GetCurrentTime()
    request.metadata["author"] = "test_user"
    request.metadata["description"] = "Test save"

    # Send request
    response = await grpc_client.SaveWorld(request)

    # Verify response
    assert response.success is True
    assert response.save_id == "test_save_1"
    assert "saved successfully" in response.message.lower()
    assert response.size_bytes > 0

    print(f"✓ SaveWorld succeeded: {response.save_id}")
    print(f"  Size: {response.size_bytes} bytes")


@pytest.mark.asyncio
async def test_load_world_basic(grpc_client):
    """Test basic LoadWorld functionality."""
    # First, save a world
    world_state = core_pb2.WorldState()
    world_state.tick_number = 200
    world_state.timestamp.GetCurrentTime()

    actor = core_pb2.Actor()
    actor.id = "actor_2"
    actor.name = "Bob"
    actor.position.x = 30.0
    actor.position.y = 40.0
    world_state.actors["actor_2"].CopyFrom(actor)

    save_request = fate_engine_service_pb2.SaveWorldRequest()
    save_request.save_id = "test_save_2"
    save_request.world_state.CopyFrom(world_state)
    save_request.timestamp.GetCurrentTime()
    save_request.metadata["version"] = "1.0"

    await grpc_client.SaveWorld(save_request)

    # Now load the world
    load_request = fate_engine_service_pb2.LoadWorldRequest()
    load_request.save_id = "test_save_2"

    response = await grpc_client.LoadWorld(load_request)

    # Verify response
    assert response.success is True
    assert response.world_state.tick_number == 200
    assert "actor_2" in response.world_state.actors
    assert response.world_state.actors["actor_2"].name == "Bob"
    assert response.world_state.actors["actor_2"].position.x == 30.0
    assert response.world_state.actors["actor_2"].position.y == 40.0
    assert response.metadata["version"] == "1.0"

    print(f"✓ LoadWorld succeeded: tick={response.world_state.tick_number}")
    print(f"  Actors: {len(response.world_state.actors)}")


@pytest.mark.asyncio
async def test_save_world_with_multiple_actors(grpc_client):
    """Test SaveWorld with multiple actors."""
    world_state = core_pb2.WorldState()
    world_state.tick_number = 300

    # Add multiple actors
    actors_data = [
        ("alice", "Alice", (5.0, 10.0), "IDLE"),
        ("bob", "Bob", (15.0, 20.0), "WALKING"),
        ("charlie", "Charlie", (25.0, 30.0), "INTERACTING"),
    ]

    for actor_id, name, pos, state in actors_data:
        actor = core_pb2.Actor()
        actor.id = actor_id
        actor.name = name
        actor.position.x = pos[0]
        actor.position.y = pos[1]
        actor.state = state
        world_state.actors[actor_id].CopyFrom(actor)

    request = fate_engine_service_pb2.SaveWorldRequest()
    request.save_id = "test_multi_actors"
    request.world_state.CopyFrom(world_state)
    request.timestamp.GetCurrentTime()

    response = await grpc_client.SaveWorld(request)

    assert response.success is True
    assert len(world_state.actors) == 3
    assert response.size_bytes > 0

    print(f"✓ Saved world with {len(world_state.actors)} actors")


@pytest.mark.asyncio
async def test_load_world_data_integrity(grpc_client):
    """Test that LoadWorld preserves data integrity."""
    # Create a complex world state
    world_state = core_pb2.WorldState()
    world_state.tick_number = 400

    # Add actor with inventory
    actor = core_pb2.Actor()
    actor.id = "player_1"
    actor.name = "Player"
    actor.position.x = 0.0
    actor.position.y = 0.0
    actor.state = "IDLE"
    actor.inventory.extend(["sword", "potion", "key"])
    world_state.actors["player_1"].CopyFrom(actor)

    # Add environment objects
    obj = core_pb2.EnvironmentObject()
    obj.id = "obj_1"
    obj.type = "chest"
    obj.position.x = 10.0
    obj.position.y = 10.0
    obj.interactive = True
    obj.properties["locked"] = "true"
    world_state.objects["obj_1"].CopyFrom(obj)

    # Add locations
    loc = core_pb2.Location()
    loc.name = "tavern"
    loc.position.x = 50.0
    loc.position.y = 50.0
    world_state.locations["tavern"].CopyFrom(loc)

    # Save
    save_request = fate_engine_service_pb2.SaveWorldRequest()
    save_request.save_id = "test_integrity"
    save_request.world_state.CopyFrom(world_state)
    save_request.timestamp.GetCurrentTime()

    await grpc_client.SaveWorld(save_request)

    # Load
    load_request = fate_engine_service_pb2.LoadWorldRequest()
    load_request.save_id = "test_integrity"

    response = await grpc_client.LoadWorld(load_request)

    # Verify all data is preserved
    assert response.success is True

    # Actor data
    loaded_actor = response.world_state.actors["player_1"]
    assert loaded_actor.name == "Player"
    assert len(loaded_actor.inventory) == 3
    assert "sword" in loaded_actor.inventory
    assert "potion" in loaded_actor.inventory
    assert "key" in loaded_actor.inventory

    # Object data
    loaded_obj = response.world_state.objects["obj_1"]
    assert loaded_obj.type == "chest"
    assert loaded_obj.properties["locked"] == "true"

    # Location data
    loaded_loc = response.world_state.locations["tavern"]
    assert loaded_loc.position.x == 50.0
    assert loaded_loc.position.y == 50.0

    print("✓ Data integrity verified after save/load")


@pytest.mark.asyncio
async def test_load_nonexistent_save(grpc_client):
    """Test loading a non-existent save."""
    request = fate_engine_service_pb2.LoadWorldRequest()
    request.save_id = "nonexistent_save"

    response = await grpc_client.LoadWorld(request)

    assert response.success is False
    assert "not found" in response.message.lower()

    print("✓ Non-existent save handled correctly")


@pytest.mark.asyncio
async def test_list_saves(grpc_client):
    """Test listing all saved worlds."""
    # Create multiple saves
    for i in range(3):
        world_state = core_pb2.WorldState()
        world_state.tick_number = i * 100

        request = fate_engine_service_pb2.SaveWorldRequest()
        request.save_id = f"save_{i}"
        request.world_state.CopyFrom(world_state)
        request.timestamp.GetCurrentTime()
        request.metadata["index"] = str(i)

        await grpc_client.SaveWorld(request)

    # List saves
    request = fate_engine_service_pb2.ListSavesRequest()
    response = await grpc_client.ListSaves(request)

    assert response.success is True
    assert len(response.saves) >= 3

    # Verify save IDs
    save_ids = {save.save_id for save in response.saves}
    assert "save_0" in save_ids
    assert "save_1" in save_ids
    assert "save_2" in save_ids

    print(f"✓ Listed {len(response.saves)} saves")


@pytest.mark.asyncio
async def test_delete_save(grpc_client):
    """Test deleting a save."""
    # Create a save
    world_state = core_pb2.WorldState()
    world_state.tick_number = 500

    save_request = fate_engine_service_pb2.SaveWorldRequest()
    save_request.save_id = "save_to_delete"
    save_request.world_state.CopyFrom(world_state)
    save_request.timestamp.GetCurrentTime()

    await grpc_client.SaveWorld(save_request)

    # Verify it exists
    load_request = fate_engine_service_pb2.LoadWorldRequest()
    load_request.save_id = "save_to_delete"
    load_response = await grpc_client.LoadWorld(load_request)
    assert load_response.success is True

    # Delete it
    delete_request = fate_engine_service_pb2.DeleteSaveRequest()
    delete_request.save_id = "save_to_delete"
    delete_response = await grpc_client.DeleteSave(delete_request)
    assert delete_response.success is True

    # Verify it's gone
    load_response2 = await grpc_client.LoadWorld(load_request)
    assert load_response2.success is False

    print("✓ Save deleted successfully")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_save_performance(grpc_client):
    """Benchmark SaveWorld performance."""
    world_state = core_pb2.WorldState()
    world_state.tick_number = 1000

    # Add many actors
    for i in range(100):
        actor = core_pb2.Actor()
        actor.id = f"actor_{i}"
        actor.name = f"Actor{i}"
        actor.position.x = float(i * 10)
        actor.position.y = float(i * 10)
        world_state.actors[actor.id].CopyFrom(actor)

    request = fate_engine_service_pb2.SaveWorldRequest()
    request.save_id = "perf_test"
    request.world_state.CopyFrom(world_state)
    request.timestamp.GetCurrentTime()

    start_time = time.time()
    response = await grpc_client.SaveWorld(request)
    elapsed = time.time() - start_time

    assert response.success is True
    assert elapsed < 1.0, f"Save too slow: {elapsed:.3f}s"

    print(f"✓ Save performance: {elapsed:.3f}s for {len(world_state.actors)} actors")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_load_performance(grpc_client):
    """Benchmark LoadWorld performance."""
    # First save a large world
    world_state = core_pb2.WorldState()
    world_state.tick_number = 2000

    for i in range(100):
        actor = core_pb2.Actor()
        actor.id = f"actor_{i}"
        actor.name = f"Actor{i}"
        actor.position.x = float(i * 10)
        actor.position.y = float(i * 10)
        world_state.actors[actor.id].CopyFrom(actor)

    save_request = fate_engine_service_pb2.SaveWorldRequest()
    save_request.save_id = "perf_load_test"
    save_request.world_state.CopyFrom(world_state)
    save_request.timestamp.GetCurrentTime()

    await grpc_client.SaveWorld(save_request)

    # Benchmark load
    load_request = fate_engine_service_pb2.LoadWorldRequest()
    load_request.save_id = "perf_load_test"

    start_time = time.time()
    response = await grpc_client.LoadWorld(load_request)
    elapsed = time.time() - start_time

    assert response.success is True
    assert elapsed < 1.0, f"Load too slow: {elapsed:.3f}s"

    print(f"✓ Load performance: {elapsed:.3f}s for {len(response.world_state.actors)} actors")


@pytest.mark.asyncio
async def test_save_world_without_id(grpc_client):
    """Test SaveWorld without specifying a save_id."""
    world_state = core_pb2.WorldState()
    world_state.tick_number = 600

    request = fate_engine_service_pb2.SaveWorldRequest()
    request.world_state.CopyFrom(world_state)
    request.timestamp.GetCurrentTime()
    # No save_id specified - should auto-generate

    response = await grpc_client.SaveWorld(request)

    assert response.success is True
    assert response.save_id is not None
    assert "save_" in response.save_id

    print(f"✓ Auto-generated save ID: {response.save_id}")


@pytest.mark.asyncio
async def test_save_world_metadata(grpc_client):
    """Test SaveWorld with custom metadata."""
    world_state = core_pb2.WorldState()
    world_state.tick_number = 700

    request = fate_engine_service_pb2.SaveWorldRequest()
    request.save_id = "test_metadata"
    request.world_state.CopyFrom(world_state)
    request.timestamp.GetCurrentTime()
    request.metadata["author"] = "test_user"
    request.metadata["description"] = "Test save with metadata"
    request.metadata["tags"] = "test,experimental"
    request.metadata["version"] = "2.0"

    response = await grpc_client.SaveWorld(request)

    assert response.success is True

    # Verify metadata is preserved
    load_request = fate_engine_service_pb2.LoadWorldRequest()
    load_request.save_id = "test_metadata"

    load_response = await grpc_client.LoadWorld(load_request)

    assert load_response.success is True
    assert load_response.metadata["author"] == "test_user"
    assert load_response.metadata["description"] == "Test save with metadata"
    assert load_response.metadata["tags"] == "test,experimental"
    assert load_response.metadata["version"] == "2.0"

    print("✓ Metadata preserved correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
