"""
This module contains the core application logic for the Revit Warnings Manager.
"""
import tkinter as tk
from tkinter import ttk
from ui import UIManager
from handlers import EventHandlers
from file_operations import FileOperations
import os
from loguru import logger

# Configure logging
logger.add("app.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB", compression="zip")
logger.debug("Application started.")

class RevitManager:
    """
    The main application class that orchestrates the UI, event handling,
    and file operations.
    """
    def __init__(self, root):
        logger.debug("Initializing RevitManager.")
        self.root = root
        self.root.title("AEC.codes - Revit Resolution Tools")
        self.root.geometry("1400x900")
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                logger.debug(f"Window icon set successfully: {icon_path}")
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")

        # Data holders
        self.warnings_data = []
        self.json_file_path = None
        self.journal_problems = []

        # Initialize components
        self.ui = UIManager(self)
        self.events = EventHandlers(self)
        self.files = FileOperations(self)

        # Setup UI
        self.ui.setup_ui()
        logger.debug("UI setup completed.")

        # Debugging journal_tree initialization
        if not hasattr(self, 'journal_tree'):
            logger.error("journal_tree attribute is missing after UI setup.")
        else:
            logger.debug("journal_tree attribute successfully initialized.")
