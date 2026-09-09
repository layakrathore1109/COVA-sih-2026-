import os
# pyrefly: ignore [missing-import]
import chromadb
# pyrefly: ignore [missing-import]
from chromadb.utils import embedding_functions

def get_chroma_client():
    """
    Initializes and returns a persistent ChromaDB client.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    return client

def get_or_create_collection(client, collection_name="mining_reports"):
    """
    Gets or creates a collection using Chroma's built-in embedding function.
    """
    # By default, Chroma uses all-MiniLM-L6-v2 which is local and requires no API key.
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name=collection_name, 
        embedding_function=default_ef
    )
    return collection

def chunk_text(text, chunk_size=1000, overlap=200):
    """
    Splits text into chunks of specified size and overlap.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def populate_db(pdf_files_data):
    """
    Populates ChromaDB with extracted text chunks.
    pdf_files_data should be a list of dicts: [{'filename': '...', 'text': '...'}]
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    
    # Check existing files in the database
    existing_data = collection.get(include=["metadatas"])
    existing_filenames = set()
    if existing_data and existing_data["metadatas"]:
        for meta in existing_data["metadatas"]:
            if meta and "source" in meta:
                existing_filenames.add(meta["source"])
    
    docs = []
    metadatas = []
    ids = []
    
    for item in pdf_files_data:
        filename = item['filename']
        
        if filename in existing_filenames:
            print(f"Skipping {filename}, already indexed.")
            continue
            
        text = item['text']
        
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            # Only add non-empty chunks
            if chunk.strip():
                docs.append(chunk)
                metadatas.append({"source": filename, "chunk_index": i})
                ids.append(f"{filename}_chunk_{i}")
            
    if not docs:
        print("No new chunks to add.")
        return collection
        
    print(f"Adding {len(docs)} new chunks to ChromaDB...")
    
    # Process in batches
    batch_size = 5000
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.upsert(
            documents=batch_docs,
            metadatas=batch_metadatas,
            ids=batch_ids
        )
        print(f"  Inserted batch {i//batch_size + 1} ({len(batch_docs)} chunks)")
        
    print("Database population complete.")
    return collection

if __name__ == "__main__":
    import json
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs_dir = os.path.join(base_dir, "outputs")
    json_path = os.path.join(outputs_dir, "extracted_data.json")
    
    print(f"Reading extracted texts from {json_path} for embedding...")
    pdf_data = []
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            if item.get("type") in ["pdf", "tabular"]:
                pdf_data.append({"filename": item["filename"], "text": item["text"]})
                
        if pdf_data:
            print(f"Found {len(pdf_data)} files to index.")
            collection = populate_db(pdf_data)
            print(f"Total chunks in collection '{collection.name}': {collection.count()}")
        else:
            print("No valid PDF data found in the JSON file.")
    else:
        print(f"Error: Extracted data not found at {json_path}. Please run extract.py first.")
