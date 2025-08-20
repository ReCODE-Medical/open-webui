import os
import json
import logging
from contextlib import contextmanager
from typing import Any, Optional

from open_webui.internal.wrappers import register_connection
from open_webui.env import (
    OPEN_WEBUI_DIR,
    DATABASE_URL,
    DATABASE_SCHEMA,
    SRC_LOG_LEVELS,
    DATABASE_POOL_MAX_OVERFLOW,
    DATABASE_POOL_RECYCLE,
    DATABASE_POOL_SIZE,
    DATABASE_POOL_TIMEOUT,
    SUPABASE_DATABASE_URL,
)
from peewee_migrate import Router
from sqlalchemy import Dialect, create_engine, MetaData, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.sql.type_api import _T
from typing_extensions import Self

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["DB"])


class JSONField(types.TypeDecorator):
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value: Optional[_T], dialect: Dialect) -> Any:
        return json.dumps(value)

    def process_result_value(self, value: Optional[_T], dialect: Dialect) -> Any:
        if value is not None:
            return json.loads(value)

    def copy(self, **kw: Any) -> Self:
        return JSONField(self.impl.length)

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


def create_db_engine(database_url: str, is_sqlite: bool = False):
    """Helper function to create database engines with consistent configuration"""
    
    # Handle SQLCipher URLs
    if database_url.startswith("sqlite+sqlcipher://"):
        database_password = os.environ.get("DATABASE_PASSWORD")
        if not database_password or database_password.strip() == "":
            raise ValueError(
                "DATABASE_PASSWORD is required when using sqlite+sqlcipher:// URLs"
            )

        # Extract database path from SQLCipher URL
        db_path = database_url.replace("sqlite+sqlcipher://", "")
        if db_path.startswith("/"):
            db_path = db_path[1:]  # Remove leading slash for relative paths

        # Create a custom creator function that uses sqlcipher3
        def create_sqlcipher_connection():
            import sqlcipher3

            conn = sqlcipher3.connect(db_path, check_same_thread=False)
            conn.execute(f"PRAGMA key = '{database_password}'")
            return conn

        engine = create_engine(
            "sqlite://",  # Dummy URL since we're using creator
            creator=create_sqlcipher_connection,
            echo=False,
        )

        log.info("Connected to encrypted SQLite database using SQLCipher")
        return engine
    
    elif is_sqlite or "sqlite" in database_url:
        return create_engine(
            database_url, connect_args={"check_same_thread": False}
        )
    else:
        if isinstance(DATABASE_POOL_SIZE, int):
            if DATABASE_POOL_SIZE > 0:
                return create_engine(
                    database_url,
                    pool_size=DATABASE_POOL_SIZE,
                    max_overflow=DATABASE_POOL_MAX_OVERFLOW,
                    pool_timeout=DATABASE_POOL_TIMEOUT,
                    pool_recycle=DATABASE_POOL_RECYCLE,
                    pool_pre_ping=True,
                    poolclass=QueuePool,
                )
            else:
                return create_engine(
                    database_url, pool_pre_ping=True, poolclass=NullPool
                )
        else:
            return create_engine(database_url, pool_pre_ping=True)


# Workaround to handle the peewee migration
def handle_peewee_migration(DATABASE_URL):
    try:
        db = register_connection(DATABASE_URL.replace("postgresql://", "postgres://"))
        migrate_dir = OPEN_WEBUI_DIR / "internal" / "migrations"
        router = Router(db, logger=log, migrate_dir=migrate_dir)
        router.run()
        db.close()

    except Exception as e:
        log.error(f"Failed to initialize the database connection: {e}")
        log.warning(
            "Hint: If your database password contains special characters, you may need to URL-encode it."
        )
        raise
    finally:
        if db and not db.is_closed():
            db.close()
        assert db.is_closed(), "Database connection is still open."


# Initialize primary database
handle_peewee_migration(DATABASE_URL)

# Create engines for both databases
main_engine = create_db_engine(DATABASE_URL, is_sqlite="sqlite" in DATABASE_URL)
supa_engine = create_db_engine(SUPABASE_DATABASE_URL)

# Create session factories for both databases
MainSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=main_engine, expire_on_commit=False
)
SupaSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=supa_engine, expire_on_commit=False
)

metadata_obj = MetaData(schema=DATABASE_SCHEMA)
Base = declarative_base(metadata=metadata_obj)
Session = scoped_session(MainSessionLocal)
SupaSession = scoped_session(SupaSessionLocal)


def init_supa_table(tables: list):
    try:
        Base.metadata.create_all(bind=supa_engine, tables=tables)
        log.info("Supabase tables initialized successfully")
    except Exception as e:
        log.warning(f"Failed to initialize Supabase tables: {e}")
        raise


def get_main_session():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_supa_session():
    db = SupaSessionLocal()
    try:
        yield db
    finally:
        db.close()


get_db = contextmanager(get_main_session)
get_supabase_db = contextmanager(get_supa_session)