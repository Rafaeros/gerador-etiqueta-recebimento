import json
import os
from typing import Any, Dict

class ConfigManager:
    """
    Global system configuration manager.
    Responsible for reading, validating, and saving the JSON configuration file.
    """
    
    def __init__(self, config_path: str = "configs.json") -> None:
        self.config_path = config_path
        self.is_new_install = False
        self.config = self._initialize_config()

    def _initialize_config(self) -> Dict[str, Any]:
        """
        Validates the existence of the config file. 
        If it doesn't exist, creates a default template and flags as a new install.
        
        Returns:
            Dict[str, Any]: Dictionary containing the configurations.
        """
        default_config = {
            "username": "",
            "password": "",
            "printer_name": ""
        }

        if not os.path.exists(self.config_path):
            self.is_new_install = True
            self._write_file(default_config)
            return default_config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.is_new_install = True
            self._write_file(default_config)
            return default_config

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the configuration."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the configuration and saves to the file."""
        self.config[key] = value
        self.save()

    def save(self) -> None:
        """Persists the current dictionary to the JSON file."""
        self._write_file(self.config)

    def _write_file(self, data: Dict[str, Any]) -> None:
        """Internal utility method to write to the file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_session_config(self) -> Dict[str, str]:
        """Retrieves the session credentials."""
        return {
            "username": self.get("username", ""),
            "password": self.get("password", "")
        }

    def set_session_config(self, session_config: Dict[str, str]) -> None:
        """Updates the session credentials and saves them."""
        self.config["username"] = session_config.get("username", "")
        self.config["password"] = session_config.get("password", "")
        self.save()