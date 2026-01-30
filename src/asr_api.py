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

# --- CONFIGURATION: UPDATE THESE PATHS ---
# Replace the strings below with the actual paths on your local machine
MODEL_PATH = r"ADD_YOUR_MODEL_FILEPATH_HERE" 
FFMPEG_PATH = r"ADD_YOUR_FFMPEG_FILEPATH_HERE" 

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load Model
if os.path.exists(MODEL_PATH):
    print(f"Loading model on {device}: {MODEL_PATH}")
    model = nemo_asr.models.EncDecHybridRNNTCTCModel.restore_from(
        restore_path=MODEL_PATH,
        map_location=torch.device(device)
    )
    model.eval()
    model.change_decoding_strategy(decoder_type='ctc')
else:
    print(f"Error: Model not found! Please update MODEL_PATH in the script.")

@app.post("/transcribe")
async def transcribe(lang: str = Query(..., description="Language code (e.g., 'hi', 'ta')"), 
                      file: UploadFile = File(...)):
    raw_path = f"raw_{file.filename}"
    fixed_path = f"fixed_{file.filename}.wav"
    convert_path = f"converted_{file.filename}.wav"
    
    temp_files = [raw_path, fixed_path, convert_path]
    
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Multi-Format Support (M4A to WAV) using FFmpeg
        if raw_path.lower().endswith(".m4a"):
            # Uses the FFMPEG_PATH defined above
            subprocess.run([
                FFMPEG_PATH, "-y", "-i", raw_path, 
                "-ar", "16000", "-ac", "1", convert_path
            ], check=True, capture_output=True)
            process_target = convert_path
        else:
            process_target = raw_path

        # 2. Universal Audio Normalization (16kHz Mono)
        audio, sr = librosa.load(process_target, sr=16000, mono=True)
        sf.write(fixed_path, audio, 16000)

        # 3. Model Inference
        transcription = model.transcribe([fixed_path], batch_size=1, language_id=lang)

        # 4. Extract Text from Hybrid Output
        if isinstance(transcription, tuple):
            text = transcription[1] if transcription[1] else transcription[0]
        else:
            text = transcription

        while isinstance(text, list) and len(text) > 0:
            text = text[0]

        final_text = text if (text and isinstance(text, str)) else ""
        
        return {"status": "success", "transcription": final_text}

    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return {"status": "error", "message": f"Processing failed: {str(e)}"}

    finally:
        # 5. Robust Cleanup of temporary files
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    print(f"Cleanup error for {path}: {cleanup_error}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
