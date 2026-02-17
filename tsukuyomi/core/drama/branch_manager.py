"""
Branch Manager - Narrative branching logic.

Manages narrative branches and conditional path selection based on
world state and agent conditions.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("BranchManager")


@dataclass
class BranchState:
    """Tracks the state of a narrative branch."""
    branch_id: str
    active: bool = False
    completed: bool = False
    entry_tick: int = 0
    exit_tick: int = 0
    selected_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "branch_id": self.branch_id,
            "active": self.active,
            "completed": self.completed,
            "entry_tick": self.entry_tick,
            "exit_tick": self.exit_tick,
            "selected_path": self.selected_path,
        }


class ConditionEvaluator:
    """
    Evaluates condition expressions for branch selection.
    
    Supports:
    - Attribute comparisons: "agent.trait > 0.5"
    - Aggregations: "any_agent.belief_changed", "all_agents.stance == 'guilty'"
    - Logical operators: AND, OR, NOT
    - State checks: "tension > 0.5", "ticks > 1000"
    """
    
    def __init__(self):
        self._custom_functions: Dict[str, Callable] = {}
    
    def register_function(self, name: str, func: Callable):
        """Register a custom function for condition evaluation."""
        self._custom_functions[name] = func
    
    def evaluate(
        self, 
        condition: str, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Evaluate a condition string.
        
        Args:
            condition: Condition string to evaluate.
            world_state: Current world state dictionary.
            agent_states: Dictionary of agent_id -> agent_state.
            
        Returns:
            Boolean result of condition evaluation.
        """
        try:
            return self._evaluate_expression(condition, world_state, agent_states)
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _evaluate_expression(
        self, 
        expr: str, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Parse and evaluate an expression."""
        
        expr = expr.strip()
        
        # Handle logical operators
        if " AND " in expr.upper():
            # Split carefully preserving case
            parts = re.split(r'\s+AND\s+', expr, flags=re.IGNORECASE)
            return all(self._evaluate_expression(p, world_state, agent_states) for p in parts)
        
        if " OR " in expr.upper():
            parts = re.split(r'\s+OR\s+', expr, flags=re.IGNORECASE)
            return any(self._evaluate_expression(p, world_state, agent_states) for p in parts)
        
        if expr.upper().startswith("NOT "):
            inner = expr[4:].strip()
            return not self._evaluate_expression(inner, world_state, agent_states)
        
        # Handle aggregations
        if expr.startswith("any_agent."):
            return self._evaluate_any_agent(expr, agent_states)
        
        if expr.startswith("all_agents."):
            return self._evaluate_all_agents(expr, agent_states)
        
        # Handle function calls
        if "(" in expr and expr.endswith(")"):
            return self._evaluate_function(expr, world_state, agent_states)
        
        # Handle simple comparison
        return self._evaluate_comparison(expr, world_state, agent_states)
    
    def _evaluate_comparison(
        self, 
        expr: str, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Evaluate a simple comparison expression."""
        
        # Parse comparison
        match = re.match(r"(.+?)\s*([><=!]+)\s*(.+)", expr)
        if not match:
            logger.warning(f"Could not parse comparison: {expr}")
            return False
        
        left_expr, operator, right_expr = match.groups()
        
        # Get values
        left_value = self._get_value(left_expr.strip(), world_state, agent_states)
        right_value = self._get_value(right_expr.strip(), world_state, agent_states)
        
        # Handle string comparisons
        if isinstance(right_value, str):
            right_value = right_value.strip("'\"")
        
        # Compare
        try:
            if operator == ">":
                return left_value > right_value
            elif operator == ">=":
                return left_value >= right_value
            elif operator == "<":
                return left_value < right_value
            elif operator == "<=":
                return left_value <= right_value
            elif operator == "==" or operator == "=":
                return left_value == right_value
            elif operator == "!=":
                return left_value != right_value
        except TypeError:
            logger.warning(f"Type mismatch in comparison: {left_value} {operator} {right_value}")
            return False
        
        return False
    
    def _get_value(
        self, 
        expr: str, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Any:
        """Get a value from an expression."""
        
        # Numeric literal
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # String literal
        if (expr.startswith("'") and expr.endswith("'")) or \
           (expr.startswith('"') and expr.endswith('"')):
            return expr[1:-1]
        
        # Boolean literal
        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False
        
        # Special value: same_value (for consensus checks)
        if expr == "same_value":
            return "same_value"
        
        # World state attribute
        if expr in world_state:
            return world_state[expr]
        
        # Dot notation
        if "." in expr:
            parts = expr.split(".", 1)
            first = parts[0]
            rest = parts[1] if len(parts) > 1 else None
            
            # Check if it's an agent reference
            if first in agent_states:
                if rest:
                    return self._get_nested_value(agent_states[first], rest)
                return agent_states[first]
            
            # Check world state
            if first in world_state:
                if rest:
                    return self._get_nested_value(world_state[first], rest)
                return world_state[first]
        
        # Direct attribute in world_state
        return world_state.get(expr, 0.0)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a nested value using dot notation."""
        parts = path.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
    
    def _evaluate_any_agent(
        self, 
        expr: str, 
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Evaluate 'any_agent.*' expression."""
        
        # Extract the condition part after "any_agent."
        inner = expr[10:]  # len("any_agent.") = 10
        
        # Special handling for "stance('topic') == same_value"
        if ".stance(" in inner:
            return self._evaluate_stance_consensus(inner, agent_states, require_all=False)
        
        # Parse the inner comparison
        for agent_id, state in agent_states.items():
            # Try to evaluate the condition for this agent
            if self._evaluate_agent_condition(inner, state, agent_id):
                return True
        
        return False
    
    def _evaluate_all_agents(
        self, 
        expr: str, 
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Evaluate 'all_agents.*' expression."""
        
        inner = expr[11:]  # len("all_agents.") = 11
        
        # Special handling for stance consensus
        if ".stance(" in inner:
            return self._evaluate_stance_consensus(inner, agent_states, require_all=True)
        
        for agent_id, state in agent_states.items():
            if not self._evaluate_agent_condition(inner, state, agent_id):
                return False
        
        return True
    
    def _evaluate_agent_condition(
        self, 
        condition: str, 
        agent_state: Dict[str, Any],
        agent_id: str
    ) -> bool:
        """Evaluate a condition for a single agent."""
        
        # Replace "belief_changed_recently" etc.
        if "belief_changed_recently" in condition:
            return agent_state.get("belief_changed_recently", False)
        
        # Parse attribute comparison
        match = re.match(r"(\w+)\s*([><=!]+)\s*(.+)", condition)
        if match:
            attr, operator, value_str = match.groups()
            
            # Get attribute value from agent state
            attr_value = agent_state.get(attr, agent_state.get("traits", {}).get(attr, 0.0))
            
            # Get comparison value
            value_str = value_str.strip()
            try:
                if "." in value_str:
                    value = float(value_str)
                else:
                    value = float(value_str)
            except ValueError:
                value = value_str.strip("'\"")
            
            # Compare
            if operator == ">":
                return attr_value > value
            elif operator == ">=":
                return attr_value >= value
            elif operator == "<":
                return attr_value < value
            elif operator == "<=":
                return attr_value <= value
            elif operator == "==" or operator == "=":
                return attr_value == value
            elif operator == "!=":
                return attr_value != value
        
        return False
    
    def _evaluate_stance_consensus(
        self, 
        inner: str, 
        agent_states: Dict[str, Dict[str, Any]],
        require_all: bool
    ) -> bool:
        """Evaluate stance consensus conditions."""
        
        # Extract topic from stance('topic')
        match = re.search(r"stance\(['\"](\w+)['\"]\)\s*==\s*same_value", inner)
        if not match:
            return False
        
        topic = match.group(1)
        
        # Get all stances on this topic
        stances = []
        for agent_id, state in agent_states.items():
            stance = state.get("stances", {}).get(topic)
            if stance is not None:
                stances.append(stance)
        
        if not stances:
            return False
        
        # Check if all same
        first_stance = stances[0]
        all_same = all(s == first_stance for s in stances)
        
        return all_same
    
    def _evaluate_function(
        self, 
        expr: str, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Evaluate a function call."""
        
        # Parse function name and args
        match = re.match(r"(\w+)\(([^)]*)\)", expr)
        if not match:
            return False
        
        func_name = match.group(1)
        args_str = match.group(2)
        
        # Check custom functions
        if func_name in self._custom_functions:
            return self._custom_functions[func_name](args_str, world_state, agent_states)
        
        logger.warning(f"Unknown function: {func_name}")
        return False


class BranchManager:
    """
    Manages narrative branching and path selection.
    
    Tracks active branches, evaluates conditions, and determines
    which narrative path to follow based on world state.
    """
    
    def __init__(self):
        """Initialize the branch manager."""
        self._evaluator = ConditionEvaluator()
        self._branch_states: Dict[str, BranchState] = {}
        self._active_branch: Optional[str] = None
        self._branch_history: List[Dict[str, Any]] = []
        self._completed_beats: Set[str] = set()
    
    def evaluate_branch(
        self,
        branch_conditions: List[Dict[str, Any]],
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        current_tick: int
    ) -> Optional[str]:
        """
        Evaluate branch conditions and return the selected path.
        
        Args:
            branch_conditions: List of branch condition configs.
            world_state: Current world state.
            agent_states: Current agent states.
            current_tick: Current simulation tick.
            
        Returns:
            Target beat ID for selected branch, or None if no match.
        """
        
        for branch in branch_conditions:
            branch_id = branch.get("id", "")
            condition = branch.get("condition", "")
            target = branch.get("then", "")
            
            if self._evaluator.evaluate(condition, world_state, agent_states):
                # Record branch selection
                self._record_branch_selection(branch_id, target, current_tick)
                logger.info(f"🌳 Branch selected: {branch_id} -> {target}")
                return target
        
        return None
    
    def _record_branch_selection(
        self, 
        branch_id: str, 
        target: str, 
        tick: int
    ):
        """Record a branch selection in history."""
        
        self._branch_history.append({
            "tick": tick,
            "branch_id": branch_id,
            "target": target,
        })
        
        # Update branch state
        if branch_id not in self._branch_states:
            self._branch_states[branch_id] = BranchState(branch_id=branch_id)
        
        state = self._branch_states[branch_id]
        state.active = True
        state.selected_path = target
        state.entry_tick = tick
    
    def set_active_branch(self, branch_id: str):
        """Set the currently active branch."""
        self._active_branch = branch_id
        logger.debug(f"Active branch set to: {branch_id}")
    
    def complete_branch(self, branch_id: str, tick: int):
        """Mark a branch as completed."""
        
        if branch_id in self._branch_states:
            state = self._branch_states[branch_id]
            state.active = False
            state.completed = True
            state.exit_tick = tick
        
        if self._active_branch == branch_id:
            self._active_branch = None
    
    def mark_beat_completed(self, beat_id: str):
        """Mark a beat as completed."""
        self._completed_beats.add(beat_id)
    
    def is_beat_completed(self, beat_id: str) -> bool:
        """Check if a beat has been completed."""
        return beat_id in self._completed_beats
    
    def check_prerequisite(
        self,
        prerequisite: Optional[str],
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Check if a prerequisite beat has been completed.
        
        Args:
            prerequisite: Beat ID that must be completed first.
            world_state: Current world state.
            agent_states: Current agent states.
            
        Returns:
            True if prerequisite is met or None.
        """
        if not prerequisite:
            return True
        
        return prerequisite in self._completed_beats
    
    def get_branch_state(self, branch_id: str) -> Optional[BranchState]:
        """Get the state of a specific branch."""
        return self._branch_states.get(branch_id)
    
    def get_all_branch_states(self) -> Dict[str, BranchState]:
        """Get all branch states."""
        return self._branch_states.copy()
    
    def get_branch_history(self) -> List[Dict[str, Any]]:
        """Get the history of branch selections."""
        return self._branch_history.copy()
    
    def register_custom_condition(
        self, 
        name: str, 
        evaluator: Callable[[str, Dict, Dict], bool]
    ):
        """Register a custom condition evaluator function."""
        self._evaluator.register_function(name, evaluator)
    
    def reset(self):
        """Reset all branch state."""
        self._branch_states.clear()
        self._active_branch = None
        self._branch_history.clear()
        self._completed_beats.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status for debugging/logging."""
        return {
            "active_branch": self._active_branch,
            "completed_beats": list(self._completed_beats),
            "branch_count": len(self._branch_states),
            "history_length": len(self._branch_history),
        }