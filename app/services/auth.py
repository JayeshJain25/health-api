from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database.mongodb import MongoDB

# to get a string like this run: openssl rand -hex 32
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Get user function for database lookup
async def get_user(email: str):
    db = MongoDB()
    try:
        users = db.get_collection("users")
        user = users.find_one({"email": email})
        if user:
            return {
                "email": user["email"],
                "name": user["name"],
                "hashed_password": user["hashed_password"],
                "_id": str(user["_id"])
            }
        return None
    finally:
        db.close()

# Dummy TokenData class (replace with your schema)
class TokenData:
    def __init__(self, email: str):
        self.email = email

# Implement authentication logic here

async def register_user(email: str, name: str, password: str):
    db = MongoDB()
    users = db.get_collection("users")
    # Check if user already exists
    if users.find_one({"email": email}):
        db.close()
        raise Exception("User already exists")
    hashed_password = get_password_hash(password)
    user_doc = {"email": email, "name": name, "hashed_password": hashed_password}
    result = users.insert_one(user_doc)
    
    # Create JWT token for the new user
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    user_id = str(result.inserted_id)
    db.close()
    return access_token, user_id

async def login_user(email: str, password: str):
    db = MongoDB()
    users = db.get_collection("users")
    user = users.find_one({"email": email})
    db.close()
    if not user:
        raise Exception("Invalid email or password")
    if not verify_password(password, user["hashed_password"]):
        raise Exception("Invalid email or password")
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    user_id = str(user.get("_id"))
    user_name = user.get("name")
    return access_token, user_id, user_name

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user