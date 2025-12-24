from logging.config import dictConfig

from app.config import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)s%(reset)s:"
                    " %(module)s: %(message)s",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "purple",
            },
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
    },

    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console"],
    },
}

def set_logging():
    dictConfig(LOGGING_CONFIG)