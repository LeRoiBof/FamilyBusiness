@echo off
setlocal enabledelayedexpansion

REM setup.bat - Script d'initialisation pour Windows
REM À placer à la racine du projet (même niveau que le dossier familybusiness/)

echo 🚀 Family Business - Script d'initialisation
echo ==============================================

REM Vérifications préliminaires
echo 🔍 Vérification des prérequis...

REM Vérifier Python 3
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou n'est pas dans le PATH
    echo    Veuillez installer Python 3.8+ avant de continuer
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% détecté

REM Vérifier que nous sommes dans le bon répertoire
if not exist "familybusiness" (
    echo ❌ Le script doit être exécuté depuis la racine du projet
    echo    Structure attendue : .\familybusiness\manage.py
    pause
    exit /b 1
)

if not exist "familybusiness\manage.py" (
    echo ❌ Le script doit être exécuté depuis la racine du projet
    echo    Structure attendue : .\familybusiness\manage.py
    pause
    exit /b 1
)

echo ✅ Structure du projet validée

REM Créer et activer l'environnement virtuel
echo.
echo 📦 Configuration de l'environnement virtuel...

if exist "venv" (
    echo ⚠️  Un environnement virtuel existe déjà
    set /p recreate_venv="Voulez-vous le supprimer et le recréer ? (y/N): "
    if /i "!recreate_venv!"=="y" (
        echo 🗑️  Suppression de l'ancien environnement...
        rmdir /s /q venv
    ) else (
        echo 📂 Utilisation de l'environnement existant
    )
)

if not exist "venv" (
    echo 🔨 Création de l'environnement virtuel...
    python -m venv venv
)

echo 🔗 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances
echo.
echo 📋 Installation des dépendances...

if not exist "requirements.txt" (
    echo ❌ Fichier requirements.txt introuvable
    pause
    exit /b 1
)

python -m pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Dépendances installées avec succès

REM Aller dans le répertoire du projet Django
cd familybusiness

REM Appliquer les migrations
echo.
echo 🗄️  Application des migrations de base de données...
python manage.py migrate

echo ✅ Migrations appliquées avec succès

REM Compiler les messages de traduction
echo.
echo 🌍 Compilation des messages de traduction...
django-admin compilemessages

echo ✅ Traductions compilées avec succès

REM Créer le superutilisateur
echo.
echo 👤 Création du superutilisateur...
echo    Email: admin@admin.be
echo    Nom: Admin
echo    Prénom: Admin
echo    Mot de passe: admin

echo.
echo ⚠️  Veuillez entrer les informations suivantes :
echo    - Email: admin@admin.be
echo    - First Name: Admin
echo    - Last Name: Admin
echo    - Password: admin
echo    - Password (again): admin
echo    - Bypass validation: y
echo.

REM Créer un fichier temporaire avec les réponses
echo admin@admin.be> temp_input.txt
echo Admin>> temp_input.txt
echo Admin>> temp_input.txt
echo admin>> temp_input.txt
echo admin>> temp_input.txt
echo y>> temp_input.txt

python manage.py createsuperuser < temp_input.txt

REM Nettoyer le fichier temporaire
del temp_input.txt

echo ✅ Superutilisateur créé avec succès

REM Retour au répertoire racine
cd ..

REM Message final
echo.
echo 🎉 Initialisation terminée avec succès !
echo ========================================
echo.
echo 📋 Informations de connexion :
echo    Email    : admin@admin.be
echo    Password : admin
echo.
echo 🚀 Pour démarrer le serveur :
echo    venv\Scripts\activate
echo    python familybusiness\manage.py runserver
echo.
echo 🌐 L'application sera accessible sur : http://127.0.0.1:8000
echo 👨‍💼 Interface d'administration : http://127.0.0.1:8000/admin
echo.
echo ✨ Bon développement avec Family Business ! ✨
echo.
pause