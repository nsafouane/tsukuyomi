"""
Guest SDK - External Agent Integration

Provides a Python SDK for external agents to connect to Tsukuyomi
simulations as guests. Supports handshake authentication, action
submission, and real-time tick streaming.

Usage:
    from tsukuyomi.guest_sdk import GuestAgent
    
    agent = GuestAgent("my_agent", "MyAgent", "localhost:50051")
    await agent.connect(access_token="tsukuyomi-secret-2026")
    await agent.register()
    
    async for tick in agent.stream_ticks():
        # Process tick updates
        pass

Security:
- Uses TLS when certificates are available
- Requires access token for handshake authentication
"""

import asyncio
import logging
import uuid
import os
from typing import Dict, Optional, AsyncIterator
import grpc
from tsukuyomi.proto import guest_api_pb2
from tsukuyomi.proto import guest_api_pb2_grpc
from tsukuyomi.proto import core_pb2

logger = logging.getLogger("GuestSDK")

class GuestAgent:
    """
    Python SDK for external agents to connect to Tsukuyomi.
    """
    
    def __init__(self, agent_id: str, agent_name: str, server_addr: str = "localhost:50051"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.server_addr = server_addr
        self.session_id: Optional[str] = None
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[guest_api_pb2_grpc.GuestServiceStub] = None
        self.is_connected = False
        
    async def connect(self, access_token: str = None) -> bool:
        """Establish connection via Handshake."""
        if access_token is None:
            access_token = os.getenv("GUEST_ACCESS_TOKEN", "tsukuyomi-secret-2026")
            
        logger.info(f"Connecting to Tsukuyomi at {self.server_addr}...")
        
        # Security: Use secure channel if certificates are found
        tls_cert_path = os.getenv("TLS_CERT_PATH", "certs/server.crt")
        if os.path.exists(tls_cert_path):
            with open(tls_cert_path, 'rb') as f:
                creds = grpc.ssl_channel_credentials(f.read())
            self.channel = grpc.aio.secure_channel(self.server_addr, creds)
            logger.info("Using secure channel (TLS)")
        else:
            self.channel = grpc.aio.insecure_channel(self.server_addr)
            logger.warning("Using insecure channel")

        self.stub = guest_api_pb2_grpc.GuestServiceStub(self.channel)
        
        try:
            request = guest_api_pb2.HandshakeRequest(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                access_token=access_token
            )
            response = await self.stub.Handshake(request)
            
            if response.success:
                self.session_id = response.session_id
                self.is_connected = True
                logger.info(f"Connected! Session ID: {self.session_id}")
                logger.info(f"Server Message: {response.message}")
                return True
            else:
                logger.error(f"Handshake failed: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self, reason: str = "Graceful exit"):
        """Disconnect from the simulation."""
        if not self.is_connected or not self.session_id:
            return
            
        try:
            request = guest_api_pb2.DisconnectRequest(
                session_id=self.session_id,
                reason=reason
            )
            await self.stub.Disconnect(request)
            logger.info("Disconnected from Tsukuyomi.")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
        finally:
            self.is_connected = False
            if self.channel:
                await self.channel.close()

    async def submit_proposal(self, action: str, params: Dict[str, str] = None) -> bool:
        """Submit an action proposal."""
        if not self.is_connected:
            return False
            
        try:
            # Map string action to Enum
            action_enum = getattr(core_pb2, action.upper(), core_pb2.ACTION_TYPE_UNSPECIFIED)
            
            proposal = core_pb2.Proposal(
                proposal_id=str(uuid.uuid4()),
                actor_id=self.agent_id,
                action=action_enum,
                parameters=params or {}
            )
            metadata = [("session_token", self.session_id)]
            response = await self.stub.SubmitProposal(proposal, metadata=metadata)
            return response.accepted
        except Exception as e:
            logger.error(f"SubmitProposal error: {e}")
            return False

    async def pulse(self) -> bool:
        """Send heartbeat pulse."""
        if not self.is_connected:
            return False
            
        try:
            request = guest_api_pb2.PulseRequest(session_id=self.session_id)
            response = await self.stub.Pulse(request)
            return response.acknowledged
        except Exception as e:
            logger.error(f"Pulse error: {e}")
            return False

    async def stream_updates(self) -> AsyncIterator[core_pb2.TickState]:
        """Subscribe to tick updates."""
        if not self.is_connected:
            return
            
        request = guest_api_pb2.SubscribeRequest(session_id=self.session_id)
        async for tick in self.stub.Subscribe(request):
            yield tick

async def run_guest_example():
    logging.basicConfig(level=logging.INFO)
    agent = GuestAgent("guest-007", "James Bond")
    
    if await agent.connect():
        # Submit an action
        await agent.submit_proposal("MOVE", {"destination": "tavern"})
        
        # Pulse for a bit
        for _ in range(3):
            await agent.pulse()
            await asyncio.sleep(1)
            
        await agent.disconnect()

if __name__ == "__main__":
    asyncio.run(run_guest_example())
