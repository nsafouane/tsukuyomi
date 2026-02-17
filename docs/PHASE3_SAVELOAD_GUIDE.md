# Tsukuyomi V2 Phase 3 - SaveWorld/LoadWorld Usage Guide

## Overview

The SaveWorld/LoadWorld system allows you to save and restore complete simulation states in Tsukuyomi V2 Phase 3. This guide covers how to use the SaveWorld and LoadWorld gRPC methods, best practices, and common use cases.

## Table of Contents

1. [Introduction](#introduction)
2. [API Overview](#api-overview)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Best Practices](#best-practices)
6. [Use Cases](#use-cases)
7. [Troubleshooting](#troubleshooting)

## Introduction

SaveWorld and LoadWorld are gRPC methods that provide persistence for Tsukuyomi simulations:

- **SaveWorld**: Serializes the current world state and saves it to persistent storage
- **LoadWorld**: Restores a previously saved world state

Key features:
- Complete world state preservation (actors, objects, locations)
- Metadata support for custom save information
- Multiple save slots
- Cross-platform compatibility
- Efficient serialization using Protocol Buffers

## API Overview

### SaveWorld

#### Request (SaveWorldRequest)

```protobuf
message SaveWorldRequest {
  string save_id = 1;                    // Optional: Save identifier
  WorldState world_state = 2;             // World state to save
  Timestamp timestamp = 3;               // Save timestamp
  map<string, string> metadata = 4;      // Custom metadata
}
```

#### Response (SaveWorldResponse)

```protobuf
message SaveWorldResponse {
  bool success = 1;                      // Whether save succeeded
  string save_id = 2;                    // Generated or provided save ID
  string message = 3;                    // Status message
  uint64 size_bytes = 4;                 // Size of saved data
}
```

### LoadWorld

#### Request (LoadWorldRequest)

```protobuf
message LoadWorldRequest {
  string save_id = 1;                     // Save identifier to load
}
```

#### Response (LoadWorldResponse)

```protobuf
message LoadWorldResponse {
  bool success = 1;                      // Whether load succeeded
  WorldState world_state = 2;             // Loaded world state
  string message = 3;                     // Status message
  map<string, string> metadata = 4;       // Save metadata
}
```

### ListSaves

#### Request (ListSavesRequest)

```protobuf
message ListSavesRequest {
  // Empty request
}
```

#### Response (ListSavesResponse)

```protobuf
message ListSavesResponse {
  bool success = 1;                      // Whether list succeeded
  repeated SaveInfo saves = 2;            // List of save information
}

message SaveInfo {
  string save_id = 1;                     // Save identifier
  Timestamp timestamp = 2;               // Save timestamp
  map<string, string> metadata = 3;      // Save metadata
}
```

### DeleteSave

#### Request (DeleteSaveRequest)

```protobuf
message DeleteSaveRequest {
  string save_id = 1;                     // Save identifier to delete
}
```

#### Response (DeleteSaveResponse)

```protobuf
message DeleteSaveResponse {
  bool success = 1;                      // Whether delete succeeded
  string message = 2;                     // Status message
}
```

## Basic Usage

### Python Client Example

```python
import grpc
from tsukuyomi.proto import (
    core_pb2,
    fate_engine_service_pb2,
    fate_engine_service_pb2_grpc
)

# Connect to Fate Engine
channel = grpc.insecure_channel('localhost:50051')
stub = fate_engine_service_pb2_grpc.FateEngineServiceStub(channel)

# Save World
def save_world(save_id: str = None):
    """Save the current world state."""
    # Get current world state
    get_world_req = fate_engine_service_pb2.GetWorldStateRequest()
    world_state = stub.GetWorldState(get_world_req)

    # Create save request
    save_req = fate_engine_service_pb2.SaveWorldRequest()
    if save_id:
        save_req.save_id = save_id
    save_req.world_state.CopyFrom(world_state)
    save_req.timestamp.GetCurrentTime()

    # Add metadata
    save_req.metadata["tick"] = str(world_state.tick_number)
    save_req.metadata["actors"] = str(len(world_state.actors))
    save_req.metadata["description"] = f"Save at tick {world_state.tick_number}"

    # Save
    response = stub.SaveWorld(save_req)

    if response.success:
        print(f"World saved: {response.save_id} ({response.size_bytes} bytes)")
        return response.save_id
    else:
        print(f"Save failed: {response.message}")
        return None

# Load World
def load_world(save_id: str):
    """Load a saved world state."""
    load_req = fate_engine_service_pb2.LoadWorldRequest()
    load_req.save_id = save_id

    response = stub.LoadWorld(load_req)

    if response.success:
        print(f"World loaded: {save_id}")
        print(f"Tick: {response.world_state.tick_number}")
        print(f"Actors: {len(response.world_state.actors)}")
        print(f"Metadata: {dict(response.metadata)}")
        return response.world_state
    else:
        print(f"Load failed: {response.message}")
        return None

# List Saves
def list_saves():
    """List all saved worlds."""
    list_req = fate_engine_service_pb2.ListSavesRequest()
    response = stub.ListSaves(list_req)

    if response.success:
        print(f"Found {len(response.saves)} saves:")
        for save in response.saves:
            print(f"  - {save.save_id}: {dict(save.metadata)}")
        return response.saves
    else:
        print(f"List failed: {response.message}")
        return []

# Delete Save
def delete_save(save_id: str):
    """Delete a saved world."""
    delete_req = fate_engine_service_pb2.DeleteSaveRequest()
    delete_req.save_id = save_id

    response = stub.DeleteSave(delete_req)

    if response.success:
        print(f"Save deleted: {save_id}")
        return True
    else:
        print(f"Delete failed: {response.message}")
        return False
```

### Async Python Client Example

```python
import grpc.aio
from tsukuyomi.proto import (
    fate_engine_service_pb2,
    fate_engine_service_pb2_grpc
)

async def save_world_async(stub, save_id: str = None):
    """Save world asynchronously."""
    get_world_req = fate_engine_service_pb2.GetWorldStateRequest()
    world_state = await stub.GetWorldState(get_world_req)

    save_req = fate_engine_service_pb2.SaveWorldRequest()
    if save_id:
        save_req.save_id = save_id
    save_req.world_state.CopyFrom(world_state)
    save_req.timestamp.GetCurrentTime()

    response = await stub.SaveWorld(save_req)
    return response.save_id if response.success else None

async def load_world_async(stub, save_id: str):
    """Load world asynchronously."""
    load_req = fate_engine_service_pb2.LoadWorldRequest()
    load_req.save_id = save_id

    response = await stub.LoadWorld(load_req)
    return response.world_state if response.success else None

# Usage
async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = fate_engine_service_pb2_grpc.FateEngineServiceStub(channel)

        # Save
        save_id = await save_world_async(stub, "my_save")
        print(f"Saved: {save_id}")

        # Load
        world_state = await load_world_async(stub, "my_save")
        print(f"Loaded tick: {world_state.tick_number}")

import asyncio
asyncio.run(main())
```

## Advanced Features

### Auto-Generated Save IDs

If you don't provide a `save_id`, the server will automatically generate one:

```python
save_req = fate_engine_service_pb2.SaveWorldRequest()
save_req.world_state.CopyFrom(world_state)
save_req.timestamp.GetCurrentTime()
# No save_id provided

response = stub.SaveWorld(save_req)
# Response will contain auto-generated save_id like "save_1234567890"
```

### Custom Metadata

Store custom information with your saves:

```python
save_req.metadata["author"] = "alice"
save_req.metadata["description"] = "Before the dragon fight"
save_req.metadata["tags"] = "checkpoint,important"
save_req.metadata["difficulty"] = "hard"
save_req.metadata["version"] = "3.0"
```

### Multiple Save Slots

Create multiple save points for different scenarios:

```python
# Create checkpoints
save_ids = []
for tick in [100, 200, 300]:
    world_state = get_world_state_at_tick(tick)
    save_id = f"checkpoint_{tick}"
    save_ids.append(save_world(save_id))

# Rollback to any checkpoint
load_world("checkpoint_200")
```

### Conditional Saving

Save only under certain conditions:

```python
def conditional_save(world_state, condition_fn):
    """Save world only if condition is met."""
    if condition_fn(world_state):
        save_id = f"save_{world_state.tick_number}"
        return save_world(save_id)
    return None

# Example: Save when actor reaches certain location
def actor_at_location(actor_id, location):
    def check(world_state):
        if actor_id in world_state.actors:
            return world_state.actors[actor_id].current_location == location
        return False
    return check

world_state = stub.GetWorldState(fate_engine_service_pb2.GetWorldStateRequest())
conditional_save(world_state, actor_at_location("alice", "castle"))
```

### Differential Saving

Save only changes from previous save:

```python
class DifferentialSaver:
    def __init__(self, stub):
        self.stub = stub
        self.previous_state = None

    def save_delta(self, save_id):
        """Save only changed data."""
        current_state = self.stub.GetWorldState(
            fate_engine_service_pb2.GetWorldStateRequest()
        )

        if self.previous_state:
            # Compare and save only differences
            delta = compute_delta(self.previous_state, current_state)
            save_req = fate_engine_service_pb2.SaveWorldRequest()
            save_req.save_id = save_id
            save_req.world_state.CopyFrom(delta)
            save_req.metadata["type"] = "differential"
            response = self.stub.SaveWorld(save_req)

        self.previous_state = current_state
        return response.save_id
```

### Compression

For large worlds, enable compression:

```python
import zlib

def save_compressed(stub, save_id):
    """Save world with compression."""
    world_state = stub.GetWorldState(
        fate_engine_service_pb2.GetWorldStateRequest()
    )

    # Serialize and compress
    serialized = world_state.SerializeToString()
    compressed = zlib.compress(serialized)

    # Store in metadata
    save_req = fate_engine_service_pb2.SaveWorldRequest()
    save_req.save_id = save_id
    save_req.metadata["compressed_size"] = str(len(compressed))
    save_req.metadata["original_size"] = str(len(serialized))
    save_req.metadata["compression_ratio"] = f"{len(compressed) / len(serialized):.2f}"

    response = stub.SaveWorld(save_req)
    return response
```

## Best Practices

### Save Frequency

Save at appropriate intervals:

```python
# Good: Periodic saves
if tick_number % 100 == 0:
    save_world(f"checkpoint_{tick_number}")

# Good: Before major events
if major_event_about_to_happen():
    save_world(f"before_event_{event_name}")

# Bad: Save every tick (too frequent)
# save_world(f"save_{tick_number}")  # Don't do this
```

### Save Naming

Use descriptive save names:

```python
# Good: Descriptive names
save_world("checkpoint_100")
save_world("before_dragon_fight")
save_world("alice_at_castle")

# Bad: Generic names
save_world("save_1")
save_world("temp")
```

### Metadata Standards

Use consistent metadata:

```python
# Recommended metadata
save_req.metadata["tick"] = str(world_state.tick_number)
save_req.metadata["timestamp"] = str(time.time())
save_req.metadata["actors"] = str(len(world_state.actors))
save_req.metadata["objects"] = str(len(world_state.objects))
save_req.metadata["version"] = "3.0"

# Optional: Application-specific
save_req.metadata["author"] = "simulation_name"
save_req.metadata["description"] = "Human-readable description"
save_req.metadata["tags"] = "comma,separated,tags"
```

### Error Handling

Always handle errors:

```python
def safe_save(world_state, save_id, retries=3):
    """Save with error handling and retries."""
    for attempt in range(retries):
        try:
            save_req = fate_engine_service_pb2.SaveWorldRequest()
            save_req.save_id = save_id
            save_req.world_state.CopyFrom(world_state)
            save_req.timestamp.GetCurrentTime()

            response = stub.SaveWorld(save_req, timeout=30.0)

            if response.success:
                return response.save_id
            else:
                print(f"Save failed: {response.message}")

        except grpc.RpcError as e:
            print(f"RPC error (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(1 ** attempt)

    raise Exception(f"Failed to save after {retries} attempts")
```

### Cleanup

Regularly clean up old saves:

```python
def cleanup_old_saves(max_saves=10):
    """Keep only the most recent saves."""
    saves = list_saves()
    saves.sort(key=lambda s: s.timestamp.seconds, reverse=True)

    for save in saves[max_saves:]:
        delete_save(save.save_id)
        print(f"Deleted old save: {save.save_id}")
```

## Use Cases

### Scenario 1: Checkpoint System

Create regular checkpoints:

```python
class CheckpointManager:
    def __init__(self, stub, interval=100, max_checkpoints=10):
        self.stub = stub
        self.interval = interval
        self.max_checkpoints = max_checkpoints
        self.checkpoints = []

    def create_checkpoint(self, tick_number):
        """Create a checkpoint at current tick."""
        if tick_number % self.interval == 0:
            save_id = f"checkpoint_{tick_number}"
            saved = save_world(save_id)
            if saved:
                self.checkpoints.append(saved)
                self._cleanup_old()

    def restore_checkpoint(self, tick_number):
        """Restore checkpoint at specific tick."""
        save_id = f"checkpoint_{tick_number}"
        return load_world(save_id)

    def latest_checkpoint(self):
        """Get the latest checkpoint."""
        if self.checkpoints:
            return load_world(self.checkpoints[-1])
        return None

    def _cleanup_old(self):
        """Remove old checkpoints."""
        while len(self.checkpoints) > self.max_checkpoints:
            old_save = self.checkpoints.pop(0)
            delete_save(old_save)

# Usage
manager = CheckpointManager(stub, interval=100, max_checkpoints=5)

while running:
    tick()
    manager.create_checkpoint(current_tick)
```

### Scenario 2: Branching Simulations

Create multiple simulation branches:

```python
def create_branch(parent_save_id, branch_name, modifications):
    """Create a new branch from existing save."""
    # Load parent save
    world_state = load_world(parent_save_id)

    # Apply modifications
    for mod in modifications:
        apply_modification(world_state, mod)

    # Save as new branch
    save_id = f"branch_{branch_name}"
    return save_world(save_id)

# Example: Create "alice_dies" branch
modifications = [
    {"type": "remove_actor", "actor_id": "alice"},
    {"type": "add_event", "event": "Alice has fallen in battle"}
]

create_branch("checkpoint_200", "alice_dies", modifications)
```

### Scenario 3: A/B Testing

Test different scenarios from same save:

```python
def run_ab_test(base_save_id, scenarios):
    """Run multiple scenarios from same save."""
    results = {}

    for scenario_name, scenario_mods in scenarios.items():
        # Load base save
        world_state = load_world(base_save_id)

        # Apply scenario modifications
        for mod in scenario_mods:
            apply_modification(world_state, mod)

        # Run simulation
        result = run_simulation(world_state, duration=100)
        results[scenario_name] = result

    return results

# Example
scenarios = {
    "peaceful": [{"type": "set_mode", "mode": "peaceful"}],
    "aggressive": [{"type": "set_mode", "mode": "aggressive"}],
    "balanced": [{"type": "set_mode", "mode": "balanced"}]
}

results = run_ab_test("checkpoint_100", scenarios)
```

### Scenario 4: Time Travel

Implement time travel by jumping between saves:

```python
class TimeTravelManager:
    def __init__(self, stub):
        self.stub = stub
        self.timeline = []

    def record_state(self, tick_number):
        """Record current state in timeline."""
        save_id = f"timeline_{tick_number}"
        saved = save_world(save_id)
        if saved:
            self.timeline.append((tick_number, saved))

    def travel_to(self, tick_number):
        """Travel to specific tick."""
        for recorded_tick, save_id in self.timeline:
            if recorded_tick == tick_number:
                return load_world(save_id)
        raise Exception(f"Tick {tick_number} not found in timeline")

    def list_available_ticks(self):
        """List all available ticks in timeline."""
        return [tick for tick, _ in self.timeline]

# Usage
manager = TimeTravelManager(stub)

# Record timeline
for tick in [100, 150, 200, 250]:
    simulate_to(tick)
    manager.record_state(tick)

# Time travel
manager.travel_to(150)
```

## Troubleshooting

### Common Issues

#### Save ID Already Exists

```
Error: Save with ID "checkpoint_100" already exists
```

**Solution**: Use unique save IDs:
```python
import time
save_id = f"checkpoint_{tick_number}_{int(time.time())}"
```

#### World State Too Large

```
Error: World state exceeds maximum size
```

**Solution**: Enable compression or save less frequently:
```python
save_req.metadata["compressed"] = "true"
```

#### Connection Timeout

```
Error: SaveWorld timed out
```

**Solution**: Increase timeout or save smaller states:
```python
response = stub.SaveWorld(save_req, timeout=60.0)
```

#### Load Failed: Corrupted Data

```
Error: Failed to parse world state
```

**Solution**: Verify save integrity:
```python
def verify_save(save_id):
    """Verify save integrity."""
    try:
        world_state = load_world(save_id)
        return world_state is not None
    except Exception as e:
        print(f"Save corrupted: {e}")
        return False
```

### Debug Tips

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

grpc_channel = grpc.insecure_channel('localhost:50051', options=[
    ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
    ('grpc.max_send_message_length', 100 * 1024 * 1024)
])
```

## Conclusion

The SaveWorld/LoadWorld system provides robust persistence for Tsukuyomi simulations. By following best practices and using advanced features, you can create sophisticated save/load mechanisms for your applications.

---

**Version:** 3.0
**Last Updated:** 2026-02-15
**Phase:** Tsukuyomi V2 Phase 3 (Persistence & Scale)
