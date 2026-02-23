"""
Tsukuyomi V2 - World Builder API

This module provides a programmatic interface for building and initializing
worlds in the Fate Engine. It allows scenarios to define
locations, objects, and agents without modifying engine code.

Usage:
    builder = WorldBuilder()
    builder.add_location("MarketSquare", Vector2(0, 0), 20.0)
    builder.add_object("fountain", "decoration", Vector2(5, 5), {"water": True})
    builder.add_agent("merchant", "Marcus", "Merchant")
    await engine.initialize_world(builder.serialize())
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum

logger = logging.getLogger(__name__)


class ObjectType(Enum):
    """Types of objects that can be placed in the world."""
    DECORATION = "decoration"  # Visual props, no interaction
    INTERACTIVE = "interactive"  # Can be interacted with
    CONTAINER = "container"  # Can hold items
    PORTAL = "portal"  # Connects to other locations
    SPAWN_POINT = "spawn"  # Agent spawn locations


@dataclass
class Affordance:
    """
    Defines what actions are possible on an object.

    Example:
        Affordance(
            action_type="COLLECT",
            precondition="distance < 2.0 AND inventory_empty",
            effect="inventory.add(item_id)"
        )
    """
    action_type: str
    precondition: Optional[str] = None
    effect_description: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "action_type": self.action_type,
            "precondition": self.precondition,
            "effect": self.effect_description
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Affordance':
        """Create Affordance from dictionary."""
        return cls(
            action_type=data["action_type"],
            precondition=data.get("precondition"),
            effect_description=data.get("effect")
        )


@dataclass
class EnvironmentObject:
    """
    Represents an object in the world (static entity).

    Attributes:
        object_id: Unique identifier
        obj_type: Type of object (decoration, interactive, etc.)
        name: Display name
        position: (x, y) coordinates
        properties: Custom properties dict
        affordances: List of possible actions
    """
    object_id: str = field(default_factory=lambda: str(uuid4()))
    obj_type: ObjectType = ObjectType.DECORATION
    name: str = "object"
    position: tuple = (0.0, 0.0)
    properties: Dict[str, Any] = field(default_factory=dict)
    affordances: List[Affordance] = field(default_factory=list)

    def add_affordance(
        self,
        action_type: str,
        precondition: Optional[str] = None,
        effect: Optional[str] = None
    ) -> None:
        """Add an affordance to this object."""
        affordance = Affordance(action_type, precondition, effect)
        self.affordances.append(affordance)
        logger.debug(f"Added affordance {action_type} to object {self.name}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "object_id": self.object_id,
            "obj_type": self.obj_type.value,
            "name": self.name,
            "position": {"x": self.position[0], "y": self.position[1]},
            "properties": self.properties,
            "affordances": [a.to_dict() for a in self.affordances]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EnvironmentObject':
        """Create EnvironmentObject from dictionary."""
        obj = cls(
            object_id=data["object_id"],
            obj_type=ObjectType(data["obj_type"]),
            name=data["name"],
            position=(data["position"]["x"], data["position"]["y"]),
            properties=data.get("properties", {})
        )

        # Restore affordances
        if "affordances" in data:
            obj.affordances = [Affordance.from_dict(a) for a in data["affordances"]]

        return obj


@dataclass
class Location:
    """
    Represents a location/zone in the world.

    Attributes:
        location_id: Unique identifier
        name: Display name
        position: Center position
        size: Width and height
        objects: List of objects in this location
        spawn_points: List of valid spawn positions
    """
    location_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "location"
    position: tuple = (0.0, 0.0)
    size: tuple = (10.0, 10.0)  # (width, height)
    objects: List[EnvironmentObject] = field(default_factory=list)
    spawn_points: List[tuple] = field(default_factory=list)

    def add_object(self, obj: EnvironmentObject) -> None:
        """Add an object to this location."""
        self.objects.append(obj)
        logger.debug(f"Added object {obj.name} to location {self.name}")

    def add_spawn_point(self, x: float, y: float) -> None:
        """Add a valid spawn point."""
        self.spawn_points.append((x, y))
        logger.debug(f"Added spawn point ({x}, {y}) to location {self.name}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "location_id": self.location_id,
            "name": self.name,
            "position": {"x": self.position[0], "y": self.position[1]},
            "size": {"width": self.size[0], "height": self.size[1]},
            "objects": [o.to_dict() for o in self.objects],
            "spawn_points": [{"x": x, "y": y} for x, y in self.spawn_points]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Location':
        """Create Location from dictionary."""
        loc = cls(
            location_id=data["location_id"],
            name=data["name"],
            position=(data["position"]["x"], data["position"]["y"]),
            size=(data["size"]["width"], data["size"]["height"])
        )

        # Restore objects
        if "objects" in data:
            loc.objects = [EnvironmentObject.from_dict(o) for o in data["objects"]]

        # Restore spawn points
        if "spawn_points" in data:
            loc.spawn_points = [(p["x"], p["y"]) for p in data["spawn_points"]]

        return loc


@dataclass
class WorldBuilder:
    """
    Main API for building and configuring worlds.

    This is the public interface scenarios use to define their world.
    """
    locations: List[Location] = field(default_factory=list)
    global_objects: List[EnvironmentObject] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_location(
        self,
        name: str,
        position: tuple,
        size: tuple,
        spawn_points: Optional[List[tuple]] = None
    ) -> Location:
        """
        Add a location to the world.

        Args:
            name: Location name
            position: Center position (x, y)
            size: Dimensions (width, height)
            spawn_points: List of spawn positions

        Returns:
            The created Location instance
        """
        location = Location(name=name, position=position, size=size)

        if spawn_points:
            for sp in spawn_points:
                location.add_spawn_point(sp[0], sp[1])

        self.locations.append(location)
        logger.info(f"Created location: {name} at {position}")
        return location

    def add_object(
        self,
        name: str,
        obj_type: ObjectType,
        position: tuple,
        properties: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None
    ) -> EnvironmentObject:
        """
        Add an object to the world.

        Args:
            name: Object name
            obj_type: Type of object
            position: Position (x, y)
            properties: Custom properties
            location_id: Location to place object in (None = global)

        Returns:
            The created EnvironmentObject instance
        """
        obj = EnvironmentObject(
            name=name,
            obj_type=obj_type,
            position=position,
            properties=properties or {}
        )

        if location_id:
            # Add to specific location
            location = self.get_location(location_id)
            if location:
                location.add_object(obj)
            else:
                logger.warning(f"Location {location_id} not found, adding object globally")
                self.global_objects.append(obj)
        else:
            # Add globally
            self.global_objects.append(obj)

        logger.info(f"Created object: {name} ({obj_type.value}) at {position}")
        return obj

    def add_interactive_object(
        self,
        name: str,
        position: tuple,
        affordances: List[Dict[str, str]],
        properties: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None
    ) -> EnvironmentObject:
        """
        Convenience method to add an interactive object with affordances.

        Args:
            name: Object name
            position: Position (x, y)
            affordances: List of affordance dicts
            properties: Custom properties
            location_id: Location to place object in

        Returns:
            The created EnvironmentObject instance
        """
        obj = self.add_object(name, ObjectType.INTERACTIVE, position, properties, location_id)

        # Add affordances
        for aff in affordances:
            obj.add_affordance(
                action_type=aff["action_type"],
                precondition=aff.get("precondition"),
                effect=aff.get("effect")
            )

        return obj

    def get_location(self, location_id: str) -> Optional[Location]:
        """
        Get a location by ID.

        Args:
            location_id: Location ID

        Returns:
            Location instance or None
        """
        for location in self.locations:
            if location.location_id == location_id or location.name == location_id:
                return location
        return None

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata for the world.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        logger.debug(f"Set metadata: {key} = {value}")

    def serialize(self) -> Dict:
        """
        Serialize the world to a dictionary for gRPC transmission.

        Returns:
            Dictionary representation of the world
        """
        return {
            "locations": [l.to_dict() for l in self.locations],
            "global_objects": [o.to_dict() for o in self.global_objects],
            "metadata": self.metadata,
            "version": "2.0"
        }

    @classmethod
    def deserialize(cls, data: Dict) -> 'WorldBuilder':
        """
        Create WorldBuilder from serialized dictionary.

        Args:
            data: Serialized world data

        Returns:
            WorldBuilder instance
        """
        builder = cls()

        # Restore metadata
        if "metadata" in data:
            builder.metadata = data["metadata"]

        # Restore locations
        if "locations" in data:
            builder.locations = [Location.from_dict(l) for l in data["locations"]]

        # Restore global objects
        if "global_objects" in data:
            builder.global_objects = [EnvironmentObject.from_dict(o) for o in data["global_objects"]]

        logger.info(f"Deserialized world with {len(builder.locations)} locations")
        return builder

    def validate(self) -> List[str]:
        """
        Validate the world configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for duplicate location IDs
        location_ids = [l.location_id for l in self.locations]
        duplicates = [lid for lid in location_ids if location_ids.count(lid) > 1]
        if duplicates:
            errors.append(f"Duplicate location IDs: {duplicates}")

        # Check for empty spawn points
        for location in self.locations:
            if not location.spawn_points:
                errors.append(f"Location {location.name} has no spawn points")

        # Check object positions within location bounds
        for location in self.locations:
            for obj in location.objects:
                px, py = obj.position
                lx, ly = location.position
                lw, lh = location.size

                min_x, max_x = lx - lw/2, lx + lw/2
                min_y, max_y = ly - lh/2, ly + lh/2

                if not (min_x <= px <= max_x and min_y <= py <= max_y):
                    errors.append(
                        f"Object {obj.name} at ({px}, {py}) is outside "
                        f"location {location.name} bounds"
                    )

        return errors
