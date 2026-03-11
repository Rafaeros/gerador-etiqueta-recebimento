import os
import csv
from datetime import datetime
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
TMP_FOLDER = PROJECT_ROOT / "tmp"
LOGS_FOLDER = TMP_FOLDER / "logs"
LOG_FILE = LOGS_FOLDER / "print_log.csv"


def log_label_generation(label_type: str, qty: int):
    """
    Logs the generation of labels to a CSV file.
    """
    try:
        LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

        file_exists = LOG_FILE.exists()

        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M:%S")

        with open(LOG_FILE, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            if not file_exists:
                writer.writerow(["Data", "Hora", "Tipo", "Quantidade"])

            writer.writerow([date_str, time_str, label_type, qty])
    except Exception as e:
        print(f"Error logging label generation: {e}")
