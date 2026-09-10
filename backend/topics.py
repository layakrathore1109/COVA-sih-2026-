import os
import json
import subprocess
# pyrefly: ignore [missing-import]
from bertopic import BERTopic
# pyrefly: ignore [missing-import]
from wordcloud import WordCloud, STOPWORDS
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
import string

def ensure_extracted_data(data_folder, outputs_folder):
    """
    Helper function to ensure extracted_data.json exists.
    If not, it runs the extraction script.
    """
    json_path = os.path.join(outputs_folder, "extracted_data.json")
    if not os.path.exists(json_path):
        print(f"File {json_path} not found. Running extraction...")
        # Get the path to the extract.py script
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        extract_script = os.path.join(backend_dir, "extract.py")
        subprocess.run(["python", extract_script], check=True)
    return json_path

def generate_topics(data_folder):
    """
    Loads extracted text from outputs/extracted_data.json (or re-extracts if missing).
    Runs BERTopic on the list of document texts and returns a list of topics with top keywords.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs_folder = os.path.join(base_dir, "outputs")
    json_path = ensure_extracted_data(data_folder, outputs_folder)

    # Load the extracted text
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return []

    # Get a list of document texts
    docs = [item.get("text", "") for item in data if item.get("text")]
    
    if not docs:
        print("No document texts found for topic modeling.")
        return []

    print("Running BERTopic on documents...")
    # Initialize and fit BERTopic
    topic_model = BERTopic()
    try:
        topics, probs = topic_model.fit_transform(docs)
    except Exception as e:
        print(f"Error running BERTopic: {e}")
        return []

    # Get topic info and extract keywords
    topic_info = topic_model.get_topic_info()
    topics_list = []
    
    # Step 1: Collect keywords for all valid topics to batch prompt the LLM
    topics_to_name = {}
    for topic_id in topic_info['Topic']:
        if topic_id == -1:
            continue
        keywords = topic_model.get_topic(topic_id)
        if keywords:
            word_list = [word for word, prob in keywords]
            topics_to_name[int(topic_id)] = word_list[:6] # Send top 6 words for context
            
    # Step 2: Use LLM to generate human-readable titles
    generated_names = {}
    if topics_to_name:
        from llm_utils import call_gemini_with_fallback
        prompt = (
            "You are an expert at identifying the core theme from a list of keywords. "
            "Given the following topic IDs and their keywords, generate a short, highly readable, "
            "and professional title (1 to 4 words max) for each topic. "
            "Respond ONLY with a valid JSON object where keys are the topic IDs (as strings) "
            "and values are the generated titles. Do not include markdown code blocks or any other text.\n\n"
            f"Topics:\n{json.dumps(topics_to_name, indent=2)}"
        )
        try:
            print("Calling LLM to generate readable topic headings...")
            llm_response = call_gemini_with_fallback(prompt)
            text = llm_response.get("text", "").strip()
            # Clean up potential markdown formatting
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            generated_names = json.loads(text.strip())
        except Exception as e:
            print(f"Error generating topic titles via LLM: {e}")
            generated_names = {}

    # Step 3: Build the final topics list
    for topic_id in topic_info['Topic']:
        if topic_id == -1:
            continue
        
        keywords = topic_model.get_topic(topic_id)
        if keywords:
            word_list = [word for word, prob in keywords]
            
            # Prefer LLM generated name, fallback to simple filtering
            clean_name = generated_names.get(str(topic_id)) or generated_names.get(int(topic_id))
            if not clean_name:
                meaningful_words = [w for w in word_list if w.lower() not in STOPWORDS and len(w) > 2]
                clean_name = ", ".join(meaningful_words[:3]).title() if meaningful_words else f"Topic {topic_id}"
            
            topics_list.append({
                "topic_id": int(topic_id),
                "name": clean_name,
                "keywords": word_list
            })

    return topics_list

def generate_wordcloud(data_folder):
    """
    Loads extracted text, combines it into one string, and generates a word cloud image.
    Saves the image to outputs/wordcloud.png.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs_folder = os.path.join(base_dir, "outputs")
    json_path = ensure_extracted_data(data_folder, outputs_folder)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return

    # Combine all texts
    combined_text = " ".join([item.get("text", "") for item in data if item.get("text")])
    
    if not combined_text.strip():
        print("No text available to generate word cloud.")
        return

    print("Generating word cloud...")
    try:
        # Create a custom stopword list
        custom_stopwords = set(STOPWORDS)
        custom_stopwords.update(['nan', 'unnamed', 'fig', 'NaN', 'Unnamed', 'Fig'])
        # Exclude single-letter tokens
        custom_stopwords.update(list(string.ascii_lowercase) + list(string.ascii_uppercase))

        # Generate word cloud
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            stopwords=custom_stopwords
        ).generate(combined_text)
        
        # Save image
        output_image_path = os.path.join(outputs_folder, "wordcloud.png")
        # Ensure outputs directory exists
        os.makedirs(outputs_folder, exist_ok=True)
        wordcloud.to_file(output_image_path)
        print(f"Word cloud successfully saved to {output_image_path}")
    except Exception as e:
        print(f"Error generating word cloud: {e}")


if __name__ == "__main__":
    # Test block
    base_dir_test = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_data_folder = os.path.join(base_dir_test, "data")
    
    print("--- Testing Topic Generation ---")
    topics_result = generate_topics(test_data_folder)
    print("\nIdentified Topics:")
    for t in topics_result:
        print(f"Topic {t['topic_id']}: {t['keywords'][:5]}...")
        
    print("\n--- Testing Word Cloud Generation ---")
    generate_wordcloud(test_data_folder)
