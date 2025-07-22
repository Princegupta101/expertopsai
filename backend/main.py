import os
from typing import List, Optional
from datetime import datetime
import uuid
from io import BytesIO

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from azure.storage.blob import BlobServiceClient
from jose import JWTError, jwt
from PIL import Image
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
DATABASE_URL = os.getenv("DATABASE_URL")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5242880))  # 5MB default
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif").split(",")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Secure Image Upload API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure Blob Storage client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

# Security
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_auth0_public_key():
    """Get Auth0 public key for JWT verification"""
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(url)
    jwks = response.json()
    return jwks

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Auth0"""
    token = credentials.credentials
    
    try:
        # Get public key
        jwks = get_auth0_public_key()
        
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the correct key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            return payload
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def validate_image_file(file: UploadFile) -> bool:
    """Validate if uploaded file is a valid image"""
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    
    # Check file extension
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False
    
    return True

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename for storage"""
    file_extension = original_filename.split('.')[-1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{file_extension}"

@app.get("/")
async def root():
    return {"message": "Secure Image Upload API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload an image file to Azure Blob Storage"""
    
    # Validate file
    if not validate_image_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPG, PNG, and GIF images are allowed."
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    # Validate image content using PIL
    try:
        image = Image.open(BytesIO(file_content))
        image.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )
    
    # Generate unique filename
    stored_filename = generate_unique_filename(file.filename)
    
    try:
        # Upload to Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_STORAGE_CONTAINER_NAME,
            blob=stored_filename
        )
        
        # Reset file position after reading
        file_stream = BytesIO(file_content)
        blob_client.upload_blob(file_stream, overwrite=True)
        
        # Get the URL of the uploaded file
        file_url = blob_client.url
        
        # Save metadata to database
        db_file = FileUpload(
            user_id=current_user["sub"],
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_url=file_url,
            file_size=file_size,
            content_type=file.content_type
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {
            "id": db_file.id,
            "filename": file.filename,
            "url": file_url,
            "size": file_size,
            "uploaded_at": db_file.uploaded_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@app.get("/files")
async def get_user_files(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get list of files uploaded by the current user"""
    
    files = db.query(FileUpload).filter(
        FileUpload.user_id == current_user["sub"]
    ).order_by(FileUpload.uploaded_at.desc()).all()
    
    return [
        {
            "id": file.id,
            "original_filename": file.original_filename,
            "file_url": file.file_url,
            "file_size": file.file_size,
            "content_type": file.content_type,
            "uploaded_at": file.uploaded_at.isoformat()
        }
        for file in files
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
