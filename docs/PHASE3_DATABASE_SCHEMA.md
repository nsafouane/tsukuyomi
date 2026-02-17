# Tsukuyomi V2 Phase 3 - Database Schema Documentation

## Overview

This document describes the PostgreSQL database schema for Tsukuyomi V2 Phase 3 (Persistence & Scale). The schema supports persistent storage of simulation state, world snapshots, and RAG (Retrieval-Augmented Generation) vector embeddings.

## Design Principles

1. **ACID Compliance**: All operations ensure atomicity, consistency, isolation, and durability
2. **Performance**: Optimized with indexes, foreign keys, and appropriate data types
3. **Scalability**: Designed to support 100+ concurrent agents and long-running simulations
4. **Migration Path**: Compatible with SQLite-based Phase 2 storage for smooth upgrades
5. **JSONB Usage**: JSONB columns for flexible metadata and JSON data storage

## Schema Overview

### Core Tables

#### `actors`
Stores information about all agents in the simulation.

```sql
CREATE TABLE actors (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    state VARCHAR(50) NOT NULL,
    current_location VARCHAR(255),
    inventory JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tick_number INTEGER NOT NULL
);

CREATE INDEX idx_actors_location ON actors(current_location);
CREATE INDEX idx_actors_state ON actors(state);
```

**Columns:**
- `id`: Unique identifier (UUID) for the actor
- `name`: Human-readable name
- `x`, `y`: Position coordinates in the world
- `state`: Current state (e.g., "IDLE", "WALKING", "INTERACTING")
- `current_location`: Name of current location (e.g., "tavern", "market")
- `inventory`: JSONB array of item IDs in the actor's possession
- `created_at`: Timestamp when actor was created
- `updated_at`: Timestamp of last update
- `tick_number`: Simulation tick when this record was created

#### `environment_objects`
Stores information about environmental objects (props, doors, terrain).

```sql
CREATE TABLE environment_objects (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    interactive BOOLEAN DEFAULT FALSE,
    properties JSONB DEFAULT '{}'::jsonb,
    display_name VARCHAR(255),
    state VARCHAR(50),
    owner_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tick_number INTEGER NOT NULL
);

CREATE INDEX idx_objects_type ON environment_objects(type);
CREATE INDEX idx_objects_interactive ON environment_objects(interactive);
CREATE INDEX idx_objects_owner ON environment_objects(owner_id);
```

**Columns:**
- `id`: Unique identifier for the object
- `type`: Object type (e.g., "chest", "door", "weapon")
- `x`, `y`: Position coordinates
- `interactive`: Whether the object can be interacted with
- `properties`: JSONB object with custom properties
- `display_name`: Human-readable name
- `state`: Current state (e.g., "open", "closed", "locked")
- `owner_id`: Foreign key to actors table (if owned by an actor)
- `created_at`, `updated_at`: Timestamps
- `tick_number`: Simulation tick

#### `locations`
Stores information about world locations.

```sql
CREATE TABLE locations (
    name VARCHAR(255) PRIMARY KEY,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_locations_pos ON locations(x, y);
```

**Columns:**
- `name`: Unique name of the location
- `x`, `y`: Position coordinates
- `description`: Description of the location
- `created_at`: Creation timestamp

#### `ticks`
Stores world state snapshots at each simulation tick.

```sql
CREATE TABLE ticks (
    tick_number INTEGER PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    world_state_json JSONB NOT NULL,
    pending_proposals_json JSONB DEFAULT '[]'::jsonb,
    resolutions_json JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ticks_timestamp ON ticks(timestamp DESC);
CREATE INDEX idx_ticks_created ON ticks(created_at DESC);
```

**Columns:**
- `tick_number`: Unique tick identifier
- `timestamp`: Tick timestamp
- `world_state_json`: Complete world state as JSONB
- `pending_proposals_json`: Pending proposals as JSONB array
- `resolutions_json`: Resolved proposals as JSONB array
- `created_at`: Insertion timestamp

**Indexes:**
- `idx_ticks_timestamp`: For querying by time range
- `idx_ticks_created`: For recency queries

#### `proposals`
Stores actor proposals for world state changes.

```sql
CREATE TABLE proposals (
    id UUID PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    tick_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_proposals_actor ON proposals(actor_id);
CREATE INDEX idx_proposals_tick ON proposals(tick_number);
CREATE INDEX idx_proposals_action ON proposals(action_type);
```

**Columns:**
- `id`: Unique proposal identifier (UUID)
- `actor_id`: Foreign key to actors
- `tick_number`: Simulation tick when proposal was made
- `action_type`: Type of action (e.g., "MOVE", "INTERACT")
- `parameters`: JSONB object with action parameters
- `timestamp`: Proposal timestamp
- `created_at`: Insertion timestamp

**Indexes:**
- `idx_proposals_actor`: For querying by actor
- `idx_proposals_tick`: For querying by tick
- `idx_proposals_action`: For querying by action type

#### `resolutions`
Stores fate resolution results for proposals.

```sql
CREATE TABLE resolutions (
    id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    tick_number INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    outcome JSONB DEFAULT '{}'::jsonb,
    reason TEXT,
    modified_action JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_resolutions_proposal ON resolutions(proposal_id);
CREATE INDEX idx_resolutions_actor ON resolutions(actor_id);
CREATE INDEX idx_resolutions_tick ON resolutions(tick_number);
CREATE INDEX idx_resolutions_success ON resolutions(success);
```

**Columns:**
- `id`: Unique resolution identifier (UUID)
- `proposal_id`: Foreign key to proposals
- `actor_id`: Foreign key to actors
- `tick_number`: Simulation tick when resolution occurred
- `success`: Whether the resolution was successful
- `outcome`: JSONB object with outcome details
- `reason`: Text explanation of resolution
- `modified_action`: JSONB object if action was modified by fate
- `timestamp`: Resolution timestamp
- `created_at`: Insertion timestamp

**Indexes:**
- `idx_resolutions_proposal`: For querying by proposal
- `idx_resolutions_actor`: For querying by actor
- `idx_resolutions_tick`: For querying by tick
- `idx_resolutions_success`: For filtering by success/failure

#### `interactions`
Stores interaction events between actors/objects.

```sql
CREATE TABLE interactions (
    id UUID PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    tick_number INTEGER NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_actor ON interactions(actor_id);
CREATE INDEX idx_interactions_target ON interactions(target_id);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);
CREATE INDEX idx_interactions_tick ON interactions(tick_number);
```

**Columns:**
- `id`: Unique interaction identifier (UUID)
- `actor_id`: Foreign key to actors
- `interaction_type`: Type of interaction (e.g., "talk", "trade", "use")
- `target_id`: ID of target (actor or object)
- `target_type`: Type of target ("actor" or "object")
- `tick_number`: Simulation tick
- `data`: JSONB object with interaction data
- `timestamp`: Interaction timestamp
- `created_at`: Insertion timestamp

**Indexes:**
- `idx_interactions_actor`: For querying by actor
- `idx_interactions_target`: For querying by target
- `idx_interactions_type`: For querying by interaction type
- `idx_interactions_tick`: For querying by tick

#### `relationships`
Stores relationship data between actors.

```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),
    last_updated_tick INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(actor_id, target_id, relationship_type)
);

CREATE INDEX idx_relationships_actor ON relationships(actor_id);
CREATE INDEX idx_relationships_target ON relationships(target_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_relationships_strength ON relationships(strength);
```

**Columns:**
- `id`: Unique relationship identifier (UUID)
- `actor_id`: Foreign key to actors (source)
- `target_id`: Foreign key to actors (target)
- `relationship_type`: Type of relationship (e.g., "friend", "enemy", "neutral")
- `strength`: Relationship strength (0.0 to 1.0)
- `last_updated_tick`: Last tick when relationship was updated
- `metadata`: JSONB object with custom metadata
- `created_at`, `updated_at`: Timestamps

**Constraints:**
- `CHECK (strength >= 0.0 AND strength <= 1.0)`: Ensures strength is within valid range
- `UNIQUE(actor_id, target_id, relationship_type)`: Prevents duplicate relationships

**Indexes:**
- `idx_relationships_actor`: For querying by actor
- `idx_relationships_target`: For querying by target
- `idx_relationships_type`: For querying by relationship type
- `idx_relationships_strength`: For sorting by strength

### RAG Tables

#### `memories`
Stores long-term memories for RAG system.

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0.0 AND importance <= 1.0),
    tick_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_memories_actor ON memories(actor_id);
CREATE INDEX idx_memories_entity ON memories(entity_type, entity_id);
CREATE INDEX idx_memories_tick ON memories(tick_number);
CREATE INDEX idx_memories_importance ON memories(importance);
CREATE INDEX idx_memories_gin ON memories USING gin(metadata);
```

**Columns:**
- `id`: Unique memory identifier (UUID)
- `actor_id`: Foreign key to actors (if memory is associated with an actor)
- `entity_type`: Type of entity ("memory", "fact", "event")
- `entity_id`: Entity identifier
- `text`: Text content of the memory
- `importance`: Importance score (0.0 to 1.0)
- `tick_number`: Simulation tick when memory was created
- `created_at`: Creation timestamp
- `metadata`: JSONB object with custom metadata

**Indexes:**
- `idx_memories_actor`: For querying by actor
- `idx_memories_entity`: For querying by entity
- `idx_memories_tick`: For querying by tick
- `idx_memories_importance`: For sorting by importance
- `idx_memories_gin`: GIN index for fast JSONB queries

#### `vector_embeddings`
Stores vector embeddings for semantic search.

```sql
CREATE TABLE vector_embeddings (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    embedding VECTOR(768) NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_vector_entity ON vector_embeddings(entity_type, entity_id);
CREATE INDEX idx_vector_embedding ON vector_embeddings USING ivfflat(embedding vector_cosine_ops);
```

**Columns:**
- `id`: Unique embedding identifier (UUID)
- `entity_type`: Type of entity ("memory", "actor", "object")
- `entity_id`: Entity identifier
- `embedding`: Vector embedding (768 dimensions)
- `embedding_dimension`: Dimension of the embedding
- `created_at`: Creation timestamp
- `metadata`: JSONB object with custom metadata

**Indexes:**
- `idx_vector_entity`: For querying by entity
- `idx_vector_embedding`: IVFFlat index for efficient vector similarity search

**Note:** Requires the `pgvector` extension for PostgreSQL.

### Metadata Tables

#### `metadata`
Stores system metadata and configuration.

```sql
CREATE TABLE metadata (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Columns:**
- `key`: Metadata key
- `value`: Metadata value
- `updated_at`: Last update timestamp

**Example Records:**
```sql
INSERT INTO metadata (key, value) VALUES
('schema_version', '3.0'),
('last_tick', '1000'),
('simulation_id', '550e8400-e29b-41d4-a716-446655440000');
```

## PostgreSQL Extensions

### pgvector
Required for vector similarity search.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Functions

#### `update_updated_at_column()`
Automatically updates the `updated_at` column.

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
```

Apply to tables with `updated_at` columns:

```sql
CREATE TRIGGER update_actors_updated_at BEFORE UPDATE ON actors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_environment_objects_updated_at BEFORE UPDATE ON environment_objects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_relationships_updated_at BEFORE UPDATE ON relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Migration from SQLite

### SQLite Schema (Phase 2)
```sql
CREATE TABLE ticks (
    tick_number INTEGER PRIMARY KEY,
    timestamp REAL,
    tick_state_json TEXT
);
```

### Migration Steps

1. **Backup SQLite Database**
   ```bash
   cp tsukuyomi_history.db tsukuyomi_history_backup.db
   ```

2. **Create PostgreSQL Schema**
   ```bash
   psql -U postgres -d tsukuyomi -f schema.sql
   ```

3. **Migrate Data**
   ```python
   import sqlite3
   import psycopg2
   import json

   # Connect to databases
   sqlite_conn = sqlite3.connect('tsukuyomi_history.db')
   pg_conn = psycopg2.connect("postgresql://user:pass@localhost/tsukuyomi")

   # Migrate ticks
   cur = sqlite_conn.cursor()
   pg_cur = pg_conn.cursor()

   cur.execute("SELECT tick_number, timestamp, tick_state_json FROM ticks")
   for row in cur.fetchall():
       tick_num, timestamp, tick_state_json = row

       # Parse tick state
       tick_state = json.loads(tick_state_json)

       # Insert into PostgreSQL
       pg_cur.execute("""
           INSERT INTO ticks (tick_number, timestamp, world_state_json, pending_proposals_json, resolutions_json)
           VALUES (%s, %s, %s, %s, %s)
       """, (
           tick_num,
           timestamp,
           json.dumps(tick_state.get('worldState', {})),
           json.dumps(tick_state.get('pendingProposals', [])),
           json.dumps(tick_state.get('resolutions', []))
       ))

   pg_conn.commit()
   ```

## Performance Considerations

### Indexing Strategy

1. **Foreign Keys**: All foreign key columns are indexed
2. **Query Patterns**: Indexes designed for common query patterns:
   - Query by actor
   - Query by tick number
   - Query by time range
   - Query by location
3. **JSONB**: GIN indexes for JSONB columns with complex queries

### Connection Pooling

Use connection pooling for optimal performance:

```python
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    dsn="postgresql://user:pass@localhost/tsukuyomi"
)
```

### Batch Operations

Use batch inserts for better performance:

```python
cursor.execute("""
    INSERT INTO actors (id, name, x, y, state, tick_number)
    VALUES %s
""", [(id1, name1, x1, y1, state1, tick1), ...])
```

### Vector Search Optimization

For vector similarity search with `pgvector`:

1. **IVFFlat Index**: Use for large datasets (>100k vectors)
2. **HNSW Index**: Use for faster queries (requires pgvector >= 0.5.0)
3. **Tuning**: Adjust `lists` parameter for IVFFlat based on dataset size

```sql
CREATE INDEX idx_vector_embedding_hnsw ON vector_embeddings
    USING hnsw(embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

## Backup and Recovery

### Backup

```bash
# Full backup
pg_dump -U postgres -F c -b -v -f tsukuyomi_backup.dump tsukuyomi

# Schema-only backup
pg_dump -U postgres -s tsukuyomi > schema_backup.sql
```

### Restore

```bash
# Restore from backup
pg_restore -U postgres -d tsukuyomi -v tsukuyomi_backup.dump
```

## Monitoring Queries

### Check Table Sizes
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Index Usage
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Check Slow Queries
```sql
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%tsukuyomi%'
ORDER BY mean_time DESC
LIMIT 10;
```

## Conclusion

This schema provides a robust foundation for Tsukuyomi V2 Phase 3, supporting:
- Persistent storage of simulation state
- Efficient querying of historical data
- Vector similarity search for RAG
- Scalability to 100+ concurrent agents
- Smooth migration from Phase 2 SQLite storage

---

**Version:** 3.0
**Last Updated:** 2026-02-15
**Phase:** Tsukuyomi V2 Phase 3 (Persistence & Scale)
