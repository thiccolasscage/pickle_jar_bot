import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Set up file logging
log_file = os.path.join(log_dir, 'bot.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

class BotLogger:
    @staticmethod
    def log(message, level="info"):
        """Log a message with the specified level"""
        if level.lower() == "error":
            logging.error(message)
            print(f"ERROR: {message}")
        elif level.lower() == "warning":
            logging.warning(message)
            print(f"WARNING: {message}")
        else:
            logging.info(message)
            print(f"INFO: {message}")

# Create a singleton instance
logger = BotLogger()
