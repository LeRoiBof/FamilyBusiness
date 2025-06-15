#!/bin/bash

# setup.sh - Script d'initialisation pour Linux/macOS
# À placer à la racine du projet (même niveau que le dossier familybusiness/)

set -e  # Arrêter le script en cas d'erreur

echo "🚀 Family Business - Script d'initialisation"
echo "=============================================="

# Vérifications préliminaires
echo "🔍 Vérification des prérequis..."

# Vérifier Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé ou n'est pas dans le PATH"
    echo "   Veuillez installer Python 3.8+ avant de continuer"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION détecté"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "familybusiness" ] || [ ! -f "familybusiness/manage.py" ]; then
    echo "❌ Le script doit être exécuté depuis la racine du projet"
    echo "   Structure attendue : ./familybusiness/manage.py"
    exit 1
fi

echo "✅ Structure du projet validée"

# Créer et activer l'environnement virtuel
echo ""
echo "📦 Configuration de l'environnement virtuel..."

if [ -d "venv" ]; then
    echo "⚠️  Un environnement virtuel existe déjà"
    read -p "Voulez-vous le supprimer et le recréer ? (y/N): " recreate_venv
    if [[ $recreate_venv =~ ^[Yy]$ ]]; then
        echo "🗑️  Suppression de l'ancien environnement..."
        rm -rf venv
    else
        echo "📂 Utilisation de l'environnement existant"
    fi
fi

if [ ! -d "venv" ]; then
    echo "🔨 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

echo "🔗 Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérifier que l'activation a fonctionné
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Échec de l'activation de l'environnement virtuel"
    exit 1
fi

echo "✅ Environnement virtuel activé : $VIRTUAL_ENV"

# Installer les dépendances
echo ""
echo "📋 Installation des dépendances..."

if [ ! -f "requirements.txt" ]; then
    echo "❌ Fichier requirements.txt introuvable"
    exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dépendances installées avec succès"

# Aller dans le répertoire du projet Django
cd familybusiness

# Appliquer les migrations
echo ""
echo "🗄️  Application des migrations de base de données..."
python manage.py migrate

echo "✅ Migrations appliquées avec succès"

# Compiler les messages de traduction
echo ""
echo "🌍 Compilation des messages de traduction..."
django-admin compilemessages

echo "✅ Traductions compilées avec succès"

# Créer le superutilisateur
echo ""
echo "👤 Création du superutilisateur..."
echo "   Email: admin@admin.be"
echo "   Nom: Admin"
echo "   Prénom: Admin"
echo "   Mot de passe: admin"

# Utiliser expect si disponible, sinon interaction manuelle
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
    echo "⚠️  'expect' n'est pas installé. Création manuelle du superutilisateur..."
    echo "   Veuillez entrer les informations suivantes :"
    echo "   - Email: admin@admin.be"
    echo "   - First Name: Admin"
    echo "   - Last Name: Admin"
    echo "   - Password: admin"
    echo "   - Password (again): admin"
    echo "   - Bypass validation: y"
    echo ""
    python manage.py createsuperuser
fi

echo "✅ Superutilisateur créé avec succès"

# Retour au répertoire racine
cd ..

# Message final
echo ""
echo "🎉 Initialisation terminée avec succès !"
echo "========================================"
echo ""
echo "📋 Informations de connexion :"
echo "   Email    : admin@admin.be"
echo "   Password : admin"
echo ""
echo "🚀 Pour démarrer le serveur :"
echo "   source venv/bin/activate"
echo "   python3 familybusiness/manage.py runserver"
echo ""
echo "🌐 L'application sera accessible sur : http://127.0.0.1:8000"
echo "   Interface d'administration : http://127.0.0.1:8000/admin"
echo ""