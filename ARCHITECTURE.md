# 📋 Architecture du Formulaire Candidat - DC Formulaire

## Vue d'ensemble

L'application DC Formulaire est une application Django pour gérer les profils de candidats. Elle est structurée autour d'**9 sections principales** organisées de manière cohérente dans tous les fichiers (views, URLs, forms, templates).

---

## 📍 9 Sections principales

### 1. **Headers & Infos du Candidat**
- **Fichiers concernés**: views.py, urls.py, forms.py, candidat_edit.html
- **Description**: Gestion des informations de base du candidat
- **Éléments**:
  - Nom, Prénom, Email, Trigramme
  - Poste principal
  - Années d'expérience
- **Vues**: `candidat_list`, `candidat_create`, `candidat_detail`, `candidat_edit`
- **Formulaire**: `CandidatInfoForm`

### 2. **Postes Cibles**
- **Fichiers concernés**: views.py, urls.py, candidat_edit.html
- **Description**: Liste des postes visés par le candidat avec gestion d'état
- **Opérations**: Ajouter, Supprimer, Activer, Mettre à jour
- **Vues**: `poste_cible_add`, `poste_cible_delete`, `poste_cible_activate`, `poste_cible_update`

### 3. **Main-Skills Domaines** (section bullet)
- **Fichiers concernés**: views.py, urls.py, forms.py, candidat_edit.html
- **Description**: Hiérarchie des domaines de compétences (ex: "Développement")
- **Structure**: Arborescence avec domaines principaux et compétences enfants
- **Vues**: `main_skills_hierarchy_add`, `main_skills_hierarchy_add_child`, `main_skills_hierarchy_update`, `main_skills_hierarchy_delete`
- **Template partial**: `main_skills_hierarchy_item.html`

### 4. **Main-Skills Outils** (section table)
- **Fichiers concernés**: views.py, urls.py, candidat_edit.html
- **Description**: Hiérarchie des outils et langages (ex: "Python", "JavaScript")
- **Structure**: Arborescence similaire aux domaines
- **Vues**: Mêmes vues que domaines (logique partagée)
- **Rendu**: Tableau au lieu de bullets

### 5. **Formations**
- **Fichiers concernés**: views.py, urls.py, forms.py, candidat_edit.html
- **Description**: Liste des formations académiques
- **Éléments**: Titre, École, Date, Description
- **Vues**: `formation_add`, `formation_remove`
- **Formulaire**: `FormationForm`

### 6. **Certifications**
- **Fichiers concernés**: views.py, urls.py, forms.py, candidat_edit.html
- **Description**: Liste des certifications professionnelles
- **Éléments**: Titre, Date, Description
- **Vues**: `certification_add`, `certification_remove`
- **Formulaire**: `CertificationForm`

### 7. **Langues**
- **Fichiers concernés**: views.py, urls.py, forms.py, candidat_edit.html
- **Description**: Liste des langues parlées
- **Éléments**: Nom de la langue, Niveau/Détails
- **Vues**: `langue_add`, `langue_remove`
- **Formulaire**: `LangueForm`

### 8. **Xp_Pro Blocs** (1ère étape du workflow)
- **Fichiers concernés**: views.py, urls.py, forms.py, candidat_edit.html
- **Description**: Expériences professionnelles principales
- **Éléments**: Entreprise, Poste, Période, Contexte, Technologies
- **Vues**: `experience_add`, `experience_remove`
- **Formulaire**: `ExperienceForm`
- **Workflow**: Première étape du processus d'édition des expériences

### 9. **Xp_Pro Bullets** (2e étape du workflow)
- **Fichiers concernés**: views.py, urls.py, candidat_edit.html
- **Description**: Réalisations hiérarchiques au sein de chaque expérience
- **Structure**: Sous-éléments imbriqués dans chaque bloc d'expérience
- **Vues**: `xp_pro_realization_add`, `xp_pro_realization_update`, `xp_pro_realization_delete`
- **Template partial**: `xp_pro_hierarchy_item.html`
- **Helpers**: `_find_xp_pro_item_recursive()`, `_find_xp_pro_parent_and_index()`
- **Workflow**: Deuxième étape du processus d'édition des expériences

---

## 🏗️ Structure de stockage des données

Les données du candidat sont stockées dans un JSONField `dossier` du modèle `Candidat`:

```json
{
  "header": {
    "nom": "...",
    "prenom": "...",
    "email": "...",
    "trigramme": "...",
    "poste": "...",
    "xp_duration": 0
  },
  "poste_cible": [
    {
      "id": "uuid",
      "title": "...",
      "active": true
    }
  ],
  "main_skills": {
    "bullet": [
      {
        "id": "uuid",
        "name": "...",
        "children": [...]
      }
    ],
    "table": [
      {
        "id": "uuid",
        "name": "...",
        "children": [...]
      }
    ]
  },
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
      "realizations": [
        {
          "id": "uuid",
          "title": "...",
          "children": [...]
        }
      ]
    }
  ]
}
```

---

## 🔄 Workflows principaux

### Workflow édition candidat:
1. Ouvrir `candidat_edit` → Affichage de 9 cartes sections
2. Utilisateur modifie une section
3. Soumission HTMX (pas rechargement page)
4. Vue met à jour le JSONField `dossier`
5. Template affiche la section mise à jour

### Workflow 2-étapes pour expériences:
1. **Étape 1** (Section 8): Créer/modifier une expérience globale
2. **Étape 2** (Section 9): Ajouter les réalisations (bullets) sous cette expérience
3. Chaque réalisation peut elle-même avoir des sous-éléments (imbrication possible)

---

## 📝 Organisation des fichiers code

### `/backend/app/formulaire/views.py` (~900 lignes)
```
1. Imports & Helpers
   - Imports, _new_id(), _clean_text(), _empty_dossier(), _get_placeholders()
   
2. Headers & Infos du Candidat
   - candidat_list(), candidat_create(), candidat_detail(), candidat_edit()
   
3. Postes Cibles
   - poste_cible_add(), poste_cible_delete(), poste_cible_activate(), poste_cible_update()
   
4. Main-Skills Domaines
   - main_skills_hierarchy_* (add, add_child, update, delete)
   - _find_main_skills_hierarchy_parent_and_index() helper
   
5. Main-Skills Outils
   - Mêmes fonctions que domaines (avec paramètre section différent)
   
6. Formations
   - formation_add(), formation_remove()
   
7. Certifications
   - certification_add(), certification_remove()
   
8. Langues
   - langue_add(), langue_remove()
   
9. Xp_Pro Blocs
   - experience_add(), experience_remove()
   - _find_xp_pro_parent_and_index() helper
   
10. Xp_Pro Bullets
    - xp_pro_realization_add(), xp_pro_realization_update(), xp_pro_realization_delete()
    - _find_xp_pro_item_recursive() helper
    
11. DOCX Export
    - candidat_export_docx()
```

### `/backend/app/formulaire/urls.py` (29 URL patterns)
- Organisées selon les mêmes 9 sections
- Toutes les routes incluent l'UUID du candidat: `/candidat/<uuid:pk>/...`
- Préfixe de nom correspondant à la section

### `/backend/app/formulaire/forms.py` (5 formulaires)
```
1. CandidatInfoForm - Infos du candidat
2. FormationForm - Une formation
3. CertificationForm - Une certification
4. LangueForm - Une langue
5. ExperienceForm - Une expérience professionnelle
```

### `/backend/app/formulaire/templates/formulaire/candidat_edit.html` (~450 lignes)
- 9 cartes Bootstrap correspondant aux 9 sections
- Sections imbriquées: Section 9 (bullets) est imbriquée dans Section 8 (blocs)
- Utilise HTMX pour soumissions asynchrones
- Partials pour templates récursifs: `main_skills_hierarchy_item.html`, `xp_pro_hierarchy_item.html`

---

## ✨ Améliorations apportées

✅ **Clarté organisationnelle**: Structure cohérente dans tous les fichiers  
✅ **En-têtes explicites**: Sections délimitées avec marques markdown  
✅ **Navigation améliorée**: Facile de trouver une section spécifique  
✅ **Documentation intégrée**: Commentaires clairs pour chaque bloc  
✅ **Workflow évident**: La relation 2-étapes des expériences est claire  

---

## 🚀 Pour continuer le développement

- Garder la même structure pour nouvelles sections
- Respecter l'ordre 1-9 dans tous les fichiers
- Utiliser les en-têtes `# ========================================================================` pour cohérence
- S'inspirer des helpers existants (`_find_*_parent_and_index()`) pour structures arborescentes
