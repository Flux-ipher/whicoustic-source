"""
User model for Whicoustic platform.
"""

from datetime import datetime
import os
import sqlite3
import uuid
import logging
from sqlalchemy import Column, String, Boolean, DateTime, Text, Date, Float
from ..core.database import Base

logger = logging.getLogger(__name__)


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    firebase_uid = Column(String(128), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    dob = Column(Date, nullable=True)
    display_name = Column(String(255), nullable=True)
    avatar = Column(String(512), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    role = Column(String(50), default="user")
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    subscription_tier = Column(String(50), default="free")

    # Milestone 1 onboarding columns
    is_onboarded = Column(Boolean, default=False, nullable=False)
    onboarded_at = Column(DateTime, nullable=True)
    royalty_floor_pct = Column(Float, nullable=True, default=18.5)
    voice_category = Column(String(100), nullable=True)
    vault_key = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"


def migrate_sqlite_user_table(db_path: str = None) -> bool:
    """Migrate SQLite users table schema safely by adding any missing Milestone 1 columns."""
    candidate_paths = [
        db_path,
        "backend/vcaas_dev2.db",
        "vcaas_dev2.db",
        os.path.join(os.path.dirname(__file__), "..", "..", "vcaas_dev2.db"),
    ]
    migrated_any = False
    new_columns = [
        ("is_onboarded", "BOOLEAN DEFAULT 0 NOT NULL"),
        ("onboarded_at", "DATETIME"),
        ("royalty_floor_pct", "REAL DEFAULT 18.5"),
        ("voice_category", "VARCHAR(100)"),
        ("vault_key", "VARCHAR(255)"),
    ]

    for p in candidate_paths:
        if not p or not os.path.exists(p):
            continue
        try:
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(users)")
            existing = {row[1] for row in cur.fetchall()}
            if not existing:
                conn.close()
                continue
            for col_name, col_sql in new_columns:
                if col_name not in existing:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_sql}")
                    migrated_any = True
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning(f"Failed SQLite migration for {p}: {exc}")

    return migrated_any


# Automatically perform migration on import if SQLite database files are found
try:
    migrate_sqlite_user_table()
except Exception:
    pass


