import requests

def translate_to_english(text):
    """
    Translates input text to English using Sarvam AI's API.
    """

    # 1. Replace with your actual API key from the Sarvam dashboard
    api_key = "PASTE_YOUR_API_KEY_HERE"

    # API Endpoint
    url = "https://api.sarvam.ai/translate"

    # Request Payload
    # You can also use 'ta-IN' for Tamil or 'hi-IN' for Hindi specifically.
    payload = {
        "input": text,
        "source_language_code": "ta-IN", 
        "target_language_code": "en-IN",
        "model": "sarvam-translate:v1"
    }

    # Headers - Sarvam uses 'api-subscription-key' for authentication
    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            # The API returns an object with 'translated_text'
            return result.get('translated_text', "No translation found.")
        else:
            return f"API Error {response.status_code}: {response.text}"

    except requests.exceptions.RequestException as e:
        return f"Connection Error: {str(e)}"

# --- Usage Example ---
if __name__ == "__main__":
    input_text = "எப்படி இருக்கிறீர்கள்?"
    translated = translate_to_english(input_text)

    print(f"Original Text: {input_text}")
    print(f"Translated Text: {translated}")
