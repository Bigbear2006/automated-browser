import logging.config

logger = logging.getLogger('automated-browser')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'default'}
    },
    'loggers': {
        'automated-browser': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
