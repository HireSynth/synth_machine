import logging


def udf(func):
    def wrapper(*args, **kwargs):
        logging.debug(f"Starting user defined function: {func.__name__}")
        result = func(*args, **kwargs)
        logging.debug(f"User defined function: {func.__name__} complete")
        return result

    return wrapper
