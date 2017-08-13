import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
handler = logging.handlers.RotatingFileHandler('mercury.log', maxBytes=1024**2, backupCount=1)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s '))
logger.addHandler(handler)
logger.setLevel(1)
