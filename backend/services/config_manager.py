import json
import os

CONFIG_FILE = "agent_config.json"

class ConfigManager:
    @staticmethod
    def load_config():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @staticmethod
    def save_config(config_data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
