"""
Licensing system endpoints for Whicoustic API v1.
Handles license creation, token generation, usage tracking, and billing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

from decimal import Decimal

from ...core.database import get_db
from ...core.config import settings
from ...services.license_service import LicenseService
from ...models.user import User
from ...models.voice import Voice
from ...models.license import License
from ...models.usage_log import LicenseUsage
from .auth import get_current_user
from ...schemas.license import (
    LicenseCreate,
    LicenseResponse,
    LicenseTokenRequest,
    LicenseTokenResponse,
    LicenseUsageResponse
)
from ...services.escrow_service import EscrowService
from ...schemas.escrow import (
    LicenseDisbursementsResponse,
    DisbursementCreateRequest,
    DisbursementItemResponse,
    PlaybackRoyaltySplitRequest,
    PlaybackRoyaltySplitResponse,
    EscrowSummaryResponse,
)

router = APIRouter(prefix="/licenses", tags=["licensing"])

@router.post("", response_model=LicenseResponse)
@router.post("/", response_model=LicenseResponse)
async def create_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new license for a voice."""
    
    # Verify voice ownership
    voice = db.query(Voice).filter(
        Voice.id == license_data.voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found or access denied"
        )
    
    # Generate unique license ID
    license_id = f"lic_{uuid.uuid4().hex[:16]}"
    
    # Create license
    license = License(
        id=license_id,
        user_id=current_user.id,
        voice_id=license_data.voice_id,
        name=license_data.name,
        description=license_data.description,
        license_type=license_data.license_type,
        price=license_data.price,
        currency=license_data.currency,
        duration_days=license_data.duration_days,
        usage_limit=license_data.usage_limit,
        territory=license_data.territory,
        allowed_use_cases=license_data.allowed_use_cases,
        restrictions=license_data.restrictions,
        is_active=True
    )
    
    db.add(license)
    db.commit()
    db.refresh(license)
    
    return LicenseResponse(
        id=license.id,
        voice_id=license.voice_id,
        name=license.name,
        description=license.description,
        license_type=license.license_type,
        price=license.price,
        currency=license.currency,
        duration_days=license.duration_days,
        usage_limit=license.usage_limit,
        territory=license.territory,
        allowed_use_cases=license.allowed_use_cases,
        restrictions=license.restrictions,
        is_active=license.is_active,
        created_at=license.created_at,
        updated_at=license.updated_at
    )

@router.get("", response_model=List[LicenseResponse])
@router.get("/", response_model=List[LicenseResponse])
async def list_licenses(
    voice_id: Optional[str] = None,
    license_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all licenses created by the current user."""
    
    query = db.query(License).filter(License.user_id == current_user.id)
    
    if voice_id:
        query = query.filter(License.voice_id == voice_id)
    if license_type:
        query = query.filter(License.license_type == license_type)
    if is_active is not None:
        query = query.filter(License.is_active == is_active)
    
    licenses = query.order_by(License.created_at.desc()).all()
    
    return [
        LicenseResponse(
            id=license.id,
            voice_id=license.voice_id,
            name=license.name,
            description=license.description,
            license_type=license.license_type,
            price=license.price,
            currency=license.currency,
            duration_days=license.duration_days,
            usage_limit=license.usage_limit,
            territory=license.territory,
            allowed_use_cases=license.allowed_use_cases,
            restrictions=license.restrictions,
            is_active=license.is_active,
            created_at=license.created_at,
            updated_at=license.updated_at
        )
        for license in licenses
    ]

@router.get("/{license_id}", response_model=LicenseResponse)
async def get_license(
    license_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific license."""
    
    license = db.query(License).filter(
        License.id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    return LicenseResponse(
        id=license.id,
        voice_id=license.voice_id,
        name=license.name,
        description=license.description,
        license_type=license.license_type,
        price=license.price,
        currency=license.currency,
        duration_days=license.duration_days,
        usage_limit=license.usage_limit,
        territory=license.territory,
        allowed_use_cases=license.allowed_use_cases,
        restrictions=license.restrictions,
        is_active=license.is_active,
        created_at=license.created_at,
        updated_at=license.updated_at
    )

@router.put("/{license_id}", response_model=LicenseResponse)
async def update_license(
    license_id: str,
    license_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update license details."""
    
    license = db.query(License).filter(
        License.id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    # Update allowed fields
    allowed_fields = [
        'name', 'description', 'price', 'duration_days', 
        'usage_limit', 'territory', 'allowed_use_cases', 
        'restrictions', 'is_active'
    ]
    
    for field in allowed_fields:
        if field in license_data:
            setattr(license, field, license_data[field])
    
    license.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(license)
    
    return LicenseResponse(
        id=license.id,
        voice_id=license.voice_id,
        name=license.name,
        description=license.description,
        license_type=license.license_type,
        price=license.price,
        currency=license.currency,
        duration_days=license.duration_days,
        usage_limit=license.usage_limit,
        territory=license.territory,
        allowed_use_cases=license.allowed_use_cases,
        restrictions=license.restrictions,
        is_active=license.is_active,
        created_at=license.created_at,
        updated_at=license.updated_at
    )

@router.delete("/{license_id}")
async def delete_license(
    license_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a license."""
    
    license = db.query(License).filter(
        License.id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    # Soft delete by deactivating
    license.is_active = False
    license.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "License deactivated successfully"}

@router.post("/{license_id}/tokens", response_model=LicenseTokenResponse)
async def generate_license_token(
    license_id: str,
    token_request: LicenseTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a license token for a specific purchaser."""
    
    license = db.query(License).filter(
        License.id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    if not license.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License is not active"
        )
    
    # Initialize license service
    license_service = LicenseService(db)
    
    # Generate token
    token_data = await license_service.generate_license_token(
        license_id=license_id,
        purchaser_email=token_request.purchaser_email,
        purchaser_name=token_request.purchaser_name,
        purchase_amount=token_request.purchase_amount,
        custom_terms=token_request.custom_terms
    )
    
    return LicenseTokenResponse(
        token=token_data['token'],
        token_id=token_data['token_id'],
        license_id=license_id,
        purchaser_email=token_request.purchaser_email,
        expires_at=token_data['expires_at'],
        usage_remaining=license.usage_limit,
        terms_url=token_data.get('terms_url')
    )

@router.get("/{license_id}/usage", response_model=List[LicenseUsageResponse])
async def get_license_usage(
    license_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage history for a license."""
    
    # Verify license ownership
    license = db.query(License).filter(
        License.id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    # Get usage records
    usage_records = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_id
    ).order_by(
        LicenseUsage.used_at.desc()
    ).limit(min(limit, 100)).all()
    
    return [
        LicenseUsageResponse(
            id=usage.id,
            license_id=usage.license_id,
            token_id=usage.token_id,
            user_id=usage.user_id,
            voice_id=usage.voice_id,
            text_length=usage.text_length,
            audio_duration=usage.audio_duration,
            watermark_id=usage.watermark_id,
            used_at=usage.used_at,
            metadata=usage.meta_json
        )
        for usage in usage_records
    ]

@router.get("/{license_id}/stats")
async def get_license_stats(
    license_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a license."""
    
    # Verify license ownership
    license = db.query(License).filter(
        License.id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    # Get usage statistics
    usage_records = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_id
    ).all()
    
    total_uses = len(usage_records)
    total_text_length = sum(usage.text_length for usage in usage_records)
    total_audio_duration = sum(
        usage.audio_duration for usage in usage_records 
        if usage.audio_duration
    )
    
    unique_users = len(set(usage.user_id for usage in usage_records))
    
    # Calculate revenue (if applicable)
    total_revenue = license.price * total_uses if license.price else 0
    
    return {
        "license_id": license_id,
        "license_name": license.name,
        "total_uses": total_uses,
        "usage_limit": license.usage_limit,
        "usage_remaining": max(0, license.usage_limit - total_uses) if license.usage_limit else None,
        "unique_users": unique_users,
        "total_text_length": total_text_length,
        "total_audio_duration": total_audio_duration,
        "total_revenue": float(total_revenue),
        "currency": license.currency,
        "last_used": max(usage.used_at for usage in usage_records) if usage_records else None,
        "created_at": license.created_at
    }

@router.post("/validate-token")
async def validate_license_token(
    token: str,
    voice_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Validate a license token (public endpoint for token verification)."""
    
    license_service = LicenseService(db)
    
    validation_result = await license_service.validate_license_token(
        token=token,
        voice_id=voice_id
    )
    
    if not validation_result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired license token"
        )
    
    return {
        "valid": True,
        "license_id": validation_result['license_id'],
        "voice_id": validation_result.get('voice_id'),
        "usage_remaining": validation_result.get('usage_remaining'),
        "expires_at": validation_result.get('expires_at'),
        "allowed_use_cases": validation_result.get('allowed_use_cases'),
        "territory": validation_result.get('territory')
    }

@router.get("/marketplace/browse")
async def browse_marketplace_licenses(
    license_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    territory: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Browse available licenses in the marketplace."""
    
    # This would be expanded for a full marketplace implementation
    query = db.query(License).filter(
        License.is_active == True,
        License.is_public == True  # Assuming we add this field later
    )
    
    if license_type:
        query = query.filter(License.license_type == license_type)
    if min_price:
        query = query.filter(License.price >= min_price)
    if max_price:
        query = query.filter(License.price <= max_price)
    if territory:
        query = query.filter(License.territory.contains(territory))
    
    licenses = query.limit(min(limit, 100)).all()
    
    # Return public information only
    return [
        {
            "id": license.id,
            "voice_id": license.voice_id,
            "name": license.name,
            "description": license.description,
            "license_type": license.license_type,
            "price": float(license.price),
            "currency": license.currency,
            "territory": license.territory,
            "allowed_use_cases": license.allowed_use_cases,
            "duration_days": license.duration_days,
            "usage_limit": license.usage_limit,
            "creator_name": "Anonymous",  # Would be configurable
            "voice_preview_url": f"/api/v1/voices/{license.voice_id}/preview"
        }
        for license in licenses
    ]


@router.get("/{license_id}/disbursements", response_model=LicenseDisbursementsResponse)
@router.get("/{id}/disbursements", response_model=LicenseDisbursementsResponse, include_in_schema=False)
async def get_license_disbursements_endpoint(
    license_id: Optional[str] = None,
    id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get escrow disbursement details and royalty calculations for a voice license.
    Calculates gross escrow, platform fee (15%), net creator disbursement (85%),
    and returns breakdown of settled, pending, and disputed royalty streams.
    Conforms to PROJECT.md § Backend Escrow Disbursement Contract.
    """
    target_id = license_id or id
    if not target_id:
        raise HTTPException(status_code=400, detail="License ID is required")

    # Verify license exists
    license = db.query(License).filter(License.id == target_id).first()
    if not license:
        raise HTTPException(
            status_code=404,
            detail="License not found"
        )

    # Verify access: licensor/creator or authorized user
    if license.user_id != current_user.id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=403,
            detail="Access denied to license disbursement records"
        )

    escrow_service = EscrowService(db)
    result = escrow_service.get_license_disbursements(license_id=target_id, status=status)
    return result


@router.post("/{license_id}/disbursements", response_model=DisbursementItemResponse)
async def create_license_disbursement_endpoint(
    license_id: str,
    payload: DisbursementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a new disbursement in escrow for a license."""
    license = db.query(License).filter(License.id == license_id).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    if license.user_id != current_user.id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Access denied")

    escrow_service = EscrowService(db)
    disb = escrow_service.create_disbursement(
        license_id=license_id,
        royalty_stream=payload.royalty_stream,
        licensee=payload.licensee,
        gross_amount=payload.gross_amount,
        status=payload.status,
        playback_seconds=payload.playback_seconds,
        rate_per_second=payload.rate_per_second,
        tx_hash=payload.tx_hash,
        payment_method=payload.payment_method
    )
    return DisbursementItemResponse(
        id=disb.id,
        royalty_stream=disb.royalty_stream,
        licensee=disb.licensee,
        gross_amount=disb.gross_amount,
        platform_fee=disb.platform_fee,
        net_amount=disb.net_amount,
        status=disb.status,
        disbursed_at=disb.disbursed_at.isoformat() + "Z" if disb.disbursed_at else None
    )


@router.post("/{license_id}/calculate-split", response_model=PlaybackRoyaltySplitResponse)
async def calculate_playback_royalty_split_endpoint(
    license_id: str,
    payload: PlaybackRoyaltySplitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate per-second playback royalty splits and fee deductions."""
    license = db.query(License).filter(License.id == license_id).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    escrow_service = EscrowService(db)
    return escrow_service.calculate_playback_split(
        duration_seconds=payload.duration_seconds,
        rate_per_second=payload.rate_per_second,
        platform_fee_percent=payload.platform_fee_percent
    )


@router.get("/{license_id}/escrow-summary", response_model=EscrowSummaryResponse)
async def get_license_escrow_summary_endpoint(
    license_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get aggregated escrow balances broken down by settled, pending, and disputed statuses."""
    license = db.query(License).filter(License.id == license_id).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    if license.user_id != current_user.id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Access denied")

    escrow_service = EscrowService(db)
    return escrow_service.get_escrow_summary(license_id=license_id)