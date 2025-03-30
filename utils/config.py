import json

class ConfigManager:
    def __init__(self):
        with open("config.json") as f:
            self.config = json.load(f)

    def get(self, key, default=None):
        return self.config.get(key, default)

config = ConfigManager()
