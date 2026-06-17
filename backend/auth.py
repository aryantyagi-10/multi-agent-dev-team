import datetime as dt
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt directly to avoid passlib 
    compatibility bugs with bcrypt 4.0+.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password string using bcrypt.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def create_access_token(subject: str, user_id: int) -> str:
    # Using timezone-aware UTC to prevent deprecation warnings in modern Python versions
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "uid": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str = Depends(oauth2_scheme)) -> dict:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("sub") is None or payload.get("uid") is None:
            raise cred_exc
        return {"username": payload["sub"], "uid": payload["uid"]}
    except JWTError:
        raise cred_exc