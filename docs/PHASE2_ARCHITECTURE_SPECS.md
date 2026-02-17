# Tsukuyomi V2 Phase 2: World Dynamics - Detailed Architecture Specs

**Date:** 2026-02-15
**Status:** Technical Specification (Ready for Implementation)
**Version:** 1.0

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Component 1: Spatial Index](#component-1-spatial-index)
3. [Component 2: Proposal Window System](#component-2-proposal-window-system)
4. [Component 3: Affordance System](#component-3-affordance-system)
5. [Component 4: Visual Perception with Raycasting](#component-4-visual-perception-with-raycasting)
6. [Integration Interfaces](#integration-interfaces)
7. [Performance Specifications](#performance-specifications)
8. [Data Structures & API Contracts](#data-structures--api-contracts)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document provides the detailed technical specifications for Phase 2 of Tsukuyomi V2, focusing on **World Dynamics**. The primary objectives are:

1. **Spatial Awareness**: Enable O(log N) spatial queries for efficient multi-agent simulations
2. **Temporal Coordination**: Implement proposal windows for coordinated multi-tick actions
3. **Interaction Semantics**: Formalize affordance-based object interactions
4. **Realistic Perception**: Add line-of-sight and occlusion to visual perception

**Key Performance Targets:**
- Support 100+ agents with <10ms tick latency
- O(log N) complexity for all spatial queries
- <1% overhead for spatial indexing vs linear search baseline
- <50ms perception update time per agent

---

## Component 1: Spatial Index

### 1.1 Overview

The **SpatialIndex** is a spatial partitioning system that provides efficient proximity queries, collision detection, and range-based operations. It serves as the foundation for all spatial interactions in the simulation.

### 1.2 Design Decisions

**Primary Implementation: Grid-Based Spatial Hash**
- **Rationale**: Simple, cache-friendly, predictable performance
- **Cell Size**: 2.0 × 2.0 meters (configurable)
- **World Bounds**: Bounded grid with optional dynamic expansion
- **Collision Granularity**: Bounding box (AABB) with optional radius fallback

**Alternative (Future Phase 3): Quadtree**
- **Rationale**: Better for sparse, uneven distributions
- **Implementation**: Deferred to Phase 3 for optimization phase

### 1.3 Core Interface

```python
class SpatialIndex:
    """
    High-performance spatial partitioning system.
    
    Uses a grid-based spatial hash with O(1) insertion/deletion
    and O(k) query where k = number of cells in query radius.
    """
    
    def __init__(self, cell_size: float = 2.0, world_bounds: Optional[Bounds] = None):
        """
        Args:
            cell_size: Size of each grid cell in meters
            world_bounds: Optional (min_x, min_y, max_x, max_y) bounds
        """
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], List[SpatialEntry]] = defaultdict(list)
        self.object_map: Dict[str, SpatialEntry] = {}  # object_id -> entry
        self.world_bounds = world_bounds
        
    def add(self, obj_id: str, position: Vector2, radius: float = 0.5,
            obj_type: str = "unknown", metadata: Dict = None) -> bool:
        """
        Register an object in the spatial index.
        
        Args:
            obj_id: Unique identifier for the object
            position: 2D position in world space
            radius: Bounding radius for collision detection
            obj_type: Type string for filtering queries
            metadata: Optional metadata dictionary
            
        Returns:
            True if successfully added, False if already exists
            
        Complexity: O(1) amortized
        """
        pass
    
    def remove(self, obj_id: str) -> bool:
        """
        Remove an object from the spatial index.
        
        Args:
            obj_id: Object identifier to remove
            
        Returns:
            True if found and removed, False otherwise
            
        Complexity: O(1) amortized
        """
        pass
    
    def update(self, obj_id: str, new_position: Vector2) -> bool:
        """
        Update an object's position (handles cell migration).
        
        Args:
            obj_id: Object identifier
            new_position: New position in world space
            
        Returns:
            True if updated, False if not found
            
        Complexity: O(1) if within same cell, O(1) for new cell
        """
        pass
    
    def query_radius(self, position: Vector2, radius: float,
                    obj_type: Optional[str] = None) -> List[QueryResult]:
        """
        Query all objects within a radius of a position.
        
        Args:
            position: Center point for query
            radius: Query radius in meters
            obj_type: Optional type filter
            
        Returns:
            List of QueryResult with object_id, position, distance
            
        Complexity: O(k) where k = number of cells covered by query
        """
        pass
    
    def query_aabb(self, min_x: float, min_y: float,
                   max_x: float, max_y: float,
                   obj_type: Optional[str] = None) -> List[QueryResult]:
        """
        Query all objects within an axis-aligned bounding box.
        
        Args:
            min_x, min_y: Bottom-left corner
            max_x, max_y: Top-right corner
            obj_type: Optional type filter
            
        Returns:
            List of QueryResult
            
        Complexity: O(k) where k = number of cells covered by query
        """
        pass
    
    def query_nearest(self, position: Vector2, limit: int = 1,
                     obj_type: Optional[str] = None,
                     max_distance: float = float('inf')) -> List[QueryResult]:
        """
        Query the N nearest objects to a position.
        
        Args:
            position: Center point for query
            limit: Maximum number of results (default 1)
            obj_type: Optional type filter
            max_distance: Maximum distance to consider
            
        Returns:
            List of QueryResult sorted by distance (ascending)
            
        Complexity: O(k + n log n) where k = cells, n = objects found
        """
        pass
    
    def find_collisions(self, obj_id: str, padding: float = 0.0) -> List[Collision]:
        """
        Find all objects colliding with a given object.
        
        Args:
            obj_id: Object to check collisions for
            padding: Additional collision margin
            
        Returns:
            List of Collision with object_id, penetration_depth, normal
            
        Complexity: O(k) where k = number of cells covered by object
        """
        pass
    
    def get_cell_occupancy(self, cell_x: int, cell_y: int) -> int:
        """
        Get the number of objects in a specific cell.
        Useful for load balancing and debugging.
        """
        pass
    
    def get_stats(self) -> SpatialIndexStats:
        """
        Get performance and usage statistics.
        """
        pass
```

### 1.4 Data Structures

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class Vector2:
    x: float
    y: float

@dataclass
class SpatialEntry:
    """Internal representation of an object in the spatial index."""
    obj_id: str
    position: Vector2
    radius: float
    obj_type: str
    metadata: Dict
    cell_x: int
    cell_y: int

@dataclass
class QueryResult:
    """Result from spatial queries."""
    obj_id: str
    position: Vector2
    distance: float
    obj_type: str
    metadata: Dict

@dataclass
class Collision:
    """Collision detection result."""
    obj_id: str
    other_obj_id: str
    penetration_depth: float
    normal: Vector2  # Points from other_obj towards obj

@dataclass
class Bounds:
    """World boundary definition."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

@dataclass
class SpatialIndexStats:
    """Performance and usage statistics."""
    total_objects: int
    total_cells: int
    occupied_cells: int
    avg_objects_per_cell: float
    max_objects_in_cell: int
    query_count: int
    avg_query_time_ms: float
```

### 1.5 Algorithm Details

#### Grid Coordinate Conversion

```python
def world_to_grid(self, position: Vector2) -> Tuple[int, int]:
    """Convert world position to grid cell coordinates."""
    cell_x = int(position.x // self.cell_size)
    cell_y = int(position.y // self.cell_size)
    return (cell_x, cell_y)

def grid_to_world(self, cell_x: int, cell_y: int) -> Vector2:
    """Convert grid cell to world position (cell center)."""
    return Vector2(
        x=(cell_x + 0.5) * self.cell_size,
        y=(cell_y + 0.5) * self.cell_size
    )
```

#### Cell Range Calculation for Queries

```python
def get_cells_in_radius(self, position: Vector2, radius: float) -> List[Tuple[int, int]]:
    """
    Get all grid cells that intersect with a query circle.
    
    Algorithm:
    1. Calculate cell range from bounding box of query circle
    2. Iterate through cells in range
    3. Add cells that intersect with the circle
    """
    min_x = position.x - radius
    max_x = position.x + radius
    min_y = position.y - radius
    max_y = position.y + radius
    
    cell_min_x = int(min_x // self.cell_size)
    cell_max_x = int(max_x // self.cell_size)
    cell_min_y = int(min_y // self.cell_size)
    cell_max_y = int(max_y // self.cell_size)
    
    cells = []
    for cx in range(cell_min_x, cell_max_x + 1):
        for cy in range(cell_min_y, cell_max_y + 1):
            # Check if cell actually intersects with circle (optimization)
            if self.cell_intersects_circle(cx, cy, position, radius):
                cells.append((cx, cy))
    
    return cells
```

### 1.6 Integration with FateEngine

```python
class FateEngine:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Initialize spatial index
        self.spatial_index = SpatialIndex(
            cell_size=2.0,
            world_bounds=self._get_world_bounds_from_config()
        )
        
        # Register all initial objects
        self._register_world_objects()
    
    def _register_world_objects(self):
        """Register all actors and objects in spatial index."""
        # Register actors
        for actor_id, actor in self.world_state.actors.items():
            self.spatial_index.add(
                obj_id=actor_id,
                position=actor.position,
                radius=0.5,  # Actor collision radius
                obj_type="actor",
                metadata={"name": actor.name}
            )
        
        # Register environmental objects
        for obj_id, obj in self.world_state.objects.items():
            radius = float(obj.properties.get("radius", "1.0"))
            self.spatial_index.add(
                obj_id=obj_id,
                position=obj.position,
                radius=radius,
                obj_type=obj.type,
                metadata=obj.properties
            )
    
    async def _resolve_move(self, proposal: Proposal, actor: Actor) -> Resolution:
        """Enhanced move resolution with spatial collision detection."""
        # ... existing code ...
        
        # Check for collisions at destination using spatial index
        collisions = self.spatial_index.find_collisions(
            obj_id=actor_id,
            padding=0.1
        )
        
        if collisions:
            # Collision detected - resolve based on agent hierarchy
            for collision in collisions:
                if collision.other_obj_id in self.world_state.actors:
                    # Actor-Actor collision
                    other_actor = self.world_state.actors[collision.other_obj_id]
                    return self._resolve_actor_collision(
                        proposal, actor, other_actor, collision
                    )
                else:
                    # Actor-Object collision
                    obj = self.world_state.objects.get(collision.other_obj_id)
                    return self._resolve_object_collision(
                        proposal, actor, obj, collision
                    )
        
        # No collision - proceed with move
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=True,
            outcome={...}
        )
```

---

## Component 2: Proposal Window System

### 2.1 Overview

The **ProposalWindow** system introduces temporal coordination for agent actions. Instead of instant resolution, agents submit proposals during a configurable time window, allowing for:

- Simultaneous action coordination
- Conflict detection before resolution
- Prioritized action sequencing
- Multi-tick commitment phases

### 2.2 Design Decisions

**Window Strategy: Fixed Tick Windows**
- **Window Size**: 3-5 ticks (configurable, ~150-250ms at 20 TPS)
- **Window Phases**: Open → Closing → Resolved
- **Buffering**: Proposals submitted outside window queued for next window
- **Prioritization**: EMOTE > INTERACT > MOVE (configurable)

**Alternative (Future): Rolling Windows**
- Deferred to Phase 3 for optimization

### 2.3 Core Interface

```python
class ProposalWindow:
    """
    Manages multi-tick proposal windows for coordinated agent actions.
    
    Window Lifecycle:
    1. OPEN: Accepting new proposals
    2. CLOSING: No longer accepting, preparing for resolution
    3. RESOLVED: All proposals processed, ready for next window
    
    States transition deterministically based on tick numbers.
    """
    
    def __init__(self, window_size_ticks: int = 5):
        """
        Args:
            window_size_ticks: Number of ticks per proposal window
        """
        self.window_size_ticks = window_size_ticks
        self.current_window_id: int = 0
        self.window_state: WindowState = WindowState.OPEN
        
        # Proposal storage
        self.current_proposals: List[core_pb2.Proposal] = []
        self.pending_queue: List[core_pb2.Proposal] = []
        self.resolved_queue: Dict[int, List[Resolution]] = {}  # window_id -> resolutions
        
        # Timing
        self.window_start_tick: int = 0
        self.window_close_tick: int = window_size_ticks - 1
        
    def submit(self, proposal: core_pb2.Proposal) -> SubmissionResult:
        """
        Submit a proposal to the current or next window.
        
        Args:
            proposal: Proposal to submit
            
        Returns:
            SubmissionResult with status (ACCEPTED/QUEUED/REJECTED)
        """
        pass
    
    def advance_tick(self, tick: int) -> WindowTransition:
        """
        Advance the proposal window state.
        
        Called at the beginning of each tick to:
        1. Check if window should close
        2. If closing, trigger resolution phase
        3. If resolved, start new window
        
        Args:
            tick: Current tick number
            
        Returns:
            WindowTransition describing what happened
        """
        pass
    
    def get_current_window_id(self) -> int:
        """Get the ID of the current proposal window."""
        pass
    
    def get_proposals_for_resolution(self) -> List[core_pb2.Proposal]:
        """
        Get all proposals ready for resolution.
        
        Should only be called when window state is CLOSING.
        """
        pass
    
    def submit_resolutions(self, window_id: int, resolutions: List[Resolution]):
        """
        Submit resolutions for a completed window.
        
        Args:
            window_id: Window ID these resolutions belong to
            resolutions: List of resolved proposals
        """
        pass
    
    def get_resolutions_for_feedback(self, tick: int) -> List[Resolution]:
        """
        Get resolutions ready for agent feedback.
        
        Uses a delay mechanism (typically 2 ticks) to ensure
        all agents see consistent world state.
        """
        pass
    
    def get_window_stats(self) -> WindowStats:
        """Get statistics about proposal windows."""
        pass
```

### 2.4 Data Structures

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class WindowState(Enum):
    """States of a proposal window."""
    OPEN = "OPEN"           # Accepting proposals
    CLOSING = "CLOSING"     # Preparing for resolution
    RESOLVED = "RESOLVED"   # Resolution complete

@dataclass
class SubmissionResult:
    """Result of a proposal submission."""
    status: SubmissionStatus
    window_id: int
    proposal_id: str
    message: str

class SubmissionStatus(Enum):
    ACCEPTED = "ACCEPTED"     # Accepted into current window
    QUEUED = "QUEUED"        # Queued for next window
    REJECTED = "REJECTED"     # Rejected (invalid window state)

@dataclass
class WindowTransition:
    """Description of a window state transition."""
    tick: int
    previous_state: WindowState
    new_state: WindowState
    action_taken: TransitionAction
    proposals_resolved: int

class TransitionAction(Enum):
    NONE = "NONE"
    WINDOW_CLOSED = "WINDOW_CLOSED"
    WINDOW_RESOLVED = "WINDOW_RESOLVED"
    NEW_WINDOW_OPENED = "NEW_WINDOW_OPENED"

@dataclass
class WindowStats:
    """Statistics about proposal windows."""
    current_window_id: int
    current_state: WindowState
    proposals_in_window: int
    proposals_queued: int
    avg_proposals_per_window: float
    windows_completed: int
```

### 2.5 Proposal Prioritization

```python
class ProposalPrioritizer:
    """
    Sorts proposals for deterministic resolution order.
    
    Priority Rules:
    1. Action type: EMOTE > INTERACT > MOVE > IDLE
    2. Timestamp: Earlier proposals first
    3. Actor speed (for MOVE): Faster actors first
    4. Random seed tiebreaker: Deterministic randomness
    """
    
    ACTION_PRIORITY = {
        core_pb2.ActionType.EMOTE: 100,
        core_pb2.ActionType.REFLECT: 90,
        core_pb2.ActionType.INTERACT: 80,
        core_pb2.ActionType.USE: 75,
        core_pb2.ActionType.EXAMINE: 70,
        core_pb2.ActionType.COLLECT: 60,
        core_pb2.ActionType.TAKE: 50,
        core_pb2.ActionType.DROP: 40,
        core_pb2.ActionType.MOVE: 30,
        core_pb2.ActionType.IDLE: 10,
    }
    
    @staticmethod
    def prioritize(proposals: List[core_pb2.Proposal],
                  actor_speeds: Dict[str, float],
                  rng: random.Random) -> List[core_pb2.Proposal]:
        """
        Sort proposals by priority rules.
        
        Args:
            proposals: List of proposals to prioritize
            actor_speeds: Mapping of actor_id -> movement speed
            rng: Seeded random number generator for tiebreaking
            
        Returns:
            Sorted list of proposals
        """
        def sort_key(proposal: core_pb2.Proposal) -> tuple:
            # Primary: Action type priority (higher = more important)
            action_priority = ProposalPrioritizer.ACTION_PRIORITY.get(
                proposal.action, 0
            )
            
            # Secondary: Timestamp (earlier = more important)
            timestamp = _from_pb_timestamp(proposal.timestamp)
            
            # Tertiary: Actor speed (for MOVE actions)
            speed = actor_speeds.get(proposal.actor_id, 1.0)
            
            # Quaternary: Deterministic tiebreaker
            # Use hash of proposal_id for deterministic ordering
            tiebreaker = hash(proposal.proposal_id) & 0x7FFFFFFF
            
            return (-action_priority, timestamp, -speed, tiebreaker)
        
        return sorted(proposals, key=sort_key)
```

### 2.6 Integration with FateEngine

```python
class FateEngine:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Initialize proposal window system
        self.proposal_window = ProposalWindow(
            window_size_ticks=self.proposal_window_ms // 50  # Convert ms to ticks at 20 TPS
        )
        
        # Actor speeds for prioritization
        self.actor_speeds: Dict[str, float] = {}
    
    async def submit_proposal(self, proposal: core_pb2.Proposal) -> bool:
        """Submit proposal through the window system."""
        result = self.proposal_window.submit(proposal)
        
        if result.status == SubmissionStatus.REJECTED:
            logger.warning(f"Proposal rejected: {result.message}")
            return False
        
        return True
    
    async def _phase_proposal_window(self, tick: int):
        """
        Enhanced proposal window phase with multi-tick coordination.
        """
        # Advance window state
        transition = self.proposal_window.advance_tick(tick)
        
        logger.debug(
            f"  Window transition: {transition.previous_state} -> "
            f"{transition.new_state} ({transition.action_taken})"
        )
        
        # Handle window closing
        if transition.action_taken == TransitionAction.WINDOW_CLOSED:
            logger.info(f"  Proposal window {transition.tick} closed with "
                       f"{len(self.proposal_window.current_proposals)} proposals")
        
        # Handle resolution phase
        if transition.action_taken == TransitionAction.WINDOW_RESOLVED:
            proposals = self.proposal_window.get_proposals_for_resolution()
            self.current_window_proposals = proposals
            
            # Prioritize proposals
            self.current_window_proposals = ProposalPrioritizer.prioritize(
                proposals,
                self.actor_speeds,
                self.rng
            )
            
            logger.debug(f"  {len(self.current_window_proposals)} proposals prioritized")
            
            # Generate reflex proposals if available
            if self.reflex_layer:
                reflex_proposals = await self._generate_reflex_proposals(tick)
                self.current_window_proposals.extend(reflex_proposals)
    
    async def _phase_fate_resolution(self, tick: int) -> List[Resolution]:
        """
        Enhanced resolution with window system integration.
        """
        resolutions = []
        
        # Resolve prioritized proposals
        for proposal in self.current_window_proposals:
            resolution = await self._resolve_proposal(proposal)
            resolutions.append(resolution)
            
            if resolution.success:
                await self._apply_outcome(resolution)
            
            logger.debug(
                f"  Resolved {ActionType.Name(proposal.action)} for "
                f"{proposal.actor_id}: {'SUCCESS' if resolution.success else 'FAILED'}"
            )
        
        # Submit resolutions to window system
        window_id = self.proposal_window.get_current_window_id()
        self.proposal_window.submit_resolutions(window_id, resolutions)
        
        return resolutions
```

---

## Component 3: Affordance System

### 3.1 Overview

The **AffordanceSystem** provides a declarative framework for defining what actions are possible on objects and under what conditions. It replaces hardcoded action logic with a flexible, extensible system.

### 3.2 Design Decisions

**Affordance Model: Declarative Rules**
- **Structure**: Each object has a list of affordances
- **Conditions**: Boolean expressions evaluated at runtime
- **Effects**: Procedural descriptions of outcomes
- **Semantic Tags**: For LLM affordance discovery

**Validation Strategy: Multi-Stage**
1. **Syntax Validation**: Parse precondition expression
2. **Semantic Validation**: Check variable existence
3. **Runtime Validation**: Evaluate with current world state

### 3.3 Core Interface

```python
class AffordanceSystem:
    """
    Manages object affordances and validates interaction proposals.
    
    Affordances define what actions an object supports and under what
    conditions those actions can be performed.
    """
    
    def __init__(self, world_state: core_pb2.WorldState):
        """
        Args:
            world_state: Reference to world state for condition evaluation
        """
        self.world_state = world_state
        self.condition_parser: ConditionParser = ConditionParser()
        
    def validate_affordance(self, actor: Actor, obj: EnvironmentObject,
                           action: str) -> AffordanceValidation:
        """
        Validate if an actor can perform an action on an object.
        
        Args:
            actor: Actor attempting the action
            obj: Object being acted upon
            action: Action type (e.g., "COLLECT", "USE")
            
        Returns:
            AffordanceValidation with success status and details
        """
        pass
    
    def get_available_affordances(self, actor: Actor,
                                  obj: EnvironmentObject) -> List[Affordance]:
        """
        Get all affordances available to an actor for an object.
        
        Filters affordances based on the actor's current state.
        """
        pass
    
    def execute_affordance(self, actor: Actor, obj: EnvironmentObject,
                          affordance: Affordance, context: Dict) -> AffordanceEffect:
        """
        Execute an affordance and return its effects.
        
        Args:
            actor: Actor performing the action
            obj: Object being acted upon
            affordance: Affordance to execute
            context: Additional context (parameters, etc.)
            
        Returns:
            AffordanceEffect with world state changes
        """
        pass
    
    def add_affordance(self, obj_id: str, affordance: Affordance) -> bool:
        """Add an affordance to an object."""
        pass
    
    def remove_affordance(self, obj_id: str, action_type: str) -> bool:
        """Remove an affordance from an object."""
        pass
```

### 3.4 Data Structures

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

@dataclass
class Affordance:
    """
    Definition of an affordance (what an object allows).
    
    Example:
        Affordance(
            action_type="COLLECT",
            precondition="distance < 2.0 AND actor.holding == False",
            effect_description="agent.inventory.add(object.id)",
            semantic_tags=["takeable", "portable"]
        )
    """
    action_type: str
    precondition: str  # Boolean expression string
    effect_description: str  # Natural language description
    semantic_tags: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)  # Additional constraints
    
    def is_valid_for_action(self, action: str) -> bool:
        """Check if this affordance matches an action type."""
        return self.action_type.upper() == action.upper()

@dataclass
class AffordanceValidation:
    """Result of affordance validation."""
    is_valid: bool
    affordance: Optional[Affordance]
    failed_conditions: List[str] = field(default_factory=list)
    reason: str = ""
    
    def __bool__(self) -> bool:
        return self.is_valid

@dataclass
class AffordanceEffect:
    """Result of executing an affordance."""
    success: bool
    world_changes: Dict[str, Any] = field(default_factory=dict)
    actor_changes: Dict[str, Any] = field(default_factory=dict)
    object_changes: Dict[str, Any] = field(default_factory=dict)
    side_effects: List[str] = field(default_factory=list)

class AffordanceError(Enum):
    """Types of affordance validation errors."""
    NO_AFFORDANCE = "NO_AFFORDANCE"
    CONDITION_FAILED = "CONDITION_FAILED"
    PARSE_ERROR = "PARSE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    MISSING_VARIABLE = "MISSING_VARIABLE"
```

### 3.5 Condition Parser

```python
class ConditionParser:
    """
    Parses and evaluates affordance precondition expressions.
    
    Supports:
    - Comparisons: ==, !=, <, >, <=, >=
    - Logical operators: AND, OR, NOT
    - Parentheses for grouping
    - Variables: actor.*, object.*, world.*
    
    Example conditions:
        "distance < 2.0"
        "actor.holding == False"
        "object.state == 'open' AND actor.has_key == True"
        "world.time_of_day != 'night'"
    """
    
    # Token types
    TOKEN_TYPES = {
        'IDENTIFIER': r'[a-zA-Z_][a-zA-Z0-9_]*',
        'NUMBER': r'\d+\.?\d*',
        'STRING': r'\'[^\']*\'|\"[^\"]*\"',
        'OPERATOR': r'==|!=|<=|>=|<|>|AND|OR|NOT',
        'PAREN': r'\(|\)',
        'WHITESPACE': r'\s+',
    }
    
    def parse(self, condition: str) -> ASTNode:
        """
        Parse a condition string into an AST.
        
        Args:
            condition: Condition expression string
            
        Returns:
            ASTNode representing the parsed condition
            
        Raises:
            ParseError: If condition syntax is invalid
        """
        pass
    
    def evaluate(self, ast: ASTNode, context: Dict[str, Any]) -> bool:
        """
        Evaluate a parsed AST with given context.
        
        Args:
            ast: Parsed AST node
            context: Variable binding context (actor, object, distance, etc.)
            
        Returns:
            Boolean result of evaluation
            
        Raises:
            EvaluationError: If evaluation fails
        """
        pass
    
    def validate_syntax(self, condition: str) -> ValidationResult:
        """
        Validate condition syntax without evaluating.
        
        Returns:
            ValidationResult with success and any errors
        """
        pass

@dataclass
class ASTNode:
    """Abstract Syntax Tree node."""
    type: str  # 'AND', 'OR', 'NOT', 'COMPARE', 'VALUE'
    operator: Optional[str] = None
    left: Optional['ASTNode'] = None
    right: Optional['ASTNode'] = None
    value: Optional[Any] = None

@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

### 3.6 Standard Affordance Library

```python
class StandardAffordances:
    """
    Predefined affordances for common object types.
    
    These can be used as templates or directly applied to objects.
    """
    
    @staticmethod
    def collectible(max_distance: float = 2.0) -> Affordance:
        """Affordance for collectible objects."""
        return Affordance(
            action_type="COLLECT",
            precondition=f"distance < {max_distance} AND actor.holding == False",
            effect_description="Object is added to actor's inventory",
            semantic_tags=["takeable", "portable"]
        )
    
    @staticmethod
    def openable(requires_key: bool = False, key_id: Optional[str] = None) -> Affordance:
        """Affordance for openable objects (doors, chests)."""
        if requires_key and key_id:
            precondition = (f"distance < 2.0 AND object.state != 'open' AND "
                          f"actor.inventory contains '{key_id}'")
        else:
            precondition = "distance < 2.0 AND object.state != 'open'"
        
        return Affordance(
            action_type="INTERACT",
            precondition=precondition,
            effect_description="Object is opened, revealing contents",
            semantic_tags=["openable", "container"]
        )
    
    @staticmethod
    def usable(duration_ticks: int = 1) -> Affordance:
        """Affordance for usable items (tools, consumables)."""
        return Affordance(
            action_type="USE",
            precondition="distance < 1.0 AND actor.inventory contains object.id",
            effect_description=f"Object is used, taking effect for {duration_ticks} tick(s)",
            semantic_tags=["usable", "consumable"],
            requirements={"duration_ticks": duration_ticks}
        )
    
    @staticmethod
    def examinable(max_distance: float = 5.0) -> Affordance:
        """Affordance for examining objects."""
        return Affordance(
            action_type="EXAMINE",
            precondition=f"distance < {max_distance}",
            effect_description="Object's details are revealed to the actor",
            semantic_tags=["examinable"]
        )
    
    @staticmethod
    def tradable(price: int, currency: str = "gold") -> Affordance:
        """Affordance for trading objects."""
        return Affordance(
            action_type="INTERACT",
            precondition=f"distance < 2.0 AND actor.{currency} >= {price}",
            effect_description=f"Object is exchanged for {price} {currency}",
            semantic_tags=["tradable", "valuable"],
            requirements={"price": price, "currency": currency}
        )
    
    @staticmethod
    def container(capacity: int = 10) -> Affordance:
        """Affordance for container objects."""
        return Affordance(
            action_type="INTERACT",
            precondition=f"distance < 2.0 AND object.contents.length < {capacity}",
            effect_description="Actor can add/remove items from container",
            semantic_tags=["container", "storage"],
            requirements={"capacity": capacity}
        )
```

### 3.7 Integration with FateEngine

```python
class FateEngine:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Initialize affordance system
        self.affordance_system = AffordanceSystem(self.world_state)
    
    def _load_object_affordances(self):
        """Load affordances for all world objects."""
        for obj_id, obj in self.world_state.objects.items():
            # Add affordances from object definition
            for aff_proto in obj.affordances:
                affordance = Affordance(
                    action_type=aff_proto.action_type,
                    precondition=aff_proto.precondition,
                    effect_description=aff_proto.effect_description,
                    semantic_tags=list(aff_proto.semantic_tags)
                )
                self.affordance_system.add_affordance(obj_id, affordance)
    
    async def _resolve_interact(self, proposal: Proposal, actor: Actor) -> Resolution:
        """Enhanced interaction resolution with affordance validation."""
        target_id = proposal.parameters.get("target_id")
        
        # Check if target exists
        if target_id not in self.world_state.objects:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=proposal.actor_id,
                success=False,
                reason=f"Target object not found: {target_id}"
            )
        
        obj = self.world_state.objects[target_id]
        
        # Calculate distance
        distance = (
            (actor.position.x - obj.position.x) ** 2 +
            (actor.position.y - obj.position.y) ** 2
        ) ** 0.5
        
        # Build context for affordance evaluation
        context = {
            'actor': actor,
            'object': obj,
            'distance': distance,
            'world': self.world_state
        }
        
        # Validate affordance
        validation = self.affordance_system.validate_affordance(
            actor, obj, proposal.parameters.get("type", "INTERACT")
        )
        
        if not validation:
            return core_pb2.Resolution(
                proposal_id=proposal.proposal_id,
                actor_id=proposal.actor_id,
                success=False,
                reason=f"Affordance validation failed: {validation.reason}"
            )
        
        # Execute affordance
        effect = self.affordance_system.execute_affordance(
            actor, obj, validation.affordance, proposal.parameters
        )
        
        if effect.success:
            # Apply world changes
            self._apply_affordance_effect(effect)
        
        return core_pb2.Resolution(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.actor_id,
            success=effect.success,
            outcome={
                "action": "interact",
                "type": proposal.parameters.get("type", "generic"),
                "target_id": target_id,
                "effects": effect.world_changes
            },
            reason=effect.world_changes.get("result", "")
        )
```

---

## Component 4: Visual Perception with Raycasting

### 4.1 Overview

The **VisualPerceptionSystem** adds line-of-sight (LOS) and occlusion to agent perception. Instead of seeing all objects within a radius, agents can only see objects that are not blocked by obstacles.

### 4.2 Design Decisions

**Raycasting Strategy: Discrete Ray Sampling**
- **Ray Count**: 32-64 rays per agent (configurable)
- **Ray Distribution**: Uniform within FOV
- **Occlusion Objects**: Static environment objects marked as "opaque"
- **Distance Falloff**: Certainty decays with distance (0.0 at max_range)

**Optimization: Grid-Based Ray Traversal**
- Uses the existing SpatialIndex for efficient ray traversal
- DDA (Digital Differential Analyzer) algorithm for cell traversal
- Early termination when occluder is hit

### 4.3 Core Interface

```python
class VisualPerceptionSystem:
    """
    Provides line-of-sight perception for agents.
    
    Agents can only see objects that are:
    1. Within their vision range
    2. Within their field of view
    3. Not occluded by opaque objects
    """
    
    def __init__(self, spatial_index: SpatialIndex):
        """
        Args:
            spatial_index: Spatial index for ray traversal
        """
        self.spatial_index = spatial_index
        self.ray_cache: Dict[Tuple, RaycastResult] = {}  # Cache for ray results
        
    def get_visible_objects(self, agent: Actor,
                            profile: SensoryProfile) -> List[VisibleObject]:
        """
        Get all objects visible to an agent.
        
        Args:
            agent: Agent performing the perception
            profile: Sensory profile (range, FOV, etc.)
            
        Returns:
            List of VisibleObject with object info and certainty
        """
        pass
    
    def cast_ray(self, origin: Vector2, direction: Vector2,
                max_distance: float) -> RaycastResult:
        """
        Cast a single ray and find what it hits.
        
        Args:
            origin: Ray start position
            direction: Normalized ray direction
            max_distance: Maximum ray distance
            
        Returns:
            RaycastResult with hit information
        """
        pass
    
    def cast_rays(self, origin: Vector2, facing_direction: float,
                 fov: float, ray_count: int,
                 max_distance: float) -> List[RaycastResult]:
        """
        Cast multiple rays covering a field of view.
        
        Args:
            origin: Ray origin position
            facing_direction: Direction agent is facing (radians)
            fov: Field of view angle (radians)
            ray_count: Number of rays to cast
            max_distance: Maximum ray distance
            
        Returns:
            List of RaycastResult
        """
        pass
    
    def is_line_blocked(self, start: Vector2, end: Vector2,
                       ignore_objects: List[str] = None) -> bool:
        """
        Check if a line segment is blocked by any occluders.
        
        Args:
            start: Line start position
            end: Line end position
            ignore_objects: Objects to ignore for occlusion
            
        Returns:
            True if line is blocked, False otherwise
        """
        pass
    
    def get_percept_for_object(self, agent: Actor, obj_id: str,
                              profile: SensoryProfile) -> Optional[Percept]:
        """
        Get a percept for a specific object (if visible).
        
        Args:
            agent: Agent performing perception
            obj_id: Object ID to check
            profile: Sensory profile
            
        Returns:
            Percept if visible, None otherwise
        """
        pass
```

### 4.4 Data Structures

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

@dataclass
class SensoryProfile:
    """
    Defines an agent's sensory capabilities.
    """
    vision_range: float = 15.0  # Max vision distance (meters)
    vision_fov: float = 120.0   # Field of view in degrees
    ray_count: int = 32         # Number of rays for raycasting
    vision_certainty_decay: float = 0.05  # Certainty decay per meter
    hearing_range: float = 10.0  # Max hearing distance (meters)
    
    def to_radians(self, degrees: float) -> float:
        """Convert degrees to radians."""
        return degrees * 3.14159 / 180.0
    
    @property
    def vision_fov_radians(self) -> float:
        """Get FOV in radians."""
        return self.to_radians(self.vision_fov)

@dataclass
class VisibleObject:
    """
    Information about a visible object.
    """
    obj_id: str
    obj_type: str
    position: Vector2
    distance: float
    certainty: float  # 0.0 - 1.0
    visible_affordances: List[str] = field(default_factory=list)
    apparent_state: str = ""
    occluded: bool = False  # True if partially occluded

@dataclass
class RaycastResult:
    """
    Result of a raycast operation.
    """
    hit: bool
    hit_position: Optional[Vector2] = None
    hit_object_id: Optional[str] = None
    distance: float = 0.0
    traversed_cells: List[Tuple[int, int]] = field(default_factory=list)
    occluded_objects: List[str] = field(default_factory=list)  # Objects passed through

@dataclass
class Percept:
    """
    A single unit of sensory information.
    """
    percept_id: str
    tick_observed: int
    channel: PerceptChannel
    content: Any  # ActorPercept, ObjectPercept, EventPercept, SpeechPercept
    salience: float = 0.5  # 0.0 - 1.0
    certainty: float = 1.0  # 0.0 - 1.0

class PerceptChannel(Enum):
    VISION = "VISION"
    HEARING = "HEARING"
    PROPRIOCEPTION = "PROPRIOCEPTION"
    MEMORY_ECHO = "MEMORY_ECHO"
```

### 4.5 Raycasting Algorithms

#### DDA Grid Traversal

```python
def dda_traversal(self, origin: Vector2, direction: Vector2,
                  max_distance: float) -> List[Tuple[int, int]]:
    """
    Digital Differential Analyzer for efficient grid traversal.
    
    Args:
        origin: Ray origin in world space
        direction: Normalized ray direction
        max_distance: Maximum traversal distance
        
    Returns:
        List of (cell_x, cell_y) tuples traversed by the ray
    """
    cell_size = self.spatial_index.cell_size
    
    # Starting cell
    start_x = int(origin.x // cell_size)
    start_y = int(origin.y // cell_size)
    
    # Direction sign for each axis
    step_x = 1 if direction.x >= 0 else -1
    step_y = 1 if direction.y >= 0 else -1
    
    # Distance to next cell boundary
    t_max_x = self._next_cell_boundary(origin.x, direction.x, step_x, cell_size)
    t_max_y = self._next_cell_boundary(origin.y, direction.y, step_y, cell_size)
    
    # Distance between cell boundaries
    t_delta_x = cell_size / abs(direction.x) if direction.x != 0 else float('inf')
    t_delta_y = cell_size / abs(direction.y) if direction.y != 0 else float('inf')
    
    # Current position
    current_x, current_y = start_x, start_y
    cells = [(current_x, current_y)]
    
    # Traverse until max_distance
    current_distance = 0.0
    
    while current_distance < max_distance:
        # Move to next cell
        if t_max_x < t_max_y:
            current_x += step_x
            current_distance = t_max_x
            t_max_x += t_delta_x
        else:
            current_y += step_y
            current_distance = t_max_y
            t_max_y += t_delta_y
        
        cells.append((current_x, current_y))
        
        # Check for occluder in current cell
        if self._cell_has_occluder(current_x, current_y):
            break
    
    return cells

def _next_cell_boundary(self, pos: float, direction: float,
                       step: int, cell_size: float) -> float:
    """
    Calculate distance to next cell boundary.
    """
    if direction == 0:
        return float('inf')
    
    if step > 0:
        boundary = (int(pos // cell_size) + 1) * cell_size
    else:
        boundary = int(pos // cell_size) * cell_size
    
    return (boundary - pos) / direction
```

#### Ray-Object Intersection

```python
def check_ray_object_intersection(self, ray_origin: Vector2, ray_dir: Vector2,
                                  obj_id: str, obj_radius: float) -> Optional[float]:
    """
    Check if a ray intersects with a circular object.
    
    Args:
        ray_origin: Ray start position
        ray_dir: Normalized ray direction
        obj_id: Object ID to check
        obj_radius: Object's bounding radius
        
    Returns:
        Distance to intersection, or None if no intersection
    """
    obj_entry = self.spatial_index.object_map.get(obj_id)
    if not obj_entry:
        return None
    
    obj_pos = obj_entry.position
    
    # Vector from ray origin to object center
    to_object = Vector2(
        obj_pos.x - ray_origin.x,
        obj_pos.y - ray_origin.y
    )
    
    # Project onto ray direction
    projection = to_object.x * ray_dir.x + to_object.y * ray_dir.y
    
    # Closest point on ray to object center
    closest = Vector2(
        ray_origin.x + projection * ray_dir.x,
        ray_origin.y + projection * ray_dir.y
    )
    
    # Distance from closest point to object center
    distance_to_center = (
        (closest.x - obj_pos.x) ** 2 +
        (closest.y - obj_pos.y) ** 2
    ) ** 0.5
    
    # Check if ray hits object
    if distance_to_center <= obj_radius:
        # Calculate intersection distance
        offset = (obj_radius ** 2 - distance_to_center ** 2) ** 0.5
        hit_distance = projection - offset
        
        if hit_distance >= 0:
            return hit_distance
    
    return None
```

### 4.6 Integration with Agent Brain

```python
class AgentBrain:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Initialize visual perception system
        if hasattr(fate_engine, 'visual_perception'):
            self.visual_perception = fate_engine.visual_perception
        else:
            self.visual_perception = None
    
    async def update_perception(self):
        """
        Update agent's perception using enhanced visual system.
        """
        if not self.visual_perception:
            # Fallback to simple distance-based perception
            return await self._update_perception_simple()
        
        # Get sensory profile
        profile = self._get_sensory_profile()
        
        # Get visible objects
        visible_objects = self.visual_perception.get_visible_objects(
            self.actor, profile
        )
        
        # Build percepts
        percepts = []
        
        for visible_obj in visible_objects:
            # Determine percept type
            if visible_obj.obj_type == "actor":
                content = self._build_actor_percept(visible_obj)
            else:
                content = self._build_object_percept(visible_obj)
            
            percept = Percept(
                percept_id=f"{self.actor.id}_percept_{uuid.uuid4().hex[:8]}",
                tick_observed=self.current_tick,
                channel=PerceptChannel.VISION,
                content=content,
                salience=self._calculate_salience(visible_obj),
                certainty=visible_obj.certainty
            )
            
            percepts.append(percept)
        
        # Add memory echoes for recently seen but no longer visible objects
        memory_echoes = self._get_memory_echoes(visible_objects)
        percepts.extend(memory_echoes)
        
        # Store percepts for decision making
        self.current_percepts = percepts
        
        return percepts
    
    def _get_sensory_profile(self) -> SensoryProfile:
        """
        Get or create sensory profile for this agent.
        
        Default values can be overridden by agent-specific properties.
        """
        return SensoryProfile(
            vision_range=float(self.actor.properties.get("vision_range", "15.0")),
            vision_fov=float(self.actor.properties.get("vision_fov", "120.0")),
            ray_count=int(self.actor.properties.get("ray_count", "32")),
            hearing_range=float(self.actor.properties.get("hearing_range", "10.0"))
        )
    
    def _calculate_salience(self, visible_obj: VisibleObject) -> float:
        """
        Calculate salience of a visible object.
        
        Higher salience = more attention from the agent.
        """
        # Distance-based salience (closer = more salient)
        distance_salience = max(0.0, 1.0 - visible_obj.distance / 15.0)
        
        # Movement salience (moving objects are more salient)
        movement_salience = 0.3 if "moving" in visible_obj.apparent_state else 0.0
        
        # Type-based salience
        type_salience = {
            "actor": 0.5,
            "weapon": 0.4,
            "food": 0.3,
            "tool": 0.2,
            "decoration": 0.1
        }.get(visible_obj.obj_type, 0.1)
        
        # Combine with weighted average
        salience = (
            distance_salience * 0.4 +
            movement_salience * 0.3 +
            type_salience * 0.3
        )
        
        return min(1.0, max(0.0, salience))
    
    def _build_object_percept(self, visible_obj: VisibleObject) -> ObjectPercept:
        """Build an ObjectPercept from visible object data."""
        return ObjectPercept(
            object_id=visible_obj.obj_id,
            apparent_type=visible_obj.obj_type,
            approximate_position=visible_obj.position,
            visible_affordances=visible_obj.visible_affordances
        )
```

---

## Integration Interfaces

### Interface 1: SpatialIndex ↔ FateEngine

```python
# Integration points in FateEngine

class FateEngine:
    def __init__(self, ...):
        # Initialize spatial index
        self.spatial_index = SpatialIndex(cell_size=2.0)
    
    # Actor lifecycle hooks
    def register_actor(self, actor_id: str, name: str, position: tuple = (0, 0)):
        """Register actor and add to spatial index."""
        # ... existing code ...
        self.spatial_index.add(
            obj_id=actor_id,
            position=common_pb2.Vector2(x=position[0], y=position[1]),
            radius=0.5,
            obj_type="actor",
            metadata={"name": name}
        )
    
    def unregister_actor(self, actor_id: str):
        """Unregister actor and remove from spatial index."""
        self.spatial_index.remove(actor_id)
        # ... existing code ...
    
    # Movement resolution with spatial checks
    async def _resolve_move(self, proposal: Proposal, actor: Actor) -> Resolution:
        # Check spatial collisions
        dest_pos = Vector2(x=float(proposal.parameters.get("to_x", 0)),
                           y=float(proposal.parameters.get("to_y", 0)))
        
        # Temporary move for collision check
        old_pos = actor.position
        actor.position = dest_pos
        
        collisions = self.spatial_index.find_collisions(actor_id)
        actor.position = old_pos  # Restore position
        
        if collisions:
            return self._handle_collisions(proposal, actor, collisions)
        
        # No collision - proceed
        return Resolution(...)
```

### Interface 2: ProposalWindow ↔ FateEngine

```python
# Integration points in FateEngine

class FateEngine:
    async def run(self):
        """
        Enhanced tick loop with proposal window system.
        """
        while self.running:
            # Phase 1: State Broadcast
            await self._phase_state_broadcast(self.current_tick)
            
            # Phase 2: Proposal Window (multi-tick coordination)
            await self._phase_proposal_window(self.current_tick)
            
            # Phase 3: Fate Resolution
            resolutions = await self._phase_fate_resolution(self.current_tick)
            
            # ... existing code ...
    
    async def submit_proposal(self, proposal: Proposal) -> bool:
        """Route proposal through window system."""
        return self.proposal_window.submit(proposal)
```

### Interface 3: AffordanceSystem ↔ FateEngine

```python
# Integration points in FateEngine

class FateEngine:
    async def _resolve_interact(self, proposal: Proposal, actor: Actor) -> Resolution:
        """Interaction resolution with affordance validation."""
        target_id = proposal.parameters.get("target_id")
        obj = self.world_state.objects.get(target_id)
        
        if not obj:
            return Resolution(success=False, reason="Object not found")
        
        # Validate affordance
        validation = self.affordance_system.validate_affordance(
            actor, obj, proposal.parameters.get("type", "INTERACT")
        )
        
        if not validation:
            return Resolution(success=False, reason=validation.reason)
        
        # Execute affordance
        effect = self.affordance_system.execute_affordance(
            actor, obj, validation.affordance, proposal.parameters
        )
        
        # Apply effects
        if effect.success:
            self._apply_world_changes(effect.world_changes)
            self._apply_actor_changes(actor, effect.actor_changes)
            self._apply_object_changes(obj, effect.object_changes)
        
        return Resolution(success=effect.success, outcome=effect.world_changes)
```

### Interface 4: VisualPerceptionSystem ↔ AgentBrain

```python
# Integration points in AgentBrain

class AgentBrain:
    def __init__(self, fate_engine, visual_perception=None):
        self.fate_engine = fate_engine
        self.visual_perception = visual_perception or fate_engine.visual_perception
    
    async def update_perception(self):
        """Enhanced perception with raycasting."""
        if not self.visual_perception:
            # Fallback to simple perception
            return await self._update_perception_simple()
        
        profile = self._get_sensory_profile()
        visible_objects = self.visual_perception.get_visible_objects(
            self.actor, profile
        )
        
        # Build percepts from visible objects
        percepts = self._build_percepts(visible_objects)
        self.current_percepts = percepts
        
        return percepts
    
    def _get_sensory_profile(self) -> SensoryProfile:
        """Get agent's sensory profile."""
        return SensoryProfile(
            vision_range=float(self.actor.properties.get("vision_range", "15.0")),
            vision_fov=float(self.actor.properties.get("vision_fov", "120.0")),
            ray_count=int(self.actor.properties.get("ray_count", "32"))
        )
```

---

## Performance Specifications

### Performance Targets

| Component | Operation | Target Complexity | Target Latency |
|-----------|-----------|-------------------|----------------|
| SpatialIndex | add/remove | O(1) | <1ms |
| SpatialIndex | query_radius | O(k) where k = cells in radius | <5ms |
| SpatialIndex | query_nearest (n results) | O(k + n log n) | <10ms |
| SpatialIndex | find_collisions | O(k) | <5ms |
| ProposalWindow | submit | O(1) | <1ms |
| ProposalWindow | advance_tick | O(1) | <1ms |
| ProposalWindow | prioritize | O(n log n) where n = proposals | <10ms |
| AffordanceSystem | validate_affordance | O(p) where p = conditions | <5ms |
| AffordanceSystem | execute_affordance | O(e) where e = effects | <5ms |
| VisualPerception | cast_ray | O(k) where k = cells traversed | <2ms |
| VisualPerception | get_visible_objects | O(r * k) where r = rays | <50ms |

### Scalability Targets

- **Max Agents**: 100+ with <10ms tick latency
- **Max Objects**: 500+ with <50ms perception update
- **Max Ray Count per Agent**: 64 rays (configurable)
- **Spatial Index Cell Size**: 2.0m (tunable based on object density)

### Memory Usage Estimates

| Component | Per Agent | Per Object | Total (100 agents, 500 objects) |
|-----------|-----------|------------|----------------------------------|
| SpatialIndex Entry | ~100 bytes | ~80 bytes | ~50 KB |
| Proposal (per window) | ~200 bytes | N/A | ~20 KB (100 proposals/window) |
| Affordance | N/A | ~150 bytes | ~75 KB |
| Percept Cache | ~1 KB | N/A | ~100 KB |
| **Total** | ~1.3 KB | ~230 bytes | ~245 KB |

---

## Data Structures & API Contracts

### Proto Extensions for Phase 2

```protobuf
// Additions to core.proto

// Enhanced EnvironmentObject with occlusion properties
message EnvironmentObject {
    // ... existing fields ...
    
    // Phase 2: Occlusion properties
    bool occluder = 11;  // If true, blocks line of sight
    float occlusion_radius = 12;  // Effective radius for occlusion
    
    // Phase 2: Sensory properties
    float luminance = 13;  // 0.0 (dark) to 1.0 (bright)
    string sound_emission = 14;  // "none", "quiet", "normal", "loud"
}

// Enhanced Actor with sensory profile
message Actor {
    // ... existing fields ...
    
    // Phase 2: Sensory profile
    SensoryProfile sensory_profile = 11;
    
    // Phase 2: Facing direction (radians)
    float facing_direction = 12;
    
    // Phase 2: Movement speed
    float movement_speed = 13;
}

// Sensory profile definition
message SensoryProfile {
    float vision_range = 1;
    float vision_fov = 2;
    int32 ray_count = 3;
    float vision_certainty_decay = 4;
    float hearing_range = 5;
}

// Affordance validation result (for feedback)
message AffordanceValidation {
    bool is_valid = 1;
    string reason = 2;
    repeated string failed_conditions = 3;
}

// Proposal window state (for debugging/monitoring)
message ProposalWindowState {
    int32 current_window_id = 1;
    string window_state = 2;  // "OPEN", "CLOSING", "RESOLVED"
    int32 proposals_in_window = 3;
    int32 proposals_queued = 4;
    int64 window_start_tick = 5;
    int64 window_close_tick = 6;
}

// Spatial index statistics
message SpatialIndexStats {
    int32 total_objects = 1;
    int32 total_cells = 2;
    int32 occupied_cells = 3;
    float avg_objects_per_cell = 4;
    int32 max_objects_in_cell = 5;
}
```

### API Contract: FateEngineService Extensions

```protobuf
// Additions to fate_engine_service.proto

service FateEngineService {
  // ... existing methods ...
  
  // Phase 2: Query visible objects for an agent
  rpc QueryVisibleObjects (QueryVisibleObjectsRequest) returns (QueryVisibleObjectsResponse);
  
  // Phase 2: Check affordance validity
  rpc ValidateAffordance (ValidateAffordanceRequest) returns (ValidateAffordanceResponse);
  
  // Phase 2: Get spatial query results
  rpc QuerySpatial (QuerySpatialRequest) returns (QuerySpatialResponse);
  
  // Phase 2: Get system stats
  rpc GetSystemStats (GetSystemStatsRequest) returns (GetSystemStatsResponse);
}

message QueryVisibleObjectsRequest {
  string actor_id = 1;
  bool include_details = 2;  // Include affordances, state, etc.
}

message QueryVisibleObjectsResponse {
  repeated tsukuyomi.perception.Percept percepts = 1;
  int32 total_objects = 2;
  int32 visible_objects = 3;
}

message ValidateAffordanceRequest {
  string actor_id = 1;
  string object_id = 2;
  string action_type = 3;
  map<string, string> parameters = 4;
}

message ValidateAffordanceResponse {
  bool is_valid = 1;
  string reason = 2;
  repeated string available_affordances = 3;
}

message QuerySpatialRequest {
  enum QueryType {
    RADIUS = 0;
    NEAREST = 1;
    AABB = 2;
  }
  QueryType query_type = 1;
  string center_object_id = 2;  // For radius/nearest queries
  float radius = 3;  // For radius queries
  int32 limit = 4;  // For nearest queries
  string obj_type_filter = 5;  // Optional type filter
  float aabb_min_x = 6;  // For AABB queries
  float aabb_min_y = 7;
  float aabb_max_x = 8;
  float aabb_max_y = 9;
}

message QuerySpatialResponse {
  repeated string object_ids = 1;
  repeated float distances = 2;  // Distance from center (if applicable)
  int32 total_found = 3;
}

message GetSystemStatsRequest {
  // Empty for now
}

message GetSystemStatsResponse {
  SpatialIndexStats spatial_stats = 1;
  ProposalWindowState window_state = 2;
  int32 current_tick = 3;
  float tick_rate = 4;
}
```

---

## Implementation Roadmap

### Sprint 1: Spatial Index Foundation (Week 1-2)

**Tasks:**
1. Implement `SpatialIndex` class with grid-based hashing
2. Add spatial index integration to `FateEngine.__init__`
3. Implement actor/object registration in spatial index
4. Add spatial collision detection to `_resolve_move`
5. Unit tests for spatial queries (radius, nearest, AABB)

**Acceptance Criteria:**
- All spatial queries meet O(log N) performance target
- 100 agents can query nearby objects in <5ms
- Spatial index statistics are accurate
- All unit tests pass

### Sprint 2: Proposal Window System (Week 3-4)

**Tasks:**
1. Implement `ProposalWindow` class with multi-tick lifecycle
2. Integrate proposal window into FateEngine tick loop
3. Implement `ProposalPrioritizer` for deterministic ordering
4. Update `submit_proposal` to route through window system
5. Add window state monitoring and stats

**Acceptance Criteria:**
- Proposal windows open/close deterministically
- Proposals are correctly queued when window is closed
- Prioritization rules are applied correctly
- Window stats are accurate

### Sprint 3: Affordance System (Week 5-6)

**Tasks:**
1. Implement `ConditionParser` for expression parsing
2. Implement `AffordanceSystem` class
3. Create `StandardAffordances` library
4. Integrate affordance validation into `_resolve_interact`
5. Add affordance loading from object definitions

**Acceptance Criteria:**
- All standard affordances work correctly
- Complex conditions are parsed and evaluated
- Affordance execution produces correct world changes
- Integration tests with FateEngine pass

### Sprint 4: Visual Perception with Raycasting (Week 7-8)

**Tasks:**
1. Implement DDA grid traversal algorithm
2. Implement ray-object intersection logic
3. Implement `VisualPerceptionSystem` class
4. Add occlusion properties to `EnvironmentObject`
5. Integrate visual perception into `AgentBrain`

**Acceptance Criteria:**
- Raycasting correctly identifies visible objects
- Occlusion blocks line of sight as expected
- Perception system meets <50ms performance target
- Agents correctly perceive only visible objects

### Sprint 5: Integration & Testing (Week 9-10)

**Tasks:**
1. Integrate all Phase 2 components
2. End-to-end testing with multi-agent scenarios
3. Performance profiling and optimization
4. Documentation updates
5. Demo scenario preparation

**Acceptance Criteria:**
- All components work together seamlessly
- Performance targets are met
- Documentation is complete and accurate
- Demo scenario showcases all Phase 2 features

---

## Appendix: Example Scenarios

### Scenario 1: Market Crowd Simulation

**Setup:**
- 50 agents in a 100m × 100m market square
- 30 objects (stalls, decorations, obstacles)
- 5 occluding objects (walls, large stalls)

**Behavior:**
- Agents wander using spatial queries for pathfinding
- Agents perceive only visible objects (raycasting)
- Agents interact with stalls using affordance validation
- Multiple agents attempt to collect the same item (proposal window)

**Expected Results:**
- <10ms tick latency with 50 agents
- <50ms perception update per agent
- Realistic occlusion (agents can't see through walls)
- Conflicts resolved via proposal prioritization

### Scenario 2: Stealth Encounter

**Setup:**
- 1 guard agent with 15m vision, 60° FOV
- 1 thief agent attempting to steal an item
- 5 occluding objects (crates, pillars)
- 1 valuable object (treasure chest)

**Behavior:**
- Guard performs raycasting perception every tick
- Thief moves using occluders to stay out of sight
- Thief uses affordance validation to unlock chest
- Guard's perception threshold adjusts based on stealth

**Expected Results:**
- Thief remains undetected when behind occluders
- Thief detected when in guard's line of sight
- Affordance validation correctly checks for lock requirements
- Dynamic tension based on detection risk

### Scenario 3: Combat Coordination

**Setup:**
- 2 opposing teams (5 agents each)
- 10 weapon objects
- 5 occluding objects (cover)
- Proposal window size = 5 ticks

**Behavior:**
- Agents coordinate attacks within proposal windows
- Agents use occluders for cover
- Weapons have affordances (USE, THROW)
- Conflict resolution handles simultaneous actions

**Expected Results:**
- Coordinated multi-tick attacks work correctly
- Cover blocks line of sight and provides protection
- Weapon affordances enable combat mechanics
- Simultaneous actions resolved deterministically

---

**End of Document**
