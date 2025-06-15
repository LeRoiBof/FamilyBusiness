@echo off
setlocal enabledelayedexpansion

REM setup.bat - Initialization script for Windows
REM Place at project root (same level as familybusiness/ folder)

echo 🚀 Family Business - Initialization Script
echo ===========================================

REM Preliminary checks
echo 🔍 Checking prerequisites...

REM Check Python 3
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.8+ before continuing
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detected

REM Check that we are in the correct directory
if not exist "familybusiness" (
    echo ❌ Script must be run from project root
    echo    Expected structure: .\familybusiness\manage.py
    pause
    exit /b 1
)

if not exist "familybusiness\manage.py" (
    echo ❌ Script must be run from project root
    echo    Expected structure: .\familybusiness\manage.py
    pause
    exit /b 1
)

echo ✅ Project structure validated

REM Create and activate virtual environment
echo.
echo 📦 Configuring virtual environment...

if exist "venv" (
    echo ⚠️  A virtual environment already exists
    set /p recreate_venv="Do you want to delete and recreate it? (y/N): "
    if /i "!recreate_venv!"=="y" (
        echo 🗑️  Removing old environment...
        rmdir /s /q venv
    ) else (
        echo 📂 Using existing environment
    )
)

if not exist "venv" (
    echo 🔨 Creating virtual environment...
    python -m venv venv
)

echo 🔗 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo 📋 Installing dependencies...

if not exist "requirements.txt" (
    echo ❌ requirements.txt file not found
    pause
    exit /b 1
)

python -m pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Dependencies installed successfully

REM Go to Django project directory
cd familybusiness

REM Apply migrations
echo.
echo 🗄️  Applying database migrations...
python manage.py migrate

echo ✅ Migrations applied successfully

REM Compile translation messages
echo.
echo 🌍 Compiling translation messages...
django-admin compilemessages

echo ✅ Translations compiled successfully

REM Create superuser
echo.
echo 👤 Creating superuser...
echo    Email: admin@admin.be
echo    First Name: Admin
echo    Last Name: Admin
echo    Password: admin

echo.
echo ⚠️  Please enter the following information:
echo    - Email: admin@admin.be
echo    - First Name: Admin
echo    - Last Name: Admin
echo    - Password: admin
echo    - Password (again): admin
echo    - Bypass validation: y
echo.

REM Create temporary file with answers
echo admin@admin.be> temp_input.txt
echo Admin>> temp_input.txt
echo Admin>> temp_input.txt
echo admin>> temp_input.txt
echo admin>> temp_input.txt
echo y>> temp_input.txt

python manage.py createsuperuser < temp_input.txt

REM Clean up temporary file
del temp_input.txt

echo ✅ Superuser created successfully

REM Return to root directory
cd ..

REM Final message
echo.
echo 🎉 Initialization completed successfully!
echo =========================================
echo.
echo 📋 Login credentials:
echo    Email    : admin@admin.be
echo    Password : admin
echo.
echo 🚀 To start the server:
echo    venv\Scripts\activate
echo    python familybusiness\manage.py runserver
echo.
echo 🌐 Application will be accessible at: http://127.0.0.1:8000
echo    Admin interface: http://127.0.0.1:8000/admin
echo.
pause