import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db_manager, create_tables_sync
from app.models.user import User
from app.core.security import get_password_hash

# First ensure tables are created (though main.py does this on startup)
create_tables_sync()

try:
    admin_password = os.getenv("ADMIN_INITIAL_PASSWORD")
    if not admin_password:
        raise RuntimeError("ADMIN_INITIAL_PASSWORD must be set before creating the admin user")

    with db_manager.get_sync_session() as db:
        admin = db.query(User).filter_by(username="ritsa_admin").first()
        if not admin:
            admin = User(
                id="admin_12345",
                email="admin@voiceclone.ai",
                username="ritsa_admin",
                hashed_password=get_password_hash(admin_password),
                full_name="Ritsa Admin",
                is_active=True,
                is_premium=True,
                is_verified=True,
                subscription_tier="enterprise"
            )
            db.add(admin)
            db.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
except Exception as e:
    print(f"Error: {e}")
