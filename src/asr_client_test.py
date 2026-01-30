import requests

def transcribe_audio(file_path, lang_code):
    # Your API URL
    url = "http://localhost:8000/transcribe"
    
    # Define the language parameter
    params = {'lang': lang_code}
    
    # Open the audio file in binary mode
    try:
        with open(file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            
            # Send the POST request
            response = requests.post(url, params=params, files=files)
        
        if response.status_code == 200:
            return response.json().get('transcription')
        else:
            return f"Error: {response.text}"
            
    except FileNotFoundError:
        return "Error: The specified audio file was not found."
    except Exception as e:
        return f"Error: {str(e)}"

# --- GITHUB UPLOAD NOTE ---
# To test this, ensure your FastAPI server (asr_api.py) is running 
# and replace "sample_audio.wav" with your actual file path.
if __name__ == "__main__":
    # Example usage: Change 'sample_audio.wav' to your file and 'ta' to your language code
    result = transcribe_audio("sample_audio.wav", "ta")
    print(f"Transcription: {result}")
