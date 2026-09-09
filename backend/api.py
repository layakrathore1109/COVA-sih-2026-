import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.rag_pipeline import ask
from backend.topics import generate_topics, generate_wordcloud
from backend.report_gen import generate_report
from backend.vector_store import get_chroma_client, get_or_create_collection, populate_db

app = FastAPI(title="COVA API")

# Setup CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
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
        topics = generate_topics(data_dir)
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
        # Assuming filename is provided as a basename or full path inside data/
        if os.path.isabs(req.filename):
            file_path = req.filename
        else:
            file_path = os.path.join(data_dir, req.filename)
            
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {req.filename} not found in {data_dir}")
            
        output_path = generate_report(file_path)
        if output_path:
            return {"path": output_path, "message": "Report generated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Report generation failed internally")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
