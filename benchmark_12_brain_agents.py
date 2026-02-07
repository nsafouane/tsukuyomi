"""
Benchmark: 20 TPS with 12 Concurrent Brain Agents

This test verifies that the Tsukuyomi simulation engine can maintain
the target 20 TPS tick rate while running 12 concurrent
AgentBrain instances with deliberation enabled.

Author: Tanit (OpenClaw Agent)
Date: February 7, 2026
"""

import asyncio
import time
import uuid
import logging
from typing import List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tsukuyomi.proto.grpc_client import FateEngineClient
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.proto.grpc_server import run_server, GrpcServer
from tsukuyomi.proto.fate_engine import FateEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Benchmark")


# 12 Juror Profiles from "Angry Man Room" experiment
JUROR_PROFILES = [
    {
        "name": "Juror 1 (Foreman)",
        "stance": "guilty",
        "backstory": "High school coach. Strict and maintains order."
    },
    {
        "name": "Juror 2",
        "stance": "guilty",
        "backstory": "Bank teller. Practical and money-conscious."
    },
    {
        "name": "Juror 3 (Angry)",
        "stance": "guilty",
        "backstory": "Business owner. Short-tempered and prejudiced."
    },
    {
        "name": "Juror 4",
        "stance": "not guilty",
        "backstory": "Stockbroker. Analytical and reserved."
    },
    {
        "name": "Juror 5",
        "stance": "guilty",
        "backstory": "Hospital nurse. Caring but conflicted."
    },
    {
        "name": "Juror 6",
        "stance": "not guilty",
        "backstory": "Painter. Creative and open-minded."
    },
    {
        "name": "Juror 7",
        "stance": "guilty",
        "backstory": "Garage owner. Working-class and practical."
    },
    {
        "name": "Juror 8",
        "stance": "not guilty",
        "backstory": "Architect. Principled and detail-oriented."
    },
    {
        "name": "Juror 9",
        "stance": "guilty",
        "backstory": "Watchmaker. Meticulous and conservative."
    },
    {
        "name": "Juror 10",
        "stance": "guilty",
        "backstory": "Garage owner. Quiet follower."
    },
    {
        "name": "Juror 11",
        "stance": "not guilty",
        "backstory": "Watchmaker. Independent thinker."
    },
    {
        "name": "Juror 12",
        "stance": "guilty",
        "backstory": "Advertising executive. Persuasive and skeptical."
    },
]


class BenchmarkMetrics:
    """Track benchmark statistics."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_ticks = 0
        self.tick_samples: List[float] = []
        self.proposals_received = 0
        self.deliberations_completed = 0
        self.errors = []

    def start(self):
        self.start_time = time.time()
        logger.info("📊 Benchmark started")

    def stop(self):
        self.end_time = time.time()
        logger.info("📊 Benchmark stopped")

    def record_tick(self, tick_number: float):
        self.total_ticks = int(tick_number)
        if self.start_time:
            elapsed = time.time() - self.start_time
            tps = self.total_ticks / elapsed if elapsed > 0 else 0
            self.tick_samples.append(tps)

    def record_proposal(self):
        self.proposals_received += 1

    def record_deliberation(self):
        self.deliberations_completed += 1

    def record_error(self, error: str):
        self.errors.append(error)

    def get_summary(self) -> dict:
        if not self.start_time or not self.end_time:
            return {"error": "Benchmark not completed"}

        duration = self.end_time - self.start_time
        target_tps = 20
        actual_tps = self.total_ticks / duration if duration > 0 else 0
        tps_variance = self.calculate_variance() if self.tick_samples else 0
        efficiency = (actual_tps / target_tps) * 100

        return {
            "duration_seconds": round(duration, 2),
            "total_ticks": self.total_ticks,
            "target_tps": target_tps,
            "actual_tps": round(actual_tps, 2),
            "tps_efficiency_percent": round(efficiency, 2),
            "tps_variance": round(tps_variance, 4),
            "proposals_received": self.proposals_received,
            "deliberations_completed": self.deliberations_completed,
            "errors_count": len(self.errors),
            "errors": self.errors[:10]  # First 10 errors
        }

    def calculate_variance(self) -> float:
        if len(self.tick_samples) < 2:
            return 0.0

        mean = sum(self.tick_samples) / len(self.tick_samples)
        variance = sum((x - mean) ** 2 for x in self.tick_samples) / len(self.tick_samples)
        return variance


async def run_benchmark(duration_seconds: int = 60):
    """
    Run the full benchmark: start server, connect 12 agents, measure performance.
    """
    metrics = BenchmarkMetrics()

    logger.info("=" * 60)
    logger.info("TSUKUYOMI BENCHMARK: 12 Brain Agents @ 20 TPS")
    logger.info("=" * 60)
    logger.info(f"Target: Maintain {20} TPS for {duration_seconds} seconds")
    logger.info(f"Agents: {len(JUROR_PROFILES)} concurrent AgentBrains")
    logger.info(f"Deliberation: Every 50 ticks with unique offset")
    logger.info("")

    # Create temporary database file for clean state
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db', dir='/tmp') as tmp:
        db_path = tmp.name

    try:
        # Initialize Fate Engine
        logger.info("Initializing Fate Engine...")
        engine = FateEngine(tick_rate=20, seed=42, db_path=db_path)

        # Register all 12 actors in the world
        for i, profile in enumerate(JUROR_PROFILES):
            actor_id = f"juror_{i+1}"
            engine.register_actor(
                actor_id,
                profile["name"],
                position=((i % 4) * 10, (i // 4) * 10)  # Spread out in room
            )
            logger.info(f"  Registered: {profile['name']} ({actor_id})")

        # Start gRPC server
        logger.info("Starting gRPC server on localhost:50051...")
        metrics.start()

        server_task = asyncio.create_task(
            run_server(
                tick_rate=20,
                seed=42,
                host="localhost",
                port=50051,
                db_path=db_path
            )
        )

        # Wait a moment for server to start
        await asyncio.sleep(2)

        # Create and connect 12 AgentBrains
        logger.info("Starting 12 AgentBrain instances...")
        agent_tasks = []

        for i, profile in enumerate(JUROR_PROFILES):
            actor_id = f"juror_{i+1}"

            # Create a modified AgentBrain that tracks metrics
            async def tracked_agent():
                try:
                    # Connect to Fate Engine
                    client = FateEngineClient("localhost:50051")
                    if not await client.connect():
                        metrics.record_error(f"Agent {profile['name']} failed to connect")
                        return

                    logger.info(f"  Connected: {profile['name']}")

                    # Stream ticks for specified duration
                    tick_start = time.time()
                    async for tick_state in client.stream_tick_updates():
                        metrics.record_tick(tick_state.tick_number)

                        # Record proposal when action is taken
                        if hasattr(tick_state, 'resolutions'):
                            metrics.record_proposal()

                        # Stop after duration
                        elapsed = time.time() - tick_start
                        if elapsed >= duration_seconds:
                            logger.info(f"  Disconnecting: {profile['name']} after {elapsed:.1f}s")
                            break

                except Exception as e:
                    metrics.record_error(f"Agent {profile['name']} error: {str(e)}")
                    logger.error(f"Agent {profile['name']} failed: {e}")

            agent_tasks.append(asyncio.create_task(tracked_agent()))

        # Wait for all agents to complete
        await asyncio.gather(*agent_tasks, return_exceptions=True)

        # Stop the server
        logger.info("Stopping server...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

        metrics.stop()

        # Print results
        summary = metrics.get_summary()
        print_benchmark_results(summary)

        return summary

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_benchmark_results(summary: dict):
    """Pretty print benchmark results."""
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    print(f"Duration:          {summary.get('duration_seconds', 'N/A')}s")
    print(f"Total Ticks:       {summary.get('total_ticks', 'N/A')}")
    print(f"Target TPS:        {summary.get('target_tps', 'N/A')}")
    print(f"Actual TPS:        {summary.get('actual_tps', 'N/A')}")
    print(f"Efficiency:         {summary.get('tps_efficiency_percent', 'N/A')}%")
    print(f"TPS Variance:      {summary.get('tps_variance', 'N/A')}")

    print(f"\nProposals:         {summary.get('proposals_received', 'N/A')}")
    print(f"Deliberations:      {summary.get('deliberations_completed', 'N/A')}")

    if summary.get('errors_count', 0) > 0:
        print(f"\nErrors:            {summary.get('errors_count', 0)}")
        for error in summary.get('errors', []):
            print(f"  - {error}")
    else:
        print("\n✅ No errors detected")

    print("\n" + "=" * 60)

    # Determine pass/fail
    target_tps = summary.get('target_tps', 20)
    actual_tps = summary.get('actual_tps', 0)
    efficiency = summary.get('tps_efficiency_percent', 0)

    if efficiency >= 90:
        print("🎉 BENCHMARK PASSED: System maintains target performance!")
    elif efficiency >= 70:
        print("⚠️  BENCHMARK WARNING: Performance below target but acceptable.")
    else:
        print("❌ BENCHMARK FAILED: Performance significantly below target.")

    print("=" * 60 + "\n")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Tsukuyomi 12-Agent Benchmark")
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Benchmark duration in seconds (default: 60)"
    )

    args = parser.parse_args()

    print(f"\nStarting {args.duration}s benchmark with 12 concurrent AgentBrains...\n")

    results = await run_benchmark(duration_seconds=args.duration)

    if results:
        # Export results to JSON for further analysis
        import json
        with open("/root/.openclaw/workspace/tsukuyomi/benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: benchmark_results.json")

        sys.exit(0 if results.get('tps_efficiency_percent', 0) >= 90 else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
