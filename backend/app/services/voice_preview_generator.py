"""
Voice Preview Generation System for Whicoustic Platform
Generates voice samples and previews for available voices
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .tts_inference_engine import TTSInferenceEngine, SynthesisRequest

@dataclass
class PreviewSpec:
    """Voice preview specification"""
    text: str
    duration: str
    description: str
    use_case: str

class VoicePreviewGenerator:
    """Generates voice previews and samples"""
    
    def __init__(self, tts_engine: TTSInferenceEngine):
        self.tts_engine = tts_engine
        self.logger = logging.getLogger(__name__)
        
        # Standard preview texts
        self.preview_texts = {
            'greeting': PreviewSpec(
                text="Hello! Welcome to Whicoustic. I'm here to help you create natural sounding speech from any text.",
                duration="short",
                description="Friendly greeting",
                use_case="customer_service"
            ),
            'professional': PreviewSpec(
                text="Good morning. This is a professional voice demonstration showcasing clear articulation and business-appropriate tone.",
                duration="medium", 
                description="Professional business tone",
                use_case="corporate_communications"
            ),
            'storytelling': PreviewSpec(
                text="Once upon a time, in a land far away, there lived a curious inventor who dreamed of bringing stories to life through the magic of artificial intelligence.",
                duration="long",
                description="Narrative storytelling",
                use_case="audiobooks"
            ),
            'technical': PreviewSpec(
                text="To configure the system settings, navigate to the main dashboard and select advanced options. The parameters can be adjusted using the provided controls.",
                duration="medium",
                description="Technical explanation",
                use_case="training_materials"
            ),
            'conversational': PreviewSpec(
                text="Hey there! Hope you're having a great day. This voice is perfect for casual conversations and friendly interactions.",
                duration="short",
                description="Casual conversation",
                use_case="chatbots"
            ),
            'announcement': PreviewSpec(
                text="Attention passengers, the train will be arriving on platform two in approximately five minutes. Please stand clear of the doors.",
                duration="medium",
                description="Public announcement",
                use_case="public_systems"
            )
        }
    
    async def generate_preview_for_voice(
        self,
        voice_id: str,
        preview_type: str = "greeting",
        custom_text: Optional[str] = None,
        quality: str = "high"
    ) -> Dict[str, Any]:
        """Generate a single preview for a voice"""
        
        try:
            # Use custom text or predefined preview
            if custom_text:
                text = custom_text
                preview_spec = PreviewSpec(
                    text=custom_text,
                    duration="custom",
                    description="Custom text",
                    use_case="custom"
                )
            else:
                if preview_type not in self.preview_texts:
                    preview_type = "greeting"
                preview_spec = self.preview_texts[preview_type]
                text = preview_spec.text
            
            # Generate preview
            result = await self.tts_engine.generate_voice_preview(voice_id, text)
            
            # Get voice info
            voices = await self.tts_engine.get_available_voices()
            voice_info = next((v for v in voices if v['id'] == voice_id), None)
            
            if not voice_info:
                raise ValueError(f"Voice not found: {voice_id}")
            
            preview_data = {
                'voice_id': voice_id,
                'voice_info': voice_info,
                'preview_type': preview_type,
                'preview_spec': {
                    'text': preview_spec.text,
                    'duration': preview_spec.duration,
                    'description': preview_spec.description,
                    'use_case': preview_spec.use_case
                },
                'audio_data': result.audio_data,
                'audio_metadata': {
                    'duration': result.duration,
                    'sample_rate': result.sample_rate,
                    'format': result.format,
                    'size_bytes': len(result.audio_data)
                },
                'generation_metadata': result.metadata,
                'generated_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated {preview_type} preview for voice {voice_id}")
            return preview_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate preview for voice {voice_id}: {e}")
            raise
    
    async def generate_all_previews_for_voice(
        self,
        voice_id: str,
        preview_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate all preview types for a voice"""
        
        if not preview_types:
            preview_types = list(self.preview_texts.keys())
        
        voice_previews = {
            'voice_id': voice_id,
            'previews': {},
            'generation_summary': {
                'total_requested': len(preview_types),
                'successful': 0,
                'failed': 0,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        for preview_type in preview_types:
            try:
                preview = await self.generate_preview_for_voice(voice_id, preview_type)
                voice_previews['previews'][preview_type] = preview
                voice_previews['generation_summary']['successful'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to generate {preview_type} preview for {voice_id}: {e}")
                voice_previews['previews'][preview_type] = {
                    'error': str(e),
                    'failed_at': datetime.now().isoformat()
                }
                voice_previews['generation_summary']['failed'] += 1
        
        return voice_previews
    
    async def generate_voice_showcase(
        self,
        voice_ids: Optional[List[str]] = None,
        preview_type: str = "greeting",
        max_voices: int = 10
    ) -> Dict[str, Any]:
        """Generate a showcase with multiple voices using the same text"""
        
        try:
            # Get available voices if not specified
            if not voice_ids:
                all_voices = await self.tts_engine.get_available_voices()
                # Select top quality voices
                voice_ids = [v['id'] for v in all_voices[:max_voices]]
            
            showcase = {
                'showcase_type': preview_type,
                'preview_spec': self.preview_texts.get(preview_type, self.preview_texts['greeting']),
                'voices': {},
                'summary': {
                    'total_voices': len(voice_ids),
                    'successful': 0,
                    'failed': 0,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
            # Generate previews for all voices
            tasks = []
            for voice_id in voice_ids:
                task = self.generate_preview_for_voice(voice_id, preview_type)
                tasks.append((voice_id, task))
            
            # Execute all tasks concurrently
            for voice_id, task in tasks:
                try:
                    preview = await task
                    showcase['voices'][voice_id] = preview
                    showcase['summary']['successful'] += 1
                except Exception as e:
                    self.logger.error(f"Showcase failed for voice {voice_id}: {e}")
                    showcase['voices'][voice_id] = {
                        'error': str(e),
                        'failed_at': datetime.now().isoformat()
                    }
                    showcase['summary']['failed'] += 1
            
            return showcase
            
        except Exception as e:
            self.logger.error(f"Failed to generate voice showcase: {e}")
            raise
    
    async def generate_comparison_samples(
        self,
        voice_ids: List[str],
        text: str,
        variations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comparison samples for multiple voices with same text"""
        
        if not variations:
            variations = {
                'normal': {'speed': 1.0, 'pitch_shift': 0.0},
                'fast': {'speed': 1.3, 'pitch_shift': 0.0},
                'slow': {'speed': 0.8, 'pitch_shift': 0.0},
                'high_pitch': {'speed': 1.0, 'pitch_shift': 2.0},
                'low_pitch': {'speed': 1.0, 'pitch_shift': -2.0}
            }
        
        comparison = {
            'comparison_text': text,
            'variations': variations,
            'voices': {},
            'summary': {
                'total_voices': len(voice_ids),
                'total_variations': len(variations),
                'successful_samples': 0,
                'failed_samples': 0,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        for voice_id in voice_ids:
            voice_samples = {'voice_id': voice_id, 'variations': {}}
            
            for variation_name, params in variations.items():
                try:
                    # Create synthesis request with variation parameters
                    request = SynthesisRequest(
                        text=text,
                        voice_id=voice_id,
                        speed=params.get('speed', 1.0),
                        pitch_shift=params.get('pitch_shift', 0.0),
                        emotion=params.get('emotion', 'neutral'),
                        quality='high'
                    )
                    
                    result = await self.tts_engine.synthesize_speech(request)
                    
                    voice_samples['variations'][variation_name] = {
                        'parameters': params,
                        'audio_data': result.audio_data,
                        'metadata': {
                            'duration': result.duration,
                            'sample_rate': result.sample_rate,
                            'size_bytes': len(result.audio_data)
                        },
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    comparison['summary']['successful_samples'] += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to generate {variation_name} variation for voice {voice_id}: {e}")
                    voice_samples['variations'][variation_name] = {
                        'parameters': params,
                        'error': str(e),
                        'failed_at': datetime.now().isoformat()
                    }
                    comparison['summary']['failed_samples'] += 1
            
            comparison['voices'][voice_id] = voice_samples
        
        return comparison
    
    async def save_preview_to_file(
        self,
        preview_data: Dict[str, Any],
        output_dir: str = "voice_previews"
    ) -> str:
        """Save preview audio to file"""
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            voice_id = preview_data['voice_id']
            preview_type = preview_data['preview_type']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"{voice_id}_{preview_type}_{timestamp}.wav"
            file_path = output_path / filename
            
            with open(file_path, 'wb') as f:
                f.write(preview_data['audio_data'])
            
            # Save metadata
            metadata_file = output_path / f"{filename}.json"
            metadata = {
                'voice_id': voice_id,
                'preview_type': preview_type,
                'audio_file': str(file_path),
                'voice_info': preview_data['voice_info'],
                'preview_spec': preview_data['preview_spec'],
                'audio_metadata': preview_data['audio_metadata'],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Saved preview to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save preview: {e}")
            raise
    
    async def create_voice_catalog(
        self,
        output_dir: str = "voice_catalog",
        include_all_previews: bool = False
    ) -> Dict[str, Any]:
        """Create a comprehensive voice catalog with previews"""
        
        try:
            catalog_path = Path(output_dir)
            catalog_path.mkdir(parents=True, exist_ok=True)
            
            # Get all available voices
            all_voices = await self.tts_engine.get_available_voices()
            
            catalog = {
                'catalog_info': {
                    'name': 'Whicoustic Voice Catalog',
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'total_voices': len(all_voices),
                    'preview_types_included': list(self.preview_texts.keys()) if include_all_previews else ['greeting']
                },
                'voices': {}
            }
            
            preview_types = list(self.preview_texts.keys()) if include_all_previews else ['greeting']
            
            for voice in all_voices:
                voice_id = voice['id']
                self.logger.info(f"Creating catalog entry for voice {voice_id}")
                
                try:
                    if include_all_previews:
                        voice_previews = await self.generate_all_previews_for_voice(voice_id, preview_types)
                    else:
                        preview = await self.generate_preview_for_voice(voice_id, 'greeting')
                        voice_previews = {
                            'voice_id': voice_id,
                            'previews': {'greeting': preview}
                        }
                    
                    # Save audio files
                    for preview_type, preview_data in voice_previews['previews'].items():
                        if 'audio_data' in preview_data:
                            audio_filename = f"{voice_id}_{preview_type}.wav"
                            audio_path = catalog_path / audio_filename
                            
                            with open(audio_path, 'wb') as f:
                                f.write(preview_data['audio_data'])
                            
                            # Replace audio data with file reference
                            preview_data['audio_file'] = audio_filename
                            del preview_data['audio_data']
                    
                    catalog['voices'][voice_id] = voice_previews
                    
                except Exception as e:
                    self.logger.error(f"Failed to create catalog entry for voice {voice_id}: {e}")
                    catalog['voices'][voice_id] = {
                        'error': str(e),
                        'voice_info': voice,
                        'failed_at': datetime.now().isoformat()
                    }
            
            # Save catalog metadata
            catalog_file = catalog_path / "catalog.json"
            with open(catalog_file, 'w') as f:
                json.dump(catalog, f, indent=2)
            
            self.logger.info(f"Voice catalog created at {catalog_path}")
            
            return {
                'catalog_path': str(catalog_path),
                'catalog_file': str(catalog_file),
                'total_voices': len(all_voices),
                'successful_voices': len([v for v in catalog['voices'].values() if 'error' not in v]),
                'catalog_data': catalog
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create voice catalog: {e}")
            raise

# Example usage and testing
async def main():
    """Example usage of the voice preview generator"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize TTS engine and preview generator
    registry_path = "../models/whicoustic_voice_registry/voice_registry.json"
    tts_engine = TTSInferenceEngine(registry_path)
    preview_generator = VoicePreviewGenerator(tts_engine)
    
    # Wait for engine to load
    await asyncio.sleep(1)
    
    # Get available voices
    voices = await tts_engine.get_available_voices()
    print(f"Available voices: {len(voices)}")
    
    if voices:
        # Generate a single preview
        voice_id = voices[0]['id']
        preview = await preview_generator.generate_preview_for_voice(voice_id, "greeting")
        print(f"Generated greeting preview for {voice_id}: {len(preview['audio_data'])} bytes")
        
        # Generate a voice showcase
        top_voices = [v['id'] for v in voices[:3]]
        showcase = await preview_generator.generate_voice_showcase(top_voices, "professional")
        print(f"Generated showcase with {len(showcase['voices'])} voices")
        
        # Create a voice catalog (limited for testing)
        catalog = await preview_generator.create_voice_catalog("test_catalog", include_all_previews=False)
        print(f"Created voice catalog: {catalog['catalog_path']}")

if __name__ == "__main__":
    asyncio.run(main())