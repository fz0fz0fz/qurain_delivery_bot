
import random
import string

def generate_order_id():
    return "G" + ''.join(random.choices(string.digits, k=3))
