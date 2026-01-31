import uvicorn
import shutil
import os
import torch
import librosa
import subprocess
import soundfile as sf
from fastapi import FastAPI, File, UploadFile, Query
import nemo.collections.asr as nemo_asr

app = FastAPI(title="VoxPedia ASR Service")


# 1. USER CONFIGURATION (PASTE YOUR PATHS HERE)

# Path to your .nemo model file (e.g., D:\models\indicconformer.nemo)
MODEL_PATH = r"PASTE_YOUR_MODEL_PATH_HERE"

# Path to your ffmpeg.exe (e.g., C:\ffmpeg\bin\ffmpeg.exe)
FFMPEG_PATH = r"PASTE_YOUR_FFMPEG_PATH_HERE"

# Automatically selects GPU (cuda) if available, otherwise defaults to CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# --- Model Initialization ---
if os.path.exists(MODEL_PATH):
    print(f"Loading model on {device}: {MODEL_PATH}")
    model = nemo_asr.models.EncDecHybridRNNTCTCModel.restore_from(
        restore_path=MODEL_PATH,
        map_location=torch.device(device)
    )
    model.eval()
    # Using CTC decoding strategy for efficient real-time transcription
    model.change_decoding_strategy(decoder_type='ctc')
else:
    print(f"Error: Model not found at {MODEL_PATH}")


@app.post("/transcribe")
async def transcribe(lang: str = Query(...), file: UploadFile = File(...)):
    """
    Endpoint to transcribe audio files.
    - lang: The language ID (e.g., 'ta' for Tamil)
    - file: The audio file (mp3, wav, m4a, etc.)
    """
    
    # Generate unique temporary filenames to prevent request collisions
    request_id = os.urandom(3).hex()
    raw_path = f"raw_{request_id}_{file.filename}"
    sanitized_path = f"clean_{request_id}.wav"
    
    temp_files = [raw_path, sanitized_path]
    
    # Save the incoming uploaded file to disk
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # --- 1. Audio Sanitization (Stream Processing) ---
        # We use FFmpeg to force re-encoding into a clean 16kHz Mono PCM WAV.
        # This fixes 'Illegal MPEG-Header' errors and synchronization issues.
        print(f"Sanitizing audio stream: {raw_path}")
        subprocess.run([
            FFMPEG_PATH, "-y", "-i", raw_path, 
            "-ar", "16000", "-ac", "1", "-f", "wav", sanitized_path
        ], check=True, capture_output=True)

        # --- 2. Transcription Logic ---
        # NeMo processes the sanitized WAV file
        transcription = model.transcribe([sanitized_path], batch_size=1, language_id=lang)

        # --- 3. Result Extraction ---
        # Handles various return types from the NeMo hybrid model
        if isinstance(transcription, tuple):
            text = transcription[1] if transcription[1] else transcription[0]
        else:
            text = transcription

        # Deep cleaning of the result list/string
        while isinstance(text, list) and len(text) > 0:
            text = text[0]

        final_text = text if (text and isinstance(text, str)) else ""
        
        return {"status": "success", "transcription": final_text}

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")
        return {"status": "error", "message": "Audio sanitization failed. Ensure FFmpeg path is correct."}
    except Exception as e:
        print(f"Transcription Error: {str(e)}")
        return {"status": "error", "message": f"Processing failed: {str(e)}"}

    finally:
        # --- 4. Robust Cleanup ---
        # Delete temporary files to free up disk space
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    print(f"Could not delete {path}: {cleanup_error}")


if __name__ == "__main__":
    # Runs the server locally on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
