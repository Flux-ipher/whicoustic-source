#!/usr/bin/env python3
"""
Import Advanced Trained Models into Whicoustic Platform
Integrates LibriTTS and Common Voice trained models with full metadata
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def create_voice_registry_entry(training_result: Dict, model_dir: Path) -> Dict:
    """Create a voice registry entry from training results"""
    
    speaker_id = training_result['speaker_id']
    config = training_result['model_config']
    stats = training_result['data_stats']
    voice_chars = config['speaker_info']['voice_characteristics']
    
    # Determine dataset source
    dataset_source = "LibriTTS" if speaker_id.startswith("libri_") else "Common Voice"
    clean_speaker_id = speaker_id.replace("libri_", "").replace("cv_", "")
    
    # Create voice profile
    voice_profile = {
        'voice_id': f"whicoustic_{dataset_source.lower()}_{clean_speaker_id}",
        'display_name': f"{dataset_source} Speaker {clean_speaker_id[:8]}",
        'description': f"High-quality TTS voice trained on {dataset_source} dataset. Quality score: {training_result['quality_score']:.3f}",
        
        # Model information
        'model_info': {
            'model_type': config['model_type'],
            'architecture': config['architecture'],
            'training_config': config['training'],
            'model_path': str(model_dir / "pytorch_model.pth"),
            'config_path': str(model_dir / "model_config.json"),
            'vocoder_config': str(model_dir / "vocoder_config.json")
        },
        
        # Voice characteristics
        'voice_characteristics': {
            'language': 'en-US',
            'gender': voice_chars.get('gender', 'unknown'),
            'age_range': voice_chars.get('age_range', 'unknown'),
            'accent': voice_chars.get('accent', 'american'),
            'pitch_range': voice_chars.get('pitch_estimate', 150),
            'speaking_rate': voice_chars.get('tempo_estimate', 1.0),
            'energy_level': voice_chars.get('energy_level', 0.7),
            'articulation_clarity': voice_chars.get('articulation_clarity', 0.8)
        },
        
        # Quality metrics
        'quality_metrics': {
            'overall_score': training_result['quality_score'],
            'final_loss': training_result['final_loss'],
            'embedding_quality': config['speaker_info']['embedding_quality'],
            'sample_coverage': stats['total_samples'],
            'training_duration': stats['total_duration'],
            'success_rate': stats['success_rate']
        },
        
        # Training metadata
        'training_info': {
            'dataset_source': dataset_source,
            'training_date': training_result['training_start'],
            'training_duration': training_result['training_duration'],
            'epochs': training_result['epochs'],
            'total_samples': stats['total_samples'],
            'avg_sample_duration': stats['avg_duration'],
            'text_coverage': stats['text_coverage']
        },
        
        # Usage settings
        'usage_settings': {
            'is_public': True,
            'license_type': 'open_source' if dataset_source == "Common Voice" else 'academic',
            'commercial_use': dataset_source == "Common Voice",
            'attribution_required': True,
            'quality_tier': 'premium' if training_result['quality_score'] >= 0.9 else 'standard'
        },
        
        # Technical specifications
        'technical_specs': {
            'sample_rate': 22050,
            'bit_depth': 16,
            'channels': 1,
            'format': 'wav',
            'mel_channels': config['architecture']['mel_channels'],
            'embedding_dim': config['architecture']['speaker_embedding_dim'],
            'supported_formats': ['wav', 'mp3', 'flac']
        },
        
        # Metadata
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'version': '1.0',
            'compatible_engines': ['YourTTS', 'VITS', 'FastSpeech2'],
            'tags': [
                dataset_source.lower().replace(" ", "_"),
                f"quality_{training_result['quality_score']:.1f}".replace(".", "_"),
                'multilingual' if dataset_source == "LibriTTS" else 'english',
                'neural_tts',
                'voice_cloning'
            ]
        }
    }
    
    return voice_profile

def import_advanced_models(models_dir: str, output_dir: str = None) -> bool:
    """Import advanced trained models and create Whicoustic registry"""
    
    models_path = Path(models_dir)
    if not models_path.exists():
        print(f"❌ Models directory not found: {models_path}")
        return False
    
    # Load training session summary
    session_path = models_path / "training_session.json"
    if not session_path.exists():
        print(f"❌ Training session file not found: {session_path}")
        return False
    
    with open(session_path, 'r') as f:
        training_session = json.load(f)
    
    print("🚀 Importing Advanced Trained Models into Whicoustic")
    print("=" * 70)
    print(f"📅 Training Session: {training_session['session_start']}")
    print(f"📊 Total Models: {training_session['summary']['successful_models']}")
    print(f"⭐ High Quality: {training_session['summary']['high_quality_models']}")
    print(f"📈 Average Quality: {training_session['summary']['average_quality']:.3f}")
    print("=" * 70)
    
    # Set up output directory
    if not output_dir:
        output_dir = models_path.parent / "whicoustic_voice_registry"
    
    registry_dir = Path(output_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)
    
    # Create voice registry
    voice_registry = {
        'registry_info': {
            'created_at': datetime.now().isoformat(),
            'version': '2.0',
            'total_voices': len(training_session['results']),
            'datasets': list(training_session['datasets'].keys()),
            'quality_threshold': training_session['parameters']['min_quality']
        },
        'voices': {},
        'categories': {
            'libri_speakers': [],
            'common_voice_speakers': [],
            'high_quality': [],
            'premium_tier': [],
            'standard_tier': []
        },
        'quality_distribution': {
            'premium': 0,
            'high': 0,
            'standard': 0,
            'total': 0
        }
    }
    
    # Process each trained model
    imported_count = 0
    categories = voice_registry['categories']
    quality_dist = voice_registry['quality_distribution']
    
    for result in training_session['results']:
        speaker_id = result['speaker_id']
        model_dir = models_path / f"speaker_{speaker_id}"
        
        if not model_dir.exists():
            print(f"⚠️  Model directory not found: {model_dir}")
            continue
        
        print(f"🎤 Processing: {speaker_id}")
        
        try:
            # Create voice registry entry
            voice_profile = create_voice_registry_entry(result, model_dir)
            voice_id = voice_profile['voice_id']
            
            # Add to registry
            voice_registry['voices'][voice_id] = voice_profile
            
            # Categorize voice
            dataset_source = voice_profile['training_info']['dataset_source']
            quality_score = voice_profile['quality_metrics']['overall_score']
            quality_tier = voice_profile['usage_settings']['quality_tier']
            
            if dataset_source == "LibriTTS":
                categories['libri_speakers'].append(voice_id)
            else:
                categories['common_voice_speakers'].append(voice_id)
            
            if quality_score >= 0.9:
                categories['high_quality'].append(voice_id)
                quality_dist['premium'] += 1
            elif quality_score >= 0.8:
                quality_dist['high'] += 1
            else:
                quality_dist['standard'] += 1
            
            if quality_tier == 'premium':
                categories['premium_tier'].append(voice_id)
            else:
                categories['standard_tier'].append(voice_id)
            
            quality_dist['total'] += 1
            imported_count += 1
            
            print(f"  ✅ Imported as {voice_id} (quality: {quality_score:.3f}, tier: {quality_tier})")
            
        except Exception as e:
            print(f"  ❌ Failed to import {speaker_id}: {str(e)}")
            continue
    
    # Save voice registry
    registry_path = registry_dir / "voice_registry.json"
    with open(registry_path, 'w') as f:
        json.dump(voice_registry, f, indent=2)
    
    # Create API-compatible voice list
    api_voices = []
    for voice_id, profile in voice_registry['voices'].items():
        api_voice = {
            'id': voice_id,
            'name': profile['display_name'],
            'description': profile['description'],
            'language': profile['voice_characteristics']['language'],
            'gender': profile['voice_characteristics']['gender'],
            'accent': profile['voice_characteristics']['accent'],
            'quality_score': profile['quality_metrics']['overall_score'],
            'quality_tier': profile['usage_settings']['quality_tier'],
            'dataset': profile['training_info']['dataset_source'],
            'commercial_use': profile['usage_settings']['commercial_use'],
            'tags': profile['metadata']['tags']
        }
        api_voices.append(api_voice)
    
    # Sort by quality score
    api_voices.sort(key=lambda x: x['quality_score'], reverse=True)
    
    api_list_path = registry_dir / "api_voice_list.json"
    with open(api_list_path, 'w') as f:
        json.dump({
            'voices': api_voices,
            'total': len(api_voices),
            'last_updated': datetime.now().isoformat()
        }, f, indent=2)
    
    # Create deployment configuration
    deployment_config = {
        'voice_registry': {
            'path': str(registry_path),
            'api_list': str(api_list_path),
            'model_base_path': str(models_path)
        },
        'tts_config': {
            'default_sample_rate': 22050,
            'supported_formats': ['wav', 'mp3', 'flac'],
            'max_text_length': 1000,
            'batch_size': 4,
            'inference_device': 'auto'
        },
        'quality_tiers': {
            'premium': {'min_score': 0.9, 'max_requests_per_day': 1000},
            'standard': {'min_score': 0.7, 'max_requests_per_day': 500}
        },
        'categories': voice_registry['categories'],
        'statistics': {
            'total_voices': imported_count,
            'quality_distribution': quality_dist,
            'datasets': {
                'LibriTTS': len(categories['libri_speakers']),
                'Common Voice': len(categories['common_voice_speakers'])
            }
        }
    }
    
    config_path = registry_dir / "deployment_config.json"
    with open(config_path, 'w') as f:
        json.dump(deployment_config, f, indent=2)
    
    # Final report
    print("\n" + "=" * 70)
    print("🎉 Advanced Model Import Complete!")
    print("=" * 70)
    print(f"📈 Successfully imported: {imported_count} voice models")
    print(f"🏆 Premium quality (≥0.9): {quality_dist['premium']}")
    print(f"⭐ High quality (≥0.8): {quality_dist['high']}")
    print(f"📊 Standard quality: {quality_dist['standard']}")
    print(f"📚 LibriTTS speakers: {len(categories['libri_speakers'])}")
    print(f"🗣️  Common Voice speakers: {len(categories['common_voice_speakers'])}")
    print("\n📁 Output Files:")
    print(f"  🗂️  Voice Registry: {registry_path}")
    print(f"  🌐 API Voice List: {api_list_path}")
    print(f"  ⚙️  Deployment Config: {config_path}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Import advanced trained models into Whicoustic')
    parser.add_argument('--models_dir', default='../models/advanced_trained',
                       help='Directory containing trained models')
    parser.add_argument('--output_dir', help='Output directory for voice registry')
    
    args = parser.parse_args()
    
    success = import_advanced_models(args.models_dir, args.output_dir)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
