import logging


def setLoggingFormat(level=20):
    logging.basicConfig(
        format='{"@timestamp": "%(asctime)s","level": "%(levelname)s","thread": "%(threadName)s","name": "%(name)s","message": "%(message)s"}'
    )
    logging.getLogger().setLevel(level)


def letUserPickBackupFile(options):
    print("Please select:")
    for idx, element in enumerate(options):
        print("{}) {}".format(idx + 1, element))
    i = input("Enter number: ")
    try:
        if 0 < int(i) <= len(options):
            return options[int(i) - 1]
    except Exception as e:
        logging.error(e)
    return None
