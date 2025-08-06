import whisper
import os
import logging
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Whisper")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=DEVICE)
logger.info(f"✅ Whisper model loaded on {DEVICE}")

def transcribe_stream(file_path: str) -> str:
    if not os.path.isfile(file_path):
        logger.error(f"❌ Audio file not found: {file_path}")
        return ""
    try:
        result = model.transcribe(file_path, language="en", fp16=torch.cuda.is_available())
        text = result.get("text", "").strip()
        return text
    except Exception as e:
        logger.exception("❌ Whisper transcription failed:")
        return ""