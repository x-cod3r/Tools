import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sounddevice as sd
import numpy as np
import scipy.signal
import soundfile as sf
import threading
import queue
from pydub import AudioSegment
from pydub.playback import play # Not strictly needed for saving, but good to have if playback is added later

class VoiceRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder")
        self.root.geometry("400x300")
        
        # Audio parameters
        self.sample_rate = 44100
        self.channels = 1
        self.recording = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.waveform_queue = queue.Queue()
        
        # UI Elements
        self.create_widgets()
        
    def create_widgets(self):
        # Recording controls
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        self.record_btn = ttk.Button(control_frame, text="Record", command=self.start_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_recording, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Noise cancellation option
        self.noise_reduction = tk.BooleanVar()
        noise_check = ttk.Checkbutton(control_frame, text="Noise Cancellation", variable=self.noise_reduction)
        noise_check.pack(side=tk.LEFT, padx=5)
        
        noise_frame = ttk.Frame(self.root, padding="10")
        noise_frame.pack(fill=tk.X)
        ttk.Label(noise_frame, text="NR Level:").pack(side=tk.LEFT, padx=5)
        self.nr_level_var = tk.DoubleVar(value=1.0)
        nr_scale = ttk.Scale(noise_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, variable=self.nr_level_var)
        nr_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        
        # Format selector
        format_frame = ttk.Frame(self.root, padding="10")
        format_frame.pack(fill=tk.X)
        
        ttk.Label(format_frame, text="Save Format:").pack(side=tk.LEFT, padx=5)
        self.format_var = tk.StringVar(value="wav")
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                   values=["wav", "flac", "ogg", "mp3"], state="readonly", width=10)
        format_combo.pack(side=tk.LEFT, padx=5)
        
        # Save button
        self.save_btn = ttk.Button(format_frame, text="Save Recording", command=self.save_recording, state=tk.DISABLED)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Volume control
        volume_frame = ttk.Frame(self.root, padding="10")
        volume_frame.pack(fill=tk.X)
        ttk.Label(volume_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_scale = ttk.Scale(volume_frame, from_=0.1, to=5.0, orient=tk.HORIZONTAL, variable=self.volume_var)
        volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Status display
        self.status_var = tk.StringVar(value="Ready to record")
        status_label = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.CENTER)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Audio visualization (simple)
        self.canvas = tk.Canvas(self.root, bg="black", height=150)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.draw_waveform()
        
    def draw_waveform(self, data=None):
        self.canvas.delete("all")
        self.root.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1: width = 380
        if height <= 1: height = 150
        center = height / 2

        # Draw center line
        self.canvas.create_line(0, center, width, center, fill="green", dash=(2,2))

        if data is None and self.recording is not None:
            data = self.recording
        
        if data is not None:
            data = data.flatten()
            
            if len(data) > width:
                # Downsample for visualization
                data = scipy.signal.resample(data, width)

            max_amp = np.max(np.abs(data))
            if max_amp == 0: max_amp = 1.0
            
            scaled_data = data / max_amp * (height / 2)

            points = []
            for i, sample in enumerate(scaled_data):
                points.extend([i, center - sample])
            
            if len(points) > 2:
                self.canvas.create_line(points, fill="lightgreen", width=1)
        
    def start_recording(self):
        self.recording = None
        self.draw_waveform()
        self.record_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set("Recording...")
        self.is_recording = True
        
        # Start recording in a separate thread
        threading.Thread(target=self.record_audio, daemon=True).start()
        self.update_waveform_display()
        
    def record_audio(self):
        recorded_frames = []
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32') as stream:
                while self.is_recording:
                    data, overflowed = stream.read(1024)
                    recorded_frames.append(data)
                    # For live visualization
                    self.waveform_queue.put(data.copy())
            
            if recorded_frames:
                self.recording = np.concatenate(recorded_frames, axis=0)
                
                if self.noise_reduction.get():
                    self.recording = self.reduce_noise(self.recording)
                
                self.recording = self.amplify_audio(self.recording)
                    
                self.audio_queue.put(self.recording)
                self.root.after(0, self.finish_recording)
            else:
                self.root.after(0, self.reset_ui)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Recording failed: {str(e)}"))
            self.root.after(0, self.reset_ui)

    def update_waveform_display(self):
        if not self.is_recording:
            # Clear the queue
            while not self.waveform_queue.empty():
                try:
                    self.waveform_queue.get_nowait()
                except queue.Empty:
                    break
            return
        
        try:
            data_chunk = self.waveform_queue.get_nowait()
            self.draw_waveform(data_chunk)
        except queue.Empty:
            pass
        
        self.root.after(50, self.update_waveform_display) # Update rate
            
    def reduce_noise(self, audio_data, noise_len_sec=0.5, nr_level=None):
        """
        Reduce noise using spectral subtraction.
        """
        if nr_level is None:
            nr_level = self.nr_level_var.get()

        audio_data = audio_data.flatten()
        
        # Estimate noise
        noise_len_samples = int(noise_len_sec * self.sample_rate)
        noise_segment = audio_data[:noise_len_samples]
        noise_stft = scipy.signal.stft(noise_segment)[2]
        noise_power_spectrum = np.mean(np.abs(noise_stft)**2, axis=1)
        
        # Process the whole signal
        _, _, signal_stft = scipy.signal.stft(audio_data)
        signal_power_spectrum = np.abs(signal_stft)**2
        
        # Subtract noise
        power_difference = signal_power_spectrum - nr_level * np.expand_dims(noise_power_spectrum, axis=1)
        power_difference[power_difference < 0] = 0
        
        # Wiener filtering-like approach
        signal_mask = power_difference / (signal_power_spectrum + 1e-10)
        
        # Apply mask and invert STFT
        denoised_stft = signal_stft * signal_mask
        _, denoised_audio = scipy.signal.istft(denoised_stft)
        
        # Ensure output length matches input
        min_len = min(len(audio_data), len(denoised_audio))
        return denoised_audio[:min_len].reshape(-1, 1)

    def amplify_audio(self, audio_data):
        volume = self.volume_var.get()
        return audio_data * volume
        
    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.status_var.set("Processing...")
        
    def finish_recording(self):
        self.recording = self.audio_queue.get()
        self.status_var.set("Recording complete")
        self.save_btn.config(state=tk.NORMAL)
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.draw_waveform()
        
    def reset_ui(self):
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set("Ready to record")
        
    def save_recording(self):
        if self.recording is None:
            messagebox.showwarning("Warning", "No recording to save")
            return
            
        file_format = self.format_var.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=[(f"{file_format.upper()} files", f"*.{file_format}"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_format == "mp3":
                    # pydub expects audio in milliseconds, so convert duration
                    audio_segment = AudioSegment(
                        (self.recording * (2**15 - 1)).astype(np.int16).tobytes(),
                        frame_rate=self.sample_rate,
                        sample_width=2, # 2 bytes for int16
                        channels=self.channels
                    )
                    audio_segment.export(file_path, format="mp3")
                else:
                    sf.write(file_path, self.recording, self.sample_rate)
                messagebox.showinfo("Success", f"File saved as {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceRecorder(root)
    root.mainloop()
