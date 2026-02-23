"""
PerceptionPipeline - Phase 2.1: Perception Foundation

Implements the Perception Layer for Tsukuyomi agents:
- Sensory channels (vision, hearing, proprioception, memory echoes)
- Staggered Perception Schedule (rotating deep perception ticks)
- Salience scoring with Surprise Factor (detecting Memory Echo violations)
- Memory Echo tracking for last-known positions
- Raycasting for line-of-sight and field-of-view
- Spatial Index integration for efficient proximity detection

Reference:
- PHASE_2_SPEC.md §3: Module 1: The Perception Layer
- PHASE_2_REVIEW_SUMMARY.md: Staggered Perception Schedule & Surprise Factor
"""

import math
import uuid
import random
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

from tsukuyomi.transport.proto import core_pb2
from tsukuyomi.transport.proto import perception_pb2
from tsukuyomi.transport.proto import common_pb2

logger = logging.getLogger("PerceptionPipeline")


@dataclass
class SensoryProfile:
    """Configuration for an agent's sensory capabilities."""

    vision_range: float = 20.0  # Max vision distance (meters)
    vision_fov: float = 120.0  # Field of view in degrees
    hearing_range: float = 15.0  # Max hearing distance (meters)
    vision_certainty_decay: float = 0.1  # How fast visual certainty decays per meter
    hearing_certainty_decay: float = (
        0.15  # How fast auditory certainty decays per meter
    )


@dataclass
class AgentInternalState:
    """Simplified agent internal state for perception calculations."""

    current_concerns: List[str]  # Topics the agent is concerned about
    mood_label: str  # "frustrated", "anxious", "calm", etc.
    arousal: float  # 0.0 - 1.0
    last_seen_entities: Dict[str, int]  # entity_id -> last_seen_tick
    facing_direction: Optional[Tuple[float, float]] = None  # (dx, dy) normalized


@dataclass
class Wall:
    """Represents a wall or occluding obstacle for raycasting."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    thickness: float = 0.5  # Wall thickness for collision
    transparent: bool = False  # Whether the wall blocks vision


class Raycaster:
    """
    Implements raycasting for line-of-sight and field-of-view calculations.

    Uses Bresenham-like line sampling combined with segment intersection
    for efficient and accurate line-of-sight determination.
    """

    def __init__(self, spatial_index=None):
        """
        Initialize the raycaster.

        Args:
            spatial_index: Optional SpatialIndex instance for spatial queries
        """
        self.spatial_index = spatial_index
        self.walls: Dict[str, List[Wall]] = {}  # room_id -> list of walls

    def register_room_walls(self, room_id: str, walls: List[Wall]) -> None:
        """
        Register walls for a specific room.

        Args:
            room_id: Room identifier
            walls: List of Wall objects in this room
        """
        self.walls[room_id] = walls
        logger.debug(f"Registered {len(walls)} walls for room {room_id}")

    def cast_ray(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        room_id: Optional[str] = None,
        max_distance: Optional[float] = None,
        step_size: float = 0.5,
    ) -> Tuple[bool, Optional[Tuple[float, float]], float]:
        """
        Cast a ray from start to end and check for wall intersections.

        Args:
            start: Ray origin (x, y)
            end: Ray destination (x, y)
            room_id: Room to check walls in (None = check all)
            max_distance: Maximum ray distance (None = use distance to end)
            step_size: Step size for ray marching (meters)

        Returns:
            (is_blocked, intersection_point, distance_traveled)
            - is_blocked: True if ray hit a wall
            - intersection_point: (x, y) of first intersection or None
            - distance_traveled: Total distance from start to end/intersection
        """
        sx, sy = start
        ex, ey = end

        # Calculate ray direction
        dx = ex - sx
        dy = ey - sy
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return False, None, 0.0

        # Apply max distance limit
        if max_distance is not None and distance > max_distance:
            distance = max_distance
            ex = sx + (dx / distance) * max_distance
            ey = sy + (dy / distance) * max_distance

        # Normalize direction
        dir_x = dx / distance
        dir_y = dy / distance

        # Step along the ray
        current_distance = 0.0
        steps = int(distance / step_size) + 1

        for step in range(steps):
            # Current point along ray
            if step == steps - 1:
                # Last step: use exact end position
                current_x = ex
                current_y = ey
            else:
                current_x = sx + dir_x * (step * step_size)
                current_y = sy + dir_y * (step * step_size)

            current_distance = (
                ((current_x - sx) ** 2 + (current_y - sy) ** 2) ** 0.5
            )

            # Check for wall intersection at current position
            for rid, walls in self.walls.items():
                if room_id is not None and rid != room_id:
                    continue

                for wall in walls:
                    if wall.transparent:
                        continue

                    # Quick distance check to wall (bounding box)
                    wx1, wy1 = wall.start
                    wx2, wy2 = wall.end

                    # Wall center and radius for quick check
                    wall_cx = (wx1 + wx2) / 2
                    wall_cy = (wy1 + wy2) / 2
                    wall_length = math.sqrt((wx2 - wx1) ** 2 + (wy2 - wy1) ** 2)
                    wall_radius = wall_length / 2 + wall.thickness

                    # Distance from current point to wall center
                    dist_to_wall = math.sqrt(
                        (current_x - wall_cx) ** 2 + (current_y - wall_cy) ** 2
                    )

                    if dist_to_wall > wall_radius:
                        continue

                    # Precise line segment intersection
                    intersection = self._line_intersection(
                        (sx, sy), (current_x, current_y), wall.start, wall.end
                    )

                    if intersection is not None:
                        return True, intersection, current_distance

        return False, None, distance

    def cast_cone(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        fov_degrees: float,
        max_distance: float,
        room_id: Optional[str] = None,
        num_rays: int = 16,
    ) -> List[Tuple[float, float, float]]:
        """
        Cast multiple rays in a cone (field of view).

        Args:
            origin: Cone origin (x, y)
            direction: Direction vector (dx, dy) (will be normalized)
            fov_degrees: Field of view angle in degrees
            max_distance: Maximum ray distance
            room_id: Room to check walls in
            num_rays: Number of rays to cast

        Returns:
            List of (x, y, distance) tuples for ray endpoints
        """
        # Normalize direction
        dir_mag = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
        if dir_mag == 0:
            direction = (1.0, 0.0)
        else:
            direction = (direction[0] / dir_mag, direction[1] / dir_mag)

        # Calculate base angle
        base_angle = math.atan2(direction[1], direction[0])

        # Convert FOV to radians
        fov_rad = math.radians(fov_degrees)
        half_fov = fov_rad / 2

        results = []
        step = fov_rad / (num_rays - 1) if num_rays > 1 else 0

        for i in range(num_rays):
            # Calculate ray angle
            if num_rays == 1:
                ray_angle = base_angle
            else:
                ray_angle = base_angle - half_fov + (i * step)

            # Ray direction
            ray_dir = (math.cos(ray_angle), math.sin(ray_angle))

            # Calculate ray end point
            end_x = origin[0] + ray_dir[0] * max_distance
            end_y = origin[1] + ray_dir[1] * max_distance

            # Cast ray
            blocked, intersection, distance = self.cast_ray(
                origin, (end_x, end_y), room_id, max_distance
            )

            if blocked and intersection is not None:
                results.append((intersection[0], intersection[1], distance))
            else:
                results.append((end_x, end_y, max_distance))

        return results

    def get_visible_polygon(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        fov_degrees: float,
        max_distance: float,
        room_id: Optional[str] = None,
        num_rays: int = 32,
    ) -> List[Tuple[float, float]]:
        """
        Get the visible polygon (shape) of the agent's field of view.

        Args:
            origin: Agent position (x, y)
            direction: Facing direction (dx, dy)
            fov_degrees: Field of view angle
            max_distance: Maximum vision range
            room_id: Room to check walls in
            num_rays: Number of rays for polygon approximation

        Returns:
            List of (x, y) vertices forming the visible polygon
        """
        # Cast rays in cone
        ray_results = self.cast_cone(
            origin, direction, fov_degrees, max_distance, room_id, num_rays
        )

        # Build polygon: origin + all ray endpoints + back to origin
        polygon = [origin]
        for x, y, _ in ray_results:
            polygon.append((x, y))

        return polygon

    def is_point_visible(
        self,
        observer_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        room_id: Optional[str] = None,
        step_size: float = 0.5,
    ) -> bool:
        """
        Check if a target point is visible from observer position.

        Args:
            observer_pos: Observer position (x, y)
            target_pos: Target position (x, y)
            room_id: Room to check walls in
            step_size: Step size for ray marching

        Returns:
            True if visible (no walls blocking), False otherwise
        """
        blocked, _, _ = self.cast_ray(
            observer_pos, target_pos, room_id, step_size=step_size
        )
        return not blocked

    def _line_intersection(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float],
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate intersection point of two line segments.

        Args:
            p1, p2: First line segment endpoints
            p3, p4: Second line segment endpoints

        Returns:
            (x, y) intersection point or None if no intersection
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        # Calculate denominators
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)

        if denom == 0:
            # Lines are parallel
            return None

        # Calculate intersection point
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

        # Check if intersection is within both line segments
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            ix = x1 + ua * (x2 - x1)
            iy = y1 + ua * (y2 - y1)
            return (ix, iy)

        return None


