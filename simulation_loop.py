import asyncio
import time
import logging
from typing import List, Callable, Awaitable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SimulationLoop")

class SimulationLoop:
    """
    Core tick loop running at 20 ticks/second (50ms per tick).
    Ensures stability and manages execution phases.
    """
    def __init__(self, tick_rate: int = 20):
        self.tick_rate = tick_rate
        self.tick_duration = 1.0 / tick_rate
        self.running = False
        self.current_tick = 0
        self.phases: List[Callable[[int], Awaitable[None]]] = []

    def add_phase(self, phase_func: Callable[[int], Awaitable[None]]):
        self.phases.append(phase_func)

    async def run(self):
        self.running = True
        logger.info(f"Starting simulation loop at {self.tick_rate} TPS")
        
        while self.running:
            start_time = time.perf_counter()
            
            # Execute all registered phases for the current tick
            for phase in self.phases:
                try:
                    await phase(self.current_tick)
                except Exception as e:
                    logger.error(f"Error in phase {phase.__name__} at tick {self.current_tick}: {e}", exc_info=True)

            self.current_tick += 1
            
            elapsed = time.perf_counter() - start_time
            sleep_time = self.tick_duration - elapsed
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                if self.current_tick % 100 == 0:
                    logger.warning(f"Tick {self.current_tick} lagged by {abs(sleep_time):.4f}s")

    def stop(self):
        self.running = False
        logger.info("Stopping simulation loop")
