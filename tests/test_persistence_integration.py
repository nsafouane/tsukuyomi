
import asyncio
import os
import uuid
import time
import pytest
from tsukuyomi.proto.fate_engine import FateEngine, create_proposal
from tsukuyomi.proto.db_manager import DBManager

@pytest.mark.asyncio
async def test_persistence_integration():
    db_path = "test_persistence.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("--- Phase 1: Run Engine and Persist ---")
    engine = FateEngine(tick_rate=10, db_path=db_path, seed=42)
    
    alice_id = str(uuid.uuid4())
    engine.register_actor(alice_id, "Alice", position=(0, 0))
    
    # Run for 5 ticks
    async def stop_soon():
        while engine.current_tick < 5:
            await asyncio.sleep(0.1)
        engine.stop()
    
    await asyncio.gather(engine.run(), stop_soon())
    print(f"Engine stopped at tick {engine.current_tick}")
    
    print("\n--- Phase 2: Resume from DB ---")
    engine2 = FateEngine(tick_rate=10, db_path=db_path, seed=42)
    
    print(f"Engine2 resumed at tick {engine2.current_tick}")
    assert engine2.current_tick == 5
    assert alice_id in engine2.world_state.actors
    assert engine2.world_state.actors[alice_id].name == "Alice"
    assert "well_structure" in engine2.world_state.objects
    
    print("\n--- Phase 3: Continue Simulation ---")
    await engine2.submit_proposal(
        await create_proposal(alice_id, "MOVE", {"destination": "tavern"})
    )
    
    async def stop_later():
        while engine2.current_tick < 10:
            await asyncio.sleep(0.1)
        engine2.stop()
        
    await asyncio.gather(engine2.run(), stop_later())
    print(f"Engine2 finished at tick {engine2.current_tick}")
    assert engine2.current_tick == 10
    
    # Verify final state in DB
    db = DBManager(db_path)
    latest = db.get_latest_tick_number()
    print(f"Latest tick in DB: {latest}")
    assert latest == 9
    
    last_tick = db.get_tick(9)
    assert last_tick.world_state.actors[alice_id].current_location == "tavern"
    
    print("\nSUCCESS: Persistence integration verified.")
    
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    asyncio.run(test_persistence_integration())
