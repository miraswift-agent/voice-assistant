#!/usr/bin/env python3
"""
Voice Server for mirapc - Handles voice requests from Pi

Architecture:
- Receives HTTP POST from Pi with voice questions
- Generates responses via Ollama (qwen2.5:14b)
- Streams sentence chunks back to Pi in real-time
- Optimized for voice: concise, natural language

Endpoint: http://mirapc:8765/voice/ask
"""

from flask import Flask, request, Response, jsonify
import json
import time
import subprocess
import os

app = Flask(__name__)

# Server configuration
VOICE_PORT = 8765

# Voice configuration (NOT USED - Pi handles TTS)
# These are for reference/documentation
PIPER_MODEL = "/home/tom/voices/en_US-ljspeech-high.onnx"
PIPER_BIN = "/home/tom/voice-assistant/bin/piper"

# LLM configuration
OLLAMA_ENDPOINT = "http://citadel:11434/v1/chat/completions"
DEFAULT_MODEL = "qwen2.5:14b-instruct"

def generate_voice_response(question):
    """
    Generate concise, voice-optimized responses
    Yields sentences as they're generated
    """
    
    # Prompt for voice-optimized responses
    system_prompt = """You are Mira, Tom's AI assistant. You're speaking to him via voice.

Keep responses:
- Ultra concise (1-3 sentences max)
- Natural spoken language
- No markdown, no formatting
- Direct answers, no preamble

Example:
Q: What's the weather?
A: It's currently 70 degrees and sunny. Perfect day outside.

Q: What time is it?
A: It's 2:15 PM."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    # Call Ollama via curl for streaming
    curl_cmd = [
        "curl", "-s", "-N", OLLAMA_ENDPOINT,
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": DEFAULT_MODEL,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 200  # Keep responses short
        })
    ]
    
    process = subprocess.Popen(
        curl_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    buffer = ""
    
    for line in process.stdout:
        if not line.strip() or line.strip() == "data: [DONE]":
            continue
        
        try:
            if line.startswith("data: "):
                line = line[6:]
            
            data = json.loads(line)
            delta = data.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content", "")
            
            if content:
                buffer += content
                
                # Yield complete sentences
                while any(punct in buffer for punct in ['. ', '! ', '? ', '\n']):
                    for punct in ['. ', '! ', '? ', '\n']:
                        if punct in buffer:
                            idx = buffer.index(punct)
                            sentence = buffer[:idx+1].strip()
                            buffer = buffer[idx+1:].strip()
                            
                            if sentence:
                                yield sentence
                            break
        
        except json.JSONDecodeError:
            continue
    
    # Yield remaining buffer
    if buffer.strip():
        yield buffer.strip()


@app.route('/voice/ask', methods=['POST'])
def voice_ask():
    """
    Accept voice question, stream response chunks
    
    Request:
        POST /voice/ask
        {"question": "What's the weather?"}
    
    Response:
        Stream of newline-delimited JSON:
        {"text": "It's currently 70 degrees and sunny."}
        {"text": "Perfect day outside."}
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        print(f"\n🎤 Voice question: {question}")
        
        def generate():
            for chunk in generate_voice_response(question):
                print(f"   → {chunk}")
                yield json.dumps({"text": chunk}) + "\n"
        
        return Response(generate(), mimetype='application/x-ndjson')
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "healthy", "service": "voice-server"})


if __name__ == '__main__':
    print(f"🎤 Voice server starting on port {VOICE_PORT}...")
    print(f"   Model: {DEFAULT_MODEL}")
    print(f"   Endpoint: {OLLAMA_ENDPOINT}")
    print()
    app.run(host='0.0.0.0', port=VOICE_PORT, threaded=True)
