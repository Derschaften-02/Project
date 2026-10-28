
_registry = {}

def register_model(cls):
    """
    Class decorator to register a model.
    """
    if not hasattr(cls, "table"):
        raise AttributeError(f"{cls.__name__} missing 'table' attribute")

    _registry[cls.table] = cls()
    return cls


def all_models():
    return _registry
