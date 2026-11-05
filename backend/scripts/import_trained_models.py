#!/usr/bin/env python3
"""
Import Trained Voice Models into Whicoustic Database
Integrates Common Voice trained models into the Whicoustic platform
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.core.database import db_manager
    from app.models.voice import Voice
    from app.models.user import User
except ImportError:
    from core.database import get_db_sync
    from models.voice import Voice
    from models.user import User
from services.voice_model_registry import VoiceModelRegistry

def import_trained_models(models_dir: str, admin_user_id: str = None):
    """Import trained voice models into Whicoustic database"""
    
    models_path = Path(models_dir)
    if not models_path.exists():
        print(f"❌ Models directory not found: {models_path}")
        return False
    
    # Load training summary
    summary_path = models_path / "training_summary.json"
    if not summary_path.exists():
        print(f"❌ Training summary not found: {summary_path}")
        return False
    
    with open(summary_path, 'r') as f:
        training_summary = json.load(f)
    
    print("🚀 Importing Trained Voice Models into Whicoustic")
    print("=" * 60)
    print(f"📊 Training Date: {training_summary['training_date']}")
    print(f"📈 Models to Import: {training_summary['speakers_trained']}")
    print(f"⭐ High Quality Models: {training_summary['high_quality_models']}")
    print(f"📊 Average Quality: {training_summary['average_quality']}")
    print("-" * 60)
    
    # Get database session
    db = next(get_db_sync())
    
    # Get or create admin user for model ownership
    if admin_user_id:
        admin_user = db.query(User).filter(User.id == admin_user_id).first()
    else:
        # Create a system user for public models
        admin_user = db.query(User).filter(User.email == "system@whicoustic.ai").first()
        if not admin_user:
            admin_user = User(
                email="system@whicoustic.ai",
                username="whicoustic_system",
                subscription_tier="enterprise",
                is_verified=True,
                profile_data={
                    "full_name": "Whicoustic System",
                    "organization": "Whicoustic Platform"
                }
            )
            db.add(admin_user)
            db.commit()
    
    print(f"👤 Using admin user: {admin_user.email}")
    
    # Import each trained model
    imported_count = 0
    registry = VoiceModelRegistry()
    
    for result in training_summary['results']:
        speaker_id = result['speaker_id']
        speaker_dir = models_path / f"speaker_{speaker_id}"
        
        if not speaker_dir.exists():
            print(f"⚠️  Speaker directory not found: {speaker_dir}")
            continue
        
        # Load model config
        config_path = speaker_dir / "config.json"
        samples_path = speaker_dir / "samples.json"
        model_path = speaker_dir / "model.pth"
        
        if not all(p.exists() for p in [config_path, samples_path, model_path]):
            print(f"⚠️  Missing files for speaker {speaker_id[:12]}...")
            continue
        
        # Load metadata
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        with open(samples_path, 'r') as f:
            samples = json.load(f)
        
        # Create voice metadata
        voice_name = f"Common Voice Speaker {speaker_id[:12]}"
        
        # Determine voice characteristics from samples
        accents = list(set(s.get('accent', 'unknown') for s in samples if s.get('accent')))
        ages = list(set(s.get('age', 'unknown') for s in samples if s.get('age')))
        
        voice_tags = {
            'source': 'common_voice',
            'dataset': 'cv-corpus-22.0-delta-2025-06-20-en',
            'accents': accents,
            'ages': ages,
            'training_samples': result['num_samples'],
            'training_epochs': result['epochs'],
            'quality_score': result['quality_score'],
            'model_type': config['model_type']
        }
        
        # Check if voice already exists
        existing_voice = db.query(Voice).filter(
            Voice.name == voice_name,
            Voice.user_id == admin_user.id
        ).first()
        
        if existing_voice:
            print(f"⏭️  Voice already exists: {voice_name}")
            continue
        
        # Create new voice record
        new_voice = Voice(
            user_id=admin_user.id,
            name=voice_name,
            description=f"Voice cloned from Common Voice dataset. Quality score: {result['quality_score']:.3f}",
            language='en',
            accent=accents[0] if accents else 'unknown',
            gender='unknown',  # Could be inferred from samples if available
            age_range=ages[0] if ages else 'unknown',
            voice_tags=voice_tags,
            model_path=str(model_path),
            config_data=config,
            quality_score=result['quality_score'],
            is_public=True,  # Make Common Voice models public
            processing_status='completed'
        )
        
        try:
            db.add(new_voice)
            db.commit()
            
            # Register in voice model registry
            registry.register_model(
                voice_id=str(new_voice.id),
                model_path=str(model_path),
                config=config
            )
            
            imported_count += 1
            status = "✅ High Quality" if result['quality_score'] >= 0.8 else "⚠️  Standard Quality"
            print(f"{status} Imported: {voice_name} (score: {result['quality_score']:.3f})")
            
        except Exception as e:
            print(f"❌ Failed to import {voice_name}: {str(e)}")
            db.rollback()
            continue
    
    db.close()
    
    print("-" * 60)
    print(f"🎉 Import Complete!")
    print(f"📈 Successfully imported: {imported_count} voice models")
    print(f"💾 Models registered in Whicoustic voice registry")
    print(f"🌐 Public models available for voice cloning")
    
    return imported_count > 0

def main():
    parser = argparse.ArgumentParser(description='Import trained voice models into Whicoustic')
    parser.add_argument('--models_dir', default='models/trained_models', 
                       help='Directory containing trained models')
    parser.add_argument('--admin_user_id', help='Admin user ID for model ownership')
    
    args = parser.parse_args()
    
    success = import_trained_models(args.models_dir, args.admin_user_id)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())