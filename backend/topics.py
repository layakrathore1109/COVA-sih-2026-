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
    
    # Iterate through each topic (excluding outliers which is typically -1)
    for topic_id in topic_info['Topic']:
        if topic_id == -1:
            continue
        
        # Get the top keywords for this topic
        keywords = topic_model.get_topic(topic_id)
        if keywords:
            # Extract just the word part from the (word, probability) tuple
            word_list = [word for word, prob in keywords]
            topic_name = topic_info[topic_info['Topic'] == topic_id]['Name'].values[0]
            topics_list.append({
                "topic_id": topic_id,
                "name": topic_name,
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
