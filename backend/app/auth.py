import os
from datetime import datetime, timedelta, timezone
import bcrypt, jwt
from fastapi import HTTPException
SECRET=os.getenv("JWT_SECRET","")
ALGORITHM="HS256"
TOKEN_HOURS=int(os.getenv("ACCESS_TOKEN_HOURS","8"))
def hash_password(password:str)->str:
    if len(password)<10: raise HTTPException(400,"Password must be at least 10 characters")
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
def verify_password(password:str,hashed:str)->bool:
    try:return bcrypt.checkpw(password.encode(),hashed.encode())
    except Exception:return False
def make_token(user):
    if len(SECRET)<32: raise RuntimeError("JWT_SECRET must be at least 32 characters")
    now=datetime.now(timezone.utc)
    return jwt.encode({"sub":str(user.id),"clinic_id":user.clinic_id,"role":user.role.value,"iat":now,"exp":now+timedelta(hours=TOKEN_HOURS)},SECRET,algorithm=ALGORITHM)
def decode_token(token):
    if len(SECRET)<32: raise HTTPException(503,"Server authentication secret is not configured")
    try:return jwt.decode(token,SECRET,algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError: raise HTTPException(401,"Session expired")
    except jwt.PyJWTError: raise HTTPException(401,"Invalid authentication token")
