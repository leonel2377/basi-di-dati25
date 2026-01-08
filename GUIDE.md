# Guide d'Utilisation et Déploiement

Ce guide détaille comment lancer le programme et comment le publier sur GitHub.

---

## 📋 Table des matières

1. [Lancement du Programme](#lancement-du-programme)
2. [Configuration et Dépendances](#configuration-et-dépendances)
3. [Utilisation du Programme](#utilisation-du-programme)
4. [Publication sur GitHub](#publication-sur-github)

---

## 🚀 Lancement du Programme

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git (pour la version contrôle)

### Installation des dépendances

#### Étape 1 : Créer un environnement virtuel (recommandé)

**Sur Windows :**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Sur Linux/Mac :**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Étape 2 : Installer les dépendances

Si vous avez un fichier `requirements.txt` :
```bash
pip install -r requirements.txt
```

Sinon, installez manuellement les dépendances principales :
```bash
pip install pandas matplotlib seaborn scikit-learn
```

Pour les fonctionnalités ML avancées (optionnel) :
```bash
pip install xgboost tensorflow
```

### Exécution du programme

#### Lancement basique

```bash
python main.py
```

#### Options disponibles

Afficher l'aide :
```bash
python main.py --help
```

**Options principales :**

- `--inventory path/to/file.csv` : Spécifier un fichier d'inventaire personnalisé
- `--encoding ENCODING` : Spécifier l'encodage du fichier CSV (défaut: utf-8)
- `--save-plot output.png` : Sauvegarder le graphique dans un fichier
- `--no-show-plot` : Ne pas afficher le graphique interactivement (mode headless)
- `--orange-strategy {prompt,auto-confirm,auto-decline}` : Stratégie pour gérer les stocks faibles
  - `prompt` : Demander confirmation (défaut)
  - `auto-confirm` : Confirmer automatiquement
  - `auto-decline` : Refuser automatiquement
- `--enable-ml` : Activer les prédictions ML
- `--ml-model {random_forest,xgboost,lstm}` : Type de modèle ML (défaut: random_forest)
- `--sales-history path/to/sales.csv` : Fichier d'historique des ventes

#### Exemples d'utilisation

**Mode simple (sans interaction) :**
```bash
python main.py --orange-strategy auto-decline --no-show-plot
```

**Avec prédictions ML :**
```bash
# 1. Générer l'historique des ventes (si nécessaire)
python data/generate_sales_history.py

# 2. Lancer avec ML activé
python main.py --enable-ml --orange-strategy auto-confirm --no-show-plot
```

**Avec un fichier d'inventaire personnalisé :**
```bash
python main.py --inventory mon_inventaire.csv --save-plot rapport.png
```

### Exécution des tests

```bash
# Avec pytest
pytest

# Avec pytest en mode verbeux
pytest -v

# Exécuter un fichier de test spécifique
pytest tests/test_status.py
```

---

## 📦 Configuration et Dépendances

### Structure des fichiers CSV

Le fichier d'inventaire doit contenir les colonnes suivantes :

**Colonnes requises :**
- `product_id` : Identifiant unique du produit (obligatoire, pas de doublons)
- `product_name` : Nom du produit
- `category` : Catégorie du produit
- `quantity` : Quantité en stock (nombre positif)
- `reorder_point` : Seuil de réapprovisionnement (nombre positif)
- `critical_point` : Seuil critique (nombre positif, ≤ reorder_point)

**Colonnes optionnelles :**
- `reorder_quantity` : Quantité à commander lors d'un réapprovisionnement

**Exemple de fichier CSV :**
```csv
product_id,product_name,category,quantity,reorder_point,critical_point,reorder_quantity
SKU-1001,USB-C Cable,Accessories,120,50,20,80
SKU-1002,Wireless Mouse,Peripherals,45,40,15,60
```

### Validation des données

Le programme valide automatiquement :
- ✅ Absence de `product_id` dupliqués
- ✅ Valeurs numériques non négatives
- ✅ Absence de valeurs manquantes (NaN)
- ✅ Cohérence des seuils (critical_point ≤ reorder_point)

---

## 🐙 Publication sur GitHub

### Configuration initiale de Git

#### Étape 1 : Vérifier l'installation de Git

```bash
git --version
```

Si Git n'est pas installé, téléchargez-le depuis [git-scm.com](https://git-scm.com/)

#### Étape 2 : Configurer Git (première fois uniquement)

```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"
```

### Création d'un dépôt GitHub

#### Étape 1 : Créer un nouveau dépôt sur GitHub

1. Allez sur [github.com](https://github.com)
2. Cliquez sur le bouton **"+"** en haut à droite
3. Sélectionnez **"New repository"**
4. Remplissez les informations :
   - **Repository name** : `python_projet` (ou le nom de votre choix)
   - **Description** : "Inventory Tracker with Dynamic Reorder Alerts"
   - **Visibility** : Public ou Private
   - **Ne cochez PAS** "Initialize this repository with a README" (si vous avez déjà des fichiers)
5. Cliquez sur **"Create repository"**

#### Étape 2 : Initialiser Git dans votre projet local

```bash
# Naviguer vers le dossier du projet
cd C:\Users\39328\Desktop\python_projet

# Initialiser Git
git init
```

### Création du fichier .gitignore

Créez un fichier `.gitignore` pour exclure les fichiers inutiles :

```bash
# Créer le fichier .gitignore
```

Contenu recommandé pour `.gitignore` :
```
# Environnements virtuels
.venv/
venv/
ENV/
env/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Distribution / packaging
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Fichiers de données générés (optionnel)
data/sales_history.csv

# Fichiers de logs
*.log

# Fichiers temporaires
*.tmp
*.bak
```

### Premier commit et push

#### Étape 1 : Ajouter les fichiers

```bash
# Vérifier l'état des fichiers
git status

# Ajouter tous les fichiers (sauf ceux dans .gitignore)
git add .

# Ou ajouter des fichiers spécifiques
git add main.py
git add inventory_tracker/
git add README.md
git add GUIDE.md
```

#### Étape 2 : Créer le premier commit

```bash
git commit -m "Initial commit: Inventory Tracker application"
```

#### Étape 3 : Lier le dépôt local au dépôt GitHub

```bash
# Remplacer USERNAME et REPO_NAME par vos valeurs
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Vérifier la configuration
git remote -v
```

#### Étape 4 : Pousser le code sur GitHub

```bash
# Pousser vers la branche main (ou master selon votre dépôt)
git push -u origin main

# Si votre branche par défaut est "master" :
git push -u origin master
```

**Note :** Si c'est la première fois, GitHub vous demandera de vous authentifier. Utilisez un **Personal Access Token** (PAT) au lieu de votre mot de passe.

### Workflow Git pour les modifications futures

#### 1. Vérifier l'état des modifications

```bash
git status
```

#### 2. Ajouter les fichiers modifiés

```bash
# Ajouter tous les fichiers modifiés
git add .

# Ou ajouter des fichiers spécifiques
git add inventory_tracker/data_loader.py
```

#### 3. Créer un commit

```bash
git commit -m "Description claire de vos modifications"
```

**Exemples de messages de commit :**
- `"Fix: Correction de la validation des product_id dupliqués"`
- `"Feat: Ajout de la validation des valeurs négatives"`
- `"Docs: Mise à jour du guide d'utilisation"`
- `"Refactor: Amélioration de la structure du code"`

#### 4. Pousser les modifications

```bash
git push
```

### Gestion des branches (optionnel mais recommandé)

#### Créer une nouvelle branche

```bash
git checkout -b feature/nouvelle-fonctionnalite
```

#### Travailler sur la branche

```bash
# Faire vos modifications
# ...

# Commiter
git add .
git commit -m "Ajout de nouvelle fonctionnalité"
```

#### Fusionner avec la branche principale

```bash
# Revenir sur main
git checkout main

# Fusionner la branche
git merge feature/nouvelle-fonctionnalite

# Pousser
git push
```

### Résolution de conflits

Si vous travaillez en équipe et qu'il y a des conflits :

```bash
# Récupérer les dernières modifications
git pull origin main

# Résoudre les conflits dans les fichiers
# Puis :
git add .
git commit -m "Résolution des conflits"
git push
```

### Commandes Git utiles

```bash
# Voir l'historique des commits
git log

# Voir les différences avant de commiter
git diff

# Annuler des modifications non commitées
git checkout -- fichier.py

# Annuler le dernier commit (garder les modifications)
git reset --soft HEAD~1

# Voir les branches
git branch

# Voir les remotes configurés
git remote -v
```

---

## 🔧 Dépannage

### Problèmes courants lors du lancement

**Erreur : "Module not found"**
```bash
# Solution : Installer les dépendances
pip install -r requirements.txt
```

**Erreur : "File not found"**
```bash
# Vérifier que le fichier CSV existe
# Vérifier le chemin relatif ou absolu
python main.py --inventory data/sample_inventory.csv
```

**Erreur : "Duplicate product_id"**
```bash
# Vérifier votre fichier CSV
# Chaque product_id doit être unique
```

### Problèmes courants avec Git/GitHub

**Erreur : "Authentication failed"**
```bash
# Utiliser un Personal Access Token au lieu du mot de passe
# Créer un PAT sur GitHub : Settings > Developer settings > Personal access tokens
```

**Erreur : "Remote origin already exists"**
```bash
# Vérifier la configuration
git remote -v

# Modifier l'URL si nécessaire
git remote set-url origin https://github.com/USERNAME/REPO_NAME.git
```

**Erreur : "Updates were rejected"**
```bash
# Récupérer les dernières modifications d'abord
git pull origin main --rebase
# Puis pousser
git push
```

---

## 📚 Ressources supplémentaires

- [Documentation Python](https://docs.python.org/)
- [Documentation Git](https://git-scm.com/doc)
- [Guide GitHub](https://guides.github.com/)
- [Documentation pandas](https://pandas.pydata.org/docs/)

---

## ✅ Checklist avant un push

- [ ] Tous les tests passent (`pytest`)
- [ ] Le code fonctionne localement
- [ ] Les fichiers sensibles sont dans `.gitignore`
- [ ] Les messages de commit sont clairs et descriptifs
- [ ] Le README.md est à jour
- [ ] Pas de fichiers temporaires ou de cache inclus

---

**Bon développement ! 🚀**

