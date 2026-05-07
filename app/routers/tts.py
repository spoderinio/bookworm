import os
import subprocess
import tempfile
import hashlib
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/tts")

PIPER = os.path.expanduser("~/piper/piper")
MODELS_DIR = os.path.expanduser("~/piper-voices")

# Cache dir for generated audio
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Available voices - will be populated from piper-voices dir
def get_available_voices() -> list[dict]:
    voices = []
    if os.path.isdir(MODELS_DIR):
        for f in os.listdir(MODELS_DIR):
            if f.endswith(".onnx") and not f.endswith(".json"):
                voices.append({"id": f, "name": f.replace(".onnx", "").replace("_", " ")})
    return voices


def get_default_voice() -> str:
    voices = get_available_voices()
    if voices:
        return voices[0]["id"]
    return ""


@router.get("/speak")
async def speak(
    text: str = Query(...),
    voice: str = Query(""),
    speed: float = Query(1.0, ge=0.5, le=2.0),
):
    """Generate TTS audio for given text. Returns WAV audio."""
    if not os.path.exists(PIPER):
        return JSONResponse({"error": "Piper не е намерен"}, status_code=500)

    voice_file = voice or get_default_voice()
    if not voice_file:
        return JSONResponse({"error": "Няма наличен глас"}, status_code=500)

    model_path = os.path.join(MODELS_DIR, voice_file)
    if not os.path.exists(model_path):
        return JSONResponse({"error": f"Гласът не е намерен: {voice_file}"}, status_code=404)

    # length_scale: 1.0 = normal, >1.0 = slower, <1.0 = faster
    length_scale = round(1.0 / speed, 3)

    # Cache key
    cache_key = hashlib.md5(f"{text}{voice_file}{length_scale}".encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.wav")

    if not os.path.exists(cache_path):
        tmp = tempfile.mktemp(suffix=".wav")
        try:
            subprocess.run(
                [PIPER, "--model", model_path,
                 "--length_scale", str(length_scale),
                 "--output_file", tmp],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            os.rename(tmp, cache_path)
        except subprocess.CalledProcessError as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            return JSONResponse({"error": f"Piper грешка: {e.stderr.decode()}"}, status_code=500)

    return FileResponse(cache_path, media_type="audio/wav")


@router.get("/voices")
async def list_voices():
    return JSONResponse(get_available_voices())
