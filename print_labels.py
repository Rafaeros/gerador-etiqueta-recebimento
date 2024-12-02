""" Module to print labels from a list of file paths on a Default Printer"""

import os
import win32api
import win32print

def print_labels(file_paths: list[str]) -> None:
    """Print labels from a list of file paths"""

    printer_name = win32print.GetDefaultPrinter()
    printer = win32print.OpenPrinter(printer_name)

    try:
        for file_path in file_paths:
            abs_path = os.path.abspath(file_path)
            win32api.ShellExecute(0, "print", abs_path, None, ".", 0)
            return
    except FileNotFoundError:
        print("Arquivo nao encontrado")
        return
    finally:
        win32print.ClosePrinter(printer)


if __name__ == "__main__":
    print_labels(["./tmp/pending_labels.pdf", "./tmp/stock_labels.pdf"])
