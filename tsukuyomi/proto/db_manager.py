# db_manager.py - Persistent Storage for Tsukuyomi Tick History

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from tsukuyomi.proto import core_pb2
from google.protobuf.json_format import MessageToJson, Parse

logger = logging.getLogger("DBManager")

class DBManager:
    """
    Manages SQLite storage for Tsukuyomi simulation data.
    Stores TickHistory (world snapshots, proposals, resolutions).
    """
    
    def __init__(self, db_path: str = "tsukuyomi_history.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ticks (
                        tick_number INTEGER PRIMARY KEY,
                        timestamp REAL,
                        tick_state_json TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database at {self.db_path}: {e}", exc_info=True)
            
    def save_tick(self, tick_state: core_pb2.TickState):
        """Save a single tick state to the database."""
        tick_number = tick_state.tick_number
        timestamp = tick_state.timestamp.seconds + tick_state.timestamp.nanos / 1e9
        
        # Convert Protobuf to JSON for storage
        # Including world state, proposals, and resolutions
        tick_json = MessageToJson(tick_state, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO ticks (tick_number, timestamp, tick_state_json) VALUES (?, ?, ?)",
                    (tick_number, timestamp, tick_json)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save tick {tick_number}: {e}")

    def get_tick(self, tick_number: int) -> Optional[core_pb2.TickState]:
        """Retrieve a specific tick state from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT tick_state_json FROM ticks WHERE tick_number = ?", (tick_number,))
                row = cursor.fetchone()
                if row:
                    tick_state = core_pb2.TickState()
                    return Parse(row[0], tick_state)
        except Exception as e:
            logger.error(f"Failed to load tick {tick_number}: {e}")
        return None

    def get_latest_tick_number(self) -> int:
        """Get the highest tick number recorded."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(tick_number) FROM ticks")
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else -1

    def list_ticks(self, limit: int = 100, offset: int = 0) -> List[int]:
        """List available tick numbers."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tick_number FROM ticks ORDER BY tick_number DESC LIMIT ? OFFSET ?", (limit, offset))
            return [row[0] for row in cursor.fetchall()]
