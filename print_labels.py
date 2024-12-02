""" Print labels from a list of file paths """

import os
import time
import win32api
import win32print

def print_labels(file_paths: list[str]) -> None:
    """Print labels from a list of file paths"""

    printer_name = win32print.GetDefaultPrinter()
    printer = win32print.OpenPrinter(printer_name)

    try:
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
            abs_path = os.path.abspath(file_path)
            print(abs_path)
            time.sleep(2)
            win32api.ShellExecute(0, "print", abs_path, None, ".", 0)
            return
    except FileNotFoundError:
        print("Arquivo nao encontrado")
        return
    finally:
        win32print.ClosePrinter(printer)


if __name__ == "__main__":
    print_labels(["./pending_labels.pdf", "./stock_labels.pdf"])
