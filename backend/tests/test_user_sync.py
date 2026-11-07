from datetime import datetime
import re
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.users import sync_user
from app.core.config import settings
from app.core.database import Base
from app.core.firebase_auth import verify_firebase_token
from app.models.user import User, migrate_sqlite_user_table
from app.schemas.user import UserOut, UserSyncIn


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
    assert saved.is_onboarded is False
    assert saved.royalty_floor_pct == 18.5

    response = UserOut.from_model(saved)
    assert response.id == str(saved.id)
    assert response.uid == 'firebase-uid-123'
    assert response.name == 'Alice Example'
    assert response.photo_url == 'https://example.com/avatar.png'
    assert response.phone == '+1-555-0100'
    assert response.provider_id is None
    assert response.is_onboarded is False
    assert response.is_new_user is False
    assert response.royalty_floor_pct == 18.5


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


def test_sync_user_endpoint_new_user_unonboarded():
    db = _make_db_session()
    payload = UserSyncIn(
        uid='new-fb-uid-101',
        email='brandnew@example.com',
        name='Brand New User',
        photo_url='https://example.com/photo.jpg',
    )
    claims = {'uid': 'new-fb-uid-101', 'email': 'brandnew@example.com'}

    result = sync_user(payload=payload, db=db, claims=claims)

    assert result.is_new_user is True
    assert result.is_onboarded is False
    assert result.email == 'brandnew@example.com'
    assert result.uid == 'new-fb-uid-101'
    assert result.name == 'Brand New User'
    assert result.royalty_floor_pct == 18.5

    # Check persistence in database
    saved = db.query(User).filter(User.firebase_uid == 'new-fb-uid-101').first()
    assert saved is not None
    assert saved.is_onboarded is False
    assert saved.onboarded_at is None
    assert saved.royalty_floor_pct == 18.5


def test_sync_user_endpoint_existing_user_onboarding_completion():
    db = _make_db_session()
    # First sync creates the new user
    initial_payload = UserSyncIn(
        uid='user-onboarding-uid',
        email='onboardme@example.com',
        name='Pending Onboarding',
    )
    claims = {'uid': 'user-onboarding-uid', 'email': 'onboardme@example.com'}
    initial_res = sync_user(payload=initial_payload, db=db, claims=claims)
    assert initial_res.is_new_user is True
    assert initial_res.is_onboarded is False

    # Second sync completes onboarding
    complete_payload = UserSyncIn(
        uid='user-onboarding-uid',
        email='onboardme@example.com',
        is_onboarded=True,
        royalty_floor_pct=24.5,
        voice_category='Cinematic Narration & Audio Drama',
        vault_key='SHA256:4080c0aea1ea4cc3a63a13901af1baaa76da6e81e2804561b6fff5d5f6d917c0',
    )
    completed_res = sync_user(payload=complete_payload, db=db, claims=claims)

    assert completed_res.is_new_user is False
    assert completed_res.is_onboarded is True
    assert completed_res.royalty_floor_pct == 24.5
    assert completed_res.voice_category == 'Cinematic Narration & Audio Drama'
    assert completed_res.vault_key == 'SHA256:4080c0aea1ea4cc3a63a13901af1baaa76da6e81e2804561b6fff5d5f6d917c0'

    # Check persistence in database
    persisted = db.query(User).filter(User.firebase_uid == 'user-onboarding-uid').first()
    assert persisted is not None
    assert persisted.is_onboarded is True
    assert persisted.onboarded_at is not None
    assert isinstance(persisted.onboarded_at, datetime)
    assert persisted.royalty_floor_pct == 24.5
    assert persisted.voice_category == 'Cinematic Narration & Audio Drama'
    assert persisted.vault_key == 'SHA256:4080c0aea1ea4cc3a63a13901af1baaa76da6e81e2804561b6fff5d5f6d917c0'


def test_sync_user_endpoint_preserves_onboarded_status_on_subsequent_logins():
    db = _make_db_session()
    # Pre-create an onboarded user
    existing_user = User(
        username='onboarded_vet',
        email='veteran@example.com',
        firebase_uid='vet-uid-999',
        full_name='Veteran Onboarded',
        is_onboarded=True,
        onboarded_at=datetime.utcnow(),
        royalty_floor_pct=22.0,
        voice_category='Commercial Advertising',
        vault_key='SHA256:existingkey',
    )
    db.add(existing_user)
    db.commit()

    # Subsequent login without onboarding fields passed in payload
    login_payload = UserSyncIn(
        uid='vet-uid-999',
        email='veteran@example.com',
        name='Veteran Onboarded (Logged In)',
    )
    claims = {'uid': 'vet-uid-999', 'email': 'veteran@example.com'}
    login_res = sync_user(payload=login_payload, db=db, claims=claims)

    assert login_res.is_new_user is False
    assert login_res.is_onboarded is True
    assert login_res.royalty_floor_pct == 22.0
    assert login_res.voice_category == 'Commercial Advertising'
    assert login_res.vault_key == 'SHA256:existingkey'
    assert login_res.name == 'Veteran Onboarded (Logged In)'


def test_sync_user_endpoint_requires_uid_or_email():
    db = _make_db_session()
    empty_payload = UserSyncIn()
    try:
        sync_user(payload=empty_payload, db=db, claims={})
        assert False, "Should have raised HTTPException(400)"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "uid or email required" in exc.detail


def test_firebase_auth_mock_and_fallback():
    # Test mock token support when enabled
    orig_mock = settings.MOCK_AUTH_ENABLED
    settings.MOCK_AUTH_ENABLED = True
    try:
        mock_claims = verify_firebase_token("mock-token-123")
        assert mock_claims["uid"] == "demo-user-123"
        assert mock_claims["email"] == "demo@whicoustic.com"
        assert mock_claims["is_admin"] is True
    finally:
        settings.MOCK_AUTH_ENABLED = orig_mock

    # Test invalid token rejection
    try:
        verify_firebase_token("invalid-garbage-token")
        assert False, "Should have raised HTTPException(401)"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert "Invalid or expired token" in exc.detail

    # Test empty token rejection
    try:
        verify_firebase_token("")
        assert False, "Should have raised HTTPException(401)"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert "Missing token" in exc.detail


def test_sync_user_rejects_bola_uid_mismatch_with_http_403():
    db = _make_db_session()
    # Legitimate user Bob exists
    bob = User(
        username="bob_original",
        email="bob@example.com",
        firebase_uid="uid-bob-legit",
        full_name="Bob Original",
        is_onboarded=True,
        royalty_floor_pct=20.0,
    )
    db.add(bob)
    db.commit()

    # Attacker Alice authenticates as Alice, attempts to overwrite Bob's profile
    alice_claims = {"uid": "uid-alice-attacker", "email": "alice@attacker.org"}
    malicious_payload = UserSyncIn(
        uid="uid-bob-legit",
        name="Bob Account Hijacked",
        is_onboarded=False,
        royalty_floor_pct=5.0,
    )

    try:
        sync_user(payload=malicious_payload, db=db, claims=alice_claims)
        assert False, "BOLA attack must be rejected with HTTP 403"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert "Payload UID does not match authenticated token" in exc.detail

    # Verify Bob's profile in DB is completely untouched
    bob_check = db.query(User).filter(User.firebase_uid == "uid-bob-legit").first()
    assert bob_check.full_name == "Bob Original"
    assert bob_check.email == "bob@example.com"
    assert bob_check.is_onboarded is True
    assert bob_check.royalty_floor_pct == 20.0


def test_sync_user_rejects_email_mismatch_with_token_http_403():
    db = _make_db_session()
    claims = {"uid": "uid-alice", "email": "alice@example.com"}
    payload = UserSyncIn(
        uid="uid-alice",
        email="bob@example.com",
    )
    try:
        sync_user(payload=payload, db=db, claims=claims)
        assert False, "Email impersonation must be rejected with HTTP 403"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert "Payload email does not match authenticated token email" in exc.detail


def test_sync_user_rejects_account_takeover_collision_http_409():
    db = _make_db_session()
    # User Charlie exists with pre-linked Firebase UID
    charlie = User(
        username="charlie",
        email="charlie@example.com",
        firebase_uid="uid-charlie-original",
    )
    db.add(charlie)
    db.commit()

    # Another identity attempts to link the same email
    claims = {"uid": "uid-david-intruder", "email": "charlie@example.com"}
    payload = UserSyncIn(uid="uid-david-intruder", email="charlie@example.com")

    try:
        sync_user(payload=payload, db=db, claims=claims)
        assert False, "Account takeover must be rejected with HTTP 409"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "Account with this email is already linked" in exc.detail


def test_sync_user_rejects_duplicate_email_update_http_409():
    db = _make_db_session()
    user1 = User(username="user1", email="user1@example.com", firebase_uid="uid-1")
    user2 = User(username="user2", email="user2@example.com", firebase_uid="uid-2")
    db.add_all([user1, user2])
    db.commit()

    # User 2 attempts to update email to User 1's email
    claims = {"uid": "uid-2", "email": "user1@example.com"}
    payload = UserSyncIn(uid="uid-2", email="user1@example.com")

    try:
        sync_user(payload=payload, db=db, claims=claims)
        assert False, "Updating to existing email must be rejected with HTTP 409"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "Email is already associated with another account" in exc.detail


def test_sync_user_preserves_monotonic_onboarding_against_explicit_false_demotion():
    db = _make_db_session()
    orig_time = datetime(2026, 11, 7, 5, 0, 0)
    user = User(
        username="monotonic_creator",
        email="monotonic@example.com",
        firebase_uid="uid-monotonic-1",
        full_name="Monotonic User",
        is_onboarded=True,
        onboarded_at=orig_time,
        royalty_floor_pct=22.5,
    )
    db.add(user)
    db.commit()

    # Routine sync with is_onboarded=False must not demote
    demote_payload = UserSyncIn(
        uid="uid-monotonic-1",
        email="monotonic@example.com",
        is_onboarded=False,
    )
    claims = {"uid": "uid-monotonic-1", "email": "monotonic@example.com"}
    res = sync_user(payload=demote_payload, db=db, claims=claims)

    assert res.is_onboarded is True, "UserOut response must retain is_onboarded=True"
    persisted = db.query(User).filter(User.firebase_uid == "uid-monotonic-1").first()
    assert persisted.is_onboarded is True, "DB user.is_onboarded must not demote to False"
    assert persisted.onboarded_at == orig_time, "Historic onboarded_at timestamp must not change"


def test_sync_user_sanitizes_username_strictly_alphanumeric():
    db = _make_db_session()
    pattern = re.compile(r"^[a-zA-Z0-9_-]+$")

    # 1. Email with dots and plus signs
    payload1 = UserSyncIn(uid="uid-dots-test", email="charlie.smith+vocals@example.com")
    claims1 = {"uid": "uid-dots-test", "email": "charlie.smith+vocals@example.com"}
    res1 = sync_user(payload=payload1, db=db, claims=claims1)
    user1 = db.query(User).filter(User.firebase_uid == "uid-dots-test").first()
    assert pattern.match(user1.username), f"Username {user1.username!r} must match ^[a-zA-Z0-9_-]+$"
    assert user1.username == "charlie_smith_vocals"
    assert res1.email == "charlie.smith+vocals@example.com"

    # 2. Name with special characters
    payload2 = UserSyncIn(uid="uid-name-test", name="Jane Doe (Producer!)", email="jane@studio.com")
    claims2 = {"uid": "uid-name-test", "email": "jane@studio.com"}
    res2 = sync_user(payload=payload2, db=db, claims=claims2)
    user2 = db.query(User).filter(User.firebase_uid == "uid-name-test").first()
    assert pattern.match(user2.username), f"Username {user2.username!r} must match ^[a-zA-Z0-9_-]+$"
    assert 3 <= len(user2.username) <= 50


def test_sync_user_synthetic_fallback_email_serializes_without_pydantic_error():
    db = _make_db_session()
    # Phone or email-less user
    payload = UserSyncIn(uid="phone-user-999")
    claims = {"uid": "phone-user-999"}

    res = sync_user(payload=payload, db=db, claims=claims)
    assert res.is_new_user is True
    assert res.uid == "phone-user-999"
    assert res.email == "phone-user-999@auth.whicoustic.xyz"
    assert res.is_onboarded is False

    persisted = db.query(User).filter(User.firebase_uid == "phone-user-999").first()
    assert persisted is not None
    assert persisted.email == "phone-user-999@auth.whicoustic.xyz"


def test_user_out_accepts_legacy_firebase_local_email():
    db = _make_db_session()
    legacy_user = User(
        username="legacy_user",
        email="legacy@firebase.local",
        firebase_uid="uid-legacy-1",
        full_name="Legacy User",
    )
    db.add(legacy_user)
    db.commit()

    # Serialization via UserOut must not throw ValidationError
    out = UserOut.from_model(legacy_user)
    assert out.email == "legacy@firebase.local"
    assert out.uid == "uid-legacy-1"

