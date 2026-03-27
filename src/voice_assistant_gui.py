"""
Voice Assistant GUI with Blue Orb Visualization
Main application window with settings dialog
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import pyaudio
from pathlib import Path
from orb_visualizer import OrbVisualizer


class SettingsDialog(tk.Toplevel):
    """Settings dialog for audio device configuration"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("Voice Assistant Settings")
        self.geometry("500x600")
        self.configure(bg='#1a1a1a')
        self.resizable(False, False)
        
        self.config = config
        self.result = None
        
        # Get available audio devices
        self.audio = pyaudio.PyAudio()
        self.input_devices = self._get_input_devices()
        self.output_devices = self._get_output_devices()
        
        self._create_widgets()
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
    def _get_input_devices(self):
        """Get list of available input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels']
                })
        return devices
    
    def _get_output_devices(self):
        """Get list of available output devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxOutputChannels']
                })
        return devices
    
    def _create_widgets(self):
        """Create settings UI"""
        # Title
        title = tk.Label(self, text="⚙️ Voice Assistant Settings", 
                        font=('Arial', 16, 'bold'), bg='#1a1a1a', fg='#00BFFF')
        title.pack(pady=20)
        
        # Main frame
        main_frame = tk.Frame(self, bg='#1a1a1a')
        main_frame.pack(padx=20, fill=tk.BOTH, expand=True)
        
        # Audio Input Section
        input_label = tk.Label(main_frame, text="🎤 Audio Input Device", 
                              font=('Arial', 12, 'bold'), bg='#1a1a1a', fg='white')
        input_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.input_var = tk.StringVar(value=self.config.get('audio_input_device', 'default'))
        input_menu = ttk.Combobox(main_frame, textvariable=self.input_var, 
                                  values=[d['name'] for d in self.input_devices],
                                  state='readonly', width=50)
        input_menu.pack(pady=5)
        
        # Audio Output Section
        output_label = tk.Label(main_frame, text="🔊 Audio Output Device", 
                               font=('Arial', 12, 'bold'), bg='#1a1a1a', fg='white')
        output_label.pack(anchor=tk.W, pady=(20, 5))
        
        self.output_var = tk.StringVar(value=self.config.get('audio_output_device', 'default'))
        output_menu = ttk.Combobox(main_frame, textvariable=self.output_var,
                                   values=[d['name'] for d in self.output_devices],
                                   state='readonly', width=50)
        output_menu.pack(pady=5)
        
        # Volume Controls
        volume_label = tk.Label(main_frame, text="🎚️ Volume Controls", 
                               font=('Arial', 12, 'bold'), bg='#1a1a1a', fg='white')
        volume_label.pack(anchor=tk.W, pady=(20, 5))
        
        # Input volume
        tk.Label(main_frame, text="Input Gain:", bg='#1a1a1a', fg='white').pack(anchor=tk.W, pady=(5, 0))
        self.input_volume = tk.Scale(main_frame, from_=0, to=2.0, resolution=0.1,
                                     orient=tk.HORIZONTAL, bg='#2a2a2a', fg='white',
                                     highlightthickness=0, length=400)
        self.input_volume.set(self.config.get('volume_input', 1.0))
        self.input_volume.pack(pady=5)
        
        # Output volume
        tk.Label(main_frame, text="Output Volume:", bg='#1a1a1a', fg='white').pack(anchor=tk.W, pady=(5, 0))
        self.output_volume = tk.Scale(main_frame, from_=0, to=2.0, resolution=0.1,
                                      orient=tk.HORIZONTAL, bg='#2a2a2a', fg='white',
                                      highlightthickness=0, length=400)
        self.output_volume.set(self.config.get('volume_output', 1.0))
        self.output_volume.pack(pady=5)
        
        # Wake Words
        wake_label = tk.Label(main_frame, text="💬 Wake Words", 
                             font=('Arial', 12, 'bold'), bg='#1a1a1a', fg='white')
        wake_label.pack(anchor=tk.W, pady=(20, 5))
        
        wake_frame = tk.Frame(main_frame, bg='#1a1a1a')
        wake_frame.pack(anchor=tk.W, pady=5)
        
        wake_words = self.config.get('wake_words', ["alexa", "hey jarvis"])
        self.wake_vars = {}
        for word in ["alexa", "hey jarvis", "hey mycroft", "hey rhasspy"]:
            var = tk.BooleanVar(value=word in wake_words)
            self.wake_vars[word] = var
            tk.Checkbutton(wake_frame, text=word.title(), variable=var,
                          bg='#1a1a1a', fg='white', selectcolor='#2a2a2a',
                          activebackground='#1a1a1a', activeforeground='#00BFFF').pack(anchor=tk.W)
        
        # Test Buttons
        test_frame = tk.Frame(main_frame, bg='#1a1a1a')
        test_frame.pack(pady=20)
        
        tk.Button(test_frame, text="🔊 Test Speaker", command=self._test_speaker,
                 bg='#00BFFF', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        tk.Button(test_frame, text="🎤 Test Microphone", command=self._test_microphone,
                 bg='#1E90FF', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        # Bottom buttons
        button_frame = tk.Frame(self, bg='#1a1a1a')
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        tk.Button(button_frame, text="✓ Save", command=self._save,
                 bg='#28a745', fg='white', padx=30, pady=10, font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="✗ Cancel", command=self._cancel,
                 bg='#dc3545', fg='white', padx=30, pady=10, font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=10)
    
    def _test_speaker(self):
        """Play test sound through selected output device"""
        messagebox.showinfo("Test Speaker", "Test sound would play here\n(Feature to be implemented)")
    
    def _test_microphone(self):
        """Record brief audio from selected input device"""
        messagebox.showinfo("Test Microphone", "Microphone test would run here\n(Feature to be implemented)")
    
    def _save(self):
        """Save settings and close"""
        self.result = {
            'audio_input_device': self.input_var.get(),
            'audio_output_device': self.output_var.get(),
            'volume_input': self.input_volume.get(),
            'volume_output': self.output_volume.get(),
            'wake_words': [word for word, var in self.wake_vars.items() if var.get()]
        }
        self.audio.terminate()
        self.destroy()
    
    def _cancel(self):
        """Cancel and close"""
        self.audio.terminate()
        self.destroy()


class VoiceAssistantGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant")
        self.root.geometry("600x700")
        self.root.configure(bg='#000000')
        self.root.resizable(False, False)
        
        # Load config
        self.config_path = Path(__file__).parent.parent / "config" / "settings.json"
        self.config = self._load_config()
        
        # State
        self.is_running = False
        self.current_state = "idle"
        
        self._create_widgets()
        
        # Start orb animation
        self.orb.start()
        
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Load from example template
            example_path = self.config_path.parent / "settings.json.example"
            if example_path.exists():
                with open(example_path, 'r') as f:
                    config = json.load(f)
                    # Save as actual config
                    self._save_config(config)
                    return config
        return {}
    
    def _save_config(self, config):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _create_widgets(self):
        """Create main UI"""
        # Top bar with settings button
        top_bar = tk.Frame(self.root, bg='#000000', height=50)
        top_bar.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_bar, text="🎤 Voice Assistant", font=('Arial', 18, 'bold'),
                bg='#000000', fg='#00BFFF').pack(side=tk.LEFT)
        
        tk.Button(top_bar, text="⚙️", command=self._open_settings,
                 bg='#1a1a1a', fg='white', font=('Arial', 16),
                 padx=10, pady=5, relief=tk.FLAT).pack(side=tk.RIGHT)
        
        # Orb visualization
        self.orb = OrbVisualizer(self.root, size=450)
        self.orb.pack(pady=20)
        
        # Status text
        self.status_label = tk.Label(self.root, text="Idle", 
                                     font=('Arial', 16), bg='#000000', fg='#87CEEB')
        self.status_label.pack(pady=10)
        
        # Start/Stop button
        self.start_button = tk.Button(self.root, text="▶ Start Listening",
                                      command=self._toggle_listening,
                                      bg='#28a745', fg='white',
                                      font=('Arial', 14, 'bold'),
                                      padx=40, pady=15)
        self.start_button.pack(pady=20)
        
    def _toggle_listening(self):
        """Start/stop voice assistant"""
        if not self.is_running:
            self._start()
        else:
            self._stop()
    
    def _start(self):
        """Start voice assistant"""
        self.is_running = True
        self.start_button.config(text="⏸ Stop Listening", bg='#dc3545')
        self.set_state("listening")
        # TODO: Start actual voice assistant backend
        
    def _stop(self):
        """Stop voice assistant"""
        self.is_running = False
        self.start_button.config(text="▶ Start Listening", bg='#28a745')
        self.set_state("idle")
        # TODO: Stop voice assistant backend
        
    def set_state(self, state: str):
        """Update UI state"""
        self.current_state = state
        self.orb.set_state(state)
        
        status_text = {
            "idle": "Idle",
            "listening": "Listening...",
            "processing": "Thinking...",
            "speaking": "Speaking..."
        }.get(state, "Unknown")
        
        self.status_label.config(text=status_text)
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.root, self.config)
        self.root.wait_window(dialog)
        
        if dialog.result:
            # Update config
            self.config.update(dialog.result)
            self._save_config(self.config)
            messagebox.showinfo("Settings Saved", 
                              "Settings have been saved.\nRestart to apply changes.")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = VoiceAssistantGUI()
    app.run()
