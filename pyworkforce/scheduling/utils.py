

def check_positive_integer(name, value):
    if value <= 0 or not isinstance(value, int):
        raise ValueError(f"{name} must be a positive integer")
    else:
        return True


def check_positive_float(name, value):
    if value <= 0 or not isinstance(value, float):
        raise ValueError(f"{name} must be a positive float")
    else:
        return True
