"""
Voice Assistant - CLI Version
Wake word detection → transcription → Telegram → TTS response

Based on March 20, 2026 architecture:
- Wake word detection (openwakeword)
- Voice activity detection (webrtcvad)  
- Transcription (faster-whisper)
- Telegram integration for bidirectional communication
- Webhook server for streaming responses
- TTS playback (Piper)
"""

import os
import sys
import time
import json
import wave
import struct
import pyaudio
import webrtcvad
import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel
import requests
from flask import Flask, request, jsonify
import threading
import subprocess

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.json"
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Audio parameters
SAMPLE_RATE = 16000
CHUNK_SIZE = 512
CHANNELS = 1
VAD_FRAME_MS = 30  # webrtcvad requires 10, 20, or 30ms frames
VAD_FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)

# Initialize components
print("Loading wake word model...")
wake_word_model = WakeWordModel(
    wakeword_models=config['wake_words'],
    inference_framework='onnx'
)

print("Loading Whisper model...")
whisper_model = WhisperModel(
    config['whisper_model'],
    device=config['whisper_device'],
    compute_type=config['whisper_compute_type']
)

print("Initializing VAD...")
vad = webrtcvad.Vad(config['vad_aggressiveness'])

# Audio interface
audio = pyaudio.PyAudio()

# Webhook server for receiving responses
app = Flask(__name__)
response_queue = []

@app.route('/response', methods=['POST'])
def receive_response():
    """Receive streaming response chunks from Mira"""
    data = request.get_json()
    sentence = data.get('sentence', '')
    is_final = data.get('final', False)
    
    if sentence:
        print(f"[Response] {sentence}")
        response_queue.append(sentence)
        speak(sentence)
    
    return jsonify({"status": "ok"})

def start_webhook_server():
    """Start webhook server in background thread"""
    app.run(
        host=config['webhook_host'],
        port=config['webhook_port'],
        debug=False,
        use_reloader=False
    )

def speak(text):
    """Convert text to speech using Piper"""
    try:
        # Use Piper TTS
        cmd = [
            'piper',
            '--model', config['piper_model'],
            '--output-raw'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        audio_data, _ = process.communicate(input=text.encode('utf-8'))
        
        # Play audio
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=22050,  # Piper default
            output=True
        )
        stream.write(audio_data)
        stream.stop_stream()
        stream.close()
        
    except Exception as e:
        print(f"[TTS Error] {e}")

def record_audio(duration_ms=5000):
    """Record audio with VAD-based silence detection"""
    frames = []
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=VAD_FRAME_SIZE
    )
    
    print("[Recording] Speak now...")
    silence_frames = 0
    max_silence_frames = int(config['silence_duration_ms'] / VAD_FRAME_MS)
    
    while True:
        frame = stream.read(VAD_FRAME_SIZE, exception_on_overflow=False)
        frames.append(frame)
        
        # Check for speech
        is_speech = vad.is_speech(frame, SAMPLE_RATE)
        
        if not is_speech:
            silence_frames += 1
            if silence_frames > max_silence_frames:
                print("[Recording] Silence detected, stopping...")
                break
        else:
            silence_frames = 0
    
    stream.stop_stream()
    stream.close()
    
    return b''.join(frames)

def transcribe_audio(audio_data):
    """Transcribe audio using Whisper"""
    # Save to temp WAV file
    temp_path = "/tmp/voice_input.wav"
    with wave.open(temp_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data)
    
    # Transcribe
    segments, info = whisper_model.transcribe(temp_path, language="en")
    text = " ".join([segment.text for segment in segments])
    
    os.remove(temp_path)
    return text.strip()

def send_to_mira(text):
    """Send transcribed text to Mira via Telegram with callback URL"""
    # Get callback URL (webhook endpoint)
    callback_url = f"http://raspberrypi:{config['webhook_port']}/response"
    
    # Format message with voice indicator and callback
    message = f"🎤 Voice [{callback_url}]: {text}"
    
    # Send via Telegram Bot API
    url = f"https://api.telegram.org/bot{config['telegram_token']}/sendMessage"
    payload = {
        "chat_id": config['openclaw_chat_id'],
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"[Sent] {text}")
        else:
            print(f"[Error] Failed to send message: {response.text}")
    except Exception as e:
        print(f"[Error] {e}")

def main():
    """Main voice assistant loop"""
    print("\n" + "="*60)
    print("Voice Assistant Started")
    print("Wake words:", ", ".join(config['wake_words']))
    print("Webhook:", f"http://{config['webhook_host']}:{config['webhook_port']}/response")
    print("="*60 + "\n")
    
    # Start webhook server in background
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    # Open audio stream for wake word detection
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    print("[Listening] Waiting for wake word...")
    
    try:
        while True:
            # Read audio chunk
            chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_array = np.frombuffer(chunk, dtype=np.int16)
            
            # Feed to wake word detector
            prediction = wake_word_model.predict(audio_array)
            
            # Check if any wake word detected
            for wake_word in config['wake_words']:
                if prediction.get(wake_word, 0) > 0.5:
                    print(f"\n[Wake Word] Detected: {wake_word}")
                    
                    # Record user speech
                    audio_data = record_audio()
                    
                    # Transcribe
                    print("[Transcribing]...")
                    text = transcribe_audio(audio_data)
                    
                    if text:
                        print(f"[You said] {text}")
                        
                        # Send to Mira
                        send_to_mira(text)
                        
                        # Mira will stream responses back to /response endpoint
                        # which will automatically speak them
                    else:
                        print("[Error] No speech detected")
                    
                    print("\n[Listening] Waiting for wake word...")
                    break
                    
    except KeyboardInterrupt:
        print("\n[Stopped] Voice assistant shutting down...")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()
