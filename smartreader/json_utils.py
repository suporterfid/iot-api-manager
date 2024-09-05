# json_utils.py
def json_field(json_key):
    """
    Decorator to associate a JSON key with a Django model field.
    """
    def wrapper(func):
        func._json_key = json_key
        return func
    return wrapper
