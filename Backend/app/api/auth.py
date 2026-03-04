from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from werkzeug.security import generate_password_hash, check_password_hash
import os
from uuid import UUID
import secrets

from app.core.database import get_db
from app.models.models import User, Organization
from app.schemas.auth import UserCreate, Token, UserResponse
from app.exceptions import AuthenticationError, ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Security - validate JWT secret
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("SECRET_KEY must be at least 32 characters in production")
    else:
        # Generate a secure random key for development
        SECRET_KEY = secrets.token_urlsafe(32)
        logger.warning("jwt_secret_generated", message="Using generated SECRET_KEY for development")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Helper functions
def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

def get_password_hash(password):
    return generate_password_hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("token_validation_failed", reason="missing_subject")
            raise AuthenticationError("Could not validate credentials")
    except JWTError as e:
        logger.warning("token_validation_failed", reason="jwt_error", error=str(e))
        raise AuthenticationError("Could not validate credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning("token_validation_failed", reason="user_not_found", user_id=user_id)
        raise AuthenticationError("Could not validate credentials")
    
    if not user.is_active:
        logger.warning("token_validation_failed", reason="inactive_user", user_id=user_id)
        raise AuthenticationError("Account is inactive")
    
    return user

# Endpoints
@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and organization"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning("registration_failed", email=user_data.email, reason="email_exists")
            raise ValidationError("Email already registered")
        
        # Create organization
        org = Organization(
            name=user_data.organization_name,
            email=user_data.email,
            subscription_status="trial"
        )
        db.add(org)
        db.flush()
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.name,
            organization_id=org.id,
            role="admin"  # Keep for backward compatibility
        )
        db.add(user)
        db.flush()
        
        # Create RBAC roles if they don't exist
        from app.models.models import Role, UserRole
        
        # Check if Owner role exists, create if not
        owner_role = db.query(Role).filter(Role.name == "Owner").first()
        if not owner_role:
            owner_role = Role(
                name="Owner",
                description="Full system access and organization management",
                permissions=["*"]  # All permissions
            )
            db.add(owner_role)
            db.flush()
        
        # Assign Owner role to the first user (organization creator)
        user_role = UserRole(
            user_id=user.id,
            role_id=owner_role.id,
            tenant_id=org.id,
            assigned_by=user.id  # Self-assigned for first user
        )
        db.add(user_role)
        
        db.commit()
        db.refresh(user)
        
        logger.info("user_registered", user_id=user.id, email=user.email, org_id=org.id)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {"access_token": access_token, "token_type": "bearer"}
    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("registration_error", error=str(e))
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    try:
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning("login_failed", email=form_data.username, reason="invalid_credentials")
            raise AuthenticationError("Incorrect email or password")
        
        if not user.is_active:
            logger.warning("login_failed", email=form_data.username, reason="inactive_user")
            raise AuthenticationError("Account is inactive")
        
        logger.info("user_logged_in", user_id=user.id, email=user.email)
        
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except AuthenticationError:
        raise
    except Exception as e:
        logger.exception("login_error", error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.full_name,
        "role": current_user.role,
        "organization_id": current_user.organization_id
    }
