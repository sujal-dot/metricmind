import bcrypt


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    try:
        pwd_bytes = password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False
