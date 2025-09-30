"""
Main entry point for the Revit Warnings Manager application.
"""
import sys
import os

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from revit_warnings_manager.app import RevitManager
import logging

# Configure logging for verbose output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug("Starting the Revit Warnings Manager application.")

def main():
    logging.debug("Initializing the application.")
    try:
        root = tk.Tk()
        logging.debug("Tkinter root window created.")
        app = RevitManager(root)
        logging.debug("RevitManager initialized.")
        root.mainloop()
        logging.debug("Application main loop started.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("Press ENTER to close...")

if __name__ == "__main__":
    main()
