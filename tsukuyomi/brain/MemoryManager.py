import logging
from typing import Dict, List, Optional, Any
from tsukuyomi.proto import core_pb2

logger = logging.getLogger("MemoryManager")

class MemoryManager:
    """
    The 5W Memory Manager for Tsukuyomi Agents.
    
    Structures observations into:
    - WHO (Actors involved)
    - WHAT (Action performed)
    - WHEN (Tick number/timestamp)
    - WHERE (Location/Coordinates)
    - WHY (Inferred intent or cause)
    
    Now includes a Semantic Memory layer (Knowledge Graph).
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.episodic_memory: List[Dict] = []
        # Semantic Memory: { subject: { predicate: [ {object, confidence, timestamp} ] } }
        self.semantic_memory: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        
    def add_fact(self, subject: str, predicate: str, obj: Any, confidence: float = 1.0, timestamp: int = 0):
        """Add or update a fact in the Knowledge Graph."""
        if subject not in self.semantic_memory:
            self.semantic_memory[subject] = {}
        if predicate not in self.semantic_memory[subject]:
            self.semantic_memory[subject][predicate] = []
            
        # Check if this fact already exists to update it
        for fact in self.semantic_memory[subject][predicate]:
            if fact['object'] == obj:
                fact['confidence'] = confidence
                fact['timestamp'] = timestamp
                return
                
        self.semantic_memory[subject][predicate].append({
            "object": obj,
            "confidence": confidence,
            "timestamp": timestamp
        })
        logger.debug(f"Added fact: ({subject}) --[{predicate}]--> ({obj})")

    def get_relations(self, subject: str) -> Dict[str, List[Any]]:
        """Get all relations for a given subject."""
        if subject not in self.semantic_memory:
            return {}
        
        relations = {}
        for predicate, facts in self.semantic_memory[subject].items():
            relations[predicate] = [f['object'] for f in facts]
        return relations

    def ingest_tick(self, tick_state: core_pb2.TickState):
        """Transform a TickState into 5W episodic memories and semantic facts."""
        tick_num = tick_state.tick_number
        
        # 1. Process World State for Semantic Facts
        # Self location
        me = tick_state.world_state.actors.get(self.agent_id)
        if me:
            self.add_fact(self.agent_id, "located_at", self._get_actor_pos(tick_state, self.agent_id), timestamp=tick_num)
            
        # Other actors seen
        for actor_id, actor in tick_state.world_state.actors.items():
            if actor_id != self.agent_id:
                # Placeholder for visibility check
                self.add_fact(self.agent_id, "saw_actor", actor_id, timestamp=tick_num)
                self.add_fact(actor_id, "name", actor.name, timestamp=tick_num)

        # Objects seen
        for obj_id, obj in tick_state.world_state.objects.items():
            self.add_fact(self.agent_id, "saw_object", obj_id, timestamp=tick_num)
            self.add_fact(obj_id, "type", obj.type, timestamp=tick_num)

        # 2. Process Resolutions for Episodic Memory
        for res in tick_state.resolutions:
            memory_entry = {
                "who": res.actor_id,
                "what": res.outcome.get("action", "unknown"),
                "when": tick_num,
                "where": self._get_actor_pos(tick_state, res.actor_id),
                "details": dict(res.outcome)
            }
            self.episodic_memory.append(memory_entry)
            
            # Extract semantic knowledge from actions
            if res.success:
                action = res.outcome.get("action")
                if action == "collect":
                    obj_id = res.outcome.get("object_id")
                    self.add_fact(res.actor_id, "has_item", obj_id, timestamp=tick_num)
                    self.add_fact(obj_id, "location", "inventory", timestamp=tick_num)

        # Limit buffer
        if len(self.episodic_memory) > 500:
            self.episodic_memory.pop(0)

    def _get_actor_pos(self, tick_state: core_pb2.TickState, actor_id: str) -> str:
        actor = tick_state.world_state.actors.get(actor_id)
        if actor:
            return f"({actor.position.x}, {actor.position.y})"
        return "unknown"

    def query_recent(self, limit: int = 10) -> List[Dict]:
        """Retrieve recent episodic memories."""
        return self.episodic_memory[-limit:]

    def get_semantic_summary(self) -> List[str]:
        """Get a list of key semantic facts for LLM context."""
        summary = []
        for subject, predicates in self.semantic_memory.items():
            for predicate, facts in predicates.items():
                for fact in facts:
                    summary.append(f"{subject} {predicate} {fact['object']}")
        return summary
