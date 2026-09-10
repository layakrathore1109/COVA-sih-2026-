import os
from google import genai
from google.genai import errors

DEFAULT_MODEL_CHAIN = [
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash"
]

def call_gemini_with_fallback(prompt, model_chain=None):
    """
    Tries to generate text using the Gemini API.
    It will iterate through the model_chain using GEMINI_API_KEY.
    If all models fail due to rate-limiting (429) or quota errors,
    it will retry the entire chain using GEMINI_API_KEY_2.
    
    Returns:
        dict: {
            "text": str,
            "model": str,
            "key_used": str (e.g., "GEMINI_API_KEY" or "GEMINI_API_KEY_2")
        }
    """
    if model_chain is None:
        model_chain = DEFAULT_MODEL_CHAIN

    key_1 = os.getenv("GEMINI_API_KEY")
    key_2 = os.getenv("GEMINI_API_KEY_2")

    keys_to_try = []
    if key_1:
        keys_to_try.append(("GEMINI_API_KEY", key_1))
    if key_2:
        keys_to_try.append(("GEMINI_API_KEY_2", key_2))

    if not keys_to_try:
        raise Exception("No Gemini API keys found in environment variables.")

    last_error = None

    for key_name, api_key in keys_to_try:
        client = genai.Client(api_key=api_key)
        
        for model_name in model_chain:
            try:
                interaction = client.interactions.create(
                    model=model_name,
                    input=prompt
                )
                
                print(f"Successfully generated response using {model_name} with {key_name}.")
                return {
                    "text": interaction.output_text,
                    "model": model_name,
                    "key_used": key_name
                }
            except Exception as e:
                # Capture the error
                last_error = e
                error_str = str(e).lower()
                
                # Check for rate limit / quota
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    print(f"Rate limit/Quota error for {model_name} using {key_name}, falling back...")
                    continue
                else:
                    print(f"Non-rate-limit error with {model_name} using {key_name}: {e}")
                    # If it's not a rate limit, don't fallback to the next model for this key.
                    # Just break out to the next key or fail.
                    break
                    
    # If we exhaust all models and all keys
    raise Exception(f"All Gemini models/keys failed. Last error: {last_error}")
