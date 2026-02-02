import asyncio
import uuid
from simulation_loop import SimulationLoop
from reflex_layer import Agent, WorldState, ReflexLayer, AgentState

async def main():
    world = WorldState()
    
    # Initialize 15 agents
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy", "Karl", "Linda", "Mike", "Nancy", "Oscar"]
    for i in range(15):
        agent = Agent(
            id=uuid.uuid4(),
            name=names[i],
            position=(0.0, 0.0),
            hunger=i * 5, # Give them different starting needs
            energy=100 - (i * 2)
        )
        world.add_agent(agent)

    loop = SimulationLoop(tick_rate=20)
    reflex = ReflexLayer(world)
    
    # Add reflex evaluation as a phase
    loop.add_phase(reflex.evaluate)
    
    # Add a logger phase to monitor progress
    async def log_status(tick: int):
        if tick % 100 == 0:
            active_states = {}
            for a in world.agents.values():
                active_states[a.state.name] = active_states.get(a.state.name, 0) + 1
            print(f"Tick {tick}: States: {active_states}")
            # Example agent check
            first_agent = list(world.agents.values())[0]
            print(f"  {first_agent.name}: pos={first_agent.position}, hunger={first_agent.hunger:.1f}, energy={first_agent.energy:.1f}, state={first_agent.state.name}")

    loop.add_phase(log_status)

    # Run for a limited time for the demo/test
    try:
        await asyncio.wait_for(loop.run(), timeout=10)
    except asyncio.TimeoutError:
        loop.stop()
        print("Demo completed.")

if __name__ == "__main__":
    asyncio.run(main())
