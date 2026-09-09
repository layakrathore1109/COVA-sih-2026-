import os

try:
    from extract import extract_text, extract_excel
except ImportError:
    from backend.extract import extract_text, extract_excel

def chunk_text(text, chunk_size=400, overlap=50):
    """
    Splits text into word-based chunks with overlap.
    """
    if not text:
        return []
        
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        
    return chunks

def chunk_document(file_path):
    """
    Detects if the file is a PDF or Excel/CSV, calls the right extraction function,
    and returns a list of dicts with chunks and metadata.
    """
    filename = os.path.basename(file_path)
    text = ""
    
    if filename.lower().endswith('.pdf'):
        text = extract_text(file_path)
    elif filename.lower().endswith(('.csv', '.xlsx')):
        text, _ = extract_excel(file_path)
    else:
        print(f"Unsupported file type for chunking: {filename}")
        return []
        
    chunks = chunk_text(text)
    print(len(chunks))
    
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            'text': chunk,
            'source': filename,
            'chunk_index': i
        })
        
    return result

