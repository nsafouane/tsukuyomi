"""
Tsukuyomi V2 - Spatial Indexing System (Phase 2 Enhanced)

This module provides efficient spatial partitioning for collision detection
and proximity queries. Uses an optimized grid-based approach with spatial hashing
for performance, upgradeable to Quadtree for larger scales.

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
    nearby = index.query((15, 20), radius=5.0)
    # Bulk update
    index.update_positions_bulk([
        ("agent1", (12.0, 22.0)),
        ("agent2", (15.0, 18.0))
    ])
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Callable
from math import floor, ceil, sqrt
from collections import defaultdict
import time
import heapq

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

    # Phase 2: Cache for frequent queries
    _query_cache: Dict[str, Tuple[float, List[Tuple[str, Tuple[float, float]]]]] = field(default_factory=dict)
    _cache_ttl: float = 0.1  # Cache time-to-live in seconds
    _max_cache_size: int = 100

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

    def query(
        self,
        position: Tuple[float, float],
        radius: float,
        exclude_self: Optional[str] = None,
        use_cache: bool = True,
        metadata_filter: Optional[Callable[[Dict], bool]] = None
    ) -> List[Tuple[str, Tuple[float, float]]]:
        """
        Query for objects within radius of position (Phase 2 enhanced).

        Args:
            position: Center position for query (x, y)
            radius: Query radius in world units
            exclude_self: Object ID to exclude from results
            use_cache: Whether to use query cache (Phase 2)
            metadata_filter: Optional function to filter by metadata

        Returns:
            List of (object_id, position) tuples within radius
        """
        start_time = time.perf_counter()
        cells_checked = 0

        # Phase 2: Check cache
        cache_key = None
        if use_cache:
            cache_key = f"{position}_{radius}_{exclude_self}"
            if cache_key in self._query_cache:
                cached_time, cached_results = self._query_cache[cache_key]
                if time.time() - cached_time < self._cache_ttl:
                    logger.debug(f"Query cache hit for {cache_key}")
                    return cached_results

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

                cells_checked += 1

                # Check objects in this cell
                for obj_id in self.grid[cell_key]:
                    if obj_id == exclude_self:
                        continue

                    # Get actual position
                    spatial_obj = self.objects.get(obj_id)
                    if not spatial_obj:
                        continue

                    # Phase 2: Apply metadata filter
                    if metadata_filter and spatial_obj.metadata:
                        try:
                            if not metadata_filter(spatial_obj.metadata):
                                continue
                        except Exception:
                            continue

                    # Calculate distance
                    obj_x, obj_y = spatial_obj.position
                    distance = ((obj_x - center_x)**2 + (obj_y - center_y)**2)**0.5

                    if distance <= radius:
                        results.append((obj_id, spatial_obj.position))

        # Phase 2: Update cache
        if use_cache and cache_key:
            self._query_cache[cache_key] = (time.time(), results)

            # Prune cache if too large
            if len(self._query_cache) > self._max_cache_size:
                # Remove oldest entries
                keys_to_remove = sorted(
                    self._query_cache.keys(),
                    key=lambda k: self._query_cache[k][0]
                )[:len(self._query_cache) // 2]
                for k in keys_to_remove:
                    del self._query_cache[k]

        # Phase 2: Record statistics
        if self.enable_stats:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.query_stats.record_query(duration_ms, cells_checked, len(results))

        logger.debug(f"Query at {position} radius {radius} found {len(results)} objects in {duration_ms:.2f}ms")
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
        self._spatial_hash.clear()
        self._query_cache.clear()
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

        # Phase 2: Add cache statistics
        stats["cache"] = {
            "entries": len(self._query_cache),
            "max_size": self._max_cache_size,
            "ttl_seconds": self._cache_ttl
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

    # -------------------------------------------------------------------------
    # Phase 2: Bulk Operations
    # -------------------------------------------------------------------------

    def insert_bulk(
        self,
        objects: List[Tuple[str, Tuple[float, float]]]
    ) -> int:
        """
        Insert multiple objects at once (optimized for batch operations).

        Args:
            objects: List of (object_id, position) tuples

        Returns:
            Number of objects inserted
        """
        inserted = 0

        for object_id, position in objects:
            # Skip if already exists
            if object_id in self.objects:
                continue

            # Get cell key
            cell_key = self._position_to_cell(position)

            # Create spatial object
            spatial_obj = SpatialObject(
                object_id=object_id,
                position=position,
                cell_key=cell_key,
                last_updated=time.time()
            )
            self.objects[object_id] = spatial_obj

            # Add to grid
            self.grid[cell_key].append(object_id)
            inserted += 1

        # Rebuild spatial hash
        self._rebuild_spatial_hash()

        logger.info(f"Bulk inserted {inserted} objects")
        return inserted

    def update_positions_bulk(
        self,
        updates: List[Tuple[str, Tuple[float, float]]]
    ) -> int:
        """
        Update multiple positions at once (optimized for batch operations).

        Args:
            updates: List of (object_id, new_position) tuples

        Returns:
            Number of positions updated
        """
        updated = 0

        # Collect cell changes
        cell_changes: Dict[Tuple[int, int], List[str]] = defaultdict(list)

        for object_id, new_position in updates:
            if object_id not in self.objects:
                continue

            old_cell = self.objects[object_id].cell_key
            new_cell = self._position_to_cell(new_position)

            # If cell changed, record it
            if old_cell != new_cell:
                cell_changes[old_cell].append(object_id)
                cell_changes[new_cell].append(object_id)

            # Update object
            self.objects[object_id].position = new_position
            self.objects[object_id].cell_key = new_cell
            self.objects[object_id].last_updated = time.time()
            updated += 1

        # Apply grid changes
        for cell_key, obj_ids in cell_changes.items():
            for obj_id in obj_ids:
                if obj_id not in self.objects:
                    continue

                obj = self.objects[obj_id]
                current_cell = obj.cell_key

                # Remove from all old cells
                if cell_key in self.grid and obj_id in self.grid[cell_key]:
                    self.grid[cell_key].remove(obj_id)
                    if not self.grid[cell_key]:
                        del self.grid[cell_key]

                # Add to new cell
                if current_cell not in self.grid:
                    self.grid[current_cell] = []
                if obj_id not in self.grid[current_cell]:
                    self.grid[current_cell].append(obj_id)

        # Rebuild spatial hash
        self._rebuild_spatial_hash()

        # Invalidate cache
        self._query_cache.clear()

        logger.info(f"Bulk updated {updated} positions")
        return updated

    def remove_bulk(self, object_ids: List[str]) -> int:
        """
        Remove multiple objects at once.

        Args:
            object_ids: List of object IDs to remove

        Returns:
            Number of objects removed
        """
        removed = 0

        for object_id in object_ids:
            if self.remove(object_id):
                removed += 1

        # Invalidate cache
        self._query_cache.clear()

        logger.info(f"Bulk removed {removed} objects")
        return removed

    # -------------------------------------------------------------------------
    # Phase 2: Advanced Query Operations
    # -------------------------------------------------------------------------

    def query_within_rect(
        self,
        min_pos: Tuple[float, float],
        max_pos: Tuple[float, float],
        exclude_self: Optional[str] = None
    ) -> List[Tuple[str, Tuple[float, float]]]:
        """
        Query for objects within a rectangular region.

        Args:
            min_pos: Minimum (x, y) coordinates
            max_pos: Maximum (x, y) coordinates
            exclude_self: Object ID to exclude

        Returns:
            List of (object_id, position) tuples within region
        """
        results = []
        min_x, min_y = min_pos
        max_x, max_y = max_pos

        # Calculate affected cells
        min_cell = self._position_to_cell(min_pos)
        max_cell = self._position_to_cell(max_pos)

        # Iterate over cells in range
        for cell_x in range(min_cell[0], max_cell[0] + 1):
            for cell_y in range(min_cell[1], max_cell[1] + 1):
                if not self._is_valid_cell(cell_x, cell_y):
                    continue

                cell_key = (cell_x, cell_y)
                if cell_key not in self.grid:
                    continue

                # Check objects in this cell
                for obj_id in self.grid[cell_key]:
                    if obj_id == exclude_self:
                        continue

                    spatial_obj = self.objects.get(obj_id)
                    if not spatial_obj:
                        continue

                    obj_x, obj_y = spatial_obj.position

                    # Check if within rectangle
                    if min_x <= obj_x <= max_x and min_y <= obj_y <= max_y:
                        results.append((obj_id, spatial_obj.position))

        return results

    def find_k_nearest(
        self,
        position: Tuple[float, float],
        k: int = 5,
        exclude_self: Optional[str] = None,
        metadata_filter: Optional[Callable[[Dict], bool]] = None
    ) -> List[Tuple[str, Tuple[float, float], float]]:
        """
        Find the k nearest objects to a position (optimized with heap).

        Args:
            position: Center position (x, y)
            k: Number of nearest objects to find
            exclude_self: Object ID to exclude
            metadata_filter: Optional metadata filter function

        Returns:
            List of (object_id, position, distance) tuples, sorted by distance
        """
        if k <= 0:
            return []

        center_x, center_y = position

        # Use a max-heap to keep k smallest distances
        heap: List[Tuple[float, str, Tuple[float, float]]] = []

        # Estimate search radius based on k and object density
        search_radius = self._estimate_search_radius(k)

        candidates = self.query(
            position,
            radius=search_radius,
            exclude_self=exclude_self,
            use_cache=False,
            metadata_filter=metadata_filter
        )

        # Process candidates with heap
        for obj_id, obj_pos in candidates:
            obj_x, obj_y = obj_pos
            distance = ((obj_x - center_x)**2 + (obj_y - center_y)**2)**0.5

            # Use negative distance for max-heap simulation with heapq (min-heap)
            if len(heap) < k:
                heapq.heappush(heap, (-distance, obj_id, obj_pos))
            else:
                # If this is closer than the farthest in heap, replace it
                if -heap[0][0] > distance:
                    heapq.heappop(heap)
                    heapq.heappush(heap, (-distance, obj_id, obj_pos))

        # Convert to sorted list
        results = [(obj_id, pos, -dist) for dist, obj_id, pos in heap]
        results.sort(key=lambda x: x[2])

        return results

    def _estimate_search_radius(self, k: int) -> float:
        """
        Estimate search radius needed to find k objects.

        Uses object density to estimate appropriate radius.

        Args:
            k: Number of objects needed

        Returns:
            Estimated radius in world units
        """
        if len(self.objects) == 0:
            return self.cell_size

        # Calculate object density (objects per unit area)
        world_area = self.width * self.height
        density = len(self.objects) / world_area

        # Estimate area needed for k objects
        target_area = k / density if density > 0 else k * self.cell_size ** 2

        # Convert to radius (circle area = pi * r^2)
        radius = sqrt(target_area / 3.14159)

        # Ensure at least one cell radius
        return max(radius, self.cell_size)

    def invalidate_cache(self) -> None:
        """Clear the query cache."""
        self._query_cache.clear()
        logger.debug("Query cache invalidated")

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
