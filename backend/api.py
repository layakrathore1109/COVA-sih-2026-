import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.rag_pipeline import ask
from backend.topics import generate_topics, generate_wordcloud
from backend.report_gen import generate_report
from backend.vector_store import get_chroma_client, get_or_create_collection, populate_db
from backend.extract import extract_text
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="COVA API")

# Setup CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")
outputs_dir = os.path.join(base_dir, "outputs")
frontend_dir = os.path.join(base_dir, "frontend")
os.makedirs(frontend_dir, exist_ok=True)

class AskRequest(BaseModel):
    question: str

class ReportRequest(BaseModel):
    filename: str

@app.on_event("startup")
def startup_event():
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    
    if collection.count() == 0:
        print("ChromaDB collection is empty. Indexing documents...")
        json_path = os.path.join(outputs_dir, "extracted_data.json")
        pdf_data = []
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data:
                if item.get("type") in ["pdf", "tabular"]:
                    pdf_data.append({"filename": item["filename"], "text": item["text"]})
            if pdf_data:
                populate_db(pdf_data)
                print("Initial document indexing complete.")
            else:
                print("No valid PDF data found to index.")
        else:
            print(f"Cannot index documents, missing {json_path}")
    else:
        print(f"ChromaDB collection already contains {collection.count()} chunks. Skipping indexing.")

    # Pre-generate topics and wordcloud if they don't exist
    topics_file = os.path.join(outputs_dir, "topics.json")
    wordcloud_path = os.path.join(outputs_dir, "wordcloud.png")
    
    if not os.path.exists(topics_file):
        print("Pre-generating topics...")
        topics = generate_topics(data_dir)
        with open(topics_file, 'w', encoding='utf-8') as f:
            json.dump(topics, f)
            
    if not os.path.exists(wordcloud_path):
        print("Pre-generating wordcloud...")
        generate_wordcloud(data_dir)

@app.post("/ask")
def ask_question(req: AskRequest):
    try:
        result = ask(req.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/topics")
def get_topics():
    try:
        topics_file = os.path.join(outputs_dir, "topics.json")
        if os.path.exists(topics_file):
            with open(topics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        topics = generate_topics(data_dir)
        with open(topics_file, 'w', encoding='utf-8') as f:
            json.dump(topics, f)
            
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wordcloud")
def get_wordcloud():
    try:
        wordcloud_path = os.path.join(outputs_dir, "wordcloud.png")
        if not os.path.exists(wordcloud_path):
            generate_wordcloud(data_dir)
            
        if os.path.exists(wordcloud_path):
            return FileResponse(wordcloud_path, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Word cloud generation failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-report")
def create_report(req: ReportRequest):
    try:
        if os.path.isabs(req.filename):
            file_path = req.filename
        else:
            file_path = os.path.join(data_dir, req.filename)
            
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {req.filename} not found in {data_dir}")
            
        output_path, fields = generate_report(file_path)
        if output_path and fields:
            filename = os.path.basename(output_path)
            return {"filename": filename, "message": "Report generated successfully", "fields": fields}
        else:
            raise HTTPException(status_code=500, detail="Report generation failed internally")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-report/{filename}")
def download_report(filename: str):
    file_path = os.path.join(outputs_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/stats")
def get_stats():
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    total_chunks = collection.count()
    
    total_documents = 0
    json_path = os.path.join(outputs_dir, "extracted_data.json")
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            total_documents = len(data)
            
    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks
    }

@app.post("/summarize")
def summarize_doc(file: UploadFile = File(...)):
    try:
        temp_path = os.path.join(data_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            buffer.write(file.file.read())
            
        text = ""
        if temp_path.lower().endswith('.pdf'):
            text = extract_text(temp_path)
        elif temp_path.lower().endswith(('.xlsx', '.csv')):
            from backend.extract import extract_excel
            text, _ = extract_excel(temp_path)
            
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
            
        # Using the centralized llm_utils instead of initializing the client directly
        prompt = f"Please provide a clear, plain-language summary of the following document text, highlighting the most important points. Use markdown formatting (bullet points, bold text) for readability:\n\n{text}"
        
        try:
            from backend.llm_utils import call_gemini_with_fallback
        except ImportError:
            from llm_utils import call_gemini_with_fallback
            
        try:
            response_data = call_gemini_with_fallback(prompt)
            summary = response_data["text"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini API failed: {e}")
            
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend files at the root
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
