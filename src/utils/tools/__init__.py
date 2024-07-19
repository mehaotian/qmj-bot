import random


def generate_6_digit_uid():
    """
    Generate a 6 digit unique id
    """
    return ''.join(random.choices('0123456789', k=6))
