"""
Voice Assistant - Working CLI Version from Pi
Wake word detection → transcription → HTTP voice server → TTS response

Architecture:
- Wake word: openwakeword (Alexa, Hey Jarvis, Hey Mycroft, Hey Rhasspy)
- VAD: webrtcvad for silence detection
- Transcription: faster-whisper (tiny model, int8)
- Communication: HTTP POST to mirapc:8765/voice/ask (streaming response)
- TTS: Piper with paplay
"""

import queue
import subprocess
import tempfile
import wave
import os
import time
import requests
import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel
from openwakeword.model import Model

# Voice server on mirapc
VOICE_SERVER = "http://mirapc:8765/voice/ask"

PIPER_MODEL = "/home/tom/voice-assistant/models/en_US-lessac-medium.onnx"

INPUT_RATE = 16000
TARGET_RATE = 16000
BLOCK_MS = 30
BLOCK_SIZE = int(INPUT_RATE * BLOCK_MS / 1000)

WAKE_THRESHOLD = 0.5
MAX_RECORD_SECONDS = 12
SILENCE_SECONDS = 1.5

audio_q = queue.Queue()
vad = webrtcvad.Vad(2)
wake_model = Model()
whisper = WhisperModel("tiny", compute_type="int8")


def audio_callback(indata, frames, time, status):
    """Audio stream callback"""
    if status:
        print(f"Audio: {status}")
    audio_q.put(indata[:, 0].copy())


def pcm16(samples):
    """Convert float32 audio to int16 PCM"""
    return (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)


def save_wav(path, audio, rate):
    """Save audio array to WAV file"""
    pcm = pcm16(audio)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())


def transcribe(path):
    """Transcribe audio file with Whisper"""
    segments, _ = whisper.transcribe(path)
    return " ".join([s.text for s in segments]).strip()


def speak(text):
    """Convert text to speech with Piper and play"""
    txt_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    
    txt_path = txt_file.name
    wav_path = wav_file.name
    
    txt_file.write(text)
    txt_file.close()
    wav_file.close()
    
    try:
        with open(txt_path, "r") as stdin_f:
            subprocess.run(
                ["piper", "--model", PIPER_MODEL, "--output_file", wav_path],
                stdin=stdin_f,
                check=True,
                capture_output=True
            )
        subprocess.run(["paplay", wav_path], check=True, capture_output=True)
    finally:
        os.unlink(txt_path)
        os.unlink(wav_path)


def record_until_silence():
    """Record audio until silence detected"""
    frames = []
    silence_blocks = int((1000 * SILENCE_SECONDS) / BLOCK_MS)
    silent = 0
    max_blocks = int((1000 * MAX_RECORD_SECONDS) / BLOCK_MS)
    
    for _ in range(max_blocks):
        chunk = audio_q.get()
        frames.append(chunk)
        
        is_speech = vad.is_speech(pcm16(chunk).tobytes(), INPUT_RATE)
        
        if is_speech:
            silent = 0
        else:
            silent += 1
            if silent >= silence_blocks and len(frames) > 5:
                break
    
    return np.concatenate(frames)


def ask_mira(question):
    """Send question to Mira's voice server, receive streaming response"""
    try:
        print("   Asking Mira...")
        
        response = requests.post(
            VOICE_SERVER,
            json={"question": question},
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        
        print("   Receiving response...\n")
        
        for line in response.iter_lines():
            if line:
                data = line.decode('utf-8')
                try:
                    chunk = eval(data)  # Parse JSON-like string
                    text = chunk.get("text", "")
                    if text:
                        print(f"   Mira: {text}")
                        speak(text)
                except:
                    pass
        
        print()
        
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        speak("Sorry, I couldn't reach the voice server.")


def main():
    """Main voice assistant loop"""
    print("🎤 Voice assistant (HTTP MODE)")
    print(f"   Voice server: {VOICE_SERVER}")
    print(f"   Device: {sd.default.device[0]} @ {INPUT_RATE}Hz")
    print("   Say: Alexa / Hey Jarvis / Hey Mycroft / Hey Rhasspy\n")
    
    with sd.InputStream(
        samplerate=INPUT_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK_SIZE,
        callback=audio_callback,
    ):
        while True:
            chunk = audio_q.get()
            pcm = pcm16(chunk)
            predictions = wake_model.predict(pcm)
            
            if not any(score > WAKE_THRESHOLD for score in predictions.values()):
                continue
            
            # Clear queue
            while not audio_q.empty():
                audio_q.get()
            
            print(f"\n🎤 Wake word detected! Listening...")
            
            audio = record_until_silence()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            
            save_wav(wav_path, audio, TARGET_RATE)
            
            print("   Transcribing...")
            text = transcribe(wav_path)
            os.unlink(wav_path)
            
            if not text:
                print("   (no speech)\n")
                continue
            
            print(f"   You: {text}")
            
            ask_mira(text)


if __name__ == "__main__":
    main()
