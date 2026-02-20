
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import multiprocessing
import threading
import sys
import os
from pathlib import Path
import time
import queue

# Import core logic
try:
    import faster_whisper_srt
except ImportError:
    # Fallback if run from a different directory without proper path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import faster_whisper_srt

# --- Theme Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
THEME_COLOR = "#9bbdad"
HOVER_COLOR = "#7a9b8b"
BG_COLOR = "#2b2b2b"

class RedirectText(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, string):
        # We need to ensure we don't crash if queue is closed
        try:
            self.queue.put(string)
        except Exception:
            pass

    def flush(self):
        pass

# Worker Process Function (Must be top-level for multiprocessing on Windows)
def worker_process(files_to_process, model_name, max_chars, log_queue, progress_queue, status_queue):
    # Redirect stdout/stderr in the new process
    sys.stdout = RedirectText(log_queue)
    sys.stderr = RedirectText(log_queue)
    
    try:
        def on_model_status(msg):
            try:
                status_queue.put(msg)
            except Exception:
                pass

        status_queue.put(f"Loading Model: {model_name}...")
        
        # Load model (Blocking, but can be killed via terminate)
        model = faster_whisper_srt.load_model_with_progress(model_name, on_progress_callback=on_model_status)
        
        total_files = len(files_to_process)
        
        for i, file_path in enumerate(files_to_process):
            filename = Path(file_path).name
            log_queue.put(f"\n[{i+1}/{total_files}] Processing: {filename}\n")
            status_queue.put(f"Processing {i+1}/{total_files}: {filename}")

            def progress_cb(current, total):
                try:
                    progress_queue.put((current, total))
                except Exception:
                    pass

            try:
                success = faster_whisper_srt.process_file(
                    Path(file_path), 
                    model, 
                    model_name, 
                    max_chars,
                    progress_callback=progress_cb
                )
                if success:
                    log_queue.put(f"[+] Done: {filename}\n")
            except Exception as e:
                log_queue.put(f"[!] Error processing {filename}: {e}\n")

        log_queue.put("\n[+] All tasks finished.\n")
        status_queue.put("Finished")
        
    except Exception as e:
        log_queue.put(f"\n[!] Critical Error: {e}\n")
        status_queue.put("Error")
    finally:
        # Restore (though process is ending anyway)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Faster Whisper SRT Converter")
        self.geometry("1000x700") 
        
        self.after(0, lambda: self.state('zoomed'))

        # Data
        self.files_to_process = []
        self.process = None # multiprocessing.Process
        
        # Queues for IPC
        self.log_queue = multiprocessing.Queue()
        self.progress_queue = multiprocessing.Queue()
        self.status_queue = multiprocessing.Queue()
        
        self.model_data = [
            ("tiny", "tiny (75 MB)", "⚡⚡⚡⚡⚡ | ★☆☆☆☆ | Fastest, lowest accuracy"),
            ("base", "base (145 MB)", "⚡⚡⚡⚡ | ★★☆☆☆ | Fast, low accuracy"),
            ("small", "small (490 MB)", "⚡⚡⚡ | ★★★☆☆ | Balanced speed/accuracy"),
            ("medium", "medium (1.5 GB)", "⚡⚡ | ★★★★☆ | Reasonable accuracy (Default)"),
            ("large-v3-turbo", "large-v3-turbo (1.6 GB)", "⚡⚡⚡ | ★★★★☆ | High accuracy, faster than large"),
            ("large-v3", "large-v3 (3.1 GB)", "⚡ | ★★★★★ | Highest accuracy, slowest"),
        ]
        
        # Layout Setup
        self.setup_ui()
        
        # Start checking queues
        self.after(100, self.check_queues)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1, uniform="group1") 
        self.grid_columnconfigure(1, weight=1, uniform="group1") 
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL ---
        self.frame_left = ctk.CTkFrame(self, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nsew")
        self.frame_left.grid_rowconfigure(3, weight=1)
        self.frame_left.grid_columnconfigure(0, weight=1) 

        # Title
        self.lbl_title = ctk.CTkLabel(self.frame_left, text="Faster Whisper SRT", 
                                      font=ctk.CTkFont(size=24, weight="bold"),
                                      text_color=THEME_COLOR)
        self.lbl_title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Files
        self.frame_files = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_files.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_file = ctk.CTkLabel(self.frame_files, text="Input Files:", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_file.pack(anchor="w", pady=(0, 5))
        
        self.entry_file = ctk.CTkEntry(self.frame_files, placeholder_text="Select audio/video...")
        self.entry_file.pack(fill="x", pady=(0, 5))
        
        self.btn_browse = ctk.CTkButton(self.frame_files, text="Browse Files", command=self.browse_files,
                                        fg_color=THEME_COLOR, hover_color=HOVER_COLOR, text_color="black")
        self.btn_browse.pack(fill="x")

        # Models
        self.lbl_model_header = ctk.CTkLabel(self.frame_left, text="Select Model:", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_model_header.grid(row=2, column=0, padx=20, pady=(20, 5), sticky="nw")

        self.scroll_models = ctk.CTkScrollableFrame(self.frame_left, label_text="Available Models")
        self.scroll_models.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        self.radio_var = tk.StringVar(value="medium")
        for model_id, label_text, desc_text in self.model_data:
            item_frame = ctk.CTkFrame(self.scroll_models, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            rb = ctk.CTkRadioButton(item_frame, text=label_text, value=model_id, variable=self.radio_var,
                                    fg_color=THEME_COLOR, hover_color=HOVER_COLOR,
                                    font=ctk.CTkFont(size=13, weight="bold"))
            rb.pack(anchor="w")
            
            desc_lbl = ctk.CTkLabel(item_frame, text=desc_text, text_color="gray", font=ctk.CTkFont(size=11))
            desc_lbl.pack(anchor="w", padx=(25, 0))

        # Bind radio button change
        self.radio_var.trace_add("write", self.on_model_changed)
        # Trigger initial check
        self.after(500, self.on_model_changed)

        # Settings
        self.frame_settings = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_settings.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_chars = ctk.CTkLabel(self.frame_settings, text="Max Chars per Line:", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_chars.pack(anchor="w")
        
        self.slider_chars = ctk.CTkSlider(self.frame_settings, from_=10, to=100, number_of_steps=90, 
                                          command=self.update_chars_label,
                                          button_color=THEME_COLOR, progress_color=THEME_COLOR)
        self.slider_chars.set(40)
        self.slider_chars.pack(fill="x", pady=5)
        
        self.lbl_chars_val = ctk.CTkLabel(self.frame_settings, text="40 chars")
        self.lbl_chars_val.pack()

        # Actions
        self.frame_actions_left = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_actions_left.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        
        self.btn_start = ctk.CTkButton(self.frame_actions_left, text="START PROCESSING", command=self.start_processing, 
                                       fg_color=THEME_COLOR, hover_color=HOVER_COLOR, text_color="black",
                                       font=ctk.CTkFont(size=16, weight="bold"), height=50)
        self.btn_start.pack(fill="x", pady=(0, 10))
        
        self.btn_stop = ctk.CTkButton(self.frame_actions_left, text="STOP", command=self.stop_processing, 
                                      fg_color="#cf6679", hover_color="#b04c5e", state="disabled")
        self.btn_stop.pack(fill="x")


        # --- RIGHT PANEL ---
        self.frame_right = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e1e1e")
        self.frame_right.grid(row=0, column=1, sticky="nsew")
        
        self.frame_right_content = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        self.frame_right_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.frame_status = ctk.CTkFrame(self.frame_right_content, fg_color="transparent")
        self.frame_status.pack(fill="x", pady=(0, 20))

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Ready", font=ctk.CTkFont(size=18, weight="bold"), anchor="w")
        self.lbl_status.pack(fill="x", pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.frame_status, height=25, progress_color=THEME_COLOR)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        self.lbl_progress_text = ctk.CTkLabel(self.frame_status, text="0 / 0 s (0%)", text_color="gray", anchor="e")
        self.lbl_progress_text.pack(fill="x")
        
        self.lbl_log = ctk.CTkLabel(self.frame_right_content, text="Process Log:", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_log.pack(anchor="w", pady=(0, 5))
        
        self.textbox_log = ctk.CTkTextbox(self.frame_right_content, font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox_log.pack(fill="both", expand=True, pady=(0, 20))
        self.log_to_gui("Select files from the left panel to begin.")

        self.btn_open_folder = ctk.CTkButton(self.frame_right_content, text="Open Output Folder", command=self.open_output_folder, 
                                             state="disabled", height=40, font=ctk.CTkFont(size=14))
        self.btn_open_folder.pack(fill="x")

    def update_chars_label(self, value):
        self.lbl_chars_val.configure(text=f"{int(value)} chars")

    def browse_files(self):
        filetypes = [
            ("All Supported", "*" + " *".join(faster_whisper_srt.SUPPORTED_EXTENSIONS)),
            ("Audio", "*" + " *".join(faster_whisper_srt.AUDIO_EXTENSIONS)),
            ("Video", "*" + " *".join(faster_whisper_srt.VIDEO_EXTENSIONS)),
        ]
        files = filedialog.askopenfilenames(title="Select Files", filetypes=filetypes)
        if files:
            self.files_to_process = list(files)
            if len(files) == 1:
                self.entry_file.delete(0, tk.END)
                self.entry_file.insert(0, files[0])
            else:
                self.entry_file.delete(0, tk.END)
                self.entry_file.insert(0, f"{len(files)} files selected")
            
            self.log_to_gui(f"Selected {len(files)} files.")

    def on_model_changed(self, *args):
        model_name = self.radio_var.get()
        # Run in thread to avoid freezing UI if hf_hub is slow
        def check_path():
            try:
                is_cached, path_info = faster_whisper_srt.get_model_path_info(model_name)
                if is_cached:
                    msg = f"\n[Info] Model '{model_name}' found in:\n      {path_info}\n"
                else:
                    msg = f"\n[Info] Model '{model_name}' not found.\n      Will download to: {path_info}\n"
                
                # Use queue for thread safety
                self.log_queue.put(msg)
            except Exception as e:
                self.log_queue.put(f"\n[Error] Checking model path: {e}\n")
        
        threading.Thread(target=check_path, daemon=True).start()

    def log_to_gui(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def check_queues(self):
        # 1. Log Queue
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                msg = msg.replace('\r', '') 
                self.textbox_log.configure(state="normal")
                self.textbox_log.insert("end", msg)
                self.textbox_log.see("end")
                self.textbox_log.configure(state="disabled")
            except queue.Empty:
                break
        
        # 2. Progress Queue
        while not self.progress_queue.empty():
            try:
                current, total = self.progress_queue.get_nowait()
                if total > 0:
                    val = current / total
                    self.progress_bar.set(val)
                    pct = int(val * 100)
                    self.lbl_progress_text.configure(text=f"{int(current)}s / {int(total)}s ({pct}%)")
                else: 
                     self.progress_bar.set(0)
                     self.lbl_progress_text.configure(text="0s / 0s (0%)")
            except queue.Empty:
                # This catches empty queue, not internal multiprocessing.Queue Empty exception if different
                # But multiprocessing.Queue raises stdlib queue.Empty usually
                break

        # 3. Status Queue
        while not self.status_queue.empty():
             try:
                status_msg = self.status_queue.get_nowait()
                self.lbl_status.configure(text=status_msg)
             except queue.Empty:
                break
        
        # Check process status
        if self.process:
            if not self.process.is_alive():
                # Process finished (successfully or terminated)
                self.on_processing_finished()
                self.process = None

        self.after(100, self.check_queues)

    def toggle_inputs(self, enable):
        state = "normal" if enable else "disabled"
        self.btn_browse.configure(state=state)
        self.slider_chars.configure(state=state)
        self.btn_start.configure(state=state)
        self.btn_stop.configure(state="normal" if not enable else "disabled")

    def start_processing(self):
        if not self.files_to_process:
            messagebox.showwarning("No Files", "Please select at least one file.")
            return

        self.toggle_inputs(False)
        self.progress_bar.set(0)
        self.btn_open_folder.configure(state="disabled")
        self.lbl_progress_text.configure(text="0s / 0s (0%)")

        model_name = self.radio_var.get()
        max_chars = int(self.slider_chars.get())

        # Create independent process
        self.process = multiprocessing.Process(
            target=worker_process, 
            args=(
                self.files_to_process, 
                model_name, 
                max_chars, 
                self.log_queue, 
                self.progress_queue, 
                self.status_queue
            )
        )
        self.process.start()

    def stop_processing(self):
        if self.process and self.process.is_alive():
            try:
                # Force kill
                self.process.terminate()
                self.process.join() # Wait for it to die
                self.log_to_gui("\n[!] Force stopped by user.\n")
                self.lbl_status.configure(text="Stopped")
            except Exception as e:
                self.log_to_gui(f"\n[!] Error stopping: {e}\n")
            
            # The check_queues loop will see is_alive() false next time and call on_finished
        
    def on_processing_finished(self):
        self.toggle_inputs(True)
        self.btn_open_folder.configure(state="normal")
        # Ensure final state of label if not stopped
        if self.lbl_status.cget("text") not in ["Stopped", "Error", "Finished"]:
             self.lbl_status.configure(text="Finished")

    def open_output_folder(self):
        if self.files_to_process:
            folder = os.path.dirname(self.files_to_process[0])
            try:
                os.startfile(folder)
            except Exception:
                pass

if __name__ == "__main__":
    multiprocessing.freeze_support() # Crucial for PyInstaller
    app = App()
    app.mainloop()
