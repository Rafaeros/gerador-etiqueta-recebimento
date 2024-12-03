""" Module to print labels from a list of file paths on a Default Printer"""

import os
import time
import win32api
import win32print

def print_labels(file_paths: list[str]) -> None:
    """Print labels from a list of file paths"""

    printer_name = win32print.GetDefaultPrinter()
    printer = win32print.OpenPrinter(printer_name)
    print(file_paths)
    try:
        for file_path in file_paths:
            print(file_path)
            if not os.path.exists(file_path):
                continue
            abs_path = os.path.abspath(file_path)
            time.sleep(2)
            win32api.ShellExecute(0, "print", abs_path, None, ".", 0)
    except FileNotFoundError:
        print("Arquivo nao encontrado")
        return
    finally:
        win32print.ClosePrinter(printer)


if __name__ == "__main__":
    print_labels(["./tmp/pending_labels.pdf", "./tmp/stock_labels.pdf"])
