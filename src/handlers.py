"""
This module contains event handlers for the UI.
"""
from collections import defaultdict
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from loguru import logger

class EventHandlers:
    """
    Handles all UI events and updates for the application.
    Contains methods for filtering, tree manipulation, and context menus.
    """
    def __init__(self, app_controller):
        """Initialize with reference to the main app controller."""
        self.app = app_controller
        logger.debug("EventHandlers initialized")

    def apply_filter(self, *args):
        """Apply filters to the warnings tree (warnings tab)."""
        logger.debug("Applying filters to warnings tree")
        self.update_tree()

    def on_model_selected_event(self, event):
        """Handle model selection and filter journal entries."""
        selected_model = self.app.model_selector.get()
        self.filter_journal_by_model(selected_model)

    def filter_journal_by_model(self, selected_model):
        """Filter journal entries by selected model."""
        # Clear the treeview
        for item in self.app.journal_tree.get_children():
            self.app.journal_tree.delete(item)
        
        if not hasattr(self.app, 'journal_data') or not self.app.journal_data:
            return

        # Get all entries
        entries = self.app.journal_data.get('lines', [])
        
        # Filter by model if not "All models"
        if selected_model and selected_model != "All models":
            filtered_entries = [entry for entry in entries if entry.get('model') == selected_model]
        else:
            filtered_entries = entries

        # Populate the tree with filtered entries
        for entry in filtered_entries:
            values = (
                entry.get('timestamp', 'N/A'),
                entry.get('category', 'Unknown'),
                entry.get('content', '')[:100] + ('...' if len(entry.get('content', '')) > 100 else '')
            )
            self.app.journal_tree.insert("", tk.END, values=values)

    def toggle_group_mode(self):
        """Toggle between grouped view and flat list."""
        logger.debug(f"Toggling group mode: {self.app.group_mode.get()}")
        self.update_tree()

    def expand_all(self):
        """Expand all nodes in the tree."""
        logger.debug("Expanding all tree nodes")
        def expand_node(item):
            self.app.tree.item(item, open=True)
            for child in self.app.tree.get_children(item):
                expand_node(child)
        
        for item in self.app.tree.get_children():
            expand_node(item)

    def collapse_all(self):
        """Collapse all nodes in the tree."""
        logger.debug("Collapsing all tree nodes")
        def collapse_node(item):
            self.app.tree.item(item, open=False)
            for child in self.app.tree.get_children(item):
                collapse_node(child)
        
        for item in self.app.tree.get_children():
            collapse_node(item)

    def on_tree_right_click(self, event):
        """Handle right click to copy IDs."""
        item = self.app.tree.identify_row(event.y)
        if not item:
            return
            
        self.app.tree.selection_set(item)
        warning_or_group = self.get_warning_from_tree_item(item)
        
        if warning_or_group:
            if isinstance(warning_or_group, list):
                # It's a group of warnings
                all_ids = self.get_all_ids_from_group(warning_or_group)
                if all_ids:
                    ids_string = ", ".join(all_ids)
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(ids_string)
                    self.app.warnings_info_label.config(text=f"Group IDs copied ({len(all_ids)}): {ids_string[:50]}...")
                    logger.info(f"Copied {len(all_ids)} IDs from group to clipboard")
            else:
                # It's a single warning
                if warning_or_group["ids"]:
                    ids_string = ", ".join(warning_or_group["ids"])
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(ids_string)
                    self.app.warnings_info_label.config(text=f"IDs copied: {ids_string}")
                    logger.info(f"Copied IDs to clipboard: {ids_string}")

    def on_tree_double_click(self, event):
        """Handle double click on treeview to manage statuses."""
        selection = self.app.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        warning_or_group = self.get_warning_from_tree_item(item)
        
        if warning_or_group:
            if isinstance(warning_or_group, list):
                # It's a group - show group details
                self.show_group_details(warning_or_group)
            else:
                # It's a single warning - show details and status management
                self.show_warning_details(warning_or_group)
    
    def update_tree(self):
        """Update the warnings treeview with filtered data."""
        logger.debug("Updating warnings tree")
        
        # Clear the tree
        for item in self.app.tree.get_children():
            self.app.tree.delete(item)
        
        if not hasattr(self.app, 'warnings_data') or not self.app.warnings_data:
            logger.warning("No warnings data to display")
            return
            
        # Apply filters
        filtered_data = self.get_filtered_data()
        
        if hasattr(self.app, 'group_mode') and self.app.group_mode.get():
            self.populate_tree_grouped(filtered_data)
        else:
            self.populate_tree_flat(filtered_data)
            
        logger.info(f"Tree updated with {len(filtered_data)} warnings")
        
    def get_filtered_data(self):
        """Apply filters to the warnings data."""
        if not hasattr(self.app, 'warnings_data') or not self.app.warnings_data:
            return []
            
        filtered = self.app.warnings_data
        
        # Status filter
        if hasattr(self.app, 'status_filter'):
            status_filter = self.app.status_filter.get()
            if status_filter != "All":
                filtered = [w for w in filtered if w["status"] == status_filter]
        
        # Search filter
        if hasattr(self.app, 'search_var'):
            search_text = self.app.search_var.get().lower()
            if search_text:
                filtered = [w for w in filtered if search_text in w["message"].lower()]
        
        # Configure colors
        if hasattr(self.app, 'tree'):
            self.app.tree.tag_configure("open", background="#ffebee")
            self.app.tree.tag_configure("in_review", background="#fff3e0")
            self.app.tree.tag_configure("close", background="#e8f5e8")
        
        return filtered
        
    def group_warnings_by_message(self, warnings):
        """Group warnings by error message."""
        groups = defaultdict(list)
        for warning in warnings:
            groups[warning["message"]].append(warning)
        return dict(groups)
    
    def get_group_status_summary(self, warnings_group):
        """Calculate status summary for a group."""
        status_counts = defaultdict(int)
        for warning in warnings_group:
            status_counts[warning["status"]] += 1
        
        if status_counts["Open"] > 0:
            main_status = "Open"
        elif status_counts["In Review"] > 0:
            main_status = "In Review"
        else:
            main_status = "Close"
            
        summary_parts = []
        for status in ["Open", "In Review", "Close"]:
            if status_counts[status] > 0:
                summary_parts.append(f"{status}: {status_counts[status]}")
        
        return main_status, " | ".join(summary_parts)
    
    def get_all_ids_from_group(self, warnings_group):
        """Get all IDs from a group of warnings."""
        all_ids = []
        for warning in warnings_group:
            all_ids.extend(warning["ids"])
        return all_ids
    
    def get_status_tags(self, status):
        """Return tags for color coding based on status."""
        if status == "Open":
            return ("open",)
        elif status == "In Review":
            return ("in_review",)
        elif status == "Close":
            return ("close",)
        return ()
        
    def get_warning_from_tree_item(self, item):
        """Get the warning associated with a tree item."""
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return None
            
        values = self.app.tree.item(item, "values")
        if not values:
            return None
        
        # If it's a group, return all warnings in the group
        if hasattr(self.app, 'group_mode') and self.app.group_mode.get() and not self.app.tree.parent(item):
            # It's a parent node (group)
            text = self.app.tree.item(item, "text")
            # Find the corresponding group
            filtered_data = self.get_filtered_data()
            grouped = self.group_warnings_by_message(filtered_data)
            
            for message, warnings_group in grouped.items():
                group_text = f"{message[:80]}{'...' if len(message) > 80 else ''}"
                if group_text == text:
                    return warnings_group
            return None
        else:
            # It's a single warning
            try:
                index = int(values[0])
                return next((w for w in self.app.warnings_data if w["index"] == index), None)
            except (ValueError, IndexError):
                return None
    
    def populate_tree_grouped(self, filtered_data):
        """Populate the tree with grouped view."""
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
            
        grouped = self.group_warnings_by_message(filtered_data)
        
        for message, warnings_group in grouped.items():
            # Calculate group statistics
            group_status, status_summary = self.get_group_status_summary(warnings_group)
            all_ids = self.get_all_ids_from_group(warnings_group)
            
            # Color based on group status
            group_tags = self.get_status_tags(group_status)
            
            # Insert parent node (group)
            parent_text = f"{message[:80]}{'...' if len(message) > 80 else ''}"
            parent = self.app.tree.insert("", "end", text=parent_text, values=(
                len(warnings_group),
                status_summary,
                f"Group: {len(warnings_group)} warning(s)",
                f"{len(all_ids)} ID(s)"
            ), tags=group_tags, open=False)
            
            # Insert children (individual warnings)
            for warning in warnings_group:
                ids_str = ", ".join(warning["ids"])
                child_tags = self.get_status_tags(warning["status"])
                
                self.app.tree.insert(parent, "end", text=f"Warning #{warning['index']}", values=(
                    warning["index"],
                    warning["status"],
                    warning["message"][:100] + ("..." if len(warning["message"]) > 100 else ""),
                    ids_str
                ), tags=child_tags)
    
    def populate_tree_flat(self, filtered_data):
        """Populate the tree with flat view (simple list)."""
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
            
        for warning in filtered_data:
            ids_str = ", ".join(warning["ids"])
            tags = self.get_status_tags(warning["status"])
            
            self.app.tree.insert("", "end", text=f"Warning #{warning['index']}", values=(
                warning["index"],
                warning["status"],
                warning["message"][:100] + ("..." if len(warning["message"]) > 100 else ""),
                ids_str
            ), tags=tags)
    
    def show_warning_details(self, warning):
        """Show warning detail window with status management."""
        detail_window = tk.Toplevel(self.app.root)
        detail_window.title(f"Warning #{warning['index']}")
        detail_window.geometry("600x500")
        detail_window.transient(self.app.root)
        detail_window.grab_set()
        
        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"Warning #{warning['index']}", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Message
        ttk.Label(main_frame, text="Message:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        message_text = tk.Text(main_frame, height=4, wrap=tk.WORD)
        message_text.insert("1.0", warning["message"])
        message_text.config(state=tk.DISABLED)
        message_text.pack(fill=tk.X, pady=(0, 10))
        
        # Elements
        ttk.Label(main_frame, text="Elements:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        elements_text = tk.Text(main_frame, height=6, wrap=tk.WORD)
        elements_text.insert("1.0", "\n".join(warning["elements"]) if isinstance(warning["elements"], list) else str(warning["elements"]))
        elements_text.config(state=tk.DISABLED)
        elements_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # IDs and controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="IDs:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ids_label = ttk.Label(control_frame, text=", ".join(warning["ids"]))
        ids_label.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(control_frame, text="Copy IDs", 
                  command=lambda: self.copy_ids(warning["ids"])).pack(side=tk.RIGHT)
        
        # Status management
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Status:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        status_var = tk.StringVar(value=warning["status"])
        status_combo = ttk.Combobox(status_frame, textvariable=status_var, 
                                   values=["Open", "In Review", "Close"], state="readonly")
        status_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def save_changes():
            warning["status"] = status_var.get()
            warning["modified_date"] = datetime.now().isoformat()
            self.update_tree()
            detail_window.destroy()
            logger.info(f"Updated warning #{warning['index']} status to: {warning['status']}")
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=detail_window.destroy).pack(side=tk.RIGHT)
    
    def show_group_details(self, warnings_group):
        """Show detail window for a group of warnings."""
        detail_window = tk.Toplevel(self.app.root)
        detail_window.title(f"Group Warning - {len(warnings_group)} items")
        detail_window.geometry("800x600")
        detail_window.transient(self.app.root)
        detail_window.grab_set()
        
        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"Group: {len(warnings_group)} warning(s)", 
                 font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Common message
        ttk.Label(main_frame, text="Message:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        message_text = tk.Text(main_frame, height=3, wrap=tk.WORD)
        message_text.insert("1.0", warnings_group[0]["message"])
        message_text.config(state=tk.DISABLED)
        message_text.pack(fill=tk.X, pady=(0, 10))
        
        # Warnings list in the group
        ttk.Label(main_frame, text="Warnings in the group:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Frame for the list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for the list
        list_columns = ("Index", "Status", "IDs")
        list_tree = ttk.Treeview(list_frame, columns=list_columns, show="headings", height=10)
        
        list_tree.heading("Index", text="N°")
        list_tree.heading("Status", text="Status")
        list_tree.heading("IDs", text="IDs")
        
        list_tree.column("Index", width=60)
        list_tree.column("Status", width=100)
        list_tree.column("IDs", width=300)
        
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=list_tree.yview)
        list_tree.configure(yscrollcommand=list_scrollbar.set)
        
        list_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate the list
        for warning in warnings_group:
            ids_str = ", ".join(warning["ids"])
            tags = self.get_status_tags(warning["status"])
            list_tree.insert("", "end", values=(warning["index"], warning["status"], ids_str), tags=tags)
        
        # Configure colors for the list
        list_tree.tag_configure("open", background="#ffebee")
        list_tree.tag_configure("in_review", background="#fff3e0")
        list_tree.tag_configure("close", background="#e8f5e8")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def copy_all_ids():
            all_ids = self.get_all_ids_from_group(warnings_group)
            if all_ids:
                ids_string = ", ".join(all_ids)
                detail_window.clipboard_clear()
                detail_window.clipboard_append(ids_string)
                self.app.warnings_info_label.config(text=f"All group IDs copied ({len(all_ids)})")
                logger.info(f"Copied all {len(all_ids)} IDs from group to clipboard")
        
        ttk.Button(button_frame, text="Copy all IDs", command=copy_all_ids).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Close", command=detail_window.destroy).pack(side=tk.RIGHT)
        
    def copy_ids(self, ids):
        """Copy IDs to clipboard."""
        if ids:
            ids_string = ", ".join(ids)
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(ids_string)
            self.app.warnings_info_label.config(text=f"IDs copied: {ids_string}")

    def show_journal_entry_details(self, event):
        """Show detailed view of a journal entry on double-click."""
        selection = self.app.journal_tree.selection()
        if not selection:
            return
            
        # Get the selected item
        item = selection[0]
        values = self.app.journal_tree.item(item, "values")
        if not values or len(values) < 3:
            return
            
        timestamp = values[0]
        category = values[1]
        content_truncated = values[2]
        
        # Find the full content from original data
        content = content_truncated  # Default to truncated if we can't find the full version
        if hasattr(self.app, 'journal_data') and self.app.journal_data:
            entries = self.app.journal_data.get('lines', [])
            for entry in entries:
                # Match by timestamp and category to find the correct entry
                if entry.get('timestamp') == timestamp and entry.get('category') == category:
                    # Check if the truncated content matches the start of this entry's content
                    entry_content = entry.get('content', '')
                    if content_truncated.endswith('...'):
                        # Compare the non-truncated part
                        content_start = content_truncated[:-3]  # Remove '...'
                        if entry_content.startswith(content_start):
                            content = entry_content
                            break
                    elif entry_content == content_truncated:
                        # Exact match (content wasn't truncated)
                        content = entry_content
                        break
        
        # Create a detail window
        detail_window = tk.Toplevel(self.app.root)
        detail_window.title(f"Journal Entry - {category}")
        detail_window.geometry("800x500")
        detail_window.transient(self.app.root)
        detail_window.grab_set()
        
        # Create the main frame
        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Display entry information
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Category: ", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=f"{category}", font=("Arial", 10)).grid(row=0, column=1, sticky=tk.W)
        
        if timestamp:
            ttk.Label(info_frame, text=f"Timestamp: ", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W)
            ttk.Label(info_frame, text=f"{timestamp}", font=("Arial", 10)).grid(row=1, column=1, sticky=tk.W)
        
        # Content display
        ttk.Label(main_frame, text="Content:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        # Frame for content with scrollbars
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # Add vertical scrollbar only
        y_scrollbar = ttk.Scrollbar(content_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content text with word wrap and vertical scrollbar
        content_text = tk.Text(content_frame, wrap=tk.WORD, height=15,
                              yscrollcommand=y_scrollbar.set)
        content_text.insert("1.0", content)
        content_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        y_scrollbar.config(command=content_text.yview)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Copy button
        def copy_content():
            detail_window.clipboard_clear()
            detail_window.clipboard_append(content)
            if hasattr(self.app, 'journal_info_label'):
                self.app.journal_info_label.config(text="Journal entry content copied to clipboard")
        
        ttk.Button(button_frame, text="Copy Content", command=copy_content).pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(button_frame, text="Close", command=detail_window.destroy).pack(side=tk.RIGHT)

    def apply_journal_filter(self, *args):
        """Apply selected filters to the journal entries."""
        # Clear the treeview
        for item in self.app.journal_tree.get_children():
            self.app.journal_tree.delete(item)
            
        if not hasattr(self.app, 'journal_data') or not self.app.journal_data:
            return

        # Get filter values
        category_filter = self.app.journal_filter.get() if hasattr(self.app, 'journal_filter') else "All"
        search_text = self.app.journal_search_var.get().lower() if hasattr(self.app, 'journal_search_var') else ""
        time_range = self.app.time_range_var.get() if hasattr(self.app, 'time_range_var') else "All"
        filter_by_model = self.app.filter_selected_model_var.get() if hasattr(self.app, 'filter_selected_model_var') else False

        # Get current model path if filtering by model
        selected_model_path = None
        if filter_by_model and hasattr(self.app, 'model_selector') and hasattr(self.app, 'journal_models'):
            selected_index = self.app.model_selector.current()
            if selected_index >= 0 and selected_index < len(self.app.journal_models):
                selected_model = self.app.journal_models[selected_index]
                if "path" in selected_model:
                    selected_model_path = selected_model["path"]

        # Calculate time filter if needed
        filter_timestamp = None
        if time_range != "All":
            try:
                from datetime import timedelta
                latest_timestamp = None
                for entry in self.app.journal_data.get('lines', []):
                    if entry.get("timestamp"):
                        ts_str = entry["timestamp"]
                        ts = datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S.%f")
                        if latest_timestamp is None or ts > latest_timestamp:
                            latest_timestamp = ts
                
                if latest_timestamp:
                    if time_range == "Last 15 min":
                        filter_timestamp = latest_timestamp - timedelta(minutes=15)
                    elif time_range == "Last 1 hour":
                        filter_timestamp = latest_timestamp - timedelta(hours=1)
            except Exception as e:
                logger.warning(f"Time filter parsing error: {e}")

        # Filter and display entries
        displayed_count = 0
        entries = self.app.journal_data.get('lines', [])
        for entry in entries:
            # Apply category filter
            category = entry.get("category", "")
            if category_filter != "All" and category != category_filter:
                continue

            # Apply text search filter
            content = entry.get("content", "").lower()
            if search_text and search_text not in content:
                continue

            # Apply model filter
            if filter_by_model and selected_model_path:
                model_related = False
                if "model" in entry and entry["model"] == selected_model_path:
                    model_related = True
                if selected_model_path in content:
                    model_related = True
                if not model_related:
                    continue

            # Apply time filter
            if filter_timestamp and entry.get("timestamp"):
                try:
                    ts_str = entry["timestamp"]
                    entry_ts = datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S.%f")
                    if entry_ts < filter_timestamp:
                        continue
                except Exception:
                    pass  # Include if parsing fails

            # Insert the entry
            values = (
                entry.get("timestamp", "N/A"),
                entry.get("category", "Unknown"),
                entry.get("content", "")[:100] + ('...' if len(entry.get("content", "")) > 100 else '')
            )
            self.app.journal_tree.insert("", tk.END, values=values)
            displayed_count += 1

        # Update info label
        if hasattr(self.app, 'journal_info_label'):
            self.app.journal_info_label.config(text=f"Displaying {displayed_count} of {len(entries)} entries")
        
        logger.debug(f"Journal filter applied: displayed {displayed_count}/{len(entries)} entries")

    def clear_text_filter(self):
        """Clear the text filter and refresh the journal view."""
        if hasattr(self.app, 'journal_search_var'):
            self.app.journal_search_var.set("")
        self.apply_journal_filter()
        logger.debug("Journal text filter cleared")

    def update_worker_log_view(self):
        """Update the UI to display worker log entries."""
        if not hasattr(self.app, 'journal_tree'):
            return

        # Clear existing items
        self.app.journal_tree.delete(*self.app.journal_tree.get_children())

        if hasattr(self.app, 'worker_log_entries'):
            for entry in self.app.worker_log_entries:
                values = (
                    entry.get('timestamp', 'N/A'),
                    entry.get('level', 'N/A'),
                    entry.get('message', 'N/A')[:100] + ('...' if len(entry.get('message', '')) > 100 else '')
                )
                self.app.journal_tree.insert("", tk.END, values=values)

    def update_journal_tree(self):
        """Populates the journal treeview with found problems and logs them to the console."""
        if not hasattr(self.app, 'journal_tree'):
            logger.error("App object does not have a 'journal_tree' attribute.")
            raise AttributeError("App object does not have a 'journal_tree' attribute.")

        for item in self.app.journal_tree.get_children():
            self.app.journal_tree.delete(item)

        # Store the full descriptions for later use
        self.app.journal_full_descriptions = {}
        
        for i, problem in enumerate(self.app.journal_problems):
            logger.info(f"Problem found: Timestamp={problem['timestamp']}, Type={problem['type']}, Source={problem['source']}, Description={problem['description']}")
            
            # Create an ID for this item to reference the full description
            item_id = f"journal_problem_{i}"
            
            # Store the full description
            self.app.journal_full_descriptions[item_id] = problem["description"]
            
            # Insert with truncated description for display
            trunc_desc = problem["description"][:100] + ("..." if len(problem["description"]) > 100 else "")
            
            item = self.app.journal_tree.insert("", "end", iid=item_id, values=(
                problem["timestamp"],
                problem["type"],
                problem["source"],
                trunc_desc
            ))
            
    def on_journal_tree_double_click(self, event):
        """Handle double click on journal tree item to show full details."""
        item = self.app.journal_tree.focus()
        if not item:
            return
            
        if hasattr(self.app, 'journal_full_descriptions') and item in self.app.journal_full_descriptions:
            # Get the problem details
            values = self.app.journal_tree.item(item, "values")
            timestamp = values[0]
            problem_type = values[1]
            source = values[2]
            full_description = self.app.journal_full_descriptions[item]
            
            # Create a new window to show the details
            details_window = tk.Toplevel(self.app.root)
            details_window.title(f"Journal Problem Details - {problem_type}")
            details_window.geometry("800x400")
            
            # Create a frame with padding
            frame = ttk.Frame(details_window, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Add labels for metadata
            ttk.Label(frame, text=f"Timestamp: {timestamp}", font=("Arial", 10, "bold")).pack(anchor="w")
            ttk.Label(frame, text=f"Type: {problem_type}", font=("Arial", 10, "bold")).pack(anchor="w")
            ttk.Label(frame, text=f"Source: {source}", font=("Arial", 10, "bold")).pack(anchor="w")
            
            # Add a separator
            ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=10)
            
            # Add a text widget with the full description
            ttk.Label(frame, text="Full Description:", font=("Arial", 10, "bold")).pack(anchor="w")
            
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            
            text_widget = tk.Text(text_frame, wrap="word", padx=5, pady=5)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.configure(yscrollcommand=scrollbar.set)
            text_widget.insert("1.0", full_description)
            text_widget.configure(state="disabled")  # Make it read-only
            
            # Add a close button
            ttk.Button(frame, text="Close", command=details_window.destroy).pack(pady=(10, 0))
