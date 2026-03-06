"""
Module to handle cross-platform document printing.
Supports Windows via pywin32 (ShellExecute) and Linux via CUPS (lp/lpstat).
"""

import os
import platform
import subprocess
import time
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if platform.system().lower().startswith("win"):
    try:
        import win32api
        import win32print
    except ImportError:
        win32print = None
        win32api = None


class PrinterManager:
    """Cross-platform manager to list printers and dispatch print jobs."""

    # Time to wait (in seconds) on Windows to allow the external PDF viewer to spool the file
    WINDOWS_PRINT_DELAY = 3

    @staticmethod
    def is_windows() -> bool:
        """Check if the current operating system is Windows."""
        return platform.system().lower().startswith("win")

    @staticmethod
    def is_linux() -> bool:
        """Check if the current operating system is Linux."""
        return platform.system().lower().startswith("linux")

    def list_printers(self) -> list[str]:
        """
        List all available printers installed on the system.

        Returns:
            list[str]: A list containing the names of available printers.
        """
        if self.is_windows():
            return self._list_windows_printers()
        if self.is_linux():
            return self._list_linux_printers()
        return []

    def _list_windows_printers(self) -> list[str]:
        """Retrieve a list of available printers on Windows."""
        if not win32print:
            raise RuntimeError(
                "Library 'pywin32' is not installed. Run: pip install pywin32"
            )

        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return [printer[2] for printer in printers]

    def _list_linux_printers(self) -> list[str]:
        """Retrieve a list of available printers on Linux using CUPS."""
        try:
            result = subprocess.check_output(["lpstat", "-a"], text=True)
            return [line.split()[0] for line in result.splitlines() if line.strip()]
        except subprocess.CalledProcessError as e:
            logging.error("Failed to fetch printers on Linux: %s", e)
            return []

    def get_default_printer(self) -> str:
        """
        Retrieve the system's default printer name.

        Returns:
            str: The default printer name, or an empty string if not found.
        """
        if self.is_windows() and win32print:
            return win32print.GetDefaultPrinter()

        if self.is_linux():
            try:
                result = subprocess.check_output(["lpstat", "-d"], text=True)
                if "system default destination:" in result:
                    return result.split(":")[-1].strip()
            except subprocess.CalledProcessError:
                pass

        return ""

    def print_document(self, file_path: str, printer_name: str = None) -> bool:
        """
        Print a document (PDF or Image) to a specified printer.
        If no printer is provided, it defaults to the system's default printer.

        Args:
            file_path (str): The path to the file to be printed.
            printer_name (str, optional): The target printer name. Defaults to None.

        Returns:
            bool: True if the print job was dispatched successfully, False otherwise.
        """
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            logging.error("File not found -> %s", abs_path)
            return False

        target_printer = printer_name or self.get_default_printer()
        if not target_printer:
            logging.error("No printer specified and no default printer could be found.")
            return False

        logging.info("Sending '%s' to printer '%s'...", abs_path, target_printer)

        if self.is_windows():
            return self._print_windows(abs_path, target_printer)
        if self.is_linux():
            return self._print_linux(abs_path, target_printer)

        logging.error("Current operating system is not supported for printing.")
        return False

    def _print_windows(self, file_path: str, printer_name: str) -> bool:
        """Dispatch a print job on Windows using ShellExecute."""
        if not win32api:
            raise RuntimeError("Library 'pywin32' is not installed.")

        try:
            win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
            time.sleep(self.WINDOWS_PRINT_DELAY)
            return True
        except Exception as e:
            logging.error("Failed to execute print command on Windows: %s", e)
            return False

    def _print_linux(self, file_path: str, printer_name: str) -> bool:
        """Dispatch a print job on Linux using the 'lp' command."""
        try:
            subprocess.run(["lp", "-d", printer_name, file_path], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Failed to execute print command on Linux: %s", e)
            return False


if __name__ == "__main__":
    manager = PrinterManager()

    logging.info("--- Available Printers ---")
    available_printers = manager.list_printers()
    for printer in available_printers:
        print(f" - {printer}")

    default_printer = manager.get_default_printer()
    logging.info("Default Printer: %s", default_printer)

    # Target files to print
    target_files = ["./tmp/etiqueta_85x45.pdf"]

    for file_path in target_files:
        is_success = manager.print_document(file_path, printer_name=default_printer)

        if is_success:
            logging.info("Print job dispatched successfully: %s", file_path)
            # Clean up the file after printing if needed
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info("File removed: %s", file_path)
        else:
            logging.error("Failed to print file: %s", file_path)
