# dc_formulaire

Un formulaire web pour remplir un DC EPSYL — saisie du parcours professionnel, stockage PostgreSQL, export DOCX via docxtpl.

## Stack

| Couche | Technologie |
|--------|-------------|
| Frontend | Django Templates + HTMX |
| Backend | Django 5 |
| Base de données | PostgreSQL 17 |
| Export | python-docx / docxtpl |
| Déploiement | Docker Compose |

## Lancement rapide (Docker)

```bash
cp .env.example .env
# Éditez .env pour changer SECRET_KEY et les mots de passe
docker compose up --build
```

L'application est accessible sur <http://localhost:8000>.

## Structure du projet

```
dc_formulaire/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── app/
│       ├── manage.py
│       ├── config/          # settings, urls, wsgi
│       └── formulaire/      # app Django principale
├── postgres/
└── templates_docx/          # ← déposez votre template ici
    └── dc_template.docx
```

## Template DOCX (docxtpl)

Placez votre template dans `templates_docx/dc_template.docx`.

### Variables disponibles dans le contexte

| Variable | Type | Description |
|----------|------|-------------|
| `nom` | str | Nom du candidat |
| `prenom` | str | Prénom du candidat |
| `email` | str | Email du candidat |
| `sections` | list | Liste des sections du parcours |

### Structure JSON d'une section

```
sections
└── section
    ├── id        (str, UUID)
    ├── titre     (str)
    └── postes    (list)
        └── poste
            ├── id          (str, UUID)
            ├── texte       (str)
            └── sous_postes (list)
                └── sous_poste
                    ├── id    (str, UUID)
                    └── texte (str)
```

### Exemple de template docxtpl

```
{% for section in sections %}
**{{ section.titre }}**

{% for poste in section.postes %}
• {{ poste.texte }}
{% for sous_poste in poste.sous_postes %}
  – {{ sous_poste.texte }}
{% endfor %}
{% endfor %}
{% endfor %}
```

> **Note :** `postes` (et non `items`) est utilisé intentionnellement pour éviter le conflit
> avec la méthode Python `dict.items()` lors du rendu Jinja2 par docxtpl.

## Développement local (sans Docker)

```bash
cd backend
pip install -r requirements.txt
# SQLite est utilisé par défaut si DATABASE_URL n'est pas définie
SECRET_KEY=dev python app/manage.py migrate
SECRET_KEY=dev python app/manage.py runserver
```
