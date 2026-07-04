from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,HttpUrl
from sqlalchemy.orm import (
    sessionmaker,
    declarative_base,
    Session,
    relationship
) 
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)
from datetime import datetime,timedelta
import string,random 
import qrcode
import os
from sqlalchemy import func
from jose import jwt
from jose.exceptions import JWTError
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from passlib.context import CryptContext


DATABASE_URL= "sqlite:///urls.db"
BASE_URL = "http://127.0.0.1:8000"

SECRET_KEY = "mysecretkey123456789"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
security = HTTPBearer()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False})
SessionLocal =sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base= declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db 

    finally:
        db.close()

def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {"exp": expire}
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def get_current_user(
    credentials:
    HTTPAuthorizationCredentials
    = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None:
        raise credentials_exception

    return user

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String,nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    user_id = Column(
    Integer,
    ForeignKey("users.id")
    )

    owner = relationship(
    "User",
    back_populates="urls"
    )




class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    urls = relationship(
    "URL",
    back_populates="owner"
    )

Base.metadata.create_all(bind=engine)

class UserSignup(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str

from typing import Optional
from datetime import datetime

class URLRequest(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = None
    expires_at: Optional[datetime] = None

class UpdateURLRequest(BaseModel):
    original_url: HttpUrl


class URLResponse(BaseModel):
    original_url: str
    short_code:str
    short_url:str


    
    class Config:
        from_attributes = True

def generate_short_code(Length: int=6):
    return "".join(random.choices(string.ascii_letters + string.digits,k=Length))

app= FastAPI(title="URL Shortner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/signup")
def signup(
    request: UserSignup,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == request.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    new_user = User(
        username=request.username,
        email=request.email,
        password=hash_password(
            request.password
        )
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully"
    }


@app.post("/login")
def login(
    request: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Email or Password"
        )

    if not verify_password(
        request.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Email or Password"
        )

    access_token = create_access_token(
        data={
            "sub": user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post(
    "/shorten",
    response_model=URLResponse
)
def create_short_url(
    request: URLRequest,
    db: Session = Depends(get_db),
    current_user: User =
    Depends(get_current_user)
):
    original_url = str(
        request.original_url
    )

    existing = db.query(URL).filter(
        URL.original_url == original_url,
        URL.user_id == current_user.id
    ).first()

    if existing:
        return {
            "original_url":
            existing.original_url,

            "short_code":
            existing.short_code,

            "short_url":
            f"{BASE_URL}/{existing.short_code}"
        }

    if request.custom_code:
        short_code = request.custom_code

        if not short_code.isalnum():
            raise HTTPException(
                status_code=400,
                detail=
                "Only letters and numbers allowed"
            )

        existing_code = db.query(URL).filter(
            URL.short_code == short_code
        ).first()

        if existing_code:
            raise HTTPException(
                status_code=400,
                detail=
                "Custom short code already exists"
            )

    else:
        short_code = generate_short_code()

        while db.query(URL).filter(
            URL.short_code == short_code
        ).first():
            short_code = generate_short_code()

    new_url = URL(
        original_url=original_url,
        short_code=short_code,
        clicks=0,
        user_id=current_user.id,
        expires_at=request.expires_at
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    short_url = (
        f"{BASE_URL}/"
        f"{new_url.short_code}"
    )

    img = qrcode.make(short_url)

    os.makedirs(
        "qrcodes",
        exist_ok=True
    )

    img.save(
        f"qrcodes/"
        f"{new_url.short_code}.png"
    )

    return {
        "original_url":
        new_url.original_url,

        "short_code":
        new_url.short_code,

        "short_url":
        short_url
    }


@app.get("/all")
def get_all_urls(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    urls = (
        db.query(URL)
        .filter(URL.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []

    for url in urls:
        results.append(
    {
        "original_url": url.original_url,
        "short_code": url.short_code,
        "short_url": f"{BASE_URL}/{url.short_code}",
        "clicks": url.clicks,
        "expires_at": url.expires_at
    }
)
        

    return results

@app.get("/")
def home():
    return {
        "message": "URL Shortener API is Running"
    }

@app.get("/analytics/{short_code}")
def analytics(
        short_code:str,
        db:Session=Depends(get_db),
        current_user: User = Depends(get_current_user)):

    url=db.query(URL).filter(
        URL.short_code==short_code
    ).first()

    if not url:
        raise HTTPException(
            status_code=404,
            detail="URL Not Found"
        )
    
    if url.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    return {
    "original_url": url.original_url,
    "short_code": url.short_code,
    "clicks": url.clicks,
    "created_at": url.created_at,
    "expires_at": url.expires_at
    }




@app.delete("/delete/{short_code}")
def delete_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
    ):
    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    

    if not url:
        raise HTTPException(
            status_code=404,
            detail="URL Not Found"
        )
    if url.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    file_path = f"qrcodes/{short_code}.png"

    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(url)
    db.commit()

    return {
        "message": "URL deleted successfully"
    }




@app.put("/update/{short_code}")
def update_url(
    short_code: str,
    request: UpdateURLRequest,
    db: Session = Depends(get_db),current_user: User = Depends(get_current_user)
    ):
    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if not url:
        raise HTTPException(
            status_code=404,
            detail="URL Not Found"
        )
    if url.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    url.original_url = str(request.original_url)

    db.commit()
    db.refresh(url)

    return {
        "message": "URL Updated Successfully",
        "original_url": url.original_url,
        "short_code": url.short_code
    }


@app.get("/search/{short_code}")
def search_url(
    short_code: str,
    db: Session = Depends(get_db),current_user: User = Depends(get_current_user)
    ):
    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if not url:
        raise HTTPException(
            status_code=404,
            detail="URL Not Found"
        )
    if url.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    return {
    "original_url": url.original_url,
    "short_code": url.short_code,
    "clicks": url.clicks,
    "created_at": url.created_at,
    "expires_at": url.expires_at
    }


@app.get("/search-original/")
def search_original(
    original_url: str,
    db: Session = Depends(get_db),
    current_user: User =
    Depends(get_current_user)
):
    url = db.query(URL).filter(
        URL.original_url == original_url,
        URL.user_id == current_user.id
    ).first()

    if not url:
        raise HTTPException(
            status_code=404,
            detail="URL Not Found"
        )

    return {
        "original_url":
        url.original_url,

        "short_code":
        url.short_code,

        "short_url":
        f"{BASE_URL}/{url.short_code}"
    }

@app.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User =
    Depends(get_current_user)
):
    total_urls = db.query(URL).filter(
        URL.user_id == current_user.id
    ).count()

    total_clicks = db.query(
        func.sum(URL.clicks)
    ).filter(
        URL.user_id == current_user.id
    ).scalar()

    if total_clicks is None:
        total_clicks = 0

    return {
        "total_urls":
        total_urls,

        "total_clicks":
        total_clicks
    }

@app.get("/top")
def top_urls(
    db: Session = Depends(get_db),
    current_user: User =
    Depends(get_current_user)
):
    urls = (
        db.query(URL)
        .filter(
            URL.user_id ==
            current_user.id
        )
        .order_by(
            URL.clicks.desc()
        )
        .limit(5)
        .all()
    )

    result = []

    for url in urls:
        result.append(
            {
                "original_url":
                url.original_url,

                "short_code":
                url.short_code,

                "clicks":
                url.clicks
            }
        )

    return result

@app.get("/expired")
def expired_urls(
    db: Session = Depends(get_db),
    current_user: User =
    Depends(get_current_user)
):
    urls = db.query(URL).filter(
        URL.user_id ==
        current_user.id,

        URL.expires_at != None,
        URL.expires_at <
        datetime.utcnow()
    ).all()

    result = []

    for url in urls:
        result.append(
            {
                "original_url":
                url.original_url,

                "short_code":
                url.short_code,

                "expires_at":
                url.expires_at
            }
        )

    return result
@app.get("/health")
def health():
    return {
        "status": "UP",
        "message": "API is running"
    }


@app.get("/qr/{short_code}")
def get_qr(short_code: str):
    file_path = f"qrcodes/{short_code}.png"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="QR Code Not Found"
        )

    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=f"{short_code}.png"
    )


from datetime import datetime
from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse

@app.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    db: Session = Depends(get_db)
):
    url_entry = (
        db.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    if not url_entry:
        raise HTTPException(
            status_code=404,
            detail="Short URL Not Found"
        )

    # Check expiry
    if (
        url_entry.expires_at
        and url_entry.expires_at < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=410,
            detail="Short URL has expired"
        )

    # Increase click count
    url_entry.clicks += 1
    db.commit()

    return RedirectResponse(
        url=url_entry.original_url
    )