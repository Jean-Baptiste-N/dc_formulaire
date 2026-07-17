# DC Formulaire - Architecture détaillée

Documentation technique de l'application formulaire candidat.

## 📚 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [9 Sections principales](#-9-sections-principales)
3. [Structure des données](#-structure-des-données)
4. [Architecture du code](#-architecture-du-code)
5. [Workflows](#-workflows-principaux)
6. [Patterns & Conventions](#-patterns--conventions)
7. [Guide de développement](#-guide-de-développement)

---

## Vue d'ensemble

L'application gère les profils de candidats (CV structuré) avec :

- **Structure cohérente** : 9 sections organisées identiquement dans tous les fichiers
- **Stockage flexible** : JSONField PostgreSQL pour structure arborescente
- **Interface réactive** : AJAX avec Fetch API (pas de rechargement page)
- **Export document** : Génération DOCX via docxtpl (templates Jinja2)
- **Code maintenable** : Patterns génériques + fonctions helper + commentaires organisés

---

## 📍 9 Sections principales

### 1. Headers & Infos du Candidat

**Objectif** : Gestion des informations de base du candidat

**Fichiers concernés** :
- `views.py` : `candidat_list()`, `candidat_create()`, `candidat_detail()`, `candidat_edit()`
- `urls.py` : Routes CRUD du candidat
- `forms.py` : `CandidatInfoForm`
- `templates/` : `candidat_list.html`, `candidat_create.html`, `candidat_detail.html`, `candidat_edit.html`

**Champs stockés dans `dossier.header`** :
```json
{
  "nom": "string",
  "prenom": "string",
  "email": "string",
  "trigramme": "string (optionnel)",
  "poste": "string (poste principal)",
  "xp_duration": "integer (années d'expérience)"
}
```

**Opérations** :
- Créer un candidat
- Afficher la liste
- Consulter le détail
- Éditer les infos
- Exporter en DOCX

---

### 2. Postes Cibles

**Objectif** : Gérer les postes visés par le candidat avec état d'activation

**Fichiers concernés** :
- `views.py` : `poste_cible_add()`, `poste_cible_delete()`, `poste_cible_activate()`, `poste_cible_update()`
- `urls.py` : 4 routes
- `candidat_edit.html` : Carte "Postes cibles" + JavaScript handlers

**Structure** :
```json
"poste_cible": [
  {
    "id": "uuid",
    "title": "string",
    "active": "boolean"
  }
]
```

**Opérations** :
- Ajouter un poste cible
- Supprimer un poste
- Activer/désactiver un poste
- Éditer le titre

**Patterns** :
- `createHandlerInitializer()` - Factory pour initialiser listeners
- `postAndInsertHTML()` - Utilitaire async/await pour fetch + insérer HTML

---

### 3. Main-Skills Domaines (section bullet)

**Objectif** : Gérer une hiérarchie de domaines de compétences (ex: "Développement")

**Fichiers concernés** :
- `views.py` : `main_skills_hierarchy_add()`, `main_skills_hierarchy_add_child()`, `main_skills_hierarchy_update()`, `main_skills_hierarchy_delete()`, `_find_main_skills_hierarchy_parent_and_index()`
- `urls.py` : 4 routes
- `candidat_edit.html` : Carte "Compétences domaines"
- `templates/partials/main_skills_hierarchy_item.html` : Template récursif

**Structure** :
```json
"main_skills": {
  "bullet": [
    {
      "id": "uuid",
      "name": "string",
      "children": [
        {
          "id": "uuid",
          "name": "string",
          "children": [...]
        }
      ]
    }
  ]
}
```

**Opérations** :
- Ajouter un domaine principal
- Ajouter un sous-domaine (enfant)
- Éditer un élément
- Supprimer un élément (y compris ses enfants)

**Patterns** :
- Récursion pour templates (`main_skills_hierarchy_item.html`)
- Helper `_find_main_skills_hierarchy_parent_and_index()` pour localiser un item à modifier

---

### 4. Main-Skills Outils (section table)

**Objectif** : Gérer une hiérarchie d'outils/langages (ex: "Python", "JavaScript")

**Fichiers concernés** :
- `views.py` : Mêmes fonctions que Section 3 (avec paramètre `section="table"`)
- `urls.py` : Mêmes routes
- `candidat_edit.html` : Carte "Compétences outils"
- Même template partial (rendu en tableau au lieu de bullets)

**Structure** : Identique à Section 3

**Différence clé** : Le rendu (bullets vs table) est contrôlé côté template, pas côté backend

---

### 5. Formations

**Objectif** : Gérer les formations académiques du candidat

**Fichiers concernés** :
- `views.py` : `formation_add()`, `formation_remove()`
- `urls.py` : 2 routes
- `forms.py` : `FormationForm`
- `candidat_edit.html` : Carte "Formations"

**Structure** :
```json
"formations": [
  {
    "id": "uuid",
    "title": "string",
    "school": "string",
    "date": "string",
    "description": "string"
  }
]
```

**Opérations** :
- Ajouter une formation
- Supprimer une formation

**Formulaire** : `FormationForm` (Django Form)

---

### 6. Certifications

**Objectif** : Gérer les certifications professionnelles

**Fichiers concernés** :
- `views.py` : `certification_add()`, `certification_remove()`
- `urls.py` : 2 routes
- `forms.py` : `CertificationForm`
- `candidat_edit.html` : Carte "Certifications"

**Structure** :
```json
"certifications": [
  {
    "id": "uuid",
    "title": "string",
    "date": "string",
    "description": "string"
  }
]
```

**Opérations** :
- Ajouter une certification
- Supprimer une certification

---

### 7. Langues

**Objectif** : Gérer les langues parlées par le candidat

**Fichiers concernés** :
- `views.py` : `langue_add()`, `langue_remove()`
- `urls.py` : 2 routes
- `forms.py` : `LangueForm`
- `candidat_edit.html` : Carte "Langues"

**Structure** :
```json
"langues": [
  {
    "id": "uuid",
    "name": "string",
    "level": "string"
  }
]
```

**Opérations** :
- Ajouter une langue
- Supprimer une langue

---

### 8. Expériences Professionnelles - Blocs

**Objectif** : Gérer les blocs d'expérience professionnelle (première étape du workflow)

**Fichiers concernés** :
- `views.py` : `experience_add()`, `experience_remove()`, `_find_xp_pro_parent_and_index()`
- `urls.py` : 2 routes
- `forms.py` : `ExperienceForm`
- `candidat_edit.html` : Section expériences

**Structure** :
```json
"xp_pro": [
  {
    "id": "uuid",
    "company": "string",
    "poste": "string",
    "date": "string",
    "context": "string",
    "technologies": "string",
    "realizations": []  // ← voir Section 9
  }
]
```

**Opérations** :
- Ajouter un bloc d'expérience
- Supprimer un bloc

**Note** : Les réalisations (bullets) pour ce bloc sont gérées en Section 9

---

### 9. Expériences Professionnelles - Réalisations (Bullets)

**Objectif** : Gérer les réalisations imbriquées au sein d'une expérience (deuxième étape du workflow)

**Fichiers concernés** :
- `views.py` : `xp_pro_realization_add()`, `xp_pro_realization_update()`, `xp_pro_realization_delete()`, `_find_xp_pro_item_recursive()`
- `urls.py` : 3 routes
- `candidat_edit.html` : Formulaires de réalisation (imbriqués dans la Section 8)
- `templates/partials/xp_pro_hierarchy_item.html` : Template récursif

**Structure** :
```json
"realizations": [
  {
    "id": "uuid",
    "title": "string",
    "order_index": "integer",
    "children": [
      {
        "id": "uuid",
        "title": "string",
        "order_index": "integer",
        "children": [...]
      }
    ]
  }
]
```

**Opérations** :
- Ajouter une réalisation (sous une expérience)
- Ajouter une sous-réalisation (imbrication)
- Éditer une réalisation
- Supprimer une réalisation
- Réordonner via drag-drop (client-side)

**Patterns** :
- Récursion pour templates (`xp_pro_hierarchy_item.html`)
- Helper `_find_xp_pro_item_recursive()` pour traverser l'arborescence

---

## 🏗️ Structure des données

### Modèle Candidat (`models.py`)

```python
class Candidat(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    nom = CharField(max_length=150)
    prenom = CharField(max_length=150)
    slug = SlugField(max_length=200, null=True, blank=True)
    email = EmailField(unique=True)
    
    # Infos supplémentaires (dénormalisées du dossier pour indexation)
    trigramme = CharField(max_length=10, blank=True)
    poste = CharField(max_length=150, blank=True)
    xp_duration = IntegerField(blank=True, null=True)
    
    # 🔑 Cœur : stockage JSON
    dossier = JSONField(default=dict)
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### JSONField `dossier` - Schéma complet

```json
{
  "header": {
    "nom": "string",
    "prenom": "string",
    "email": "string",
    "trigramme": "string",
    "poste": "string",
    "xp_duration": "integer"
  },
  "poste_cible": [
    {
      "id": "uuid",
      "title": "string",
      "active": "boolean"
    }
  ],
  "main_skills": {
    "bullet": [ /* hiérarchie */ ],
    "table": [ /* hiérarchie */ ]
  },
  "formations": [
    {
      "id": "uuid",
      "title": "string",
      "school": "string",
      "date": "string",
      "description": "string"
    }
  ],
  "certifications": [
    {
      "id": "uuid",
      "title": "string",
      "date": "string",
      "description": "string"
    }
  ],
  "langues": [
    {
      "id": "uuid",
      "name": "string",
      "level": "string"
    }
  ],
  "xp_pro": [
    {
      "id": "uuid",
      "company": "string",
      "poste": "string",
      "date": "string",
      "context": "string",
      "technologies": "string",
      "realizations": [ /* hiérarchie */ ]
    }
  ]
}
```

---

## 📝 Architecture du code

### Organisation par section

Chaque fichier clé est organisé selon les 9 sections + exports :

#### `views.py` (51 fonctions, ~1845 lignes)

```
0. HELPERS & UTILS
   - _new_id() → UUID unique
   - _empty_dossier() → Structure vide
   - _sync_header_and_defaults() → Synchronisation
   - get_candidat_or_redirect() → Lookup candidat

1. HEADERS & INFOS
   - candidat_list()
   - candidat_create()
   - candidat_detail()
   - candidat_edit()

2. POSTES CIBLES
   - poste_cible_add()
   - poste_cible_delete()
   - poste_cible_activate()
   - poste_cible_update()

3-4. MAIN-SKILLS (DOMAINES & OUTILS)
   - main_skills_hierarchy_add()
   - main_skills_hierarchy_add_child()
   - main_skills_hierarchy_update()
   - main_skills_hierarchy_delete()
   - _find_main_skills_hierarchy_parent_and_index()

5. FORMATIONS
   - formation_add()
   - formation_remove()

6. CERTIFICATIONS
   - certification_add()
   - certification_remove()

7. LANGUES
   - langue_add()
   - langue_remove()

8. XP-PRO BLOCS
   - experience_add()
   - experience_remove()

9. XP-PRO BULLETS
   - xp_pro_realization_add()
   - xp_pro_realization_update()
   - xp_pro_realization_delete()
   - _find_xp_pro_item_recursive()
   - _find_xp_pro_parent_and_index()

10. EXPORT DOCX
    - candidat_export_docx()
```

#### `urls.py` (29 URL patterns)

Routes organisées selon les 9 sections :

```python
# Section 1 : Headers
path('candidats/', candidat_list, name='candidat_list')
path('candidats/create/', candidat_create, name='candidat_create')
path('candidat/<uuid:pk>/', candidat_detail, name='candidat_detail')
path('candidat/<uuid:pk>/edit/', candidat_edit, name='candidat_edit')

# Section 2 : Postes cibles
path('candidat/<uuid:pk>/poste-cible/ajouter/', ...)
path('candidat/<uuid:pk>/poste-cible/<str:item_id>/activer/', ...)
# etc.
```

#### `forms.py` (5 formulaires)

```python
CandidatInfoForm          # Infos du candidat
FormationForm             # Formation
CertificationForm         # Certification
LangueForm                # Langue
ExperienceForm            # Expérience pro
```

#### `templates/formulaire/candidat_edit.html` (2352 lignes)

**Sections principales** :

1. **AppLogger** (lignes ~531-572) - Logging centralisé avec DEBUG context
2. **CONFIG Constants** (lignes ~575-600) - URLs, sélecteurs, messages
3. **Utility functions** (lignes ~607-677)
   - `createHandlerInitializer()` - Factory pour listeners
   - `postAndInsertHTML()` - Fetch générique async/await + insérer
4. **9 Cartes de sections** - Chacune avec handlers et templates
5. **Partials récursifs** - `main_skills_hierarchy_item.html`, `xp_pro_hierarchy_item.html`

---

## 🔄 Workflows principaux

### Workflow édition candidat (Standard)

1. User accède `/candidat/<uuid>/edit/`
2. Vue `candidat_edit()` charge le candidat
3. Template affiche 9 cartes sections Bootstrap
4. User modifie une section (ex: Ajouter une compétence)
5. JavaScript envoie fetch POST AJAX → `/candidat/<uuid>/main-skill/ajouter/`
6. Vue backend met à jour `dossier` JSONField
7. Vue retourne partial HTML mis à jour
8. JavaScript insère le HTML dans le DOM (Fetch API)
9. **Pas de rechargement page** - Interface réactive

### Workflow 2-étapes pour expériences (Spécial)

**Étape 1** : Créer le bloc d'expérience (Section 8)
1. User clique "Ajouter une expérience"
2. Formulaire pour : Entreprise, Poste, Période, Contexte, Technologies
3. Bloc créé avec `realizations: []` vide

**Étape 2** : Ajouter les réalisations (Section 9, imbriquée)
1. User clique "Ajouter une réalisation" sous le bloc
2. Formulaire pour : Titre de la réalisation
3. Réalisation ajoutée à `realizations[]`
4. User peut ajouter des sous-réalisations (imbrication)
5. User peut réordonner via drag-drop (Sortable.js)

### Workflow d'export DOCX

1. User clique "Exporter en DOCX"
2. Vue `candidat_export_docx()` charge le template
3. Toutes les données du `dossier` sont passées comme contexte Jinja2
4. docxtpl remplace les placeholders dans le document
5. Fichier `.docx` est généré et téléchargé

---

## 🔧 Patterns & Conventions

### 1. Génération d'UUID

```python
# ❌ Ancien
item_id = str(uuid.uuid4())

# ✅ Nouveau
item_id = _new_id()
```

### 2. Modification JSONField

```python
# 1. Charger le dossier
dossier = candidat.dossier

# 2. Modifier la copie
dossier["poste_cible"].append({"id": _new_id(), "title": "...", "active": False})

# 3. Sauvegarder
candidat.dossier = dossier
candidat.save(update_fields=["dossier", "updated_at"])
```

### 3. Recherche d'item dans l'arborescence

Pour les structures imbriquées (Main-Skills, Xp-Pro) :

```python
def _find_main_skills_hierarchy_parent_and_index(dossier, section, item_id, parent=None):
    """
    Traverse récursivement pour trouver un item et son parent.
    Retourne (parent_item, index_in_parent) ou (None, None) si non trouvé
    """
    items = dossier.get("main_skills", {}).get(section, [])
    for i, item in enumerate(items):
        if item["id"] == item_id:
            return (None, i)  # Root-level item
        
        # Recherche récursive dans les enfants
        result = _find_main_skills_hierarchy_parent_and_index(
            {"main_skills": {section: item["children"]}}, 
            section, 
            item_id, 
            parent=item
        )
        if result != (None, None):
            return (item, result[1])
    
    return (None, None)
```

### 4. Rendu de template partiel

```python
html = render_to_string(
    'formulaire/partials/main_skills_hierarchy_item.html',
    {
        'item': item,
        'section': section,
        'candidat_pk': candidat.pk,
    }
)
return JsonResponse({'html': html})
```

### 5. Réponse AJAX

```python
# Pour insertion dans le DOM
return JsonResponse({'html': html_content})

# Pour validation avec message
return JsonResponse({
    'success': False,
    'error': 'Titre requis'
}, status=400)
```

### 6. JavaScript - Fetch avec CONFIG

```javascript
// CONFIG constants
const CONFIG = {
  api: {
    posteCible: (pk, action) => `/candidat/${pk}/poste-cible/${action}/`,
    // ...
  },
  selectors: {
    posteCibleList: '#poste-cible-list',
    // ...
  },
  messages: {
    posteCible: 'Poste cible',
    // ...
  }
};

// Utilisation
async function addPostesCible(e) {
  e.preventDefault();
  const candidatPk = e.target.dataset.candidatPk;
  
  await postAndInsertHTML({
    endpoint: CONFIG.api.posteCible(candidatPk, 'ajouter'),
    formData: new FormData(),
    targetSelector: CONFIG.selectors.posteCibleList,
    context: CONFIG.messages.posteCible,
    onSuccess: initPostesCibleHandlers
  });
}
```

### 7. AppLogger - Logging centralisé

```javascript
const IS_DEBUG = {{ DEBUG|lower }};  // Django context

const AppLogger = {
  debug(label, msg) { if (IS_DEBUG) console.debug(`🐛 ${label}`, msg); },
  info(label, msg) { if (IS_DEBUG || !IS_DEBUG) console.log(`ℹ️  ${label}`, msg); },
  warn(label, msg) { console.warn(`⚠️  ${label}`, msg); },
  error(label, msg) { console.error(`❌ ${label}`, msg); }
};

// Utilisation
AppLogger.info('Poste cible', 'Ajout réussi');
AppLogger.error('Poste cible', 'Erreur serveur');
```

---

## 🛠️ Guide de développement

### Ajouter une nouvelle section

Si vous ajoutez une Section 10, suivez ce modèle :

1. **Modèle (`models.py`)** : Ajouter le champ au JSONField `dossier`

2. **Formulaire (`forms.py`)** :
   ```python
   class MonSectionForm(forms.Form):
       title = forms.CharField()
       # ...
   ```

3. **Vues (`views.py`)** :
   ```python
   # MARK: 10. MA SECTION
   
   def ma_section_add(request, pk):
       candidat = get_object_or_404(Candidat, pk=pk)
       dossier = candidat.dossier
       
       form = MonSectionForm(request.POST or None)
       if form.is_valid():
           dossier["ma_section"].append({
               "id": _new_id(),
               "title": form.cleaned_data["title"]
           })
           candidat.dossier = dossier
           candidat.save(update_fields=["dossier"])
           
           html = render_to_string('formulaire/partials/ma_section.html', {...})
           return JsonResponse({'html': html})
       
       return render(request, 'formulaire/form.html', {'form': form})
   
   def ma_section_remove(request, pk, item_id):
       # Implémentation similaire
   ```

4. **URLs (`urls.py`)** :
   ```python
   path('candidat/<uuid:pk>/ma-section/ajouter/', ma_section_add, name='ma_section_add'),
   path('candidat/<uuid:pk>/ma-section/<str:item_id>/supprimer/', ma_section_remove, name='ma_section_remove'),
   ```

5. **Template (`templates/formulaire/candidat_edit.html`)** :
   ```html
   <!-- Section 10 : Ma section -->
   <div class="card">
       <div class="card-header">
           <h3>Ma section</h3>
       </div>
       <div class="card-body" id="ma-section-list">
           {% include 'formulaire/partials/ma_section.html' %}
       </div>
   </div>
   ```

6. **Partial template (`templates/formulaire/partials/ma_section.html`)** :
   ```html
   {% for item in items %}
       <div class="item">
           {{ item.title }}
           <button onclick="maSection Remove(...)">Supprimer</button>
       </div>
   {% empty %}
       <p class="text-muted">Aucun élément</p>
   {% endfor %}
   ```

### Tester une modification

```bash
# Depuis le container
docker compose exec web python manage.py shell

# Charger un candidat
from formulaire.models import Candidat
c = Candidat.objects.first()
c.dossier  # Affiche la structure JSON

# Tester une modification
c.dossier["poste_cible"].append({"id": "...", "title": "..."})
c.save()
```

### Débogage JavaScript

Activez `DEBUG=True` dans `.env` pour voir les logs AppLogger dans la console du navigateur.

```javascript
// Dans la console du navigateur
AppLogger.debug('section', 'détail')
AppLogger.error('erreur', 'message')
```

---

## 📋 Commandes utiles

```bash
# Migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Admin
docker compose exec web python manage.py createsuperuser

# Données de test
docker compose exec web python manage.py shell < seed.py

# Tests
docker compose exec web python manage.py test formulaire

# Statiques
docker compose exec web python manage.py collectstatic --noinput

# Commandes custom
docker compose exec web python manage.py fix_skills_format_dict
docker compose exec web python manage.py fix_xp_pro_description
```

---

## 🎯 Résumé

| Aspect | Détail |
|--------|--------|
| **Modèle de données** | JSONField PostgreSQL flexible |
| **Vues** | 51 fonctions organisées par section |
| **URL patterns** | 29 routes, toutes avec `<uuid:pk>` |
| **Formulaires** | 5 Django Forms pour validation |
| **Templates** | Réutilisable, partials récursifs |
| **Frontend** | Vanilla JS, Fetch API, AppLogger, CONFIG |
| **Workflows** | Standard (AJAX), 2-étapes (Xp-Pro), Export DOCX |
| **Patterns** | Récursion, helpers, factory, async/await |

---

**Pour contribuer** : Respectez l'ordre des sections 1-9 dans tous les fichiers.
