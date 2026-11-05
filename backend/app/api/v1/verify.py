"""
Watermark verification endpoints for Whicoustic API v1.
Handles watermark detection, verification, and forensic analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import tempfile
import os
from datetime import datetime
import uuid

from ...core.database import get_db
from ...core.watermark import WatermarkService
from ...services.forensics_service import ForensicsService
from ...services.speaker_verification import SpeakerVerifier
from ...services.antispoof import AntiSpoofDetector
from ...services.audio_analysis import AudioAnalysisService
from ...models.user import User
from ...models.watermark import WatermarkVerification

from ...schemas.watermark import (
    WatermarkVerificationResponse,
    ForensicAnalysisResponse
)
from fastapi.encoders import jsonable_encoder
import numpy as np

router = APIRouter(prefix="/verify", tags=["watermark-verification"])
from .auth import get_current_user, get_optional_current_user

@router.post("/watermark", response_model=WatermarkVerificationResponse)
async def verify_watermark(
    file: UploadFile = File(...),
    method: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify watermark in uploaded audio file.
    
    Args:
        file: Audio file to analyze
        method: Detection method ('mvp', 'robust', or None for auto-detect)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Watermark verification results
    """
    
    # Validate file type
    allowed_types = ['audio/wav', 'audio/mp3', 'audio/flac', 'audio/m4a']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Initialize watermark service
        watermark_service = WatermarkService()
        
        # Detect watermark
        detection_result = await watermark_service.detect_watermark(
            audio_path=temp_file_path,
            method=method
        )
        
        # Generate verification ID
        verification_id = f"verify_{uuid.uuid4().hex[:12]}"
        
        # Store verification record
        verification = WatermarkVerification(
            id=verification_id,
            user_id=current_user.id if current_user else None,
            original_filename=file.filename,
            detection_method=detection_result.get('detection_method', 'unknown'),
            watermark_found=detection_result.get('found', False),
            watermark_id=detection_result.get('watermark_id'),
            license_id=detection_result.get('license_id'),
            confidence_score=detection_result.get('confidence', 0.0),
            detection_metadata=detection_result,
            verified_at=datetime.utcnow()
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Prepare response
        response_data = WatermarkVerificationResponse(
            verification_id=verification_id,
            watermark_found=detection_result.get('found', False),
            watermark_id=detection_result.get('watermark_id'),
            license_id=detection_result.get('license_id'),
            confidence_score=detection_result.get('confidence', 0.0),
            detection_method=detection_result.get('detection_method', 'unknown'),
            timestamp=detection_result.get('timestamp'),
            signature_valid=detection_result.get('signature_valid', False),
            verification_time=verification.verified_at,
            metadata=detection_result
        )
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Watermark verification failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.post("/forensics")
async def forensic_analysis(
    file: UploadFile = File(...),
    analysis_depth: str = "standard",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive forensic analysis on audio file.
    
    Args:
        file: Audio file to analyze
        analysis_depth: Analysis depth ('quick', 'standard', 'deep')
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Comprehensive forensic analysis results
    """
    
    # Check user permissions for forensic analysis
    if not current_user.is_premium:  # Assuming premium feature
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forensic analysis requires premium subscription"
        )
    
    # Validate file
    if file.size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large for forensic analysis"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Initialize services
        watermark_service = WatermarkService()
        forensics_service = ForensicsService()
        
        # Perform watermark detection
        watermark_results = await watermark_service.detect_watermark(
            audio_path=temp_file_path,
            method=None  # Auto-detect both methods
        )
        
        # Perform forensic analysis
        forensic_results = await forensics_service.analyze_audio(
            audio_path=temp_file_path,
            depth=analysis_depth
        )
        
        # DEBUG LOGGING
        with open("debug_output.txt", "w") as f:
            f.write(f"watermark_results: {watermark_results}\n")
            f.write(f"forensic_results: {forensic_results}\n")
            f.write("TYPES:\n")
            for k, v in forensic_results.items():
                f.write(f"Key: {k}, Type: {type(v)}, Value: {v}\n")
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        f.write(f"  SubKey: {k2}, Type: {type(v2)}, Value: {v2}\n")
        
        # Generate analysis ID
        analysis_id = f"forensic_{uuid.uuid4().hex[:12]}"
        
        # Combine results
        combined_results = {
            'analysis_id': analysis_id,
            'watermark_analysis': watermark_results,
            'forensic_analysis': forensic_results,
            'analysis_depth': analysis_depth,
            'analyzed_at': datetime.utcnow(),
            'file_metadata': {
                'filename': file.filename,
                'size_bytes': file.size,
                'content_type': file.content_type
            }
        }
        
        # Store analysis record
        # This would typically be saved to a ForensicAnalysis model
        
        response = ForensicAnalysisResponse(
            analysis_id=analysis_id,
            watermark_found=watermark_results.get('found', False),
            watermark_details=watermark_results,
            audio_integrity=forensic_results.get('integrity', {}),
            manipulation_detected=forensic_results.get('manipulation_detected', False),
            manipulation_details=forensic_results.get('manipulation_details', []),
            metadata_analysis=forensic_results.get('metadata', {}),
            spectral_analysis=forensic_results.get('spectral', {}),
            confidence_score=min(
                watermark_results.get('confidence', 0.0),
                forensic_results.get('confidence', 0.0)
            ),
            analysis_depth=analysis_depth,
            analyzed_at=combined_results['analyzed_at'],
            recommendations=forensic_results.get('recommendations', [])
        )
        # Helper for manual sanitization
        def sanitize_numpy(obj):
            if isinstance(obj, dict):
                return {k: sanitize_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_numpy(v) for v in obj]
            elif isinstance(obj, tuple):
                return tuple(sanitize_numpy(v) for v in obj)
            elif hasattr(obj, 'item') and not isinstance(obj, (dict, list, tuple)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return sanitize_numpy(obj.tolist())
            return obj

        sanitized_response = sanitize_numpy(response.model_dump())
        return jsonable_encoder(sanitized_response)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forensic analysis failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.post("/speaker-match")
async def speaker_match(
    reference: UploadFile = File(...),
    sample: UploadFile = File(...),
):
    """Compare two voices and return similarity/decision."""
    import tempfile, os
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(reference.filename)[1]) as f1:
            ref_path = f1.name; f1.write(await reference.read())
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(sample.filename)[1]) as f2:
            qry_path = f2.name; f2.write(await sample.read())
        verifier = SpeakerVerifier()
        result = verifier.verify(ref_path, qry_path)
        return result
    finally:
        for p in [locals().get('ref_path'), locals().get('qry_path')]:
            try:
                if p and os.path.exists(p): os.unlink(p)
            except Exception: pass


@router.post("/antispoof")
async def antispoof_check(file: UploadFile = File(...)):
    """Estimate deepfake likelihood for a single audio file."""
    import tempfile, os
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as f:
            path = f.name; f.write(await file.read())
        det = AntiSpoofDetector()
        res = det.detect(path)
        return res
    finally:
        try:
            if 'path' in locals() and os.path.exists(path): os.unlink(path)
        except Exception: pass


@router.post("/spectral-graphs")
async def spectral_graphs(file: UploadFile = File(...)):
    """Return spectral features for plotting (mel, mfcc, centroid, etc.)."""
    import tempfile, os
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as f:
            path = f.name; f.write(await file.read())
        svc = AudioAnalysisService()
        return svc.analyze(path)
    finally:
        try:
            if 'path' in locals() and os.path.exists(path): os.unlink(path)
        except Exception: pass


@router.post("/full-analysis")
async def full_analysis(
    file: UploadFile = File(...),
    reference: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    6-Layer Defense Mechanism Orchestrator.
    Runs all 6 defense layers and computes a weighted authenticity verdict.
    """

    import tempfile, os
    from ...services.prosody_service import ProsodyService
    from ...services.paralinguistic_service import ParalinguisticService
    from ...services.semantic_service import SemanticService
    from ...services.risk_scoring import combine_layer_results, sanitize_numpy

    try:
        # Save sample
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as f:
            sample_path = f.name
            f.write(await file.read())
            
        # Save reference if provided
        ref_path = None
        if reference:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(reference.filename)[1]) as f_ref:
                ref_path = f_ref.name
                f_ref.write(await reference.read())

        results = {}
        weights = {}

        # Layer 1: Anti-Spoof (Acoustic Artifacts)
        try:
            antispoof = AntiSpoofDetector().detect(sample_path)
            # detect() returns spoof_score, we want authenticity
            auth_l1 = max(0.0, 1.0 - antispoof.get("spoof_score", 0.5))
            antispoof["score"] = round(auth_l1, 4)
            results["layer1_antispoof"] = antispoof
            weights["l1"] = {"score": auth_l1, "weight": 0.35}
        except Exception as e:
            results["layer1_antispoof"] = {"error": str(e)}

        # Layer 2: Speaker Verification & Biometric Consistency
        if ref_path:
            try:
                spk_verify = SpeakerVerifier().verify(ref_path, sample_path)
                auth_l2 = float(spk_verify.get("similarity_score", spk_verify.get("score", 0.0)))
                auth_l2 = max(0.0, min(1.0, auth_l2))
                spk_verify["score"] = round(auth_l2, 4)
                results["layer2_speaker"] = spk_verify
                weights["l2"] = {"score": auth_l2, "weight": 0.15}
            except Exception as e:
                results["layer2_speaker"] = {"error": str(e)}
        else:
            try:
                spk_verify = SpeakerVerifier().analyze_consistency(sample_path)
                auth_l2 = float(spk_verify.get("consistency_score", spk_verify.get("score", 0.85)))
                auth_l2 = max(0.0, min(1.0, auth_l2))
                spk_verify["score"] = round(auth_l2, 4)
                results["layer2_speaker"] = spk_verify
                weights["l2"] = {"score": auth_l2, "weight": 0.15}
            except Exception as e:
                results["layer2_speaker"] = {"error": str(e)}

        # Layer 3: Prosody Coherence
        try:
            prosody = ProsodyService().analyse(sample_path)
            auth_l3 = prosody.get("authenticity_score", 0.5)
            prosody["score"] = round(auth_l3, 4)
            results["layer3_prosody"] = prosody
            weights["l3"] = {"score": auth_l3, "weight": 0.15}
        except Exception as e:
            results["layer3_prosody"] = {"error": str(e)}

        # Layer 4: Paralinguistic Coherence
        try:
            paralinguistic = ParalinguisticService().analyse(sample_path)
            auth_l4 = paralinguistic.get("authenticity_score", 0.5)
            paralinguistic["score"] = round(auth_l4, 4)
            results["layer4_paralinguistic"] = paralinguistic
            weights["l4"] = {"score": auth_l4, "weight": 0.15}
        except Exception as e:
            results["layer4_paralinguistic"] = {"error": str(e)}

        # Layer 5: Semantic Alignment
        try:
            semantic = SemanticService().analyse(sample_path)
            auth_l5 = semantic.get("authenticity_score", 0.5)
            semantic["score"] = round(auth_l5, 4)
            results["layer5_semantic"] = semantic
            weights["l5"] = {"score": auth_l5, "weight": 0.15}
        except Exception as e:
            results["layer5_semantic"] = {"error": str(e)}

        # Telephony channel detection (Phase 2 Module 1)
        is_telephony = False
        try:
            from ...services.telephone_channel import TelephoneChannelPreprocessor
            import soundfile as sf
            audio_test, sr_test = sf.read(sample_path)
            if audio_test.ndim > 1:
                audio_test = np.mean(audio_test, axis=1)
            tele_meta = TelephoneChannelPreprocessor(target_sr=16000).detect_bandwidth(audio_test, sr_test)
            is_telephony = tele_meta.get("is_telephony", False)
        except Exception:
            pass

        # Layer 6: Watermark
        if is_telephony:
            results["layer6_watermark"] = {
                "status": "disabled_telephony",
                "notes": "19kHz watermark inaudible on 8kHz telephone bandwidth",
                "score": 0.5,
            }
            # Layer 6 is disabled, will be reallocated
        else:
            try:
                watermark = await WatermarkService().detect_watermark(sample_path, method=None)
                # Watermark found = synthetic (authenticity = 0.0)
                # Not found = authentic (authenticity = 1.0)
                auth_l6 = 0.0 if watermark.get("found", False) else 1.0
                watermark["score"] = round(auth_l6, 4)
                watermark["verdict"] = "Watermark Detected" if watermark.get("found") else "Clean"
                results["layer6_watermark"] = watermark
                weights["l6"] = {"score": auth_l6, "weight": 0.20}
            except Exception as e:
                results["layer6_watermark"] = {"error": str(e)}

        # Dynamic weight adjustment for telephone channel
        if is_telephony:
            from ...services.telephone_channel import TelephoneChannelPreprocessor
            weights = TelephoneChannelPreprocessor.adjust_layer_weights(weights, is_telephony=True)

        # Combine layer scores using shared risk_scoring module
        scored = combine_layer_results(results, weights)
        scored["analysis_id"] = f"full_{uuid.uuid4().hex[:12]}"
        scored["analyzed_at"] = datetime.utcnow().isoformat()
        scored["is_telephony"] = is_telephony

        return sanitize_numpy(scored)

    finally:
        try:
            if 'sample_path' in locals() and os.path.exists(sample_path): os.unlink(sample_path)
            if 'ref_path' in locals() and ref_path and os.path.exists(ref_path): os.unlink(ref_path)
        except Exception:
            pass


@router.post("/localize")
async def localize_partial_fakes(
    file: UploadFile = File(...),
    is_telephony: Optional[bool] = None,
):
    """
    Phase 2 Module 2: Locate synthetic audio segments at 0.5-second resolution.
    Returns segment-by-segment authenticity scores, labels ('REAL' / 'FAKE'),
    and merged continuous spans for partial fake detection.
    """
    import tempfile, os
    import soundfile as sf
    from ...services.partial_fake_localizer import PartialFakeLocalizer
    from ...services.risk_scoring import sanitize_numpy

    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            sample_path = f.name
            f.write(await file.read())

        # Load audio
        try:
            audio, sr = sf.read(sample_path)
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
        except Exception:
            import librosa
            audio, sr = librosa.load(sample_path, sr=None, mono=True)

        localizer = PartialFakeLocalizer(sample_rate=16000)
        result = localizer.analyze_audio(
            audio=audio,
            sr=sr,
            is_telephony=is_telephony,
        )
        result["filename"] = file.filename
        return sanitize_numpy(result)
    finally:
        try:
            if 'sample_path' in locals() and os.path.exists(sample_path):
                os.unlink(sample_path)
        except Exception:
            pass


@router.get("/history")
async def get_verification_history(
    limit: int = 20,
    watermark_found: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verification history for the current user."""
    
    query = db.query(WatermarkVerification).filter(
        WatermarkVerification.user_id == current_user.id
    )
    
    if watermark_found is not None:
        query = query.filter(WatermarkVerification.watermark_found == watermark_found)
    
    verifications = query.order_by(
        WatermarkVerification.verified_at.desc()
    ).limit(min(limit, 100)).all()
    
    return [
        {
            "verification_id": verification.id,
            "original_filename": verification.original_filename,
            "watermark_found": verification.watermark_found,
            "watermark_id": verification.watermark_id,
            "license_id": verification.license_id,
            "confidence_score": verification.confidence_score,
            "detection_method": verification.detection_method,
            "verified_at": verification.verified_at
        }
        for verification in verifications
    ]

@router.get("/{verification_id}")
async def get_verification_details(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed results of a specific verification."""
    
    verification = db.query(WatermarkVerification).filter(
        WatermarkVerification.id == verification_id,
        WatermarkVerification.user_id == current_user.id
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found"
        )
    
    return {
        "verification_id": verification.id,
        "original_filename": verification.original_filename,
        "watermark_found": verification.watermark_found,
        "watermark_id": verification.watermark_id,
        "license_id": verification.license_id,
        "confidence_score": verification.confidence_score,
        "detection_method": verification.detection_method,
        "detection_metadata": verification.detection_metadata,
        "verified_at": verification.verified_at
    }

@router.post("/batch-verify")
async def batch_verify_watermarks(
    files: list[UploadFile],
    method: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify watermarks in multiple audio files."""
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files per batch"
        )
    
    results = []
    
    for file in files:
        try:
            # Validate file type
            allowed_types = ['audio/wav', 'audio/mp3', 'audio/flac', 'audio/m4a']
            if file.content_type not in allowed_types:
                results.append({
                    "filename": file.filename,
                    "error": f"Unsupported file type: {file.content_type}",
                    "watermark_found": False
                })
                continue
            
            # Save file temporarily and verify
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Initialize watermark service
                watermark_service = WatermarkService()
                
                # Detect watermark
                detection_result = await watermark_service.detect_watermark(
                    audio_path=temp_file_path,
                    method=method
                )
                
                # Store result
                verification_id = f"batch_{uuid.uuid4().hex[:12]}"
                verification = WatermarkVerification(
                    id=verification_id,
                    user_id=current_user.id,
                    original_filename=file.filename,
                    detection_method=detection_result.get('detection_method', 'unknown'),
                    watermark_found=detection_result.get('found', False),
                    watermark_id=detection_result.get('watermark_id'),
                    license_id=detection_result.get('license_id'),
                    confidence_score=detection_result.get('confidence', 0.0),
                    detection_metadata=detection_result,
                    verified_at=datetime.utcnow()
                )
                
                db.add(verification)
                
                results.append({
                    "verification_id": verification_id,
                    "filename": file.filename,
                    "watermark_found": detection_result.get('found', False),
                    "watermark_id": detection_result.get('watermark_id'),
                    "confidence_score": detection_result.get('confidence', 0.0),
                    "detection_method": detection_result.get('detection_method', 'unknown')
                })
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e),
                "watermark_found": False
            })
    
    # Commit all verifications
    db.commit()
    
    return {
        "batch_id": f"batch_{uuid.uuid4().hex[:12]}",
        "total_files": len(files),
        "processed_files": len(results),
        "results": results
    }

@router.get("/stats")
async def get_verification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verification statistics for the current user."""
    
    verifications = db.query(WatermarkVerification).filter(
        WatermarkVerification.user_id == current_user.id
    ).all()
    
    total_verifications = len(verifications)
    watermarks_found = len([v for v in verifications if v.watermark_found])
    avg_confidence = sum(v.confidence_score for v in verifications) / max(1, total_verifications)
    
    # Method breakdown
    method_stats = {}
    for verification in verifications:
        method = verification.detection_method
        if method not in method_stats:
            method_stats[method] = {'count': 0, 'found': 0}
        method_stats[method]['count'] += 1
        if verification.watermark_found:
            method_stats[method]['found'] += 1
    
    return {
        "total_verifications": total_verifications,
        "watermarks_found": watermarks_found,
        "success_rate": watermarks_found / max(1, total_verifications),
        "average_confidence": avg_confidence,
        "method_breakdown": method_stats,
        "last_verification": max(v.verified_at for v in verifications) if verifications else None
    }