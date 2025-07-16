from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
import logging
from app.models import UserRegister, UserLogin, Token, User
from app.auth import verify_password, get_password_hash, create_access_token, create_refresh_token, get_current_user
from app.database import supabase
from app.config import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure a handler (e.g., StreamHandler for console output)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = supabase.table('users').select('id').eq('email', user_data.email).execute()
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        
        result = supabase.table('users').insert({
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": hashed_password
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        user = result.data[0]
        
        # Create user-specific categories
        await create_user_categories(user['id'])
        
        # Generate tokens
        access_token = create_access_token({"sub": user['id']})
        refresh_token = create_refresh_token({"sub": user['id']})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return tokens"""
    try:
        # Get user from database
        result = supabase.table('users').select('*').eq('email', user_credentials.email).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = result.data[0]
        
        # Verify password
        if not verify_password(user_credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = create_access_token({"sub": user['id']})
        refresh_token = create_refresh_token({"sub": user['id']})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        import jwt
        from jwt.exceptions import PyJWTError
        
        payload = jwt.decode(
            refresh_token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify user still exists
        result = supabase.table('users').select('id').eq('id', user_id).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new tokens
        access_token = create_access_token({"sub": user_id})
        new_refresh_token = create_refresh_token({"sub": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except PyJWTError as e:
        logger.error(f"❌ JWT error in token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    try:
        return {
            "id": current_user['id'],
            "email": current_user['email'],
            "full_name": current_user['full_name'],
            "created_at": current_user['created_at'],
            "updated_at": current_user['updated_at']
        }
    except Exception as e:
        logger.error(f"❌ Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user information: {str(e)}"
        )

async def create_user_categories(user_id: str):
    """Create default categories for new user"""
    default_categories = [
        {"name": "Food", "emoji": "🍽️", "user_id": user_id},
        {"name": "Transport", "emoji": "🚗", "user_id": user_id},
        {"name": "Entertainment", "emoji": "🎬", "user_id": user_id},
        {"name": "Shopping", "emoji": "🛒", "user_id": user_id},
        {"name": "Healthcare", "emoji": "🏥", "user_id": user_id},
        {"name": "Utilities", "emoji": "💡", "user_id": user_id},
        {"name": "Education", "emoji": "📚", "user_id": user_id},
        {"name": "Other", "emoji": "📝", "user_id": user_id},
    ]
    
    try:
        supabase.table('categories').insert(default_categories).execute()
    except Exception as e:
        logger.warning(f"Warning: Failed to create default categories: {e}")