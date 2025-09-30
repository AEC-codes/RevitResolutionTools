"""
This module handles file loading and saving operations.
"""
import json
import os
from tkinter import filedialog
from datetime import datetime
from loguru import logger
from parsers import HTMLParser, JournalParser, WorkerLogParser, JournalProblemFinder, ErrorHandler

class FileOperations:
    """Handles all file loading, saving, and export operations."""
    
    def __init__(self, app_controller):
        """Initialize FileOperations with a reference to the main application controller."""
        self.app = app_controller
        logger.debug("FileOperations initialized")

    def load_html(self):
        """Load and parse an HTML warnings file from Revit."""
        file_path = filedialog.askopenfilename(
            title="Select Revit HTML file",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            logger.info(f"Loading HTML file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            # Parse the HTML content
            self.app.warnings_data = HTMLParser.parse(html_content)

            # Set default JSON save path
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.app.json_file_path = os.path.join(os.path.dirname(file_path), f"{base_name}_warnings.json")

            # Update UI
            self.app.events.update_tree()
            self.app.warnings_info_label.config(text=f"Loaded {len(self.app.warnings_data)} warnings from HTML")

            # Auto-save as JSON
            self.save_json()
            logger.info(f"Successfully loaded and parsed HTML file with {len(self.app.warnings_data)} warnings")

        except Exception as e:
            ErrorHandler.show_error("Error loading HTML", f"Error loading HTML file:\n{str(e)}")
            logger.error(f"HTML loading error: {e}", exc_info=True)

    def load_json(self):
        """Load existing JSON file with warnings data."""
        file_path = filedialog.askopenfilename(
            title="Select JSON file for warnings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            logger.info(f"Loading JSON file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                self.app.warnings_data = json.load(file)
            
            self.app.json_file_path = file_path
            self.app.events.update_tree()
            self.app.warnings_info_label.config(text=f"Loaded {len(self.app.warnings_data)} warnings from JSON")
            logger.info(f"Successfully loaded JSON file with {len(self.app.warnings_data)} warnings")
            
        except Exception as e:
            ErrorHandler.show_error("Error", f"Error loading JSON file:\n{str(e)}")
            logger.error(f"JSON loading error: {e}", exc_info=True)
    
    def save_json(self):
        """Save warnings data in JSON format."""
        if not self.app.warnings_data:
            ErrorHandler.show_warning("Warning", "No data to save")
            return
        
        if not self.app.json_file_path:
            self.app.json_file_path = filedialog.asksaveasfilename(
                title="Save JSON file",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        
        if not self.app.json_file_path:
            return
        
        try:
            logger.info(f"Saving JSON file: {self.app.json_file_path}")
            with open(self.app.json_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.app.warnings_data, file, indent=2, ensure_ascii=False)
            
            self.app.warnings_info_label.config(text=f"JSON file saved: {os.path.basename(self.app.json_file_path)}")
            logger.info(f"Successfully saved {len(self.app.warnings_data)} warnings to JSON")
            
        except Exception as e:
            ErrorHandler.show_error("Error", f"Error saving JSON file:\n{str(e)}")
            logger.error(f"JSON saving error: {e}", exc_info=True)

    def analyze_journal(self):
        """Analyze a Revit journal file for potential problems."""
        file_path = filedialog.askopenfilename(
            title="Select Revit Journal file", 
            filetypes=[("Journal files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            logger.info(f"Analyzing journal file: {file_path}")
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                content = file.read()
                
            # Find problems in the journal
            finder = JournalProblemFinder()
            self.app.journal_problems = finder.find_problems(content)
            
            # Update UI
            self.app.events.update_journal_tree()
            self.app.journal_info_label.config(text=f"Found {len(self.app.journal_problems)} potential problems.")
            logger.info(f"Found {len(self.app.journal_problems)} problems in journal file")
            
        except UnicodeDecodeError as e:
            ErrorHandler.show_error("Error analyzing journal", f"Unicode decoding error: {e}")
            logger.error(f"Journal analysis Unicode error: {e}")
        except Exception as e:
            ErrorHandler.show_error("Error analyzing journal", str(e))
            logger.error(f"Journal analysis error: {e}", exc_info=True)
    
    def load_journal_file(self, file_path=None):
        """Load and parse a Revit journal file with model information."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select Revit Journal file", 
                filetypes=[("Journal files", "*.txt"), ("All files", "*.*")]
            )
        
        if not file_path:
            return
            
        try:
            logger.info(f"Loading journal file: {file_path}")
            parser = JournalParser()
            self.app.journal_data = parser.parse_journal_with_models(file_path)

            if not self.app.journal_data or not isinstance(self.app.journal_data, dict):
                if hasattr(self.app, 'journal_info_label') and self.app.journal_info_label:
                    self.app.journal_info_label.config(text="Failed to load journal file.")
                logger.error("Failed to load journal file: Invalid data format")
                return

            # Update header information
            if hasattr(self.app, 'header_vars'):
                for key, var in self.app.header_vars.items():
                    var.set(f"{key.capitalize()}: {self.app.journal_data.get('header', {}).get(key, 'Unknown')}")

            # Update model selector
            if hasattr(self.app, 'model_selector'):
                self.app.model_selector['values'] = self.app.journal_data.get('models', [])
                self.app.model_selector.current(0)
                
                # Apply filter for "All models"
                if hasattr(self.app.events, 'filter_journal_by_model'):
                    self.app.events.filter_journal_by_model("All models")

            # Load worker log if available
            worker_log_path = file_path.replace("journal", "worker1.log")
            self.load_worker_log(worker_log_path)
            
            # Update UI
            if hasattr(self.app, 'journal_info_label'):
                self.app.journal_info_label.config(
                    text=f"Loaded journal file: {os.path.basename(file_path)}"
                )
            
            logger.info(f"Successfully loaded journal file with {len(self.app.journal_data.get('models', []))-1} models")
            
        except Exception as e:
            ErrorHandler.show_error("Journal Loading Error", f"Failed to load journal file:\n{str(e)}")
            logger.error(f"Journal loading error: {e}", exc_info=True)

    def load_worker_log(self, file_path=None):
        """Load and parse a Revit worker log file."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select Worker Log file", 
                filetypes=[("Log files", "*.log"), ("All files", "*.*")]
            )
        
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Worker log file not found: {file_path}")
            return
        
        try:
            logger.info(f"Loading worker log file: {file_path}")
            parser = WorkerLogParser()
            self.app.worker_log_data = parser.parse_worker_log(file_path)

            if not self.app.worker_log_data or not isinstance(self.app.worker_log_data, dict):
                if hasattr(self.app, 'journal_info_label') and self.app.journal_info_label:
                    self.app.journal_info_label.config(text="Failed to load worker log file.")
                logger.error("Failed to load worker log file: Invalid data format")
                return

            # Update worker log information
            self.app.worker_log_entries = self.app.worker_log_data.get('entries', [])
            
            # Update UI
            if hasattr(self.app.events, 'update_worker_log_view'):
                self.app.events.update_worker_log_view()
                
            # Update info label
            if hasattr(self.app, 'journal_info_label'):
                current_text = self.app.journal_info_label.cget("text")
                self.app.journal_info_label.config(
                    text=f"{current_text} | Worker log: {len(self.app.worker_log_entries)} entries"
                )
                
            logger.info(f"Successfully loaded worker log with {len(self.app.worker_log_entries)} entries")
            
        except Exception as e:
            ErrorHandler.show_error("Worker Log Error", f"Failed to load worker log file:\n{str(e)}")
            logger.error(f"Worker log loading error: {e}", exc_info=True)
            
    def scan_revit_journals(self):
        """
        Scan Revit AppData directories for journal files.
        Returns a dictionary with Revit versions as keys and list of journal files as values.
        """
        import glob
        
        # Get the user's AppData directory
        appdata_path = os.path.expanduser(r"~\AppData\Local\Autodesk\Revit")
        
        if not os.path.exists(appdata_path):
            logger.warning(f"Revit AppData path not found: {appdata_path}")
            return {}
        
        journals_by_version = {}
        
        try:
            # Scan for Revit version directories
            for item in os.listdir(appdata_path):
                item_path = os.path.join(appdata_path, item)
                
                # Check if it's a directory and starts with "Autodesk Revit"
                if os.path.isdir(item_path) and item.startswith("Autodesk Revit"):
                    journals_dir = os.path.join(item_path, "Journals")
                    
                    if os.path.exists(journals_dir):
                        # Find all journal .txt files
                        journal_files = glob.glob(os.path.join(journals_dir, "journal*.txt"))
                        
                        if journal_files:
                            # Sort by modification time (newest first)
                            journal_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                            journals_by_version[item] = journal_files
                            logger.debug(f"Found {len(journal_files)} journals in {item}")
            
            logger.info(f"Scanned {len(journals_by_version)} Revit versions with journals")
            return journals_by_version
            
        except Exception as e:
            logger.error(f"Error scanning Revit journals: {e}", exc_info=True)
            return {}
    
    def scan_revit_cleanable_areas(self):
        """
        Scan Revit AppData directories for cleanable areas.
        Returns a dictionary with version info and cleanable areas with their sizes.
        """
        import glob
        
        roaming_path = os.path.expanduser(r"~\AppData\Roaming\Autodesk\Revit")
        local_path = os.path.expanduser(r"~\AppData\Local\Autodesk\Revit")
        
        cleanable_by_version = {}
        
        try:
            # Get all Revit versions from both directories
            all_versions = set()
            
            for base_path in [roaming_path, local_path]:
                if os.path.exists(base_path):
                    for item in os.listdir(base_path):
                        item_path = os.path.join(base_path, item)
                        if os.path.isdir(item_path) and item.startswith("Autodesk Revit"):
                            all_versions.add(item)
            
            # For each version, scan cleanable areas
            for version in sorted(all_versions):
                roaming_version_path = os.path.join(roaming_path, version)
                local_version_path = os.path.join(local_path, version)
                
                cleanable_areas = []
                
                # ROAMING areas
                if os.path.exists(roaming_version_path):
                    # 1. Recent Files (from Revit.ini)
                    ini_path = os.path.join(roaming_version_path, "Revit.ini")
                    if os.path.exists(ini_path):
                        recent_count = self._count_recent_files(ini_path)
                        cleanable_areas.append({
                            'name': 'Recent Files',
                            'type': 'ini_section',
                            'path': ini_path,
                            'count': recent_count,
                            'size': 0,  # No actual files, just ini entries
                            'description': f'{recent_count} recent file entries in Revit.ini'
                        })
                    
                    # 2. Recent File Cache
                    cache_path = os.path.join(roaming_version_path, "RecentFileCache")
                    if os.path.exists(cache_path):
                        size, count = self._get_folder_size(cache_path)
                        cleanable_areas.append({
                            'name': 'Recent File Cache',
                            'type': 'folder',
                            'path': cache_path,
                            'count': count,
                            'size': size,
                            'description': f'{count} cached files, {self._format_size(size)}'
                        })
                    
                    # 3. Workset Configurations (from Revit.ini)
                    if os.path.exists(ini_path):
                        workset_count = self._count_workset_configs(ini_path)
                        cleanable_areas.append({
                            'name': 'Workset Configurations',
                            'type': 'ini_section',
                            'path': ini_path,
                            'count': workset_count,
                            'size': 0,
                            'description': f'{workset_count} workset configurations in Revit.ini'
                        })
                    
                    # 4. UI Configuration Files
                    ui_files = []
                    for ui_file in ['KeyboardShortcuts.xml', 'RevitUILayout.xml', 'MaterialUIConfig.xml']:
                        ui_file_path = os.path.join(roaming_version_path, ui_file)
                        if os.path.exists(ui_file_path):
                            ui_files.append(ui_file_path)
                    
                    if ui_files:
                        total_size = sum(os.path.getsize(f) for f in ui_files)
                        cleanable_areas.append({
                            'name': 'UI Configuration Files',
                            'type': 'files',
                            'path': roaming_version_path,
                            'files': ui_files,
                            'count': len(ui_files),
                            'size': total_size,
                            'description': f'{len(ui_files)} UI config files, {self._format_size(total_size)}'
                        })
                
                # LOCAL areas
                if os.path.exists(local_version_path):
                    # 5. CefCache
                    cef_path = os.path.join(local_version_path, "CefCache")
                    if os.path.exists(cef_path):
                        size, count = self._get_folder_size(cef_path)
                        cleanable_areas.append({
                            'name': 'CefCache',
                            'type': 'folder',
                            'path': cef_path,
                            'count': count,
                            'size': size,
                            'description': f'Chrome cache: {count} files, {self._format_size(size)}'
                        })
                    
                    # 6. CollaborationCache
                    collab_path = os.path.join(local_version_path, "CollaborationCache")
                    if os.path.exists(collab_path):
                        size, count = self._get_folder_size(collab_path)
                        cleanable_areas.append({
                            'name': 'CollaborationCache',
                            'type': 'folder',
                            'path': collab_path,
                            'count': count,
                            'size': size,
                            'description': f'Collaboration cache: {count} files, {self._format_size(size)}'
                        })
                    
                    # 7. Product Feedback
                    feedback_path = os.path.join(local_version_path, "Product Feedback")
                    if os.path.exists(feedback_path):
                        size, count = self._get_folder_size(feedback_path)
                        cleanable_areas.append({
                            'name': 'Product Feedback',
                            'type': 'folder',
                            'path': feedback_path,
                            'count': count,
                            'size': size,
                            'description': f'Feedback data: {count} files, {self._format_size(size)}'
                        })
                
                if cleanable_areas:
                    cleanable_by_version[version] = cleanable_areas
                    logger.debug(f"Found {len(cleanable_areas)} cleanable areas in {version}")
            
            logger.info(f"Scanned {len(cleanable_by_version)} Revit versions for cleaning")
            return cleanable_by_version
            
        except Exception as e:
            logger.error(f"Error scanning cleanable areas: {e}", exc_info=True)
            return {}
    
    def _get_folder_size(self, folder_path):
        """Calculate total size and file count of a folder."""
        total_size = 0
        file_count = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                        file_count += 1
                    except (OSError, FileNotFoundError):
                        pass
        except Exception as e:
            logger.warning(f"Error calculating folder size for {folder_path}: {e}")
        
        return total_size, file_count
    
    def _format_size(self, size_bytes):
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _count_recent_files(self, ini_path):
        """Count recent file entries in Revit.ini."""
        count = 0
        try:
            # Revit.ini is typically UTF-16 LE encoded
            with open(ini_path, 'r', encoding='utf-16-le', errors='ignore') as f:
                content = f.read()
                # Count ALL File{N}= entries (don't break on gaps)
                for i in range(1, 100):  # Check up to 100 to be safe
                    if f"File{i}=" in content:
                        count += 1
            logger.debug(f"Found {count} recent files in {ini_path}")
        except Exception as e:
            logger.warning(f"Error counting recent files in {ini_path}: {e}")
        return count
    
    def _count_workset_configs(self, ini_path):
        """Count workset configuration entries in Revit.ini."""
        count = 0
        try:
            # Revit.ini is typically UTF-16 LE encoded
            with open(ini_path, 'r', encoding='utf-16-le', errors='ignore') as f:
                content = f.read()
                # Count Config1, Config2, ... entries
                for i in range(1, 100):  # Check up to 100
                    if f"Config{i}=" in content:
                        count += 1
            logger.debug(f"Found {count} workset configs in {ini_path}")
        except Exception as e:
            logger.warning(f"Error counting workset configs: {e}")
        return count
    
    def load_file(self):
        """Open a file dialog to load a journal or worker log file."""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Log Files", "*.log"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            if file_path.endswith(".txt"):
                self.load_journal_file(file_path)
            elif file_path.endswith(".log"):
                self.load_worker_log(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path}")

    def export_journal_filtered(self):
        """Export currently filtered journal entries to a text file."""
        if not hasattr(self.app, 'journal_data') or not self.app.journal_data:
            ErrorHandler.show_warning("Warning", "No journal data to export")
            return
        
        # Get currently visible items
        visible_items = []
        if hasattr(self.app, 'journal_tree'):
            for item_id in self.app.journal_tree.get_children():
                values = self.app.journal_tree.item(item_id, "values")
                visible_items.append({
                    "timestamp": values[0] if len(values) > 0 else None,
                    "category": values[1] if len(values) > 1 else None,
                    "command": values[2] if len(values) > 2 else None,
                    "content": values[3] if len(values) > 3 else None
                })
        
        if not visible_items:
            ErrorHandler.show_warning("Warning", "No entries to export")
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Export Filtered Journal",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            logger.info(f"Exporting filtered journal to: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                # Include export timestamp
                f.write(f"# Journal Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # Include model information
                if hasattr(self.app, 'journal_models') and self.app.journal_models:
                    f.write(f"# Models found in journal: {len(self.app.journal_models)}\n")
                    for i, model in enumerate(self.app.journal_models):
                        model_path = model.get("path", "Unknown")
                        model_server = model.get("server", "Unknown")
                        model_username = model.get("username", "Unknown")
                        f.write(f"# Model {i+1}: {model_path}\n")
                        f.write(f"#    Server: {model_server}\n")
                        f.write(f"#    User: {model_username}\n")
                
                # Include filter information
                f.write(f"# Filtered by:\n")
                if hasattr(self.app, 'journal_filter'):
                    f.write(f"#    Category: {self.app.journal_filter.get()}\n")
                
                if hasattr(self.app, 'journal_search_var') and self.app.journal_search_var.get():
                    f.write(f"#    Search: \"{self.app.journal_search_var.get()}\"\n")
                
                if hasattr(self.app, 'time_range_var') and self.app.time_range_var.get() != "All":
                    f.write(f"#    Time Range: {self.app.time_range_var.get()}\n")
                    
                if hasattr(self.app, 'filter_selected_model_var') and self.app.filter_selected_model_var.get():
                    selected_index = self.app.model_selector.current()
                    if hasattr(self.app, 'journal_models') and selected_index >= 0 and selected_index < len(self.app.journal_models):
                        model_path = self.app.journal_models[selected_index].get("path", "Unknown")
                        f.write(f"#    Model: {model_path}\n")
                
                # Include statistics
                if hasattr(self.app.events, 'get_journal_category_stats'):
                    category_stats = self.app.events.get_journal_category_stats()
                    if category_stats:
                        f.write("\n# JOURNAL STATISTICS\n")
                        for category, count in category_stats.items():
                            f.write(f"#    {category}: {count} entries\n")
                
                f.write("\n# JOURNAL ENTRIES\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"# Filtered Journal Export - {datetime.now()}\n")
                f.write(f"# Total entries: {len(visible_items)}\n\n")
                
                for entry in visible_items:
                    timestamp = entry["timestamp"] if entry["timestamp"] else ""
                    category = entry["category"] if entry["category"] else ""
                    command = entry["command"] if entry["command"] else ""
                    content = entry["content"] if entry["content"] else ""
                    
                    if timestamp and category:
                        f.write(f"[{timestamp}] [{category}]")
                        if command:
                            f.write(f" [{command}]")
                        f.write(f": {content}\n")
                    else:
                        f.write(f"{content}\n")
            
            if hasattr(self.app, 'journal_info_label'):
                self.app.journal_info_label.config(text=f"Exported {len(visible_items)} entries to {os.path.basename(file_path)}")
            logger.info(f"Successfully exported {len(visible_items)} journal entries")
            
        except Exception as e:
            ErrorHandler.show_error("Export Error", f"Failed to export journal data:\n{str(e)}")
            logger.error(f"Journal export error: {e}", exc_info=True)
