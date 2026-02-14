"""
Tsukuyomi V2 - Spatial Indexing System

This module provides efficient spatial partitioning for collision detection
and proximity queries. Uses a grid-based approach for MVP simplicity,
upgradeable to Quadtree for larger scales.

The spatial index reduces proximity checks from O(N) to O(1) average case.

Usage:
    index = SpatialIndex(width=100, height=100, cell_size=10)
    index.insert("agent1", (10.5, 20.3))
    nearby = index.query((15, 20), radius=5.0)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from math import floor, ceil
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SpatialObject:
    """
    Represents an object in the spatial index.

    Attributes:
        object_id: Unique identifier
        position: (x, y) coordinates
        cell_key: Grid cell this object is in
    """
    object_id: str
    position: Tuple[float, float]
    cell_key: Optional[Tuple[int, int]] = None


@dataclass
class SpatialIndex:
    """
    Grid-based spatial partitioning for efficient proximity queries.

    Divides the world into a grid of cells. Each cell contains
    references to objects within its bounds.

    Complexity:
        - Insert: O(1)
        - Query: O(k) where k is number of cells within radius
        - Remove: O(1)
    """

    # World dimensions
    width: float
    height: float

    # Grid cell size (smaller = more precise, higher memory)
    cell_size: float = 10.0

    # Grid: (cell_x, cell_y) -> List[object_id]
    grid: Dict[Tuple[int, int], List[str]] = field(default_factory=lambda: defaultdict(list))

    # Reverse lookup: object_id -> SpatialObject
    objects: Dict[str, SpatialObject] = field(default_factory=dict)

    # Grid dimensions (calculated)
    _grid_width: int = field(init=False)
    _grid_height: int = field(init=False)

    def __post_init__(self):
        """Calculate grid dimensions."""
        self._grid_width = ceil(self.width / self.cell_size)
        self._grid_height = ceil(self.height / self.cell_size)
        logger.info(
            f"SpatialIndex initialized: {self.width}x{self.height} world, "
            f"{self._grid_width}x{self._grid_height} grid cells "
            f"({self.cell_size}m cell size)"
        )

    def _position_to_cell(self, position: Tuple[float, float]) -> Tuple[int, int]:
        """
        Convert world position to grid cell coordinates.

        Args:
            position: (x, y) world coordinates

        Returns:
            (cell_x, cell_y) grid coordinates
        """
        x, y = position
        cell_x = floor(x / self.cell_size)
        cell_y = floor(y / self.cell_size)
        return (int(cell_x), int(cell_y))

    def _is_valid_cell(self, cell_x: int, cell_y: int) -> bool:
        """
        Check if cell coordinates are within grid bounds.

        Args:
            cell_x: Grid X coordinate
            cell_y: Grid Y coordinate

        Returns:
            True if valid, False otherwise
        """
        return 0 <= cell_x < self._grid_width and 0 <= cell_y < self._grid_height

    def insert(
        self,
        object_id: str,
        position: Tuple[float, float],
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Insert or update an object in the spatial index.

        Args:
            object_id: Unique identifier for the object
            position: (x, y) world coordinates
            metadata: Optional metadata to store with object
        """
        # Remove if already exists
        if object_id in self.objects:
            self.remove(object_id)

        # Get cell key
        cell_x, cell_y = self._position_to_cell(position)

        # Create spatial object
        spatial_obj = SpatialObject(
            object_id=object_id,
            position=position,
            cell_key=(cell_x, cell_y)
        )
        self.objects[object_id] = spatial_obj

        # Add to grid
        cell_key = (cell_x, cell_y)
        self.grid[cell_key].append(object_id)

        logger.debug(f"Inserted object {object_id} at {position} -> cell {cell_key}")

    def remove(self, object_id: str) -> bool:
        """
        Remove an object from the spatial index.

        Args:
            object_id: Object to remove

        Returns:
            True if removed, False if not found
        """
        if object_id not in self.objects:
            logger.warning(f"Object {object_id} not found in spatial index")
            return False

        spatial_obj = self.objects[object_id]
        cell_key = spatial_obj.cell_key

        if cell_key and cell_key in self.grid:
            # Remove from grid cell
            cell_list = self.grid[cell_key]
            try:
                cell_list.remove(object_id)
                if not cell_list:
                    del self.grid[cell_key]
            except ValueError:
                logger.warning(
                    f"Object {object_id} not found in cell {cell_key}"
                )

        # Remove from objects dict
        del self.objects[object_id]

        logger.debug(f"Removed object {object_id}")
        return True

    def update_position(
        self,
        object_id: str,
        new_position: Tuple[float, float]
    ) -> None:
        """
        Update an object's position.

        Args:
            object_id: Object to update
            new_position: New (x, y) coordinates
        """
        if object_id not in self.objects:
            logger.warning(f"Cannot update unknown object {object_id}")
            return

        old_cell = self.objects[object_id].cell_key
        new_cell = self._position_to_cell(new_position)

        # If cell changed, update grid
        if old_cell != new_cell:
            # Remove from old cell
            if old_cell and old_cell in self.grid:
                try:
                    self.grid[old_cell].remove(object_id)
                    if not self.grid[old_cell]:
                        del self.grid[old_cell]
                except ValueError:
                    pass

            # Add to new cell
            self.grid[new_cell].append(object_id)

        # Update object position
        self.objects[object_id].position = new_position
        self.objects[object_id].cell_key = new_cell

        logger.debug(f"Updated {object_id} to {new_position} -> cell {new_cell}")

    def query(
        self,
        position: Tuple[float, float],
        radius: float,
        exclude_self: Optional[str] = None
    ) -> List[Tuple[str, Tuple[float, float]]]:
        """
        Query for objects within radius of position.

        Args:
            position: Center position for query (x, y)
            radius: Query radius in world units
            exclude_self: Object ID to exclude from results

        Returns:
            List of (object_id, position) tuples within radius
        """
        results = []
        center_x, center_y = position

        # Calculate affected cells
        cell_radius = ceil(radius / self.cell_size)
        center_cell = self._position_to_cell(position)
        cx, cy = center_cell

        # Iterate over affected cells
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cell_x = cx + dx
                cell_y = cy + dy

                if not self._is_valid_cell(cell_x, cell_y):
                    continue

                cell_key = (cell_x, cell_y)
                if cell_key not in self.grid:
                    continue

                # Check objects in this cell
                for obj_id in self.grid[cell_key]:
                    if obj_id == exclude_self:
                        continue

                    # Get actual position
                    spatial_obj = self.objects.get(obj_id)
                    if not spatial_obj:
                        continue

                    # Calculate distance
                    obj_x, obj_y = spatial_obj.position
                    distance = ((obj_x - center_x)**2 + (obj_y - center_y)**2)**0.5

                    if distance <= radius:
                        results.append((obj_id, spatial_obj.position))

        logger.debug(f"Query at {position} radius {radius} found {len(results)} objects")
        return results

    def query_nearest(
        self,
        position: Tuple[float, float],
        limit: int = 5,
        exclude_self: Optional[str] = None
    ) -> List[Tuple[str, Tuple[float, float], float]]:
        """
        Query for nearest objects to position.

        Args:
            position: Center position for query (x, y)
            limit: Maximum number of results
            exclude_self: Object ID to exclude

        Returns:
            List of (object_id, position, distance) tuples, sorted by distance
        """
        # Use a larger radius to get candidates
        candidates = self.query(
            position,
            radius=min(self.width, self.height) * 0.5,
            exclude_self=exclude_self
        )

        # Sort by distance
        center_x, center_y = position
        candidates_with_distance = []

        for obj_id, obj_pos in candidates:
            obj_x, obj_y = obj_pos
            distance = ((obj_x - center_x)**2 + (obj_y - center_y)**2)**0.5
            candidates_with_distance.append((obj_id, obj_pos, distance))

        # Sort and limit
        candidates_with_distance.sort(key=lambda x: x[2])
        return candidates_with_distance[:limit]

    def get_object_position(self, object_id: str) -> Optional[Tuple[float, float]]:
        """
        Get an object's position.

        Args:
            object_id: Object to query

        Returns:
            (x, y) position or None if not found
        """
        spatial_obj = self.objects.get(object_id)
        if spatial_obj:
            return spatial_obj.position
        return None

    def clear(self) -> None:
        """Clear all objects from the spatial index."""
        self.grid.clear()
        self.objects.clear()
        logger.info("Spatial index cleared")

    def get_stats(self) -> Dict:
        """
        Get statistics about the spatial index.

        Returns:
            Dictionary with stats
        """
        occupied_cells = len(self.grid)
        total_objects = len(self.objects)

        # Calculate cell load distribution
        cell_counts = [len(cell) for cell in self.grid.values()]
        avg_load = sum(cell_counts) / occupied_cells if occupied_cells > 0 else 0
        max_load = max(cell_counts) if cell_counts else 0

        return {
            "total_objects": total_objects,
            "occupied_cells": occupied_cells,
            "total_cells": self._grid_width * self._grid_height,
            "avg_cell_load": avg_load,
            "max_cell_load": max_load,
            "utilization": occupied_cells / (self._grid_width * self._grid_height)
        }

    def to_dict(self) -> Dict:
        """Serialize spatial index to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "grid_width": self._grid_width,
            "grid_height": self._grid_height,
            "object_count": len(self.objects),
            "stats": self.get_stats()
        }
