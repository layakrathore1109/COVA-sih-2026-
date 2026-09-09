import os
# pyrefly: ignore [missing-import]
import pdfplumber
# pyrefly: ignore [missing-import]
import pytesseract
import pandas as pd

def extract_text(pdf_path):
    """
    Extracts text from a PDF using pdfplumber.
    If a page returns little or no text, falls back to pytesseract OCR.
    """
    extracted_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                
                # Check if text is sufficient (threshold can be adjusted)
                if page_text and len(page_text.strip()) > 50:
                    extracted_text += page_text + "\n"
                else:
                    # Fallback to OCR using page.to_image() to get a PIL Image
                    print(f"  Fallback to OCR for page {i+1} in {os.path.basename(pdf_path)}")
                    # Increase resolution slightly for better OCR results
                    pil_image = page.to_image(resolution=150).original
                    ocr_text = pytesseract.image_to_string(pil_image)
                    extracted_text += ocr_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        
    return extracted_text.strip()


def extract_excel(file_path):
    """
    Reads .xlsx or .csv files and returns both a raw text representation (for embedding)
    and the structured DataFrame (for direct field extraction).
    """
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Clean up dataframe
        # Drop columns that are completely empty
        df = df.dropna(axis=1, how='all')
        # Fill remaining NaN values with empty string
        df = df.fillna('')
        # Rename columns starting with 'Unnamed' to empty string
        df.columns = [col if not str(col).startswith('Unnamed') else '' for col in df.columns]
        
        raw_text = df.to_string(index=False)
        return raw_text, df
    except Exception as e:
        print(f"Error extracting tabular data from {file_path}: {e}")
        return "", None


if __name__ == "__main__":
    import json
    
    # Get the absolute path to the /data and /outputs directories relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    outputs_dir = os.path.join(base_dir, "outputs")
    
    # Ensure outputs directory exists
    os.makedirs(outputs_dir, exist_ok=True)
    
    output_data = []
    
    print(f"Looking for files in: {data_dir}\n")
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            
            if filename.lower().endswith('.pdf'):
                print(f"Processing PDF: {filename}")
                text = extract_text(file_path)
                print(f"  -> Extracted text length: {len(text)} characters\n")
                if text:
                    output_data.append({"filename": filename, "type": "pdf", "text": text})
                
            elif filename.lower().endswith('.csv') or filename.lower().endswith('.xlsx'):
                print(f"Processing Data File: {filename}")
                raw_text, df = extract_excel(file_path)
                if df is not None:
                    print(f"  -> DataFrame shape: {df.shape}")
                    print(f"  -> Raw text representation length: {len(raw_text)} characters\n")
                    output_data.append({"filename": filename, "type": "tabular", "text": raw_text})
        
        # Save to JSON
        json_path = os.path.join(outputs_dir, "extracted_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        print(f"Saved extracted data to {json_path}")
            
    else:
        print(f"Warning: /data directory not found at {data_dir}")
