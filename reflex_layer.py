from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import uuid

class AgentState(Enum):
    IDLE = "IDLE"
    WALKING = "WALKING"
    EATING = "EATING"
    SLEEPING = "SLEEPING"

@dataclass
class Agent:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Unknown"
    position: Tuple[float, float] = (0.0, 0.0)
    state: AgentState = AgentState.IDLE
    hp: int = 100
    hunger: float = 0.0  # 0 to 100
    energy: float = 100.0 # 0 to 100
    target_destination: Optional[Tuple[float, float]] = None

class WorldState:
    def __init__(self):
        self.agents: Dict[uuid.UUID, Agent] = {}
        self.locations: Dict[str, Tuple[float, float]] = {
            "well": (10.0, 10.0),
            "tavern": (20.0, 5.0),
            "inn": (5.0, 20.0)
        }

    def add_agent(self, agent: Agent):
        self.agents[agent.id] = agent

class ReflexLayer:
    """
    System 1: Rule-based reflexes (<50ms response).
    Handles basic survival and movement logic.
    """
    def __init__(self, world: WorldState):
        self.world = world

    async def evaluate(self, tick: int):
        for agent in self.world.agents.values():
            self._apply_reflexes(agent)

    def _apply_reflexes(self, agent: Agent):
        # 1. Survival Reflexes (Internal Needs)
        agent.hunger += 0.1 # Increased for faster demo
        agent.energy -= 0.05

        # 2. Rule-based State Transitions
        if agent.hunger > 50 and agent.state != AgentState.EATING:
            agent.state = AgentState.WALKING
            agent.target_destination = self.world.locations["tavern"]
        
        if agent.energy < 40 and agent.state != AgentState.SLEEPING:
            agent.state = AgentState.WALKING
            agent.target_destination = self.world.locations["inn"]

        # 3. Movement Execution
        if agent.state == AgentState.WALKING and agent.target_destination:
            self._move_towards_target(agent)

    def _move_towards_target(self, agent: Agent):
        tx, ty = agent.target_destination
        px, py = agent.position
        
        dx, dy = tx - px, ty - py
        dist = (dx**2 + dy**2)**0.5
        
        speed = 0.5 # units per tick
        
        if dist < speed:
            agent.position = (tx, ty)
            agent.target_destination = None
            # Decide what to do upon arrival
            if agent.hunger > 80:
                agent.state = AgentState.EATING
            elif agent.energy < 20:
                agent.state = AgentState.SLEEPING
            else:
                agent.state = AgentState.IDLE
        else:
            agent.position = (px + (dx/dist)*speed, py + (dy/dist)*speed)

        # Eating/Sleeping logic
        if agent.state == AgentState.EATING:
            agent.hunger -= 0.5
            if agent.hunger <= 0:
                agent.hunger = 0
                agent.state = AgentState.IDLE
        
        if agent.state == AgentState.SLEEPING:
            agent.energy += 0.2
            if agent.energy >= 100:
                agent.energy = 100
                agent.state = AgentState.IDLE
