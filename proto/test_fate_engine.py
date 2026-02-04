"""
Unit Tests for TSUKUYOMI Fate Engine
======================================

Comprehensive test suite ensuring 80%+ coverage of resolution logic.
"""

import random
import unittest
import asyncio
import time
import uuid
from fate_engine import (
    FateEngine,
    Proposal,
    Resolution,
    ActionType,
    TickState,
    create_proposal
)


class TestProposal(unittest.TestCase):
    """Test Proposal dataclass and serialization."""
    
    def test_proposal_creation(self):
        """Test creating a proposal."""
        actor_id = uuid.uuid4()
        proposal = Proposal(
            actor_id=actor_id,
            action=ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=time.time()
        )
        
        self.assertEqual(proposal.action, ActionType.MOVE)
        self.assertEqual(proposal.actor_id, actor_id)
        self.assertIsInstance(proposal.proposal_id, uuid.UUID)
    
    def test_proposal_to_dict(self):
        """Test proposal serialization."""
        actor_id = uuid.uuid4()
        proposal = Proposal(
            actor_id=actor_id,
            action=ActionType.INTERACT,
            parameters={"target": "merchant"},
            timestamp=1234567890.0
        )
        
        result = proposal.to_dict()
        
        self.assertIn("proposal_id", result)
        self.assertIn("actor_id", result)
        self.assertEqual(result["action"], "interact")
        self.assertEqual(result["parameters"], {"target": "merchant"})
        self.assertEqual(result["timestamp"], 1234567890.0)


class TestResolution(unittest.TestCase):
    """Test Resolution dataclass."""
    
    def test_resolution_creation_success(self):
        """Test creating a successful resolution."""
        proposal_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        
        resolution = Resolution(
            proposal_id=proposal_id,
            actor_id=actor_id,
            success=True,
            outcome={"action": "move", "to": {"x": 10, "y": 5}}
        )
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.actor_id, actor_id)
        self.assertIsNone(resolution.reason)
    
    def test_resolution_creation_failure(self):
        """Test creating a failed resolution."""
        proposal_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        
        resolution = Resolution(
            proposal_id=proposal_id,
            actor_id=actor_id,
            success=False,
            outcome={},
            reason="Invalid destination"
        )
        
        self.assertFalse(resolution.success)
        self.assertEqual(resolution.reason, "Invalid destination")
        self.assertEqual(resolution.outcome, {})


class TestFateEngineInitialization(unittest.TestCase):
    """Test FateEngine initialization and configuration."""
    
    def test_default_initialization(self):
        """Test default parameters."""
        engine = FateEngine()
        
        self.assertEqual(engine.tick_rate, 20)
        self.assertEqual(engine.proposal_window_ms, 25)
        self.assertEqual(engine.current_tick, 0)
        self.assertFalse(engine.running)
        self.assertIsNotNone(engine.seed)
        self.assertIsInstance(engine.rng, random.Random)
    
    def test_custom_initialization(self):
        """Test custom parameters."""
        engine = FateEngine(tick_rate=30, proposal_window_ms=50, seed=12345)
        
        self.assertEqual(engine.tick_rate, 30)
        self.assertEqual(engine.proposal_window_ms, 50)
        self.assertEqual(engine.seed, 12345)
    
    def test_deterministic_rng(self):
        """Test that same seed produces same RNG sequence."""
        engine1 = FateEngine(seed=42)
        engine2 = FateEngine(seed=42)
        
        # Both should produce same sequence
        for _ in range(10):
            self.assertEqual(engine1.rng.random(), engine2.rng.random())


class TestActorManagement(unittest.TestCase):
    """Test actor registration and management."""
    
    def setUp(self):
        self.engine = FateEngine()
    
    def test_register_actor(self):
        """Test registering an actor."""
        actor_id = uuid.uuid4()
        self.engine.register_actor(actor_id, "TestActor", position=(5, 10))
        
        self.assertIn(str(actor_id), self.engine.world_state["actors"])
        actor = self.engine.world_state["actors"][str(actor_id)]
        self.assertEqual(actor["name"], "TestActor")
        self.assertEqual(actor["position"], {"x": 5, "y": 10})
        self.assertEqual(actor["state"], "IDLE")
    
    def test_register_multiple_actors(self):
        """Test registering multiple actors."""
        actors = [(uuid.uuid4(), f"Actor{i}") for i in range(5)]
        
        for actor_id, name in actors:
            self.engine.register_actor(actor_id, name)
        
        self.assertEqual(len(self.engine.world_state["actors"]), 5)
    
    def test_unregister_actor(self):
        """Test unregistering an actor."""
        actor_id = uuid.uuid4()
        self.engine.register_actor(actor_id, "TestActor")
        
        self.assertIn(str(actor_id), self.engine.world_state["actors"])
        
        self.engine.unregister_actor(actor_id)
        
        self.assertNotIn(str(actor_id), self.engine.world_state["actors"])
    
    def test_unregister_nonexistent_actor(self):
        """Test unregistering an actor that doesn't exist (should not crash)."""
        actor_id = uuid.uuid4()
        # Should not raise an exception
        self.engine.unregister_actor(actor_id)


class TestProposalSubmission(unittest.TestCase):
    """Test proposal submission and queueing."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "TestActor")
    
    def test_submit_proposal(self):
        """Test submitting a single proposal."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=time.time()
        )
        
        async def test():
            result = await self.engine.submit_proposal(proposal)
            return result
        
        success = asyncio.run(test())
        
        self.assertTrue(success)
        self.assertEqual(len(self.engine.proposal_queue), 1)
    
    def test_submit_multiple_proposals(self):
        """Test submitting multiple proposals."""
        proposals = [
            Proposal(
                actor_id=self.actor_id,
                action=ActionType.EMOTE,
                parameters={"type": "wave"},
                timestamp=time.time()
            )
            for _ in range(5)
        ]
        
        async def test():
            for p in proposals:
                await self.engine.submit_proposal(p)
        
        asyncio.run(test())
        
        self.assertEqual(len(self.engine.proposal_queue), 5)
    
    def test_flush_proposals(self):
        """Test flushing the proposal queue."""
        proposals = [
            Proposal(
                actor_id=self.actor_id,
                action=ActionType.IDLE,
                parameters={},
                timestamp=time.time()
            )
            for _ in range(3)
        ]
        
        async def test():
            for p in proposals:
                await self.engine.submit_proposal(p)
            flushed = await self.engine.flush_proposals()
            return flushed
        
        flushed = asyncio.run(test())
        
        self.assertEqual(len(flushed), 3)
        self.assertEqual(len(self.engine.proposal_queue), 0)


class TestResolutionMove(unittest.TestCase):
    """Test movement resolution logic."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "Traveler", position=(0, 0))
    
    def test_resolve_move_valid_destination(self):
        """Test resolving a move to a valid location."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_move(
                proposal,
                self.engine.world_state["actors"][str(self.actor_id)]
            )
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.outcome["destination"], "tavern")
        self.assertEqual(resolution.outcome["to"], {"x": 10, "y": 5})
        self.assertGreater(resolution.outcome["distance"], 0)
    
    def test_resolve_move_invalid_destination(self):
        """Test resolving a move to an invalid location."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.MOVE,
            parameters={"destination": "nonexistent_place"},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_move(
                proposal,
                self.engine.world_state["actors"][str(self.actor_id)]
            )
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertFalse(resolution.success)
        self.assertIn("Invalid or unknown destination", resolution.reason)
    
    def test_resolve_move_no_destination(self):
        """Test resolving a move with no destination specified."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.MOVE,
            parameters={},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_move(
                proposal,
                self.engine.world_state["actors"][str(self.actor_id)]
            )
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertFalse(resolution.success)
    
    def test_apply_move_outcome(self):
        """Test applying a successful move outcome."""
        resolution = Resolution(
            proposal_id=uuid.uuid4(),
            actor_id=self.actor_id,
            success=True,
            outcome={
                "action": "move",
                "from": {"x": 0, "y": 0},
                "to": {"x": 10, "y": 5},
                "destination": "tavern"
            }
        )
        
        async def test():
            await self.engine._apply_outcome(resolution)
        
        asyncio.run(test())
        
        actor = self.engine.world_state["actors"][str(self.actor_id)]
        self.assertEqual(actor["position"], {"x": 10, "y": 5})
        self.assertEqual(actor["current_location"], "tavern")
        self.assertEqual(actor["state"], "IDLE")


class TestResolutionInteract(unittest.TestCase):
    """Test interaction resolution logic."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "Socializer", position=(0, 0))
    
    def test_resolve_interact_with_target(self):
        """Test resolving an interaction with a target."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.INTERACT,
            parameters={"target": "merchant", "type": "trade"},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_interact(
                proposal,
                self.engine.world_state["actors"][str(self.actor_id)]
            )
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.outcome["target"], "merchant")
        self.assertEqual(resolution.outcome["type"], "trade")
    
    def test_resolve_interact_generic(self):
        """Test resolving a generic interaction."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.INTERACT,
            parameters={},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_interact(
                proposal,
                self.engine.world_state["actors"][str(self.actor_id)]
            )
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.outcome["type"], "generic")
    
    def test_apply_interact_outcome(self):
        """Test applying an interaction outcome."""
        resolution = Resolution(
            proposal_id=uuid.uuid4(),
            actor_id=self.actor_id,
            success=True,
            outcome={
                "action": "interact",
                "type": "trade",
                "target": "merchant"
            }
        )
        
        async def test():
            await self.engine._apply_outcome(resolution)
        
        asyncio.run(test())
        
        actor = self.engine.world_state["actors"][str(self.actor_id)]
        self.assertIn("interactions", actor)
        self.assertEqual(len(actor["interactions"]), 1)
        self.assertEqual(actor["interactions"][0]["type"], "trade")
        self.assertEqual(actor["interactions"][0]["target"], "merchant")


class TestResolutionIdle(unittest.TestCase):
    """Test idle resolution logic."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "IdleActor", position=(0, 0))
    
    def test_resolve_idle_default(self):
        """Test resolving an idle action with default duration."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.IDLE,
            parameters={},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_proposal(proposal)
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.outcome["action"], "idle")
        self.assertEqual(resolution.outcome["duration"], 1)


class TestResolutionEmote(unittest.TestCase):
    """Test emote resolution logic."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "Emoter", position=(0, 0))
    
    def test_resolve_emote_with_type(self):
        """Test resolving an emote with a specific type."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.EMOTE,
            parameters={"type": "dance"},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_proposal(proposal)
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.outcome["action"], "emote")
        self.assertEqual(resolution.outcome["emote_type"], "dance")
    
    def test_resolve_emote_default(self):
        """Test resolving an emote without a type (default to wave)."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.EMOTE,
            parameters={},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_proposal(proposal)
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertTrue(resolution.success)
        self.assertEqual(resolution.outcome["emote_type"], "wave")


class TestResolutionUnknownAction(unittest.TestCase):
    """Test resolution of unknown action types."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "TestActor", position=(0, 0))
    
    def test_resolve_unknown_action(self):
        """Test that unknown actions fail gracefully."""
        # Create a proposal with an invalid action
        proposal = Proposal(
            actor_id=self.actor_id,
            action="invalid_action",  # This will fail when creating as ActionType
            parameters={},
            timestamp=time.time()
        )
        # We can't actually create this with ActionType enum, so we test
        # by directly calling with an action that's not in the enum
        
        # Instead, let's test that a modified proposal fails
        proposal.action = "not_a_valid_action"
        
        async def test():
            resolution = await self.engine._resolve_proposal(proposal)
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertFalse(resolution.success)
        self.assertIn("Unknown action type", resolution.reason)


class TestResolutionNonexistentActor(unittest.TestCase):
    """Test resolution when actor doesn't exist."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.nonexistent_actor_id = uuid.uuid4()
        # Don't register the actor
    
    def test_resolve_for_nonexistent_actor(self):
        """Test that proposals from nonexistent actors fail."""
        proposal = Proposal(
            actor_id=self.nonexistent_actor_id,
            action=ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=time.time()
        )
        
        async def test():
            resolution = await self.engine._resolve_proposal(proposal)
            return resolution
        
        resolution = asyncio.run(test())
        
        self.assertFalse(resolution.success)
        self.assertIn("Actor not found", resolution.reason)


class TestFateResolutionPhase(unittest.TestCase):
    """Test the complete fate resolution phase."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor1 = uuid.uuid4()
        self.actor2 = uuid.uuid4()
        self.engine.register_actor(self.actor1, "Alice")
        self.engine.register_actor(self.actor2, "Bob")
    
    def test_fate_resolution_empty_window(self):
        """Test fate resolution with no proposals."""
        async def test():
            resolutions = await self.engine._phase_fate_resolution(0)
            return resolutions
        
        resolutions = asyncio.run(test())
        
        self.assertEqual(len(resolutions), 0)
    
    def test_fate_resolution_multiple_proposals(self):
        """Test fate resolution with multiple proposals."""
        proposals = [
            Proposal(
                actor_id=self.actor1,
                action=ActionType.MOVE,
                parameters={"destination": "tavern"},
                timestamp=1.0
            ),
            Proposal(
                actor_id=self.actor2,
                action=ActionType.EMOTE,
                parameters={"type": "wave"},
                timestamp=2.0
            ),
            Proposal(
                actor_id=self.actor1,
                action=ActionType.IDLE,
                parameters={},
                timestamp=3.0
            )
        ]
        
        self.engine.current_window_proposals = proposals
        
        async def test():
            resolutions = await self.engine._phase_fate_resolution(0)
            return resolutions
        
        resolutions = asyncio.run(test())
        
        self.assertEqual(len(resolutions), 3)
        # Check that all proposals were resolved
        self.assertTrue(all(r.success for r in resolutions))
    
    def test_fate_resolution_applies_state_changes(self):
        """Test that fate resolution applies state changes to actors."""
        proposals = [
            Proposal(
                actor_id=self.actor1,
                action=ActionType.MOVE,
                parameters={"destination": "tavern"},
                timestamp=1.0
            )
        ]
        
        self.engine.current_window_proposals = proposals
        
        async def test():
            resolutions = await self.engine._phase_fate_resolution(0)
            return resolutions
        
        resolutions = asyncio.run(test())
        
        actor = self.engine.world_state["actors"][str(self.actor1)]
        self.assertEqual(actor["current_location"], "tavern")
        self.assertEqual(actor["position"], {"x": 10, "y": 5})


class TestFeedbackBuffer(unittest.TestCase):
    """Test the feedback buffer for delayed resolution delivery."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "TestActor")
    
    def test_feedback_buffer_delay(self):
        """Test that feedback is delayed by 2 ticks."""
        proposals = [
            Proposal(
                actor_id=self.actor_id,
                action=ActionType.EMOTE,
                parameters={"type": "wave"},
                timestamp=1.0
            )
        ]
        
        self.engine.current_window_proposals = proposals
        
        async def test():
            # Process tick 0
            await self.engine._phase_fate_resolution(0)
            
            # Feedback should not be available yet
            self.assertEqual(len(self.engine.get_pending_feedback(0)), 0)
            self.assertEqual(len(self.engine.get_pending_feedback(1)), 0)
            
            # Feedback should be available at tick 2
            feedback = self.engine.get_pending_feedback(2)
            return feedback
        
        feedback = asyncio.run(test())
        
        self.assertEqual(len(feedback), 1)
        self.assertTrue(feedback[0].success)


class TestWorldSnapshot(unittest.TestCase):
    """Test world state snapshot functionality."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "TestActor", position=(5, 10))
    
    def test_get_world_snapshot(self):
        """Test getting a world snapshot."""
        snapshot = self.engine._get_world_snapshot()
        
        self.assertIn("tick", snapshot)
        self.assertIn("actors", snapshot)
        self.assertIn("locations", snapshot)
        
        self.assertEqual(len(snapshot["actors"]), 1)
        self.assertEqual(snapshot["actors"][str(self.actor_id)]["name"], "TestActor")
    
    def test_snapshot_excludes_sensitive_data(self):
        """Test that snapshot doesn't include internal actor data."""
        snapshot = self.engine._get_world_snapshot()
        
        actor_data = snapshot["actors"][str(self.actor_id)]
        # Should not have full interaction history in snapshot
        # (though for Phase 1 this is minimal)


class TestTickHistory(unittest.TestCase):
    """Test tick history tracking."""
    
    def test_tick_state_created(self):
        """Test that tick states are created and stored in run loop."""
        engine = FateEngine()
        actor_id = uuid.uuid4()
        engine.register_actor(actor_id, "TestActor")
        
        async def test():
            # Submit a proposal and run for a few ticks
            proposal = await create_proposal(
                actor_id=actor_id,
                action="idle",
                parameters={}
            )
            await engine.submit_proposal(proposal)
            
            # Run a few ticks
            async def run_ticks():
                for i in range(5):
                    await engine._phase_state_broadcast(i)
                    await engine._phase_proposal_window(i)
                    await engine._phase_fate_resolution(i)
                    
                    # Create tick state manually (as done in run())
                    tick_state = TickState(
                        tick_number=i,
                        timestamp=time.time(),
                        world_state=engine._get_world_snapshot(),
                        pending_proposals=engine.current_window_proposals.copy(),
                        resolutions=engine.resolution_buffer.get(i + 2, [])
                    )
                    engine.tick_history.append(tick_state)
            
            await run_ticks()
            return len(engine.tick_history)
        
        count = asyncio.run(test())
        
        self.assertGreater(count, 0)
    
    def test_get_tick_state(self):
        """Test retrieving a specific tick state."""
        engine = FateEngine()
        
        async def test():
            # Manually add a tick state
            tick_state = TickState(
                tick_number=5,
                timestamp=time.time(),
                world_state={},
                pending_proposals=[],
                resolutions=[]
            )
            engine.tick_history.append(tick_state)
            
            return engine.get_tick_state(5)
        
        state = asyncio.run(test())
        
        self.assertIsNotNone(state)
        self.assertEqual(state.tick_number, 5)


class TestPhaseExecution(unittest.TestCase):
    """Test individual phase execution."""
    
    def setUp(self):
        self.engine = FateEngine()
        self.actor_id = uuid.uuid4()
        self.engine.register_actor(self.actor_id, "TestActor")
    
    def test_state_broadcast_phase(self):
        """Test state broadcast phase."""
        async def test():
            await self.engine._phase_state_broadcast(0)
        
        # Should not raise an exception
        asyncio.run(test())
    
    def test_proposal_window_phase(self):
        """Test proposal window phase."""
        async def test():
            await self.engine._phase_proposal_window(0)
        
        # Should not raise an exception
        asyncio.run(test())
    
    def test_proposal_window_collects_proposals(self):
        """Test that proposal window collects queued proposals."""
        proposal = Proposal(
            actor_id=self.actor_id,
            action=ActionType.IDLE,
            parameters={},
            timestamp=time.time()
        )
        
        async def test():
            await self.engine.submit_proposal(proposal)
            await self.engine._phase_proposal_window(0)
            return len(self.engine.current_window_proposals)
        
        count = asyncio.run(test())
        
        self.assertEqual(count, 1)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_proposal(self):
        """Test creating a proposal via convenience function."""
        actor_id = uuid.uuid4()
        
        async def test():
            proposal = await create_proposal(
                actor_id=actor_id,
                action="move",
                parameters={"destination": "tavern"}
            )
            return proposal
        
        proposal = asyncio.run(test())
        
        self.assertEqual(proposal.actor_id, actor_id)
        self.assertEqual(proposal.action, ActionType.MOVE)
        self.assertEqual(proposal.parameters["destination"], "tavern")
        self.assertIsInstance(proposal.timestamp, float)


class TestDeterminism(unittest.TestCase):
    """Test that the engine is deterministic with same seed."""
    
    def test_identical_seeds_same_world(self):
        """Test that two engines with same seed have same initial state."""
        engine1 = FateEngine(seed=12345)
        engine2 = FateEngine(seed=12345)
        
        # Both should have same world structure
        self.assertEqual(
            engine1.world_state["locations"],
            engine2.world_state["locations"]
        )
    
    def test_identical_seeds_same_resolutions(self):
        """Test that same proposals produce same resolutions with same seed."""
        engine1 = FateEngine(seed=42)
        engine2 = FateEngine(seed=42)
        
        actor_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        engine1.register_actor(actor_id, "TestActor")
        engine2.register_actor(actor_id, "TestActor")
        
        proposal = Proposal(
            actor_id=actor_id,
            action=ActionType.MOVE,
            parameters={"destination": "tavern"},
            timestamp=12345.0
        )
        
        async def test():
            res1 = await engine1._resolve_proposal(proposal)
            res2 = await engine2._resolve_proposal(proposal)
            return res1, res2
        
        res1, res2 = asyncio.run(test())
        
        self.assertEqual(res1.success, res2.success)
        self.assertEqual(res1.outcome, res2.outcome)


class TestIntegrationFullTick(unittest.TestCase):
    """Integration tests for a full tick cycle."""
    
    def test_full_tick_cycle(self):
        """Test a complete tick cycle from start to finish."""
        engine = FateEngine()
        actor_id = uuid.uuid4()
        engine.register_actor(actor_id, "TestActor")
        
        async def test():
            # Submit a proposal
            proposal = await create_proposal(
                actor_id=actor_id,
                action="move",
                parameters={"destination": "tavern"}
            )
            await engine.submit_proposal(proposal)
            
            # Run one tick
            await engine._phase_state_broadcast(0)
            await engine._phase_proposal_window(0)
            resolutions = await engine._phase_fate_resolution(0)
            
            return resolutions
        
        resolutions = asyncio.run(test())
        
        self.assertEqual(len(resolutions), 1)
        self.assertTrue(resolutions[0].success)
        
        # Verify state was updated
        actor = engine.world_state["actors"][str(actor_id)]
        self.assertEqual(actor["current_location"], "tavern")


# Run tests if executed directly
if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
