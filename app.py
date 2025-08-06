from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse, Start, Stream
from twilio.rest import Client
import asyncio
import websockets
import threading
import tempfile
import os
import uuid

from tts import text_to_speech
from whisper_mic import transcribe_stream

app = Flask(__name__)

TWILIO_SID = "YOUR_TWILIO_SID"
TWILIO_AUTH = "YOUR_TWILIO_AUTH_TOKEN"
client = Client(TWILIO_SID, TWILIO_AUTH)

CALL_SID = None
WS_URL = "wss://your-app-name.onrender.com/ws"
REPLIES = {}

@app.route("/twilio-call", methods=["POST"])
def twilio_call():
    global CALL_SID
    CALL_SID = request.form.get("CallSid")
    print(f"📞 New call received. SID: {CALL_SID}")

    response = VoiceResponse()
    start = Start()
    start.stream(url=WS_URL)
    response.append(start)

    response.say("Hey there, this is Chris from ProRisk Insurance. How can I help you today?",
        voice="Polly.Matthew", language="en-US", barge_in=True)

    return str(response)

@app.route("/call-status", methods=["POST"])
def call_status():
    call_sid = request.form.get("CallSid")
    status = request.form.get("CallStatus")
    print(f"📟 Call status update: {call_sid} - {status}")
    return "OK", 200

async def handle_websocket(websocket, path):
    print("🔌 WebSocket connected")
    audio_buffer = b""
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                audio_buffer += message
                if len(audio_buffer) > 16000 * 2:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio_buffer)
                        temp_path = f.name

                    text = transcribe_stream(temp_path)
                    print("📝 Transcribed:", text)
                    os.remove(temp_path)
                    audio_buffer = b""

                    if not text.strip():
                        continue

                    if "quote" in text.lower():
                        reply = "Sure! I can get a quote started. What’s your zip code?"
                    elif "certificate" in text.lower():
                        reply = "Okay, do you need your certificate emailed or faxed?"
                    else:
                        reply = "Can you please clarify that?"

                    filename = f"{uuid.uuid4()}.mp3"
                    text_to_speech(reply, filename)
                    REPLIES[CALL_SID] = filename

                    client.calls(CALL_SID).redirect(
                        url=f"{request.url_root}twiml-response?call_sid={CALL_SID}",
                        method="GET"
                    )
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket closed: {e}")

@app.route("/twiml-response", methods=["GET"])
def twiml_response():
    call_sid = request.args.get("call_sid")
    response = VoiceResponse()
    start = Start()
    start.stream(url=WS_URL)
    response.append(start)
    response.play(f"{request.url_root}audio?call_sid={call_sid}", barge_in=True)
    return str(response)

@app.route("/audio", methods=["GET"])
def serve_audio():
    call_sid = request.args.get("call_sid")
    path = REPLIES.get(call_sid)
    if path and os.path.exists(path):
        return send_file(path, mimetype="audio/mpeg")
    return "Audio not ready", 404

def start_websocket():
    async def run_ws():
        async with websockets.serve(handle_websocket, "0.0.0.0", 10000):
            print("🟢 WebSocket running on ws://0.0.0.0:10000")
            await asyncio.Future()
    asyncio.run(run_ws())

def start_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    threading.Thread(target=start_websocket).start()