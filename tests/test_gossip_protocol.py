"""
Tests for Tsukuyomi Brain Gossip Protocol Module

Run with: python -m pytest tests/test_gossip_protocol.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.brain.GossipProtocol import GossipProtocol


class TestGossipProtocol:
    @pytest.fixture
    def gossip(self):
        """Create a gossip protocol instance."""
        return GossipProtocol(
            base_leakage_probability=0.1,
            proximity_multiplier=2.0,
            accuracy_decay=0.1,
            max_propagation_depth=5
        )

    def test_create_gossip(self, gossip):
        """Test creating gossip protocol."""
        assert gossip is not None

    def test_register_deliberation(self, gossip):
        """Test registering a deliberation event."""
        gossip.register_deliberation(
            actor_id="agent-1",
            thought="Should I trade with Marcus?",
            action="MOVE to market",
            tick=100
        )

    def test_register_deliberation_with_context(self, gossip):
        """Test registering with world state context."""
        gossip.register_deliberation(
            actor_id="agent-1",
            thought="Angry about trade",
            action="EMOTE angry",
            tick=100,
            world_state_context={"location": "market", "tension": 0.8}
        )

    def test_get_gossip_for_agent(self, gossip):
        """Test getting gossip for an agent."""
        gossip.register_deliberation("agent-1", "Thought", "Action", 100)
        result = gossip.get_gossip_for_agent("agent-2")
        assert result is not None

    def test_get_gossip_summary_for_agent(self, gossip):
        """Test getting gossip summary."""
        gossip.register_deliberation("agent-1", "Secret thought", "Action", 100)
        summary = gossip.get_gossip_summary_for_agent("agent-2")
        assert summary is not None

    def test_get_statistics(self, gossip):
        """Test getting gossip statistics."""
        stats = gossip.get_statistics()
        assert isinstance(stats, dict)

    def test_prune_history(self, gossip):
        """Test pruning history."""
        gossip.register_deliberation("agent-1", "Thought", "Action", 100)
        gossip.prune_history(current_tick=200)
        # Should not crash

    def test_export_events(self, gossip):
        """Test exporting events."""
        gossip.register_deliberation("agent-1", "Thought", "Action", 100)
        events = gossip.export_events()
        # May return string or list
        assert events is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])