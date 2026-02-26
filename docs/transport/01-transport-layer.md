# Transport and Communication Layer

**Path:** `tsukuyomi/transport/`

**Last Updated:** 2026-02-26

---

## Overview

The Transport Layer provides gRPC-based communication between simulation components and external clients. It features a comprehensive authentication system using access tokens and session tokens, protocol buffer definitions, server implementation, and client SDKs.

## Philosophy

Per the MVP v0.1 transport architecture:
- **gRPC-Based**: High-performance RPC for agent communication
- **Protocol Buffers**: Efficient serialization
- **Bidirectional Streaming**: Real-time tick state updates via Subscribe/StreamTickUpdates
- **TLS Support**: Secure connections when certificates available
- **Session-Based Authentication**: Handshake with access_token returns session_id for subsequent calls

---

## Component Structure

```
transport/
├── proto/                    # Protocol buffer definitions
│   ├── common_pb2.py        # Common types (Vector2, Timestamp)
│   ├── core_pb2.py          # Core types (Actor, Location, WorldState, Proposal)
│   ├── fate_engine_service_pb2.py  # FateEngine service (SubmitProposal, GetWorldState, StreamTickUpdates, RegisterActor)
│   ├── guest_api_pb2.py     # Guest API service (Handshake, Pulse, SubmitProposal, Subscribe, Disconnect)
│   └── perception_pb2.py    # Perception-related types
├── grpc/
│   ├── server.py            # gRPC server main entry point
│   ├── fate_servicer.py     # FateEngineService implementation
│   ├── guest_servicer.py    # GuestService implementation
│   └── client.py            # FateEngineClient for agents
└── sdk/
    └── guest.py             # GuestAgent SDK for external clients
```

---

## 1. Protocol Buffer Definitions (`proto/`)

### Common Types (`common_pb2.py`)

```protobuf
message Vector2 {
    float x = 1;
    float y = 2;
}

message Vector3 {
    float x = 1;
    float y = 2;
    float z = 3;
}

message Timestamp {
    int64 seconds = 1;
    int32 nanos = 2;
}
```

### Core Types (`core_pb2.py`)

```protobuf
// Core entity types
message Actor {
    string id = 1;
    string name = 2;
    Vector2 position = 3;
    string state = 4;
    string current_location = 5;
}

message Location {
    string name = 1;
    Vector2 position = 2;
}

message EnvironmentObject {
    string id = 1;
    string type = 2;
    Vector2 position = 3;
    bool interactive = 4;
    map<string, string> properties = 5;
}

// World state
message WorldState {
    map<string, Location> locations = 1;
    map<string, Actor> actors = 2;
    map<string, EnvironmentObject> objects = 3;
    repeated string global_events = 4;
}

// Actions and Proposals
enum ActionType {
    UNKNOWN = 0;
    MOVE = 1;
    INTERACT = 2;
    SPEAK = 3;
    OBSERVE = 4;
    COLLECT = 5;
    ATTACK = 6;
    IDLE = 7;
}

message Proposal {
    string proposal_id = 1;
    string actor_id = 2;
    ActionType action = 3;
    map<string, string> parameters = 4;
    Timestamp timestamp = 5;
}

message Resolution {
    string proposal_id = 1;
    bool success = 2;
    map<string, string> outcome = 3;
    string error_message = 4;
}

// Tick State
message TickState {
    int32 tick_number = 1;
    Timestamp timestamp = 2;
    WorldState world_state = 3;
    repeated Proposal pending_proposals = 4;
    repeated Resolution resolutions = 5;
}
```

### Fate Engine Service (`fate_engine_service_pb2.py`)

The FateEngineService provides the core simulation interface for registered agents.

```protobuf
service FateEngineService {
    // Submit a proposal (requires session_token in metadata)
    rpc SubmitProposal(Proposal) returns (SubmitProposalResponse);

    // Get current world state
    rpc GetWorldState(GetWorldStateRequest) returns (WorldState);

    // Stream tick updates in real-time
    rpc StreamTickUpdates(StreamTickUpdatesRequest) returns (stream TickState);

    // Register an actor and receive session token
    rpc RegisterActor(RegisterActorRequest) returns (RegisterActorResponse);
}

message RegisterActorRequest {
    string actor_id = 1;
    string name = 2;
    float x = 3;
    float y = 4;
}

message RegisterActorResponse {
    bool success = 1;
    string message = 2;
    string session_token = 3;  // Returned for subsequent SubmitProposal calls
}

message SubmitProposalResponse {
    bool accepted = 1;
    string message = 2;
    string proposal_id = 3;
}

message GetWorldStateRequest {}

message StreamTickUpdatesRequest {}
```

### Session Token Authentication

1. **RegisterActor**: Client calls `RegisterActor` with actor info
2. **Token Return**: Server returns `session_token` in response
3. **SubmitProposal**: Client includes `session_token` in gRPC metadata
4. **Validation**: Server validates token matches actor_id before accepting proposal

### Guest API Service (`guest_api_pb2.py`)

The GuestService provides a formal entry point for external agents to connect to simulations. It uses a handshake-based authentication flow.

```protobuf
service GuestService {
    // Initial handshake with access token
    rpc Handshake(HandshakeRequest) returns (HandshakeResponse);

    // Heartbeat to keep session alive
    rpc Pulse(PulseRequest) returns (PulseResponse);

    // Submit action proposals
    rpc SubmitProposal(Proposal) returns (SubmitProposalResponse);

    // Subscribe to tick state stream
    rpc Subscribe(SubscribeRequest) returns (stream TickState);

    // Disconnect from simulation
    rpc Disconnect(DisconnectRequest) returns (DisconnectResponse);
}

message HandshakeRequest {
    string agent_id = 1;
    string agent_name = 2;
    string access_token = 3;  // Authentication token
    map<string, string> metadata = 4;
}

message HandshakeResponse {
    bool success = 1;
    string session_id = 2;      // Returned for subsequent calls
    string message = 3;
    map<string, string> world_config = 4;  // e.g., tick_rate
}

message PulseRequest {
    string session_id = 1;
    Timestamp timestamp = 2;
}

message PulseResponse {
    bool acknowledged = 1;
    int64 server_tick = 2;
}

message SubmitProposalResponse {
    bool accepted = 1;
    string message = 2;
    string proposal_id = 3;
}

message SubscribeRequest {
    string session_id = 1;
    uint32 downsample_factor = 2;  // Optional tick downsampling
}

message DisconnectRequest {
    string session_id = 1;
    string reason = 2;
}

message DisconnectResponse {
    bool success = 1;
}
```

### Authentication Flow

1. **Handshake**: Client sends `HandshakeRequest` with `access_token`
2. **Session Creation**: Server validates token, generates `session_id`, registers actor
3. **Subsequent Calls**: Client includes `session_id` in metadata or request body
4. **Pulse**: Client periodically sends `PulseRequest` to maintain session
5. **Disconnect**: Client sends `DisconnectRequest` to clean up

---

## 2. gRPC Server (`grpc/server.py`)

**Location:** `tsukuyomi/transport/grpc/server.py`

Main entry point for the Tsukuyomi gRPC server.

### GrpcServer Class

```python
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
    )

    async def start(self):
        """Start the gRPC server.

        Automatically enables TLS if certificates found at:
        - TLS_CERT_PATH (default: certs/server.crt)
        - TLS_KEY_PATH (default: certs/server.key)
        """

    async def stop(self, grace: float = 5.0):
        """Stop the gRPC server gracefully."""

    async def wait_for_termination(self):
        """Wait for server termination."""
```

### Server Entry Point

```python
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
```

### Command Line Usage

```bash
python -m tsukuyomi.transport.grpc.server \
    --host 0.0.0.0 \
    --port 50051 \
    --tick-rate 20 \
    --seed 42 \
    --db tsukuyomi_history.db
```

---

## 3. Service Implementations

### FateEngineServicer (`grpc/fate_servicer.py`)

Implements the FateEngineService gRPC service with session-based authentication.

```python
class FateEngineServicer(fate_engine_service_pb2_grpc.FateEngineServiceServicer):
    """
    gRPC Service implementation for the Fate Engine.

    Provides external access to:
    - Submit proposals from remote agents (with session token auth)
    - Query world state
    - Stream real-time tick updates to subscribers
    - Register actors and receive session tokens

    Session Token Authentication:
        1. Client calls RegisterActor
        2. Server returns session_token in response
        3. Client includes session_token in metadata for SubmitProposal

    Environment Variables:
        JWT_SECRET: Secret key for JWT validation (default: "tsukuyomi-dev-secret-key-2026")
        JWT_ALGORITHM: Algorithm for JWT validation (default: "HS256")
    """

    def __init__(
        self,
        fate_engine: FateEngine,
        drama_director: Optional[DramaDirector] = None
    ):
        self.engine = fate_engine
        self.drama_director = drama_director
        self._tick_subscribers: list[asyncio.Queue] = []
        self._session_tokens: dict[str, str] = {}  # session_token -> actor_id

        # JWT configuration for Moltbook integration
        self.jwt_secret = os.getenv("JWT_SECRET", "tsukuyomi-dev-secret-key-2026")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        # Register post-resolution hooks
        self.engine.post_resolution_hooks.append(self._broadcast_tick_update)
        if self.drama_director:
            self.engine.post_resolution_hooks.append(self.drama_director.on_tick_resolved)

    async def SubmitProposal(
        self,
        request: core_pb2.Proposal,
        context: grpc.aio.ServicerContext
    ) -> fate_engine_service_pb2.SubmitProposalResponse:
        """
        Submit proposal with session token authentication.

        Authentication flow:
        1. Extract session_token from gRPC metadata
        2. Validate session_token exists in registry
        3. Verify session_token belongs to request.actor_id
        4. (Bypass for test actors with test- prefix)

        Returns SubmitProposalResponse with:
        - accepted: True if proposal accepted
        - message: Status message
        - proposal_id: UUID of proposal
        """

    async def GetWorldState(
        self,
        request: fate_engine_service_pb2.GetWorldStateRequest,
        context: grpc.aio.ServicerContext
    ) -> core_pb2.WorldState:
        """
        Get current world state snapshot.

        Returns WorldState with:
        - tick_number: Current engine tick
        - timestamp: Current time
        - actors: All actors in world
        - locations: All locations
        - objects: All environment objects
        """

    async def StreamTickUpdates(
        self,
        request: fate_engine_service_pb2.StreamTickUpdatesRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[core_pb2.TickState]:
        """
        Stream real-time tick updates.

        Creates a queue for this subscriber and yields TickState messages
        as they are broadcast via _broadcast_tick_update().

        Sends heartbeat if no updates within 5 seconds to keep connection alive.
        """

    async def RegisterActor(
        self,
        request: fate_engine_service_pb2.RegisterActorRequest,
        context: grpc.aio.ServicerContext
    ) -> fate_engine_service_pb2.RegisterActorResponse:
        """
        Register actor and return session token.

        Supports Moltbook JWT in authorization metadata:
        - If "Bearer: <token>" found, validates JWT (Phase 9)

        Returns RegisterActorResponse with:
        - success: True if registered
        - message: Status message
        - session_token: UUID for subsequent SubmitProposal calls
        """

    async def _broadcast_tick_update(self, tick: int, resolutions: list):
        """
        Broadcast tick state to all subscribers.

        Called automatically after each tick resolution via post_resolution_hooks.
        """
```

### GuestServicer (`grpc/guest_servicer.py`)

Implements the GuestService gRPC service for external agent integration.

```python
class GuestServicer(guest_api_pb2_grpc.GuestServiceServicer):
    """
    gRPC Service implementation for the Guest API.

    Provides a formal entry point for external agents with:
    - Handshake authentication using access_token
    - Session-based communication with session_id
    - Pulse mechanism for connection keep-alive
    - Tick streaming for real-time updates
    - Clean disconnect handling

    Environment Variables:
        GUEST_ACCESS_TOKEN: Expected access token (default: "tsukuyomi-secret-2026")
    """

    def __init__(self, fate_engine: FateEngine):
        self.engine = fate_engine
        self.sessions: dict[str, str] = {}  # session_id -> agent_id

    async def Handshake(
        self,
        request: guest_api_pb2.HandshakeRequest,
        context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.HandshakeResponse:
        """
        Authenticate and establish session.

        Process:
        1. Validate access_token
        2. Generate session_id (UUID4)
        3. Register actor in engine
        4. Return session_id for subsequent calls

        Returns HandshakeResponse with:
        - success: True if authenticated
        - session_id: UUID for this session
        - message: Welcome message or error
        - world_config: e.g., {"tick_rate": "20"}
        """

    async def Pulse(
        self,
        request: guest_api_pb2.PulseRequest,
        context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.PulseResponse:
        """
        Heartbeat to keep session alive.

        Returns PulseResponse with:
        - acknowledged: True if session valid
        - server_tick: Current engine tick
        """

    async def SubmitProposal(
        self,
        request: core_pb2.Proposal,
        context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.SubmitProposalResponse:
        """
        Submit proposal (requires session_token in metadata).

        Validates:
        1. session_token metadata exists
        2. session_token is valid
        3. session_token belongs to request.actor_id

        Then delegates to engine.submit_proposal().
        """

    async def Subscribe(
        self,
        request: guest_api_pb2.SubscribeRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[core_pb2.TickState]:
        """
        Subscribe to tick state stream.

        Requires session_token in metadata.
        Yields TickState messages as they occur.
        """

    async def Disconnect(
        self,
        request: guest_api_pb2.DisconnectRequest,
        context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.DisconnectResponse:
        """
        Disconnect and clean up session.

        Unregisters actor and removes session mapping.
        """
```

---

## 4. gRPC Client (`grpc/client.py`)

**Location:** `tsukuyomi/transport/grpc/client.py`

Client for agents connecting to the Fate Engine with session token management.

```python
class FateEngineClient:
    """
    gRPC Client for the Fate Engine.

    Provides a high-level API for:
    - Submitting proposals (actions)
    - Querying world state
    - Streaming tick updates

    Security Configuration:
        allow_insecure: If False (default), connection fails when TLS cert not found.
                       If True, falls back to insecure connection with warning.

    Environment Variables:
        TLS_CERT_PATH: Path to TLS certificate (default: "certs/server.crt")

    Usage:
        client = FateEngineClient("localhost:50051")
        await client.connect()

        # Register actor and get session token
        await client.register_actor("agent-1", "Agent One")

        # Submit proposals (session token auto-included)
        await client.move("agent-1", "tavern")

        # Stream ticks
        async for tick in client.stream_tick_updates():
            print(f"Tick {tick.tick_number}")
    """

    def __init__(
        self,
        server_address: str = "localhost:50051",
        allow_insecure: bool = False
    ):
        self.server_address = server_address
        self.allow_insecure = allow_insecure
        self._session_tokens: Dict[str, str] = {}  # actor_id -> session_token

    async def connect(self) -> bool:
        """
        Connect to the Fate Engine server.

        Security:
        - If TLS cert found: Uses secure channel
        - If TLS cert NOT found and allow_insecure=True: Falls back to insecure
        - If TLS cert NOT found and allow_insecure=False: Raises RuntimeError
        """

    async def disconnect(self):
        """Disconnect from the server."""

    # -------------------------------------------------------------------------
    # Actor Management
    # -------------------------------------------------------------------------

    async def register_actor(
        self,
        actor_id: str,
        name: str,
        x: float = 0.0,
        y: float = 0.0
    ) -> bool:
        """
        Register a new actor and store session token.

        The returned session_token is stored and automatically included
        in subsequent submit_proposal() calls for this actor.

        Returns True if registration successful.
        """

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
        Submit a proposal with automatic session token inclusion.

        Args:
            actor_id: UUID of the actor making the proposal
            action: Action type (MOVE, INTERACT, IDLE, EMOTE)
            parameters: Action-specific parameters
            proposal_id: Optional custom proposal ID

        Returns:
            Tuple of (accepted, message, proposal_id)

        Raises:
            RuntimeError: If no session token for actor_id
        """

    async def move(
        self,
        actor_id: str,
        destination: str
    ) -> tuple[bool, str, str]:
        """Submit a MOVE proposal."""

    async def interact(
        self,
        actor_id: str,
        target_id: str,
        interaction_type: str = "generic"
    ) -> tuple[bool, str, str]:
        """Submit an INTERACT proposal."""

    async def emote(
        self,
        actor_id: str,
        emote_type: str = "wave"
    ) -> tuple[bool, str, str]:
        """Submit an EMOTE proposal."""

    async def idle(
        self,
        actor_id: str,
        duration: str = "1"
    ) -> tuple[bool, str, str]:
        """Submit an IDLE proposal."""

    # -------------------------------------------------------------------------
    # World State Query
    # -------------------------------------------------------------------------

    async def get_world_state(self) -> core_pb2.WorldState:
        """Get the current world state."""

    async def get_actors(self) -> Dict[str, core_pb2.Actor]:
        """Get all actors from the world state."""

    async def get_locations(self) -> Dict[str, core_pb2.Location]:
        """Get all locations from the world state."""

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

    async def watch_ticks(
        self,
        num_ticks: int = 10,
        callback: Optional[Callable[[core_pb2.TickState], None]] = None
    ) -> list[core_pb2.TickState]:
        """
        Watch a specific number of ticks.

        Returns:
            List of TickState messages
        """
```

---

## 5. Guest SDK (`sdk/guest.py`)

**Location:** `tsukuyomi/transport/sdk/guest.py`

Python SDK for external agents to connect to Tsukuyomi simulations as guests.

### GuestAgent Class

```python
class GuestAgent:
    """
    Python SDK for external agents to connect to Tsukuyomi.

    Provides:
    - Handshake authentication with access_token
    - Session-based communication
    - Proposal submission
    - Pulse heartbeat mechanism
    - Real-time tick streaming

    Security:
        - Uses TLS when certificates are available
        - Requires access token for handshake authentication

    Environment Variables:
        GUEST_ACCESS_TOKEN: Access token for handshake (default: "tsukuyomi-secret-2026")
        TLS_CERT_PATH: Path to TLS certificate (default: "certs/server.crt")

    Usage:
        from tsukuyomi.transport.sdk.guest import GuestAgent

        agent = GuestAgent("my_agent", "MyAgent", "localhost:50051")
        await agent.connect(access_token="tsukuyomi-secret-2026")

        # Submit proposal
        await agent.submit_proposal("MOVE", {"destination": "tavern"})

        # Stream ticks
        async for tick in agent.stream_updates():
            print(f"Tick {tick.tick_number}")

        await agent.disconnect()
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        server_addr: str = "localhost:50051"
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.server_addr = server_addr
        self.session_id: Optional[str] = None
        self.is_connected = False

    async def connect(self, access_token: str = None) -> bool:
        """
        Establish connection via Handshake.

        Process:
        1. Establishes secure (TLS) or insecure channel
        2. Sends HandshakeRequest with access_token
        3. Receives session_id for subsequent calls
        4. Registers actor automatically on server

        Args:
            access_token: Authentication token (uses GUEST_ACCESS_TOKEN env var if None)

        Returns:
            True if connection successful, False otherwise
        """

    async def disconnect(self, reason: str = "Graceful exit"):
        """
        Disconnect from the simulation.

        Sends DisconnectRequest and closes the channel.
        """

    async def submit_proposal(
        self,
        action: str,
        params: Dict[str, str] = None
    ) -> bool:
        """
        Submit an action proposal.

        Automatically includes session_id in metadata for authentication.

        Args:
            action: Action type (e.g., "MOVE", "INTERACT", "EMOTE")
            params: Action parameters

        Returns:
            True if proposal accepted, False otherwise
        """

    async def pulse(self) -> bool:
        """
        Send heartbeat pulse to keep session alive.

        Returns:
            True if acknowledged by server, False otherwise
        """

    async def stream_updates(self) -> AsyncIterator[core_pb2.TickState]:
        """
        Subscribe to tick state stream.

        Yields:
            TickState messages as they occur

        Note:
            Requires connect() to have been called first.
        """
```

### Example Usage

```python
import asyncio
from tsukuyomi.transport.sdk.guest import GuestAgent

async def run_guest():
    agent = GuestAgent("guest-007", "James Bond", "localhost:50051")

    if await agent.connect():
        # Submit an action
        await agent.submit_proposal("MOVE", {"destination": "tavern"})

        # Send heartbeats
        for _ in range(3):
            await agent.pulse()
            await asyncio.sleep(1)

        await agent.disconnect()

asyncio.run(run_guest())
```

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_grpc_server.py` | GrpcServer lifecycle, TLS handling |
| `test_fate_servicer.py` | FateEngineServicer RPC methods, session token auth |
| `test_guest_servicer.py` | GuestServicer RPC methods, handshake auth |
| `test_client.py` | FateEngineClient connection, session management |
| `test_guest_agent.py` | GuestAgent SDK functionality |

---

## Dependencies

**Internal:**
- `tsukuyomi.environment.core.FateEngine` - Core engine
- `tsukuyomi.narrative.core.DramaDirector` - Narrative director
- `tsukuyomi.shared.utils.to_pb_timestamp` - Timestamp conversion

**External:**
- `grpc` - gRPC framework
- `grpc.aio` - Async gRPC
- `asyncio` - Async operations
- `uuid` - Session ID/token generation
- `os` - Environment variable access
- `logging` - Logging

**Environment Variables:**

| Variable | Purpose | Default |
|----------|---------|---------|
| `GUEST_ACCESS_TOKEN` | Access token for Guest API handshake | "tsukuyomi-secret-2026" |
| `TLS_CERT_PATH` | Path to TLS certificate | "certs/server.crt" |
| `JWT_SECRET` | Secret key for JWT validation | "tsukuyomi-dev-secret-key-2026" |
| `JWT_ALGORITHM` | Algorithm for JWT validation | "HS256" |

---

## Design Principles

1. **gRPC-Based**: High-performance RPC for all communication
2. **Protocol Buffers**: Efficient binary serialization
3. **Bidirectional Streaming**: Real-time tick updates via Subscribe/StreamTickUpdates
4. **Session-Based Authentication**:
   - Handshake with access_token returns session_id
   - RegisterActor returns session_token
   - Subsequent calls require session token in metadata
5. **TLS Ready**: Secure connections when certificates available
6. **Service Separation**: FateEngineService and GuestService for different use cases
7. **Pulse Mechanism**: Heartbeat for session keep-alive
8. **SDK Abstraction**: High-level GuestAgent SDK for ease of use
9. **Test Bypass**: Allows test actors (prefixed with "test-") without full authentication