@echo off
echo ================================================
echo  ELSM Portal - First Time Setup
echo ================================================
echo.

:: Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [OK] Docker is running.

:: Copy env file
if not exist ".env" (
    copy .env.example .env >nul
    echo [OK] Created .env file from template.
    echo.
    echo IMPORTANT: Open .env in VS Code and update SECRET_KEY before continuing.
    echo Press any key once you have updated .env ...
    pause >nul
)

:: Start containers
echo.
echo Starting all services...
docker-compose up --build -d

echo.
echo Waiting 15 seconds for services to initialize...
timeout /t 15 /nobreak >nul

:: Create first Super Admin
echo.
echo Creating Super Admin user...
docker exec elsm_backend python -c "
import asyncio, uuid
from app.db.session import AsyncSessionLocal
from app.models.models import User, UserRole
from app.core.security import hash_password

async def create():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == 'admin@elsm.in'))
        if result.scalar_one_or_none():
            print('Admin already exists.')
            return
        admin = User(
            id=uuid.uuid4(),
            name='Super Admin',
            email='admin@elsm.in',
            phone='9999999999',
            hashed_password=hash_password('Admin@1234'),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print('Super Admin created.')

asyncio.run(create())
"

echo.
echo ================================================
echo  ELSM Portal is LIVE!
echo.
echo  API Docs  : http://localhost:8000/api/docs
echo  Health    : http://localhost:8000/health
echo  MinIO     : http://localhost:9001
echo.
echo  Login with:
echo    Email   : admin@elsm.in
echo    Password: Admin@1234
echo ================================================
pause
