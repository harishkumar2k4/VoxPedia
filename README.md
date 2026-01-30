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

## Observations and Challenges
- Observations: I found that while the wikipedia library is efficient, passing specific search queries (e.g., "Python programming language") significantly improves the quality of the retrieved text compared to broad terms.

- Challenges: The primary challenge was handling DisambiguationErrors. I implemented a nested try-except block to catch these errors and automatically proceed with the first suggested option to ensure the pipeline remains autonomous and doesn't crash on broad queries.

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

## Observations and Challenges

- Observations

  * Semantic Integrity: Using RecursiveCharacterTextSplitter significantly improved retrieval quality compared to basic splitting. By prioritizing natural breaks like paragraphs and sentences, the chunks remained contextually meaningful.

  * Local Embedding Efficiency: The all-MiniLM-L6-v2 model offered a high-performance, zero-cost solution. Running it locally eliminated API latency and simplified the development environment.

- Challenges

  * Context Tuning: Finding the right balance for chunk_size was difficult. I settled on 1000 characters to ensure the top-2 retrieved results provided sufficient detail for the LLM without exceeding its focus window.

  * Character Encoding: I encountered errors when loading files with special characters. This was resolved by forcing utf-8 encoding in the TextLoader to ensure cross-platform compatibility.

# Task 3: Deploying an ASR Model

This module deploys a high-performance Automatic Speech Recognition (ASR) service using FastAPI and the NVIDIA NeMo toolkit. It is designed to transcribe multilingual audio input into text.

## Model Choice: IndicConformer-600M

I chose the Indic-Conformer-600M-Multilingual hybrid model from AI4Bharat.

- Benefits: It supports 22 Indian languages and uses a hybrid CTC-RNNT decoding strategy, providing a superior balance between word error rate (WER) and inference speed.

- Implementation: The deployment uses the CTC decoding strategy for faster real-time response.

## Technical Implementation & Optimization

- FastAPI Wrapper: I wrapped the model in a FastAPI server to create a modular microservice. This allows the ASR "engine" to run on a GPU-enabled backend while serving requests from any lightweight frontend.

- Universal Audio Normalization: ASR models are extremely sensitive to audio formats. I implemented a preprocessing layer using librosa and soundfile to ensure all inputs are converted to 16kHz Mono PCM-WAV before inference.

- Direct FFmpeg Transcoding: To handle proprietary or compressed formats like .m4a and .mp3 on Windows, I integrated a subprocess call to the FFmpeg binary. This bypasses Python library limitations and ensures high-fidelity decoding.

## How to Run

- Install FFmpeg: Download FFmpeg and update the ffmpeg_path in src/asr_api.py to your local bin folder.

- Download Model: Download the .nemo model file and update MODEL_PATH.

- Start the Server:

      python src/asr_api.py
  
- Test the Transcription:

      python src/asr_client_test.py
