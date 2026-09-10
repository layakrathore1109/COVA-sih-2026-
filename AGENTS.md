# Project: AI Reporting Solution for CMPDI/CIL — SIH 2026

## What we're building
A RAG-based prototype with three modules:
1. AI Query & Response (RAG over coal/mining PDFs)
2. Word Cloud + Topic Identification
3. Automated Report Generation (one sample report, structured extraction)

## Tech stack (use exactly these, no substitutions)
- Python 3.10+
- pdfplumber (digital PDF text extraction)
- pytesseract (OCR for scanned PDFs)
- ChromaDB (vector store, use its built-in embedding function — no separate embeddings API)
google-generativeai SDK (model: gemini-3.1-pro-preview) for all LLM calls
- BERTopic + wordcloud for topic modeling
- python-docx for report generation
- React for the frontend
- python-dotenv for loading GEMINI_API_KEY from .env

## Folder structure rules
- All backend logic goes in /backend as separate files (one responsibility per file)
- React app.jsx stays in the root and imports from /backend
- Generated outputs (reports, word cloud images) save to /outputs
- Sample PDFs are in /data

## Coding style rules
- Keep functions small and well-commented — team is AI/ML beginner level
- Never hardcode the API key — always load via python-dotenv
- Add print statements or return values that make it easy to verify each function works before moving to the next
- Prefer simple, readable code over clever abstractions