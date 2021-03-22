import logging


def setLoggingFormat(level=20):
    logging.basicConfig(
        format='{"@timestamp": "%(asctime)s","level": "%(levelname)s","thread": "%(threadName)s","name": "%(name)s","message": "%(message)s"}'
    )
    logging.getLogger().setLevel(level)
