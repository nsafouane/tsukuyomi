"""
Tsukuyomi Server - Main Entry Point

This is the main entry point for the Tsukuyomi MVP v0.1 server.
It initializes all systems and provides the unified interface.
"""

import asyncio
import logging
from pathlib import Path

from tsukuyomi.shared.config import configure_logging, get_config
from tsukuyomi.shared.exceptions import TsukuyomiError


# Configure logging
configure_logging()
logger = logging.getLogger("tsukuyomi.server")


class TsukuyomiServer:
    """
    Main Tsukuyomi server class.

    Orchestrates the Agent, Environment, and Narrative systems
    to provide autonomous agent simulations with narrative direction.
    """

    def __init__(self):
        """Initialize the Tsukuyomi server."""
        self.config = get_config()
        self._running = False

        # Systems will be initialized here
        self.environment_engine = None
        self.narrative_director = None
        self.agents = {}

    async def start(self):
        """Start the Tsukuyomi server."""
        logger.info("Starting Tsukuyomi Server...")

        if self._running:
            logger.warning("Server is already running")
            return

        try:
            # Import systems here to avoid circular imports
            from tsukuyomi.environment.core import FateEngine
            from tsukuyomi.narrative.core import DramaDirector
            from tsukuyomi.services.llm import LLMService

            # Initialize LLM service
            logger.info("Initializing LLM service...")
            self.llm_service = LLMService()
            await self.llm_service.initialize()

            # Initialize Environment Engine
            logger.info("Initializing Environment Engine...")
            self.environment_engine = FateEngine()
            await self.environment_engine.start()

            # Initialize Narrative Director
            logger.info("Initializing Narrative Director...")
            self.narrative_director = DramaDirector(
                engine=self.environment_engine
            )

            self._running = True
            logger.info("✅ Tsukuyomi Server started successfully!")

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise TsukuyomiError(f"Server startup failed: {e}") from e

    async def stop(self):
        """Stop the Tsukuyomi server."""
        logger.info("Stopping Tsukuyomi Server...")

        if not self._running:
            logger.warning("Server is not running")
            return

        try:
            # Stop systems in reverse order
            if self.narrative_director:
                logger.info("Stopping Narrative Director...")
                await self.narrative_director.cleanup()

            if self.environment_engine:
                logger.info("Stopping Environment Engine...")
                await self.environment_engine.stop()

            if self.llm_service:
                logger.info("Stopping LLM service...")
                await self.llm_service.cleanup()

            self._running = False
            logger.info("✅ Tsukuyomi Server stopped successfully!")

        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            raise

    async def run_tick(self):
        """Run a single simulation tick."""
        if not self._running:
            raise TsukuyomiError("Server is not running")

        # The Environment Engine drives the tick loop
        await self.environment_engine.tick()


def main():
    """Main entry point."""
    server = TsukuyomiServer()

    try:
        # Run server
        asyncio.run(server.start())

        # For now, just run a single tick
        asyncio.run(server.run_tick())

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        asyncio.run(server.stop())


if __name__ == "__main__":
    main()
