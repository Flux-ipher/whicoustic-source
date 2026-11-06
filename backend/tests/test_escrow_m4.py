"""
Milestone 4 Automated Test Suite: Escrow & Royalty Disbursement Service.
Conforms strictly to:
- PROJECT.md § Backend Escrow Disbursement Contract
- 15% platform fee, 85% creator net disbursement calculation
- Per-second playback royalty splits
- Canonical seed disbursements (gross $1500.0, fee $225.0, net $1275.0)
- Status filtering: settled, pending, disputed
- API endpoints: GET /api/v1/licenses/{id}/disbursements, calculation & summary
"""

import os
import sys
import uuid
from decimal import Decimal
from datetime import datetime, date
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SyncSessionLocal, create_tables_sync
from app.models.user import User
from app.models.voice import Voice
from app.models.license import License
from app.models.escrow import EscrowDisbursement
from app.services.escrow_service import EscrowService


def _setup_test_context():
    from app.core.security import set_security_config
    set_security_config("whicoustic_test_secret_key_12345")
    create_tables_sync()
    db = SyncSessionLocal()
    
    # Create test user
    user_id = f"test_escrow_user_{uuid.uuid4().hex[:8]}"
    user = User(
        id=user_id,
        email=f"{user_id}@whicoustic.ai",
        username=user_id,
        full_name="Escrow Test Creator",
        hashed_password="mock_hashed_pw",
        dob=date(1995, 5, 15),
        is_active=True
    )
    db.add(user)
    
    # Create test voice
    voice_id = f"voice_{uuid.uuid4().hex[:8]}"
    voice = Voice(
        id=voice_id,
        user_id=user_id,
        name="Escrow Voice Profile",
        status="ready"
    )
    db.add(voice)
    
    # Create test license
    license_id = f"lic_{uuid.uuid4().hex[:8]}"
    license_obj = License(
        id=license_id,
        user_id=user_id,
        voice_id=voice_id,
        name="Commercial Broadcast License",
        license_type="commercial",
        price=1500.0,
        currency="USD",
        duration_days=365,
        is_active=True
    )
    db.add(license_obj)
    db.commit()
    
    return {
        "db": db,
        "user_id": user_id,
        "voice_id": voice_id,
        "license_id": license_id
    }


def _cleanup_test_context(ctx):
    db = ctx["db"]
    license_id = ctx["license_id"]
    voice_id = ctx["voice_id"]
    user_id = ctx["user_id"]
    try:
        db.query(EscrowDisbursement).filter(EscrowDisbursement.license_id == license_id).delete()
        db.query(License).filter(License.id == license_id).delete()
        db.query(Voice).filter(Voice.id == voice_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def test_escrow_service_split_calculations():
    """Test 15% platform fee and 85% creator payout calculation."""
    print("Testing financial split calculations...")
    db = SyncSessionLocal()
    try:
        service = EscrowService(db)
        
        # $1500 gross: fee = $225.0, net = $1275.0
        splits = service.calculate_splits(1500.0)
        assert splits["gross_amount"] == 1500.0, f"Expected 1500, got {splits['gross_amount']}"
        assert splits["platform_fee"] == 225.0, f"Expected 225, got {splits['platform_fee']}"
        assert splits["net_amount"] == 1275.0, f"Expected 1275, got {splits['net_amount']}"
        assert splits["platform_fee"] + splits["net_amount"] == splits["gross_amount"]

        # $500 gross: fee = $75.0, net = $425.0
        splits_500 = service.calculate_splits(500.0)
        assert splits_500["gross_amount"] == 500.0
        assert splits_500["platform_fee"] == 75.0
        assert splits_500["net_amount"] == 425.0

        # Non-round split with half-up rounding: $33.33 gross
        splits_odd = service.calculate_splits(33.33)
        assert splits_odd["gross_amount"] == 33.33
        assert splits_odd["platform_fee"] == 5.00
        assert splits_odd["net_amount"] == 28.33
        assert round(splits_odd["platform_fee"] + splits_odd["net_amount"], 2) == 33.33
    finally:
        db.close()


def test_escrow_service_playback_split():
    """Test per-second playback royalty splits."""
    print("Testing per-second playback splits...")
    db = SyncSessionLocal()
    try:
        service = EscrowService(db)
        
        # 10,000 seconds at $0.05/sec = $500.0 gross
        playback = service.calculate_playback_split(
            duration_seconds=10000.0,
            rate_per_second=0.05,
            platform_fee_percent=15.0
        )
        assert playback["gross_amount"] == 500.0
        assert playback["platform_fee"] == 75.0
        assert playback["net_creator_amount"] == 425.0
        assert playback["platform_fee_percent"] == 15.0
        assert playback["creator_percent"] == 85.0

        # 120 seconds at $0.10/sec = $12.0 gross -> $1.80 fee, $10.20 net
        p2 = service.calculate_playback_split(120.0, 0.10, 15.0)
        assert p2["gross_amount"] == 12.0
        assert p2["platform_fee"] == 1.80
        assert p2["net_creator_amount"] == 10.20
    finally:
        db.close()


def test_canonical_seed_and_status_filtering(ctx):
    """Test seeding canonical entries and filtering by status."""
    print("Testing canonical seeding and status filtering...")
    db = ctx["db"]
    license_id = ctx["license_id"]
    service = EscrowService(db)
    
    # 1. Full data
    data = service.get_license_disbursements(license_id)
    assert data["license_id"] == license_id
    assert data["currency"] == "USD"
    assert data["gross_escrow"] == 1500.0
    assert data["platform_fee"] == 225.0
    assert data["net_disbursement"] == 1275.0
    assert len(data["disbursements"]) == 3

    # Check canonical disb_001
    disb_001 = next(d for d in data["disbursements"] if d["id"] == "disb_001")
    assert disb_001["royalty_stream"] == "Commercial Podcast Syndication"
    assert disb_001["licensee"] == "Apex Media Labs"
    assert disb_001["gross_amount"] == 500.0
    assert disb_001["platform_fee"] == 75.0
    assert disb_001["net_amount"] == 425.0
    assert disb_001["status"] == "settled"

    # 2. Settled filter
    settled = service.get_license_disbursements(license_id, status="settled")
    assert len(settled["disbursements"]) == 1
    assert settled["disbursements"][0]["id"] == "disb_001"
    assert settled["gross_escrow"] == 500.0
    assert settled["platform_fee"] == 75.0
    assert settled["net_disbursement"] == 425.0

    # 3. Pending filter
    pending = service.get_license_disbursements(license_id, status="pending")
    assert len(pending["disbursements"]) == 1
    assert pending["disbursements"][0]["id"] == "disb_002"
    assert pending["gross_escrow"] == 600.0

    # 4. Disputed filter
    disputed = service.get_license_disbursements(license_id, status="disputed")
    assert len(disputed["disbursements"]) == 1
    assert disputed["disbursements"][0]["id"] == "disb_003"
    assert disputed["gross_escrow"] == 400.0


def test_api_license_disbursements_contract(ctx):
    """Test GET /api/v1/licenses/{id}/disbursements API contract."""
    print("Testing FastAPI HTTP endpoints...")
    client = TestClient(app)
    license_id = ctx["license_id"]
    user_id = ctx["user_id"]
    from app.core.security import create_access_token
    token = create_access_token({"sub": user_id})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Primary path: GET /api/v1/licenses/{license_id}/disbursements
    resp = client.get(f"/api/v1/licenses/{license_id}/disbursements", headers=headers)
    assert resp.status_code == 200, f"Error: {resp.text}"
    body = resp.json()
    assert body["license_id"] == license_id
    assert body["currency"] == "USD"
    assert body["gross_escrow"] == 1500.0
    assert body["platform_fee"] == 225.0
    assert body["net_disbursement"] == 1275.0
    assert len(body["disbursements"]) >= 3

    # 2. Status filtering via query param
    resp_alias = client.get(f"/api/v1/licenses/{license_id}/disbursements?status=settled", headers=headers)
    assert resp_alias.status_code == 200
    body_settled = resp_alias.json()
    assert len(body_settled["disbursements"]) == 1
    assert body_settled["disbursements"][0]["status"] == "settled"

    # 3. Escrow summary route
    resp_summary = client.get(f"/api/v1/licenses/{license_id}/escrow-summary", headers=headers)
    assert resp_summary.status_code == 200
    summary = resp_summary.json()
    assert summary["total_gross"] == 1500.0
    assert summary["total_platform_fee"] == 225.0
    assert summary["total_net"] == 1275.0
    assert summary["settled"]["net"] == 425.0
    assert summary["pending"]["net"] == 510.0
    assert summary["disputed"]["net"] == 340.0

    # 4. Playback split calculator endpoint
    split_req = {
        "duration_seconds": 10000.0,
        "rate_per_second": 0.05,
        "platform_fee_percent": 15.0
    }
    resp_split = client.post(f"/api/v1/licenses/{license_id}/calculate-split", json=split_req, headers=headers)
    assert resp_split.status_code == 200
    split_data = resp_split.json()
    assert split_data["gross_amount"] == 500.0
    assert split_data["platform_fee"] == 75.0
    assert split_data["net_creator_amount"] == 425.0


def run_all_escrow_tests():
    print("=" * 70)
    print("RUNNING WHICOUSTIC ESCROW DISBURSEMENT TEST SUITE (MILESTONE 4)")
    print("=" * 70)

    test_escrow_service_split_calculations()
    print("PASS: [1/4] Financial split calculations (15% platform fee / 85% creator payout)")

    test_escrow_service_playback_split()
    print("PASS: [2/4] Per-second playback royalty splits")

    ctx = _setup_test_context()
    try:
        test_canonical_seed_and_status_filtering(ctx)
        print("PASS: [3/4] Canonical seed disbursements & status filtering (settled/pending/disputed)")

        test_api_license_disbursements_contract(ctx)
        print("PASS: [4/4] FastAPI HTTP API endpoints and PROJECT.md contract compliance")
    finally:
        _cleanup_test_context(ctx)

    print("=" * 70)
    print("ALL 4 ESCROW DISBURSEMENT VERIFICATION SUITES PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_escrow_tests()
