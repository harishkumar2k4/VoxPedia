# Task 1: Data Collection

This module is responsible for identifying the most relevant knowledge source for a given topic and extracting its content for the local knowledge base.

## Features
- Topic Search: Dynamically identifies the closest matching Wikipedia article for any user query using the wikipedia search API.

- Content Extraction: Scrapes the full text, title, and URL of the identified article.

- Automatic Disambiguation: Handles cases where a search term may refer to multiple topics (e.g., "Python") by automatically selecting the most probable match.

- Structured Storage: Sanitizes article titles to create safe filenames and saves the content as a UTF-8 encoded .txt file.

## How to Run
- Navigate to the root directory and run the script via the command line:
  
      python src/wiki_scraper.py "Your Topic Here" 

# Task 2: Creating a Vector Database

This module converts the raw text collected in Task 1 into a searchable vector database using LangChain and FAISS.

## Chunking Strategy
- Chunk Size: I used 1000 characters. This size is large enough to capture meaningful context (roughly 1-2 paragraphs) while staying within the token limits of most embedding models.

- Overlapping: I used an overlap of 200 characters.

    - Justification: Overlapping chunks ensure that semantic information is not lost if a key concept or sentence is split across two chunks. It provides "contextual glue" that helps the retrieval process find relevant snippets even if the query matches the boundary of a chunk.

## Vector Database Choice: FAISS
- Why FAISS? I chose FAISS (Facebook AI Similarity Search) as the vector store.

- Benefits: 
  * Performance: Extremely fast similarity search for dense vectors.

  * Local Storage: It is an open-source library that runs entirely on the local machine, requiring no cloud setup or API costs.

- Drawbacks:

  * Persistence: Unlike managed databases (like Pinecone), it is an in-memory store. While it can be saved to disk, it doesn't offer built-in cloud synchronization or advanced metadata filtering out of the box.

## How to Run
- Navigate to the root directory and run the script via the command line:

      python src/build_vector_db.py data/"Saved .txt file"

# Task 3: Deploying an ASR Model

This module deploys a high-performance Automatic Speech Recognition (ASR) service using FastAPI and the NVIDIA NeMo toolkit. It is designed to transcribe multilingual audio input into text.

## Model Choice: IndicConformer-600M

I chose the Indic-Conformer-600M-Multilingual hybrid model from AI4Bharat.

- Benefits: It supports 22 Indian languages and uses a hybrid CTC-RNNT decoding strategy, providing a superior balance between word error rate (WER) and inference speed.

- Implementation: The deployment uses the CTC decoding strategy for faster real-time response.

## Technical Implementation & Optimization

- FastAPI Wrapper: I wrapped the model in a FastAPI server to create a modular microservice, enabling the GPU-heavy ASR engine to serve requests from any lightweight frontend.

- Mandatory FFmpeg Sanitization: I implemented a mandatory FFmpeg gate that re-encodes all incoming audio into 16kHz Mono PCM-WAV. This bypassed the "Illegal MPEG-Header" and sync errors I faced with standard Python loaders.

- Concurrency & Cleanup: I integrated unique request_id tracking to allow safe, concurrent processing and added a robust finally block to ensure all temporary audio files are cleared from disk.

- Dependency & Environment Sync: I resolved critical ecosystem conflicts by pinning the environment to NumPy < 2.0 and specific Hugging Face Hub versions. Additionally, I integrated unique request-ID tracking to allow for safe, concurrent processing without file collisions.

## How to Run

- Install FFmpeg: (System Requirement):

  - Download: Get the latest "Essentials" build from [Gyan.dev (FFmpeg Windows Builds)](https://www.gyan.dev/ffmpeg/builds/).

  - Setup: Extract the folder and update the ffmpeg_path in src/asr_api.py to point to your local executable (e.g., r"C:\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe").

- Download ASR Model:

  - GitHub Repository: Visit the official [AI4Bharat/IndicConformerASR](https://github.com/AI4Bharat/IndicConformerASR) repository.

  - Direct Download: Navigate to the "Resources (Multilingual)" table and click the "Download" link for the 600M size model (Language Code: multi).

  - Setup: Place the downloaded .nemo file in your project directory and update the MODEL_PATH variable in src/asr_api.py.

- Start the ASR Server: Open a terminal and run the FastAPI service:

      python src/asr_api.py
  
- Test the Transcription: While the server is running, open a separate terminal and run the client test script to verify your setup:

      python src/asr_client_test.py

# Task 4: Translation of the Text
This module handles the conversion of non-English transcriptions (e.g., Tamil or Hindi) into English.

## Implementation Strategy
- API Provider: I utilized Sarvam AI’s Translation API due to its high performance on Indian regional languages compared to standard global translation models.

- Mechanism: The script performs a REST API call to the sarvam-translate:v1 model, which supports 22 scheduled Indian languages.

- Language Handling: I configured the target_language_code to en-IN. While the source_language_code can be hardcoded for specific tasks (like ta-IN for Tamil), setting it to auto allows the pipeline to remain flexible for different users.

## How to Run
- Obtain API Key: Sign up at [Sarvam AI](https://dashboard.sarvam.ai/) to get your subscription key.

- Update Script: Open src/sarvam_translator.py and add your key to the api_key variable.

- Test the Module:

      python src/sarvam_translator.py

# Task 5 & Bonus Task: Integrated RAG Pipeline & Multimodal UI

This final module integrates all previous components into a seamless, voice-enabled chatbot. It combines real-time Speech-to-Text, Machine Translation, Web-scale Retrieval, and Large Language Models (LLMs) into a single interactive application.

## Implementation Strategy
- End-to-End Orchestration: The pipeline follows a strictly sequential flow:

    - ASR: Captures Tamil audio via the local FastAPI server.

    - Translation: Converts the transcript to English via Sarvam AI.

    - Search: Queries the live web using the Tavily API.

    - Vector Ranking: Uses FAISS to embed search results and isolate the top-2 most relevant chunks for the query.

    - LLM Reasoning: Passes the query and context to Gemini-2.5-flash-lite for a grounded, factual answer.

- Vector Database Integration: Unlike a static database, this implementation uses a Dynamic Vector Index. By building an in-memory FAISS index on-the-fly for each query, the system can "re-rank" massive web results and provide the LLM with only the most precise context.

- Bonus UI (Gradio): I developed a multimodal "Chat" interface. This allows users to upload or record audio files directly and see the conversation history along with the sources of the information provided.

## How to Run
- Prerequisites: Ensure your local ASR server (src/asr_api.py) is running on http://127.0.0.1:8000.

- Configuration:
  
    - Open src/main_pipeline.py.

    - Update the following placeholders with your actual keys:

        - SARVAM_API_KEY

        - GEMINI_API_KEY

        - TAVILY_API_KEY

- Launch the Application:

      python src/main_pipeline.py
  
- Interact: Once launched, a local Gradio URL (and a public share link if enabled) will be provided. Upload a .m4a or .wav file in Tamil to receive an English grounded response.

# Project Observations

- Hybrid RAG Effectiveness: Utilizing Tavily for broad web sourcing combined with FAISS for local re-ranking created a highly accurate "Dynamic RAG" system. This ensures the LLM receives the top-2 most relevant snippets rather than unrefined, noisy search results.

- Model Synergy: The combination of IndicConformer (ASR) and Sarvam AI (Translation) proved robust for regional languages. Sarvam's specialization in Indian dialects significantly outperformed generic global translation models in preserving linguistic context.

- Latency Trade-offs: The cascaded architecture (ASR → Translation → Retrieval → LLM) provides high accuracy but introduces a "stacking" delay. Each sequential API call adds roughly 0.5 to 1.5 seconds, impacting real-time feel.

- Prompt Grounding: Forcing the LLM (Gemini) to answer strictly based on retrieved context successfully minimized hallucinations, ensuring the chatbot remained a reliable source for factual queries.

# Technical Challenges
- Audio Stream Corruption: Encountered Illegal Audio-MPEG-Header and synchronization errors when processing raw .m4a and .mp3 files via librosa.
  
    - Solution: Implemented a mandatory FFmpeg sanitization gate to re-encode all incoming audio into a standard 16kHz PCM WAV format before model processing.

- API Dependency Conflicts: Mismatched versions between huggingface_hub, transformers, and NeMo caused frequent import crashes (e.g., the ModelFilter and is_offline_mode errors).

    - Solution: Synchronized the virtual environment by pinning specific stable versions of the Hugging Face ecosystem libraries.

- NumPy 2.0 Breaking Changes: The release of NumPy 2.0 caused significant conflicts with NVIDIA NeMo and Numba, resulting in AttributeError and binary incompatibility issues.
  
    - Solution: Forced a downgrade to NumPy 1.26.4 (pip install "numpy<2") and pinned the version in requirements.txt to maintain compatibility with the NeMo ASR toolkit.

- Nested Output Challenge: The hybrid model often returned transcriptions wrapped in nested lists (e.g., [['text']]) due to multiple decoding hypotheses, causing the translation module to crash.

    - Solution: I implemented a recursive loop to "drill down" through nested lists, isolating the raw string and ensuring a clean, flat text input for the downstream API. 
