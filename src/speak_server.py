#!/usr/bin/env python3
"""
Simple HTTP server on Pi to receive text and speak it via Piper TTS

Optional component for remote TTS playback.
Can be used by other agents/services to speak on the Pi.

Usage:
    python speak_server.py

API:
    POST /speak {"text": "Hello world"}
    GET /health
"""
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

PIPER_MODEL = "/home/tom/voices/en_US-lessac-medium.onnx"
PIPER_BIN = "/home/tom/voice-assistant/bin/piper"

@app.route('/speak', methods=['POST'])
def speak():
    """Receive text and speak it"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        # Generate WAV file via Piper
        wav_path = f"/tmp/speak_{os.getpid()}.wav"
        piper_cmd = f'echo "{text}" | {PIPER_BIN} --model {PIPER_MODEL} --output_file {wav_path}'
        subprocess.run(piper_cmd, shell=True, check=True)
        
        # Play via paplay
        subprocess.run(["paplay", wav_path], check=True)
        
        # Clean up
        os.remove(wav_path)
        
        return jsonify({"status": "spoken", "text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"service": "pi-speaker", "status": "healthy"})

if __name__ == '__main__':
    print("🔊 Pi speaker service starting on port 8766...")
    app.run(host='0.0.0.0', port=8766, threaded=True)
