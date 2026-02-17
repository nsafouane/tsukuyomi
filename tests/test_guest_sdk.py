"""
Tests for Tsukuyomi Guest SDK Module

Run with: python -m pytest tests/test_guest_sdk.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.guest_sdk import GuestAgent


class TestGuestAgent:
    def test_create_agent(self):
        """Test creating a guest agent."""
        agent = GuestAgent(
            agent_id="test-agent-001",
            agent_name="TestAgent",
            server_addr="localhost:50051"
        )
        assert agent.agent_id == "test-agent-001"
        assert agent.agent_name == "TestAgent"
        assert agent.is_connected == False

    def test_agent_default_server(self):
        """Test agent with default server address."""
        agent = GuestAgent(
            agent_id="test-002",
            agent_name="Agent2"
        )
        assert agent.server_addr == "localhost:50051"

    def test_agent_not_connected_initially(self):
        """Test that agent is not connected initially."""
        agent = GuestAgent(
            agent_id="test-003",
            agent_name="Agent3"
        )
        assert agent.is_connected == False
        assert agent.session_id is None

    def test_agent_custom_server(self):
        """Test agent with custom server."""
        agent = GuestAgent(
            agent_id="test-004",
            agent_name="Agent4",
            server_addr="custom.server:8080"
        )
        assert agent.server_addr == "custom.server:8080"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])