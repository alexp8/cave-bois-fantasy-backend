# Set up logging
import logging

logger = logging.getLogger('fantasy_trades_app')
logger.setLevel(logging.INFO)

# File handler to log to a file
file_handler = logging.FileHandler('fantasy_trades_app.log')
file_handler.setLevel(logging.INFO)

# Console handler to log to console (stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Add formatters for both handlers (optional but recommended)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)