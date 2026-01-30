import gradio as gr
import requests
import json
import time
import numpy as np
import faiss
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from google.api_core import exceptions
from tavily import TavilyClient

# --- 1. CONFIGURATION ---
# MODIFY THESE: Replace the strings below with your actual API keys.
SARVAM_API_KEY = "ADD_YOUR_SARVAM_API_KEY_HERE"
GEMINI_API_KEY = "ADD_YOUR_GEMINI_API_KEY_HERE"
TAVILY_API_KEY = "ADD_YOUR_TAVILY_API_KEY_HERE"

# MODIFY THIS: Point to your local FastAPI ASR server (from Task 3)
ASR_ENDPOINT = "http://127.0.0.1:8000/transcribe" 

# Initialize Models and Clients
genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel('gemini-2.5-flash-lite') 
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# --- 2. THE TRANSLATION ENGINE ---
def translate_to_english(text):
    """Bridge: Regional Language -> English using Sarvam AI"""
    while isinstance(text, list): 
        text = text[0] if text else ""
    if not text or not text.strip(): 
        return None
    
    url = "https://api.sarvam.ai/translate"
    payload = {
        "input": text.strip(),
        "source_language_code": "ta-IN", # Source: Tamil
        "target_language_code": "en-IN", # Target: English
        "model": "sarvam-translate:v1"
    }
    headers = {
        "api-subscription-key": SARVAM_API_KEY, 
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers)
        return res.json().get('translated_text', "") if res.status_code == 200 else None
    except Exception as e:
        print(f"Translation Error: {e}")
        return None

# --- 3. THE LLM RETRY LOGIC ---
def get_gemini_response(prompt):
    """Generates LLM response with handling for rate limits"""
    for i in range(3):
        try:
            response = llm_model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted:
            print(f"⚠️ Rate limit hit. Waiting 60s (Attempt {i+1}/3)...")
            time.sleep(60)
        except Exception as e:
            return f"Gemini Error: {str(e)}"
    return "Gemini is currently overloaded."

# --- 4. CORE PIPELINE ---
def process_voice_query(audio_path, lang_code="ta"):
    """End-to-End Workflow: ASR -> Translation -> Sourcing -> Vector Search -> LLM"""
    try:
        # Step 1: ASR - Sending file to your LOCAL FastAPI endpoint
        with open(audio_path, 'rb') as f:
            asr_res = requests.post(ASR_ENDPOINT, files={'file': f}, params={'lang': lang_code})
        
        if asr_res.status_code != 200:
            return f"❌ Local ASR Error: {asr_res.status_code}. Is your FastAPI server running?", "N/A"
            
        data = asr_res.json()
        raw_text = data.get('transcription', "")

        # Safety check: Stop if ASR fails to decode audio
        if not raw_text or not raw_text.strip():
            return "⚠️ The ASR could not extract any text. Please check audio quality/format.", "N/A"

    except Exception as e:
        return f"❌ Connection Error: {str(e)}", "N/A"   

    # Step 2: Translation to English
    print(f"DEBUG: Transcribed text for translation: '{raw_text}'") 
    english_query = translate_to_english(raw_text)
    if not english_query: 
        return "Translation failed. Check Sarvam API key.", "N/A"

    # Step 3: Knowledge Sourcing via Tavily
    print(f"DEBUG: Searching web for: '{english_query}'")
    search_res = tavily.search(query=english_query, search_depth="advanced")
    chunks = [r['content'] for r in search_res['results']]
    sources = [r['url'] for r in search_res['results']]

    if not chunks:
        return "No relevant information found on the web.", "N/A"

    # Step 4: Vector Search (FAISS) - Retrieve Top-2 closest chunks
    # We embed the search results and rank them to find the most relevant context
    embeddings = embed_model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    
    query_vec = embed_model.encode([english_query])
    _, indices = index.search(np.array(query_vec).astype('float32'), k=2)
    context = [chunks[idx] for idx in indices[0]]

    # Step 5: Grounded LLM Answer
    prompt = f"Using this web context: {' '.join(context)}\n\nAnswer the question: {english_query}"
    answer = get_gemini_response(prompt)
    
    return answer, sources[0]

# --- 5. GRADIO UI LAYOUT ---
def chat_function(message, history):
    if message.get("files"):
        audio_file = message["files"][0]
        answer, source = process_voice_query(audio_file)
        return f"**Answer:** {answer}\n\n📚 **Source:** {source}"
    return "Please record your question and upload the audio file below."

demo = gr.ChatInterface(
    fn=chat_function,
    title="🎙️ VoxPedia",
    description="Ask anything in Tamil. I transcribe, translate, search, and answer!",
    multimodal=True
)

if __name__ == "__main__":
    # MODIFY THIS: Set share=False for local hosting only
    demo.launch(share=False, debug=True)
