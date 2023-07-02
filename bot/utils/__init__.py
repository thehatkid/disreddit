import logging
from datetime import datetime

from . import exceptions
from .redditfeed import RedditFeed


class LogFormatter(logging.Formatter):
    """Custom log formatter for Python Logging module."""

    # ANSI color/style formats
    BLACK = '\x1b[30m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    BLUE = '\x1b[34m'
    MAGENTA = '\x1b[35m'
    CYAN = '\x1b[36m'
    WHITE = '\x1b[37m'
    LIGHT_BLACK = '\x1b[90m'
    LIGHT_RED = '\x1b[91m'
    LIGHT_GREEN = '\x1b[92m'
    LIGHT_YELLOW = '\x1b[93m'
    LIGHT_BLUE = '\x1b[94m'
    LIGHT_MAGENTA = '\x1b[95m'
    LIGHT_CYAN = '\x1b[96m'
    LIGHT_WHITE = '\x1b[97m'
    RESET = '\x1b[0m'
    BOLD = '\x1b[1m'
    UNDERLINE = '\x1b[4m'

    def __init__(self, fmt):
        super().__init__()
        self.FORMATS = {
            logging.DEBUG: f'{self.MAGENTA}{fmt}{self.RESET}',
            logging.INFO: f'{self.LIGHT_WHITE}{fmt}{self.RESET}',
            logging.WARNING: f'{self.YELLOW}{fmt}{self.RESET}',
            logging.ERROR: f'{self.LIGHT_RED}{fmt}{self.RESET}',
            logging.CRITICAL: f'{self.RED}{fmt}{self.RESET}'
        }

    def format(self, record):
        custom_format = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(custom_format)
        return formatter.format(record)


def uptime_to_str(date: datetime) -> str:
    """Converts :class:`datetime` uptime to :class:`str`."""
    uptime = datetime.now().timestamp() - date.timestamp()
    time_d = int(uptime) / (3600 * 24)
    time_h = int(uptime) / 3600 - int(time_d) * 24
    time_min = int(uptime) / 60 - int(time_h) * 60 - int(time_d) * 24 * 60
    time_sec = int(uptime) - int(time_min) * 60 - int(time_h) * 3600 - int(time_d) * 24 * 60 * 60
    uptime_str = '%01d days, %02d hours, %02d minutes, and %02d seconds' % (time_d, time_h, time_min, time_sec)
    return uptime_str


def sizeof_fmt(size: float) -> str:
    """Formats :class:`float` size bytes to human readable :class:`str`."""
    for unit in ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']:
        if abs(size) < 1024.0:
            return f'{size:3.1f} {unit}'
        size /= 1024.0
    return f'{size:.1f} YiB'
