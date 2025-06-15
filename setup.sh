#!/bin/bash

# setup.sh - Initialization script for Linux/macOS
# Place at project root (same level as familybusiness/ folder)

set -e  # Stop script on error

echo "🚀 Family Business - Initialization Script"
echo "==========================================="

# Preliminary checks
echo "🔍 Checking prerequisites..."

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "   Please install Python 3.8+ before continuing"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION detected"

# Check that we are in the correct directory
if [ ! -d "familybusiness" ] || [ ! -f "familybusiness/manage.py" ]; then
    echo "❌ Script must be run from project root"
    echo "   Expected structure: ./familybusiness/manage.py"
    exit 1
fi

echo "✅ Project structure validated"

# Create and activate virtual environment
echo ""
echo "📦 Configuring virtual environment..."

if [ -d "venv" ]; then
    echo "⚠️  A virtual environment already exists"
    read -p "Do you want to delete and recreate it? (y/N): " recreate_venv
    if [[ $recreate_venv =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing old environment..."
        rm -rf venv
    else
        echo "📂 Using existing environment"
    fi
fi

if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔗 Activating virtual environment..."
source venv/bin/activate

# Check that activation worked
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Install dependencies
echo ""
echo "📋 Installing dependencies..."

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt file not found"
    exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"

# Go to Django project directory
cd familybusiness

# Apply migrations
echo ""
echo "🗄️  Applying database migrations..."
python manage.py migrate

echo "✅ Migrations applied successfully"

# Compile translation messages
echo ""
echo "🌍 Compiling translation messages..."
django-admin compilemessages

echo "✅ Translations compiled successfully"

# Create superuser
echo ""
echo "👤 Creating superuser..."
echo "   Email: admin@admin.be"
echo "   First Name: Admin"
echo "   Last Name: Admin"
echo "   Password: admin"

# Use expect if available, otherwise manual interaction
if command -v expect &> /dev/null; then
    expect << EOF
spawn python manage.py createsuperuser
expect "Email:" { send "admin@admin.be\r" }
expect "First Name:" { send "Admin\r" }
expect "Last Name:" { send "Admin\r" }
expect "Password:" { send "admin\r" }
expect "Password (again):" { send "admin\r" }
expect "Bypass password validation and create user anyway?" { send "y\r" }
expect eof
EOF
else
    echo ""
    echo "⚠️  'expect' is not installed. Manual superuser creation..."
    echo "   Please enter the following information:"
    echo "   - Email: admin@admin.be"
    echo "   - First Name: Admin"
    echo "   - Last Name: Admin"
    echo "   - Password: admin"
    echo "   - Password (again): admin"
    echo "   - Bypass validation: y"
    echo ""
    python manage.py createsuperuser
fi

echo "✅ Superuser created successfully"

# Return to root directory
cd ..

# Final message
echo ""
echo "🎉 Initialization completed successfully!"
echo "========================================"
echo ""
echo "📋 Login credentials:"
echo "   Email    : admin@admin.be"
echo "   Password : admin"
echo ""
echo "🚀 To start the server:"
echo "   source venv/bin/activate"
echo "   python3 familybusiness/manage.py runserver"
echo ""
echo "🌐 Application will be accessible at: http://127.0.0.1:8000"
echo "   Admin interface: http://127.0.0.1:8000/admin"
echo ""