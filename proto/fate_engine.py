"""
TSUKUYOMI Fate Engine - Phase 1 Prototype
==========================================

Implements the Logical Tick Loop with 20 TPS, handling:
- State Broadcast
- Proposal Window
- Fate Resolution
- System 1 Reflex Integration

The Fate Engine is the authoritative core of the simulation.
"""

import asyncio
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Awaitable
from enum import Enum
import logging
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FateEngine")

# ============================================================================
# Data Structures
# ============================================================================

class ActionType(Enum):
    """Valid action types for proposals."""
    MOVE = "move"
    INTERACT = "interact"
    IDLE = "idle"
    EMOTE = "emote"


@dataclass
class Proposal:
    """A proposal from an actor to change the world state."""
    actor_id: uuid.UUID
    action: ActionType
    parameters: Dict
    timestamp: float
    proposal_id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    def to_dict(self) -> Dict:
        """Convert proposal to dictionary for serialization."""
        return {
            "proposal_id": str(self.proposal_id),
            "actor_id": str(self.actor_id),
            "action": self.action.value,
            "parameters": self.parameters,
            "timestamp": self.timestamp
        }


@dataclass
class Resolution:
    """The result of fate resolution for a proposal."""
    proposal_id: uuid.UUID
    actor_id: uuid.UUID
    success: bool
    outcome: Dict
    reason: Optional[str] = None
    modified_action: Optional[Dict] = None


@dataclass
class TickState:
    """The state snapshot for a single tick."""
    tick_number: int
    timestamp: float
    world_state: Dict
    pending_proposals: List[Proposal]
    resolutions: List[Resolution]


# ============================================================================
# Fate Engine Core
# ============================================================================

class FateEngine:
    """
    The core authority of the simulation.
    
    Implements a deterministic tick loop at 20 TPS that:
    1. Broadcasts current state
    2. Opens a proposal window
    3. Resolves proposals and updates state
    4. Integrates with System 1 reflexes
    """
    
    def __init__(
        self,
        tick_rate: int = 20,
        proposal_window_ms: int = 25,  # Time window to accept proposals per tick
        seed: Optional[int] = None
    ):
        self.tick_rate = tick_rate
        self.tick_duration = 1.0 / tick_rate
        self.proposal_window_ms = proposal_window_ms
        
        # Determinism setup
        self.seed = seed if seed is not None else int(time.time())
        self.rng = random.Random(self.seed)
        
        # Tick state
        self.current_tick = 0
        self.running = False
        self.tick_history: List[TickState] = []
        
        # Proposal management
        self.proposal_queue: List[Proposal] = []
        self.current_window_proposals: List[Proposal] = []
        self.proposal_buffer_lock = asyncio.Lock()
        
        # World state (mock environment)
        self.world_state: Dict = {
            "actors": {},
            "locations": {
                "market_square": {"x": 0, "y": 0},
                "tavern": {"x": 10, "y": 5},
                "inn": {"x": 5, "y": 20},
                "well": {"x": 10, "y": 10}
            },
            "global_events": []
        }
        
        # Resolution history for feedback (2-tick delay)
        self.resolution_buffer: Dict[int, List[Resolution]] = defaultdict(list)
        
        # Phase hooks
        self.pre_broadcast_hooks: List[Callable[[int], Awaitable[None]]] = []
        self.post_resolution_hooks: List[Callable[[int, List[Resolution]], Awaitable[None]]] = []
        
        # System 1 reflex layer (to be attached)
        self.reflex_layer: Optional[object] = None
        
        logger.info(f"Fate Engine initialized with seed={self.seed}, tick_rate={self.tick_rate} TPS")

    # -------------------------------------------------------------------------
    # Proposal Management
    # -------------------------------------------------------------------------
    
    async def submit_proposal(self, proposal: Proposal) -> bool:
        """
        Submit a proposal to be considered in the current or next tick window.
        
        Returns True if proposal was accepted into current window,
        False if queued for next tick.
        """
        async with self.proposal_buffer_lock:
            proposal.timestamp = time.time()
            
            # Check if we're still in the proposal window for current tick
            # For simplicity, we accept proposals continuously and batch them per tick
            self.proposal_queue.append(proposal)
            
            logger.debug(f"Proposal received: {proposal.proposal_id} from {proposal.actor_id}")
            return True
    
    async def flush_proposals(self) -> List[Proposal]:
        """Get all pending proposals and clear the queue."""
        async with self.proposal_buffer_lock:
            proposals = self.proposal_queue.copy()
            self.proposal_queue.clear()
            return proposals
    
    # -------------------------------------------------------------------------
    # Core Tick Phases
    # -------------------------------------------------------------------------
    
    async def _phase_state_broadcast(self, tick: int):
        """
        Phase 1: State Broadcast
        
        Broadcast the current world state to all observers.
        This includes: tick number, actor states, location data.
        """
        # Execute pre-broadcast hooks
        for hook in self.pre_broadcast_hooks:
            try:
                await hook(tick)
            except Exception as e:
                logger.error(f"Pre-broadcast hook error at tick {tick}: {e}", exc_info=True)
        
        # Broadcast tick info
        logger.info(f"=== Tick [{tick}] ===")
        
        # Broadcast actor states (sample for demo)
        active_actors = list(self.world_state["actors"].values())[:5]
        for actor in active_actors:
            logger.debug(f"  Actor {actor['name']}: pos={actor['position']}, state={actor['state']}")
        
        # Broadcast pending proposal count
        pending = len(self.proposal_queue)
        logger.debug(f"  Pending proposals: {pending}")
    
    async def _phase_proposal_window(self, tick: int):
        """
        Phase 2: Proposal Window
        
        Open a small time window to receive actor proposals.
        For Phase 1, we simply collect proposals that have accumulated.
        """
        # Collect proposals for this tick
        proposals = await self.flush_proposals()
        self.current_window_proposals = proposals
        
        logger.debug(f"  Proposal window collected {len(proposals)} proposals")
        
        # Generate reflex proposals if reflex layer is attached
        if self.reflex_layer:
            reflex_proposals = await self._generate_reflex_proposals(tick)
            self.current_window_proposals.extend(reflex_proposals)
            logger.debug(f"  Generated {len(reflex_proposals)} reflex proposals")
    
    async def _phase_fate_resolution(self, tick: int) -> List[Resolution]:
        """
        Phase 3: Fate Resolution
        
        Resolve all proposals and update world state.
        This is where the "Fate" of each proposal is determined.
        
        Returns list of resolutions for feedback.
        """
        resolutions = []
        
        # Sort proposals by timestamp for deterministic processing
        sorted_proposals = sorted(
            self.current_window_proposals,
            key=lambda p: p.timestamp
        )
        
        for proposal in sorted_proposals:
            resolution = await self._resolve_proposal(proposal)
            resolutions.append(resolution)
            
            # If successful, apply the state change
            if resolution.success:
                await self._apply_outcome(resolution)
            
            logger.debug(
                f"  Resolved {proposal.action.value} for {proposal.actor_id}: "
                f"{'SUCCESS' if resolution.success else 'FAILED'}"
            )
        
        # Store resolutions for 2-tick feedback delay
        feedback_tick = tick + 2
        self.resolution_buffer[feedback_tick] = resolutions
        
        # Execute post-resolution hooks
        for hook in self.post_resolution_hooks:
            try:
                await hook(tick, resolutions)
            except Exception as e:
                logger.error(f"Post-resolution hook error at tick {tick}: {e}", exc_info=True)
        
        return resolutions
    
    # -------------------------------------------------------------------------
    # Resolution Logic
    # -------------------------------------------------------------------------
    
    async def _resolve_proposal(self, proposal: Proposal) -> Resolution:
        """
        Determine the fate of a proposal.
        
        For Phase 1, we implement basic movement and interaction resolution.
        Future phases will include physics checks, conflict resolution, and
        skill-based outcomes.
        """
        actor_id = proposal.actor_id
        
        # Check if actor exists
        if str(actor_id) not in self.world_state["actors"]:
            return Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=False,
                outcome={},
                reason="Actor not found in world state"
            )
        
        actor = self.world_state["actors"][str(actor_id)]
        
        # Resolve based on action type
        if proposal.action == ActionType.MOVE:
            return await self._resolve_move(proposal, actor)
        elif proposal.action == ActionType.INTERACT:
            return await self._resolve_interact(proposal, actor)
        elif proposal.action == ActionType.IDLE:
            return Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=True,
                outcome={"action": "idle", "duration": proposal.parameters.get("duration", 1)}
            )
        elif proposal.action == ActionType.EMOTE:
            return Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=True,
                outcome={
                    "action": "emote",
                    "emote_type": proposal.parameters.get("type", "wave")
                }
            )
        else:
            return Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=actor_id,
                success=False,
                outcome={},
                reason=f"Unknown action type: {proposal.action}"
            )
    
    async def _resolve_move(self, proposal: Proposal, actor: Dict) -> Resolution:
        """Resolve a movement proposal."""
        destination = proposal.parameters.get("destination")
        
        # Check if destination exists
        if not destination or destination not in self.world_state["locations"]:
            return Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=proposal.actor_id,
                success=False,
                outcome={},
                reason="Invalid or unknown destination"
            )
        
        dest_pos = self.world_state["locations"][destination]
        current_pos = actor["position"]
        
        # Calculate distance (for Phase 1, movement is instant)
        distance = (
            (dest_pos["x"] - current_pos["x"])**2 +
            (dest_pos["y"] - current_pos["y"])**2
        )**0.5
        
        # For Phase 1, we allow unlimited movement
        # Future: check stamina, path obstacles, etc.
        
        return Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=True,
            outcome={
                "action": "move",
                "from": current_pos,
                "to": dest_pos,
                "destination": destination,
                "distance": distance
            }
        )
    
    async def _resolve_interact(self, proposal: Proposal, actor: Dict) -> Resolution:
        """Resolve an interaction proposal."""
        target = proposal.parameters.get("target")
        interaction_type = proposal.parameters.get("type", "generic")
        
        # For Phase 1, interactions always succeed
        # Future: check relationship, skills, cooldowns, etc.
        
        return Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=True,
            outcome={
                "action": "interact",
                "type": interaction_type,
                "target": target
            }
        )
    
    async def _apply_outcome(self, resolution: Resolution):
        """Apply a successful resolution outcome to the world state."""
        actor_id = str(resolution.actor_id)
        
        if actor_id not in self.world_state["actors"]:
            return
        
        actor = self.world_state["actors"][actor_id]
        outcome = resolution.outcome
        
        if outcome.get("action") == "move":
            # Update actor position
            actor["position"] = outcome["to"]
            actor["current_location"] = outcome["destination"]
            actor["state"] = "IDLE"  # Reset to idle after move
        
        elif outcome.get("action") == "interact":
            # Record interaction
            if "interactions" not in actor:
                actor["interactions"] = []
            actor["interactions"].append({
                "type": outcome["type"],
                "target": outcome["target"],
                "tick": self.current_tick
            })
    
    # -------------------------------------------------------------------------
    # Reflex Integration
    # -------------------------------------------------------------------------
    
    async def _generate_reflex_proposals(self, tick: int) -> List[Proposal]:
        """
        Generate proposals from the System 1 reflex layer.
        
        This allows NPCs to automatically propose actions based on
        their needs and environmental stimuli.
        """
        if not self.reflex_layer:
            return []
        
        # Get world from reflex layer if it has agents
        try:
            world = getattr(self.reflex_layer, 'world', None)
            if not world:
                return []
            
            proposals = []
            
            # Generate proposals for each agent based on their reflex state
            for agent_id, agent in world.agents.items():
                if agent.state.name == "WALKING" and agent.target_destination:
                    # Propose movement to target
                    proposals.append(Proposal(
                        actor_id=agent.id,
                        action=ActionType.MOVE,
                        parameters={
                            "destination": self._find_location_name(agent.target_destination)
                        },
                        timestamp=time.time()
                    ))
            
            return proposals
        except Exception as e:
            logger.error(f"Error generating reflex proposals: {e}", exc_info=True)
            return []
    
    def _find_location_name(self, position) -> Optional[str]:
        """Find the location name closest to a position."""
        for name, loc in self.world_state["locations"].items():
            if loc["x"] == position[0] and loc["y"] == position[1]:
                return name
        return None
    
    def attach_reflex_layer(self, reflex_layer):
        """Attach a System 1 reflex layer to the fate engine."""
        self.reflex_layer = reflex_layer
        logger.info("Reflex layer attached to Fate Engine")
    
    # -------------------------------------------------------------------------
    # Tick Loop
    # -------------------------------------------------------------------------
    
    async def run(self):
        """
        Main tick loop running at 20 TPS.
        
        Each tick executes:
        1. State Broadcast
        2. Proposal Window
        3. Fate Resolution
        """
        self.running = True
        logger.info(f"Starting Fate Engine at {self.tick_rate} TPS")
        
        while self.running:
            start_time = time.perf_counter()
            
            # Phase 1: State Broadcast
            await self._phase_state_broadcast(self.current_tick)
            
            # Phase 2: Proposal Window
            await self._phase_proposal_window(self.current_tick)
            
            # Phase 3: Fate Resolution
            resolutions = await self._phase_fate_resolution(self.current_tick)
            
            # Store tick state for debugging/history
            tick_state = TickState(
                tick_number=self.current_tick,
                timestamp=time.time(),
                world_state=self._get_world_snapshot(),
                pending_proposals=self.current_window_proposals.copy(),
                resolutions=resolutions
            )
            self.tick_history.append(tick_state)
            
            # Keep history manageable
            if len(self.tick_history) > 1000:
                self.tick_history.pop(0)
            
            # Advance tick
            self.current_tick += 1
            
            # Maintain tick rate
            elapsed = time.perf_counter() - start_time
            sleep_time = self.tick_duration - elapsed
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                if self.current_tick % 100 == 0:
                    logger.warning(
                        f"Tick {self.current_tick - 1} lagged by {abs(sleep_time):.4f}s"
                    )
    
    def stop(self):
        """Stop the tick loop."""
        self.running = False
        logger.info(f"Fate Engine stopped at tick {self.current_tick}")
    
    # -------------------------------------------------------------------------
    # Actor Management
    # -------------------------------------------------------------------------
    
    def register_actor(self, actor_id: uuid.UUID, name: str, position: tuple = (0, 0)):
        """Register an actor in the world state."""
        self.world_state["actors"][str(actor_id)] = {
            "id": str(actor_id),
            "name": name,
            "position": {"x": position[0], "y": position[1]},
            "state": "IDLE",
            "current_location": None,
            "interactions": []
        }
        logger.info(f"Actor registered: {name} ({actor_id})")
    
    def unregister_actor(self, actor_id: uuid.UUID):
        """Remove an actor from the world state."""
        if str(actor_id) in self.world_state["actors"]:
            name = self.world_state["actors"][str(actor_id)]["name"]
            del self.world_state["actors"][str(actor_id)]
            logger.info(f"Actor unregistered: {name} ({actor_id})")
    
    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    
    def _get_world_snapshot(self) -> Dict:
        """Get a snapshot of the current world state."""
        return {
            "tick": self.current_tick,
            "actors": {
                aid: {
                    "name": a["name"],
                    "position": a["position"],
                    "state": a["state"],
                    "location": a.get("current_location")
                }
                for aid, a in self.world_state["actors"].items()
            },
            "locations": self.world_state["locations"].copy()
        }
    
    def get_pending_feedback(self, tick: int) -> List[Resolution]:
        """Get feedback (resolutions) available for a given tick."""
        return self.resolution_buffer.get(tick, [])
    
    def get_tick_state(self, tick: int) -> Optional[TickState]:
        """Get the state of a specific tick from history."""
        for state in self.tick_history:
            if state.tick_number == tick:
                return state
        return None


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_proposal(
    actor_id: uuid.UUID,
    action: str,
    parameters: Dict
) -> Proposal:
    """Create a proposal with automatic timestamp."""
    return Proposal(
        actor_id=actor_id,
        action=ActionType(action.lower()),
        parameters=parameters,
        timestamp=time.time()
    )


# ============================================================================
# Demo / Test Runner
# ============================================================================

async def demo_fate_engine():
    """Run a quick demonstration of the Fate Engine."""
    # Initialize fate engine with deterministic seed
    engine = FateEngine(tick_rate=20, seed=42)
    
    # Register some actors
    alice = uuid.uuid4()
    bob = uuid.uuid4()
    
    engine.register_actor(alice, "Alice", position=(0, 0))
    engine.register_actor(bob, "Bob", position=(5, 5))
    
    # Submit some initial proposals
    await engine.submit_proposal(
        await create_proposal(
            actor_id=alice,
            action="MOVE",
            parameters={"destination": "tavern"}
        )
    )
    
    await engine.submit_proposal(
        await create_proposal(
            actor_id=bob,
            action="EMOTE",
            parameters={"type": "wave"}
        )
    )
    
    # Run for a limited time
    async def limited_run():
        await asyncio.sleep(2)  # Run for 2 seconds (~40 ticks)
        engine.stop()
    
    # Start both the engine and the limiter
    await asyncio.gather(engine.run(), limited_run())
    
    # Print summary
    print(f"\nDemo completed: {engine.current_tick} ticks executed")
    print(f"Total proposals processed: {len(engine.tick_history)}")
    
    # Show final state
    final_state = engine._get_world_snapshot()
    print("\nFinal World State:")
    for aid, actor in final_state["actors"].items():
        print(f"  {actor['name']}: pos={actor['position']}, loc={actor['location']}")


if __name__ == "__main__":
    asyncio.run(demo_fate_engine())
