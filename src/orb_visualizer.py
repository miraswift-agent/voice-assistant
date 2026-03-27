"""
Blue orb visualization for voice assistant
Animated states: idle, listening, processing, speaking
"""

import tkinter as tk
import math
import time
from typing import List, Tuple


class OrbVisualizer(tk.Canvas):
    """Animated blue orb that responds to voice assistant states"""
    
    # State constants
    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_PROCESSING = "processing"
    STATE_SPEAKING = "speaking"
    
    # Colors
    COLOR_IDLE = "#1E90FF"      # Dodger blue
    COLOR_ACTIVE = "#00BFFF"    # Deep sky blue
    COLOR_GLOW = "#87CEEB"      # Sky blue
    
    def __init__(self, parent, size=400):
        super().__init__(parent, width=size, height=size, bg='#000000', highlightthickness=0)
        
        self.size = size
        self.center = size // 2
        self.radius = size // 3
        
        self.state = self.STATE_IDLE
        self.animation_frame = 0
        self.audio_levels = []  # For waveform visualization
        self.running = False
        
        # Draw initial orb
        self._draw_orb()
        
    def set_state(self, state: str):
        """Change orb animation state"""
        if state not in [self.STATE_IDLE, self.STATE_LISTENING, 
                         self.STATE_PROCESSING, self.STATE_SPEAKING]:
            raise ValueError(f"Invalid state: {state}")
        self.state = state
        
    def update_audio_levels(self, levels: List[float]):
        """Update audio waveform data (0.0 to 1.0)"""
        self.audio_levels = levels[-50:]  # Keep last 50 samples
        
    def start(self):
        """Start animation loop"""
        self.running = True
        self._animate()
        
    def stop(self):
        """Stop animation loop"""
        self.running = False
        
    def _animate(self):
        """Main animation loop"""
        if not self.running:
            return
            
        self.animation_frame += 1
        self._draw_orb()
        
        # Animation speed based on state
        delay = {
            self.STATE_IDLE: 50,       # Slow breathing
            self.STATE_LISTENING: 30,  # Faster pulse
            self.STATE_PROCESSING: 40, # Spinner speed
            self.STATE_SPEAKING: 30    # Waveform update
        }.get(self.state, 50)
        
        self.after(delay, self._animate)
        
    def _draw_orb(self):
        """Redraw orb based on current state"""
        self.delete("all")
        
        if self.state == self.STATE_IDLE:
            self._draw_idle()
        elif self.state == self.STATE_LISTENING:
            self._draw_listening()
        elif self.state == self.STATE_PROCESSING:
            self._draw_processing()
        elif self.state == self.STATE_SPEAKING:
            self._draw_speaking()
            
    def _draw_idle(self):
        """Gentle breathing pulse"""
        # Calculate pulse (slow sine wave)
        pulse = math.sin(self.animation_frame * 0.05) * 0.15 + 0.85
        r = int(self.radius * pulse)
        
        # Outer glow
        glow_r = r + 20
        self.create_oval(
            self.center - glow_r, self.center - glow_r,
            self.center + glow_r, self.center + glow_r,
            fill="", outline=self.COLOR_GLOW, width=3
        )
        
        # Main orb
        self.create_oval(
            self.center - r, self.center - r,
            self.center + r, self.center + r,
            fill=self.COLOR_IDLE, outline=self.COLOR_ACTIVE, width=2
        )
        
    def _draw_listening(self):
        """Faster pulse + waveform rings"""
        # Faster pulse
        pulse = math.sin(self.animation_frame * 0.15) * 0.2 + 0.9
        r = int(self.radius * pulse)
        
        # Draw waveform rings if we have audio data
        if self.audio_levels:
            for i, level in enumerate(self.audio_levels[-10:]):
                ring_r = r + (i * 5) + int(level * 20)
                alpha = 1.0 - (i / 10)
                color = self._blend_color(self.COLOR_ACTIVE, "#000000", alpha)
                self.create_oval(
                    self.center - ring_r, self.center - ring_r,
                    self.center + ring_r, self.center + ring_r,
                    fill="", outline=color, width=2
                )
        
        # Main orb
        self.create_oval(
            self.center - r, self.center - r,
            self.center + r, self.center + r,
            fill=self.COLOR_ACTIVE, outline=self.COLOR_GLOW, width=3
        )
        
    def _draw_processing(self):
        """Rotating spinner"""
        # Spinner dots around orb
        num_dots = 8
        angle_offset = (self.animation_frame * 5) % 360
        
        for i in range(num_dots):
            angle = (360 / num_dots * i + angle_offset) * math.pi / 180
            x = self.center + math.cos(angle) * (self.radius + 30)
            y = self.center + math.sin(angle) * (self.radius + 30)
            
            # Dots fade as they rotate
            alpha = (math.sin(angle + math.pi) + 1) / 2
            color = self._blend_color(self.COLOR_ACTIVE, "#000000", alpha)
            
            self.create_oval(x-5, y-5, x+5, y+5, fill=color, outline="")
        
        # Static center orb
        self.create_oval(
            self.center - self.radius, self.center - self.radius,
            self.center + self.radius, self.center + self.radius,
            fill=self.COLOR_IDLE, outline=self.COLOR_ACTIVE, width=2
        )
        
    def _draw_speaking(self):
        """Waveform synchronized to speech output"""
        # Draw waveform bars around orb
        num_bars = 32
        
        for i in range(num_bars):
            angle = (360 / num_bars * i) * math.pi / 180
            
            # Get amplitude from audio data or use animation
            if self.audio_levels and i < len(self.audio_levels):
                amplitude = self.audio_levels[i] * 40
            else:
                # Fallback: animated wave pattern
                wave = math.sin(self.animation_frame * 0.1 + i * 0.3)
                amplitude = (wave + 1) / 2 * 30
            
            inner_r = self.radius + 10
            outer_r = inner_r + amplitude
            
            x1 = self.center + math.cos(angle) * inner_r
            y1 = self.center + math.sin(angle) * inner_r
            x2 = self.center + math.cos(angle) * outer_r
            y2 = self.center + math.sin(angle) * outer_r
            
            self.create_line(x1, y1, x2, y2, fill=self.COLOR_GLOW, width=3)
        
        # Center orb
        self.create_oval(
            self.center - self.radius, self.center - self.radius,
            self.center + self.radius, self.center + self.radius,
            fill=self.COLOR_ACTIVE, outline=self.COLOR_GLOW, width=2
        )
        
    def _blend_color(self, color1: str, color2: str, ratio: float) -> str:
        """Blend two hex colors by ratio (0.0 to 1.0)"""
        # Parse hex colors
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        # Blend
        r = int(r1 * ratio + r2 * (1 - ratio))
        g = int(g1 * ratio + g2 * (1 - ratio))
        b = int(b1 * ratio + b2 * (1 - ratio))
        
        return f"#{r:02x}{g:02x}{b:02x}"


if __name__ == "__main__":
    # Test visualization
    root = tk.Tk()
    root.title("Orb Visualizer Test")
    root.configure(bg='#000000')
    
    orb = OrbVisualizer(root, size=500)
    orb.pack(padx=20, pady=20)
    
    # State controls
    frame = tk.Frame(root, bg='#000000')
    frame.pack(pady=10)
    
    def set_idle():
        orb.set_state(OrbVisualizer.STATE_IDLE)
    
    def set_listening():
        orb.set_state(OrbVisualizer.STATE_LISTENING)
        # Simulate audio levels
        import random
        def update_audio():
            if orb.state == OrbVisualizer.STATE_LISTENING:
                orb.update_audio_levels([random.random() for _ in range(10)])
                root.after(50, update_audio)
        update_audio()
    
    def set_processing():
        orb.set_state(OrbVisualizer.STATE_PROCESSING)
    
    def set_speaking():
        orb.set_state(OrbVisualizer.STATE_SPEAKING)
        # Simulate speech waveform
        import random
        def update_speech():
            if orb.state == OrbVisualizer.STATE_SPEAKING:
                orb.update_audio_levels([random.random() for _ in range(32)])
                root.after(30, update_speech)
        update_speech()
    
    tk.Button(frame, text="Idle", command=set_idle, bg='#1E90FF', fg='white').pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Listening", command=set_listening, bg='#00BFFF', fg='white').pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Processing", command=set_processing, bg='#87CEEB', fg='black').pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Speaking", command=set_speaking, bg='#4169E1', fg='white').pack(side=tk.LEFT, padx=5)
    
    orb.start()
    root.mainloop()
