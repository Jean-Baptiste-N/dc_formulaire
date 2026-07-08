import json
import logging
import uuid
from pathlib import Path
import io
import tempfile
from typing import Tuple, Literal, Optional
from docxtpl import DocxTemplate

from django.conf import settings
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.http import require_POST

from .forms import CandidatInfoForm
from .models import Candidat
from .utils import clean_text, remove_empty_paragraphs

logger = logging.getLogger(__name__)

# ============================================================================
# MARK: 0. HELPERS - Utility functions
# ============================================================================

def _new_id():
    return str(uuid.uuid4())

def get_candidat_or_redirect(pk_or_slug, index=0) -> Tuple[Literal['success', 'redirect', 'not_found'], Optional[Candidat]]:
    """Lookup candidat par slug ou pk. Si accès via pk, redirige vers slug.

    Pour les slugs avec doublons, utiliser le paramètre 'index' pour accéder au Nth candidat.
    """
    # Essayer de lookup par slug d'abord
    candidates = Candidat.objects.filter(slug=pk_or_slug).all()
    if candidates:
        # Vérifier l'index
        if index < 0 or index >= len(candidates):
            return ('not_found', None)
        candidat = candidates[index]
        return ('success', candidat)

    # Sinon, essayer par pk (UUID)
    try:
        candidat = Candidat.objects.get(pk=pk_or_slug)
        # Si on a trouvé via pk et qu'il a un slug différent, il faudra rediriger
        if candidat.slug and candidat.slug != pk_or_slug:
            return ('redirect', candidat)  # Signal de redirection
        return ('success', candidat)
    except Candidat.DoesNotExist:
        return ('not_found', None)

def _clean_text(text):
    """Wrapper pour compatibilité avec le code existant."""
    return clean_text(text)

def _empty_dossier():
    """Initialise la structure du dossier de competences."""
    return {
        "header": {},
        "poste_cible": [],
        "skills_cible": [],
        "main_skills": {
            "bullet": [],
            "table": []
        },
        "formations": [],
        "certifications": [],
        "langues": [],
        "xp_pro": []
    }

def _sync_header_and_defaults(candidat):
    """
    Synchro le header du dossier avec les infos du candidat.
    Initialise aussi poste_cible par défaut s'il n'existe pas.

    Retourne True si des changements ont été faits (pour décider si sauvegarder).
    """
    dossier = candidat.dossier or _empty_dossier()
    needs_save = False

    # Synchro du header
    current_header = dossier.get('header', {})
    new_header = {
        'nom': candidat.nom,
        'prenom': candidat.prenom,
        'email': candidat.email,
        'trigramme': candidat.trigramme,
        'poste': candidat.poste,
        'xp_duration': candidat.xp_duration,
    }

    if current_header != new_header:
        dossier['header'] = new_header
        needs_save = True

    # Initialiser poste_cible par défaut s'il n'existe pas/est vide
    if not dossier.get('poste_cible'):
        dossier['poste_cible'] = []
        if candidat.poste:
            dossier['poste_cible'].append({
                'id': _new_id(),
                'title': candidat.poste,
                'active': True
            })
        needs_save = True

    # Initialiser skills_cible par défaut s'il n'existe pas
    if not dossier.get('skills_cible'):
        dossier['skills_cible'] = []
        needs_save = True

    # Sauvegarder si nécessaire
    if needs_save:
        candidat.dossier = dossier
        candidat.save(update_fields=['dossier'])

    return needs_save

def _get_placeholders():
    """Centralize tous les placeholders pour l'UI."""
    return {
        "formations": {
            "title": "ex: Master en Informatique",
            "school": "ex: Université de Technologie",
            "date": "ex: 2015-2020",
            "description": "ex: Cours sur les algorithmes, structures de données, etc.",
        },
        "certifications": {
            "title": "ex: Certification Python",
            "date": "ex: 2021",
            "description": "ex: Formules et classes avancées en Python, gestion des exceptions, etc.",
        },
        "langues": {
            "title": "ex: Anglais",
            "description": "ex: Bilingue, TOEIC 925/990",
        },
        "experiences": {
            "company": "ex: Tech Solutions",
            "poste": "ex: Développeur Junior",
            "date": "ex: 2020-2023",
            "context": "ex: J'ai participé au développement d'une application pour la gestion des stocks, dans un équipe de 5 développeurs, en utilisant la méthodologie Agile...",
            "technologies": "ex: Python, Django, PostgreSQL...",
        },
        "main_skills": {
            "bullet": {
                0: "Domaine de Compétence",
                1: "Expertise",
            },
            "table": {
                0: "Catégorie",
                1: "Outil/Langage",
            },
        },
        "xp_pro": [
            "Activité",
            "Mission",
            "Tâche",
            "Sous-tâche",
        ],
    }

def _get_main_skills_placeholders(section):
    """Retourne les placeholders pour une section main_skills (bullet ou table)."""
    placeholders_dict = _get_placeholders()
    # Retourner directement le dict avec les indices numériques pour que le filtre get_placeholder:depth fonctionne
    return placeholders_dict["main_skills"][section]

def _ensure_realization_ids(description):
    """Ajoute des IDs aux réalisations qui n'en ont pas (migration)."""
    if not isinstance(description, list):
        return description

    for item in description:
        if "id" not in item:
            item["id"] = _new_id()
        if "description" in item and isinstance(item["description"], list):
            _ensure_realization_ids(item["description"])

    return description

def _ensure_hierarchy_ids(items):
    """Ajoute des IDs aux items main_skills qui n'en ont pas (migration)."""
    if not isinstance(items, list):
        return items

    for item in items:
        if "id" not in item:
            item["id"] = _new_id()
        if "description" in item and isinstance(item["description"], list):
            _ensure_hierarchy_ids(item["description"])

    return items

# ============================================================================
# MARK: 1. HEADERS & INFOS DU CANDIDAT - List, Create, Edit, Detail
# ============================================================================

def candidat_list(request):
    candidats = Candidat.objects.all()
    return render(request, "formulaire/candidat_list.html", {"candidats": candidats})

def candidat_create(request):
    if request.method == "POST":
        form = CandidatInfoForm(request.POST)
        if form.is_valid():
            candidat = form.save(commit=False)
            candidat.dossier = _empty_dossier()

            # Ajouter une première variante de poste cible avec le poste principal
            if candidat.poste:
                candidat.dossier["poste_cible"].append({
                    "id": _new_id(),
                    "title": candidat.poste,
                    "active": True
                })

            candidat.save()
            return redirect("formulaire:candidat_edit", pk=candidat.pk)
    else:
        form = CandidatInfoForm()
    return render(request, "formulaire/candidat_create.html", {"form": form})

# ---------------------------------------------------------------------------
# Candidat edit (main form)
# ---------------------------------------------------------------------------

def candidat_edit(request, pk=None, slug=None):
    identifier = slug or pk
    index = int(request.GET.get('index', 0))
    status, candidat = get_candidat_or_redirect(identifier, index=index)

    if status == 'not_found':
        raise Http404(f"Candidat not found: {identifier}")

    assert candidat is not None, f"Candidat should not be None (status={status})"

    # Si on accède via pk et le candidat a un slug différent, rediriger vers slug
    if status == 'redirect' and candidat.slug:
        url = f'/candidat/{candidat.slug}/modifier/'
        if index > 0:
            url += f'?index={index}'
        return redirect(url)

    # Synchro du header et initialisation des defaults (poste_cible)
    # À faire en premier, avant toute autre logique
    _sync_header_and_defaults(candidat)

    # Enrichir les réalisations et hiérarchies avec des IDs si nécessaire et sauvegarder
    ids_added = False
    if candidat.dossier:
        # Enrichir xp_pro
        if "xp_pro" in candidat.dossier:
            for exp in candidat.dossier["xp_pro"]:
                if "description" in exp:
                    _ensure_realization_ids(exp["description"])
                    ids_added = True

        # Enrichir main_skills (bullet et table)
        if "main_skills" in candidat.dossier:
            if "bullet" in candidat.dossier["main_skills"]:
                _ensure_hierarchy_ids(candidat.dossier["main_skills"]["bullet"])
                ids_added = True
            if "table" in candidat.dossier["main_skills"]:
                _ensure_hierarchy_ids(candidat.dossier["main_skills"]["table"])
                ids_added = True

    # Sauvegarder si des IDs ont été ajoutés (migration data)
    if ids_added:
        candidat.save(update_fields=["dossier"])

    if request.method == "POST":
        form = CandidatInfoForm(request.POST, instance=candidat)
        if form.is_valid():
            form.save()

            # Synchroniser les infos dans le dossier['header']
            # (le formulaire a mis à jour candidat, on synchro dans le dossier)
            _sync_header_and_defaults(candidat)
    else:
        form = CandidatInfoForm(instance=candidat)

    placeholders = _get_placeholders()
    context = {
        "candidat": candidat,
        "form": form,
        "placeholders": placeholders,
        "xp_pro_placeholders": placeholders.get("xp_pro", []),
    }

    return render(
        request,
        "formulaire/candidat_edit.html",
        context,
    )

# ---------------------------------------------------------------------------
# Candidat detail (visualisation)
# ---------------------------------------------------------------------------

def candidat_detail(request, pk=None, slug=None):
    identifier = slug or pk
    index = int(request.GET.get('index', 0))
    status, candidat = get_candidat_or_redirect(identifier, index=index)

    if status == 'not_found':
        raise Http404(f"Candidat not found: {identifier}")

    assert candidat is not None, f"Candidat should not be None (status={status})"

    # Si on accède via pk et le candidat a un slug différent, rediriger vers slug
    if status == 'redirect' and candidat.slug:
        url = f'/candidat/{candidat.slug}/detail/'
        if index > 0:
            url += f'?index={index}'
        return redirect(url)

    return render(request, "formulaire/candidat_detail.html", {"candidat": candidat})

# ============================================================================
# MARK: 2.1 POSTES CIBLES - Add, Delete, Activate, Update
# ============================================================================

@require_POST
def poste_cible_add(request, pk):
    """Ajoute une variante de poste cible."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "poste_cible" not in dossier:
        dossier["poste_cible"] = []

    # Créer une nouvelle variante
    new_poste_cible = {
        "id": _new_id(),
        "title": "",
        "active": False,
    }

    dossier["poste_cible"].append(new_poste_cible)
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])

    return render(
        request,
        "formulaire/partials/poste_cible_item.html",
        {"poste_cible": new_poste_cible, "candidat": candidat},
    )

@require_POST
def poste_cible_delete(request, pk, poste_cible_id):
    """Supprime une variante de poste cible."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "poste_cible" in dossier:
        dossier["poste_cible"] = [
            pc for pc in dossier["poste_cible"] if pc["id"] != poste_cible_id
        ]
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return HttpResponse("")

@require_POST
def poste_cible_activate(request, pk, poste_cible_id):
    """Active une variante de poste cible (déplie les autres)."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "poste_cible" in dossier:
        for pc in dossier["poste_cible"]:
            pc["active"] = (pc["id"] == poste_cible_id)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return HttpResponse("")

@require_POST
def poste_cible_update(request, pk, poste_cible_id):
    """Met à jour le titre d'une variante de poste cible."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    title = _clean_text(request.POST.get("title", ""))

    if "poste_cible" in dossier:
        for pc in dossier["poste_cible"]:
            if pc["id"] == poste_cible_id:
                pc["title"] = title
                break
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return HttpResponse("")

@require_POST
def poste_cible_bulk_update(request, pk):
    """Met à jour les titres de plusieurs variantes de poste cible (bulk update)."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        items = json.loads(request.POST.get("items", "[]"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "poste_cible" in dossier:
        for item in items:
            for pc in dossier["poste_cible"]:
                if pc["id"] == item.get("id"):
                    pc["title"] = _clean_text(item.get("title", ""))
                    break
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return JsonResponse({"status": "ok"})

# ============================================================================
# MARK: 2.2 SKILLS_CIBLE - Compétences cibles (Checkboxes)
# ============================================================================

@require_POST
def skills_cible_add(request, pk):
    """Ajoute une compétence cible."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "skills_cible" not in dossier:
        dossier["skills_cible"] = []

    # Créer une nouvelle compétence cible
    new_skill_cible = {
        "id": _new_id(),
        "title": "",
        "active": False,
    }

    dossier["skills_cible"].append(new_skill_cible)
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])

    return render(
        request,
        "formulaire/partials/skills_cible_item.html",
        {"skills_cible": new_skill_cible, "candidat": candidat},
    )

@require_POST
def skills_cible_delete(request, pk, skills_cible_id):
    """Supprime une compétence cible."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "skills_cible" in dossier:
        dossier["skills_cible"] = [
            sc for sc in dossier["skills_cible"] if sc["id"] != skills_cible_id
        ]
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return HttpResponse("")

@require_POST
def skills_cible_toggle(request, pk, skills_cible_id):
    """Active/désactive une compétence cible (toggle checkbox)."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "skills_cible" in dossier:
        for sc in dossier["skills_cible"]:
            if sc["id"] == skills_cible_id:
                sc["active"] = not sc["active"]
                break
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return HttpResponse("")

@require_POST
def skills_cible_update(request, pk, skills_cible_id):
    """Met à jour le titre d'une compétence cible."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    title = _clean_text(request.POST.get("title", ""))

    if "skills_cible" in dossier:
        for sc in dossier["skills_cible"]:
            if sc["id"] == skills_cible_id:
                sc["title"] = title
                break
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return HttpResponse("")

@require_POST
def skills_cible_bulk_update(request, pk):
    """Met à jour les titres de plusieurs compétences cibles (bulk update)."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        items = json.loads(request.POST.get("items", "[]"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "skills_cible" in dossier:
        for item in items:
            for sc in dossier["skills_cible"]:
                if sc["id"] == item.get("id"):
                    sc["title"] = _clean_text(item.get("title", ""))
                    sc["active"] = item.get("active", False)
                    break
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return JsonResponse({"status": "ok"})

# ============================================================================
# MARK: 3.1 MAIN-SKILLS DOMAINES DE COMPÉTENCES - Bullet Section
# ============================================================================

@require_POST
def main_skills_hierarchy_add(request, pk, section):
    """Ajoute un item racine à main_skills.bullet ou main_skills.table."""
    # section: 'bullet' ou 'table'
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "main_skills" not in dossier:
        dossier["main_skills"] = {"bullet": [], "table": []}
    if section not in dossier["main_skills"]:
        dossier["main_skills"][section] = []

    new_item = {
        "id": _new_id(),
        "title": "",
        "description": []
    }

    dossier["main_skills"][section].append(new_item)
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])

    # Retourner le template HTML du nouvel item
    placeholders = _get_main_skills_placeholders(section)
    return render(
        request,
        "formulaire/partials/main_skills_hierarchy_item.html",
        {
            "item": new_item,
            "depth": 0,
            "target_index": len(dossier["main_skills"][section]) - 1,
            "endpoint_base": f"main_skills_{section}",
            "max_depth": 1,
            "main_skills_placeholders": placeholders,
        }
    )

@require_POST
def main_skills_hierarchy_add_child(request, pk, section):
    """Ajoute un enfant à un item de main_skills."""
    try:
        candidat = get_object_or_404(Candidat, pk=pk)
        dossier = candidat.dossier or _empty_dossier()

        parent_id = request.POST.get("parent_id", "")
        depth = int(request.POST.get("depth", "0"))
        target_index = request.POST.get("target_index", "")

        if "main_skills" not in dossier or section not in dossier["main_skills"]:
            return HttpResponse("Section introuvable", status=404)

        if depth > 1:
            return HttpResponse("⚠️ Limite de profondeur atteinte (2 niveaux maximum)", status=400)

        # Trouver le parent
        parent_list, parent_idx = _find_main_skills_hierarchy_parent_and_index(dossier["main_skills"][section], parent_id)
        if parent_list is None:
            return HttpResponse("Parent introuvable", status=404)

        parent = parent_list[parent_idx]
        new_child = {
            "id": _new_id(),
            "title": "",
            "description": []
        }

        parent["description"].append(new_child)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Récupérer les placeholders
        placeholders = _get_main_skills_placeholders(section)

        return render(
            request,
            "formulaire/partials/main_skills_hierarchy_item.html",
            {
                "item": new_child,
                "depth": depth,
                "target_index": target_index,
                "endpoint_base": f"main_skills_{section}",
                "max_depth": 1,
                "main_skills_placeholders": placeholders,
            }
        )
    except (ValueError, KeyError) as e:
        logger.error(f"Erreur main_skills_hierarchy_add_child: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)

@require_POST
def main_skills_hierarchy_update(request, pk, section, item_id):
    """Met à jour le titre d'un item main_skills."""
    try:
        candidat = get_object_or_404(Candidat, pk=pk)
        dossier = candidat.dossier or _empty_dossier()
        title = _clean_text(request.POST.get("title", ""))

        if "main_skills" not in dossier or section not in dossier["main_skills"]:
            return HttpResponse("Section introuvable", status=404)

        parent_list, idx = _find_main_skills_hierarchy_parent_and_index(dossier["main_skills"][section], item_id)
        if parent_list is None or idx is None:
            return HttpResponse("Item introuvable", status=404)

        parent_list[idx]["title"] = title
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        return HttpResponse("OK")
    except Exception as e:
        logger.error(f"Erreur main_skills_hierarchy_update: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)

@require_POST
def main_skills_hierarchy_delete(request, pk, section, item_id):
    """Supprime un item main_skills et ses enfants."""
    try:
        candidat = get_object_or_404(Candidat, pk=pk)
        dossier = candidat.dossier or _empty_dossier()

        if "main_skills" not in dossier or section not in dossier["main_skills"]:
            return HttpResponse("Section introuvable", status=404)

        parent_list, idx = _find_main_skills_hierarchy_parent_and_index(dossier["main_skills"][section], item_id)
        if parent_list is None or idx is None:
            return HttpResponse("Item introuvable", status=404)

        parent_list.pop(idx)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        return HttpResponse("OK")
    except Exception as e:
        logger.error(f"Erreur main_skills_hierarchy_delete: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)

def _find_main_skills_hierarchy_parent_and_index(items, item_id):
    """Cherche récursivement un item main_skills par ID et retourne (parent_list, index)."""
    for idx, item in enumerate(items):
        if item.get("id") == item_id:
            return items, idx
        if "description" in item and isinstance(item["description"], list):
            result = _find_main_skills_hierarchy_parent_and_index(item["description"], item_id)
            if result[0] is not None:
                return result
    return None, None

@require_POST
def main_skills_hierarchy_bulk_update(request, pk, section):
    """Met à jour les titres de plusieurs items main_skills (bulk update)."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        items = json.loads(request.POST.get("items", "[]"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "main_skills" not in dossier or section not in dossier["main_skills"]:
        return JsonResponse({"error": "Section not found"}, status=404)

    # Fonction interne pour mettre à jour récursivement
    def update_items_recursive(items_list, items_to_update):
        for item in items_list:
            for update_item in items_to_update:
                if item.get("id") == update_item.get("id"):
                    item["title"] = _clean_text(update_item.get("title", ""))
                    break
            # Récursion sur les enfants
            if "description" in item and isinstance(item["description"], list):
                update_items_recursive(item["description"], items_to_update)

    update_items_recursive(dossier["main_skills"][section], items)
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])

    return JsonResponse({"status": "ok"})

# ============================================================================
# MARK: 3.2 MAIN-SKILLS OUTILS & LANGAGES - Table Section
# ============================================================================
# Note: Les fonctions pour la table sont les mêmes que pour bullet (main_skills_hierarchy_*)
# La différence réside dans le paramètre 'section' passé aux URLs

# ============================================================================
# MARK: 4. FORMATIONS - Add, Remove
# ============================================================================

@require_POST
def formation_add(request, pk):
    """Ajoute une formation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    formation = {
        "title": _clean_text(request.POST.get("title", "")),
        "school": _clean_text(request.POST.get("school", "")),
        "date": _clean_text(request.POST.get("date", "")),
        "description": _clean_text(request.POST.get("description", "")),
    }

    if formation["title"] and formation["school"]:
        if "formations" not in dossier:
            dossier["formations"] = []
        dossier["formations"].append(formation)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Pour AJAX: retourner juste le snippet HTML du nouvel élément
        index = len(dossier["formations"]) - 1
        desc_html = f'<br><small class="text-muted">{escape(formation["description"])}</small>' if formation.get("description", "").strip() else ''
        html = f'''<div class="alert alert-info mb-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>{escape(formation["date"])} - {escape(formation["title"])}</strong> <br>
              <small>{escape(formation["school"])}</small>
              {desc_html}
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger btn-formation-remove"
                    data-candidat-pk="{pk}"
                    data-formation-index="{index}">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>'''
        return HttpResponse(html)

    return redirect("formulaire:candidat_edit", pk=pk)

@require_POST
def formation_remove(request, pk, index):
    """Supprime une formation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "formations" in dossier and 0 <= index < len(dossier["formations"]):
            dossier["formations"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
            # Return JSON for AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
                return JsonResponse({"success": True})
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)

# ============================================================================
# MARK: 5. CERTIFICATIONS - Add, Remove
# ============================================================================

@require_POST
def certification_add(request, pk):
    """Ajoute une certification."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    certification = {
        "title": _clean_text(request.POST.get("title", "")),
        "date": _clean_text(request.POST.get("date", "")),
        "description": _clean_text(request.POST.get("description", "")),
    }

    if certification["title"]:
        if "certifications" not in dossier:
            dossier["certifications"] = []
        dossier["certifications"].append(certification)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Pour AJAX: retourner juste le snippet HTML du nouvel élément
        index = len(dossier["certifications"]) - 1
        desc_html = f'<br><small class="text-muted">{escape(certification["description"])}</small>' if certification.get("description", "").strip() else ''
        html = f'''<div class="alert alert-info mb-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>{escape(certification["date"])} - {escape(certification["title"])}</strong>
              {desc_html}
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger btn-certification-remove"
                    data-candidat-pk="{pk}"
                    data-certification-index="{index}">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>'''
        return HttpResponse(html)

    return redirect("formulaire:candidat_edit", pk=pk)

@require_POST
def certification_remove(request, pk, index):
    """Supprime une certification."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "certifications" in dossier and 0 <= index < len(dossier["certifications"]):
            dossier["certifications"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
            # Return JSON for AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
                return JsonResponse({"success": True})
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)

# ============================================================================
# MARK: 6. LANGUES - Add, Remove
# ============================================================================

@require_POST
def langue_add(request, pk):
    """Ajoute une langue."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    langue = {
        "title": _clean_text(request.POST.get("title", "")),
        "description": _clean_text(request.POST.get("description", "")),
    }

    if langue["title"]:
        if "langues" not in dossier:
            dossier["langues"] = []
        dossier["langues"].append(langue)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Pour AJAX: retourner juste le snippet HTML du nouvel élément
        index = len(dossier["langues"]) - 1
        desc_html = f'<br><small class="text-muted">{escape(langue["description"])}</small>' if langue.get("description", "").strip() else ''
        html = f'''<div class="alert alert-info mb-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>{escape(langue["title"])}</strong>
              {desc_html}
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger btn-langue-remove"
                    data-candidat-pk="{pk}"
                    data-langue-index="{index}">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>'''
        return HttpResponse(html)

    return redirect("formulaire:candidat_edit", pk=pk)

@require_POST
def langue_remove(request, pk, index):
    """Supprime une langue."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "langues" in dossier and 0 <= index < len(dossier["langues"]):
            dossier["langues"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
            # Return JSON for AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
                return JsonResponse({"success": True})
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)

# ============================================================================
# MARK: 7.1 XP_PRO BLOCS - 1ère étape du workflow (Add, Remove)
# ============================================================================

@require_POST
def experience_add(request, pk):
    """Ajoute une expérience professionnelle."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    technologies = request.POST.get("technologies", "").strip()
    tech_list = [_clean_text(t) for t in technologies.split(",") if t.strip()] if technologies else []

    # Pré-remplir avec un premier item vide (scaffolding UX)
    description_array = [{
        "id": _new_id(),
        "title": "",
        "description": []
    }]

    experience = {
        "company": _clean_text(request.POST.get("company", "")),
        "poste": _clean_text(request.POST.get("poste", "")),
        "date": _clean_text(request.POST.get("date", "")),
        "context": _clean_text(request.POST.get("context", "")),
        "description": description_array,
        "env_tech": tech_list,
    }

    if experience["company"] and experience["poste"]:
        if "xp_pro" not in dossier:
            dossier["xp_pro"] = []
        dossier["xp_pro"].append(experience)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Pour AJAX: retourner la section complète avec toutes les sous-sections remplissables
        index = len(dossier["xp_pro"]) - 1
        placeholders = _get_placeholders()

        # Générer le HTML des réalisations avec le partial existant
        realizations_html = ""
        for realization in experience["description"]:
            realizations_html += render_to_string(
                "formulaire/partials/xp_pro_hierarchy_item.html",
                {
                    "item": realization,
                    "exp_index": index,
                    "depth": 0,
                    "candidat": candidat,
                    "xp_pro_placeholders": placeholders.get("xp_pro", {}),
                }
            )

        # Tech badges HTML
        tech_badges_html = ""
        if tech_list:
            for tech in tech_list:
                tech_badges_html += f'<span class="badge bg-info text-dark me-2 mb-2">{escape(tech)}<button type="button" class="btn-xp-pro-step2-tech-remove" data-tech="{escape(tech)}">×</button></span>'
        else:
            tech_badges_html = '<span class="text-muted small">Aucune technologie ajoutée</span>'

        # Retourner le HTML complet avec structure xp_pro_step2
        html = f'''<div class="alert alert-xp-pro mb-3 xp-pro-step2-container" data-exp-index="{index}" data-candidat-pk="{pk}">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div style="flex: 1;">
              <strong>{escape(experience["date"])} : {escape(experience["poste"])}</strong> chez <strong>{escape(experience["company"])}</strong><br>
            </div>
            <button type="button" class="btn btn-sm btn-danger btn-experience-remove"
                    data-candidat-pk="{pk}"
                    data-exp-index="{index}">
              <i class="bi bi-trash"></i>
            </button>
          </div>

          <!-- Contexte -->
          <div class="mb-4">
            <label class="form-label small fw-semibold"><i class="bi bi-list-check"></i> Contexte de l'expérience</label>
            <textarea class="form-control xp-pro-step2-context"
                      placeholder="{escape(placeholders['experiences']['context'])}"
                      rows="2">{escape(experience.get('context', ''))}</textarea>
          </div>

          <!-- Technologies -->
          <div class="mb-4">
            <label class="form-label small fw-semibold"><i class="bi bi-list-check"></i> Technologies utilisées</label>
            <div class="input-group input-group-sm mb-2">
              <input type="text"
                      class="form-control xp-pro-step2-tech-input"
                      placeholder="ex: Python, Django, PostgreSQL... (séparées par des virgules)"
                      data-separator=",">
              <button class="btn btn-outline-success btn-sm btn-xp-pro-step2-tech-add" type="button">
                <i class="bi bi-plus-lg"></i>
              </button>
            </div>
            <div class="xp-pro-step2-tech-badges">
              {tech_badges_html}
            </div>
          </div>

          <!-- Réalisations -->
          <div class="mb-4">
            <label class="form-label small fw-semibold"><i class="bi bi-list-check"></i> Réalisations</label>
            <div id="realizations-{index}" class="xp-pro-step2-realizations ps-2">
              {realizations_html}
            </div>
          </div>

          <!-- Boutons -->
          <div class="d-flex gap-2 align-items-center pt-3 border-top">
            <button type="button" class="btn btn-sm btn-secondary btn-xp-pro-step2-add-realization">
              <i class="bi bi-plus-lg"></i> Ajouter une Activité
            </button>
            <button type="button"
                    class="btn btn-sm btn-success btn-xp-pro-step2-save"
                    data-exp-index="{index}"
                    data-candidat-pk="{pk}">
              <i class="bi bi-check-lg"></i> Enregistrer
            </button>
          </div>
        </div>'''
        return HttpResponse(html)

    return redirect("formulaire:candidat_edit", pk=pk)

@require_POST
def experience_remove(request, pk, index):
    """Supprime une expérience."""

    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "xp_pro" in dossier and 0 <= index < len(dossier["xp_pro"]):
            dossier["xp_pro"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
            # Return JSON for AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
                return JsonResponse({"success": True})
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)

def _calculate_xp_pro_depth(items, item_id, current_depth=0):
    """Calcule la profondeur d'un item xp_pro dans la hiérarchie (pour validation)."""
    for item in items:
        if item.get("id") == item_id:
            return current_depth
        if "description" in item and isinstance(item["description"], list):
            result = _calculate_xp_pro_depth(item["description"], item_id, current_depth + 1)
            if result is not None:
                return result
    return None

def _find_xp_pro_item_recursive(items, item_id):
    """Cherche un item xp_pro par son ID dans la structure récursive (description)."""
    for item in items:
        if item.get("id") == item_id:
            return item
        if "description" in item and isinstance(item["description"], list):
            found = _find_xp_pro_item_recursive(item["description"], item_id)
            if found:
                return found
    return None

def _find_xp_pro_parent_and_index(items, item_id):
    """Cherche le parent et l'index d'un item xp_pro dans la structure récursive."""
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            return items, i
        if "description" in item and isinstance(item["description"], list):
            parent, idx = _find_xp_pro_parent_and_index(item["description"], item_id)
            if parent is not None:
                return parent, idx
    return None, None

# ============================================================================
# MARK: 7.2 XP_PRO BULLETS - 2e étape du workflow (Add, Update, Delete)
# ============================================================================

@require_POST
def xp_pro_realization_add(request, pk, exp_index):
    """Ajoute une réalisation xp_pro ou un sous-item à une réalisation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        exp_index = int(exp_index)
        if "xp_pro" not in dossier or exp_index >= len(dossier["xp_pro"]):
            return HttpResponse("Expérience introuvable", status=404)

        experience = dossier["xp_pro"][exp_index]

        # Initialiser description si nécessaire
        if "description" not in experience:
            experience["description"] = []
        elif not isinstance(experience["description"], list):
            experience["description"] = []

        new_item = {
            "id": _new_id(),
            "title": "",
            "description": []
        }

        # Vérifier si c'est un sous-item (a un parent_id)
        parent_id = request.POST.get("parent_id")
        requested_depth = request.POST.get("depth")

        # Limiter à 3 niveaux de détails (depth max = 3)
        if requested_depth:
            requested_depth = int(requested_depth)
            if requested_depth > 3:
                return HttpResponse("Limite de profondeur atteinte (3 niveaux de détails maximum)", status=400)

        if parent_id:
            logger.info(f"Cherche parent_id={parent_id} dans exp {exp_index}")
            logger.info(f"Items en base avec IDs: {[item.get('id') for item in experience['description']]}")
            parent = _find_xp_pro_item_recursive(experience["description"], parent_id)
            if parent:
                if "description" not in parent:
                    parent["description"] = []
                parent["description"].append(new_item)
                logger.info(f"Parent trouvé! Nouvel item ajouté sous {parent.get('id')}")
            else:
                logger.error(f"❌ Parent {parent_id} non trouvé!")
                logger.error(f"   Tous les IDs disponibles: {[item.get('id') for item in experience['description']]}")
                logger.error(f"   Cherchait dans: {experience['description']}")
                return HttpResponse(f"Parent introuvable (cherchait {parent_id[:8]}...)", status=404)
        else:
            # C'est un item racine
            experience["description"].append(new_item)

        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Retourner le HTML du nouvel item avec la profondeur correcte
        current_depth = requested_depth if requested_depth else 0
        xp_pro_placeholders = _get_placeholders()["xp_pro"]
        html = render_to_string(
            "formulaire/partials/xp_pro_hierarchy_item.html",
            {
                "item": new_item,
                "exp_index": exp_index,
                "depth": current_depth,
                "xp_pro_placeholders": xp_pro_placeholders,
            }
        )
        return HttpResponse(html)

    except (ValueError, IndexError) as e:
        logger.error(f"Erreur xp_pro_realization_add: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)

@require_POST
def xp_pro_realization_delete(request, pk, exp_index, item_id):
    """Supprime une réalisation xp_pro et ses enfants."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        exp_index = int(exp_index)
        if "xp_pro" not in dossier or exp_index >= len(dossier["xp_pro"]):
            return HttpResponse("Expérience introuvable", status=404)

        experience = dossier["xp_pro"][exp_index]
        if "description" not in experience or not isinstance(experience["description"], list):
            return HttpResponse("Description introuvable", status=404)

        parent, idx = _find_xp_pro_parent_and_index(experience["description"], item_id)
        if parent is None or idx is None:
            return HttpResponse("Item introuvable", status=404)

        # Supprimer l'item
        parent.pop(idx)

        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        return HttpResponse("OK")

    except (ValueError, IndexError) as e:
        logger.error(f"Erreur xp_pro_realization_delete: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)

@require_POST
def xp_pro_step2_update(request, pk, exp_index):
    """
    Met à jour les 3 sections de la 2e étape du workflow xp_pro:
    - Contexte de l'expérience
    - Technologies utilisées (env_tech)
    - Réalisations (description)
    """
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        exp_index = int(exp_index)
        if "xp_pro" not in dossier or exp_index >= len(dossier["xp_pro"]):
            return JsonResponse({"error": "Experience not found"}, status=404)

        experience = dossier["xp_pro"][exp_index]
        if "description" not in experience or not isinstance(experience["description"], list):
            return JsonResponse({"error": "Description not found"}, status=404)

        # 1. Mettre à jour le contexte
        context = request.POST.get("context", "").strip()
        experience["context"] = _clean_text(context)

        # 2. Mettre à jour les technologies (env_tech)
        env_tech_raw = request.POST.get("env_tech", "")
        try:
            # Essayer de parser comme JSON (array)
            if env_tech_raw.startswith("["):
                env_tech_list = json.loads(env_tech_raw)
                # Nettoyer chaque tech après parse JSON (supprime les guillemets d'échappement)
                env_tech_list = [_clean_text(tech) if isinstance(tech, str) else tech for tech in env_tech_list if tech]
            else:
                # Sinon, parser comme chaîne comma-separated
                env_tech_list = [_clean_text(tech.strip()) for tech in env_tech_raw.split(",") if tech.strip()]
        except json.JSONDecodeError:
            env_tech_list = [_clean_text(tech.strip()) for tech in env_tech_raw.split(",") if tech.strip()]

        experience["env_tech"] = env_tech_list

        # 3. Mettre à jour les réalisations (description)
        realization_items = request.POST.get("realizations", "[]")
        try:
            realization_list = json.loads(realization_items) if realization_items else []
        except json.JSONDecodeError:
            realization_list = []

        # Fonction pour nettoyer et reconstruire l'arborescence
        def clean_realization_tree(items):
            cleaned = []
            for item in items:
                cleaned_item = {
                    "id": item.get("id", _new_id()),
                    "title": _clean_text(item.get("title", "")),
                }
                if "description" in item and isinstance(item["description"], list):
                    cleaned_item["description"] = clean_realization_tree(item["description"])
                else:
                    cleaned_item["description"] = []
                cleaned.append(cleaned_item)
            return cleaned

        experience["description"] = clean_realization_tree(realization_list)

        # Sauvegarder les modifications
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        return JsonResponse({"status": "ok"})

    except (ValueError, IndexError) as e:
        logger.error(f"Erreur xp_pro_step2_update: {e}")
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
def xp_pro_step2_bulk_update(request, pk, exp_index):
    """Unified bulk update for xp_pro step2 (contexte + env_tech + realizations)."""
    return xp_pro_step2_update(request, pk, exp_index)

# ============================================================================
# MARK: 10. DOCX EXPORT
# ============================================================================

def candidat_export_docx(request, pk=None, slug=None):
    identifier = slug or pk
    index = int(request.GET.get('index', 0))
    status, candidat = get_candidat_or_redirect(identifier, index=index)

    if status == 'not_found':
        raise Http404(f"Candidat not found: {identifier}")

    assert candidat is not None, f"Candidat should not be None (status={status})"

    # Si on accède via pk et le candidat a un slug différent, rediriger vers slug
    if status == 'redirect' and candidat.slug:
        url = f'/candidat/{candidat.slug}/export/'
        if index > 0:
            url += f'?index={index}'
        return redirect(url)

    template_path = Path(settings.DOCX_TEMPLATE_PATH)

    if not template_path.exists():
        return HttpResponse(
            "Le template DOCX est introuvable. Veuillez le placer dans templates_docx/template_jinja.docx.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    try:

        tpl = DocxTemplate(template_path)
        # Extraire les données du dossier JSON
        dossier_data = candidat.dossier or {}

        # Enrichir le header avec les infos du candidat
        header_data = dossier_data.get("header", {})
        header_data.update({
            "trigramme": candidat.trigramme,
            "poste": candidat.poste,
            "skills": [],
            "xp_duration": candidat.xp_duration,
        })

        context = {
            "candidat": candidat,
            "nom": candidat.nom,
            "prenom": candidat.prenom,
            "email": candidat.email,
            "trigramme": candidat.trigramme,
            "poste": candidat.poste,
            "xp_duration": candidat.xp_duration,
            "sections": candidat.get_sections(),
            "dossier": candidat.dossier,
            # Passer les clés du dossier directement au contexte
            "header": header_data,
            "main_skills": dossier_data.get("main_skills", {"bullet": [], "table": []}),
            "xp_pro": dossier_data.get("xp_pro", []),
            "formations": dossier_data.get("formations", []),
            "certifications": dossier_data.get("certifications", []),
            "poste_cible": dossier_data.get("poste_cible", []),
            "skills_cible": dossier_data.get("skills_cible", []),
            "langues": dossier_data.get("langues", []),
        }

        # Récupérer le poste_cible actif pour le nom du fichier
        poste_cible_list = context.get("poste_cible", [])
        active_poste = next((p for p in poste_cible_list if p.get("active")), None)
        poste_filename = (active_poste.get("title", "") if active_poste else candidat.poste or "").title().replace(" ", "_")

        tpl.render(context)

        buffer = io.BytesIO()
        tpl.save(buffer)

        # Supprimer les bullets vides et les paragraphes vides dans les tables (colonne 1 seulement)
        buffer.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(buffer.getvalue())
            tmp_path = tmp.name

        try:
            remove_empty_paragraphs(tmp_path)

            with open(tmp_path, "rb") as f:
                file_content = f.read()

            filename = f"DC_{candidat.trigramme}_{poste_filename}.docx".replace(" ", "_")
            response = HttpResponse(
                file_content,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        logger.exception("Erreur lors de la génération du DOCX pour le candidat %s: %s", pk, str(e))
        return HttpResponse(
            f"Une erreur est survenue lors de la génération du document:\n{str(e)}",
            status=500,
            content_type="text/plain; charset=utf-8",
        )
