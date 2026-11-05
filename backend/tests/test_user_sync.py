from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.schemas.user import UserOut


def _make_db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_user_sync_creates_user_with_username_and_schema_shape():
    db = _make_db_session()

    payload = {
        'uid': 'firebase-uid-123',
        'email': 'alice@example.com',
        'name': 'Alice Example',
        'photo_url': 'https://example.com/avatar.png',
        'phone': '+1-555-0100',
        'provider_id': 'google.com',
    }

    user = User(
        username='alice',
        email='alice@example.com',
        firebase_uid='firebase-uid-123',
        full_name='Alice Example',
        avatar='https://example.com/avatar.png',
        phone='+1-555-0100',
    )
    db.add(user)
    db.commit()

    saved = db.query(User).filter(User.firebase_uid == payload['uid']).first()
    assert saved is not None
    assert saved.username == 'alice'
    assert saved.email == 'alice@example.com'

    response = UserOut.from_model(saved)
    assert response.id == saved.id
    assert response.uid == 'firebase-uid-123'
    assert response.name == 'Alice Example'
    assert response.photo_url == 'https://example.com/avatar.png'
    assert response.phone == '+1-555-0100'
    assert response.provider_id is None


def test_user_sync_builds_unique_username_for_same_email():
    db = _make_db_session()
    existing = User(
        username='jane',
        email='jane@example.com',
        firebase_uid='existing-uid',
        full_name='Jane Doe',
    )
    db.add(existing)
    db.commit()

    generated = 'jane'
    candidate = generated
    for suffix in range(1, 10):
        if not db.query(User).filter(User.username == candidate).first():
            break
        candidate = f"{generated}_{suffix}"

    assert candidate == 'jane_1'

    duplicate = User(username=candidate, email='jane+other@example.com', firebase_uid='other-uid', full_name='Duplicate')
    db.add(duplicate)
    db.commit()

    assert db.query(User).filter(User.username == 'jane_1').count() == 1
