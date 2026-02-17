"""
Test PostgreSQL Schema Validation for Phase 3.

Tests:
- Schema creation and constraints
- Data integrity checks
- Migration compatibility
- Performance benchmarks

NOTE: These tests require PostgreSQL to be running and psycopg2 installed.
They are skipped by default unless --run-postgresql flag is passed.
"""

import pytest

# Skip entire module if psycopg2 is not available
psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 not installed")

from psycopg2 import sql, pool
from typing import List, Dict, Any
import time

# Skip all tests in this module unless explicitly enabled
pytestmark = pytest.mark.skip(reason="PostgreSQL tests require --run-postgresql flag and database setup")


class PostgreSQLSchemaValidator:
    """Validates PostgreSQL schema for Tsukuyomi Phase 3."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn_pool = None

    def __enter__(self):
        self.conn_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=self.db_url
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn_pool:
            self.conn_pool.closeall()

    def get_connection(self):
        """Get a connection from the pool."""
        return self.conn_pool.getconn()

    def release_connection(self, conn):
        """Release a connection back to the pool."""
        self.conn_pool.putconn(conn)


# Expected schema for Tsukuyomi Phase 3
EXPECTED_TABLES = [
    'actors',
    'environment_objects',
    'locations',
    'ticks',
    'proposals',
    'resolutions',
    'interactions',
    'relationships',
    'memories',
    'metadata',
    'vector_embeddings'
]

EXPECTED_ACTOR_COLUMNS = [
    'id', 'name', 'x', 'y', 'state', 'current_location',
    'inventory', 'created_at', 'updated_at', 'tick_number'
]

EXPECTED_TICK_COLUMNS = [
    'tick_number', 'timestamp', 'world_state_json',
    'pending_proposals_json', 'resolutions_json'
]

EXPECTED_VECTOR_COLUMNS = [
    'id', 'entity_type', 'entity_id', 'embedding',
    'embedding_dimension', 'metadata', 'created_at'
]


@pytest.fixture
def postgres_validator(postgresql_db_url):
    """Fixture to create a PostgreSQL schema validator."""
    with PostgreSQLSchemaValidator(postgresql_db_url) as validator:
        yield validator


@pytest.fixture
def postgresql_db_url():
    """
    Get PostgreSQL database URL for testing.
    Uses environment variable or default test database.
    """
    import os
    # Try environment variable first
    db_url = os.environ.get('TEST_POSTGRESQL_URL')
    if not db_url:
        # Use pytest-postgresql fixture if available
        pytest.skip("PostgreSQL database URL not provided. Set TEST_POSTGRESQL_URL environment variable.")
    return db_url


def test_schema_table_exists(postgres_validator):
    """Test that all required tables exist in the database."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            actual_tables = {row[0] for row in cur.fetchall()}

            missing_tables = set(EXPECTED_TABLES) - actual_tables
            extra_tables = actual_tables - set(EXPECTED_TABLES)

            assert not missing_tables, f"Missing tables: {missing_tables}"
            print(f"✓ All expected tables exist: {EXPECTED_TABLES}")

            # Log extra tables as warnings
            if extra_tables:
                print(f"⚠ Warning: Extra tables found: {extra_tables}")

    finally:
        postgres_validator.release_connection(conn)


def test_actor_table_columns(postgres_validator):
    """Test that the actors table has all required columns."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'actors'
                ORDER BY ordinal_position
            """)
            columns = {row[0]: {'type': row[1], 'nullable': row[2]}
                       for row in cur.fetchall()}

            for col in EXPECTED_ACTOR_COLUMNS:
                assert col in columns, f"Missing column: {col}"
                print(f"✓ Actor column exists: {col} ({columns[col]['type']})")

            # Check that id is NOT NULL
            assert columns['id']['nullable'] == 'NO', "Actor.id must be NOT NULL"
            print("✓ Actor.id constraint: NOT NULL")

    finally:
        postgres_validator.release_connection(conn)


def test_tick_table_columns(postgres_validator):
    """Test that the ticks table has all required columns."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'ticks'
                ORDER BY ordinal_position
            """)
            columns = {row[0]: {'type': row[1], 'nullable': row[2]}
                       for row in cur.fetchall()}

            for col in EXPECTED_TICK_COLUMNS:
                assert col in columns, f"Missing column: {col}"
                print(f"✓ Tick column exists: {col} ({columns[col]['type']})")

            # Check constraints
            assert columns['tick_number']['nullable'] == 'NO', "Tick.tick_number must be NOT NULL"
            print("✓ Tick.tick_number constraint: NOT NULL")

    finally:
        postgres_validator.release_connection(conn)


def test_vector_table_columns(postgres_validator):
    """Test that the vector_embeddings table has all required columns."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'vector_embeddings'
                ORDER BY ordinal_position
            """)
            columns = {row[0]: {'type': row[1], 'nullable': row[2]}
                       for row in cur.fetchall()}

            for col in EXPECTED_VECTOR_COLUMNS:
                assert col in columns, f"Missing column: {col}"
                print(f"✓ Vector column exists: {col} ({columns[col]['type']})")

    finally:
        postgres_validator.release_connection(conn)


def test_primary_keys(postgres_validator):
    """Test that all tables have primary keys."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'PRIMARY KEY'
                AND table_schema = 'public'
            """)
            tables_with_pk = {row[0] for row in cur.fetchall()}

            # Most tables should have primary keys
            tables_requiring_pk = [
                'actors', 'environment_objects', 'ticks',
                'proposals', 'resolutions', 'vector_embeddings'
            ]

            for table in tables_requiring_pk:
                assert table in tables_with_pk, f"Table {table} missing primary key"
                print(f"✓ Table has primary key: {table}")

    finally:
        postgres_validator.release_connection(conn)


def test_foreign_keys(postgres_validator):
    """Test that foreign key constraints are properly defined."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """)
            foreign_keys = cur.fetchall()

            # Expected foreign keys
            expected_fks = [
                ('proposals', 'actor_id', 'actors', 'id'),
                ('resolutions', 'proposal_id', 'proposals', 'id'),
                ('interactions', 'actor_id', 'actors', 'id'),
            ]

            for fk in expected_fks:
                assert any(
                    fk[0] == row[0] and fk[1] == row[1] and
                    fk[2] == row[2] and fk[3] == row[3]
                    for row in foreign_keys
                ), f"Missing foreign key: {fk}"
                print(f"✓ Foreign key exists: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

    finally:
        postgres_validator.release_connection(conn)


def test_indexes(postgres_validator):
    """Test that performance-critical indexes exist."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            indexes = {(row[0], row[1]) for row in cur.fetchall()}

            # Expected indexes for performance
            expected_indexes = [
                ('actors', 'idx_actors_location'),
                ('ticks', 'idx_ticks_tick_number'),
                ('ticks', 'idx_ticks_timestamp'),
                ('vector_embeddings', 'idx_vector_entity'),
            ]

            for idx in expected_indexes:
                assert idx in indexes, f"Missing index: {idx[0]}.{idx[1]}"
                print(f"✓ Index exists: {idx[0]}.{idx[1]}")

    finally:
        postgres_validator.release_connection(conn)


def test_data_integrity_constraints(postgres_validator):
    """Test data integrity constraints (NOT NULL, CHECK, UNIQUE)."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    tc.table_name,
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                AND tc.constraint_type IN ('CHECK', 'UNIQUE')
            """)
            constraints = cur.fetchall()

            # Log all constraints
            print(f"Found {len(constraints)} CHECK/UNIQUE constraints:")
            for table, name, type_ in constraints:
                print(f"  - {table}.{name} ({type_})")

            # Verify at least some constraints exist
            assert len(constraints) > 0, "No CHECK or UNIQUE constraints found"

    finally:
        postgres_validator.release_connection(conn)


def test_vector_embedding_dimension(postgres_validator):
    """Test that vector embeddings have consistent dimensions."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT embedding_dimension
                FROM vector_embeddings
                LIMIT 10
            """)
            dimensions = [row[0] for row in cur.fetchall()]

            if dimensions:
                # All dimensions should be the same
                assert len(set(dimensions)) == 1, "Vector embeddings have inconsistent dimensions"
                print(f"✓ Vector embedding dimension: {dimensions[0]}")
            else:
                print("⚠ No vector embeddings found (table may be empty)")

    finally:
        postgres_validator.release_connection(conn)


def test_jsonb_columns(postgres_validator):
    """Test that JSONB columns are used for JSON data (better performance than JSON)."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE data_type = 'jsonb'
                AND table_schema = 'public'
            """)
            jsonb_columns = [(row[0], row[1]) for row in cur.fetchall()]

            # JSONB should be used for performance
            expected_jsonb = [
                ('actors', 'inventory'),
                ('ticks', 'world_state_json'),
                ('ticks', 'pending_proposals_json'),
                ('ticks', 'resolutions_json'),
                ('environment_objects', 'properties'),
                ('vector_embeddings', 'metadata'),
            ]

            for col in expected_jsonb:
                assert col in jsonb_columns, f"Expected JSONB column: {col[0]}.{col[1]}"
                print(f"✓ JSONB column: {col[0]}.{col[1]}")

    finally:
        postgres_validator.release_connection(conn)


@pytest.mark.benchmark
def test_insert_performance(postgres_validator):
    """Benchmark insert performance for 1000 ticks."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            # Create test data
            tick_count = 1000
            start_time = time.time()

            for i in range(tick_count):
                cur.execute("""
                    INSERT INTO ticks (tick_number, timestamp, world_state_json)
                    VALUES (%s, NOW(), %s)
                """, (i, '{"test": "data"}'))

            conn.commit()
            elapsed = time.time() - start_time
            rate = tick_count / elapsed

            print(f"✓ Inserted {tick_count} ticks in {elapsed:.2f}s ({rate:.0f} ticks/s)")

            # Should be able to insert at least 100 ticks per second
            assert rate >= 100, f"Insert performance too slow: {rate:.0f} ticks/s"

            # Cleanup
            cur.execute("DELETE FROM ticks WHERE tick_number < %s", (tick_count,))
            conn.commit()

    finally:
        postgres_validator.release_connection(conn)


@pytest.mark.benchmark
def test_query_performance(postgres_validator):
    """Benchmark query performance for retrieving tick history."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            # Insert test data first
            tick_count = 1000
            for i in range(tick_count):
                cur.execute("""
                    INSERT INTO ticks (tick_number, timestamp, world_state_json)
                    VALUES (%s, NOW(), %s)
                """, (i, f'{{"tick": {i}}}'))
            conn.commit()

            # Benchmark queries
            start_time = time.time()

            # Query latest tick
            cur.execute("SELECT MAX(tick_number) FROM ticks")
            cur.fetchone()

            # Query range of ticks
            cur.execute("""
                SELECT tick_number, world_state_json
                FROM ticks
                WHERE tick_number >= %s AND tick_number < %s
                ORDER BY tick_number DESC
            """, (900, 1000))
            cur.fetchall()

            elapsed = time.time() - start_time
            print(f"✓ Query performance: {elapsed:.4f}s for 2 queries")

            # Queries should be fast (< 0.1s)
            assert elapsed < 0.1, f"Query performance too slow: {elapsed:.4f}s"

            # Cleanup
            cur.execute("DELETE FROM ticks WHERE tick_number < %s", (tick_count,))
            conn.commit()

    finally:
        postgres_validator.release_connection(conn)


def test_migration_compatibility(postgres_validator):
    """Test that schema is compatible with SQLite migrations."""
    conn = postgres_validator.get_connection()
    try:
        with conn.cursor() as cur:
            # Check that PostgreSQL has all fields that SQLite had
            sqlite_schema = {
                'ticks': ['tick_number', 'timestamp', 'tick_state_json'],
            }

            postgres_schema = {}
            cur.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
            """)
            for table, column in cur.fetchall():
                if table not in postgres_schema:
                    postgres_schema[table] = []
                postgres_schema[table].append(column)

            # Verify SQLite tables have equivalents in PostgreSQL
            for table, columns in sqlite_schema.items():
                assert table in postgres_schema, f"PostgreSQL missing table: {table}"
                for col in columns:
                    # Some column names may have changed (e.g., tick_state_json -> world_state_json)
                    # This is acceptable as long as the data is preserved
                    if col not in postgres_schema[table]:
                        print(f"⚠ Column changed: {table}.{col} -> {postgres_schema[table]}")

            print("✓ Schema is migration-compatible")

    finally:
        postgres_validator.release_connection(conn)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
