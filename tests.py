import unittest
import asyncio
import time
from simulation_loop import SimulationLoop
from reflex_layer import WorldState, Agent, ReflexLayer, AgentState

class TestTsukuyomiPhase1(unittest.TestCase):
    
    def test_simulation_loop_tps(self):
        loop = SimulationLoop(tick_rate=20)
        ticks_counted = 0
        
        async def counter(tick):
            nonlocal ticks_counted
            ticks_counted += 1
            if ticks_counted >= 20:
                loop.stop()

        loop.add_phase(counter)
        
        start = time.perf_counter()
        asyncio.run(asyncio.wait_for(loop.run(), timeout=2.0))
        duration = time.perf_counter() - start
        
        self.assertGreaterEqual(ticks_counted, 20)
        # 20 ticks at 20 TPS should take ~1 second. Allowing buffer.
        self.assertLess(duration, 1.5)

    def test_agent_hunger_reflex(self):
        world = WorldState()
        agent = Agent(name="TestAgent", hunger=79.9, position=(0,0))
        world.add_agent(agent)
        reflex = ReflexLayer(world)
        
        # Hunger increases by 0.01 per tick. 
        # In 20 ticks, it should cross 80.
        for _ in range(20):
            asyncio.run(reflex.evaluate(0))
        
        self.assertEqual(agent.state, AgentState.WALKING)
        self.assertEqual(agent.target_destination, world.locations["tavern"])

    def test_agent_movement(self):
        world = WorldState()
        # Speed is 0.5. Target is (10, 10). Starting at (0,0).
        # Distance is ~14.14. Should take ~29 ticks.
        agent = Agent(name="Traveler", position=(0,0), state=AgentState.WALKING, target_destination=(10, 10))
        world.add_agent(agent)
        reflex = ReflexLayer(world)
        
        for _ in range(10):
            asyncio.run(reflex.evaluate(0))
        
        self.assertNotEqual(agent.position, (0,0))
        self.assertLess(agent.position[0], 10)
        
        for _ in range(50):
            asyncio.run(reflex.evaluate(0))
            
        self.assertEqual(agent.position, (10, 10))
        self.assertIsNone(agent.target_destination)

    def test_agent_energy_reflex(self):
        world = WorldState()
        agent = Agent(name="Sleepy", energy=20.05, position=(0,0))
        world.add_agent(agent)
        reflex = ReflexLayer(world)
        
        # Energy decreases by 0.005 per tick.
        # 20 ticks -> 0.1 decrease.
        for _ in range(20):
            asyncio.run(reflex.evaluate(0))
            
        self.assertEqual(agent.state, AgentState.WALKING)
        self.assertEqual(agent.target_destination, world.locations["inn"])

if __name__ == '__main__':
    unittest.main()
