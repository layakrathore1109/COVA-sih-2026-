import os
import time
from dotenv import load_dotenv
from google import genai
try:
    from vector_store import get_chroma_client, get_or_create_collection
    from gap_detector import check_coverage
except ImportError:
    from backend.vector_store import get_chroma_client, get_or_create_collection
    from backend.gap_detector import check_coverage

# Load environment variables
load_dotenv()

def retrieve(question, n_results=4):
    """
    Queries the 'mining_reports' collection and returns the top matching chunks
    along with their metadata (source document, chunk index).
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client, "mining_reports")
    
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    chunks = []
    if results and results.get("documents") and len(results["documents"]) > 0:
        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [[None]*len(docs)])[0]
        
        for i in range(len(docs)):
            chunks.append({
                "text": docs[i],
                "metadata": metadatas[i],
                "distance": distances[i]
            })
            
    return chunks

def ask(question):
    """
    Retrieves context for the question, builds a context string, and sends it to
    the LLM to get an answer. Measures total elapsed time.
    """
    start_time = time.time()
    
    # 1. Retrieve relevant chunks
    chunks = retrieve(question)
    
    # 1.5 Check for coverage gap
    gap_check = check_coverage(question, chunks)
    if gap_check['has_gap']:
        return {
            "answer": gap_check['message'],
            "sources": [],
            "elapsed_seconds": time.time() - start_time
        }
    
    # 2. Build context string
    context_parts = []
    sources_set = set()
    
    for i, chunk in enumerate(chunks):
        source_doc = chunk['metadata'].get('source', 'Unknown Document')
        chunk_idx = chunk['metadata'].get('chunk_index', 'Unknown Index')
        sources_set.add(source_doc)
        
        context_parts.append(f"--- Source Document: {source_doc} (Chunk {chunk_idx}) ---\n{chunk['text']}")
        
    context_string = "\n\n".join(context_parts)
    
    # 3. Send to LLM
    prompt = f"""You are a helpful assistant for CMPDI/CIL.
Answer the following question using ONLY the provided context. If the answer is not contained in the context, say so.
Mention which source document(s) the answer came from based on the provided labels.
If multiple numeric figures appear for a similar query across different chunks, explicitly note that they may refer to different scopes or contexts and briefly clarify the distinction, rather than just listing them without explanation.


Context:
{context_string}

Question:
{question}
"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment variables.")
        
    client = genai.Client(api_key=api_key)
    
    # Use gemini-3.7-flash instead of deprecated 2.5 series
    interaction = client.interactions.create(
        model="gemini-3.7-flash",
        input=prompt
    )
    
    answer = interaction.output_text
    
    # 4. Measure elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    
    # 5. Return dict
    return {
        "answer": answer,
        "sources": list(sources_set),
        "elapsed_seconds": elapsed_seconds
    }

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
        
    # Test block
    test_questions = [
        "What are the budget estimates for 2021-22?",
        "What are the key safety initiatives in mining?",
        "What is the capital of France?"
    ]
    
    for test_question in test_questions:
        print(f"=====================================")
        print(f"Question: {test_question}\n")
        
        try:
            result = ask(test_question)
            print("Answer:")
            print(result["answer"])
            print("\nSources:")
            for source in result["sources"]:
                print(f"- {source}")
            print(f"\nElapsed time: {result['elapsed_seconds']:.2f} seconds\n")
        except Exception as e:
            print(f"Error occurred during testing: {e}")
