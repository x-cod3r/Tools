import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import wmi
import datetime
import subprocess
import os
import sys
import ctypes  # Import for is_admin, and run_as_admin
import traceback # Import to show traceback
import logging  # Import for logging

# Setup Logging
LOG_FILE = 'restore_manager.log'
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class RestorePointManager:
    TITLE = "System Restore Point Manager"
    ERROR_TITLE = "Error"
    
    def __init__(self, root):
        self.root = root
        self.root.title(RestorePointManager.TITLE)
        self.root.geometry("800x600")
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.c = wmi.WMI()
        self.restore_points = []

        self._create_widgets()
        self._load_restore_points()

    def _create_widgets(self):
        # Restore Point List Frame
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Restore Point List
        self.listbox = tk.Listbox(frame, height=20, width=80)
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox['yscrollcommand'] = scrollbar.set

        # Status Label
        self.status_label = ttk.Label(self.root, text="", wraplength=600)
        self.status_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Button Frame
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        # Create Button
        ttk.Button(button_frame, text="Create Restore Point", command=self._create_restore_point).grid(row=0, column=0, sticky="ew", padx=5)

        # Details button
        ttk.Button(button_frame, text="Show Details", command=self._show_details).grid(row=0, column=1, sticky="ew", padx=5)
        
        # Delete Button
        ttk.Button(button_frame, text="Delete Restore Point", command=self._delete_restore_point).grid(row=0, column=2, sticky="ew", padx=5)
        
        # Restore System
        ttk.Button(button_frame, text="Restore System", command=self._restore_system).grid(row=0, column=3, sticky="ew", padx=5)

        # Refresh Button
        ttk.Button(button_frame, text="Refresh Restore Points", command=self._load_restore_points).grid(row=0, column=4, sticky="ew", padx=5)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)
        button_frame.grid_columnconfigure(4, weight=1)

    def _load_restore_points(self):
        """Loads and displays system restore points in the listbox."""
        try:
            self.listbox.delete(0, tk.END)
            self.restore_points = []
            # Corrected line: Use "SystemRestore" instead of "Win32_SystemRestore"
            for rp in self.c.SystemRestore().Instances():
                self.restore_points.append(rp)
                formatted_date = self._format_time(rp.CreationTime)
                self.listbox.insert(tk.END, f"{rp.Description} ({formatted_date})")
            self._update_status(f"{len(self.restore_points)} restore point(s) found.")
        except Exception as e:
            self._log_error(f"Error retrieving restore points: {e}")
            self._update_status("Error loading restore points. Check log for details.")
            self._show_error("Error Retriving Restore Points", f"Error: {e}")

    def _create_restore_point(self):
        """Creates a new system restore point with a user-provided summary."""
        summary = simpledialog.askstring("Restore Point Summary", "Enter a brief summary of the change:")
        if not summary:
            self._update_status("Restore point creation cancelled.")
            return

        try:
            if not self._is_admin():
                self._update_status("Administrator privileges are required to create a restore point.")
                self._show_error("Permissions Error","Administrator permissions required to create a restore point.")
                self._run_as_admin()
                return
            
            self.c.SystemRestore.CreateRestorePoint(Description=f"Install: {summary}", RestorePointType=0)
            self._update_status(f"Restore point created successfully: Install - {summary}")
            self._load_restore_points()
        except Exception as e:
           self._log_error(f"Error creating restore point: {e}")
           self._update_status("Error creating restore point. Check log for details")
           self._show_error("Error Creating Restore Point", f"Error: {e}")

    def _show_details(self):
        """Displays details of the selected restore point."""
        selection = self.listbox.curselection()
        if not selection:
            self._update_status("No restore point selected.")
            return

        selected_index = selection[0]
        selected_rp = self.restore_points[selected_index]

        formatted_date = self._format_time(selected_rp.CreationTime)
        details = (
            f"Description: {selected_rp.Description}\n"
            f"Creation Time: {formatted_date}\n"
            f"Restore Point Type: {selected_rp.RestorePointType}\n"
            f"Sequence Number: {selected_rp.SequenceNumber}\n"
        )

        detail_window = tk.Toplevel(self.root)
        detail_window.title("Restore Point Details")
        detail_text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD, width=80, height=20)
        detail_text.insert(tk.INSERT, details)
        detail_text.config(state=tk.DISABLED)
        detail_text.pack(expand=True, fill="both", padx=10, pady=10)

    def _delete_restore_point(self):
        """Deletes the selected system restore point."""
        selection = self.listbox.curselection()
        if not selection:
            self._update_status("No restore point selected for deletion.")
            return
        
        selected_index = selection[0]
        selected_rp = self.restore_points[selected_index]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the restore point '{selected_rp.Description}'?"):
            try:
                if not self._is_admin():
                     self._update_status("Administrator privileges are required to delete a restore point.")
                     self._show_error("Permissions Error","Administrator permissions required to delete a restore point.")
                     self._run_as_admin()
                     return
                
                self.c.SystemRestore.DeleteRestorePoint(selected_rp.SequenceNumber)
                self._update_status(f"Restore point '{selected_rp.Description}' deleted successfully.")
                self._load_restore_points()  # Refresh the list
            except Exception as e:
                self._log_error(f"Error deleting restore point: {e}")
                self._update_status("Error deleting restore point. Check log for details.")
                self._show_error("Error Deleting Restore Point", f"Error: {e}")
                
    def _restore_system(self):
        """Initiates a system restore to the selected restore point."""
        selection = self.listbox.curselection()
        if not selection:
            self._update_status("No restore point selected for system restore.")
            return

        selected_index = selection[0]
        selected_rp = self.restore_points[selected_index]

        if messagebox.askyesno("Confirm Restore", f"Are you sure you want to restore your system to '{selected_rp.Description}'? This will restart your computer."):
            try:
                if not self._is_admin():
                    self._update_status("Administrator privileges are required to restore the system.")
                    self._show_error("Permissions Error","Administrator permissions required to restore the system.")
                    self._run_as_admin()
                    return
                
                subprocess.run(["rstrui.exe", "/RESTART", f"/s:{selected_rp.SequenceNumber}"], check = True) 
                self._update_status("System restore initiated. Your computer will restart.")
                # Note the user will not see this, but we will still update just in case
            except Exception as e:
                self._log_error(f"Error initiating system restore: {e}")
                self._update_status("Error initiating system restore. Check log for details.")
                self._show_error("Error Initiating System Restore", f"Error: {e}")
    
    def _format_time(self, wmi_time):
        """Formats a WMI timestamp into a readable datetime string."""
        timestamp = wmi_time / 10000000 - 11644473600
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def _is_admin(self):
        """Checks if the script is running with administrator privileges."""
        try:
            return os.getuid() == 0 # Checks to see if you have administrator rights on Unix based system
        except AttributeError:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0 #Checks to see if you have admin on Windows

    def _run_as_admin(self):
        """Restarts the script with administrator privileges if needed."""
        try:
            if sys.platform == "win32":
                if not self._is_admin():
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                    sys.exit()
        except Exception as e:
            self._log_error (f"Error getting administrator prompt: {e}")
            self._show_error ("Administrator prompt Error", str(e))
            self._update_status ("Error getting administrator prompt. Check log for more info.")
            
    def _update_status(self, message):
        """Updates the status label with the provided message."""
        self.status_label.config(text=message)
        self.root.update()

    def _show_error(self, title, message):
         """Displays an error message box."""
         messagebox.showerror(title, message)

    def _log_error(self, message):
         """Logs error messages with traceback."""
         logging.error(message)
         logging.error(traceback.format_exc())
         

def main():
    root = tk.Tk()
    app = RestorePointManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()