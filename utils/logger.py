import logging

logging.basicConfig(
    filename="logs/bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

class BotLogger:
    @staticmethod
    def log(message, level="info"):
        if level == "error":
            logging.error(message)
        else:
            logging.info(message)

logger = BotLogger()
