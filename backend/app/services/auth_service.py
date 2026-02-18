"""Authentication service for admin users."""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.admin import AdminUser

settings = get_settings()
security = HTTPBearer()


class AuthService:
    """Service for admin authentication."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, email: str, password: str) -> str | None:
        """Authenticate admin user and return JWT token."""
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.email == email)
        )
        admin = result.scalar_one_or_none()

        if not admin or not admin.is_active:
            return None

        if not bcrypt.verify(password, admin.password_hash):
            return None

        # Create JWT token
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
        payload = {
            "sub": str(admin.id),
            "email": admin.email,
            "exp": expire,
        }
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return token

    async def verify_token(self, token: str) -> AdminUser | None:
        """Verify JWT token and return admin user."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            admin_id = payload.get("sub")
            if not admin_id:
                return None

            result = await self.db.execute(
                select(AdminUser).where(AdminUser.id == admin_id)
            )
            admin = result.scalar_one_or_none()
            if not admin or not admin.is_active:
                return None

            return admin
        except JWTError:
            return None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return bcrypt.hash(password)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Dependency to get current authenticated admin."""
    auth_service = AuthService(db)
    admin = await auth_service.verify_token(credentials.credentials)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return admin
