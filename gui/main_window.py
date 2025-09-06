"""
Main window for BDSP-Batch-Editor.
Contains the primary GUI interface for the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, Dict, Any, List
import os
import sys
import copy

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unpacker import FileUnpacker
from core.level_editor import LevelEditor
from gui.dialogs import FileSelectionDialog, BackupConfirmationDialog, ErrorDialog


class MainWindow:
    """Main application window for BDSP-Batch-Editor."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.unpacker = FileUnpacker()
        self.level_editor = LevelEditor()

        # Application state
        self.current_file_path: Optional[str] = None
        self.trainer_data: Optional[Dict[str, Any]] = None
        self.trainer_poke_data: Optional[List[Dict[str, Any]]] = None
        self.original_trainer_poke_data: Optional[List[Dict[str, Any]]] = None
        self.selected_trainers: set = set()  # Track selected trainer IDs

        self._setup_window()
        self._create_widgets()
        self._setup_menu()

    def _setup_window(self):
        """Setup the main window properties."""
        self.root.title("BDSP-Batch-Editor")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _create_widgets(self):
        """Create the main window widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # File operations frame
        self._create_file_frame(main_frame)

        # Data display and editing frame
        self._create_data_frame(main_frame)

        # Level editing controls frame
        self._create_controls_frame(main_frame)

        # Status bar
        self._create_status_bar(main_frame)

    def _create_file_frame(self, parent):
        """Create the file operations frame."""
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding="5")
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.grid_columnconfigure(1, weight=1)

        # Open file button
        ttk.Button(
            file_frame, text="Open TrainerTable JSON", command=self._open_file
        ).grid(row=0, column=0, padx=(0, 10))

        # File path label
        self.file_path_var = tk.StringVar(value="No file selected")
        self.file_path_label = ttk.Label(
            file_frame, textvariable=self.file_path_var, relief="sunken", padding="5"
        )
        self.file_path_label.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # Save button
        self.save_button = ttk.Button(
            file_frame,
            text="Save to New File",
            command=self._save_file,
            state="disabled",
        )
        self.save_button.grid(row=0, column=2)

    def _create_data_frame(self, parent):
        """Create the data display frame."""
        data_frame = ttk.LabelFrame(parent, text="Trainer Data", padding="5")
        data_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        data_frame.grid_rowconfigure(1, weight=1)
        data_frame.grid_columnconfigure(0, weight=1)

        # Add explanation label
        explanation_frame = ttk.Frame(data_frame)
        explanation_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        explanation_label = ttk.Label(
            explanation_frame,
            text="✓ Select | Current Levels | Original Levels (OG)",
            font=("TkDefaultFont", 9),
            foreground="#555555",
        )
        explanation_label.pack()

        # Create treeview for data display
        tree_frame = ttk.Frame(data_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Treeview with columns - Checkbox first, then current levels, then original levels
        columns = (
            "selected",
            "trainer_id",
            "p1_level",
            "p2_level",
            "p3_level",
            "p4_level",
            "p5_level",
            "p6_level",
            "p1_orig_level",
            "p2_orig_level",
            "p3_orig_level",
            "p4_orig_level",
            "p5_orig_level",
            "p6_orig_level",
        )
        self.data_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=15
        )

        # Configure tags for highlighting changes
        self.data_tree.tag_configure("changed", background="#ffffcc")  # Light yellow
        self.data_tree.tag_configure("unchanged", background="white")

        # Configure separator column styling
        self.data_tree.tag_configure(
            "separator_col", background="#f0f0f0", foreground="#666666"
        )

        # Configure column headings and widths
        self.data_tree.heading("selected", text="✓")
        self.data_tree.heading("trainer_id", text="Trainer ID")

        # Current levels section
        self.data_tree.heading("p1_level", text="P1")
        self.data_tree.heading("p2_level", text="P2")
        self.data_tree.heading("p3_level", text="P3")
        self.data_tree.heading("p4_level", text="P4")
        self.data_tree.heading("p5_level", text="P5")
        self.data_tree.heading("p6_level", text="P6")

        # Original levels section
        self.data_tree.heading("p1_orig_level", text="P1 OG")
        self.data_tree.heading("p2_orig_level", text="P2 OG")
        self.data_tree.heading("p3_orig_level", text="P3 OG")
        self.data_tree.heading("p4_orig_level", text="P4 OG")
        self.data_tree.heading("p5_orig_level", text="P5 OG")
        self.data_tree.heading("p6_orig_level", text="P6 OG")

        # Set column widths
        self.data_tree.column("selected", width=40, anchor="center")
        self.data_tree.column("trainer_id", width=100)

        # Current levels columns
        for i in range(1, 7):
            self.data_tree.column(f"p{i}_level", width=60)

        # Original levels columns
        for i in range(1, 7):
            self.data_tree.column(f"p{i}_orig_level", width=60)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.data_tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.data_tree.xview
        )
        self.data_tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind click event for checkbox toggling
        self.data_tree.bind("<Button-1>", self._on_treeview_click)

        # Data info frame
        info_frame = ttk.Frame(data_frame)
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.data_info_var = tk.StringVar(value="No data loaded")
        ttk.Label(info_frame, textvariable=self.data_info_var).pack(side=tk.LEFT)

    def _create_controls_frame(self, parent):
        """Create the level editing controls frame."""
        controls_frame = ttk.LabelFrame(parent, text="Level Editing", padding="5")
        controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Input frame
        input_frame = ttk.Frame(controls_frame)
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Level modification input
        ttk.Label(input_frame, text="Level Modification:").grid(
            row=0, column=0, padx=(0, 10)
        )

        self.level_input_var = tk.StringVar()
        self.level_input = ttk.Entry(
            input_frame, textvariable=self.level_input_var, width=20
        )
        self.level_input.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(input_frame, text="(e.g., +10, -5, 20%)").grid(
            row=0, column=2, padx=(0, 20)
        )

        # Level constraints
        ttk.Label(input_frame, text="Min Level:").grid(row=0, column=3, padx=(0, 5))
        self.min_level_var = tk.StringVar(value="1")
        ttk.Entry(input_frame, textvariable=self.min_level_var, width=5).grid(
            row=0, column=4, padx=(0, 10)
        )

        ttk.Label(input_frame, text="Max Level:").grid(row=0, column=5, padx=(0, 5))
        self.max_level_var = tk.StringVar(value="100")
        ttk.Entry(input_frame, textvariable=self.max_level_var, width=5).grid(
            row=0, column=6, padx=(0, 10)
        )

        # Trainer selection input (new row)
        ttk.Label(input_frame, text="Trainer IDs:").grid(
            row=1, column=0, padx=(0, 10), pady=(10, 0)
        )

        self.trainer_ids_var = tk.StringVar()
        self.trainer_ids_input = ttk.Entry(
            input_frame, textvariable=self.trainer_ids_var, width=30
        )
        self.trainer_ids_input.grid(
            row=1, column=1, columnspan=2, padx=(0, 10), pady=(10, 0), sticky="ew"
        )

        ttk.Label(input_frame, text="(e.g., 57,38,289 or leave empty for all)").grid(
            row=1, column=3, columnspan=4, padx=(0, 0), pady=(10, 0)
        )

        # Bind event to update checkboxes when text changes
        self.trainer_ids_var.trace("w", self._on_trainer_ids_changed)

        # Buttons frame
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        # Preview button
        self.preview_button = ttk.Button(
            buttons_frame,
            text="Preview Changes",
            command=self._preview_changes,
            state="disabled",
        )
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))

        # Apply button
        self.apply_button = ttk.Button(
            buttons_frame,
            text="Apply Changes",
            command=self._apply_changes,
            state="disabled",
        )
        self.apply_button.pack(side=tk.LEFT, padx=(0, 10))

        # Reset button
        self.reset_button = ttk.Button(
            buttons_frame, text="Reset Data", command=self._reset_data, state="disabled"
        )
        self.reset_button.pack(side=tk.LEFT)

    def _create_status_bar(self, parent):
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame, textvariable=self.status_var, relief="sunken", padding="2"
        )
        status_label.grid(row=0, column=0, sticky="ew")

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, variable=self.progress_var, mode="determinate"
        )
        self.progress_bar.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.progress_bar.grid_remove()  # Hide by default

    def _setup_menu(self):
        """Setup the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Open...", command=self._open_file, accelerator="Ctrl+O"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Save to New File", command=self._save_file, accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label="Save As...", command=self._save_as_file, accelerator="Ctrl+Shift+S"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Reset Data", command=self._reset_data)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_as_file())

    def _open_file(self):
        """Open a trainer file."""
        file_path = FileSelectionDialog.select_trainer_file(self.root)
        if not file_path:
            return

        self._set_status("Loading file...")
        self._show_progress()

        def load_file():
            try:
                # Load and validate the file
                self.trainer_data = self.unpacker.load_trainer_file(file_path)

                if not self.unpacker.validate_trainer_data():
                    raise ValueError("Invalid trainer data structure")

                self.trainer_poke_data = self.unpacker.extract_trainer_poke_data()
                # Store a deep copy of the original data for comparison
                self.original_trainer_poke_data = copy.deepcopy(self.trainer_poke_data)
                self.current_file_path = file_path

                # Update UI on main thread
                self.root.after(0, self._file_loaded_callback)

            except Exception as e:
                self.root.after(0, lambda: self._file_load_error(str(e)))

        # Load file in background thread
        threading.Thread(target=load_file, daemon=True).start()

    def _file_loaded_callback(self):
        """Callback when file is successfully loaded."""
        self._hide_progress()
        self._populate_data_tree()
        self._update_ui_state(True)
        self._update_file_path_display()
        self._update_data_info()
        self._set_status(f"Loaded {len(self.trainer_poke_data or [])} trainer entries")

    def _file_load_error(self, error_message: str):
        """Handle file loading error."""
        self._hide_progress()
        self._set_status("Error loading file")
        ErrorDialog.show_error(
            self.root, "File Load Error", "Failed to load trainer file", error_message
        )

    def _populate_data_tree(self):
        """Populate the data tree with trainer information."""
        # Clear existing data
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)

        if not self.trainer_poke_data or not self.original_trainer_poke_data:
            return

        # Process all entries (no artificial limit)
        total_entries = len(self.trainer_poke_data)

        # For large datasets, update progress periodically
        update_interval = max(
            100, total_entries // 50
        )  # Update every 2% or minimum 100 entries

        for i in range(total_entries):
            entry = self.trainer_poke_data[i]
            original_entry = self.original_trainer_poke_data[i]
            trainer_id = entry.get("ID", i)

            # Get Pokemon levels and check for changes
            values = []
            has_changes = False

            # Checkbox status first
            checkbox_display = "☑" if trainer_id in self.selected_trainers else "☐"
            values.append(checkbox_display)

            # Trainer ID
            values.append(trainer_id)

            # Current levels
            current_levels = []
            for j in range(1, 7):
                level_key = f"P{j}Level"
                current_level = entry.get(level_key, 0)
                current_display = str(current_level) if current_level > 0 else "-"
                current_levels.append(current_display)
            values.extend(current_levels)

            # Original levels
            for j in range(1, 7):
                level_key = f"P{j}Level"

                # Original level
                orig_level = original_entry.get(level_key, 0)
                orig_display = str(orig_level) if orig_level > 0 else "-"

                # Current level for comparison
                current_level = entry.get(level_key, 0)

                # Check if level changed
                if orig_level > 0 and current_level > 0 and orig_level != current_level:
                    has_changes = True

                values.append(orig_display)

            # Insert with appropriate tag
            tag = "changed" if has_changes else "unchanged"
            self.data_tree.insert("", tk.END, values=values, tags=(tag,))

            # Update GUI periodically for large datasets to show progress
            if total_entries > 1000 and (i + 1) % update_interval == 0:
                self.root.update_idletasks()  # Allow GUI to refresh

    def _update_ui_state(self, file_loaded: bool):
        """Update UI state based on whether a file is loaded."""
        state = "normal" if file_loaded else "disabled"

        self.save_button.config(state=state)
        self.preview_button.config(state=state)
        self.apply_button.config(state=state)
        self.reset_button.config(state=state)

    def _update_file_path_display(self):
        """Update the file path display."""
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            self.file_path_var.set(
                f"{filename} ({os.path.dirname(self.current_file_path)})"
            )
        else:
            self.file_path_var.set("No file selected")

    def _update_data_info(self):
        """Update the data information display."""
        if self.trainer_poke_data:
            stats = self.level_editor.get_modification_statistics(
                self.trainer_poke_data
            )
            info_text = (
                f"Total Trainers: {stats['total_trainers']} | "
                f"Trainers with Pokemon: {stats['trainers_with_pokemon']} | "
                f"Total Pokemon: {stats['total_pokemon']}"
            )
            self.data_info_var.set(info_text)
        else:
            self.data_info_var.set("No data loaded")

    def _preview_changes(self):
        """Preview level modifications."""
        if not self.trainer_poke_data:
            ErrorDialog.show_warning(self.root, "No Data", "No trainer data loaded")
            return

        try:
            operation_type, value = self._validate_input()
            min_level = int(self.min_level_var.get())
            max_level = int(self.max_level_var.get())
            selected_trainers = self._get_selected_trainer_ids()

            self._set_status("Generating preview...")

            preview_data = self.level_editor.preview_modifications(
                self.trainer_poke_data,
                operation_type,
                value,
                min_level,
                max_level,
                selected_trainers,
                max_preview_entries=100,
            )

            if not preview_data:
                ErrorDialog.show_info(
                    self.root,
                    "No Changes",
                    "No Pokemon levels would be modified with these settings.",
                )
                self._set_status("Ready")
                return

            # Show preview dialog (simplified for now)
            modification_info = {
                "operation_type": operation_type,
                "value": value,
                "min_level": min_level,
                "max_level": max_level,
            }

            total_changes = sum(
                len([p for p in entry["pokemon_previews"] if p["changed"]])
                for entry in preview_data
            )

            selection_info = ""
            if selected_trainers:
                selection_info = f"Selected trainers: {len(selected_trainers)} IDs\n"
            else:
                selection_info = "Selection: All trainers\n"

            message = (
                f"Preview of modifications:\n\n"
                f"Operation: {operation_type} {value:+g}\n"
                f"{selection_info}"
                f"Trainers affected: {len(preview_data)}\n"
                f"Pokemon affected: {total_changes}\n\n"
                f"Level constraints: {min_level} - {max_level}\n\n"
                f"Do you want to apply these changes?"
            )

            result = messagebox.askyesno("Preview Changes", message, parent=self.root)

            if result:
                self._apply_changes()

            self._set_status("Ready")

        except Exception as e:
            ErrorDialog.show_error(
                self.root, "Preview Error", "Failed to generate preview", str(e)
            )
            self._set_status("Ready")

    def _apply_changes(self):
        """Apply level modifications."""
        if not self.trainer_poke_data:
            ErrorDialog.show_warning(self.root, "No Data", "No trainer data loaded")
            return

        try:
            operation_type, value = self._validate_input()
            min_level = int(self.min_level_var.get())
            max_level = int(self.max_level_var.get())
            selected_trainers = self._get_selected_trainer_ids()

            self._set_status("Applying modifications...")
            self._show_progress()

            # Apply modifications
            result = self.level_editor.apply_level_modification(
                self.trainer_poke_data,
                operation_type,
                value,
                min_level,
                max_level,
                selected_trainers,
            )

            self._hide_progress()

            # Update display
            self._populate_data_tree()

            # Show result
            selection_info = ""
            if selected_trainers:
                selection_info = f"Selected trainers: {len(selected_trainers)} IDs\n"
            else:
                selection_info = "Selection: All trainers\n"

            message = (
                f"Modifications applied successfully:\n\n"
                f"{selection_info}"
                f"Trainers modified: {result['total_trainers_modified']}\n"
                f"Pokemon modified: {result['total_pokemon_modified']}"
            )

            ErrorDialog.show_info(self.root, "Changes Applied", message)
            self._set_status("Changes applied - save to new file to preserve!")

        except Exception as e:
            self._hide_progress()
            ErrorDialog.show_error(
                self.root, "Application Error", "Failed to apply changes", str(e)
            )
            self._set_status("Ready")

    def _validate_input(self):
        """Validate the level modification input."""
        input_text = self.level_input_var.get().strip()
        if not input_text:
            raise ValueError("Please enter a level modification value")

        try:
            operation_type, value = self.level_editor.parse_level_modification(
                input_text
            )
        except ValueError as e:
            raise ValueError(f"Invalid input format: {str(e)}")

        try:
            min_level = int(self.min_level_var.get())
            max_level = int(self.max_level_var.get())

            if min_level < 1 or max_level > 100 or min_level > max_level:
                raise ValueError("Invalid level constraints")

        except ValueError:
            raise ValueError("Invalid level constraints")

        return operation_type, value

    def _save_file(self):
        """Save to a new file (original file is never modified)."""
        self._save_as_file()

    def _save_as_file(self):
        """Save the file with a new name."""
        if not self.trainer_data:
            ErrorDialog.show_warning(self.root, "No Data", "No data to save")
            return

        # Always suggest "TrainerTable.json" as the default name
        default_name = "TrainerTable.json"

        file_path = FileSelectionDialog.select_save_location(self.root, default_name)
        if file_path:
            self._save_to_file(file_path)

    def _save_to_file(self, file_path: str):
        """Save data to the specified file."""
        try:
            # Prevent overwriting the original file
            if file_path == self.current_file_path:
                ErrorDialog.show_warning(
                    self.root,
                    "Cannot Overwrite Original",
                    "The original file cannot be modified. Please choose a different filename to preserve your original data.",
                )
                return

            self._set_status("Saving file...")
            self.unpacker.save_trainer_file(file_path)

            # Show success confirmation dialog
            filename = os.path.basename(file_path)
            ErrorDialog.show_info(
                self.root,
                "File Saved Successfully",
                f"Your trainer data has been saved to:\n\n{filename}\n\nLocation: {os.path.dirname(file_path)}",
            )

            self._set_status(f"File saved: {filename}")

        except Exception as e:
            ErrorDialog.show_error(
                self.root, "Save Error", "Failed to save file", str(e)
            )
            self._set_status("Ready")

    def _reset_data(self):
        """Reset data to original state."""
        if not self.original_trainer_poke_data:
            return

        result = messagebox.askyesno(
            "Reset Data",
            "Reset all modifications and restore original levels?",
            parent=self.root,
        )
        if result:
            # Restore from the original data backup
            self.trainer_poke_data = copy.deepcopy(self.original_trainer_poke_data)
            self._populate_data_tree()
            self._set_status("Data reset to original values")

    def _open_file_direct(self, file_path: str):
        """Open a specific file directly."""
        try:
            self.trainer_data = self.unpacker.load_trainer_file(file_path)
            self.trainer_poke_data = self.unpacker.extract_trainer_poke_data()
            self._file_loaded_callback()

        except Exception as e:
            self._file_load_error(str(e))

    def _show_about(self):
        """Show about dialog."""
        about_text = (
            "BDSP-Batch-Editor\n"
            "Version 1.0\n\n"
            "A tool for bulk editing Pokemon levels in\n"
            "Brilliant Diamond/Shining Pearl trainer data.\n\n"
            "Supports absolute and percentage level modifications\n"
            "with preview functionality."
        )

        ErrorDialog.show_info(self.root, "About BDSP-Batch-Editor", about_text)

    def _set_status(self, message: str):
        """Set the status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()

    def _show_progress(self):
        """Show the progress bar."""
        self.progress_bar.grid()
        self.progress_var.set(0)
        self.root.update_idletasks()

    def _hide_progress(self):
        """Hide the progress bar."""
        self.progress_bar.grid_remove()
        self.root.update_idletasks()

    def _on_trainer_ids_changed(self, *args):
        """Handle trainer IDs text input changes."""
        trainer_ids_text = self.trainer_ids_var.get().strip()

        # Clear current selection
        self.selected_trainers.clear()

        if trainer_ids_text:
            try:
                # Parse comma-separated trainer IDs
                trainer_ids = [
                    int(id_str.strip())
                    for id_str in trainer_ids_text.split(",")
                    if id_str.strip()
                ]
                self.selected_trainers.update(trainer_ids)
            except ValueError:
                # Invalid input, keep selection empty
                pass

        # Refresh the data tree to update checkboxes
        self._populate_data_tree()

    def _on_treeview_click(self, event):
        """Handle treeview click events for checkbox toggling."""
        # Identify clicked region
        region = self.data_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Get clicked item and column
        item = self.data_tree.identify_row(event.y)
        column = self.data_tree.identify_column(event.x)

        # Only handle clicks on the checkbox column (first column)
        if column == "#1":  # First column (checkbox)
            # Get trainer ID from the row
            values = self.data_tree.item(item, "values")
            if values and len(values) > 1:
                try:
                    trainer_id = int(values[1])  # Trainer ID is in second column

                    # Toggle selection
                    if trainer_id in self.selected_trainers:
                        self.selected_trainers.remove(trainer_id)
                    else:
                        self.selected_trainers.add(trainer_id)

                    # Update the text field to reflect the selection
                    self._update_trainer_ids_text()

                    # Refresh the data tree to update checkboxes
                    self._populate_data_tree()

                except (ValueError, IndexError):
                    # Invalid trainer ID, ignore
                    pass

    def _update_trainer_ids_text(self):
        """Update the trainer IDs text field from the selected set."""
        if self.selected_trainers:
            trainer_ids_text = ",".join(
                str(trainer_id) for trainer_id in sorted(self.selected_trainers)
            )
            self.trainer_ids_var.set(trainer_ids_text)
        else:
            self.trainer_ids_var.set("")

    def _get_selected_trainer_ids(self):
        """Get the list of selected trainer IDs for modifications."""
        return list(self.selected_trainers) if self.selected_trainers else None
