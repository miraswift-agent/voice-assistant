"""
Settings dialog with device selection
"""
import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import json
from pathlib import Path

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("500x400")
        self.configure(bg='#1a1a1a')
        self.resizable(False, False)
        
        self.parent_app = parent
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        # Get all devices
        self.devices = sd.query_devices()
        self.input_devices = [(i, d['name']) for i, d in enumerate(self.devices) 
                              if d['max_input_channels'] > 0]
        self.output_devices = [(i, d['name']) for i, d in enumerate(self.devices) 
                               if d['max_output_channels'] > 0]
        
        # Load saved settings
        self.config_path = Path.home() / "voice-assistant" / "config" / "settings.json"
        self.load_settings()
        
        self._create_widgets()
        
    def load_settings(self):
        """Load saved device settings"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.saved_input = config.get('input_device')
                    self.saved_output = config.get('output_device')
            else:
                self.saved_input = sd.default.device[0]
                self.saved_output = sd.default.device[1]
        except:
            self.saved_input = sd.default.device[0]
            self.saved_output = sd.default.device[1]
    
    def _create_widgets(self):
        """Create settings UI"""
        # Title
        tk.Label(self, text="⚙️ Audio Settings", font=('Arial', 16, 'bold'),
                bg='#1a1a1a', fg='#00BFFF').pack(pady=20)
        
        # Main frame
        frame = tk.Frame(self, bg='#1a1a1a')
        frame.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Microphone selection
        tk.Label(frame, text="🎤 Microphone:", font=('Arial', 12, 'bold'),
                bg='#1a1a1a', fg='white').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(frame, textvariable=self.mic_var, 
                                      state='readonly', width=40)
        self.mic_combo['values'] = [f"{i}: {name}" for i, name in self.input_devices]
        
        # Set current selection
        for idx, (dev_id, name) in enumerate(self.input_devices):
            if dev_id == self.saved_input:
                self.mic_combo.current(idx)
                break
        
        self.mic_combo.grid(row=1, column=0, pady=(0, 20), sticky=tk.EW)
        
        # Speaker selection
        tk.Label(frame, text="🔊 Speaker:", font=('Arial', 12, 'bold'),
                bg='#1a1a1a', fg='white').grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.speaker_var = tk.StringVar()
        self.speaker_combo = ttk.Combobox(frame, textvariable=self.speaker_var,
                                         state='readonly', width=40)
        self.speaker_combo['values'] = [f"{i}: {name}" for i, name in self.output_devices]
        
        # Set current selection
        for idx, (dev_id, name) in enumerate(self.output_devices):
            if dev_id == self.saved_output:
                self.speaker_combo.current(idx)
                break
        
        self.speaker_combo.grid(row=3, column=0, pady=(0, 20), sticky=tk.EW)
        
        # Wake words info
        tk.Label(frame, text="Wake Words:", font=('Arial', 11, 'bold'),
                bg='#1a1a1a', fg='white').grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        wake_text = tk.Text(frame, height=3, bg='#2a2a2a', fg='white', 
                           font=('Arial', 10), wrap=tk.WORD)
        wake_text.insert('1.0', "• Alexa\n• Hey Jarvis\n• Hey Mycroft\n• Hey Rhasspy")
        wake_text.config(state=tk.DISABLED)
        wake_text.grid(row=5, column=0, sticky=tk.EW)
        
        # Buttons
        btn_frame = tk.Frame(self, bg='#1a1a1a')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Cancel", command=self._cancel,
                 bg='#6c757d', fg='white', font=('Arial', 12),
                 padx=30, pady=10).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="OK", command=self._ok,
                 bg='#28a745', fg='white', font=('Arial', 12, 'bold'),
                 padx=40, pady=10).pack(side=tk.LEFT, padx=10)
    
    def _ok(self):
        """Save settings and close"""
        # Parse selected device IDs
        mic_text = self.mic_var.get()
        speaker_text = self.speaker_var.get()
        
        mic_id = int(mic_text.split(':')[0])
        speaker_id = int(speaker_text.split(':')[0])
        
        # Save to config file
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({
                'input_device': mic_id,
                'output_device': speaker_id
            }, f, indent=2)
        
        self.result = {'input': mic_id, 'output': speaker_id}
        self.destroy()
    
    def _cancel(self):
        """Close without saving"""
        self.result = None
        self.destroy()
