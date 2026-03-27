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

# LLM configuration
OLLAMA_ENDPOINT = "http://citadel:11434/v1/chat/completions"
DEFAULT_MODEL = "qwen2.5:14b-instruct"

def generate_voice_response(question):
    """
    Generate concise, voice-optimized responses
    Yields sentences as they're generated
    """
    
    # STRICT prompt for ultra-short voice responses
    system_prompt = """You are Mira, Tom's AI assistant speaking via voice.

CRITICAL RULES:
- ONE sentence only, never more
- Direct answer, no preamble or questions
- No "let me", "I can", "would you like" - just state the answer
- Max 15 words

Examples:
Q: What's the weather?
A: It's 72 degrees and sunny.

Q: What time is it?
A: It's 4:47 PM.

Q: How are you?
A: I'm doing well, thanks."""

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
            "temperature": 0.5,
            "max_tokens": 50  # Force brevity
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
    sentence_count = 0
    
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
                
                # Yield complete sentences (but only first one)
                while any(punct in buffer for punct in ['. ', '! ', '? ', '\n']) and sentence_count == 0:
                    for punct in ['. ', '! ', '? ', '\n']:
                        if punct in buffer:
                            idx = buffer.index(punct)
                            sentence = buffer[:idx+1].strip()
                            buffer = buffer[idx+1:].strip()
                            
                            if sentence:
                                sentence_count += 1
                                yield sentence
                                return  # Stop after first sentence
                            break
        
        except json.JSONDecodeError:
            continue
    
    # Yield remaining buffer (but only if no sentence sent yet)
    if buffer.strip() and sentence_count == 0:
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
