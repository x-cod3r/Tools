import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
import queue

class PDFToImageConverter:
    # Constants for DPI presets
    DPI_SCREEN = 72
    DPI_HIGH = 144
    DPI_PRINT = 300
    DPI_ULTRA = 600

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF to High-Quality Image Converter")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Variables
        self.pdf_path: tk.StringVar = tk.StringVar()
        self.output_dir: tk.StringVar = tk.StringVar()
        self.zoom = tk.DoubleVar(value=2.0)  # Default zoom factor (2.0 = 144 DPI)
        self.output_format = tk.StringVar(value="PNG")
        self.progress_queue = queue.Queue()
        
        # Create GUI elements
        self.create_widgets()
        
        # Check for updates in the progress queue
        self.root.after(100, self.process_queue)
    
    def create_widgets(self) -> None:
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF to High-Quality Image Converter", 
                               font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # PDF Selection
        pdf_frame = ttk.Frame(main_frame)
        pdf_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(pdf_frame, text="PDF File:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(pdf_frame, textvariable=self.pdf_path, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(pdf_frame, text="Browse", command=self.browse_pdf).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Output Directory
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="Output Folder:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Format Selection
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=tk.X, pady=10)
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=(0, 10))
        format_options = ["PNG", "JPEG", "TIFF", "BMP"]
        format_menu = ttk.Combobox(format_frame, textvariable=self.output_format, values=format_options, state="readonly", width=10)
        format_menu.pack(side=tk.LEFT)
        format_menu.set("PNG") # Default selection

        # Zoom Settings
        zoom_frame = ttk.Frame(main_frame)
        zoom_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(zoom_frame, text="Quality (Zoom):").pack(side=tk.LEFT, padx=(0, 10))
        zoom_scale = ttk.Scale(zoom_frame, from_=1.0, to=8.5, variable=self.zoom,
                              orient=tk.HORIZONTAL, length=200, command=self.update_zoom_label)
        zoom_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.zoom_label = ttk.Label(zoom_frame, text="2.0x (144 DPI)")
        self.zoom_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Quality Presets
        preset_frame = ttk.Frame(main_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preset_frame, text="Quality Presets:").pack(side=tk.LEFT, padx=(0, 10))
        # Base PDF DPI is 72, so zoom = target_dpi / 72
        ttk.Button(preset_frame, text=f"Screen ({self.DPI_SCREEN} DPI)", command=lambda: self.set_zoom(self.DPI_SCREEN / 72)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text=f"High ({self.DPI_HIGH} DPI)", command=lambda: self.set_zoom(self.DPI_HIGH / 72)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text=f"Print ({self.DPI_PRINT} DPI)", command=lambda: self.set_zoom(self.DPI_PRINT / 72)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text=f"Ultra ({self.DPI_ULTRA} DPI)", command=lambda: self.set_zoom(self.DPI_ULTRA / 72)).pack(side=tk.LEFT, padx=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=20)
        
        # Status Label
        self.status_label = ttk.Label(main_frame, text="Ready to convert", font=('Helvetica', 10))
        self.status_label.pack(pady=5)
        
        # Convert Button
        self.convert_btn = ttk.Button(main_frame, text="Convert PDF to Images", 
                                     command=self.start_conversion, style='Accent.TButton')
        self.convert_btn.pack(pady=20)
        
        # Configure style
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Helvetica', 12, 'bold'))
    
    def update_zoom_label(self, value: str) -> None:
        zoom = float(value)
        dpi = round(zoom * 72)  # Base PDF DPI is 72
        self.zoom_label.config(text=f"{zoom:.1f}x ({dpi} DPI)")
    
    def set_zoom(self, value: float) -> None:
        self.zoom.set(value)
        self.update_zoom_label(str(value))
    
    def browse_pdf(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            self.pdf_path.set(file_path)
            # Set default output directory to PDF's location
            if not self.output_dir.get():
                self.output_dir.set(str(Path(file_path).parent))
    
    def browse_output(self) -> None:
        dir_path = filedialog.askdirectory(title="Select Output Folder")
        if dir_path:
            self.output_dir.set(dir_path)
    
    def start_conversion(self) -> None:
        # Validate inputs
        if not self.pdf_path.get():
            messagebox.showerror("Error", "Please select a PDF file")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        # Disable button during conversion
        self.convert_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.status_label.config(text="Starting conversion...")
        
        # Start conversion in a separate thread
        threading.Thread(target=self.convert_pdf, daemon=True).start()
    
    def convert_pdf(self) -> None:
        """
        Performs the PDF to image conversion in a worker thread.
        Communicates progress, completion, or errors back to the main thread via a queue.
        """
        try:
            pdf_path = Path(self.pdf_path.get())
            output_dir = Path(self.output_dir.get())
            zoom = self.zoom.get()
            output_format = self.output_format.get()
            
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use a 'with' statement for robust resource management
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                
                self.progress_queue.put(("progress", 0, total_pages))
                self.progress_queue.put(("status", f"Converting {total_pages} pages at {zoom:.1f}x zoom..."))
                
                # Process each page
                for page_num in range(total_pages):
                    page = doc.load_page(page_num)  # Get the page
                    
                    # Render page to an image (pixmap)
                    mat = fitz.Matrix(zoom, zoom)  # Zoom factor
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # For formats like JPEG that don't support alpha channels,
                    # ensure image is in RGB mode. Our 'frombytes' call already does this.
                    if output_format == "JPEG":
                        img = img.convert("RGB")

                    # Save in the selected format
                    file_extension = output_format.lower()
                    output_path = output_dir / f"{pdf_path.stem}_page_{page_num+1}.{file_extension}"
                    img.save(output_path, format=output_format)
                    
                    # Update progress
                    self.progress_queue.put(("progress", page_num+1, total_pages))
                    self.progress_queue.put(("status", f"Converted page {page_num+1}/{total_pages}"))
            
            self.progress_queue.put(("complete", total_pages))
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def process_queue(self) -> None:
        """Checks the progress queue and updates the GUI accordingly."""
        try:
            while True:
                msg_type, *args = self.progress_queue.get_nowait()
                
                if msg_type == "progress":
                    current, total = args
                    self.progress['value'] = (current / total) * 100
                elif msg_type == "status":
                    self.status_label.config(text=args[0])
                elif msg_type == "complete":
                    total = args[0]
                    self.status_label.config(text=f"Conversion complete! {total} pages saved")
                    messagebox.showinfo("Success", f"Successfully converted {total} pages to images")
                    self.convert_btn.config(state=tk.NORMAL)
                elif msg_type == "error":
                    messagebox.showerror("Conversion Error", args[0])
                    self.status_label.config(text="Conversion failed")
                    self.convert_btn.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    PDFToImageConverter(root)
    root.mainloop()