# DC Formulaire

Application web pour remplir un dossier de compétences (DC EPSYL) : gestion du parcours professionnel, stockage PostgreSQL, et export DOCX.

## 🎯 Quickstart

### Prérequis

- Docker & Docker Compose

### Lancement

```bash
# 1. Cloner et configurer
git clone <repo>
cd dc_formulaire
cp .env.example .env
# Éditer .env pour changer SECRET_KEY et les identifiants

# 2. Démarrer les services
docker compose up --build

# L'application est accessible sur http://localhost:8001
```

## 📊 Stack technique

| Couche                     | Technologie                                |
| -------------------------- | ------------------------------------------ |
| **Frontend**         | Django Templates + Bootstrap 5 + Fetch API |
| **Backend**          | Django 6                                   |
| **Base de données** | PostgreSQL 17                              |
| **Export document**  | python-docx + docxtpl (Jinja2)             |
| **Déploiement**     | Docker Compose                             |

## 🏗️ Architecture

L'application gère **9 sections** organisées de façon cohérente :

1. **Headers & Infos** - Données candidat (nom, email, poste, années d'XP)
2. **Postes Cibles** - Postes visés avec état d'activation
3. **Compétences Domaines** - Hiérarchie des domaines (Développement, etc.)
4. **Compétences Outils** - Hiérarchie des outils/langages
5. **Formations** - Parcours académique
6. **Certifications** - Certifications professionnelles
7. **Langues** - Langues parlées et niveaux
8. **Expériences (Blocs)** - Blocs d'expérience professionnelle
9. **Expériences (Bullets)** - Réalisations imbriquées par bloc

Chaque section est gérée de manière indépendante via AJAX (sans rechargement page).

### Structure des données

Toutes les données candidat sont stockées dans un **JSONField PostgreSQL** appelé `dossier` :

```json
{
  "header": { "nom": "...", "prenom": "...", "email": "...", ... },
  "poste_cible": [ { "id": "uuid", "title": "...", "active": true } ],
  "main_skills": { "bullet": [...], "table": [...] },
  "formations": [...],
  "certifications": [...],
  "langues": [...],
  "xp_pro": [
    {
      "id": "uuid",
      "company": "...",
      "poste": "...",
      "date": "...",
      "context": "...",
      "technologies": "...",
      "realizations": [...]
    }
  ]
}
```

## 📁 Structure du projet

```
dc_formulaire/
├── README.md                    # Ce fichier
├── docker-compose.yml           # Orchestration Docker
├── .env.example                 # Variables d'environnement
├── backend/
│   ├── Dockerfile              # Image Docker (Django + Gunicorn)
│   ├── entrypoint.sh            # Script de démarrage
│   ├── requirements.txt          # Dépendances Python
│   └── app/
│       ├── manage.py            # CLI Django
│       ├── config/              # Configuration Django
│       │   ├── settings.py       # Paramètres de l'app
│       │   ├── urls.py          # Routage principal
│       │   └── wsgi.py          # Point d'entrée WSGI
│       └── formulaire/          # App Django principal
│           ├── models.py        # Modèle Candidat
│           ├── views.py         # Vues (51 fonctions)
│           ├── urls.py          # Routes (29 patterns)
│           ├── forms.py         # Formulaires Django (5)
│           ├── utils.py         # Utilitaires
│           ├── admin.py         # Admin Django
│           ├── templates/       # Templates HTML
│           │   └── formulaire/
│           │       ├── base.html                    # Layout principal
│           │       ├── candidat_list.html           # Liste des candidats
│           │       ├── candidat_create.html         # Création candidat
│           │       ├── candidat_detail.html         # Vue détail candidat
│           │       ├── candidat_edit.html           # Édition (2352 lignes)
│           │       └── partials/                    # Templates partiels
│           │           ├── detail_hierarchy.html
│           │           ├── main_skills_hierarchy_item.html
│           │           ├── xp_pro_hierarchy_item.html
│           │           └── ...
│           ├── static/         # Fichiers statiques
│           │   └── css/custom.css
│           ├── management/
│           │   └── commands/    # Commandes Django custom
│           └── migrations/      # Migrations de BD
├── templates_docx/
│   └── template_jinja.docx     # ← Template DOCX à personnaliser
└── postgres/                    # (ignoré) Volume de données PostgreSQL
```

## 🚀 Déploiement & Commandes

### Docker Compose

```bash
# Démarrer en arrière-plan
docker compose up -d --build

# Voir les logs
docker compose logs -f web

# Arrêter
docker compose down

# Arrêter et supprimer les volumes
docker compose down -v
```

### Migrations & Maintenance

```bash
# Créer des migrations
docker compose exec web python manage.py makemigrations

# Appliquer les migrations
docker compose exec web python manage.py migrate

# Créer un superutilisateur
docker compose exec web python manage.py createsuperuser

# Collecte des fichiers statiques
docker compose exec web python manage.py collectstatic --noinput
```

### Variables d'environnement (.env)

```bash
# Secret Django (générer : python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
SECRET_KEY=your-secret-key-here

# Mode debug (False en production)
DEBUG=True

# BD PostgreSQL
POSTGRES_DB=dc_formulaire
POSTGRES_USER=dcuser
POSTGRES_PASSWORD=your-secure-password

# Django
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 📄 Export DOCX

Pour exporter le dossier d'un candidat en document Word :

1. **Placer le template** : Copier votre template Jinja2 dans `templates_docx/template_jinja.docx`
2. **Variables disponibles** :

   - Toutes les données du `dossier` JSONField
   - Infos du candidat (nom, email, etc.)
   - Sections 1-9 normalisées
3. **Export** : Cliquer sur le bouton "Exporter en DOCX" dans l'interface candidat

## 🔧 Développement local

### Sans Docker

```bash
# 1. Créer venv et installer dépendances
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt

# 2. Configurer la BD PostgreSQL locale
# Éditer backend/app/config/settings.py DATABASE_URL

# 3. Migrations
python manage.py migrate

# 4. Démarrer le serveur
python manage.py runserver

# Accessible sur http://localhost:8000
```

## 📚 Documentation

- **Architecture détaillée** : Voir [backend/app/formulaire/README.md](backend/app/formulaire/README.md)
- **Workflow utilisateur** : Voir la section "Workflows" dans la doc détaillée
- **Exemple de structure JSON** : Voir [inputs/JNZ_app.json](inputs/JNZ_app.json)

## 🐛 Support & Issues

- Les logs sont disponibles via `docker compose logs -f`
- Mode DEBUG activable via `.env`
- Admin Django accessible sur `/admin` après création d'un superutilisateur

## 📝 Licence

© 2025 - DC Formulaire
