"""
Database configuration for Whicoustic platform.
Handles Supabase PostgreSQL connection with resilient automatic fallback to SQLite vcaas_dev2.db.
"""

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from typing import AsyncGenerator, Generator, Tuple, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

SQLITE_ASYNC_URL = "sqlite+aiosqlite:///./vcaas_dev2.db"
SQLITE_SYNC_URL = "sqlite:///./vcaas_dev2.db"


def _resolve_target_urls() -> Tuple[Optional[str], Optional[str]]:
    """Determine candidate database URLs from Supabase configuration or DATABASE_URL."""
    candidate = (
        getattr(settings, "SUPABASE_DB_URL", None)
        or (settings.SUPABASE_URL if (getattr(settings, "SUPABASE_URL", None) and ("postgres" in str(settings.SUPABASE_URL))) else None)
        or (settings.DATABASE_URL if (getattr(settings, "DATABASE_URL", None) and not settings.DATABASE_URL.startswith("sqlite")) else None)
    )
    if not candidate:
        return None, None

    clean = str(candidate).strip()
    if clean.startswith("postgres://"):
        clean = "postgresql://" + clean[len("postgres://"):]

    if "+asyncpg" in clean:
        async_url = clean
        sync_url = clean.replace("+asyncpg", "")
    elif "+psycopg2" in clean:
        sync_url = clean
        async_url = clean.replace("+psycopg2", "+asyncpg")
    elif clean.startswith("postgresql://"):
        async_url = clean.replace("postgresql://", "postgresql+asyncpg://")
        sync_url = clean
    else:
        async_url = clean
        sync_url = clean

    return async_url, sync_url


def _create_sqlite_engines(db_url: Optional[str] = None):
    """Create local SQLite sync and async engines with thread-safe pooling."""
    async_url = db_url or SQLITE_ASYNC_URL
    sync_url = async_url.replace("+aiosqlite", "")

    # For in-memory databases, StaticPool is required to retain state across sessions.
    # For file-based SQLite databases, NullPool creates dedicated connections per session,
    # eliminating thread cursor corruption under FastAPI worker pools.
    is_memory = ":memory:" in sync_url
    pool_class = StaticPool if is_memory else NullPool
    connect_args = {"check_same_thread": False, "timeout": 30.0}

    a_eng = create_async_engine(
        async_url,
        echo=settings.DEBUG,
        connect_args=connect_args,
        poolclass=pool_class,
        pool_pre_ping=True,
    )
    s_eng = create_engine(
        sync_url,
        connect_args=connect_args,
        poolclass=pool_class,
        echo=settings.DEBUG,
    )
    return a_eng, s_eng, "sqlite"


def init_engines():
    """Initialize database engines with Supabase PostgreSQL and automatic SQLite fallback."""
    candidate_async, candidate_sync = _resolve_target_urls()

    if not candidate_sync:
        if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"):
            try:
                return _create_sqlite_engines(settings.DATABASE_URL)
            except Exception as e:
                logger.warning(
                    f"Error configuring sqlite database: {e}. Falling back to local SQLite database: vcaas_dev2.db"
                )
                return _create_sqlite_engines()

        logger.info("Supabase PostgreSQL credentials unset. Falling back to local SQLite database: vcaas_dev2.db")
        return _create_sqlite_engines()

    # Attempt Supabase / PostgreSQL connection
    try:
        s_eng = create_engine(
            candidate_sync,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3} if "postgres" in candidate_sync else {},
            echo=settings.DEBUG,
        )
        with s_eng.connect() as conn:
            conn.execute(text("SELECT 1"))

        a_eng = create_async_engine(
            candidate_async,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        logger.info("Successfully connected to Supabase PostgreSQL database.")
        return a_eng, s_eng, "postgresql"
    except Exception as exc:
        logger.warning(
            f"Failed to connect to Supabase/PostgreSQL ({candidate_sync}): {exc}. "
            "Falling back to local SQLite database: vcaas_dev2.db"
        )
        return _create_sqlite_engines()


async_engine, sync_engine, active_db_type = init_engines()

# Create session makers
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db() -> Generator:
    """Dependency to get sync database session (for compatibility)"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_tables():
    """Create all database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_tables_sync():
    """Create all tables synchronously"""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully")


class DatabaseManager:
    """Database management utilities."""

    def __init__(self):
        self.async_engine = async_engine
        self.sync_engine = sync_engine
        self.AsyncSessionLocal = AsyncSessionLocal
        self.SyncSessionLocal = SyncSessionLocal
        self.db_type = active_db_type

    def get_sync_session(self):
        """Get a sync database session."""
        return SyncSessionLocal()

    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with sync_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_connection_info(self) -> dict:
        """Get database connection information."""
        url = sync_engine.url
        is_fallback = (
            self.db_type == "sqlite" and
            bool(getattr(settings, "SUPABASE_URL", None) or getattr(settings, "SUPABASE_DB_URL", None))
        )
        return {
            "drivername": url.drivername,
            "host": url.host,
            "port": url.port,
            "database": url.database,
            "username": url.username,
            "db_type": self.db_type,
            "is_fallback": is_fallback
        }


# Global database manager instance
db_manager = DatabaseManager()

# Export engine for main.py (aliased to async_engine)
engine = async_engine
