#!/usr/bin/env python3
"""Create a test admin account for development/testing."""
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models.user import User, UserRole
from app.core.security import hash_password_sync

async def main():
    # Create engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if admin exists
        query = select(User).where(User.email == "admin@truematch.local")
        result = await session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Admin user already exists: {existing.email}")
            return
        
        # Create admin user
        admin = User(
            id=uuid4(),
            email="admin@truematch.local",
            password_hash=hash_password_sync("admin123"),
            display_name="Admin User",
            role=UserRole.admin,
        )
        
        session.add(admin)
        await session.commit()
        
        print("✅ Test admin account created!")
        print("")
        print("Credentials:")
        print("  Email: admin@truematch.local")
        print("  Password: admin123")
        print("")
        print("Use these to log in at: http://localhost:3001/login")

if __name__ == "__main__":
    asyncio.run(main())
