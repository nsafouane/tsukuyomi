"""
PHASE 11: Multi-Room Spatial Logic
===================================

Manages spatial partitioning of the world into rooms, portal connections,
and basic collision/occlusion logic for agent movement.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("SpatialLogic")

@dataclass
class Portal:
    """A connection between two rooms (doorway, archway, gate)."""
    portal_id: str
    source_room_id: str
    target_room_id: str
    position: Tuple[float, float]  # x, y in source room
    size: float = 1.0  # Width of the doorway (collision radius)
    locked: bool = False

@dataclass
class Room:
    """A defined physical space with boundaries and potential occlusions."""
    room_id: str
    name: str
    description: str
    # Simple bounding box for MVP: x_min, x_max, y_min, y_max
    boundaries: Dict[str, float] = field(default_factory=lambda: {
        'x_min': 0.0, 'x_max': 20.0, 'y_min': 0.0, 'y_max': 20.0
    })
    portals: List[Portal] = field(default_factory=list)
    occlusions: List[Tuple[float, float, float]] = field(default_factory=list) # x, y, radius

class SpatialLogic:
    """
    Manages multi-room spatial partitioning and movement validation.
    
    Responsibilities:
    - Room registry and boundary enforcement
    - Portal traversal logic
    - Basic collision checks (wall avoidance)
    - Line-of-sight occlusion (MVP: simple distance/object check)
    """
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.portals_by_room: Dict[str, List[Portal]] = {}

    def add_room(self, room: Room):
        """Register a new room in the world."""
        self.rooms[room.room_id] = room
        self.portals_by_room[room.room_id] = room.portals
        logger.info(f"[SpatialLogic] Added room: {room.name} ({room.room_id})")
        logger.debug(f"  Boundaries: {room.boundaries}")
        logger.debug(f"  Portals: {len(room.portals)}")

    def add_portal(self, portal: Portal):
        """Add a portal to a specific room."""
        if portal.source_room_id not in self.rooms:
            logger.warning(f"Cannot add portal to unknown room: {portal.source_room_id}")
            return

        source_room = self.rooms[portal.source_room_id]
        source_room.portals.append(portal)
        
        if portal.source_room_id not in self.portals_by_room:
            self.portals_by_room[portal.source_room_id] = []
        self.portals_by_room[portal.source_room_id].append(portal)
        
        logger.info(f"[SpatialLogic] Added portal: {portal.portal_id} ({portal.source_room_id} -> {portal.target_room_id})")

    def can_move_to(self, room_id: str, target_pos: Tuple[float, float], radius: float = 0.5) -> bool:
        """
        Check if a position is within the bounds of the current room 
        and not colliding with occlusions.
        """
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        x, y = target_pos
        
        # 1. Boundary Check (with margin for agent radius)
        if not (room.boundaries['x_min'] + radius <= x <= room.boundaries['x_max'] - radius and
                room.boundaries['y_min'] + radius <= y <= room.boundaries['y_max'] - radius):
            return False
            
        # 2. Occlusion/Collision Check (MVP: Circle-circle collision)
        for ox, oy, orad in room.occlusions:
            dist_sq = (x - ox)**2 + (y - oy)**2
            min_dist = radius + orad
            if dist_sq < min_dist**2:
                return False # Collision detected
            
        return True

    def get_portal_at(self, room_id: str, position: Tuple[float, float]) -> Optional[Portal]:
        """
        Check if a position intersects with a portal.
        Returns the Portal object if found, None otherwise.
        """
        if room_id not in self.portals_by_room:
            return None
        
        x, y = position
        for portal in self.portals_by_room[room_id]:
            px, py = portal.position
            # Distance check
            dist_sq = (x - px)**2 + (y - py)**2
            if dist_sq <= (portal.size / 2)**2:
                return portal
        
        return None

    def attempt_move_through_portal(self, room_id: str, position: Tuple[float, float]) -> Optional[str]:
        """
        Attempt to move through a portal. 
        Returns the new room_id if successful, None otherwise.
        """
        portal = self.get_portal_at(room_id, position)
        
        if portal and not portal.locked:
            # Verify target room exists
            if portal.target_room_id in self.rooms:
                return portal.target_room_id
            else:
                logger.warning(f"Portal {portal.portal_id} leads to non-existent room {portal.target_room_id}")
        
        return None

    def get_initial_position(self, room_id: str) -> Tuple[float, float]:
        """Get a default spawn position for a room (center)."""
        if room_id in self.rooms:
            r = self.rooms[room_id]
            return (
                (r.boundaries['x_min'] + r.boundaries['x_max']) / 2,
                (r.boundaries['y_min'] + r.boundaries['y_max']) / 2
            )
        return (0.0, 0.0)

    def is_visible(self, room_id: str, pos_a: Tuple[float, float], pos_b: Tuple[float, float]) -> bool:
        """
        MVP Visibility Check: 
        Returns False if an occlusion exists directly between points.
        (Simplified implementation for Phase 11 MVP)
        """
        if room_id not in self.rooms:
            return True # Assume visible if room unknown
        
        room = self.rooms[room_id]
        
        # Simple check: is point B inside an occlusion object?
        bx, by = pos_b
        for ox, oy, orad in room.occlusions:
            dist_sq = (bx - ox)**2 + (by - oy)**2
            if dist_sq < orad**2:
                return False # B is inside a wall/occlusion
        
        return True
