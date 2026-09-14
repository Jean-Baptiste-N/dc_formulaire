# Auto-Increment XP Duration Feature

## 📋 Vue d'ensemble

Cette fonctionnalité permet d'**auto-incrémenter** automatiquement la durée d'expérience (`xp_duration`) d'un candidat en fonction de :
- La durée initiale saisie par l'utilisateur lors de la création
- Le temps écoulé depuis la création du profil

## 🎯 Cas d'usage

**Exemple :**
- User crée un profil avec "5 années d'expérience" le 2026-09-09
- 2 ans plus tard (2028-09-09), le système affiche automatiquement "7 années"

## 🔧 Comment ça marche

### 1️⃣ Première création

L'utilisateur renseigne une valeur dans le formulaire de création (`xp_duration`).

```python
# Backend stocke :
candidat.xp_duration = 5           # Affichage/utilisation
candidat.xp_duration_start = 5     # Valeur de référence (interne)
candidat.created_at = 2026-09-09   # Date de création (auto)
```

### 2️⃣ Calcul automatique

Chaque fois que le candidat est affiché ou sauvegardé, le système **recalcule** la durée :

**Formule :**
```
xp_duration = xp_duration_start + ⌊ (now - created_at) / 365.25 ⌋
```

**Exemple de séquence :**
```
T0 (2026-09-09)  : xp_duration_start=5  → xp_duration=5
T+1 year (2027)  : xp_duration_start=5  → xp_duration=6
T+2 years (2028) : xp_duration_start=5  → xp_duration=7
```

### 3️⃣ Quand ça se met à jour

La mise à jour se déclenche automatiquement sur :
- ✅ Accès à la page d'édition (`/candidat/{slug}/modifier/`)
- ✅ Sauvegarde du formulaire (POST)
- ✅ Accès à la page de détail (`/candidat/{slug}/detail/`)
- ✅ Exécution de la commande d'admin

## 📱 Pour l'utilisateur

**Pour l'utilisateur final**, c'est transparent :
- Il renseigne une seule fois sa durée d'expérience à la création
- Le champ `xp_duration` se met à jour automatiquement
- Pas besoin de modifier manuellement chaque année

## 👨‍💻 Pour les développeurs

### Accéder à la durée calculée

```python
from formulaire.models import Candidat

candidat = Candidat.objects.get(pk='...')

# Lire la durée calculée (sans modifier la BD)
years = candidat.xp_duration_calculated
# → Retourne: int ou None

# Mettre à jour la BD si changée
was_updated = candidat.update_xp_duration()
# → Retourne: True si mise à jour, False sinon
```

### Champs du modèle

| Champ | Type | Rôle | Éditable |
|-------|------|------|----------|
| `xp_duration` | IntegerField | Valeur affichée dans l'interface | ❌ Auto-géré |
| `xp_duration_start` | IntegerField | Valeur initiale (référence) | ❌ Auto-géré |
| `created_at` | DateTimeField | Date de création du profil | ❌ Non éditable |

### Méthodes du modèle

#### `xp_duration_calculated` (Propriété)
```python
@property
def xp_duration_calculated(self) -> int | None:
    """Calcule la durée actuelle sans modifier la BD"""
```

**Retour :** durée calculée en années complètes ou `None`

#### `update_xp_duration()` (Méthode)
```python
def update_xp_duration(self) -> bool:
    """Met à jour xp_duration si la valeur calculée a changé"""
```

**Retour :** `True` si mise à jour en BD, `False` sinon

## 🛠️ Commandes d'administration

### Mettre à jour tous les candidats

```bash
# Voir ce qui changerait (dry-run)
python manage.py update_xp_durations --dry-run

# Appliquer les mises à jour
python manage.py update_xp_durations
```

**Sortie exemple :**
```
Traitement de 3 candidat(s)...

  ✓ Pas de changement | Jean DUPONT (créé: 2026-09-09, initial: 5)
  → 5 → 6 | Marie MARTIN (créé: 2025-09-09, initial: 5)
  → 10 → 13 | Pierre BERNARD (créé: 2023-09-09, initial: 10)

======================================================================
Résumé: 2 mise(s) à jour, 1 inchangé(s)
```

## 🚀 Étapes d'installation

### 1. Appliquer la migration

```bash
python manage.py migrate
```

Cela crée le champ `xp_duration_start` en base de données.

### 2. Initialiser les candidats existants

Pour les candidats créés avant cette fonctionnalité :

```bash
# Voir les changements avant de les appliquer
python manage.py update_xp_durations --dry-run

# Appliquer les mises à jour
python manage.py update_xp_durations
```

### 3. Vérifier l'intégration

C'est automatique ! Les vues `candidat_edit` et `candidat_detail` se chargent d'appeler `update_xp_duration()`.

## ⚠️ Notes importantes

- ✅ **Pas de perte de données** : `xp_duration_start` est conservé tel quel
- ✅ **Pas de modifications manuelles** : Champs auto-gérés (invisibles utilisateur)
- ✅ **Optimisé** : Ne met à jour la BD que si la valeur change
- ✅ **Respecte les timestamps** : `updated_at` est mis à jour comme d'habitude
- ⚠️ **Calcul par années complètes** : 1.9 ans = 1 an supplémentaire (pas d'arrondis)

## 🔄 Exemple complet

```python
# 1. User crée un profil
user = Candidat.objects.create(
    nom="DUPONT",
    prenom="Jean",
    email="jean.dupont@example.com",
    xp_duration=5  # Utilisateur renseigne "5 ans"
)

# Backend sauvegarde :
# user.xp_duration = 5
# user.xp_duration_start = 5  (auto-défini dans candidat_create)
# user.created_at = 2026-09-09

# 2. Deux ans plus tard...
user = Candidat.objects.get(pk=user.pk)
print(user.xp_duration_calculated)  # → 7

# 3. Afficher la page d'édition → auto-update
# candidat_edit() appelle user.update_xp_duration()
# → user.xp_duration passe de 5 à 7

# 4. User voit "7 ans" dans le formulaire
```

## 🐛 Dépannage

**Q: Pourquoi `xp_duration_calculated` retourne `None` ?**
A: L'un des deux champs est manquant : `xp_duration_start` ou `created_at`. Vérifiez en BD.

**Q: La durée n'a pas changé après une année ?**
A: Attendez une année **complète** (365.25 jours). Ça s'incrémente par années entières.

**Q: Puis-je éditer manuellement `xp_duration_start` ?**
A: C'est déconseillé (champ backstage). Utilisez plutôt un script Django pour corriger.

---

**Version:** 1.0  
**Date:** 2026-09-09  
**Statut:** ✅ Production-Ready
