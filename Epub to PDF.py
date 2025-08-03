import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from pathlib import Path
import tempfile
import subprocess
import sys

try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class EPUBToPDFConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB to PDF Converter")
        self.root.geometry("650x450")
        self.root.resizable(True, True)
        
        # Variables
        self.epub_file = tk.StringVar()
        self.pdf_file = tk.StringVar()
        self.conversion_method = tk.StringVar(value="reportlab")
        
        self.setup_ui()
        self.check_dependencies()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="EPUB to PDF Converter", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # EPUB file selection
        ttk.Label(main_frame, text="Select EPUB file:").grid(row=1, column=0, 
                                                            sticky=tk.W, pady=5)
        
        epub_entry = ttk.Entry(main_frame, textvariable=self.epub_file, width=50)
        epub_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        epub_button = ttk.Button(main_frame, text="Browse", 
                                command=self.browse_epub_file)
        epub_button.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # PDF output selection
        ttk.Label(main_frame, text="Save PDF as:").grid(row=2, column=0, 
                                                       sticky=tk.W, pady=5)
        
        pdf_entry = ttk.Entry(main_frame, textvariable=self.pdf_file, width=50)
        pdf_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        pdf_button = ttk.Button(main_frame, text="Browse", 
                               command=self.browse_pdf_file)
        pdf_button.grid(row=2, column=2, pady=5, padx=(5, 0))
        
        # Conversion method selection
        ttk.Label(main_frame, text="Conversion method:").grid(row=3, column=0, 
                                                             sticky=tk.W, pady=5)
        
        method_frame = ttk.Frame(main_frame)
        method_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        ttk.Radiobutton(method_frame, text="ReportLab (Recommended)", 
                       variable=self.conversion_method, value="reportlab").pack(side=tk.LEFT)
        ttk.Radiobutton(method_frame, text="Calibre (if installed)", 
                       variable=self.conversion_method, value="calibre").pack(side=tk.LEFT, padx=(20, 0))
        
        # Convert button
        convert_button = ttk.Button(main_frame, text="Convert to PDF", 
                                   command=self.start_conversion,
                                   style="Accent.TButton")
        convert_button.grid(row=4, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                              pady=(0, 10))
        
        # Status text
        self.status_text = tk.Text(main_frame, height=12, width=70, 
                                  wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, 
                                 command=self.status_text.yview)
        scrollbar.grid(row=6, column=3, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Configure row weight for text area
        main_frame.rowconfigure(6, weight=1)
        
    def check_dependencies(self):
        """Check and report available dependencies"""
        missing_deps = []
        
        if not EBOOKLIB_AVAILABLE:
            missing_deps.append("ebooklib")
        if not REPORTLAB_AVAILABLE:
            missing_deps.append("reportlab")
        if not BS4_AVAILABLE:
            missing_deps.append("beautifulsoup4")
            
        if missing_deps:
            deps_str = ", ".join(missing_deps)
            self.log_status(f"Missing dependencies: {deps_str}")
            self.log_status(f"Install with: pip install {deps_str}")
            self.log_status("=" * 50)
        else:
            self.log_status("All dependencies available!")
            self.log_status("=" * 50)
        
    def browse_epub_file(self):
        file_path = filedialog.askopenfilename(
            title="Select EPUB file",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        if file_path:
            self.epub_file.set(file_path)
            # Auto-suggest PDF filename
            pdf_path = str(Path(file_path).with_suffix('.pdf'))
            self.pdf_file.set(pdf_path)
            
    def browse_pdf_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.pdf_file.set(file_path)
            
    def log_status(self, message):
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.configure(state=tk.DISABLED)
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_conversion(self):
        if not self.epub_file.get():
            messagebox.showerror("Error", "Please select an EPUB file")
            return
            
        if not self.pdf_file.get():
            messagebox.showerror("Error", "Please specify output PDF file")
            return
            
        if not EBOOKLIB_AVAILABLE:
            messagebox.showerror("Error", "ebooklib is required. Install with: pip install ebooklib")
            return
            
        # Clear status text
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.configure(state=tk.DISABLED)
        
        # Start conversion in separate thread
        self.progress_bar.start()
        thread = threading.Thread(target=self.convert_epub_to_pdf)
        thread.daemon = True
        thread.start()
        
    def convert_epub_to_pdf(self):
        try:
            method = self.conversion_method.get()
            
            if method == "calibre":
                self.convert_with_calibre()
            else:
                self.convert_with_reportlab()
                
        except Exception as e:
            error_msg = f"Error during conversion: {str(e)}"
            self.log_status(error_msg)
            messagebox.showerror("Conversion Error", error_msg)
            
        finally:
            self.progress_bar.stop()
            
    def convert_with_calibre(self):
        """Convert using Calibre command line tool"""
        self.log_status("Using Calibre for conversion...")
        
        try:
            # Check if Calibre is installed
            result = subprocess.run(['ebook-convert', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception("Calibre not found. Please install Calibre.")
                
            self.log_status(f"Found Calibre: {result.stdout.strip()}")
            
            # Run conversion
            cmd = [
                'ebook-convert', 
                self.epub_file.get(), 
                self.pdf_file.get(),
                '--paper-size', 'a4',
                '--pdf-default-font-size', '12',
                '--pdf-mono-font-size', '10',
                '--margin-left', '72',
                '--margin-right', '72',
                '--margin-top', '72',
                '--margin-bottom', '72'
            ]
            
            self.log_status("Starting Calibre conversion...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_status("Conversion completed successfully!")
                messagebox.showinfo("Success", 
                                  f"EPUB successfully converted to PDF:\n{self.pdf_file.get()}")
            else:
                raise Exception(f"Calibre conversion failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Conversion timed out")
        except FileNotFoundError:
            raise Exception("Calibre not found. Please install Calibre and ensure it's in your PATH.")
            
    def convert_with_reportlab(self):
        """Convert using ReportLab"""
        if not REPORTLAB_AVAILABLE:
            raise Exception("ReportLab is required. Install with: pip install reportlab")
            
        self.log_status("Using ReportLab for conversion...")
        self.log_status(f"Input: {self.epub_file.get()}")
        self.log_status(f"Output: {self.pdf_file.get()}")
        
        # Read EPUB file
        self.log_status("Reading EPUB file...")
        book = epub.read_epub(self.epub_file.get())
        
        # Create PDF
        doc = SimpleDocTemplate(self.pdf_file.get(), pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        author_style = ParagraphStyle(
            'CustomAuthor',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0
        )
        
        # Add title and author
        title = book.get_metadata('DC', 'title')
        author = book.get_metadata('DC', 'creator')
        
        if title:
            story.append(Paragraph(title[0][0], title_style))
            
        if author:
            story.append(Paragraph(f"by {author[0][0]}", author_style))
            
        story.append(Spacer(1, 0.5*inch))
        
        # Process content
        chapter_count = 0
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapter_count += 1
                self.log_status(f"Processing chapter {chapter_count}: {item.get_name()}")
                
                content = item.get_content().decode('utf-8')
                text_content = self.extract_text_from_html(content)
                
                if text_content.strip():
                    # Split into paragraphs
                    paragraphs = text_content.split('\n')
                    
                    for para in paragraphs:
                        para = para.strip()
                        if para:
                            # Simple heading detection
                            if len(para) < 100 and (para.isupper() or 
                                                   para.startswith('Chapter') or 
                                                   para.startswith('CHAPTER')):
                                story.append(Paragraph(para, heading_style))
                            else:
                                story.append(Paragraph(para, body_style))
                    
                    story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        self.log_status("Generating PDF...")
        doc.build(story)
        
        self.log_status("Conversion completed successfully!")
        messagebox.showinfo("Success", 
                          f"EPUB successfully converted to PDF:\n{self.pdf_file.get()}")
        
    def extract_text_from_html(self, html_content):
        """Extract text from HTML content"""
        if BS4_AVAILABLE:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        else:
            # Fallback: simple HTML tag removal
            import re
            text = re.sub('<[^<]+?>', '', html_content)
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            return text


def main():
    root = tk.Tk()
    app = EPUBToPDFConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()