import requests

def text_to_speech(text, filename, voice_id="1t1EeRixsJrKbiF1zwM6"):
    api_key = "YOUR_ELEVENLABS_API_KEY"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.9,
            "style": 1.0,
            "use_speaker_boost": True
        }
    }

    response = requests.post(url, headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(f"TTS error: {response.status_code} - {response.text}")