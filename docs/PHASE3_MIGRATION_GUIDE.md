# Tsukuyomi V2 Phase 3 - Migration Guide

## Overview

This guide helps you migrate from Tsukuyomi V2 Phase 2 (SQLite-based persistence) to Phase 3 (PostgreSQL-based persistence with RAG and SaveWorld/LoadWorld).

## Table of Contents

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Migration Overview](#migration-overview)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Post-Migration Tasks](#post-migration-tasks)
5. [Rollback Procedure](#rollback-procedure)
6. [Troubleshooting](#troubleshooting)

## Pre-Migration Checklist

Before starting the migration, ensure:

- [ ] **Backup existing data**
  - Create backup of `tsukuyomi_history.db`
  - Document current simulation state
  - Note any custom modifications

- [ ] **Review Phase 3 requirements**
  - PostgreSQL 14+ installed
  - Python 3.10+
  - Sufficient disk space (2x current database size)

- [ ] **Test environment ready**
  - Development/staging environment available
  - Test data prepared
  - Migration script tested

- [ ] **Team coordination**
  - Notify stakeholders about downtime
  - Schedule maintenance window
  - Prepare rollback plan

## Migration Overview

### What Changes?

| Aspect | Phase 2 (SQLite) | Phase 3 (PostgreSQL) |
|--------|-----------------|----------------------|
| Database | SQLite (`tsukuyomi_history.db`) | PostgreSQL |
| Schema | Single `ticks` table | Multiple normalized tables |
| Persistence | Automatic tick saving | SaveWorld/LoadWorld API |
| Memory | No long-term memory | RAG with vector embeddings |
| Scale | Limited to ~50 agents | Supports 100+ agents |
| Performance | Basic | Optimized with indexes |

### Migration Path

```
Phase 2 (SQLite)
    ↓
    [Migration Script]
    ↓
Phase 3 (PostgreSQL)
    ↓
    [Validation]
    ↓
    Production
```

## Step-by-Step Migration

### Step 1: Prepare PostgreSQL Database

#### Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-14 postgresql-contrib

# macOS
brew install postgresql@14

# Start PostgreSQL
sudo service postgresql start
```

#### Install pgvector Extension

```bash
# Download and install pgvector
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable extension in PostgreSQL
sudo -u postgres psql -d tsukuyomi -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE tsukuyomi;

# Create user
CREATE USER tsukuyomi_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tsukuyomi TO tsukuyomi_user;

# Exit
\q
```

#### Create Schema

```bash
# Apply schema
psql -U tsukuyomi_user -d tsukuyomi -f docs/schema_phase3.sql
```

Expected schema creation:
- ✓ `actors`
- ✓ `environment_objects`
- ✓ `locations`
- ✓ `ticks`
- ✓ `proposals`
- ✓ `resolutions`
- ✓ `interactions`
- ✓ `relationships`
- ✓ `memories`
- ✓ `vector_embeddings`
- ✓ `metadata`

### Step 2: Backup Existing Data

```bash
# Create backup directory
mkdir -p backups/phase2_to_phase3

# Backup SQLite database
cp tsukuyomi_history.db backups/phase2_to_phase3/tsukuyomi_history_backup.db

# Backup code (if modified)
tar -czf backups/phase2_to_phase3/code_backup.tar.gz tsukuyomi/

# Verify backup
ls -lh backups/phase2_to_phase3/
```

### Step 3: Run Migration Script

#### Create Migration Script

Create `migrate_to_phase3.py`:

```python
#!/usr/bin/env python3
"""
Migration script: SQLite (Phase 2) → PostgreSQL (Phase 3)
"""

import sqlite3
import psycopg2
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SQLITE_DB_PATH = "tsukuyomi_history.db"
POSTGRESQL_URL = "postgresql://tsukuyomi_user:your_password@localhost/tsukuyomi"

class Migration:
    def __init__(self):
        self.sqlite_conn = None
        self.pg_conn = None
        self.stats = {
            'ticks_migrated': 0,
            'actors_migrated': 0,
            'objects_migrated': 0,
            'errors': 0
        }

    def connect(self):
        """Connect to both databases."""
        logger.info("Connecting to databases...")

        # SQLite connection
        self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        self.sqlite_conn.row_factory = sqlite3.Row

        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(POSTGRESQL_URL)
        self.pg_conn.autocommit = False

        logger.info("Connected to both databases")

    def migrate_ticks(self):
        """Migrate ticks from SQLite to PostgreSQL."""
        logger.info("Migrating ticks...")

        cur = self.sqlite_conn.cursor()
        pg_cur = self.pg_conn.cursor()

        try:
            # Get all ticks
            cur.execute("SELECT tick_number, timestamp, tick_state_json FROM ticks ORDER BY tick_number")
            ticks = cur.fetchall()

            for tick in ticks:
                tick_number = tick['tick_number']
                timestamp = tick['timestamp']
                tick_state_json = tick['tick_state_json']

                try:
                    # Parse tick state
                    tick_state = json.loads(tick_state_json)

                    # Extract components
                    world_state = tick_state.get('worldState', {})
                    pending_proposals = tick_state.get('pendingProposals', [])
                    resolutions = tick_state.get('resolutions', [])

                    # Insert tick
                    pg_cur.execute("""
                        INSERT INTO ticks (tick_number, timestamp, world_state_json, pending_proposals_json, resolutions_json)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (tick_number) DO NOTHING
                    """, (
                        tick_number,
                        datetime.fromtimestamp(timestamp),
                        json.dumps(world_state),
                        json.dumps(pending_proposals),
                        json.dumps(resolutions)
                    ))

                    self.stats['ticks_migrated'] += 1

                    # Log progress
                    if self.stats['ticks_migrated'] % 100 == 0:
                        logger.info(f"Migrated {self.stats['ticks_migrated']} ticks...")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tick {tick_number}: {e}")
                    self.stats['errors'] += 1

            # Commit
            self.pg_conn.commit()
            logger.info(f"✓ Migrated {self.stats['ticks_migrated']} ticks")

        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"Failed to migrate ticks: {e}")
            raise

    def migrate_actors(self):
        """Migrate actors from world state."""
        logger.info("Migrating actors...")

        cur = self.sqlite_conn.cursor()
        pg_cur = self.pg_conn.cursor()

        try:
            # Get latest tick
            cur.execute("SELECT tick_state_json FROM ticks ORDER BY tick_number DESC LIMIT 1")
            row = cur.fetchone()

            if row:
                tick_state = json.loads(row['tick_state_json'])
                world_state = tick_state.get('worldState', {})
                actors = world_state.get('actors', {})

                for actor_id, actor_data in actors.items():
                    try:
                        pg_cur.execute("""
                            INSERT INTO actors (id, name, x, y, state, current_location, inventory, tick_number)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                x = EXCLUDED.x,
                                y = EXCLUDED.y,
                                state = EXCLUDED.state,
                                current_location = EXCLUDED.current_location,
                                inventory = EXCLUDED.inventory,
                                tick_number = EXCLUDED.tick_number
                        """, (
                            actor_id,
                            actor_data.get('name', ''),
                            actor_data.get('position', {}).get('x', 0.0),
                            actor_data.get('position', {}).get('y', 0.0),
                            actor_data.get('state', 'IDLE'),
                            actor_data.get('currentLocation', ''),
                            json.dumps(actor_data.get('inventory', [])),
                            world_state.get('tickNumber', 0)
                        ))

                        self.stats['actors_migrated'] += 1

                    except Exception as e:
                        logger.error(f"Failed to migrate actor {actor_id}: {e}")
                        self.stats['errors'] += 1

                self.pg_conn.commit()
                logger.info(f"✓ Migrated {self.stats['actors_migrated']} actors")

        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"Failed to migrate actors: {e}")
            raise

    def migrate_objects(self):
        """Migrate environment objects."""
        logger.info("Migrating objects...")

        cur = self.sqlite_conn.cursor()
        pg_cur = self.pg_conn.cursor()

        try:
            cur.execute("SELECT tick_state_json FROM ticks ORDER BY tick_number DESC LIMIT 1")
            row = cur.fetchone()

            if row:
                tick_state = json.loads(row['tick_state_json'])
                world_state = tick_state.get('worldState', {})
                objects = world_state.get('objects', {})

                for obj_id, obj_data in objects.items():
                    try:
                        pg_cur.execute("""
                            INSERT INTO environment_objects (id, type, x, y, interactive, properties, display_name, state, tick_number)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                type = EXCLUDED.type,
                                x = EXCLUDED.x,
                                y = EXCLUDED.y,
                                interactive = EXCLUDED.interactive,
                                properties = EXCLUDED.properties,
                                display_name = EXCLUDED.display_name,
                                state = EXCLUDED.state,
                                tick_number = EXCLUDED.tick_number
                        """, (
                            obj_id,
                            obj_data.get('type', ''),
                            obj_data.get('position', {}).get('x', 0.0),
                            obj_data.get('position', {}).get('y', 0.0),
                            obj_data.get('interactive', False),
                            json.dumps(obj_data.get('properties', {})),
                            obj_data.get('displayName', ''),
                            obj_data.get('state', ''),
                            world_state.get('tickNumber', 0)
                        ))

                        self.stats['objects_migrated'] += 1

                    except Exception as e:
                        logger.error(f"Failed to migrate object {obj_id}: {e}")
                        self.stats['errors'] += 1

                self.pg_conn.commit()
                logger.info(f"✓ Migrated {self.stats['objects_migrated']} objects")

        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"Failed to migrate objects: {e}")
            raise

    def validate_migration(self):
        """Validate migrated data."""
        logger.info("Validating migration...")

        cur = self.sqlite_conn.cursor()
        pg_cur = self.pg_conn.cursor()

        # Check ticks count
        cur.execute("SELECT COUNT(*) FROM ticks")
        sqlite_ticks = cur.fetchone()[0]

        pg_cur.execute("SELECT COUNT(*) FROM ticks")
        pg_ticks = pg_cur.fetchone()[0]

        if sqlite_ticks == pg_ticks:
            logger.info(f"✓ Ticks match: {sqlite_ticks}")
        else:
            logger.warning(f"Ticks mismatch: SQLite={sqlite_ticks}, PostgreSQL={pg_ticks}")

        # Check actors count
        cur.execute("SELECT tick_state_json FROM ticks ORDER BY tick_number DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            tick_state = json.loads(row['tick_state_json'])
            world_state = tick_state.get('worldState', {})
            sqlite_actors = len(world_state.get('actors', {}))
        else:
            sqlite_actors = 0

        pg_cur.execute("SELECT COUNT(*) FROM actors")
        pg_actors = pg_cur.fetchone()[0]

        if sqlite_actors == pg_actors:
            logger.info(f"✓ Actors match: {sqlite_actors}")
        else:
            logger.warning(f"Actors mismatch: SQLite={sqlite_actors}, PostgreSQL={pg_actors}")

        logger.info("✓ Validation complete")

    def close(self):
        """Close database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()

    def run(self):
        """Run full migration."""
        try:
            logger.info("=" * 50)
            logger.info("Starting migration: Phase 2 → Phase 3")
            logger.info("=" * 50)

            self.connect()
            self.migrate_ticks()
            self.migrate_actors()
            self.migrate_objects()
            self.validate_migration()

            logger.info("=" * 50)
            logger.info("Migration complete!")
            logger.info(f"  Ticks migrated: {self.stats['ticks_migrated']}")
            logger.info(f"  Actors migrated: {self.stats['actors_migrated']}")
            logger.info(f"  Objects migrated: {self.stats['objects_migrated']}")
            logger.info(f"  Errors: {self.stats['errors']}")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close()

if __name__ == "__main__":
    migration = Migration()
    migration.run()
```

#### Run Migration

```bash
# Make script executable
chmod +x migrate_to_phase3.py

# Run migration
python3 migrate_to_phase3.py
```

Expected output:
```
==================================================
Starting migration: Phase 2 → Phase 3
==================================================
Connecting to databases...
Connected to both databases
Migrating ticks...
Migrated 100 ticks...
Migrated 200 ticks...
✓ Migrated 500 ticks
Migrating actors...
✓ Migrated 50 actors
Migrating objects...
✓ Migrated 100 objects
Validating migration...
✓ Ticks match: 500
✓ Actors match: 50
✓ Validation complete
==================================================
Migration complete!
  Ticks migrated: 500
  Actors migrated: 50
  Objects migrated: 100
  Errors: 0
==================================================
```

### Step 4: Update Configuration

#### Update Environment Variables

```bash
# .env
TSUKUYOMI_DB_TYPE=postgresql
TSUKUYOMI_DB_URL=postgresql://tsukuyomi_user:your_password@localhost/tsukuyomi
TSUKUYOMI_RAG_ENABLED=true
TSUKUYOMI_SAVELOAD_ENABLED=true
```

#### Update Code

```python
# Old: Phase 2
from tsukuyomi.proto.db_manager import DBManager

db = DBManager(db_path="tsukuyomi_history.db")

# New: Phase 3
from tsukuyomi.rag import VectorDatabase
from tsukuyomi.persistence import PostgreSQLManager

db = PostgreSQLManager(db_url="postgresql://...")

# RAG integration
vector_db = VectorDatabase(db_url="postgresql://...")
rag = RAGSystem(embedding_model, vector_db)
```

### Step 5: Test Migration

#### Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run Phase 3 tests
pytest tests/test_phase3_postgresql_schema.py -v
pytest tests/test_phase3_saveload_world.py -v
pytest tests/test_phase3_rag_system.py -v
pytest tests/test_phase3_vector_database.py -v
pytest tests/test_phase3_integration.py -v

# Run integration tests
pytest tests/test_persistence_integration.py -v
```

#### Manual Verification

```python
# Verify data in PostgreSQL
import psycopg2

conn = psycopg2.connect("postgresql://tsukuyomi_user:your_password@localhost/tsukuyomi")
cur = conn.cursor()

# Check counts
cur.execute("SELECT COUNT(*) FROM ticks")
print(f"Ticks: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM actors")
print(f"Actors: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM vector_embeddings")
print(f"Vector embeddings: {cur.fetchone()[0]}")

conn.close()
```

## Post-Migration Tasks

### Task 1: Initialize RAG System

```python
from tsukuyomi.rag import RAGSystem, EmbeddingModel, VectorDatabase

# Initialize embedding model
model = EmbeddingModel(dimension=768)

# Initialize vector database
vector_db = VectorDatabase(
    db_url="postgresql://tsukuyomi_user:your_password@localhost/tsukuyomi",
    dimension=768
)

# Create RAG system
rag = RAGSystem(model, vector_db)

# Migrate existing memories to RAG
def migrate_memories_to_rag():
    """Migrate existing memories to RAG system."""
    # Get memories from database
    conn = psycopg2.connect("postgresql://...")
    cur = conn.cursor()

    cur.execute("SELECT id, text, metadata FROM memories")
    memories = cur.fetchall()

    for mem_id, text, metadata in memories:
        rag.store_memory(mem_id, "memory", text, metadata)

    conn.close()
    print(f"Migrated {len(memories)} memories to RAG")

migrate_memories_to_rag()
```

### Task 2: Set Up SaveWorld/LoadWorld

```python
# Configure SaveWorld/LoadWorld
from tsukuyomi.persistence import SaveLoadManager

save_load_manager = SaveLoadManager(
    db_url="postgresql://...",
    max_saves=10
)

# Create initial checkpoint
save_load_manager.save_world("initial_checkpoint")

# Set up automatic saves
def setup_automatic_saves(interval=100):
    """Set up automatic saves at intervals."""
    # This would be integrated into your tick loop
    if current_tick % interval == 0:
        save_load_manager.save_world(f"checkpoint_{current_tick}")
```

### Task 3: Update Monitoring

```python
# Monitor PostgreSQL performance
import psycopg2
import time

def monitor_postgresql():
    """Monitor PostgreSQL performance."""
    conn = psycopg2.connect("postgresql://...")
    cur = conn.cursor()

    # Check connection count
    cur.execute("""
        SELECT count(*)
        FROM pg_stat_activity
        WHERE datname = 'tsukuyomi'
    """)
    connections = cur.fetchone()[0]

    # Check table sizes
    cur.execute("""
        SELECT
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    table_sizes = cur.fetchall()

    print(f"Connections: {connections}")
    print("Table sizes:")
    for table, size in table_sizes:
        print(f"  {table}: {size}")

    conn.close()

# Run monitoring
monitor_postgresql()
```

### Task 4: Document Changes

Update documentation:

```markdown
# Migration Summary

- Migrated from SQLite to PostgreSQL
- Date: 2026-02-15
- Ticks migrated: 500
- Actors migrated: 50
- Objects migrated: 100

New Features:
- RAG system for long-term memory
- SaveWorld/LoadWorld for state persistence
- Vector embeddings for semantic search

Performance Improvements:
- ~10x faster queries
- Support for 100+ concurrent agents
- Efficient indexing

Next Steps:
- Train RAG model on simulation data
- Set up automatic backups
- Monitor performance
```

## Rollback Procedure

If migration fails, roll back to Phase 2:

### Step 1: Stop Phase 3 Services

```bash
# Stop Fate Engine
pkill -f fate_engine.py

# Stop any other services
```

### Step 2: Restore SQLite Database

```bash
# Restore backup
cp backups/phase2_to_phase3/tsukuyomi_history_backup.db tsukuyomi_history.db

# Verify integrity
python3 -c "import sqlite3; conn = sqlite3.connect('tsukuyomi_history.db'); print(conn.execute('SELECT COUNT(*) FROM ticks').fetchone()[0])"
```

### Step 3: Revert Configuration

```bash
# .env
TSUKUYOMI_DB_TYPE=sqlite
TSUKUYOMI_DB_PATH=tsukuyomi_history.db
TSUKUYOMI_RAG_ENABLED=false
TSUKUYOMI_SAVELOAD_ENABLED=false
```

### Step 4: Restart Phase 2 Services

```bash
# Restart Fate Engine
python3 tsukuyomi/core/fate_engine.py

# Verify functionality
curl http://localhost:50051/health
```

## Troubleshooting

### Issue: Migration Script Fails

**Error:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Start PostgreSQL
sudo service postgresql start

# Check connection
psql -U tsukuyomi_user -d tsukuyomi -c "SELECT 1;"
```

### Issue: Vector Extension Not Found

**Error:**
```
ERROR: extension "vector" does not exist
```

**Solution:**
```bash
# Install pgvector
cd /path/to/pgvector
make
sudo make install

# Enable extension
sudo -u postgres psql -d tsukuyomi -c "CREATE EXTENSION vector;"
```

### Issue: Data Loss During Migration

**Error:**
```
Validation failed: Ticks mismatch
```

**Solution:**
```bash
# Check logs
tail -f migration.log

# Verify backup
sqlite3 backups/phase2_to_phase3/tsukuyomi_history_backup.db "SELECT COUNT(*) FROM ticks;"

# Re-run migration after fixing issue
python3 migrate_to_phase3.py
```

### Issue: Performance Degradation

**Error:**
```
Queries are slow after migration
```

**Solution:**
```sql
-- Check if indexes exist
SELECT indexname FROM pg_indexes WHERE tablename = 'ticks';

-- Recreate indexes if needed
CREATE INDEX IF NOT EXISTS idx_ticks_timestamp ON ticks(timestamp DESC);

-- Vacuum database
VACUUM ANALYZE;
```

## Conclusion

Successful migration to Phase 3 provides:
- Robust PostgreSQL persistence
- RAG capabilities for long-term memory
- SaveWorld/LoadWorld for state management
- Improved performance and scalability

Remember to:
- Keep backups until migration is verified
- Monitor performance after migration
- Document any custom modifications
- Train team on new features

---

**Version:** 3.0
**Last Updated:** 2026-02-15
**Phase:** Tsukuyomi V2 Phase 3 (Persistence & Scale)
