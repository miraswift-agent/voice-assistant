"""
Voice Assistant GUI - Integrated with Working Voice Loop
Connects blue orb visualization to actual voice states
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import queue
import subprocess
import tempfile
import wave
import threading
import requests
import numpy as np
import sounddevice as sd
import webrtcvad
from pathlib import Path
import json
from faster_whisper import WhisperModel
from openwakeword.model import Model
from orb_visualizer import OrbVisualizer
from settings_dialog import SettingsDialog

# Configuration
VOICE_SERVER = "http://mirapc:8765/voice/ask"
PIPER_MODEL = "/home/tom/voices/en_US-lessac-medium.onnx"

INPUT_RATE = 16000
BLOCK_MS = 30
BLOCK_SIZE = int(INPUT_RATE * BLOCK_MS / 1000)
WAKE_THRESHOLD = 0.5
MAX_RECORD_SECONDS = 12
SILENCE_SECONDS = 1.5

def load_device_config():
    """Load saved audio device configuration"""
    config_path = Path.home() / 'voice-assistant' / 'config' / 'settings.json'
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('input_device'), config.get('output_device')
    except:
        pass
    return None, None


class VoiceAssistantGUI:
    """Main GUI application with integrated voice loop"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant")
        self.root.geometry("600x750")
        self.root.configure(bg='#000000')
        self.root.resizable(False, False)
        
        # Voice loop state
        self.is_running = False
        self.audio_q = queue.Queue()
        self.vad = None
        self.wake_model = None
        self.whisper = None
        self.stream = None
        self.voice_thread = None
        
        # Audio device configuration
        self.input_device = None
        self.output_device = None
        self._load_device_config()
        
        self._create_widgets()
        
        # Start orb animation
        self.orb.start()
        
    def _create_widgets(self):
        """Create main UI"""
        # Top bar
        top_bar = tk.Frame(self.root, bg='#000000', height=50)
        top_bar.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_bar, text="🎤 Voice Assistant", font=('Arial', 18, 'bold'),
                bg='#000000', fg='#00BFFF').pack(side=tk.LEFT)
        
        # Settings button
        tk.Button(top_bar, text="⚙️", command=self._open_settings,
                 bg='#1a1a1a', fg='white', font=('Arial', 16),
                 padx=10, pady=5, relief=tk.FLAT).pack(side=tk.RIGHT)
        
        # Orb visualization
        self.orb = OrbVisualizer(self.root, size=350)
        self.orb.pack(pady=5)
        
        # Status text
        self.status_label = tk.Label(self.root, text="Ready to start", 
                                     font=('Arial', 16), bg='#000000', fg='#87CEEB')
        self.status_label.pack(pady=10)
        
        # Start/Stop button
        self.start_button = tk.Button(self.root, text="▶ Start Listening",
                                      command=self._toggle_listening,
                                      bg='#28a745', fg='white',
                                      font=('Arial', 14, 'bold'),
                                      padx=40, pady=15)
        self.start_button.pack(pady=10)
        
    def _load_device_config(self):
        """Load device configuration from file"""
        self.input_device, self.output_device = load_device_config()
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.root)
        self.root.wait_window(dialog)
        
    def _toggle_listening(self):
        """Start/stop voice assistant"""
        if not self.is_running:
            self._start()
        else:
            self._stop()
    
    def _start(self):
        """Start voice assistant"""
        try:
            # Initialize voice components
            self.set_status("Loading models...")
            
            self.vad = webrtcvad.Vad(2)
            self.wake_model = Model()
            self.whisper = WhisperModel("tiny", compute_type="int8")
            
            self.is_running = True
            self.start_button.config(text="⏸ Stop Listening", bg='#dc3545')
            
            # Start voice loop in background thread
            self.voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
            self.voice_thread.start()
            
            self.set_status("Listening for wake word...")
            self.set_state("idle")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start:\n{e}")
            self._stop()
    
    def _stop(self):
        """Stop voice assistant"""
        self.is_running = False
        self.start_button.config(text="▶ Start Listening", bg='#28a745')
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.set_state("idle")
        self.set_status("Stopped")
    
    def _audio_callback(self, indata, frames, time, status):
        """Audio stream callback"""
        if status:
            print(f"Audio: {status}")
        self.audio_q.put(indata[:, 0].copy())
    
    def _voice_loop(self):
        """Main voice detection loop"""
        # Open audio stream
        self.stream = sd.InputStream(
            device=self.input_device,  # Use configured device
            samplerate=INPUT_RATE,
            channels=1,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            callback=self._audio_callback,
        )
        self.stream.start()
        
        while self.is_running:
            try:
                chunk = self.audio_q.get(timeout=0.1)
                pcm = self._pcm16(chunk)
                
                # Update orb with audio levels (for visualization)
                level = float(np.abs(chunk).mean())
                self.orb.update_audio_levels([level])
                
                # Check for wake word
                predictions = self.wake_model.predict(pcm)
                
                if any(score > WAKE_THRESHOLD for score in predictions.values()):
                    self._handle_wake_word()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Voice loop error: {e}")
    
    def _handle_wake_word(self):
        """Handle wake word detection"""
        # Clear queue
        while not self.audio_q.empty():
            self.audio_q.get()
        
        self.set_status("Wake word detected! Speak now...")
        self.set_state("listening")
        
        # Record audio
        audio = self._record_until_silence()
        
        # Transcribe
        self.set_status("Transcribing...")
        self.set_state("processing")
        
        text = self._transcribe(audio)
        
        if not text:
            self.set_status("(no speech detected)")
            self.set_state("idle")
            return
        
        self.set_status(f"You: {text}")
        
        # Get response
        self._ask_mira(text)
        
        # Back to listening
        self.set_status("Listening for wake word...")
        self.set_state("idle")
    
    def _record_until_silence(self):
        """Record audio until silence detected"""
        frames = []
        silence_blocks = int((1000 * SILENCE_SECONDS) / BLOCK_MS)
        silent = 0
        max_blocks = int((1000 * MAX_RECORD_SECONDS) / BLOCK_MS)
        
        for _ in range(max_blocks):
            if not self.is_running:
                break
                
            try:
                chunk = self.audio_q.get(timeout=0.5)
                frames.append(chunk)
                
                # Update visualization
                level = float(np.abs(chunk).mean())
                self.orb.update_audio_levels([level * 5])  # Amplify for visibility
                
                is_speech = self.vad.is_speech(self._pcm16(chunk).tobytes(), INPUT_RATE)
                
                if is_speech:
                    silent = 0
                else:
                    silent += 1
                    if silent >= silence_blocks and len(frames) > 5:
                        break
            except queue.Empty:
                break
        
        return np.concatenate(frames) if frames else np.array([])
    
    def _transcribe(self, audio):
        """Transcribe audio with Whisper"""
        if len(audio) == 0:
            return ""
        
        # Save to temp WAV
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        
        self._save_wav(wav_path, audio, INPUT_RATE)
        
        try:
            segments, _ = self.whisper.transcribe(wav_path)
            text = " ".join([s.text for s in segments]).strip()
        finally:
            os.unlink(wav_path)
        
        return text
    
    def _ask_mira(self, question):
        """Send question to Mira, get streaming response"""
        self.set_status("Asking Mira...")
        self.set_state("processing")
        
        try:
            response = requests.post(
                VOICE_SERVER,
                json={"question": question},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            self.set_state("speaking")
            
            for line in response.iter_lines():
                if line and self.is_running:
                    data = line.decode('utf-8')
                    try:
                        chunk = eval(data)
                        text = chunk.get("text", "")
                        if text:
                            self.set_status(f"Mira: {text}")
                            self._speak(text)
                    except:
                        pass
        
        except Exception as e:
            print(f"Error asking Mira: {e}")
            self.set_status(f"Error: {e}")
            self._speak("Sorry, I couldn't reach the voice server.")
        
        finally:
            # Clear audio queue to prevent feedback loop
            import time
            time.sleep(0.5)  # Wait for TTS to finish
            while not self.audio_q.empty():
                try:
                    self.audio_q.get_nowait()
                except:
                    break
    
    def _speak(self, text):
        """Speak text with Piper TTS"""
        # Simulate waveform during speech
        for i in range(10):
            if self.is_running:
                levels = [np.random.random() * 0.8 for _ in range(32)]
                self.orb.update_audio_levels(levels)
        
        # Generate and play TTS
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
    
    def _pcm16(self, samples):
        """Convert float32 to int16 PCM"""
        return (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    
    def _save_wav(self, path, audio, rate):
        """Save audio to WAV file"""
        pcm = self._pcm16(audio)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(pcm.tobytes())
    
    def set_state(self, state: str):
        """Update orb state"""
        self.orb.set_state(state)
    
    def set_status(self, text: str):
        """Update status label"""
        self.status_label.config(text=text)
        self.root.update()
    
    def run(self):
        """Start the GUI application"""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        """Clean shutdown"""
        self._stop()
        self.root.destroy()


if __name__ == "__main__":
    app = VoiceAssistantGUI()
    app.run()
