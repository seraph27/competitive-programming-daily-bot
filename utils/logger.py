import logging
import os
from datetime import datetime

_logger_initialized = False

def get_logger(name=None):
    return logging.getLogger(name) if name else logging.getLogger()

def setup_logging(level=logging.INFO, log_dir="./logs", force=False, module_levels=None):
    global _logger_initialized
    if _logger_initialized and not force:
        return False
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, datetime.utcnow().strftime("%Y%m%d.log"))
    handlers = [logging.FileHandler(log_file), logging.StreamHandler()]
    logging.basicConfig(level=level, handlers=handlers, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if module_levels:
        for name, lvl in module_levels.items():
            logging.getLogger(name).setLevel(lvl)
    _logger_initialized = True
    return True
