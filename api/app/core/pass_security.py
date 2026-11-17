from bcrypt import hashpw, gensalt, checkpw

def hash_pw(plain: str) -> str:
    return hashpw(plain.encode(), gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return checkpw(plain.encode(), hashed.encode())