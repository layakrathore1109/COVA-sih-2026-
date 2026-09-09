# CMPDI AI Reporting Solution - SIH 2026

This project is an AI-powered reporting solution designed for CMPDI/CIL as part of the Smart India Hackathon (SIH) 2026. It features a RAG-based R&D prototype with three main modules:
1. **AI Query & Response**: RAG over coal and mining PDFs.
2. **Word Cloud & Topic Identification**: Discovering themes in documents.
3. **Automated Report Generation**: Structured extraction and report building.

## Tech Stack

- **Backend / Core**: Python 3.10+
- **PDF Processing**: `pdfplumber` (digital text extraction), `pytesseract` (OCR for scanned PDFs)
- **Vector Database**: `chromadb`
- **Generative AI**: `google-generativeai` SDK (Gemini 3 Pro Preview)
- **Topic Modeling & Visualization**: `BERTopic`, `wordcloud`
- **Document Generation**: `python-docx`
- **Environment Management**: `python-dotenv`
- **Frontend**: React

## Setup Instructions

Follow these steps to set up the project locally.

### 1. Clone the repository
```bash
git clone <repository_url>
cd cmpdi-ai-reporting
```

### 2. Create and activate a Virtual Environment
```bash
python -m venv venv
```
Activate the environment:
- **Windows**: `.\venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the provided `.env.example` file to create your local `.env` file:
```bash
cp .env.example .env
```
Open `.env` and replace `your_key_here` with your actual Gemini API key.

### 5. Build the Vector Database
To initialize and populate the vector store with sample documents, run:
```bash
python backend/vector_store.py
```
