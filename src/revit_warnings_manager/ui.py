"""
This module handles the user interface setup for the Revit Warnings Manager.
"""
import os
import tkinter as tk
from tkinter import ttk
from loguru import logger

class UIManager:
    """Manages the creation and layout of all UI components."""
    def __init__(self, app_controller):
        self.app = app_controller
        self.root = self.app.root

    def setup_ui(self):
        """Sets up the main UI, including notebook and tabs."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.setup_warnings_tab()
        self.setup_journal_tab()
        self.setup_cleaning_tab()

    def setup_warnings_tab(self):
        """Sets up the 'Warnings' tab with all its widgets."""
        warnings_frame = ttk.Frame(self.notebook)
        self.notebook.add(warnings_frame, text="Warnings")
        warnings_frame.columnconfigure(1, weight=1)
        warnings_frame.rowconfigure(2, weight=1)

        # Control buttons
        control_frame = ttk.Frame(warnings_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
        ttk.Button(control_frame, text="Load HTML", command=self.app.files.load_html).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Load JSON", command=self.app.files.load_json).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Save JSON", command=self.app.files.save_json).pack(side=tk.LEFT, padx=(0, 10))

        # Filter frame
        filter_frame = ttk.LabelFrame(warnings_frame, text="Filters", padding="5")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 10))

        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.status_filter = ttk.Combobox(filter_frame, values=["All", "Open", "In Review", "Close"], 
                                             state="readonly", width=10)
        self.app.status_filter.set("All")
        self.app.status_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.app.status_filter.bind('<<ComboboxSelected>>', self.app.events.apply_filter)

        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.search_var = tk.StringVar()
        self.app.search_entry = ttk.Entry(filter_frame, textvariable=self.app.search_var, width=30)
        self.app.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.app.search_var.trace('w', self.app.events.apply_filter)

        # Checkbox for grouped view
        self.app.group_mode = tk.BooleanVar(value=True)
        self.app.group_checkbox = ttk.Checkbutton(filter_frame, text="Grouped View", 
                                                variable=self.app.group_mode, command=self.app.events.toggle_group_mode)
        self.app.group_checkbox.pack(side=tk.LEFT, padx=(20, 10))

        # Expand/Collapse buttons
        ttk.Button(filter_frame, text="Expand All", command=self.app.events.expand_all).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(filter_frame, text="Collapse All", command=self.app.events.collapse_all).pack(side=tk.RIGHT, padx=(5, 0))

        # Treeview for warnings
        tree_frame = ttk.Frame(warnings_frame)
        tree_frame.grid(row=2, column=0, columnspan=2, sticky="wens")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Columns for the treeview
        columns = ("Count", "Status", "Message", "IDs")
        self.app.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=25)

        # Column configuration
        self.app.tree.heading("#0", text="Warning")
        self.app.tree.heading("Count", text="Count")
        self.app.tree.heading("Status", text="Status")
        self.app.tree.heading("Message", text="Message")
        self.app.tree.heading("IDs", text="IDs")

        self.app.tree.column("#0", width=200)
        self.app.tree.column("Count", width=50)
        self.app.tree.column("Status", width=80)
        self.app.tree.column("Message", width=500)
        self.app.tree.column("IDs", width=200)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.app.tree.yview)
        self.app.tree.configure(yscrollcommand=scrollbar.set)

        self.app.tree.grid(row=0, column=0, sticky="wens")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind events
        self.app.tree.bind("<Button-3>", self.app.events.on_tree_right_click)  # Right click to copy IDs
        self.app.tree.bind("<Double-1>", self.app.events.on_tree_double_click)  # Double click for details

        # Info label for Warnings
        self.app.warnings_info_label = ttk.Label(warnings_frame, text="Load an HTML or JSON file to start")
        self.app.warnings_info_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))

    def setup_journal_tab(self):
        """Setup the Journal tab with sidebar for journal selection and main content area."""
        journal_tab = ttk.Frame(self.notebook)
        self.notebook.add(journal_tab, text="Journal")

        # Main container with sidebar and content area
        main_container = ttk.PanedWindow(journal_tab, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT SIDEBAR - Journal browser
        sidebar_frame = ttk.Frame(main_container, width=300)
        main_container.add(sidebar_frame, weight=0)

        # Sidebar title
        ttk.Label(sidebar_frame, text="Revit Journals", font=("Arial", 10, "bold")).pack(padx=5, pady=5)

        # Journal tree
        journal_sidebar_frame = ttk.Frame(sidebar_frame)
        journal_sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.app.journals_tree = ttk.Treeview(journal_sidebar_frame, show="tree")
        journals_scrollbar = ttk.Scrollbar(journal_sidebar_frame, orient=tk.VERTICAL, command=self.app.journals_tree.yview)
        self.app.journals_tree.configure(yscrollcommand=journals_scrollbar.set)

        self.app.journals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        journals_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load selected journal button
        ttk.Button(sidebar_frame, text="► Load Selected", command=self.load_selected_journal, width=15).pack(padx=5, pady=5)

        # Refresh journals button
        ttk.Button(sidebar_frame, text="🔄 Refresh", command=self.refresh_journals_tree, width=15).pack(padx=5, pady=(0, 5))

        # RIGHT CONTENT AREA
        content_frame = ttk.Frame(main_container)
        main_container.add(content_frame, weight=1)

        # Top controls frame (Load File button + Filters)
        top_controls_frame = ttk.Frame(content_frame)
        top_controls_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        # Load external file button
        ttk.Button(top_controls_frame, text="Load External File", command=self.app.files.load_file, width=18).pack(side=tk.LEFT, padx=(0, 20))

        # Journal Filters on the same row
        ttk.Label(top_controls_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.journal_filter = ttk.Combobox(top_controls_frame, values=["All", "Control", "Header", "Event", "Command", "Journal", "Comment", "Unknown", "Error", "BIG GAP", "Performance", "Model"], state="readonly", width=12)
        self.app.journal_filter.set("All")
        self.app.journal_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.app.journal_filter.bind('<<ComboboxSelected>>', self.app.events.apply_journal_filter)

        ttk.Label(top_controls_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.journal_search_var = tk.StringVar()
        journal_search_entry = ttk.Entry(top_controls_frame, textvariable=self.app.journal_search_var, width=20)
        journal_search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.app.journal_search_var.trace('w', self.app.events.apply_journal_filter)

        ttk.Label(top_controls_frame, text="Time:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.time_range_var = tk.StringVar(value="All")
        time_combo = ttk.Combobox(top_controls_frame, textvariable=self.app.time_range_var, values=["All", "Last 15 min", "Last 1 hour"], state="readonly", width=12)
        time_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.app.time_range_var.trace('w', self.app.events.apply_journal_filter)

        self.app.filter_selected_model_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top_controls_frame, text="Filter by Model", variable=self.app.filter_selected_model_var, command=self.app.events.apply_journal_filter).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top_controls_frame, text="Clear", command=self.app.events.clear_text_filter).pack(side=tk.LEFT)

        # Header Information
        header_frame = ttk.LabelFrame(content_frame, text="Header Information")
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        self.app.header_vars = {
            'build': tk.StringVar(value="Build: Unknown"),
            'branch': tk.StringVar(value="Branch: Unknown"),
            'release': tk.StringVar(value="Release: Unknown"),
            'username': tk.StringVar(value="Username: Unknown")
        }

        for i, (key, var) in enumerate(self.app.header_vars.items()):
            ttk.Label(header_frame, textvariable=var).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # Model Selector
        model_frame = ttk.LabelFrame(content_frame, text="Models")
        model_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(model_frame, text="Select Model:").pack(side=tk.LEFT, padx=5)
        self.app.model_selector = ttk.Combobox(model_frame, state="readonly")
        self.app.model_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.app.model_selector.bind("<<ComboboxSelected>>", self.app.events.on_model_selected_event)

        # Treeview for Journal Entries
        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.app.journal_tree = ttk.Treeview(tree_frame, columns=("Timestamp", "Category", "Content"), show="headings")
        self.app.journal_tree.heading("Timestamp", text="Timestamp")
        self.app.journal_tree.heading("Category", text="Category")
        self.app.journal_tree.heading("Content", text="Content")

        self.app.journal_tree.column("Timestamp", width=150)
        self.app.journal_tree.column("Category", width=100)
        self.app.journal_tree.column("Content", width=500)

        self.app.journal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.app.journal_tree.yview)
        self.app.journal_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click for journal entry details
        self.app.journal_tree.bind("<Double-1>", self.app.events.show_journal_entry_details)

        # Journal Info Label
        self.app.journal_info_label = ttk.Label(content_frame, text="No journal loaded.")
        self.app.journal_info_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Initialize journals tree on startup
        self.refresh_journals_tree()

    def load_selected_journal(self):
        """Load the selected journal from the sidebar tree."""
        selection = self.app.journals_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        # Check if it's a journal file (not a version folder)
        parent = self.app.journals_tree.parent(item)
        
        if parent:  # It's a journal file
            # Get the file path stored in the tree
            file_path = self.app.journals_tree.item(item, "values")
            if file_path and len(file_path) > 0:
                self.app.files.load_journal_file(file_path[0])
    
    def refresh_journals_tree(self):
        """Scan and refresh the journals tree."""
        # Clear existing tree
        for item in self.app.journals_tree.get_children():
            self.app.journals_tree.delete(item)
        
        # Scan for journals
        journals_by_version = self.app.files.scan_revit_journals()
        
        if not journals_by_version:
            self.app.journals_tree.insert("", "end", text="No journals found", values=())
            return
        
        # Populate tree
        for version, journals in journals_by_version.items():
            # Add version as parent
            version_node = self.app.journals_tree.insert("", "end", text=f"{version} ({len(journals)} journals)", values=())
            
            # Add journals as children
            for journal_path in journals:
                journal_name = os.path.basename(journal_path)
                # Get file modification time
                try:
                    mod_time = os.path.getmtime(journal_path)
                    from datetime import datetime
                    mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                    display_text = f"{journal_name} - {mod_date}"
                except:
                    display_text = journal_name
                
                self.app.journals_tree.insert(version_node, "end", text=display_text, values=(journal_path,))

    def setup_cleaning_tab(self):
        """Setup the Cleaning tab with sidebar for version selection and cleaning operations."""
        cleaning_tab = ttk.Frame(self.notebook)
        self.notebook.add(cleaning_tab, text="Cleaning")

        # Main container with sidebar and content area
        main_container = ttk.PanedWindow(cleaning_tab, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT SIDEBAR - Revit versions and cleanable areas
        sidebar_frame = ttk.Frame(main_container, width=350)
        main_container.add(sidebar_frame, weight=0)

        # Sidebar title
        title_frame = ttk.Frame(sidebar_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(title_frame, text="Cleanable Areas", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ttk.Button(title_frame, text="🔄", command=self.refresh_cleaning_tree, width=3).pack(side=tk.RIGHT)

        # Cleaning tree
        cleaning_sidebar_frame = ttk.Frame(sidebar_frame)
        cleaning_sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.app.cleaning_tree = ttk.Treeview(cleaning_sidebar_frame, show="tree", selectmode="extended")
        cleaning_scrollbar = ttk.Scrollbar(cleaning_sidebar_frame, orient=tk.VERTICAL, command=self.app.cleaning_tree.yview)
        self.app.cleaning_tree.configure(yscrollcommand=cleaning_scrollbar.set)

        self.app.cleaning_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cleaning_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.app.cleaning_tree.bind("<<TreeviewSelect>>", self.on_cleaning_selection)

        # RIGHT CONTENT AREA
        content_frame = ttk.Frame(main_container)
        main_container.add(content_frame, weight=1)

        # Title area
        ttk.Label(content_frame, text="Cleaning Details", font=("Arial", 12, "bold")).pack(padx=10, pady=(10, 5))

        # Details frame
        details_frame = ttk.LabelFrame(content_frame, text="Selected Area Information", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.app.cleaning_info_text = tk.Text(details_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        cleaning_info_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.app.cleaning_info_text.yview)
        self.app.cleaning_info_text.configure(yscrollcommand=cleaning_info_scrollbar.set)

        self.app.cleaning_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cleaning_info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons frame
        action_frame = ttk.Frame(content_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        # Backup option
        self.app.backup_before_clean = tk.BooleanVar(value=True)
        ttk.Checkbutton(action_frame, text="💾 Backup before cleaning", variable=self.app.backup_before_clean).pack(side=tk.LEFT, padx=(0, 20))

        # Action buttons
        ttk.Button(action_frame, text="🗑️ Clean Selected", command=self.clean_selected_area, width=20).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="🧹 Clean All (Version)", command=self.clean_all_version, width=20).pack(side=tk.RIGHT, padx=5)

        # Status label
        self.app.cleaning_status_label = ttk.Label(content_frame, text="Select an area to see details", foreground="gray")
        self.app.cleaning_status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Initialize cleaning tree on startup
        self.refresh_cleaning_tree()
    
    def refresh_cleaning_tree(self):
        """Scan and refresh the cleaning tree with all cleanable areas."""
        # Clear existing tree
        for item in self.app.cleaning_tree.get_children():
            self.app.cleaning_tree.delete(item)
        
        # Scan for cleanable areas
        cleanable_data = self.app.files.scan_revit_cleanable_areas()
        
        if not cleanable_data:
            self.app.cleaning_tree.insert("", "end", text="No Revit installations found", values=())
            return
        
        # Store the data for later use
        self.app.cleanable_data = cleanable_data
        
        # Populate tree
        for version, areas in cleanable_data.items():
            # Calculate total size for this version
            total_size = sum(area['size'] for area in areas)
            total_count = sum(area['count'] for area in areas)
            
            # Add version as parent
            version_text = f"{version} ({len(areas)} areas, {total_count} items, {self.app.files._format_size(total_size)})"
            version_node = self.app.cleaning_tree.insert("", "end", text=version_text, values=(version,), tags=('version',))
            
            # Add cleanable areas as children
            for i, area in enumerate(areas):
                area_text = f"{area['name']} - {area['description']}"
                self.app.cleaning_tree.insert(version_node, "end", text=area_text, values=(version, i), tags=('area',))
        
        logger.info(f"Cleaning tree refreshed with {len(cleanable_data)} Revit versions")
    
    def on_cleaning_selection(self, event):
        """Handle selection in the cleaning tree."""
        selection = self.app.cleaning_tree.selection()
        if not selection:
            return
        
        # Clear the info text
        self.app.cleaning_info_text.config(state=tk.NORMAL)
        self.app.cleaning_info_text.delete('1.0', tk.END)
        
        # Get selected item
        item = selection[0]
        values = self.app.cleaning_tree.item(item, "values")
        
        if not values:
            self.app.cleaning_info_text.config(state=tk.DISABLED)
            return
        
        # Check if it's a version or an area
        if len(values) == 1:  # It's a version
            version = values[0]
            if hasattr(self.app, 'cleanable_data') and version in self.app.cleanable_data:
                areas = self.app.cleanable_data[version]
                
                info = f"📁 {version}\n\n"
                info += f"Total cleanable areas: {len(areas)}\n"
                info += f"Total items: {sum(a['count'] for a in areas)}\n"
                info += f"Total size: {self.app.files._format_size(sum(a['size'] for a in areas))}\n\n"
                info += "Areas:\n"
                for area in areas:
                    info += f"  • {area['name']}: {area['description']}\n"
                
                self.app.cleaning_info_text.insert('1.0', info)
                self.app.cleaning_status_label.config(text=f"Selected: {version}", foreground="blue")
        
        elif len(values) == 2:  # It's a specific area
            version, area_index = values
            if hasattr(self.app, 'cleanable_data') and version in self.app.cleanable_data:
                area = self.app.cleanable_data[version][int(area_index)]
                
                info = f"📋 {area['name']}\n\n"
                info += f"Type: {area['type']}\n"
                info += f"Path: {area['path']}\n"
                info += f"Items: {area['count']}\n"
                info += f"Size: {self.app.files._format_size(area['size'])}\n\n"
                info += f"Description:\n{area['description']}\n\n"
                
                if area['type'] == 'folder':
                    info += f"\n⚠️ This will delete all files in:\n{area['path']}\n"
                elif area['type'] == 'ini_section':
                    info += f"\n⚠️ This will clear entries in:\n{area['path']}\n"
                elif area['type'] == 'files':
                    info += f"\n⚠️ This will delete {len(area['files'])} files:\n"
                    for f in area.get('files', [])[:10]:  # Show first 10
                        info += f"  • {os.path.basename(f)}\n"
                    if len(area.get('files', [])) > 10:
                        info += f"  ... and {len(area['files']) - 10} more\n"
                
                self.app.cleaning_info_text.insert('1.0', info)
                self.app.cleaning_status_label.config(text=f"Ready to clean: {area['name']}", foreground="orange")
        
        self.app.cleaning_info_text.config(state=tk.DISABLED)
    
    def clean_selected_area(self):
        """Clean the selected area."""
        # TODO: Implement cleaning logic
        logger.info("Clean selected area - to be implemented")
        if hasattr(self.app, 'cleaning_status_label'):
            self.app.cleaning_status_label.config(text="Cleaning functionality coming soon...", foreground="blue")
    
    def clean_all_version(self):
        """Clean all areas for the selected version."""
        # TODO: Implement cleaning logic
        logger.info("Clean all version - to be implemented")
        if hasattr(self.app, 'cleaning_status_label'):
            self.app.cleaning_status_label.config(text="Cleaning functionality coming soon...", foreground="blue")
