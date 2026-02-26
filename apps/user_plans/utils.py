import random
import string

def generate_plan_number():
    return "PLAN-" + str(random.randint(10000,99999))

def generate_share_token(length=20):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))