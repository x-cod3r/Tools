import tkinter as tk
from tkinter import messagebox

def main():
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Show alert message
    messagebox.showinfo("Test Alert", "The app run successfully!")
    
    # Close the application
    root.destroy()

if __name__ == "__main__":
    main()