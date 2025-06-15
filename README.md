# Family Business - Installation

## 🚀 Installation rapide

### Linux / macOS
```bash
chmod +x setup.sh
./setup.sh
```

### Windows (Batch)
```cmd
setup.bat
```

## 📋 Ce que fait le script

1. **Vérification des prérequis** : Python 3.8+
2. **Création de l'environnement virtuel** : `venv/`
3. **Installation des dépendances** : `pip install -r requirements.txt`
4. **Application des migrations** : `python manage.py migrate`
5. **Compilation des traductions** : `django-admin compilemessages`
6. **Création du superutilisateur** :
   - Email: `admin@admin.be`
   - Nom: `Admin`
   - Prénom: `Admin`
   - Mot de passe: `admin`

## 🚀 Lancement du serveur

Après l'installation, démarrez le serveur :

### Linux / macOS
```bash
source venv/bin/activate
python3 familybusiness/manage.py runserver
```

### Windows
```cmd
venv\Scripts\activate
python familybusiness\manage.py runserver
```

## 🌐 Accès à l'application

- **Application** : http://127.0.0.1:8000
- **Administration** : http://127.0.0.1:8000/admin

### Identifiants de connexion
- **Email** : `admin@admin.be`
- **Mot de passe** : `admin`

## 📁 Structure du projet

```
Family Business/
├── familybusiness/          # Code Django
│   ├── manage.py
│   ├── familybusiness/      # Configuration
│   ├── wallet/              # App principale
│   ├── account/             # Gestion utilisateurs
│   └── adminpanel/          # Administration
├── venv/                    # Environnement virtuel (créé par le script)
├── requirements.txt         # Dépendances Python
├── setup.sh                 # Script Linux/macOS
├── setup.bat                # Script Windows (Batch)
└── README.md               # Documentation
```

## 🔧 Installation manuelle

Si les scripts automatiques ne fonctionnent pas :

```bash
# 1. Créer l'environnement virtuel
python3 -m venv venv

# 2. Activer l'environnement
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Aller dans le répertoire Django
cd familybusiness

# 5. Appliquer les migrations
python manage.py migrate

# 6. Compiler les traductions
django-admin compilemessages

# 7. Créer le superutilisateur
python manage.py createsuperuser

# 8. Lancer le serveur
python manage.py runserver
```

## ⚠️ Prérequis

- **Python 3.8+** installé et dans le PATH

## 🐛 Résolution de problèmes

### Python non trouvé
- Vérifiez que Python est installé : `python --version`
- Sur certains systèmes, utilisez `python3` au lieu de `python`

### Problèmes de permissions (Linux/macOS)
```bash
chmod +x setup.sh
```

### Environnement virtuel corrompu
Supprimez le dossier `venv/` et relancez le script.