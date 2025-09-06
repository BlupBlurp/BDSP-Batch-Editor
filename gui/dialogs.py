"""
Dialog windows for BDSP-Batch-Editor.
Contains file selection, confirmation, and other dialog windows.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from typing import Optional, List, Dict, Any


class FileSelectionDialog:
    """Dialog for selecting trainer data files."""

    @staticmethod
    def select_trainer_file(parent=None) -> Optional[str]:
        """
        Open file dialog to select a trainer JSON file.

        Args:
            parent: Parent window

        Returns:
            Selected file path or None if cancelled
        """
        filetypes = [("JSON files", "*.json"), ("All files", "*.*")]

        file_path = filedialog.askopenfilename(
            parent=parent,
            title="Select TrainerTable JSON File",
            filetypes=filetypes,
            initialdir=".",
        )

        return file_path if file_path else None

    @staticmethod
    def select_save_location(
        parent=None, default_name: str = "TrainerTable_modified.json"
    ) -> Optional[str]:
        """
        Open file dialog to select save location.

        Args:
            parent: Parent window
            default_name: Default filename

        Returns:
            Selected save path or None if cancelled
        """
        filetypes = [("JSON files", "*.json"), ("All files", "*.*")]

        file_path = filedialog.asksaveasfilename(
            parent=parent,
            title="Save Modified File As",
            filetypes=filetypes,
            defaultextension=".json",
            initialfile=default_name,
        )

        return file_path if file_path else None


class BackupConfirmationDialog:
    """Dialog for backup confirmation."""

    @staticmethod
    def confirm_backup(parent=None, file_path: str = "") -> bool:
        """
        Show backup confirmation dialog.

        Args:
            parent: Parent window
            file_path: Path of file to be backed up

        Returns:
            True if user confirms backup, False otherwise
        """
        message = (
            f"A backup will be created before modifying the file:\n\n"
            f"{file_path}\n\n"
            f"The backup will be saved as:\n"
            f"{file_path}.backup\n\n"
            f"Do you want to continue?"
        )

        result = messagebox.askyesno("Backup Confirmation", message, icon="question")

        return result


class ErrorDialog:
    """Dialog for displaying error messages."""

    @staticmethod
    def show_error(
        parent=None, title: str = "Error", message: str = "", details: str = ""
    ):
        """Show an error dialog with optional details."""
        if details:
            full_message = f"{message}\n\nDetails:\n{details}"
        else:
            full_message = message

        if parent:
            messagebox.showerror(title, full_message, parent=parent)
        else:
            messagebox.showerror(title, full_message)

    @staticmethod
    def show_warning(parent=None, title: str = "Warning", message: str = ""):
        """Show a warning dialog."""
        if parent:
            messagebox.showwarning(title, message, parent=parent)
        else:
            messagebox.showwarning(title, message)

    @staticmethod
    def show_info(parent=None, title: str = "Information", message: str = ""):
        """Show an information dialog."""
        if parent:
            messagebox.showinfo(title, message, parent=parent)
        else:
            messagebox.showinfo(title, message)
