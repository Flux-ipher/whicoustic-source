import os
import traceback

os.environ["COQUI_TOS_AGREED"] = "1"
import torch
try:
    if hasattr(torch.serialization, "add_safe_globals"):
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import XttsAudioConfig 
        torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
except Exception as e:
    print("Safe globals patch error:", e)

try:
    from TTS.api import TTS
    print("TTS imported successfully")
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    print("TTS model initialized successfully")
except Exception as e:
    print("Initialization failed:")
    traceback.print_exc()
