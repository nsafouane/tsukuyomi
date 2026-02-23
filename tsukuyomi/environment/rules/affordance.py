"""
Tsukuyomi V2 - Affordance System (Phase 2)

This module implements affordance validation for EnvironmentObject interactions.
Affordances represent the possible actions an object supports and the conditions
under which those actions can be performed.

The affordance system ensures that:
1. Actions are validated against object capabilities
2. Pre-conditions are checked before execution
3. Effects are applied correctly after execution
4. Semantic tags enable richer interaction discovery

Usage:
    validator = AffordanceValidator()
    is_valid, reason = validator.validate_action(object, action_type, actor)
    effects = validator.get_effects(object, action_type, outcome)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum
from abc import ABC, abstractmethod

from tsukuyomi.transport.proto import core_pb2, common_pb2

logger = logging.getLogger(__name__)


class AffordanceError(Enum):
    """Types of affordance validation errors."""
    UNSUPPORTED_ACTION = "unsupported_action"
    PRECONDITION_FAILED = "precondition_failed"
    MISSING_ATTRIBUTE = "missing_attribute"
    TYPE_MISMATCH = "type_mismatch"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    COOLDOWN_ACTIVE = "cooldown_active"
    INSUFFICIENT_RESOURCES = "insufficient_resources"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class ValidationResult:
    """
    Result of an affordance validation.

    Attributes:
        is_valid: Whether the action is valid
        error_type: Type of error if invalid
        reason: Human-readable explanation
        modified_action: Optional modified action parameters
    """
    is_valid: bool
    error_type: Optional[AffordanceError] = None
    reason: str = ""
    modified_action: Optional[Dict[str, str]] = None


@dataclass
class AffordanceEffect:
    """
    Effect of performing an action on an object.

    Attributes:
        effect_type: Type of effect (e.g., "add_property", "remove_property", "modify_state")
        target: What the effect applies to (e.g., "actor", "object", "world")
        parameters: Effect parameters
    """
    effect_type: str
    target: str
    parameters: Dict[str, Any]


class PreconditionChecker(ABC):
    """
    Abstract base class for precondition checkers.

    Preconditions are conditions that must be satisfied before
    an action can be performed on an object.
    """

    @abstractmethod
    def check(
        self,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """
        Check if precondition is satisfied.

        Args:
            obj: The environment object
            actor: The actor attempting the action
            parameters: Action parameters

        Returns:
            ValidationResult indicating if precondition is satisfied
        """
        pass


class DistancePreconditionChecker(PreconditionChecker):
    """
    Checks if actor is within required distance of object.
    """

    def __init__(self, max_distance: float = 2.0):
        """
        Initialize distance checker.

        Args:
            max_distance: Maximum allowed distance in world units
        """
        self.max_distance = max_distance

    def check(
        self,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """Check distance precondition."""
        distance = (
            (actor.position.x - obj.position.x) ** 2 +
            (actor.position.y - obj.position.y) ** 2
        ) ** 0.5

        if distance <= self.max_distance:
            return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            error_type=AffordanceError.PRECONDITION_FAILED,
            reason=f"Too far from object ({distance:.2f} > {self.max_distance:.2f})"
        )


class InteractivePreconditionChecker(PreconditionChecker):
    """
    Checks if object is marked as interactive.
    """

    def check(
        self,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """Check if object is interactive."""
        if obj.interactive:
            return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            error_type=AffordanceError.PRECONDITION_FAILED,
            reason="Object is not interactive"
        )


class OwnershipPreconditionChecker(PreconditionChecker):
    """
    Checks ownership conditions for actions.
    """

    def check(
        self,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """Check ownership precondition."""
        # If no owner, object is free to interact with
        if not obj.owner_id:
            return ValidationResult(is_valid=True)

        # If owned, check if actor is the owner
        if obj.owner_id == actor.id:
            return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            error_type=AffordanceError.PERMISSION_DENIED,
            reason=f"Object is owned by {obj.owner_id}"
        )


class StatePreconditionChecker(PreconditionChecker):
    """
    Checks if object is in required state.
    """

    def __init__(self, required_state: str):
        """
        Initialize state checker.

        Args:
            required_state: Required object state
        """
        self.required_state = required_state

    def check(
        self,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """Check state precondition."""
        obj_state = obj.state if obj.state else "default"

        if obj_state == self.required_state:
            return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            error_type=AffordanceError.PRECONDITION_FAILED,
            reason=f"Object must be in state '{self.required_state}', currently '{obj_state}'"
        )


class PropertyPreconditionChecker(PreconditionChecker):
    """
    Checks if object has required properties.
    """

    def __init__(self, required_properties: Dict[str, str]):
        """
        Initialize property checker.

        Args:
            required_properties: Required property key-value pairs
        """
        self.required_properties = required_properties

    def check(
        self,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """Check property precondition."""
        missing = []
        mismatched = []

        for key, expected_value in self.required_properties.items():
            if key not in obj.properties:
                missing.append(key)
            elif obj.properties[key] != expected_value:
                mismatched.append((key, expected_value, obj.properties[key]))

        if missing or mismatched:
            reason_parts = []
            if missing:
                reason_parts.append(f"missing properties: {', '.join(missing)}")
            if mismatched:
                for key, expected, actual in mismatched:
                    reason_parts.append(f"property '{key}': expected '{expected}', got '{actual}'")

            return ValidationResult(
                is_valid=False,
                error_type=AffordanceError.PRECONDITION_FAILED,
                reason="; ".join(reason_parts)
            )

        return ValidationResult(is_valid=True)


class AffordanceValidator:
    """
    Validates actions against object affordances.

    The validator checks:
    1. Whether the action is supported by the object
    2. Whether all preconditions are satisfied
    3. Whether the actor has permission
    4. Whether the object state allows the action
    """

    def __init__(self):
        """Initialize the affordance validator."""
        # Registry of precondition checkers
        self._precondition_checkers: Dict[str, List[PreconditionChecker]] = {}

        # Default checkers for common preconditions
        self._register_default_checkers()

        logger.info("AffordanceValidator initialized")

    def _register_default_checkers(self):
        """Register default precondition checkers."""
        # Distance checkers for different ranges
        self._precondition_checkers["distance:close"] = [DistancePreconditionChecker(max_distance=2.0)]
        self._precondition_checkers["distance:medium"] = [DistancePreconditionChecker(max_distance=5.0)]
        self._precondition_checkers["distance:far"] = [DistancePreconditionChecker(max_distance=10.0)]

        # Interactive checker
        self._precondition_checkers["interactive"] = [InteractivePreconditionChecker()]

        # Ownership checker
        self._precondition_checkers["ownership:any"] = [OwnershipPreconditionChecker()]
        self._precondition_checkers["ownership:owned"] = [OwnershipPreconditionChecker()]

        logger.debug(f"Registered {len(self._precondition_checkers)} default precondition checkers")

    def register_checker(
        self,
        name: str,
        checker: PreconditionChecker
    ) -> None:
        """
        Register a custom precondition checker.

        Args:
            name: Name for the checker (referenced in affordances)
            checker: The checker instance
        """
        if name not in self._precondition_checkers:
            self._precondition_checkers[name] = []
        self._precondition_checkers[name].append(checker)
        logger.debug(f"Registered precondition checker: {name}")

    def validate_action(
        self,
        obj: core_pb2.EnvironmentObject,
        action_type: core_pb2.ActionType,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """
        Validate an action against object affordances.

        Args:
            obj: The environment object
            action_type: The action being attempted
            actor: The actor attempting the action
            parameters: Action parameters

        Returns:
            ValidationResult indicating validity
        """
        # Get affordances for this object
        affordances = obj.affordances

        # Find matching affordance
        matching_affordance = None
        action_name = core_pb2.ActionType.Name(action_type)

        for affordance in affordances:
            if affordance.action_type == action_name:
                matching_affordance = affordance
                break

        # If no explicit affordance, use default validation
        if matching_affordance is None:
            return self._validate_default_action(obj, action_type, actor, parameters)

        # Parse and check preconditions
        precondition_str = matching_affordance.precondition
        if precondition_str:
            validation = self._check_preconditions(
                precondition_str, obj, actor, parameters
            )
            if not validation.is_valid:
                return validation

        # Action is valid
        return ValidationResult(is_valid=True)

    def _validate_default_action(
        self,
        obj: core_pb2.EnvironmentObject,
        action_type: core_pb2.ActionType,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """
        Validate an action with default rules (no explicit affordance).

        Args:
            obj: The environment object
            action_type: The action being attempted
            actor: The actor attempting the action
            parameters: Action parameters

        Returns:
            ValidationResult
        """
        action_name = core_pb2.ActionType.Name(action_type)

        # Default validation rules for different action types
        if action_type == core_pb2.ActionType.EXAMINE:
            # EXAMINE always valid, just distance-limited
            return ValidationResult(is_valid=True)

        elif action_type in (core_pb2.ActionType.COLLECT, core_pb2.ActionType.TAKE):
            # COLLECT and TAKE require object to be interactive
            if not obj.interactive:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PRECONDITION_FAILED,
                    reason="Object is not collectible"
                )

            # Check distance
            distance = (
                (actor.position.x - obj.position.x) ** 2 +
                (actor.position.y - obj.position.y) ** 2
            ) ** 0.5

            if distance > 2.0:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PRECONDITION_FAILED,
                    reason=f"Too far to collect ({distance:.2f} > 2.0)"
                )

            # Check ownership
            if obj.owner_id and obj.owner_id != actor.id:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PERMISSION_DENIED,
                    reason=f"Object is owned by {obj.owner_id}"
                )

            return ValidationResult(is_valid=True)

        elif action_type == core_pb2.ActionType.USE:
            # USE requires object to be in inventory (owner_id == actor.id)
            if obj.owner_id != actor.id:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PERMISSION_DENIED,
                    reason=f"Object is not owned by actor"
                )

            return ValidationResult(is_valid=True)

        elif action_type == core_pb2.ActionType.DROP:
            # DROP requires object to be owned by actor
            if obj.owner_id != actor.id:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PERMISSION_DENIED,
                    reason=f"Object is not owned by actor"
                )

            return ValidationResult(is_valid=True)

        elif action_type == core_pb2.ActionType.INTERACT:
            # INTERACT requires object to be interactive
            if not obj.interactive:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PRECONDITION_FAILED,
                    reason="Object is not interactive"
                )

            # Check distance
            distance = (
                (actor.position.x - obj.position.x) ** 2 +
                (actor.position.y - obj.position.y) ** 2
            ) ** 0.5

            if distance > 2.0:
                return ValidationResult(
                    is_valid=False,
                    error_type=AffordanceError.PRECONDITION_FAILED,
                    reason=f"Too far to interact ({distance:.2f} > 2.0)"
                )

            return ValidationResult(is_valid=True)

        else:
            # Unknown action - deny by default
            return ValidationResult(
                is_valid=False,
                error_type=AffordanceError.UNSUPPORTED_ACTION,
                reason=f"Action '{action_name}' not supported for this object"
            )

    def _check_preconditions(
        self,
        precondition_str: str,
        obj: core_pb2.EnvironmentObject,
        actor: core_pb2.Actor,
        parameters: Dict[str, str]
    ) -> ValidationResult:
        """
        Check preconditions from an affordance.

        Preconditions can be combined with AND/OR:
        - "distance:close AND interactive"
        - "ownership:owned OR (interactive AND state:open)"

        Args:
            precondition_str: Precondition expression string
            obj: The environment object
            actor: The actor attempting the action
            parameters: Action parameters

        Returns:
            ValidationResult
        """
        # For now, handle simple comma-separated AND conditions
        # Future: Implement full expression parser
        conditions = [c.strip() for c in precondition_str.split(",")]

        for condition in conditions:
            # Check if we have a registered checker for this condition
            if condition in self._precondition_checkers:
                for checker in self._precondition_checkers[condition]:
                    result = checker.check(obj, actor, parameters)
                    if not result.is_valid:
                        return result
            else:
                # Try to parse as key:value property condition
                if ":" in condition:
                    key, value = condition.split(":", 1)
                    if key in obj.properties:
                        if obj.properties[key] != value:
                            return ValidationResult(
                                is_valid=False,
                                error_type=AffordanceError.PRECONDITION_FAILED,
                                reason=f"Property '{key}' must be '{value}', currently '{obj.properties[key]}'"
                            )
                    else:
                        return ValidationResult(
                            is_valid=False,
                            error_type=AffordanceError.MISSING_ATTRIBUTE,
                            reason=f"Object missing property '{key}'"
                        )
                else:
                    # Simple boolean property check
                    if condition not in obj.properties or obj.properties[condition] != "true":
                        return ValidationResult(
                            is_valid=False,
                            error_type=AffordanceError.PRECONDITION_FAILED,
                            reason=f"Property '{condition}' not satisfied"
                        )

        return ValidationResult(is_valid=True)

    def get_supported_actions(
        self,
        obj: core_pb2.EnvironmentObject
    ) -> List[str]:
        """
        Get list of actions supported by an object.

        Args:
            obj: The environment object

        Returns:
            List of action type names
        """
        actions = []

        # From explicit affordances
        for affordance in obj.affordances:
            actions.append(affordance.action_type)

        # If no affordances, add default actions based on object properties
        if not actions:
            if obj.interactive:
                actions.extend(["EXAMINE", "INTERACT"])
                if obj.type in ("item", "weapon", "tool", "food"):
                    actions.extend(["COLLECT", "TAKE", "USE", "DROP"])

        return actions

    def get_effects(
        self,
        obj: core_pb2.EnvironmentObject,
        action_type: core_pb2.ActionType,
        outcome: Dict[str, str]
    ) -> List[AffordanceEffect]:
        """
        Get effects of performing an action on an object.

        Args:
            obj: The environment object
            action_type: The action performed
            outcome: Resolution outcome

        Returns:
            List of effects to apply
        """
        effects = []
        action_name = core_pb2.ActionType.Name(action_type)

        # Find matching affordance
        matching_affordance = None
        for affordance in obj.affordances:
            if affordance.action_type == action_name:
                matching_affordance = affordance
                break

        if matching_affordance:
            # Parse effect description
            effect_desc = matching_affordance.effect_description

            # Simple parsing: effect_type:target:parameter1=value1,parameter2=value2
            # Example: "add_property:actor:health=+10"
            parts = effect_desc.split(":")
            if len(parts) >= 2:
                effect_type = parts[0]
                target = parts[1]
                params = {}

                if len(parts) > 2:
                    param_str = parts[2]
                    for param in param_str.split(","):
                        if "=" in param:
                            key, value = param.split("=", 1)
                            params[key] = value

                effects.append(AffordanceEffect(
                    effect_type=effect_type,
                    target=target,
                    parameters=params
                ))

        return effects

    def get_stats(self) -> Dict:
        """
        Get statistics about the validator.

        Returns:
            Dictionary with statistics
        """
        return {
            "precondition_checkers": len(self._precondition_checkers),
            "total_checkers": sum(len(checkers) for checkers in self._precondition_checkers.values()),
            "checker_names": list(self._precondition_checkers.keys())
        }
