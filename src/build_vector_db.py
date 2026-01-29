import argparse
import os
import sys
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def create_vector_db(file_path):
    # 1. Load the text file
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    print(f"Loading data from {file_path}...")
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()

    # 2. Chunk the text
    # Rationale: RecursiveCharacterTextSplitter maintains semantic flow by splitting
    # at logical points like double newlines or sentences.
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split text into {len(chunks)} chunks.")

    # 3. Initialize Embeddings
    # Using 'all-MiniLM-L6-v2' as it is a highly efficient local model.
    print("Initializing embedding model (this may take a moment)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 4. Create and Store in Vector DB (FAISS)
    # FAISS is chosen for its speed and ability to save index files locally.
    print("Creating Vector Database...")
    vector_db = FAISS.from_documents(chunks, embeddings)

    # Save the DB in the project root
    db_path = "faiss_index"
    vector_db.save_local(db_path)

    print(f"Success! Vector Database saved to local folder '{db_path}'.")

    # 5. Quick Test: Perform a similarity search
    print("\n--- Testing Retrieval ---")
    query = "What is the history of this topic?"
    results = vector_db.similarity_search(query, k=2)

    for i, res in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Content: {res.page_content[:200]}...")

def main():
    parser = argparse.ArgumentParser(description="Create a Vector DB from a text file.")
    parser.add_argument("filename", type=str, help="Path to the .txt file")

    args = parser.parse_args()
    create_vector_db(args.filename)

if __name__ == "__main__":
    main()
