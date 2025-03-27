import logging
import os

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)  # Ensure logs directory exists

log_file = os.path.join(log_dir, 'bot.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    filemode='a'
)

logger = logging.getLogger(__name__)
