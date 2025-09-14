"""
Main window for BDSP-Batch-Editor with multi-file support.
Contains the primary GUI interface with left panel navigation and right panel editor.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional, Dict, Any, List
import os
import sys
import copy
import shutil

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unpacker import FileUnpacker
from core.level_editor import LevelEditor
from core.file_detector import FileDetector
from core.config import SUPPORTED_FILES, CONTENT_TYPES, UI_CONFIG, is_content_supported
from gui.dialogs import FileSelectionDialog, BackupConfirmationDialog, ErrorDialog


class MainWindow:
    """Main application window for BDSP-Batch-Editor with multi-file support."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.unpacker = FileUnpacker()
        self.level_editor = LevelEditor()

        # Multi-file state
        self.detected_files: Dict[str, Optional[str]] = {}  # file_type -> file_path
        self.available_content: Dict[str, List[str]] = {}  # file_type -> content_list
        self.selected_file_type: Optional[str] = None
        self.selected_content: Optional[str] = None
        self.is_single_file_mode: bool = False

        # Current editor state (TrainerTable for now)
        self.current_file_path: Optional[str] = None
        self.trainer_data: Optional[Dict[str, Any]] = None
        self.trainer_poke_data: Optional[List[Dict[str, Any]]] = None
        self.original_trainer_poke_data: Optional[List[Dict[str, Any]]] = None
        self.selected_trainers: set = set()  # Track selected trainer IDs

        self._setup_window()
        self._create_widgets()
        self._setup_menu()
        self._update_ui_state()

        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_window(self):
        """Setup the main window properties."""
        config = UI_CONFIG["main_window"]
        self.root.title(config["title"])

        # Set default window size (larger for better usability)
        default_width = config.get("default_width", config["min_width"])
        default_height = config.get("default_height", config["min_height"])
        self.root.geometry(f"{default_width}x{default_height}")
        self.root.minsize(config["min_width"], config["min_height"])

        # Center the window on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - default_width) // 2
        y = (screen_height - default_height) // 2
        self.root.geometry(f"{default_width}x{default_height}+{x}+{y}")

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0)  # Left panel (fixed width)
        self.root.grid_columnconfigure(1, weight=1)  # Right panel (expandable)

    def _create_widgets(self):
        """Create the main window widgets."""
        # Left panel for file navigation
        self._create_left_panel()

        # Right panel for current editor
        self._create_right_panel()

    def _create_left_panel(self):
        """Create the left panel with file selection and navigation."""
        # Left panel frame
        left_frame = ttk.Frame(
            self.root, padding="10", width=UI_CONFIG["main_window"]["left_panel_width"]
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_propagate(False)  # Maintain fixed width
        left_frame.grid_rowconfigure(2, weight=1)  # Content tree expandable
        left_frame.grid_columnconfigure(0, weight=1)

        # File selection buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            button_frame, text="Select Folder", command=self._select_folder
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ttk.Button(button_frame, text="Select File", command=self._select_file).grid(
            row=0, column=1, sticky="ew", padx=(5, 0)
        )

        # Detected Files section
        detected_frame = ttk.LabelFrame(left_frame, text="Detected Files", padding="5")
        detected_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        detected_frame.grid_columnconfigure(0, weight=1)

        # Detected files tree
        self.detected_tree = ttk.Treeview(detected_frame, height=6, show="tree")
        self.detected_tree.grid(row=0, column=0, sticky="ew")

        # Scrollbar for detected files
        detected_scroll = ttk.Scrollbar(
            detected_frame, orient="vertical", command=self.detected_tree.yview
        )
        self.detected_tree.configure(yscrollcommand=detected_scroll.set)
        detected_scroll.grid(row=0, column=1, sticky="ns")

        # Available Content section
        content_frame = ttk.LabelFrame(
            left_frame, text="Available Content", padding="5"
        )
        content_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # Available content tree
        self.content_tree = ttk.Treeview(content_frame, show="tree")
        self.content_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for content tree
        content_scroll = ttk.Scrollbar(
            content_frame, orient="vertical", command=self.content_tree.yview
        )
        self.content_tree.configure(yscrollcommand=content_scroll.set)
        content_scroll.grid(row=0, column=1, sticky="ns")

        # Bind selection events
        self.detected_tree.bind("<<TreeviewSelect>>", self._on_file_selected)
        self.content_tree.bind("<<TreeviewSelect>>", self._on_content_selected)

        # Export Options section
        export_frame = ttk.LabelFrame(left_frame, text="Export Options", padding="5")
        export_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        export_frame.grid_columnconfigure(0, weight=1)

        # Export mode selection
        mode_frame = ttk.Frame(export_frame)
        mode_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        mode_frame.grid_columnconfigure(0, weight=1)
        mode_frame.grid_columnconfigure(1, weight=1)

        self.export_mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(
            mode_frame,
            text="Single File",
            variable=self.export_mode_var,
            value="single",
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            mode_frame,
            text="ROMFS Structure",
            variable=self.export_mode_var,
            value="romfs",
        ).grid(row=0, column=1, sticky="w")

        # Export button
        self.export_button = ttk.Button(
            export_frame,
            text="Export Modified Files",
            command=self._export_files,
            state="disabled",
        )
        self.export_button.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        # Status info
        self.left_status_var = tk.StringVar(value="No files detected")
        ttk.Label(
            left_frame, textvariable=self.left_status_var, font=("TkDefaultFont", 9)
        ).grid(row=4, column=0, sticky="ew")

    def _create_right_panel(self):
        """Create the right panel with the current editor."""
        # Right panel frame
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Editor selection frame
        editor_frame = ttk.LabelFrame(right_frame, text="Current Editor", padding="5")
        editor_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.editor_info_var = tk.StringVar(value="No content selected")
        ttk.Label(editor_frame, textvariable=self.editor_info_var).pack()

        # Placeholder for editor content - will be created when file is selected
        self.editor_content_frame = ttk.Frame(right_frame)
        self.editor_content_frame.grid(row=1, column=0, sticky="nsew")
        self.editor_content_frame.grid_rowconfigure(0, weight=1)
        self.editor_content_frame.grid_columnconfigure(0, weight=1)

        # Welcome message when no content is selected
        self._show_welcome_message()

    def _show_welcome_message(self):
        """Show welcome message when no content is selected."""
        # Clear any existing content
        for widget in self.editor_content_frame.winfo_children():
            widget.destroy()

        # Reset trainer data state
        self.trainer_data = None
        self.trainer_poke_data = None
        self.original_trainer_poke_data = None
        self.current_file_path = None
        self.selected_trainers.clear()

        welcome_frame = ttk.LabelFrame(
            self.editor_content_frame, text="Welcome", padding="20"
        )
        welcome_frame.pack(fill="both", expand=True)

        welcome_text = """Welcome to BDSP-Batch-Editor!

To get started:
1. Select a folder or file using the buttons in the left panel
2. Choose a file type from the "Detected Files" section
3. Select content from the "Available Content" section
4. The editor will appear here to modify your data

Export your changes using the Export Options in the left panel."""

        ttk.Label(
            welcome_frame, text=welcome_text, justify="left", font=("TkDefaultFont", 10)
        ).pack(expand=True)

    def _create_trainer_table_editor(self):
        """Create the TrainerTable editor interface with dropdown selection."""
        # Clear any existing content
        for widget in self.editor_content_frame.winfo_children():
            widget.destroy()

        if not self.trainer_poke_data:
            return

        # Initialize UI variables early so they're available for button callbacks
        if not hasattr(self, "trainer_ids_var"):
            self.trainer_ids_var = tk.StringVar()
        if not hasattr(self, "level_input_var"):
            self.level_input_var = tk.StringVar()
        if not hasattr(self, "min_level_var"):
            self.min_level_var = tk.StringVar(value="1")
        if not hasattr(self, "max_level_var"):
            self.max_level_var = tk.StringVar(value="100")

        # Main container
        main_frame = ttk.Frame(self.editor_content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Trainer selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Select Trainer", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        # Create Trainer dropdown
        ttk.Label(selection_frame, text="Trainer:").pack(side=tk.LEFT, padx=(0, 5))

        # Prepare Trainer list for dropdown
        self.trainer_list = []
        self.trainer_lookup = {}

        for entry in self.trainer_poke_data:
            trainer_id = entry.get("ID", 0)
            display_name = f"Trainer #{trainer_id:03d}"
            self.trainer_list.append(display_name)
            self.trainer_lookup[display_name] = entry

        self.selected_trainer_var = tk.StringVar()
        self.trainer_dropdown = ttk.Combobox(
            selection_frame,
            textvariable=self.selected_trainer_var,
            values=self.trainer_list,
            state="readonly",
            width=20,
        )
        self.trainer_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        self.trainer_dropdown.bind("<<ComboboxSelected>>", self._on_trainer_selected)

        # Set default selection
        if self.trainer_list:
            self.trainer_dropdown.set(self.trainer_list[0])

        # Trainer details frame
        self.trainer_details_frame = ttk.LabelFrame(
            main_frame, text="Trainer Pokemon Details", padding=10
        )
        self.trainer_details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Load initial trainer data
        if self.trainer_list:
            self._load_trainer_details()

        # Level modification controls frame (keep existing functionality)
        level_controls_frame = ttk.LabelFrame(
            main_frame, text="Level Modification", padding=10
        )
        level_controls_frame.pack(fill=tk.X, pady=(0, 5))

        # Use existing level controls method but adapt for single trainer
        self._create_trainer_level_controls(level_controls_frame)

        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Preview and Apply buttons
        self.preview_trainer_button = ttk.Button(
            button_frame, text="Preview Changes", command=self._preview_changes
        )
        self.preview_trainer_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.apply_trainer_button = ttk.Button(
            button_frame, text="Apply Changes", command=self._apply_changes
        )
        self.apply_trainer_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Reset button
        self.reset_trainer_button = ttk.Button(
            button_frame, text="Reset Selection", command=self._reset_trainer_selection
        )
        self.reset_trainer_button.pack(side=tk.RIGHT)

    def _on_trainer_selected(self, event=None):
        """Handle trainer selection change."""
        self._load_trainer_details()

    def _load_trainer_details(self):
        """Load details for the currently selected trainer."""
        selected = self.selected_trainer_var.get()
        if not selected or selected not in self.trainer_lookup:
            return

        # Clear existing details widgets
        for widget in self.trainer_details_frame.winfo_children():
            widget.destroy()

        trainer_data = self.trainer_lookup[selected]

        # Create scrollable frame for trainer details
        canvas = tk.Canvas(self.trainer_details_frame)
        scrollbar = ttk.Scrollbar(
            self.trainer_details_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Trainer details entry fields
        self.trainer_entries = {}

        # Get layout configuration
        editor_config = UI_CONFIG.get("personal_table_editor", {})
        columns_per_row = editor_config.get("columns_per_row", 3)
        field_width = editor_config.get("field_width", 12)

        # Define pokemon slots and their fields
        pokemon_slots = []
        for i in range(1, 7):  # P1 through P6
            slot_data = {
                "slot": i,
                "level": trainer_data.get(f"P{i}Level", 0),
                "monsno": trainer_data.get(f"P{i}MonsNo", 0),
                "formno": trainer_data.get(f"P{i}FormNo", 0),
                "talent_hp": trainer_data.get(f"P{i}TalentHp", 0),
                "talent_atk": trainer_data.get(f"P{i}TalentAtk", 0),
                "talent_def": trainer_data.get(f"P{i}TalentDef", 0),
                "talent_spatk": trainer_data.get(f"P{i}TalentSpAtk", 0),
                "talent_spdef": trainer_data.get(f"P{i}TalentSpDef", 0),
                "talent_agi": trainer_data.get(f"P{i}TalentAgi", 0),
                "effort_hp": trainer_data.get(f"P{i}EffortHp", 0),
                "effort_atk": trainer_data.get(f"P{i}EffortAtk", 0),
                "effort_def": trainer_data.get(f"P{i}EffortDef", 0),
                "effort_spatk": trainer_data.get(f"P{i}EffortSpAtk", 0),
                "effort_spdef": trainer_data.get(f"P{i}EffortSpDef", 0),
                "effort_agi": trainer_data.get(f"P{i}EffortAgi", 0),
            }

            # Only include pokemon that exist (MonsNo > 0 or Level > 0)
            if slot_data["monsno"] > 0 or slot_data["level"] > 0:
                pokemon_slots.append(slot_data)

        if not pokemon_slots:
            # No pokemon found
            no_pokemon_label = ttk.Label(
                scrollable_frame,
                text="No Pokemon found for this trainer.",
                font=("TkDefaultFont", 10, "italic"),
            )
            no_pokemon_label.pack(pady=20)
        else:
            # Create multi-column layout for pokemon details
            current_row = 0

            for slot_data in pokemon_slots:
                slot_num = slot_data["slot"]

                # Pokemon header
                pokemon_header = ttk.Label(
                    scrollable_frame,
                    text=f"Pokemon {slot_num} (ID: {slot_data['monsno']}, Form: {slot_data['formno']})",
                    font=("TkDefaultFont", 10, "bold"),
                    foreground="blue",
                )
                pokemon_header.grid(
                    row=current_row,
                    column=0,
                    columnspan=columns_per_row * 2,
                    sticky="w",
                    pady=(15, 5),
                    padx=10,
                )
                current_row += 1

                # Define field categories for this pokemon
                field_categories = {
                    "Basic Info": [
                        (f"P{slot_num}Level", "Level", slot_data["level"]),
                        (f"P{slot_num}MonsNo", "Pokemon ID", slot_data["monsno"]),
                        (f"P{slot_num}FormNo", "Form", slot_data["formno"]),
                    ],
                    "IVs (Talents)": [
                        (f"P{slot_num}TalentHp", "HP IV", slot_data["talent_hp"]),
                        (f"P{slot_num}TalentAtk", "ATK IV", slot_data["talent_atk"]),
                        (f"P{slot_num}TalentDef", "DEF IV", slot_data["talent_def"]),
                        (
                            f"P{slot_num}TalentSpAtk",
                            "SP.ATK IV",
                            slot_data["talent_spatk"],
                        ),
                        (
                            f"P{slot_num}TalentSpDef",
                            "SP.DEF IV",
                            slot_data["talent_spdef"],
                        ),
                        (f"P{slot_num}TalentAgi", "SPEED IV", slot_data["talent_agi"]),
                    ],
                    "EVs (Efforts)": [
                        (f"P{slot_num}EffortHp", "HP EV", slot_data["effort_hp"]),
                        (f"P{slot_num}EffortAtk", "ATK EV", slot_data["effort_atk"]),
                        (f"P{slot_num}EffortDef", "DEF EV", slot_data["effort_def"]),
                        (
                            f"P{slot_num}EffortSpAtk",
                            "SP.ATK EV",
                            slot_data["effort_spatk"],
                        ),
                        (
                            f"P{slot_num}EffortSpDef",
                            "SP.DEF EV",
                            slot_data["effort_spdef"],
                        ),
                        (f"P{slot_num}EffortAgi", "SPEED EV", slot_data["effort_agi"]),
                    ],
                }

                for category, fields in field_categories.items():
                    # Category subheader
                    category_label = ttk.Label(
                        scrollable_frame,
                        text=category,
                        font=("TkDefaultFont", 9, "bold"),
                        foreground="darkgreen",
                    )
                    category_label.grid(
                        row=current_row,
                        column=0,
                        columnspan=columns_per_row * 2,
                        sticky="w",
                        pady=(5, 2),
                        padx=20,
                    )
                    current_row += 1

                    # Fields in multiple columns
                    current_col = 0
                    for field_key, display_name, value in fields:
                        # Label
                        label = ttk.Label(scrollable_frame, text=f"{display_name}:")
                        label.grid(
                            row=current_row,
                            column=current_col * 2,
                            sticky="w",
                            padx=(30 if current_col == 0 else 10, 5),
                            pady=1,
                        )

                        # Entry
                        var = tk.StringVar(value=str(value))
                        entry = ttk.Entry(
                            scrollable_frame, textvariable=var, width=field_width
                        )
                        entry.grid(
                            row=current_row,
                            column=current_col * 2 + 1,
                            sticky="w",
                            padx=(0, 15),
                            pady=1,
                        )

                        self.trainer_entries[field_key] = var

                        # Move to next column
                        current_col += 1

                        # If we've filled all columns, move to next row
                        if current_col >= columns_per_row:
                            current_col = 0
                            current_row += 1

                    # If we didn't fill the last row completely, move to next row for next category
                    if current_col > 0:
                        current_row += 1
                        current_col = 0

        # Configure column weights for better distribution
        for col in range(columns_per_row * 2):
            scrollable_frame.columnconfigure(col, weight=1 if col % 2 == 1 else 0)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def _create_trainer_level_controls(self, parent):
        """Create the level editing controls for batch editing."""
        # Level modification input
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(input_frame, text="Level Modification:").pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self.level_input = ttk.Entry(
            input_frame, textvariable=self.level_input_var, width=20
        )
        self.level_input.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(input_frame, text="(e.g., +10, -5, 20%)").pack(
            side=tk.LEFT, padx=(0, 20)
        )

        # Level constraints
        ttk.Label(input_frame, text="Min Level:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.min_level_var, width=5).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        ttk.Label(input_frame, text="Max Level:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.max_level_var, width=5).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        # Trainer selection frame (NEW - for batch editing)
        trainer_frame = ttk.Frame(parent)
        trainer_frame.pack(fill="x", pady=(10, 10))

        ttk.Label(trainer_frame, text="Target Trainers:").pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self.trainer_ids_input = ttk.Entry(
            trainer_frame, textvariable=self.trainer_ids_var, width=40
        )
        self.trainer_ids_input.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(
            trainer_frame, text="(Leave empty for ALL trainers, or specify IDs: 1,2,3)"
        ).pack(side=tk.LEFT, padx=(0, 10))

    def _preview_trainer_changes(self):
        """Preview changes for the selected trainer."""
        selected = self.selected_trainer_var.get()
        if not selected or selected not in self.trainer_lookup:
            messagebox.showwarning("No Selection", "Please select a trainer first.")
            return

        level_modification = self.level_input_var.get().strip()
        if not level_modification:
            messagebox.showwarning(
                "No Modification", "Please enter a level modification."
            )
            return

        try:
            # Get trainer data
            trainer_data = self.trainer_lookup[selected]
            trainer_id = trainer_data.get("ID", 0)

            # Apply level modification using existing logic
            from core.level_editor import LevelEditor

            level_editor = LevelEditor()

            # Parse the modification
            operation_type, value = level_editor.parse_level_modification(
                level_modification
            )

            # Create a temporary list with just this trainer for preview
            preview_data = [trainer_data.copy()]

            # Use existing level modification logic
            level_editor.modification_history = []
            try:
                result = level_editor.apply_level_modification(
                    preview_data,
                    operation_type,
                    value,
                    min_level=int(self.min_level_var.get()),
                    max_level=int(self.max_level_var.get()),
                    selected_trainers=[trainer_id],  # Only apply to selected trainer
                )

                # Show preview dialog
                preview_text = f"Preview for Trainer #{trainer_id}:\n\n"
                for i in range(1, 7):
                    original_level = trainer_data.get(f"P{i}Level", 0)
                    new_level = preview_data[0].get(f"P{i}Level", 0)
                    if original_level > 0:  # Only show pokemon that exist
                        preview_text += f"P{i} Level: {original_level} → {new_level}\n"

                messagebox.showinfo("Preview Changes", preview_text)

            except Exception as e:
                messagebox.showerror(
                    "Preview Error", f"Error applying modification: {str(e)}"
                )

        except Exception as e:
            messagebox.showerror("Preview Error", f"Error during preview: {str(e)}")

    def _apply_trainer_changes(self):
        """Apply changes for the selected trainer."""
        selected = self.selected_trainer_var.get()
        if not selected or selected not in self.trainer_lookup:
            messagebox.showwarning("No Selection", "Please select a trainer first.")
            return

        level_modification = self.level_input_var.get().strip()
        if not level_modification:
            messagebox.showwarning(
                "No Modification", "Please enter a level modification."
            )
            return

        try:
            # Get trainer data
            trainer_data = self.trainer_lookup[selected]
            trainer_id = trainer_data.get("ID", 0)

            # Apply level modification using existing logic
            from core.level_editor import LevelEditor

            level_editor = LevelEditor()

            # Parse the modification
            operation_type, value = level_editor.parse_level_modification(
                level_modification
            )

            # Apply to the actual trainer data in the dataset
            if self.trainer_poke_data:
                actual_trainer = next(
                    (t for t in self.trainer_poke_data if t.get("ID") == trainer_id),
                    None,
                )

                if actual_trainer:
                    level_editor.modification_history = []
                    result = level_editor.apply_level_modification(
                        [actual_trainer],  # Apply to actual data
                        operation_type,
                        value,
                        min_level=int(self.min_level_var.get()),
                        max_level=int(self.max_level_var.get()),
                        selected_trainers=[trainer_id],
                    )

                    # Update the lookup data as well
                    trainer_data.update(actual_trainer)

                    # Refresh the trainer details display
                    self._load_trainer_details()

                    messagebox.showinfo(
                        "Success",
                        f"Applied level modification to Trainer #{trainer_id}",
                    )

                else:
                    messagebox.showerror("Error", "Could not find trainer in dataset.")
            else:
                messagebox.showerror("Error", "No trainer data available.")

        except Exception as e:
            messagebox.showerror("Apply Error", f"Error applying changes: {str(e)}")

    def _reset_trainer_selection(self):
        """Reset the selected trainer to original values."""
        selected = self.selected_trainer_var.get()
        if not selected or selected not in self.trainer_lookup:
            messagebox.showwarning("No Selection", "Please select a trainer first.")
            return

        if (
            hasattr(self, "original_trainer_poke_data")
            and self.original_trainer_poke_data
        ):
            trainer_data = self.trainer_lookup[selected]
            trainer_id = trainer_data.get("ID", 0)

            # Find original data
            original_trainer = next(
                (
                    t
                    for t in self.original_trainer_poke_data
                    if t.get("ID") == trainer_id
                ),
                None,
            )

            if original_trainer:
                # Reset both the lookup data and actual data
                trainer_data.update(original_trainer.copy())

                if self.trainer_poke_data:
                    actual_trainer = next(
                        (
                            t
                            for t in self.trainer_poke_data
                            if t.get("ID") == trainer_id
                        ),
                        None,
                    )
                    if actual_trainer:
                        actual_trainer.update(original_trainer.copy())

                # Refresh the display
                self._load_trainer_details()

                messagebox.showinfo(
                    "Reset", f"Reset Trainer #{trainer_id} to original values."
                )
            else:
                messagebox.showerror("Error", "Could not find original trainer data.")
        else:
            messagebox.showerror("Error", "No original data available for reset.")

    def _create_level_controls(self, parent):
        """Create the level editing controls (legacy method for compatibility)."""
        # This method is kept for compatibility with existing code
        # The new trainer editor uses _create_trainer_level_controls instead
        controls_frame = ttk.LabelFrame(parent, text="Level Editing", padding="5")
        controls_frame.pack(fill="x", pady=(0, 10))

        # Input frame
        input_frame = ttk.Frame(controls_frame)
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Level modification input
        ttk.Label(input_frame, text="Level Modification:").grid(
            row=0, column=0, padx=(0, 10)
        )
        self.level_input = ttk.Entry(
            input_frame, textvariable=self.level_input_var, width=20
        )
        self.level_input.grid(row=0, column=1, padx=(0, 10))
        ttk.Label(input_frame, text="(e.g., +10, -5, 20%)").grid(
            row=0, column=2, padx=(0, 20)
        )

        # Level constraints
        ttk.Label(input_frame, text="Min Level:").grid(row=0, column=3, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.min_level_var, width=5).grid(
            row=0, column=4, padx=(0, 10)
        )

        ttk.Label(input_frame, text="Max Level:").grid(row=0, column=5, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.max_level_var, width=5).grid(
            row=0, column=6, padx=(0, 10)
        )

        # Trainer selection
        ttk.Label(input_frame, text="Trainer IDs:").grid(
            row=1, column=0, padx=(0, 10), pady=(10, 0)
        )
        self.trainer_ids_input = ttk.Entry(
            input_frame, textvariable=self.trainer_ids_var, width=30
        )
        self.trainer_ids_input.grid(
            row=1, column=1, columnspan=2, padx=(0, 10), pady=(10, 0), sticky="ew"
        )
        ttk.Label(input_frame, text="(e.g., 57,38,289 or leave empty for all)").grid(
            row=1, column=3, columnspan=4, padx=(0, 0), pady=(10, 0)
        )

        # Bind event
        self.trainer_ids_var.trace("w", self._on_trainer_ids_changed)

        # Buttons frame
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.preview_button = ttk.Button(
            buttons_frame,
            text="Preview Changes",
            command=self._preview_changes,
            state="disabled",
        )
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))

        self.apply_button = ttk.Button(
            buttons_frame,
            text="Apply Changes",
            command=self._apply_changes,
            state="disabled",
        )
        self.apply_button.pack(side=tk.LEFT, padx=(0, 10))

        self.reset_button = ttk.Button(
            buttons_frame, text="Reset Data", command=self._reset_data, state="disabled"
        )
        self.reset_button.pack(side=tk.LEFT)

    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Folder...", command=self._select_folder)
        file_menu.add_command(label="Select File...", command=self._select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export...", command=self._export_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _select_folder(self):
        """Select a folder containing ROMFS structure."""
        folder_path = filedialog.askdirectory(title="Select ROMFS Folder")
        if folder_path:
            self._process_folder_selection(folder_path)

    def _select_file(self):
        """Select a single BDSP data file."""
        filetypes = [
            ("All Supported", "masterdatas;personal_masterdatas"),
            ("Masterdatas files", "masterdatas"),
            ("Personal masterdatas", "personal_masterdatas"),
            ("All files", "*.*"),
        ]
        file_path = filedialog.askopenfilename(
            title="Select BDSP Data File", filetypes=filetypes
        )
        if file_path:
            self._process_file_selection(file_path)

    def _process_folder_selection(self, folder_path: str):
        """Process folder selection and detect ROMFS structure."""
        try:
            detected = FileDetector.detect_romfs_structure(folder_path)
            # Convert to match our type signature
            self.detected_files = {}
            for file_type in SUPPORTED_FILES.keys():
                self.detected_files[file_type] = detected.get(file_type)
            self.is_single_file_mode = False
            self._update_detected_files_tree()
            self._update_left_status()

        except Exception as e:
            ErrorDialog.show_error(self.root, "Folder Detection Error", str(e))

    def _process_file_selection(self, file_path: str):
        """Process single file selection."""
        try:
            file_type = FileDetector.get_file_type(file_path)
            if not file_type:
                raise ValueError(
                    f"Unsupported file type: {os.path.basename(file_path)}"
                )

            self.detected_files = {file_type: file_path}
            # Add other supported types as None
            for supported_type in SUPPORTED_FILES.keys():
                if supported_type not in self.detected_files:
                    self.detected_files[supported_type] = None

            self.is_single_file_mode = True
            self._update_detected_files_tree()
            self._update_left_status()

        except Exception as e:
            ErrorDialog.show_error(self.root, "File Selection Error", str(e))

    def _update_detected_files_tree(self):
        """Update the detected files tree display."""
        # Clear existing items
        for item in self.detected_tree.get_children():
            self.detected_tree.delete(item)

        # Add detected files
        for file_type, file_path in self.detected_files.items():
            display_name = SUPPORTED_FILES.get(file_type, {}).get(
                "display_name", file_type
            )

            if file_path:
                # File found
                item_id = self.detected_tree.insert(
                    "", "end", text=f"✓ {display_name}", values=(file_type,)
                )
            else:
                # File not found
                item_id = self.detected_tree.insert(
                    "", "end", text=f"⚫ {display_name}", values=(file_type,)
                )

    def _update_left_status(self):
        """Update the left panel status message."""
        found_count = sum(
            1 for path in self.detected_files.values() if path is not None
        )
        total_count = len(self.detected_files)

        if self.is_single_file_mode:
            self.left_status_var.set(f"Single file mode - {found_count} file selected")
        else:
            self.left_status_var.set(
                f"ROMFS mode - {found_count}/{total_count} files detected"
            )

    def _on_file_selected(self, event):
        """Handle file selection in detected files tree."""
        selection = self.detected_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.detected_tree.item(item, "values")
        if values:
            file_type = values[0]
            self.selected_file_type = file_type
            self._update_content_tree(file_type)

    def _update_content_tree(self, file_type: str):
        """Update the content tree for the selected file type."""
        # Clear existing items
        for item in self.content_tree.get_children():
            self.content_tree.delete(item)

        file_path = self.detected_files.get(file_type)
        if not file_path:
            self.content_tree.insert("", "end", text="⚫ File not found")
            return

        # Get supported content for this file type
        supported_content = SUPPORTED_FILES.get(file_type, {}).get(
            "supported_content", []
        )

        if not supported_content:
            self.content_tree.insert("", "end", text="⚫ No supported content")
            return

        # Add content items
        for content_name in supported_content:
            display_name = CONTENT_TYPES.get(content_name, {}).get(
                "display_name", content_name
            )

            if is_content_supported(file_type, content_name):
                # Supported content
                item_id = self.content_tree.insert(
                    "", "end", text=f"► {display_name}", values=(content_name,)
                )
            else:
                # Unsupported content (grayed out)
                item_id = self.content_tree.insert(
                    "", "end", text=f"⚫ {display_name}", values=(content_name,)
                )

    def _on_content_selected(self, event):
        """Handle content selection in content tree."""
        selection = self.content_tree.selection()
        if not selection or not self.selected_file_type:
            # Show welcome message when nothing is selected
            self.selected_content = None
            self.editor_info_var.set("No content selected")
            self._show_welcome_message()
            self._update_ui_state()
            return

        item = selection[0]
        values = self.content_tree.item(item, "values")
        if values:
            content_name = values[0]

            # Only allow supported content
            if is_content_supported(self.selected_file_type, content_name):
                self.selected_content = content_name
                self._load_content_editor(self.selected_file_type, content_name)
            else:
                # Unsupported content, show welcome message
                self.selected_content = None
                self.editor_info_var.set("No content selected")
                self._show_welcome_message()
                self._update_ui_state()

    def _load_content_editor(self, file_type: str, content_name: str):
        """Load the appropriate editor for the selected content."""
        file_path = self.detected_files.get(file_type)
        if not file_path:
            ErrorDialog.show_error(self.root, "Load Error", "File not found")
            return

        if content_name == "TrainerTable":
            self._load_trainer_table_editor(file_path, file_type)
        elif content_name == "PersonalTable":
            self._load_personal_table_editor(file_path, file_type)
        else:
            ErrorDialog.show_error(
                self.root, "Editor Error", f"No editor available for {content_name}"
            )

    def _load_trainer_table_editor(self, file_path: str, file_type: str):
        """Load the TrainerTable editor with data from the specified file."""

        def load_in_thread():
            try:
                # Load file through unpacker
                trainer_data = self.unpacker.load_trainer_file(file_path, file_type)

                # Update UI in main thread
                self.root.after(
                    0, lambda: self._on_trainer_data_loaded(trainer_data, file_path)
                )

            except Exception as exc:
                # Capture the exception in a different variable name
                error_message = str(exc)
                self.root.after(
                    0,
                    lambda: ErrorDialog.show_error(
                        self.root,
                        "Load Error",
                        f"Failed to load TrainerTable: {error_message}",
                    ),
                )

        # Start loading in background thread
        threading.Thread(target=load_in_thread, daemon=True).start()

        # Update UI to show loading
        self.editor_info_var.set("Loading TrainerTable...")
        self._update_ui_state()

    def _on_trainer_data_loaded(self, trainer_data: Dict[str, Any], file_path: str):
        """Handle successful trainer data loading."""
        self.trainer_data = trainer_data
        self.current_file_path = file_path
        self.trainer_poke_data = self.unpacker.extract_trainer_poke_data()
        self.original_trainer_poke_data = copy.deepcopy(self.trainer_poke_data)

        # Initialize selected trainers to all trainers (for batch operations)
        # This ensures that when the trainer ID field is empty, all trainers are selected
        self.selected_trainers = {
            entry.get("ID", 0) for entry in self.trainer_poke_data
        }

        # Update editor info
        self.editor_info_var.set(f"TrainerTable Editor - {os.path.basename(file_path)}")

        # Create the trainer table editor interface now that we have data
        self._create_trainer_table_editor()

        # Populate the data tree
        self._populate_data_tree()
        self._update_ui_state()

    def _load_personal_table_editor(self, file_path: str, file_type: str):
        """Load the PersonalTable editor with data from the specified file."""

        def load_in_thread():
            try:
                # Load file through unpacker
                data = self.unpacker.load_trainer_file(file_path, file_type)

                # Update UI in main thread
                self.root.after(
                    0, lambda: self._on_personal_data_loaded(data, file_path)
                )

            except Exception as exc:
                # Capture the exception in a different variable name
                error_message = str(exc)
                self.root.after(
                    0,
                    lambda: ErrorDialog.show_error(
                        self.root,
                        "Load Error",
                        f"Failed to load PersonalTable: {error_message}",
                    ),
                )

        # Start loading in background thread
        threading.Thread(target=load_in_thread, daemon=True).start()

        # Update UI to show loading
        self.editor_info_var.set("Loading PersonalTable...")
        self._update_ui_state()

    def _on_personal_data_loaded(self, data: Dict[str, Any], file_path: str):
        """Handle successful personal data loading."""
        self.trainer_data = data  # Using same variable for consistency
        self.current_file_path = file_path
        self.personal_data = self.unpacker.extract_personal_data()
        self.original_personal_data = copy.deepcopy(self.personal_data)

        # Update editor info
        self.editor_info_var.set(
            f"PersonalTable Editor - {os.path.basename(file_path)}"
        )

        # Create the personal table editor interface now that we have data
        self._create_personal_table_editor()

        self._update_ui_state()

    def _create_personal_table_editor(self):
        """Create the PersonalTable editor interface."""
        # Clear any existing content
        for widget in self.editor_content_frame.winfo_children():
            widget.destroy()

        if not self.personal_data:
            return

        # Main container
        main_frame = ttk.Frame(self.editor_content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Pokemon selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Select Pokemon", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        # Create Pokemon dropdown
        ttk.Label(selection_frame, text="Pokemon:").pack(side=tk.LEFT, padx=(0, 5))

        # Prepare Pokemon list for dropdown
        self.pokemon_list = []
        self.pokemon_lookup = {}

        # personal_data is a list of Pokemon entries
        if self.personal_data:
            for entry in self.personal_data:
                pokemon_id = entry.get("id", 0)
                # Use ID as display name for now (could be enhanced with actual Pokemon names)
                display_name = f"#{pokemon_id:03d}"
                self.pokemon_list.append(display_name)
                self.pokemon_lookup[display_name] = entry

        self.selected_pokemon_var = tk.StringVar()
        self.pokemon_dropdown = ttk.Combobox(
            selection_frame,
            textvariable=self.selected_pokemon_var,
            values=self.pokemon_list,
            state="readonly",
            width=20,
        )
        self.pokemon_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        self.pokemon_dropdown.bind("<<ComboboxSelected>>", self._on_pokemon_selected)

        # Set default selection
        if self.pokemon_list:
            self.pokemon_dropdown.set(self.pokemon_list[0])

        # Pokemon stats frame
        self.stats_frame = ttk.LabelFrame(main_frame, text="Pokemon Stats", padding=10)
        self.stats_frame.pack(fill=tk.BOTH, expand=True)

        # Load initial Pokemon data
        if self.pokemon_list:
            self._load_pokemon_stats()

        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Save button
        self.save_personal_button = ttk.Button(
            button_frame, text="Save Changes", command=self._save_personal_changes
        )
        self.save_personal_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Reset button
        self.reset_personal_button = ttk.Button(
            button_frame, text="Reset", command=self._reset_personal_changes
        )
        self.reset_personal_button.pack(side=tk.RIGHT)

    def _on_pokemon_selected(self, event=None):
        """Handle Pokemon selection change."""
        self._load_pokemon_stats()

    def _load_pokemon_stats(self):
        """Load stats for the currently selected Pokemon."""
        selected = self.selected_pokemon_var.get()
        if not selected or selected not in self.pokemon_lookup:
            return

        # Clear existing stats widgets
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        pokemon_data = self.pokemon_lookup[selected]

        # Create scrollable frame for stats
        # Remove fixed height to allow dynamic sizing
        canvas = tk.Canvas(self.stats_frame)
        scrollbar = ttk.Scrollbar(
            self.stats_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Stats entry fields
        self.pokemon_entries = {}

        # Get layout configuration
        editor_config = UI_CONFIG.get("personal_table_editor", {})
        columns_per_row = editor_config.get("columns_per_row", 3)
        field_width = editor_config.get("field_width", 12)
        category_spacing = editor_config.get("category_spacing", 15)

        # Define stat categories and their fields (reorganized for better layout)
        stat_categories = {
            "Basic Stats": [
                "basic_hp",
                "basic_atk",
                "basic_def",
                "basic_agi",
                "basic_spatk",
                "basic_spdef",
            ],
            "Types & Abilities": ["type1", "type2", "tokusei1", "tokusei2", "tokusei3"],
            "Physical Traits": ["height", "weight", "color", "sex"],
            "Experience & Growth": [
                "exp_value",
                "give_exp",
                "grow",
                "initial_friendship",
            ],
            "Breeding": [
                "egg_group1",
                "egg_group2",
                "egg_birth",
                "egg_monsno",
                "egg_formno",
            ],
            "Capture & Items": ["get_rate", "rank", "item1", "item2", "item3"],
            "Machines": [
                "machine1",
                "machine2",
                "machine3",
                "machine4",
                "hiden_machine",
            ],
            "Form & Sprite Data": ["form_index", "form_max", "monsno", "gra_no"],
            "Regional & Inheritance": [
                "chihou_zukan_no",
                "egg_formno_kawarazunoishi",
                "egg_form_inherit_kawarazunoishi",
            ],
        }

        # Create a multi-column layout
        current_row = 0
        current_col = 0

        for category, fields in stat_categories.items():
            # Calculate how many fields are actually available for this category
            available_fields = [field for field in fields if field in pokemon_data]

            if not available_fields:
                continue

            # Category header spans full width
            category_label = ttk.Label(
                scrollable_frame,
                text=category,
                font=("TkDefaultFont", 10, "bold"),
                foreground="blue",
            )
            category_label.grid(
                row=current_row,
                column=0,
                columnspan=columns_per_row
                * 2,  # Span all columns (label + entry pairs)
                sticky="w",
                pady=(category_spacing, 5),
                padx=10,
            )
            current_row += 1

            # Reset column for fields
            current_col = 0

            # Create fields in multiple columns
            for field in available_fields:
                # Label
                label = ttk.Label(scrollable_frame, text=f"{field}:")
                label.grid(
                    row=current_row,
                    column=current_col * 2,  # Even columns for labels
                    sticky="w",
                    padx=(20 if current_col == 0 else 10, 5),
                    pady=2,
                )

                # Entry
                var = tk.StringVar(value=str(pokemon_data[field]))
                entry = ttk.Entry(scrollable_frame, textvariable=var, width=field_width)
                entry.grid(
                    row=current_row,
                    column=current_col * 2 + 1,  # Odd columns for entries
                    sticky="w",
                    padx=(0, 15),
                    pady=2,
                )

                self.pokemon_entries[field] = var

                # Move to next column
                current_col += 1

                # If we've filled all columns, move to next row
                if current_col >= columns_per_row:
                    current_col = 0
                    current_row += 1

            # If we didn't fill the last row completely, move to next row for next category
            if current_col > 0:
                current_row += 1
                current_col = 0

            # Add extra spacing after each category
            current_row += 1

        # Configure column weights for better distribution
        for col in range(columns_per_row * 2):
            scrollable_frame.columnconfigure(col, weight=1 if col % 2 == 1 else 0)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def _save_personal_changes(self):
        """Save changes to the PersonalTable."""
        selected = self.selected_pokemon_var.get()
        if not selected or selected not in self.pokemon_lookup:
            return

        # Update the pokemon data with entry values
        pokemon_data = self.pokemon_lookup[selected]

        for field, var in self.pokemon_entries.items():
            try:
                value = var.get()
                # Try to convert to appropriate type (int for most fields)
                if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                    pokemon_data[field] = int(value)
                else:
                    pokemon_data[field] = value
            except ValueError:
                # Keep original value if conversion fails
                pass

        # Update the personal data through unpacker
        try:
            if self.personal_data is not None:
                self.unpacker.update_personal_data(self.personal_data)

                # Update info
                self.editor_info_var.set(
                    f"PersonalTable Editor - Changes saved for {selected}"
                )
            else:
                ErrorDialog.show_error(
                    self.root, "Save Error", "No PersonalTable data available to save"
                )

        except Exception as e:
            ErrorDialog.show_error(
                self.root,
                "Save Error",
                f"Failed to save PersonalTable changes: {str(e)}",
            )

    def _reset_personal_changes(self):
        """Reset PersonalTable to original values."""
        if hasattr(self, "original_personal_data"):
            self.personal_data = copy.deepcopy(self.original_personal_data)
            self._load_pokemon_stats()
            self.editor_info_var.set("PersonalTable Editor - Changes reset")

    def _update_ui_state(self):
        """Update the UI state based on current data."""
        has_trainer_data = self.trainer_data is not None

        # Enable/disable buttons (only if they exist)
        if hasattr(self, "preview_button"):
            self.preview_button.config(
                state="normal" if has_trainer_data else "disabled"
            )
        if hasattr(self, "apply_button"):
            self.apply_button.config(state="normal" if has_trainer_data else "disabled")
        if hasattr(self, "reset_button"):
            self.reset_button.config(state="normal" if has_trainer_data else "disabled")

        # Export button should always exist since it's in the left panel
        self.export_button.config(state="normal" if has_trainer_data else "disabled")

    def _populate_data_tree(self):
        """Legacy method - no longer used with new dropdown interface."""
        # This method is kept for compatibility but does nothing
        # The new trainer interface doesn't use a data tree
        pass

    def _on_treeview_click(self, event):
        """Legacy method - no longer used with new dropdown interface."""
        # This method is kept for compatibility but does nothing
        pass

    def _on_trainer_ids_changed(self, *args):
        """Handle changes to the trainer IDs input field."""
        # Note: This method is kept for compatibility but no longer updates selected_trainers
        # The trainer ID field is now read directly in preview/apply methods for batch operations
        pass

    def _preview_changes(self):
        """Preview the level changes without applying them."""
        if not self._validate_inputs() or not self.trainer_poke_data:
            return

        try:
            level_modification = self.level_input_var.get().strip()
            min_level = int(self.min_level_var.get())
            max_level = int(self.max_level_var.get())

            # Use trainer ID field to determine which trainers to modify (NOT dropdown selection)
            trainer_ids_text = self.trainer_ids_var.get().strip()

            if not trainer_ids_text:
                # Empty field = apply to ALL trainers (batch editing default)
                selected_data = copy.deepcopy(self.trainer_poke_data)
                operation_scope = "ALL trainers"
            else:
                # Parse specific trainer IDs from the input field
                try:
                    trainer_ids = [
                        int(id_str.strip())
                        for id_str in trainer_ids_text.split(",")
                        if id_str.strip()
                    ]
                    selected_data = [
                        entry
                        for entry in self.trainer_poke_data
                        if entry.get("ID", 0) in trainer_ids
                    ]
                    operation_scope = f"trainers {trainer_ids_text}"
                except ValueError:
                    messagebox.showerror(
                        "Invalid Input",
                        "Please enter valid trainer IDs (e.g., 1,2,3 or leave empty for all)",
                    )
                    return

            if not selected_data:
                messagebox.showwarning(
                    "Preview", f"No trainer data found for {operation_scope}"
                )
                return

            # Preview changes
            preview_data = copy.deepcopy(selected_data)
            modified_data = self.level_editor.apply_level_modification_from_string(
                preview_data, level_modification, min_level, max_level
            )

            # Show preview dialog with scope information
            self._show_preview_dialog(
                selected_data,
                modified_data,
                f"{level_modification} to {operation_scope}",
            )

        except Exception as e:
            ErrorDialog.show_error(self.root, "Preview Error", str(e))

    def _apply_changes(self):
        """Apply the level changes to the trainer data."""
        if not self._validate_inputs() or not self.trainer_poke_data:
            return

        try:
            level_modification = self.level_input_var.get().strip()
            min_level = int(self.min_level_var.get())
            max_level = int(self.max_level_var.get())

            # Use trainer ID field to determine which trainers to modify (NOT dropdown selection)
            trainer_ids_text = self.trainer_ids_var.get().strip()

            if not trainer_ids_text:
                # Empty field = apply to ALL trainers (batch editing default)
                target_indices = list(range(len(self.trainer_poke_data)))
                operation_scope = "ALL trainers"
            else:
                # Parse specific trainer IDs from the input field
                try:
                    trainer_ids = [
                        int(id_str.strip())
                        for id_str in trainer_ids_text.split(",")
                        if id_str.strip()
                    ]
                    target_indices = []
                    for i, entry in enumerate(self.trainer_poke_data):
                        if entry.get("ID", 0) in trainer_ids:
                            target_indices.append(i)
                    operation_scope = f"trainers {trainer_ids_text}"
                except ValueError:
                    messagebox.showerror(
                        "Invalid Input",
                        "Please enter valid trainer IDs (e.g., 1,2,3 or leave empty for all)",
                    )
                    return

            if not target_indices:
                messagebox.showwarning(
                    "Apply Changes", f"No trainer data found for {operation_scope}"
                )
                return

            # Apply changes to target trainers
            modified_count = 0
            for index in target_indices:
                trainer_data = [self.trainer_poke_data[index]]

                # Parse modification and apply
                operation_type, value = self.level_editor.parse_level_modification(
                    level_modification
                )
                result = self.level_editor.apply_level_modification(
                    trainer_data, operation_type, value, min_level, max_level
                )

                # The data was modified in-place, so trainer_data[0] now contains the changes
                self.trainer_poke_data[index] = trainer_data[0]
                modified_count += 1

            # Show success message with scope
            messagebox.showinfo(
                "Success",
                f"Applied level modification '{level_modification}' to {modified_count} trainer(s) ({operation_scope})",
            )

            # Refresh the current trainer display if one is selected
            if hasattr(self, "trainer_dropdown") and self.trainer_dropdown:
                current_selection = self.trainer_dropdown.get()
                if current_selection:
                    self._on_trainer_selected()

        except Exception as e:
            ErrorDialog.show_error(self.root, "Apply Changes Error", str(e))

    def _reset_data(self):
        """Reset trainer data to original values."""
        if not self.original_trainer_poke_data:
            return

        result = messagebox.askyesno(
            "Reset Data",
            "Are you sure you want to reset all trainer data to original values? This cannot be undone.",
        )

        if result:
            self.trainer_poke_data = copy.deepcopy(self.original_trainer_poke_data)
            self.unpacker.update_trainer_poke_data(self.trainer_poke_data)
            self._populate_data_tree()
            messagebox.showinfo("Reset Data", "Trainer data reset to original values")

    def _validate_inputs(self) -> bool:
        """Validate user inputs."""
        try:
            level_modification = self.level_input_var.get().strip()
            if not level_modification:
                messagebox.showerror(
                    "Validation Error", "Please enter a level modification"
                )
                return False

            min_level = int(self.min_level_var.get())
            max_level = int(self.max_level_var.get())

            if min_level < 1 or max_level > 100 or min_level > max_level:
                messagebox.showerror("Validation Error", "Invalid level constraints")
                return False

            return True

        except ValueError:
            messagebox.showerror("Validation Error", "Invalid numeric values")
            return False

    def _show_preview_dialog(self, original_data, modified_data, modification):
        """Show a preview dialog with changes."""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Preview Changes")
        preview_window.geometry("600x400")

        # Preview content
        frame = ttk.Frame(preview_window, padding="10")
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=f"Modification: {modification}",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(pady=(0, 10))

        # Create preview tree
        columns = ("trainer_id", "pokemon", "before", "after", "change")
        preview_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)

        preview_tree.heading("trainer_id", text="Trainer ID")
        preview_tree.heading("pokemon", text="Pokemon")
        preview_tree.heading("before", text="Before")
        preview_tree.heading("after", text="After")
        preview_tree.heading("change", text="Change")

        # Populate preview
        for i, (orig, mod) in enumerate(zip(original_data, modified_data)):
            trainer_id = orig.get("ID", 0)
            for j in range(1, 7):
                level_key = f"P{j}Level"
                before_level = orig.get(level_key, 0)
                after_level = mod.get(level_key, 0)

                if before_level > 0:  # Only show existing Pokemon
                    change = after_level - before_level
                    change_str = f"+{change}" if change > 0 else str(change)

                    preview_tree.insert(
                        "",
                        "end",
                        values=(
                            trainer_id,
                            f"P{j}",
                            before_level,
                            after_level,
                            change_str,
                        ),
                    )

        preview_tree.pack(fill="both", expand=True, pady=(0, 10))

        # Close button
        ttk.Button(preview_window, text="Close", command=preview_window.destroy).pack()

    def _export_files(self):
        """Export modified files based on selected mode."""
        if not self.trainer_data:
            messagebox.showwarning("Export", "No data to export")
            return

        mode = self.export_mode_var.get()

        if mode == "single":
            self._export_single_file()
        else:
            self._export_romfs_structure()

    def _export_single_file(self):
        """Export a single modified file."""
        if not self.current_file_path:
            return

        # Ask for output location
        filename = os.path.basename(self.current_file_path)
        output_path = filedialog.asksaveasfilename(
            title="Save Modified File",
            defaultextension="",
            filetypes=[("All files", "*.*")],
        )

        if output_path:
            try:
                self.unpacker.save_trainer_file(output_path, create_backup=False)
                messagebox.showinfo(
                    "Export", f"File exported successfully to:\n{output_path}"
                )
            except Exception as e:
                ErrorDialog.show_error(self.root, "Export Error", str(e))

    def _export_romfs_structure(self):
        """Export complete ROMFS structure with modifications."""
        if self.is_single_file_mode:
            messagebox.showwarning(
                "Export", "ROMFS export not available in single file mode"
            )
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select Export Directory")
        if output_dir:
            try:
                # Create ROMFS structure
                romfs_path = os.path.join(
                    output_dir, "romfs", "Data", "StreamingAssets", "AssetAssistant"
                )

                # Export all detected files to maintain structure
                exported_files = []
                for file_type, file_path in self.detected_files.items():
                    if file_path and os.path.exists(
                        file_path
                    ):  # Only export files that actually exist
                        # Determine target directory
                        if file_type == "masterdatas":
                            target_dir = os.path.join(romfs_path, "Dpr")
                        elif file_type == "personal_masterdatas":
                            target_dir = os.path.join(romfs_path, "Pml")
                        else:
                            continue

                        os.makedirs(target_dir, exist_ok=True)
                        target_path = os.path.join(
                            target_dir, os.path.basename(file_path)
                        )

                        # If this is the currently loaded and modified file, save modifications
                        if (
                            file_type == self.selected_file_type
                            and self.current_file_path == file_path
                            and self.trainer_data
                            is not None  # Only if we actually have modified data
                        ):
                            self.unpacker.save_trainer_file(
                                target_path, create_backup=False
                            )
                        else:
                            # Copy original file without modifications
                            shutil.copy2(file_path, target_path)

                        exported_files.append(
                            f"{file_type}: {os.path.basename(file_path)}"
                        )

                export_list = "\n".join(exported_files)
                messagebox.showinfo(
                    "Export",
                    f"ROMFS structure exported successfully to:\n{output_dir}\n\nExported files:\n{export_list}",
                )

            except Exception as e:
                ErrorDialog.show_error(self.root, "Export Error", str(e))

    def _show_about(self):
        """Show about dialog."""
        about_text = """BDSP-Batch-Editor
Multi-File Support Version

A tool for editing Pokémon Brilliant Diamond/Shining Pearl game data.

Features:
• Multi-file ROMFS structure support
• TrainerTable level editing
• Batch modifications with regex patterns
• Export to single files or complete ROMFS

For support, visit: https://discord.gg/5Qwz85EvC3"""

        messagebox.showinfo("About", about_text)

    def _on_closing(self):
        """Handle window closing."""
        # Clean up resources
        self.unpacker.cleanup()

        # Close the window
        self.root.quit()
        self.root.destroy()
