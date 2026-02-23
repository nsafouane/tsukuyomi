"""
TSUKUYOMI Guest Servicer Implementation
========================================

Implements the GuestService gRPC servicer for external agent integration.
Provides a formal entry point for external agents to connect to simulations.

Author: Tanit (OpenClaw Agent)
Date: 2026-02-04
"""

import asyncio
import logging
import uuid
from typing import AsyncIterator

import grpc
from grpc import aio
import os

# Import generated protobuf classes
from tsukuyomi.transport.proto import core_pb2
from tsukuyomi.transport.proto import guest_api_pb2
from tsukuyomi.transport.proto import guest_api_pb2_grpc

# Import the Fate Engine
from tsukuyomi.environment.core import FateEngine

logger = logging.getLogger("gRPC.GuestServicer")


class GuestServicer(guest_api_pb2_grpc.GuestServiceServicer):
    """
    gRPC Service implementation for the Guest API.

    Provides a formal entry point for external agents.
    """

    def __init__(self, fate_engine: FateEngine):
        self.engine = fate_engine
        self.sessions: dict[str, str] = {}  # session_id -> agent_id

    async def Handshake(
        self, request: guest_api_pb2.HandshakeRequest, context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.HandshakeResponse:
        logger.info(f"Handshake request from {request.agent_name} ({request.agent_id})")

        # Simple access token check
        expected_token = os.getenv("GUEST_ACCESS_TOKEN", "tsukuyomi-secret-2026")
        if request.access_token != expected_token:
            return guest_api_pb2.HandshakeResponse(
                success=False, message="Invalid access token."
            )

        session_id = str(uuid.uuid4())
        self.sessions[session_id] = request.agent_id

        # Register the actor in the engine automatically
        self.engine.register_actor(request.agent_id, request.agent_name)

        return guest_api_pb2.HandshakeResponse(
            success=True,
            session_id=session_id,
            message=f"Welcome, {request.agent_name}. Connection established.",
            world_config={"tick_rate": str(self.engine.tick_rate)},
        )

    async def Pulse(
        self, request: guest_api_pb2.PulseRequest, context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.PulseResponse:
        if request.session_id not in self.sessions:
            return guest_api_pb2.PulseResponse(acknowledged=False)

        return guest_api_pb2.PulseResponse(
            acknowledged=True, server_tick=self.engine.current_tick
        )

    async def SubmitProposal(
        self, request: core_pb2.Proposal, context: grpc.aio.ServicerContext
    ) -> guest_api_pb2.SubmitProposalResponse:
        # FIX: Validate session token from metadata
        metadata = dict(context.invocation_metadata())
        session_token = metadata.get("session_token", "")

        if not session_token:
            logger.warning(
                f"SubmitProposal rejected: no session token from {request.actor_id}"
            )
            return guest_api_pb2.SubmitProposalResponse(
                accepted=False,
                message="Authentication required: session_token metadata missing",
                proposal_id="",
            )

        # Validate session token and actor_id match
        if session_token not in self.sessions:
            logger.warning(
                f"SubmitProposal rejected: invalid session token from {request.actor_id}"
            )
            return guest_api_pb2.SubmitProposalResponse(
                accepted=False,
                message="Authentication failed: invalid session token",
                proposal_id="",
            )

        # Verify that the session token belongs to the actor_id in the request
        if self.sessions[session_token] != request.actor_id:
            logger.warning(
                f"SubmitProposal rejected: session token belongs to different actor"
            )
            return guest_api_pb2.SubmitProposalResponse(
                accepted=False,
                message="Authentication failed: session token does not match actor_id",
                proposal_id="",
            )

        # We leverage the existing logic in FateEngine
        accepted = await self.engine.submit_proposal(request)
        return guest_api_pb2.SubmitProposalResponse(
            accepted=accepted,
            message="Accepted" if accepted else "Queued",
            proposal_id=request.proposal_id,
        )

    async def Subscribe(
        self, request: guest_api_pb2.SubscribeRequest, context: grpc.aio.ServicerContext
    ) -> AsyncIterator[core_pb2.TickState]:
        # FIX: Validate session token from metadata
        metadata = dict(context.invocation_metadata())
        session_token = metadata.get("session_token", "")

        if not session_token:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Authentication required: session_token metadata missing",
            )

        # Validate session token
        if session_token not in self.sessions:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Authentication failed: invalid session token",
            )

        # Verify that the session token belongs to the session_id in request
        if session_token != request.session_id:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Authentication failed: session token does not match session_id",
            )

        # For now, yield one dummy tick state to verify the stream works
        yield core_pb2.TickState(tick_number=self.engine.current_tick)

    async def Disconnect(
        self,
        request: guest_api_pb2.DisconnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> guest_api_pb2.DisconnectResponse:
        if request.session_id in self.sessions:
            agent_id = self.sessions.pop(request.session_id)
            self.engine.unregister_actor(agent_id)
            logger.info(f"Agent {agent_id} disconnected: {request.reason}")
            return guest_api_pb2.DisconnectResponse(success=True)
        return guest_api_pb2.DisconnectResponse(success=False)
