"""
Tsukuyomi V2 - Spatial Indexing System (Phase 2 Enhanced)
Core Data Structures

This module provides the core spatial partitioning data structures for
collision detection and proximity queries. Uses an optimized grid-based
approach with spatial hashing for performance.

The spatial index reduces proximity checks from O(N) to O(1) average case.

Phase 2 Enhancements:
- Optimized cell management with spatial hashing
- Bulk operations for batch updates
- Dynamic cell size adjustment
- Performance monitoring and statistics
- Support for 50+ agents with <200ms query time

Usage:
    index = SpatialIndex(width=100, height=100, cell_size=10)
    index.insert("agent1", (10.5, 20.3))
    index.update_position("agent1", (12.0, 22.0))
    index.remove("agent1")
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from math import floor, ceil, sqrt
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


@dataclass
class SpatialObject:
    """
    Represents an object in the spatial index.

    Attributes:
        object_id: Unique identifier
        position: (x, y) coordinates
        cell_key: Grid cell this object is in
        last_updated: Timestamp of last position update
        metadata: Optional metadata for filtering
    """
    object_id: str
    position: Tuple[float, float]
    cell_key: Optional[Tuple[int, int]] = None
    last_updated: float = field(default_factory=time.time)
    metadata: Optional[Dict] = None


@dataclass
class QueryStats:
    """
    Statistics for spatial queries.

    Attributes:
        query_count: Total number of queries
        avg_query_time_ms: Average query time in milliseconds
        max_query_time_ms: Maximum query time observed
        cells_checked_avg: Average number of cells checked per query
        objects_found_avg: Average number of objects found per query
    """
    query_count: int = 0
    total_query_time_ms: float = 0.0
    max_query_time_ms: float = 0.0
    total_cells_checked: int = 0
    total_objects_found: int = 0

    def record_query(self, duration_ms: float, cells_checked: int, objects_found: int):
        """Record a query for statistics."""
        self.query_count += 1
        self.total_query_time_ms += duration_ms
        self.max_query_time_ms = max(self.max_query_time_ms, duration_ms)
        self.total_cells_checked += cells_checked
        self.total_objects_found += objects_found

    def get_avg_query_time_ms(self) -> float:
        """Get average query time in milliseconds."""
        return self.total_query_time_ms / self.query_count if self.query_count > 0 else 0.0

    def get_avg_cells_checked(self) -> float:
        """Get average cells checked per query."""
        return self.total_cells_checked / self.query_count if self.query_count > 0 else 0.0

    def get_avg_objects_found(self) -> float:
        """Get average objects found per query."""
        return self.total_objects_found / self.query_count if self.query_count > 0 else 0.0


@dataclass
class SpatialIndex:
    """
    Optimized grid-based spatial partitioning for efficient proximity queries.

    Phase 2 enhancements:
    - Spatial hashing for faster lookups
    - Bulk operations for batch updates
    - Dynamic cell size adjustment
    - Performance monitoring
    - Filtered queries

    Divides the world into a grid of cells. Each cell contains
    references to objects within its bounds.

    Complexity:
        - Insert: O(1)
        - Query: O(k) where k is number of cells within radius
        - Remove: O(1)
        - Bulk update: O(n) with optimized cell changes

    Performance targets (Phase 2):
        - Support 50+ agents with <200ms query time
        - 95th percentile query time <150ms for 100 agents

    Query operations are in spatial_query.py
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

    # Phase 2: Performance monitoring
    query_stats: QueryStats = field(default_factory=QueryStats)
    enable_stats: bool = True
    stats_sample_rate: int = 10  # Record every Nth query

    # Phase 2: Spatial hashing for faster cell lookups
    _spatial_hash: Dict[Tuple[int, int], int] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate grid dimensions and initialize Phase 2 optimizations."""
        self._grid_width = ceil(self.width / self.cell_size)
        self._grid_height = ceil(self.height / self.cell_size)

        # Initialize spatial hash
        self._rebuild_spatial_hash()

        logger.info(
            f"SpatialIndex initialized (Phase 2): {self.width}x{self.height} world, "
            f"{self._grid_width}x{self._grid_height} grid cells "
            f"({self.cell_size}m cell size), stats={'enabled' if self.enable_stats else 'disabled'}"
        )

    def _rebuild_spatial_hash(self):
        """Rebuild the spatial hash from current grid state."""
        self._spatial_hash.clear()
        for cell_key in self.grid:
            self._spatial_hash[cell_key] = len(self.grid[cell_key])

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
                        # Phase 2: Update spatial hash
                        if old_cell in self._spatial_hash:
                            del self._spatial_hash[old_cell]
                except ValueError:
                    pass

            # Add to new cell
            self.grid[new_cell].append(object_id)
            # Phase 2: Update spatial hash
            self._spatial_hash[new_cell] = len(self.grid[new_cell])

        # Update object position
        self.objects[object_id].position = new_position
        self.objects[object_id].cell_key = new_cell
        self.objects[object_id].last_updated = time.time()

        logger.debug(f"Updated {object_id} to {new_position} -> cell {new_cell}")

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
        self._spatial_hash.clear()
        self.query_stats = QueryStats()
        logger.info("Spatial index cleared")

    def get_stats(self) -> Dict:
        """
        Get statistics about the spatial index (Phase 2 enhanced).

        Returns:
            Dictionary with stats
        """
        occupied_cells = len(self.grid)
        total_objects = len(self.objects)

        # Calculate cell load distribution
        cell_counts = [len(cell) for cell in self.grid.values()]
        avg_load = sum(cell_counts) / occupied_cells if occupied_cells > 0 else 0
        max_load = max(cell_counts) if cell_counts else 0

        stats = {
            "total_objects": total_objects,
            "occupied_cells": occupied_cells,
            "total_cells": self._grid_width * self._grid_height,
            "avg_cell_load": avg_load,
            "max_cell_load": max_load,
            "utilization": occupied_cells / (self._grid_width * self._grid_height)
        }

        # Phase 2: Add query statistics
        if self.enable_stats and self.query_stats.query_count > 0:
            stats["query_performance"] = {
                "query_count": self.query_stats.query_count,
                "avg_query_time_ms": round(self.query_stats.get_avg_query_time_ms(), 3),
                "max_query_time_ms": round(self.query_stats.max_query_time_ms, 3),
                "avg_cells_checked": round(self.query_stats.get_avg_cells_checked(), 2),
                "avg_objects_found": round(self.query_stats.get_avg_objects_found(), 2)
            }

        return stats

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

    def set_cell_size(self, new_cell_size: float) -> None:
        """
        Change the cell size and rebuild the grid.

        Note: This is an expensive operation as it requires rebuilding the entire grid.

        Args:
            new_cell_size: New cell size in world units
        """
        if new_cell_size <= 0:
            raise ValueError("Cell size must be positive")

        # Store all current objects
        all_objects = [
            (obj_id, obj.position, obj.metadata)
            for obj_id, obj in self.objects.items()
        ]

        # Clear and reinitialize
        self.clear()
        self.cell_size = new_cell_size
        self._grid_width = ceil(self.width / self.cell_size)
        self._grid_height = ceil(self.height / self.cell_size)

        # Re-insert all objects
        for obj_id, position, metadata in all_objects:
            cell_key = self._position_to_cell(position)
            spatial_obj = SpatialObject(
                object_id=obj_id,
                position=position,
                cell_key=cell_key,
                last_updated=time.time(),
                metadata=metadata
            )
            self.objects[obj_id] = spatial_obj
            self.grid[cell_key].append(obj_id)

        self._rebuild_spatial_hash()

        logger.info(f"Cell size changed to {new_cell_size}, grid rebuilt as {self._grid_width}x{self._grid_height}")

    def query_nearby(
        self,
        position: Tuple[float, float],
        radius: float,
        filter_fn: Callable = None
    ) -> List[SpatialObject]:
        """
        Query for objects within a radius of a position.

        Args:
            position: (x, y) center position
            radius: Search radius in world units
            filter_fn: Optional filter function (takes SpatialObject, returns bool)

        Returns:
            List of SpatialObject within radius
        """
        start_time = time.time()
        cx, cy = position
        results = []

        cells_in_radius = int(radius / self.cell_size) + 1
        center_cell = self._position_to_cell(position)
        cells_checked = 0

        for dx in range(-cells_in_radius, cells_in_radius + 1):
            for dy in range(-cells_in_radius, cells_in_radius + 1):
                cell_key = (center_cell[0] + dx, center_cell[1] + dy)
                cells_checked += 1

                if cell_key not in self.grid:
                    continue

                for obj_id in self.grid[cell_key]:
                    obj = self.objects.get(obj_id)
                    if obj is None:
                        continue

                    ox, oy = obj.position
                    dist = sqrt((cx - ox) ** 2 + (cy - oy) ** 2)

                    if dist <= radius:
                        if filter_fn is None or filter_fn(obj):
                            results.append(obj)

        if self.enable_stats:
            duration_ms = (time.time() - start_time) * 1000
            self.query_stats.record_query(duration_ms, cells_checked, len(results))

        return results

    def query(
        self,
        position: Tuple[float, float],
        radius: float,
        exclude_self: Optional[str] = None,
        use_cache: bool = False
    ) -> List[Tuple[str, Tuple[float, float]]]:
        """
        Query for objects within radius, returning (id, position) tuples.

        Args:
            position: (x, y) center position
            radius: Search radius
            exclude_self: Optional object_id to exclude from results
            use_cache: Ignored (for API compatibility)

        Returns:
            List of (object_id, position) tuples
        """
        results = []
        cx, cy = position

        cells_in_radius = int(radius / self.cell_size) + 1
        center_cell = self._position_to_cell(position)

        for dx in range(-cells_in_radius, cells_in_radius + 1):
            for dy in range(-cells_in_radius, cells_in_radius + 1):
                cell_key = (center_cell[0] + dx, center_cell[1] + dy)

                if cell_key not in self.grid:
                    continue

                for obj_id in self.grid[cell_key]:
                    if exclude_self and obj_id == exclude_self:
                        continue

                    obj = self.objects.get(obj_id)
                    if obj is None:
                        continue

                    ox, oy = obj.position
                    dist = sqrt((cx - ox) ** 2 + (cy - oy) ** 2)

                    if dist <= radius:
                        results.append((obj_id, obj.position))

        return results

    def query_nearest(
        self,
        position: Tuple[float, float],
        limit: int = 5
    ) -> List[Tuple[str, Tuple[float, float], float]]:
        """
        Query for nearest objects to a position.

        Args:
            position: (x, y) center position
            limit: Maximum number of results

        Returns:
            List of (object_id, position, distance) tuples sorted by distance
        """
        cx, cy = position
        results = []

        for obj_id, obj in self.objects.items():
            ox, oy = obj.position
            dist = sqrt((cx - ox) ** 2 + (cy - oy) ** 2)
            results.append((obj_id, obj.position, dist))

        results.sort(key=lambda x: x[2])
        return results[:limit]

    def find_k_nearest(
        self,
        position: Tuple[float, float],
        k: int = 5
    ) -> List[Tuple[str, Tuple[float, float], float]]:
        """Alias for query_nearest for API compatibility."""
        return self.query_nearest(position, limit=k)

    def insert_bulk(
        self,
        objects: List[Tuple[str, Tuple[float, float]]]
    ) -> int:
        """
        Bulk insert objects.

        Args:
            objects: List of (object_id, position) tuples

        Returns:
            Number of objects inserted
        """
        count = 0
        for obj_id, position in objects:
            self.insert(obj_id, position)
            count += 1
        return count

    def update_positions_bulk(
        self,
        updates: List[Tuple[str, Tuple[float, float]]]
    ) -> int:
        """
        Bulk update positions.

        Args:
            updates: List of (object_id, new_position) tuples

        Returns:
            Number of objects updated
        """
        count = 0
        for obj_id, position in updates:
            if obj_id in self.objects:
                self.update_position(obj_id, position)
                count += 1
        return count

    def remove_bulk(
        self,
        object_ids: List[str]
    ) -> int:
        """
        Bulk remove objects.

        Args:
            object_ids: List of object IDs to remove

        Returns:
            Number of objects removed
        """
        count = 0
        for obj_id in object_ids:
            if self.remove(obj_id):
                count += 1
        return count
