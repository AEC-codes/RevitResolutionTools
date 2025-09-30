"""
This module contains the parsing logic for HTML and Journal files.
"""
import re
import os
import urllib.parse
from datetime import datetime, timedelta
from tkinter import messagebox
from loguru import logger

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
    logger.info("BeautifulSoup4 imported successfully")
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None  # Definizione esplicita per evitare errori di binding
    logger.warning("BeautifulSoup4 is not available. HTML parsing will be limited.")

class ErrorHandler:
    """Handles error and warning messages for the application."""
    
    @staticmethod
    def show_error(title, message):
        """Display an error message box with the given title and message."""
        logger.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    @staticmethod
    def show_warning(title, message):
        """Display a warning message box with the given title and message."""
        logger.warning(f"{title}: {message}")
        messagebox.showwarning(title, message)

class HTMLParser:
    """Parser for HTML warning files exported from Revit."""
    
    @staticmethod
    def parse(html_content):
        """
        Parses the HTML content and extracts error messages and elements as lists.
        Returns a list of warning dicts with error message, elements, ids, and metadata.
        
        Args:
            html_content (str): The HTML content to parse.
            
        Returns:
            list: A list of dictionaries, each representing a warning with its associated metadata.
        """
        if not BS4_AVAILABLE:
            ErrorHandler.show_error("Error", "BeautifulSoup4 is not available.\n\nInstall it using:\npip install beautifulsoup4")
            return []

        # Se arriviamo qui, BeautifulSoup è disponibile
        try:
            logger.debug("Starting HTML parsing")
            # Usando import locale per evitare errori Pylance quando BS4_AVAILABLE=False
            from bs4 import BeautifulSoup as BS
            
            soup = BS(html_content, 'html.parser')
            table = soup.find('table')
            
            if table is None:
                ErrorHandler.show_error("Parsing Error", "Could not find a <table> in the HTML content.")
                return []

            warnings = []
            # Find_all è un metodo garantito per BeautifulSoup
            rows = table.find_all('tr')
            logger.debug(f"Found {len(rows) - 1} warning rows in the HTML table")
            
            for i, row in enumerate(rows[1:], 1):  # Skip header row
                cells = row.find_all('td')
                if len(cells) == 2:
                    error_message = cells[0].get_text(strip=True)
                    # Split elements by <br> and strip whitespace
                    raw_html = str(cells[1])
                    # Use BeautifulSoup to split by <br> tags
                    sub_soup = BS(raw_html, 'html.parser')
                    elements = [el.strip() for el in sub_soup.stripped_strings]
                    # Extract all ids from all elements
                    ids = []
                    for el in elements:
                        ids.extend(re.findall(r'id (\d+)', el))
                    
                    warning = {
                        "index": i,
                        "message": error_message,
                        "elements": elements,
                        "ids": ids,
                        "status": "Open",
                        "created_date": datetime.now().isoformat(),
                        "modified_date": datetime.now().isoformat()
                    }
                    warnings.append(warning)
            
            logger.info(f"Successfully parsed {len(warnings)} warnings from HTML")
            return warnings
        except Exception as e:
            ErrorHandler.show_error("Parsing Error", f"Error during HTML parsing:\n{str(e)}")
            logger.error(f"HTML parsing error: {e}", exc_info=True)
            return []

class JournalParser:
    """Parser for Revit journal files."""
    
    @staticmethod
    def parse_journal(file_path):
        """
        Parses a Revit journal file and categorizes lines based on their prefixes and important content.
        Returns a list of dictionaries with categorized data.
        
        Args:
            file_path (str): Path to the journal file to parse.
            
        Returns:
            list: A list of dictionaries containing categorized journal entries.
        """
        # Lista di codifiche da provare
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        last_exception = None
        
        # Prova diverse codifiche
        for encoding in encodings:
            parsed_data = []
            last_timestamp = ""  # Memorizzare l'ultimo timestamp trovato
            models_info = []  # Lista di modelli trovati
            current_model_info = {}  # Informazioni sul modello corrente
            current_command = ""  # Comando corrente
            
            try:
                logger.debug(f"Attempting to parse journal with {encoding} encoding")
                with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                    for line in file:
                        line = line.strip()
                        
                        # Extract timestamp for all lines if present
                        timestamp = ""
                        # Extract timestamp like "27-Sep-2025 13:08:35.485"
                        match = re.search(r"\d+-\w+-\d+ \d+:\d+:\d+\.\d+", line)
                        if match:
                            timestamp = match.group(0)
                            last_timestamp = timestamp
                        else:
                            # If no timestamp in this line, use the most recent timestamp
                            timestamp = last_timestamp
                        
                        # Determine primary category based on prefix
                        if line.startswith("'C"):
                            category = "Control"
                        elif line.startswith("'H"):
                            category = "Header"
                        elif line.startswith("'E"):
                            category = "Event"
                        elif line.startswith("Jrn.Command"):
                            category = "Command"
                            # Extract command details
                            command_match = re.search(r'Jrn\.Command\s+"([^"]+)"\s*,\s*"([^"]+)"', line)
                            if command_match:
                                current_command = f"{command_match.group(1)}: {command_match.group(2)}"
                        elif line.startswith("Jrn."):
                            category = "Journal"
                        elif line.startswith("'"):
                            category = "Comment"
                        else:
                            category = "Unknown"
                        
                        # Identify special categories based on content
                        if "BIG_GAP" in line or "!!!BIG_GAP" in line:
                            category = "BIG GAP"  # Performance indicator
                            # Extract gap time if available
                            gap_match = re.search(r'(\d+\.\d+)!!!', line)
                            if gap_match:
                                gap_time = gap_match.group(1)
                                line = f"BIG GAP: {gap_time} seconds - {line}"
                        elif "Unrecoverable error" in line:
                            category = "Error"  # Critical error
                        elif "exception" in line.lower():
                            category = "Error"  # Exception
                        elif "API_ERROR" in line:
                            category = "Error"  # API error
                        elif "Error posted" in line:
                            category = "Error"  # UI error message
                        elif "RAM Statistics" in line or "VM Statistics" in line:
                            category = "Performance"  # Memory usage
                        elif "Delta VM" in line or "Delta RAM" in line:
                            category = "Performance"  # Memory change
                        
                        # Extract model information - check for "ModelPath Created" lines
                        if "ModelPath Created" in line and "Path = " in line and ".rvt" in line:
                            # Create a new model info entry
                            current_model_info = {"timestamp": timestamp}
                            
                            # Extract path
                            path_match = re.search(r'Path = "([^"]+\.rvt)"', line)
                            if path_match:
                                model_path = path_match.group(1)
                                # URL decode the path to handle escaped characters
                                model_path = urllib.parse.unquote(model_path)
                                current_model_info["path"] = model_path
                            
                            # Extract region
                            region_match = re.search(r'Region = "([^"]+)"', line)
                            if region_match:
                                current_model_info["region"] = region_match.group(1)
                                
                            # Extract server info
                            server_match = re.search(r'Central server = "([^"]*)"', line)
                            if server_match:
                                current_model_info["server"] = server_match.group(1)
                                
                # Extract Is server path
                            server_path_match = re.search(r'Is server path = (\w+)', line)
                            if server_path_match:
                                is_server = server_path_match.group(1)
                                current_model_info["is_server_path"] = str(is_server.lower() == "true")
                            
                            # Add to models list if we have a valid path
                            if "path" in current_model_info:
                                # Make a copy to avoid reference issues
                                models_info.append(current_model_info.copy())
                                
                                # Also mark this line as special category
                                category = "Model"
                        # Extract user information if not already found
                        if "User's Name " in line:
                            user_match = re.search(r"User's Name ([^,]+),", line)
                            if user_match:
                                username = user_match.group(1)
                                # Add username to all model infos
                                for model in models_info:
                                    if "username" not in model:
                                        model["username"] = username
                        
                        # Create entry with all gathered information
                        entry = {
                            "category": category,
                            "content": line,
                            "timestamp": timestamp,
                            "command": current_command if category == "Command" else ""
                        }
                        
                        # Add model information if this is a model line
                        if category == "Model" and current_model_info:
                            # Convertire valori non stringa in stringa per evitare errori di tipo
                            model_info_copy = {}
                            for k, v in current_model_info.items():
                                model_info_copy[k] = str(v) if not isinstance(v, str) else v
                            entry["model_info"] = model_info_copy
                        
                        parsed_data.append(entry)
                        
                        # Reset command for next entries
                        if category == "Command":
                            current_command = ""
                
                logger.info(f"Successfully parsed journal with {encoding} encoding")
                return parsed_data  # Se la lettura ha successo, restituisci i dati
                
            except UnicodeDecodeError as ude:
                last_exception = ude
                logger.warning(f"Failed parsing with {encoding} encoding: {ude}")
                continue  # Prova la prossima codifica
            except Exception as e:
                last_exception = e
                logger.error(f"Error with {encoding} encoding: {e}")
                break  # Errore non relativo alla codifica, esci dal ciclo
        
        # Se arriviamo qui, nessuna codifica ha funzionato
        if last_exception:
            ErrorHandler.show_error("Journal Parsing Error", f"Failed to parse journal file:\n{str(last_exception)}")
            logger.error(f"Journal parsing failed with error: {last_exception}")
        else:
            ErrorHandler.show_error("Journal Parsing Error", "Failed to parse journal file with any encoding")
            logger.error("Journal parsing failed with all encodings")
        
        return []  # Restituisci una lista vuota in caso di errore

    @staticmethod
    def parse_journal_with_models(file_path):
        """
        Parses a Revit journal file, extracts models, and associates lines with models.
        Returns a dictionary with models and categorized lines.
        
        Args:
            file_path (str): Path to the journal file to parse.
            
        Returns:
            dict: A dictionary containing header info, models, and categorized lines.
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        last_exception = None
        
        for encoding in encodings:
            try:
                logger.debug(f"Attempting to parse journal with models using {encoding} encoding")
                with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                    lines = file.readlines()

                models = []
                model_handles = {}
                categorized_lines = []
                header_info = {}
                current_model = "All models"

                for line in lines:
                    line = line.strip()

                    # Extract header information
                    if "Build:" in line:
                        header_info['build'] = line.split('Build:')[1].strip()
                    elif "Branch:" in line:
                        header_info['branch'] = line.split('Branch:')[1].strip()
                    elif "Release:" in line:
                        header_info['release'] = line.split('Release:')[1].strip()
                    elif "Username" in line:
                        user_match = re.search(r'Username\s*,\s*"([^"]+)"', line)
                        if user_match:
                            header_info['username'] = user_match.group(1)
                        else:
                            header_info['username'] = "Unknown"

                    # Extract model information
                    if "ModelPath Created" in line:
                        model_match = re.search(r'Path = "([^"]+\.rvt)"', line)
                        if model_match:
                            model_path = urllib.parse.unquote(model_match.group(1))
                            models.append(model_path)
                            current_model = model_path

                    # Associate lines with models
                    handle_match = re.search(r'\(this=(0x[0-9A-Fa-f]+)\)', line)
                    if handle_match:
                        model_handles[handle_match.group(1)] = current_model

                    # Categorize lines with detailed logic (same as parse_journal)
                    timestamp_match = re.search(r'\d+-\w+-\d+ \d+:\d+:\d+\.\d+', line)
                    
                    # Determine primary category based on prefix
                    if line.startswith("'C"):
                        category = "Control"
                    elif line.startswith("'H"):
                        category = "Header"
                    elif line.startswith("'E"):
                        category = "Event"
                    elif line.startswith("Jrn.Command"):
                        category = "Command"
                    elif line.startswith("Jrn."):
                        category = "Journal"
                    elif line.startswith("'"):
                        category = "Comment"
                    else:
                        category = "Unknown"
                    
                    # Identify special categories based on content
                    if "BIG_GAP" in line or "!!!BIG_GAP" in line:
                        category = "BIG GAP"
                    elif "Unrecoverable error" in line:
                        category = "Error"
                    elif "exception" in line.lower():
                        category = "Error"
                    elif "API_ERROR" in line:
                        category = "Error"
                    elif "Error posted" in line:
                        category = "Error"
                    elif "RAM Statistics" in line or "VM Statistics" in line:
                        category = "Performance"
                    elif "Delta VM" in line or "Delta RAM" in line:
                        category = "Performance"
                    elif "ModelPath Created" in line:
                        category = "Model"
                    
                    categorized_lines.append({
                        'timestamp': timestamp_match.group(0) if timestamp_match else None,
                        'category': category,
                        'content': line,
                        'model': current_model
                    })

                logger.info(f"Successfully parsed journal with models, found {len(models)} models")
                # Assicuriamoci che 'header' sia sempre un dizionario di stringhe
                string_header = {}
                for key, value in header_info.items():
                    string_header[key] = str(value)
                
                return {
                    'header': string_header,
                    'models': ['All models'] + models,
                    'lines': categorized_lines
                }

            except Exception as e:
                last_exception = e
                logger.warning(f"Failed parsing journal with models using {encoding} encoding: {e}")
                continue

        if last_exception:
            logger.error(f"All encoding attempts failed for journal with models parsing: {last_exception}")
            raise RuntimeError("Failed to parse journal file") from last_exception

class WorkerLogParser:
    """Parser for worker log files generated by Revit."""

    @staticmethod
    def parse_worker_log(file_path):
        """
        Parse the worker log file and return structured data.
        
        Args:
            file_path (str): Path to the worker log file to parse.
            
        Returns:
            dict: A dictionary containing the parsed entries or None if parsing failed.
        """
        try:
            logger.debug(f"Starting parsing worker log: {file_path}")
            if not os.path.exists(file_path):
                logger.warning(f"Worker log file does not exist: {file_path}")
                return None
                
            with open(file_path, 'r') as file:
                lines = file.readlines()

            entries = []
            for line in lines:
                parts = line.strip().split(' ', 2)
                if len(parts) == 3:
                    timestamp, level, message = parts
                    entries.append({
                        'timestamp': timestamp,
                        'level': level,
                        'message': message
                    })

            logger.info(f"Successfully parsed {len(entries)} entries from worker log")
            return {'entries': entries}
        except Exception as e:
            logger.error(f"Error parsing worker log: {e}", exc_info=True)
            return None

class JournalProblemFinder:
    """
    Analyzes a Revit journal file to find potential problems.
    """
    def __init__(self, time_threshold_sec=10, ram_spike_mb=500):
        self.time_threshold_sec = time_threshold_sec
        self.ram_spike_mb = ram_spike_mb
        self.patterns = {
            "ERROR": re.compile(r"error|exception|fail|cannot", re.IGNORECASE),
            "API_WARNING": re.compile(r"API_WARNING"),
            "PERFORMANCE": re.compile(r"slightly off axis", re.IGNORECASE),
            "RESOURCE_SPIKE": re.compile(r"RAM:.*?Used \+(\d+) MB"),
            "TIMESTAMP": re.compile(r"^'C (\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2}\.\d{3});\s*(.*)")
        }
        logger.debug("JournalProblemFinder initialized")

    def find_problems(self, file_content):
        """
        Analyzes journal content to find problems.
        
        Args:
            file_content (str): Content of the journal file to analyze.
            
        Returns:
            list: A list of problems found in the journal.
        """
        problems = []
        last_timestamp = None
        
        logger.debug("Starting problem analysis in journal")
        line_count = 0
        for line in file_content.splitlines():
            line_count += 1
            # Check for timestamp to keep track of when issues occur
            timestamp_match = self.patterns["TIMESTAMP"].match(line)
            if timestamp_match:
                last_timestamp = timestamp_match.group(1)
                
            # Check for errors and warnings
            if self.patterns["ERROR"].search(line):
                problems.append({
                    "timestamp": last_timestamp or "Unknown",
                    "type": "Error",
                    "source": "Journal",
                    "description": line[:150] + ("..." if len(line) > 150 else "")
                })
                
            # Check for API warnings
            if self.patterns["API_WARNING"].search(line):
                problems.append({
                    "timestamp": last_timestamp or "Unknown",
                    "type": "API Warning",
                    "source": "Revit API",
                    "description": line[:150] + ("..." if len(line) > 150 else "")
                })
                
            # Check for performance issues
            if self.patterns["PERFORMANCE"].search(line):
                problems.append({
                    "timestamp": last_timestamp or "Unknown",
                    "type": "Performance",
                    "source": "Geometry",
                    "description": "Possible performance issue: " + line[:120] + ("..." if len(line) > 120 else "")
                })
                
            # Check for resource spikes
            resource_match = self.patterns["RESOURCE_SPIKE"].search(line)
            if resource_match:
                ram_spike = int(resource_match.group(1))
                if ram_spike > self.ram_spike_mb:
                    problems.append({
                        "timestamp": last_timestamp or "Unknown",
                        "type": "Resource Spike",
                        "source": "Memory Usage",
                        "description": f"RAM spike of {ram_spike} MB detected"
                    })
                    
        logger.info(f"Journal analysis complete. Found {len(problems)} problems in {line_count} lines")    
        return problems
