def isid(obj):
    """
    Returns true if the given object can be converted to an ID,
    false otherwise.
    """
    if hasattr(obj, "id"):
        return True
    else:
        try:
            int(obj)
        except ValueError:
            return False
        else:
            return True
